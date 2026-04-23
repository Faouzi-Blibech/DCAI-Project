from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from sqlalchemy import func, select

from observatory.agents.coordinator import AgentCoordinator
from observatory.db.database import SessionLocal, init_db
from observatory.db.models import Lab, Publication, Researcher
from observatory.db.seed import seed_all


def _db_is_empty() -> bool:
    with SessionLocal() as session:
        for model in (Lab, Researcher, Publication):
            n = session.scalar(select(func.count()).select_from(model))
            if n and n > 0:
                return False
    return True


def _row_for(name: str, payload: Dict[str, Any]) -> Tuple[str, str, str]:
    """Return (display_name, records_str, key_metric_str) for the summary table."""
    if name == "researcher_scraper":
        return ("ResearcherScraper", str(payload.get("count", 0)), "loaded")
    if name == "publication_scraper":
        return ("PublicationScraper", str(payload.get("count", 0)), "loaded")
    if name == "lab_scraper":
        return ("LabScraper", str(payload.get("count", 0)), "loaded")
    if name == "cluster":
        sil = payload.get("silhouette_score")
        sil_txt = f"{sil:.2f}" if isinstance(sil, (int, float)) else "n/a"
        return (
            "AgentCluster",
            str(payload.get("n_clusters", 0)),
            f"silhouette={sil_txt}",
        )
    if name == "expertise_matcher":
        return (
            "ExpertiseMatcher",
            str(payload.get("candidates_inserted", 0)),
            f"avg_sim={payload.get('avg_similarity', 0.0):.2f}",
        )
    if name == "negotiator":
        return (
            "AgentNegotiator",
            str(payload.get("accepted", 0)),
            f"accepted, nash={payload.get('avg_nash_value', 0.0):.2f}",
        )
    return (name, "0", "")


def _print_summary_table(bus: Dict[str, Any], order: List[str]) -> None:
    rows = [_row_for(n, bus.get(n, {})) for n in order]
    headers = ("Agent", "Records", "Key metric")

    w0 = max(len(headers[0]), *(len(r[0]) for r in rows))
    w1 = max(len(headers[1]), *(len(r[1]) for r in rows))
    w2 = max(len(headers[2]), *(len(r[2]) for r in rows))

    def fmt(a: str, b: str, c: str) -> str:
        return f"| {a.ljust(w0)} | {b.rjust(w1)} | {c.ljust(w2)} |"

    sep = f"|{'-' * (w0 + 2)}|{'-' * (w1 + 2)}|{'-' * (w2 + 2)}|"

    print()
    print(fmt(*headers))
    print(sep)
    for r in rows:
        print(fmt(*r))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    print("Initializing database...")
    init_db()

    if _db_is_empty():
        print("Database is empty — running seed...")
        counts = seed_all()
        print("Seed complete:", counts)
    else:
        print("Database already populated; skipping seed.")

    print("\nLaunching AgentCoordinator...")
    coordinator = AgentCoordinator()
    coordinator.run(steps=1)

    print("\n=== Final Run Summary ===")
    order = [a.name for a in coordinator.ordered_agents]
    _print_summary_table(coordinator.message_bus, order)


if __name__ == "__main__":
    main()
