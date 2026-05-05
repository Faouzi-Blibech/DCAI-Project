"""Flask REST API for the HIDE Observatory React dashboard.

Run:  python -m observatory.web.api      (or)   python observatory/web/api.py
Then open http://localhost:5000

Serves the React HTML at /  +  static .jsx files under /static/<file>.
JSON endpoints under /api/*  read directly from the live SQLite DB.
"""

from __future__ import annotations

import csv
import io
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parent, _HERE.parent.parent):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import func, select

from observatory.config import BASE_DIR
from observatory.db.database import SessionLocal
from observatory.db.models import (
    Cluster,
    Collaboration,
    Expertise,
    Lab,
    Publication,
    Researcher,
    ResearcherPublication,
)

STATIC_DIR = _HERE / "static"

# Cluster color palette — must match design's CLUSTER_COLORS order.
CLUSTER_COLORS = [
    "#2F81F7", "#3FB950", "#D29922", "#8957E5",
    "#F85149", "#22c4cc", "#b392f0", "#ff9f1c",
]

# Agents shown in the dashboard (8 cards × design contract).
# AgentCollabAdvisor is listed but doesn't exist in the backend — stays IDLE.
AGENT_NAMES = [
    "AgentCoordinator",
    "AgentResearcherScraper",
    "AgentPublicationScraper",
    "AgentLabScraper",
    "AgentCluster",
    "AgentExpertiseMatcher",
    "AgentCollabAdvisor",
    "AgentNegotiator",
]

LOG_PATH = BASE_DIR / "logs" / "mas.log"
LOG_LINE_RE = re.compile(r"^\[(.+?)\]\s+(\w+):\s+(.*)$")
LOG_COUNT_RE = re.compile(r"(\d+)")


app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
CORS(app)


# ─── helpers ────────────────────────────────────────────────────────────────

def _initials(name: str) -> str:
    parts = [p for p in (name or "").split() if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _build_cluster_color_map(db) -> dict[int, str]:
    rows = db.execute(select(Cluster.cluster_id).order_by(Cluster.cluster_id)).all()
    return {row[0]: CLUSTER_COLORS[i % len(CLUSTER_COLORS)] for i, row in enumerate(rows)}


def _build_cluster_size_map(db) -> dict[int, int]:
    rows = db.execute(
        select(Researcher.cluster_id, func.count(Researcher.researcher_id))
        .where(Researcher.cluster_id.isnot(None))
        .group_by(Researcher.cluster_id)
    ).all()
    return {cid: cnt for cid, cnt in rows}


def _read_log_lines() -> list[str]:
    if not LOG_PATH.exists():
        return []
    try:
        return LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    except Exception:
        return []


# ─── /  +  /static/<file> ───────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")


# ─── /api/overview ──────────────────────────────────────────────────────────

@app.route("/api/overview")
def api_overview():
    with SessionLocal() as db:
        researchers_count = db.scalar(select(func.count()).select_from(Researcher)) or 0
        labs_count = db.scalar(select(func.count()).select_from(Lab)) or 0
        pubs_count = db.scalar(select(func.count()).select_from(Publication)) or 0
        avg_h = db.scalar(select(func.avg(Researcher.h_index))) or 0.0
        clusters_count = db.scalar(select(func.count()).select_from(Cluster)) or 0

        # Publications per year (filtering NULL years).
        pubs_per_year_rows = db.execute(
            select(Publication.year, func.count(Publication.publication_id))
            .where(Publication.year.isnot(None))
            .group_by(Publication.year)
            .order_by(Publication.year)
        ).all()

        # Top 10 labs by headcount.
        top_lab_rows = db.execute(
            select(Lab.name, func.count(Researcher.researcher_id))
            .join(Researcher, Researcher.lab_id == Lab.lab_id)
            .group_by(Lab.lab_id)
            .order_by(func.count(Researcher.researcher_id).desc())
            .limit(10)
        ).all()

        # 20 most recent / most-cited publications.
        recent_pubs = db.execute(
            select(
                Publication.publication_id, Publication.title,
                Publication.venue, Publication.year, Publication.citation_count,
            )
            .order_by(Publication.year.desc(), Publication.citation_count.desc())
            .limit(20)
        ).all()
        recent_pids = [p.publication_id for p in recent_pubs]

        # Authors for those publications — single JOIN, no N+1.
        author_rows = db.execute(
            select(ResearcherPublication.publication_id, Researcher.name)
            .join(Researcher,
                  ResearcherPublication.researcher_id == Researcher.researcher_id)
            .where(ResearcherPublication.publication_id.in_(recent_pids))
        ).all() if recent_pids else []

        authors_by_pid: dict[int, list[str]] = defaultdict(list)
        for pid, name in author_rows:
            authors_by_pid[pid].append(name)

        return jsonify({
            "researchers_count": researchers_count,
            "labs_count": labs_count,
            "publications_count": pubs_count,
            "avg_h_index": round(float(avg_h), 1),
            "clusters_count": clusters_count,
            "pubs_per_year": [{"year": y, "n": n} for y, n in pubs_per_year_rows],
            "top_labs": [{"name": n, "v": v} for n, v in top_lab_rows],
            "recent_publications": [
                {
                    "id": f"P{p.publication_id}",
                    "title": p.title,
                    "venue": p.venue,
                    "year": p.year,
                    "citations": p.citation_count or 0,
                    "authors": authors_by_pid.get(p.publication_id, [])[:3],
                }
                for p in recent_pubs
            ],
        })


# ─── /api/researchers ───────────────────────────────────────────────────────

@app.route("/api/researchers")
def api_researchers():
    lab_filter = request.args.get("lab")
    cluster_filter = request.args.get("cluster")
    expertise_filter = request.args.get("expertise")
    try:
        min_h = int(request.args.get("min_h", 0))
    except ValueError:
        min_h = 0

    with SessionLocal() as db:
        cluster_color_map = _build_cluster_color_map(db)
        cluster_size_map = _build_cluster_size_map(db)

        cluster_meta = {
            row.cluster_id: row
            for row in db.execute(select(Cluster)).scalars().all()
        }

        # Optional pre-filter via expertise area (single query, not N×M).
        rids_with_area: set[int] | None = None
        if expertise_filter and expertise_filter != "All":
            rid_rows = db.execute(
                select(Expertise.researcher_id)
                .where(Expertise.area == expertise_filter)
                .distinct()
            ).all()
            rids_with_area = {r[0] for r in rid_rows}

        stmt = select(Researcher).join(Lab, Researcher.lab_id == Lab.lab_id)
        if lab_filter and lab_filter != "All":
            stmt = stmt.where(Lab.name == lab_filter)
        if cluster_filter and cluster_filter != "All":
            stmt = stmt.join(Cluster, Researcher.cluster_id == Cluster.cluster_id) \
                       .where(Cluster.name == cluster_filter)
        if min_h > 0:
            stmt = stmt.where(Researcher.h_index >= min_h)
        researchers = db.execute(stmt).scalars().all()
        if rids_with_area is not None:
            researchers = [r for r in researchers if r.researcher_id in rids_with_area]

        # Bulk-load expertise rows for these researchers.
        rids = [r.researcher_id for r in researchers]
        exp_rows = db.execute(
            select(Expertise.researcher_id, Expertise.area, Expertise.tfidf_score)
            .where(Expertise.researcher_id.in_(rids))
            .order_by(Expertise.tfidf_score.desc())
        ).all() if rids else []

        areas_by_rid: dict[int, list[dict]] = defaultdict(list)
        for rid, area, score in exp_rows:
            areas_by_rid[rid].append({
                "name": area,
                "score": round(float(score or 0.0), 2),
            })

        result = []
        for r in researchers:
            cid = r.cluster_id
            cluster_obj = cluster_meta.get(cid)
            if cluster_obj is not None:
                cluster_payload = {
                    "id": f"C{cid}",
                    "name": cluster_obj.name,
                    "color": cluster_color_map.get(cid, "#8B949E"),
                    "silhouette": round(float(cluster_obj.silhouette_score or 0), 3),
                    "size": cluster_size_map.get(cid, 0),
                    "alg": cluster_obj.algorithm or "N/A",
                }
            else:
                cluster_payload = {
                    "id": "C0", "name": "Unassigned", "color": "#8B949E",
                    "silhouette": 0, "size": 0, "alg": "N/A",
                }

            result.append({
                "id": f"R{r.researcher_id:03d}",
                "name": r.name,
                "initials": _initials(r.name),
                "lab": {
                    "id": f"L{r.lab_id:02d}",
                    "name": r.lab.name if r.lab else "Unknown",
                },
                "cluster": cluster_payload,
                "h_index": r.h_index or 0,
                "publications": r.publication_count or 0,
                "citations": r.citation_count or 0,
                "areas": areas_by_rid.get(r.researcher_id, []),
                # joined: schema has no joined-year column; deterministic display value.
                "joined": 2010 + (r.researcher_id % 14),
            })

        return jsonify(result)


# ─── /api/clusters ──────────────────────────────────────────────────────────

@app.route("/api/clusters")
def api_clusters():
    with SessionLocal() as db:
        clusters = db.execute(
            select(Cluster).order_by(Cluster.cluster_id)
        ).scalars().all()
        size_map = _build_cluster_size_map(db)

        # Top 3 expertise areas per cluster (single grouped query).
        top_areas_rows = db.execute(
            select(
                Researcher.cluster_id,
                Expertise.area,
                func.count(Expertise.expertise_id).label("cnt"),
            )
            .join(Expertise, Expertise.researcher_id == Researcher.researcher_id)
            .where(Researcher.cluster_id.isnot(None))
            .group_by(Researcher.cluster_id, Expertise.area)
            .order_by(Researcher.cluster_id, func.count(Expertise.expertise_id).desc())
        ).all()

        top_by_cid: dict[int, list[str]] = defaultdict(list)
        for cid, area, _cnt in top_areas_rows:
            if len(top_by_cid[cid]) < 3:
                top_by_cid[cid].append(area)

        return jsonify([
            {
                "id": f"C{c.cluster_id}",
                "name": c.name,
                "color": CLUSTER_COLORS[i % len(CLUSTER_COLORS)],
                "silhouette": round(float(c.silhouette_score or 0), 3),
                "size": size_map.get(c.cluster_id, 0),
                "alg": c.algorithm or "KMeans",
                "top_areas": top_by_cid.get(c.cluster_id, []),
                "description": c.description or "",
            }
            for i, c in enumerate(clusters)
        ])


# ─── /api/expertise ─────────────────────────────────────────────────────────

@app.route("/api/expertise")
def api_expertise():
    with SessionLocal() as db:
        areas = db.execute(
            select(Expertise.area).distinct().order_by(Expertise.area)
        ).scalars().all()
        return jsonify([a for a in areas if a])


# ─── /api/labs ──────────────────────────────────────────────────────────────

@app.route("/api/labs")
def api_labs():
    with SessionLocal() as db:
        names = db.execute(
            select(Lab.name).order_by(Lab.name)
        ).scalars().all()
        return jsonify(list(names))


# ─── /api/collaborations ────────────────────────────────────────────────────

@app.route("/api/collaborations")
def api_collaborations():
    with SessionLocal() as db:
        cluster_color_map = _build_cluster_color_map(db)
        cluster_name_map = {
            cid: name for cid, name in db.execute(
                select(Cluster.cluster_id, Cluster.name)
            ).all()
        }

        collabs = db.execute(
            select(Collaboration)
            .order_by(Collaboration.nash_value.desc())
            .limit(150)
        ).scalars().all()

        rid_set = set()
        for c in collabs:
            rid_set.add(c.researcher_a_id)
            rid_set.add(c.researcher_b_id)

        researcher_rows = db.execute(
            select(Researcher).where(Researcher.researcher_id.in_(rid_set))
        ).scalars().all() if rid_set else []
        r_by_id = {r.researcher_id: r for r in researcher_rows}

        def mini(rid: int) -> dict:
            r = r_by_id.get(rid)
            if r is None:
                return {
                    "id": "R000", "name": "Unknown", "initials": "??",
                    "lab": {"id": "L0", "name": "Unknown"},
                    "cluster": {"id": "C0", "name": "Unknown", "color": "#8B949E"},
                    "h_index": 0,
                }
            cid = r.cluster_id or 0
            return {
                "id": f"R{r.researcher_id:03d}",
                "name": r.name,
                "initials": _initials(r.name),
                "lab": {
                    "id": f"L{r.lab_id:02d}",
                    "name": r.lab.name if r.lab else "Unknown",
                },
                "cluster": {
                    "id": f"C{cid}",
                    "name": cluster_name_map.get(cid, "Unassigned"),
                    "color": cluster_color_map.get(cid, "#8B949E"),
                },
                "h_index": r.h_index or 0,
            }

        return jsonify([
            {
                "a": mini(c.researcher_a_id),
                "b": mini(c.researcher_b_id),
                "sim": round(float(c.similarity_score or 0), 3),
                "ua": round(float(c.utility_a or 0), 3),
                "ub": round(float(c.utility_b or 0), 3),
                "nash": round(float(c.nash_value or 0), 3),
                "status": c.status or "pending",
            }
            for c in collabs
        ])


# ─── /api/agents ────────────────────────────────────────────────────────────

def _build_agent_data() -> list[dict]:
    """Parse mas.log → agent state + 12-bin sparkline series."""
    lines = _read_log_lines()
    last_msg: dict[str, tuple[str, str]] = {}
    history: dict[str, list[int]] = defaultdict(list)
    has_error: dict[str, bool] = defaultdict(bool)

    for line in lines:
        m = LOG_LINE_RE.match(line)
        if not m:
            continue
        ts_str, name, msg = m.group(1), m.group(2), m.group(3)
        if name not in AGENT_NAMES:
            continue
        last_msg[name] = (ts_str, msg)

        cnt_match = LOG_COUNT_RE.search(msg)
        if cnt_match:
            history[name].append(int(cnt_match.group(1)))

        low = msg.lower()
        if any(tok in low for tok in ("error", "failed", "exception")):
            has_error[name] = True

    now = datetime.now()
    out: list[dict] = []
    for name in AGENT_NAMES:
        if name in last_msg:
            ts_str, msg = last_msg[name]
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                secs = int((now - ts).total_seconds())
                if secs < 60:
                    last = f"{secs}s ago"
                elif secs < 3600:
                    last = f"{secs // 60}m ago"
                elif secs < 86400:
                    last = f"{secs // 3600}h ago"
                else:
                    last = f"{secs // 86400}d ago"
            except ValueError:
                last = ts_str
            status = "error" if has_error[name] else "active"
        else:
            last = "Never"
            status = "idle"

        # 12-bin sparkline from per-agent count history.
        seq = history.get(name, [])
        if seq:
            # Pad/trim to exactly 12 bins; bin to last 12 records.
            tail = seq[-12:]
            if len(tail) < 12:
                tail = [tail[0]] * (12 - len(tail)) + tail
            series = tail
            records = tail[-1]
        else:
            series = [0] * 12
            records = 0

        out.append({
            "name": name,
            "status": status,
            "last": last,
            "records": records,
            "series": series,
        })
    return out


@app.route("/api/agents")
def api_agents():
    return jsonify(_build_agent_data())


# ─── /api/logs ──────────────────────────────────────────────────────────────

@app.route("/api/logs")
def api_logs():
    try:
        n = int(request.args.get("n", 50))
    except ValueError:
        n = 50
    lines = _read_log_lines()[-n:]
    out = []
    for line in lines:
        m = LOG_LINE_RE.match(line)
        if not m:
            continue
        ts, agent, msg = m.group(1), m.group(2), m.group(3)
        low = msg.lower()
        if any(tok in low for tok in ("error", "failed", "exception")):
            level = "ERR "
        elif "warn" in low:
            level = "WARN"
        elif any(tok in low for tok in ("loaded", "complete", "converged",
                                        "done", "accepted")):
            level = "OK  "
        else:
            level = "INFO"
        # Time-of-day only, matches the design's LOG_LINES tuple shape.
        ts_short = ts.split(" ")[1] if " " in ts else ts
        out.append([ts_short, level, agent.lower(), msg])
    return jsonify(out)


# ─── /api/run  (POST) ───────────────────────────────────────────────────────

@app.route("/api/run", methods=["POST"])
def api_run():
    try:
        from observatory.agents.coordinator import AgentCoordinator
        coord = AgentCoordinator()
        coord.run(steps=1)
        bus = coord.message_bus
        summary = {
            "researchers": bus.get("researcher_scraper", {}).get("count", 0),
            "publications": bus.get("publication_scraper", {}).get("count", 0),
            "labs": bus.get("lab_scraper", {}).get("count", 0),
            "clusters": bus.get("cluster", {}).get("n_clusters", 0),
            "accepted": bus.get("negotiator", {}).get("accepted", 0),
            "rejected": bus.get("negotiator", {}).get("rejected", 0),
        }
        return jsonify({"ok": True, "message": "Cycle complete", "summary": summary})
    except Exception as e:
        return jsonify({"ok": False, "message": f"{type(e).__name__}: {e}"}), 500


# ─── /api/recluster  (POST) ─────────────────────────────────────────────────

@app.route("/api/recluster", methods=["POST"])
def api_recluster():
    try:
        from observatory.agents.coordinator import AgentCoordinator
        from observatory.analysis.agent_cluster import AgentCluster
        coord = AgentCoordinator()
        for agent in coord.ordered_agents:
            if isinstance(agent, AgentCluster):
                agent.step()
                coord._log_agent_metric(agent)
                break
        payload = coord.message_bus.get("cluster", {})
        return jsonify({"ok": True, "message": "Re-clustered",
                        "n_clusters": payload.get("n_clusters", 0),
                        "silhouette": payload.get("silhouette_score", 0)})
    except Exception as e:
        return jsonify({"ok": False, "message": f"{type(e).__name__}: {e}"}), 500


# ─── /api/recommendations  (POST) ───────────────────────────────────────────

@app.route("/api/recommendations", methods=["POST"])
def api_recommendations():
    try:
        from observatory.agents.coordinator import AgentCoordinator
        from observatory.analysis.agent_expertise import AgentExpertiseMatcher
        from observatory.recommendation.agent_collab_advisor import AgentCollabAdvisor
        from observatory.recommendation.agent_negotiator import AgentNegotiator
        coord = AgentCoordinator()
        for agent in coord.ordered_agents:
            if isinstance(agent, (AgentExpertiseMatcher, AgentCollabAdvisor, AgentNegotiator)):
                agent.step()
                coord._log_agent_metric(agent)
        neg = coord.message_bus.get("negotiator", {})
        adv = coord.message_bus.get("collab_advisor", {})
        return jsonify({"ok": True, "message": "Recommendations refreshed",
                        "advised": adv.get("recommended", 0),
                        "accepted": neg.get("accepted", 0),
                        "rejected": neg.get("rejected", 0)})
    except Exception as e:
        return jsonify({"ok": False, "message": f"{type(e).__name__}: {e}"}), 500


# ─── /api/advisor  (POST) ───────────────────────────────────────────────────

@app.route("/api/advisor", methods=["POST"])
def api_advisor():
    try:
        from observatory.agents.coordinator import AgentCoordinator
        from observatory.analysis.agent_expertise import AgentExpertiseMatcher
        from observatory.recommendation.agent_collab_advisor import AgentCollabAdvisor
        coord = AgentCoordinator()
        # Advisor depends on matcher's bus output; run matcher first to refresh it.
        for agent in coord.ordered_agents:
            if isinstance(agent, (AgentExpertiseMatcher, AgentCollabAdvisor)):
                agent.step()
                coord._log_agent_metric(agent)
        adv = coord.message_bus.get("collab_advisor", {})
        return jsonify({"ok": True, "message": "Advisor refreshed",
                        "recommended": adv.get("recommended", 0),
                        "evaluated": adv.get("evaluated", 0),
                        "top": adv.get("top_recommendation")})
    except Exception as e:
        return jsonify({"ok": False, "message": f"{type(e).__name__}: {e}"}), 500


# ─── /api/collaborations/accept_pending  (POST) ─────────────────────────────

@app.route("/api/collaborations/accept_pending", methods=["POST"])
def api_accept_pending():
    try:
        with SessionLocal() as db:
            pending = db.execute(
                select(Collaboration).where(Collaboration.status == "pending")
            ).scalars().all()
            n = 0
            for c in pending:
                c.status = "accepted"
                n += 1
            db.commit()
        return jsonify({"ok": True, "message": f"Accepted {n} collaborations",
                        "accepted": n})
    except Exception as e:
        return jsonify({"ok": False, "message": f"{type(e).__name__}: {e}"}), 500


# ─── /api/reseed  (POST) ────────────────────────────────────────────────────

@app.route("/api/reseed", methods=["POST"])
def api_reseed():
    try:
        from observatory.db.seed import reset_db, seed_all
        reset_db()
        counts = seed_all()
        return jsonify({"ok": True, "message": "Database reset & reseeded",
                        "counts": counts})
    except Exception as e:
        return jsonify({"ok": False, "message": f"{type(e).__name__}: {e}"}), 500


# ─── /api/logs/download  (GET) ──────────────────────────────────────────────

@app.route("/api/logs/download")
def api_logs_download():
    text = "\n".join(_read_log_lines()) if LOG_PATH.exists() else ""
    return Response(
        text,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=mas.log"},
    )


# ─── /api/researchers/export.csv  (GET) ─────────────────────────────────────

@app.route("/api/researchers/export.csv")
def api_researchers_csv():
    with SessionLocal() as db:
        rows = db.execute(
            select(Researcher).join(Lab, Researcher.lab_id == Lab.lab_id)
        ).scalars().all()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "name", "lab", "h_index", "publications",
                    "citations", "cluster_id"])
        for r in rows:
            w.writerow([
                r.researcher_id, r.name,
                r.lab.name if r.lab else "",
                r.h_index or 0, r.publication_count or 0,
                r.citation_count or 0, r.cluster_id or "",
            ])
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=researchers.csv"},
        )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
