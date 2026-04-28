from __future__ import annotations

import logging
import math
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from mesa import Agent
from sqlalchemy import select

from observatory.db.database import get_db
from observatory.db.models import Collaboration, Expertise, Researcher

logger = logging.getLogger(__name__)

NUM_EXPERTISE_AREAS = 15
ACCEPT_THRESHOLD = 0.15
PARETO_FLOOR = 0.05


def _compute_utilities(
    a_h: int,
    b_h: int,
    a_cites: int,
    b_cites: int,
    a_cluster: int | None,
    b_cluster: int | None,
    shared_areas: int,
    max_h: int,
    max_total_cites: int,
) -> Tuple[float, float, Dict[str, float]]:
    expertise_overlap = shared_areas / NUM_EXPERTISE_AREAS

    denom_h = max_h if max_h > 0 else 1
    h_gain_a = (b_h - a_h) / denom_h
    h_gain_b = (a_h - b_h) / denom_h

    log_total = math.log1p(a_cites + b_cites)
    log_max = math.log1p(max_total_cites) if max_total_cites > 0 else 1.0
    citation_potential = log_total / log_max if log_max > 0 else 0.0

    same_cluster_bonus = (
        0.1 if (a_cluster is not None and a_cluster == b_cluster) else 0.0
    )

    utility_a = (
        0.4 * expertise_overlap
        + 0.3 * max(h_gain_a, 0)
        + 0.2 * citation_potential
        + 0.1 * same_cluster_bonus
    )
    utility_b = (
        0.4 * expertise_overlap
        + 0.3 * max(h_gain_b, 0)
        + 0.2 * citation_potential
        + 0.1 * same_cluster_bonus
    )

    components = {
        "expertise_overlap": expertise_overlap,
        "h_gain_a": h_gain_a,
        "h_gain_b": h_gain_b,
        "citation_potential": citation_potential,
        "same_cluster_bonus": same_cluster_bonus,
    }
    return utility_a, utility_b, components


def _is_cc_nash(utility_a: float, utility_b: float) -> bool:
    """Pareto-dominance test over the mutual-defection baseline (0.05, 0.05).

    Cooperation is accepted when BOTH players are strictly better off
    cooperating than they would be at (D,D). This replaces the textbook
    strict-NE check, which in this payoff matrix is only satisfied at
    u_a = u_b = 0 and would reject every positive-utility pair.
    """
    return utility_a > PARETO_FLOOR and utility_b > PARETO_FLOOR


class AgentNegotiator(Agent):
    name = "negotiator"

    def step(self) -> None:
        print("AgentNegotiator: step begin")
        logger.info("AgentNegotiator: step begin")

        with get_db() as session:
            # STEP 1 — load pending collaborations + joined researcher profiles
            pending: List[Collaboration] = list(
                session.scalars(
                    select(Collaboration).where(Collaboration.status == "pending")
                ).all()
            )
            print(f"AgentNegotiator: loaded {len(pending)} pending collaborations")
            logger.info("AgentNegotiator: %d pending collaborations", len(pending))

            if not pending:
                payload = {
                    "total_evaluated": 0,
                    "accepted": 0,
                    "rejected": 0,
                    "avg_nash_value": 0.0,
                    "best_collaboration": None,
                }
                self.model.message_bus[self.name] = payload
                print(f"AgentNegotiator: nothing to do -> {payload}")
                return

            rid_set: Set[int] = set()
            for c in pending:
                rid_set.add(c.researcher_a_id)
                rid_set.add(c.researcher_b_id)
            rid_list = list(rid_set)

            researcher_rows = session.execute(
                select(
                    Researcher.researcher_id,
                    Researcher.name,
                    Researcher.h_index,
                    Researcher.citation_count,
                    Researcher.publication_count,
                    Researcher.cluster_id,
                ).where(Researcher.researcher_id.in_(rid_list))
            ).all()
            r_by_id: Dict[int, dict] = {
                row.researcher_id: {
                    "name": row.name,
                    "h_index": row.h_index or 0,
                    "citation_count": row.citation_count or 0,
                    "publication_count": row.publication_count or 0,
                    "cluster_id": row.cluster_id,
                }
                for row in researcher_rows
            }

            expertise_rows = session.execute(
                select(Expertise.researcher_id, Expertise.area).where(
                    Expertise.researcher_id.in_(rid_list)
                )
            ).all()
            areas_by_rid: Dict[int, Set[str]] = defaultdict(set)
            for rid, area in expertise_rows:
                if area:
                    areas_by_rid[rid].add(area)

            max_h = max((r["h_index"] for r in r_by_id.values()), default=0)
            max_total_cites = 0
            for c in pending:
                ra = r_by_id.get(c.researcher_a_id)
                rb = r_by_id.get(c.researcher_b_id)
                if ra and rb:
                    total = ra["citation_count"] + rb["citation_count"]
                    if total > max_total_cites:
                        max_total_cites = total

            print(
                f"AgentNegotiator: normalization anchors max_h={max_h}, "
                f"max_total_cites={max_total_cites}"
            )

            # STEP 2 + 3 — utilities + Nash check per pair
            accepted = 0
            rejected = 0
            nash_values: List[float] = []
            best: Tuple[str, str, float] | None = None

            for c in pending:
                ra = r_by_id.get(c.researcher_a_id)
                rb = r_by_id.get(c.researcher_b_id)
                if ra is None or rb is None:
                    continue

                shared = len(
                    areas_by_rid.get(c.researcher_a_id, set())
                    & areas_by_rid.get(c.researcher_b_id, set())
                )

                utility_a, utility_b, _ = _compute_utilities(
                    a_h=ra["h_index"],
                    b_h=rb["h_index"],
                    a_cites=ra["citation_count"],
                    b_cites=rb["citation_count"],
                    a_cluster=ra["cluster_id"],
                    b_cluster=rb["cluster_id"],
                    shared_areas=shared,
                    max_h=max_h,
                    max_total_cites=max_total_cites,
                )

                if _is_cc_nash(utility_a, utility_b):
                    nash_value = (utility_a + utility_b) / 2.0
                else:
                    nash_value = 0.0

                # STEP 4 — write back to row
                c.utility_a = float(utility_a)
                c.utility_b = float(utility_b)
                c.nash_value = float(nash_value)
                if nash_value > ACCEPT_THRESHOLD:
                    c.status = "accepted"
                    accepted += 1
                else:
                    c.status = "rejected"
                    rejected += 1

                nash_values.append(nash_value)

                if best is None or nash_value > best[2]:
                    best = (ra["name"], rb["name"], float(nash_value))

            # commit handled by get_db() context manager

        # STEP 5 — message bus
        total_evaluated = len(nash_values)
        avg_nash = (
            float(sum(nash_values) / total_evaluated) if total_evaluated else 0.0
        )
        payload = {
            "total_evaluated": total_evaluated,
            "accepted": accepted,
            "rejected": rejected,
            "avg_nash_value": avg_nash,
            "best_collaboration": best,
        }
        self.model.message_bus[self.name] = payload
        logger.info("AgentNegotiator: done %s", payload)
        print(
            f"AgentNegotiator: done evaluated={total_evaluated}, "
            f"accepted={accepted}, rejected={rejected}, avg_nash={avg_nash:.4f}, "
            f"best={best}"
        )


if __name__ == "__main__":
    import random as _random

    from observatory.db.database import init_db

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    init_db()

    class StubModel:
        def __init__(self) -> None:
            self.random = _random.Random()
            self.message_bus: Dict[str, dict] = {}

        def register_agent(self, agent) -> None:
            pass

        def deregister_agent(self, agent) -> None:
            pass

    model = StubModel()
    agent = AgentNegotiator(AgentNegotiator.name, model)
    agent.step()

    print("\n=== message_bus[negotiator] ===")
    for k, v in model.message_bus[AgentNegotiator.name].items():
        print(f"  {k}: {v}")
