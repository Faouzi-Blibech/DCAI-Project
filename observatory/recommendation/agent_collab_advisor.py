"""AgentCollabAdvisor — ranks the matcher's candidate pairs and surfaces the
top recommendations for human review.

Position in the pipeline:
    AgentExpertiseMatcher  (computes TF-IDF top-K, inserts pending pairs)
        → AgentCollabAdvisor   (ranks, picks top-N, logs/exposes them)
            → AgentNegotiator     (game-theoretic accept / reject)

The advisor is intentionally non-destructive: it does not write to the DB,
it reads matcher's `top_matches` from the message bus and publishes its
ranking back so the dashboard / negotiator can consume it.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from mesa import Agent
from sqlalchemy import select

from observatory.db.database import get_db
from observatory.db.models import Researcher

logger = logging.getLogger(__name__)

TOP_N_RECOMMENDATIONS = 20
PER_RESEARCHER_KEEP = 3


class AgentCollabAdvisor(Agent):
    name = "collab_advisor"

    def __init__(self, unique_id, model) -> None:
        super().__init__(unique_id, model)
        self.recommendations: List[Tuple[int, int, float]] = []

    def step(self) -> None:
        print("AgentCollabAdvisor: step begin")
        logger.info("AgentCollabAdvisor: step begin")

        bus = self.model.message_bus
        matcher_payload = bus.get("expertise_matcher", {}) or {}
        top_matches: Dict[int, List[Tuple[int, float]]] = (
            matcher_payload.get("top_matches", {}) or {}
        )

        if not top_matches:
            print("AgentCollabAdvisor: no top_matches on bus, skipping")
            logger.info("AgentCollabAdvisor: nothing to advise")
            self.model.message_bus[self.name] = {
                "evaluated": 0,
                "recommended": 0,
                "top_recommendation": None,
            }
            return

        # Keep best PER_RESEARCHER_KEEP per researcher, dedupe canonical (a<b).
        candidates: Dict[Tuple[int, int], float] = {}
        for rid, matches in top_matches.items():
            for other_id, score in matches[:PER_RESEARCHER_KEEP]:
                if rid == other_id:
                    continue
                a, b = (rid, other_id) if rid < other_id else (other_id, rid)
                prev = candidates.get((a, b))
                if prev is None or prev < score:
                    candidates[(a, b)] = float(score)

        evaluated = len(candidates)
        ranked = sorted(candidates.items(), key=lambda kv: kv[1], reverse=True)
        top = ranked[:TOP_N_RECOMMENDATIONS]
        self.recommendations = [(a, b, s) for (a, b), s in top]

        avg_score = (
            sum(s for _, s in ranked) / len(ranked) if ranked else 0.0
        )

        # Resolve names for the headline log line / dashboard tooltip.
        top_recommendation = None
        if top:
            (a, b), score = top[0]
            with get_db() as session:
                rows = session.execute(
                    select(Researcher.researcher_id, Researcher.name).where(
                        Researcher.researcher_id.in_([a, b])
                    )
                ).all()
            name_by_id = dict(rows)
            top_recommendation = (
                name_by_id.get(a, f"R{a}"),
                name_by_id.get(b, f"R{b}"),
                round(score, 4),
            )

        payload = {
            "evaluated": evaluated,
            "recommended": len(top),
            "avg_similarity": round(avg_score, 4),
            "top_recommendation": top_recommendation,
            "recommendations": self.recommendations,
        }
        self.model.message_bus[self.name] = payload

        msg = (
            f"AgentCollabAdvisor: recommended {len(top)} pairs "
            f"(evaluated={evaluated}, avg_sim={avg_score:.4f}, "
            f"top={top_recommendation})"
        )
        print(msg)
        logger.info(msg)


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
    # Without matcher output, advisor reports 0 — that's the expected behaviour.
    advisor = AgentCollabAdvisor(AgentCollabAdvisor.name, model)
    advisor.step()
