"""Generate the UML / architecture figures embedded in REPORT.docx.

Outputs four PNGs into ./figures/:
    fig1_architecture.png    — high-level system architecture
    fig2_mas_sequence.png    — MAS execution sequence (one cycle)
    fig3_er_diagram.png      — relational database schema
    fig4_class_diagram.png   — agent class hierarchy

All diagrams are pure matplotlib (no external graphviz dependency) so they
regenerate from anywhere the venv runs.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mp
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

# Palette aligned with the dashboard.
BG = "#FFFFFF"
SURFACE = "#F2F4F7"
BORDER = "#30363D"
TEXT = "#0D1117"
ACCENT = "#2F81F7"
GREEN = "#3FB950"
AMBER = "#D29922"
PURPLE = "#8957E5"
RED = "#F85149"


def _box(ax, x, y, w, h, label, color=ACCENT, fc=None, fontsize=9, bold=False):
    fc = fc or "#FFFFFF"
    box = mp.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=1.2, edgecolor=color, facecolor=fc,
    )
    ax.add_patch(box)
    weight = "bold" if bold else "normal"
    ax.text(x + w / 2, y + h / 2, label,
            ha="center", va="center", fontsize=fontsize,
            color=TEXT, weight=weight, family="DejaVu Sans")


def _arrow(ax, x1, y1, x2, y2, color=BORDER, label=None, ls="-"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.2, ls=ls),
    )
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.05, label,
                ha="center", va="bottom", fontsize=8, color=color, style="italic")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1 — System architecture
# ─────────────────────────────────────────────────────────────────────────────
def fig1_architecture():
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("Figure 1 — System architecture",
                 loc="left", fontsize=12, weight="bold", pad=12)

    # Layers
    _box(ax, 0.3, 6.3, 11.4, 1.4, "", color=BORDER, fc=SURFACE)
    ax.text(0.5, 7.5, "Presentation layer", fontsize=9, weight="bold", color=TEXT)
    _box(ax, 0.6, 6.55, 3.6, 0.9, "React SPA\n(5 pages, dark UI)", color=ACCENT, fc="#FFFFFF", bold=True)
    _box(ax, 4.5, 6.55, 3.6, 0.9, "Flask REST API\n/api/* endpoints", color=ACCENT, fc="#FFFFFF", bold=True)
    _box(ax, 8.4, 6.55, 3.0, 0.9, "Static assets\n(JSX, CSS, SVG)", color=ACCENT, fc="#FFFFFF", bold=True)

    _box(ax, 0.3, 3.4, 11.4, 2.6, "", color=BORDER, fc=SURFACE)
    ax.text(0.5, 5.85, "Multi-Agent System (Mesa)", fontsize=9, weight="bold", color=TEXT)
    _box(ax, 0.6, 4.7, 2.5, 0.8, "AgentCoordinator", color=PURPLE, fc="#FFFFFF", bold=True, fontsize=9)
    obs = [("AgentResearcher\nScraper", 3.4),
           ("AgentPublication\nScraper", 5.7),
           ("AgentLab\nScraper", 8.0)]
    for label, x in obs:
        _box(ax, x, 4.7, 2.1, 0.8, label, color=GREEN, fc="#FFFFFF", fontsize=8)
    _box(ax, 10.2, 4.7, 1.5, 0.8, "Logger\n(mas.log)", color=AMBER, fc="#FFFFFF", fontsize=8)

    ana = [("AgentCluster\n(KMeans+DBSCAN)", 0.6),
           ("AgentExpertise\nMatcher (TF-IDF)", 3.0),
           ("AgentCollab\nAdvisor", 5.4),
           ("AgentNegotiator\n(Nash)", 7.8)]
    for label, x in ana:
        _box(ax, x, 3.6, 2.2, 0.8, label, color=ACCENT, fc="#FFFFFF", fontsize=8)
    _box(ax, 10.2, 3.6, 1.5, 0.8, "AgentDashboard\nInterface", color=PURPLE, fc="#FFFFFF", fontsize=8)

    _box(ax, 0.3, 1.6, 11.4, 1.4, "", color=BORDER, fc=SURFACE)
    ax.text(0.5, 2.85, "Data layer", fontsize=9, weight="bold", color=TEXT)
    db_tables = ["researchers", "labs", "publications", "clusters",
                 "expertise", "collaborations", "researcher_publications"]
    bw = (11.4 - 0.4) / 7
    for i, name in enumerate(db_tables):
        _box(ax, 0.6 + i * bw, 1.85, bw - 0.15, 0.85, name,
             color=BORDER, fc="#FFFFFF", fontsize=8)
    ax.text(11.5, 1.7, "SQLite + SQLAlchemy", fontsize=8,
            ha="right", color=BORDER, style="italic")

    _box(ax, 0.3, 0.2, 11.4, 0.9, "", color=BORDER, fc=SURFACE)
    ax.text(0.5, 0.95, "External", fontsize=9, weight="bold", color=TEXT)
    _box(ax, 0.6, 0.30, 2.6, 0.6, "Faker seed", color=AMBER, fc="#FFFFFF", fontsize=8)
    _box(ax, 3.4, 0.30, 2.6, 0.6, "Browser (admin)", color=ACCENT, fc="#FFFFFF", fontsize=8)
    _box(ax, 6.2, 0.30, 2.6, 0.6, "logs/mas.log", color=AMBER, fc="#FFFFFF", fontsize=8)
    _box(ax, 9.0, 0.30, 2.7, 0.6, "scikit-learn / Mesa", color=GREEN, fc="#FFFFFF", fontsize=8)

    # Vertical arrows between layers
    _arrow(ax, 6, 6.3, 6, 6.0)
    _arrow(ax, 6, 3.4, 6, 3.0)
    _arrow(ax, 6, 1.6, 6, 1.1)

    fig.tight_layout()
    fig.savefig(OUT / "fig1_architecture.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2 — MAS sequence (one cycle)
# ─────────────────────────────────────────────────────────────────────────────
def fig2_mas_sequence():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_title("Figure 2 — MAS execution sequence (one cycle)",
                 loc="left", fontsize=12, weight="bold", pad=12)

    actors = [
        ("Coordinator", 1.2, PURPLE),
        ("Researcher\nScraper",   2.7, GREEN),
        ("Publication\nScraper",  4.2, GREEN),
        ("Lab\nScraper",          5.7, GREEN),
        ("Cluster\nAgent",        7.2, ACCENT),
        ("Expertise\nMatcher",    8.7, ACCENT),
        ("Collab\nAdvisor",      10.2, ACCENT),
        ("Negotiator",           11.5, AMBER),
    ]
    for name, x, color in actors:
        _box(ax, x - 0.55, 8.0, 1.1, 0.7, name, color=color, fc="#FFFFFF", fontsize=8, bold=True)
        ax.plot([x, x], [0.5, 8.0], color=BORDER, lw=0.8, ls=":")

    # Numbered messages (top → bottom)
    msgs = [
        (1.2, 7.4, 2.7, 7.4, "1. step()"),
        (2.7, 6.9, 1.2, 6.9, "    publishes count → bus"),
        (1.2, 6.4, 4.2, 6.4, "2. step()"),
        (4.2, 5.9, 1.2, 5.9, "    publishes count → bus"),
        (1.2, 5.4, 5.7, 5.4, "3. step()"),
        (5.7, 4.9, 1.2, 4.9, "    publishes count → bus"),
        (1.2, 4.4, 7.2, 4.4, "4. step()  (KMeans + DBSCAN, silhouette)"),
        (7.2, 3.9, 1.2, 3.9, "    writes researchers.cluster_id"),
        (1.2, 3.4, 8.7, 3.4, "5. step()  (TF-IDF, cosine, top-K)"),
        (8.7, 2.9, 1.2, 2.9, "    inserts pending Collaborations"),
        (1.2, 2.4, 10.2, 2.4, "6. step()  (rank top-N pairs)"),
        (10.2, 1.9, 1.2, 1.9, "    publishes recommendations → bus"),
        (1.2, 1.4, 11.5, 1.4, "7. step()  (Nash payoff per pair)"),
        (11.5, 0.9, 1.2, 0.9, "    sets status = accepted / rejected"),
    ]
    for x1, y1, x2, y2, label in msgs:
        _arrow(ax, x1, y1, x2, y2, color=ACCENT if x2 > x1 else AMBER, label=label)

    fig.tight_layout()
    fig.savefig(OUT / "fig2_mas_sequence.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3 — ER diagram
# ─────────────────────────────────────────────────────────────────────────────
def fig3_er_diagram():
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("Figure 3 — Relational database schema (ER)",
                 loc="left", fontsize=12, weight="bold", pad=12)

    tables = {
        "labs": (0.3, 5.3, 2.8, 2.0, [
            "lab_id (PK)", "name", "department", "university",
            "country", "num_researchers", "active_projects", "avg_h_index",
        ]),
        "clusters": (0.3, 1.8, 2.8, 1.6, [
            "cluster_id (PK)", "name", "description",
            "algorithm", "silhouette_score",
        ]),
        "researchers": (4.0, 4.4, 3.4, 3.0, [
            "researcher_id (PK)", "lab_id (FK)", "cluster_id (FK)",
            "name", "department", "h_index",
            "citation_count", "publication_count", "email",
        ]),
        "expertise": (4.0, 0.8, 3.4, 1.8, [
            "expertise_id (PK)", "researcher_id (FK)",
            "area", "keywords", "tfidf_score",
        ]),
        "publications": (8.3, 5.3, 2.8, 2.0, [
            "publication_id (PK)", "title", "year",
            "venue", "citation_count", "abstract",
        ]),
        "researcher_publications": (8.3, 2.6, 3.0, 1.6, [
            "researcher_id (PK,FK)", "publication_id (PK,FK)", "role",
        ]),
        "collaborations": (8.3, 0.3, 3.0, 1.8, [
            "collab_id (PK)", "researcher_a_id (FK)",
            "researcher_b_id (FK)", "similarity_score", "utility_a",
            "utility_b", "nash_value", "status",
        ]),
    }

    # Render each table block
    for name, (x, y, w, h, cols) in tables.items():
        _box(ax, x, y, w, h, "", color=BORDER, fc=SURFACE)
        ax.text(x + 0.1, y + h - 0.25, name,
                fontsize=10, weight="bold", color=ACCENT)
        for i, c in enumerate(cols):
            ax.text(x + 0.15, y + h - 0.55 - 0.22 * i,
                    "• " + c, fontsize=8, color=TEXT, family="DejaVu Sans")

    # Relationships
    rels = [
        ("labs", (3.1, 6.3),         "researchers", (4.0, 5.9), "1..N"),
        ("clusters", (3.1, 2.6),     "researchers", (4.0, 4.6), "0..N"),
        ("researchers", (7.4, 5.3),  "researcher_publications", (8.3, 3.4), "1..N"),
        ("publications", (8.3, 6.0), "researcher_publications", (9.5, 4.2), "1..N"),
        ("researchers", (7.4, 4.9),  "expertise", (7.4, 2.0), "1..N"),
        ("researchers", (7.4, 5.6),  "collaborations", (8.3, 1.2), "2..N"),
    ]
    for _t1, p1, _t2, p2, label in rels:
        _arrow(ax, p1[0], p1[1], p2[0], p2[1], color=AMBER, label=label)

    fig.tight_layout()
    fig.savefig(OUT / "fig3_er_diagram.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 4 — Agent class diagram
# ─────────────────────────────────────────────────────────────────────────────
def fig4_class_diagram():
    fig, ax = plt.subplots(figsize=(13, 7.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7.5)
    ax.axis("off")
    ax.set_title("Figure 4 — Agent class diagram",
                 loc="left", fontsize=12, weight="bold", pad=12)

    # mesa.Agent (abstract / base)
    _box(ax, 5.4, 6.0, 2.4, 1.0,
         "mesa.Agent\n(framework base)",
         color=BORDER, fc=SURFACE, fontsize=9, bold=True)

    children = [
        ("AgentResearcherScraper", 0.3, GREEN, "+ step()\n  → bus['researcher_scraper']"),
        ("AgentPublicationScraper", 2.6, GREEN, "+ step()\n  → bus['publication_scraper']"),
        ("AgentLabScraper", 4.9, GREEN, "+ step()\n  → bus['lab_scraper']"),
        ("AgentCluster", 7.2, ACCENT, "+ step()\n  KMeans+DBSCAN+silhouette"),
        ("AgentExpertiseMatcher", 9.5, ACCENT, "+ step()\n  TF-IDF + cosine, top-K"),
        ("AgentCollabAdvisor", 0.3, ACCENT, "+ step()\n  ranks pairs, picks top-N"),
        ("AgentNegotiator", 2.6, AMBER, "+ step()\n  Nash payoff, accept/reject"),
        ("AgentCoordinator", 4.9, PURPLE, "+ run(steps)\n  schedules + log_metric"),
    ]
    rows = [(0, 3, 4.4), (3, 5, 1.4), (5, 8, 1.4)]
    # First row (3 boxes)
    for i, (name, x, color, body) in enumerate(children[:3]):
        _box(ax, x, 4.4, 2.0, 1.1, name + "\n" + body,
             color=color, fc="#FFFFFF", fontsize=8, bold=True)
        _arrow(ax, x + 1.0, 5.5, 6.6, 6.0, color=BORDER, ls="--")
    for i, (name, x, color, body) in enumerate(children[3:5]):
        _box(ax, x, 4.4, 2.0, 1.1, name + "\n" + body,
             color=color, fc="#FFFFFF", fontsize=8, bold=True)
        _arrow(ax, x + 1.0, 5.5, 6.6, 6.0, color=BORDER, ls="--")
    for i, (name, x, color, body) in enumerate(children[5:]):
        _box(ax, x, 1.4, 2.0, 1.1, name + "\n" + body,
             color=color, fc="#FFFFFF", fontsize=8, bold=True)
        _arrow(ax, x + 1.0, 2.5, 6.6, 6.0, color=BORDER, ls="--")

    # Coordinator owns the others (composition arrow indication)
    ax.text(7.6, 1.0,
            "AgentCoordinator (mesa.Model) — owns the schedule, the message_bus,\n"
            "and the file logger. Drives ordered execution of the 7 step-driven agents.",
            fontsize=8, color=BORDER, style="italic")

    fig.tight_layout()
    fig.savefig(OUT / "fig4_class_diagram.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    fig1_architecture()
    fig2_mas_sequence()
    fig3_er_diagram()
    fig4_class_diagram()
    for p in sorted(OUT.glob("*.png")):
        print(f"  wrote {p.relative_to(ROOT)} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
