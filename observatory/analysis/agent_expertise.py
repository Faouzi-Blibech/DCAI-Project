from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np
from mesa import Agent
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select, update

from observatory.analysis.feature_engineering import build_expertise_tfidf_matrix
from observatory.db.database import get_db
from observatory.db.models import Collaboration, Expertise, Researcher

logger = logging.getLogger(__name__)

TOP_K = 5


class AgentExpertiseMatcher(Agent):
    name = "expertise_matcher"

    def __init__(self, unique_id, model) -> None:
        super().__init__(unique_id, model)
        self.top_matches: Dict[int, List[Tuple[int, float]]] = {}

    def step(self) -> None:
        print("AgentExpertiseMatcher: step begin")
        logger.info("AgentExpertiseMatcher: step begin")

        with get_db() as session:
            # STEP 1 — TF-IDF matrix
            tfidf, ids, _vec = build_expertise_tfidf_matrix(session)
            print(
                f"AgentExpertiseMatcher: tfidf shape={tfidf.shape}, "
                f"researchers={len(ids)}"
            )
            logger.info("AgentExpertiseMatcher: tfidf %s", tfidf.shape)

            n = len(ids)
            if n < 2:
                print("AgentExpertiseMatcher: fewer than 2 researchers, skipping")
                self.model.message_bus[self.name] = {
                    "total_pairs_evaluated": 0,
                    "candidates_inserted": 0,
                    "avg_similarity": 0.0,
                    "top_pair": None,
                }
                return

            # STEP 2 — cosine similarity
            sim = cosine_similarity(tfidf)
            np.fill_diagonal(sim, 0.0)
            print(f"AgentExpertiseMatcher: similarity matrix shape={sim.shape}")
            logger.info("AgentExpertiseMatcher: similarity matrix %s", sim.shape)

            # STEP 3 — overall expertise score per researcher (avg of row, excl self)
            row_means = sim.sum(axis=1) / (n - 1)
            mn, mx = float(row_means.min()), float(row_means.max())
            if mx - mn < 1e-12:
                normalized = np.full_like(row_means, 0.5)
            else:
                normalized = (row_means - mn) / (mx - mn)

            for rid, score in zip(ids, normalized):
                session.execute(
                    update(Expertise)
                    .where(Expertise.researcher_id == rid)
                    .values(tfidf_score=float(score))
                )
            print(
                f"AgentExpertiseMatcher: updated tfidf_score for {n} researchers "
                f"(range {float(normalized.min()):.3f}..{float(normalized.max()):.3f})"
            )
            logger.info("AgentExpertiseMatcher: tfidf_score updated for %d", n)

            # STEP 4 — top-K matches per researcher
            k = min(TOP_K, n - 1)
            self.top_matches = {}
            for i, rid in enumerate(ids):
                row = sim[i]
                top_idx = np.argsort(row)[::-1][:k]
                matches = [
                    (ids[j], float(row[j]))
                    for j in top_idx
                    if float(row[j]) > 0.0
                ]
                self.top_matches[rid] = matches
            print(
                f"AgentExpertiseMatcher: computed top-{k} matches for {len(self.top_matches)} researchers"
            )

            # STEP 5 — persist candidate collaborations (canonical a<b, no dupes)
            candidates: Dict[Tuple[int, int], float] = {}
            for rid, matches in self.top_matches.items():
                for other_id, score in matches:
                    if rid == other_id:
                        continue
                    a, b = (rid, other_id) if rid < other_id else (other_id, rid)
                    prev = candidates.get((a, b))
                    if prev is None or prev < score:
                        candidates[(a, b)] = score

            total_pairs = len(candidates)

            existing_pairs = set()
            existing_rows = session.execute(
                select(Collaboration.researcher_a_id, Collaboration.researcher_b_id)
            ).all()
            for ra, rb in existing_rows:
                lo, hi = (ra, rb) if ra < rb else (rb, ra)
                existing_pairs.add((lo, hi))

            new_rows = []
            for (a, b), score in candidates.items():
                if (a, b) in existing_pairs:
                    continue
                new_rows.append(
                    Collaboration(
                        researcher_a_id=a,
                        researcher_b_id=b,
                        similarity_score=float(score),
                        utility_a=0.0,
                        utility_b=0.0,
                        nash_value=0.0,
                        status="pending",
                    )
                )
            if new_rows:
                session.add_all(new_rows)

            inserted = len(new_rows)
            print(
                f"AgentExpertiseMatcher: evaluated {total_pairs} pairs, "
                f"inserted {inserted} new (skipped {total_pairs - inserted} existing)"
            )
            logger.info(
                "AgentExpertiseMatcher: pairs evaluated=%d inserted=%d",
                total_pairs,
                inserted,
            )

            # STEP 6 — message bus
            avg_similarity = (
                float(np.mean(list(candidates.values()))) if candidates else 0.0
            )

            flat_idx = int(np.argmax(sim))
            i_max, j_max = np.unravel_index(flat_idx, sim.shape)
            top_score = float(sim[i_max, j_max])
            name_map: Dict[int, str] = dict(
                session.execute(
                    select(Researcher.researcher_id, Researcher.name).where(
                        Researcher.researcher_id.in_(ids)
                    )
                ).all()
            )
            top_pair = (
                name_map.get(ids[int(i_max)]),
                name_map.get(ids[int(j_max)]),
                top_score,
            )

        payload = {
            "total_pairs_evaluated": total_pairs,
            "candidates_inserted": inserted,
            "avg_similarity": avg_similarity,
            "top_pair": top_pair,
        }
        self.model.message_bus[self.name] = payload
        logger.info("AgentExpertiseMatcher: done %s", payload)
        print(
            f"AgentExpertiseMatcher: done pairs={total_pairs}, inserted={inserted}, "
            f"avg_sim={avg_similarity:.4f}, top_pair={top_pair}"
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
    agent = AgentExpertiseMatcher(AgentExpertiseMatcher.name, model)
    agent.step()

    print("\n=== message_bus[expertise_matcher] ===")
    for k, v in model.message_bus[AgentExpertiseMatcher.name].items():
        print(f"  {k}: {v}")
