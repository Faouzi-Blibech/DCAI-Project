from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
from mesa import Agent
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score
from sqlalchemy import delete, select, update

from observatory.analysis.feature_engineering import build_researcher_feature_matrix
from observatory.db.database import get_db
from observatory.db.models import Cluster, Expertise, Researcher

logger = logging.getLogger(__name__)

KMEANS_K_RANGE = range(3, 11)
DBSCAN_EPS = 0.8
DBSCAN_MIN_SAMPLES = 3
RANDOM_STATE = 42


def _run_kmeans(X: np.ndarray) -> Tuple[int, np.ndarray, float]:
    best_score = -np.inf
    best_labels: Optional[np.ndarray] = None
    best_k = KMEANS_K_RANGE.start

    for k in KMEANS_K_RANGE:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X)
        if len(set(labels)) < 2:
            continue
        score = float(silhouette_score(X, labels))
        if score > best_score:
            best_score = score
            best_labels = labels
            best_k = k

    if best_labels is None:
        km = KMeans(n_clusters=3, random_state=RANDOM_STATE, n_init=10)
        best_labels = km.fit_predict(X)
        best_score = float(silhouette_score(X, best_labels))
        best_k = 3

    return best_k, best_labels, best_score


def _run_dbscan(X: np.ndarray) -> Tuple[np.ndarray, Optional[float], int]:
    db = DBSCAN(eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES)
    labels = db.fit_predict(X)
    noise_count = int((labels == -1).sum())

    non_noise_mask = labels != -1
    valid_unique = set(labels[non_noise_mask].tolist())

    if len(valid_unique) < 2 or non_noise_mask.sum() < 3:
        return labels, None, noise_count

    score = float(silhouette_score(X[non_noise_mask], labels[non_noise_mask]))
    return labels, score, noise_count


def _fetch_expertise_by_rid(session, researcher_ids: List[int]) -> Dict[int, List[str]]:
    if not researcher_ids:
        return {}
    stmt = select(Expertise.researcher_id, Expertise.area).where(
        Expertise.researcher_id.in_(researcher_ids)
    )
    out: Dict[int, List[str]] = defaultdict(list)
    for rid, area in session.execute(stmt).all():
        out[rid].append(area)
    return out


def _top_areas(
    member_ids: List[int],
    expertise_by_rid: Dict[int, List[str]],
    k: int = 3,
) -> List[str]:
    counter: Counter = Counter()
    for rid in member_ids:
        for area in expertise_by_rid.get(rid, []):
            counter[area] += 1
    return [area for area, _ in counter.most_common(k)]


class AgentCluster(Agent):
    name = "cluster"

    def step(self) -> None:
        logger.info("AgentCluster: step begin")
        print("AgentCluster: step begin")

        with get_db() as session:
            # STEP 1 — feature matrix
            X, ids = build_researcher_feature_matrix(session)
            logger.info("AgentCluster: feature matrix %s, ids=%d", X.shape, len(ids))
            print(f"AgentCluster: feature matrix shape={X.shape}, researchers={len(ids)}")

            if X.shape[0] < 3:
                print("AgentCluster: too few researchers to cluster, skipping")
                self.model.message_bus[self.name] = {
                    "algorithm": None,
                    "n_clusters": 0,
                    "silhouette_score": None,
                    "cluster_sizes": {},
                    "noise_points": 0,
                }
                return

            # STEP 2 — KMeans
            best_k, km_labels, km_score = _run_kmeans(X)
            logger.info("AgentCluster: KMeans best_k=%d silhouette=%.4f", best_k, km_score)
            print(f"AgentCluster: KMeans best_k={best_k}, silhouette={km_score:.4f}")

            # STEP 3 — DBSCAN
            db_labels, db_score, noise_count = _run_dbscan(X)
            db_valid = len(set(db_labels[db_labels != -1].tolist()))
            print(
                f"AgentCluster: DBSCAN valid_clusters={db_valid}, "
                f"noise={noise_count}, silhouette={db_score}"
            )

            # STEP 4 — pick winner
            if db_score is None or db_valid < 2 or db_score < km_score:
                algorithm = "kmeans"
                labels = km_labels.astype(int)
                silhouette = km_score
                noise_count = 0
            else:
                algorithm = "dbscan"
                labels = db_labels.astype(int)
                silhouette = db_score

            print(f"AgentCluster: winner={algorithm}, silhouette={silhouette:.4f}")

            # STEP 5 — persist
            expertise_by_rid = _fetch_expertise_by_rid(session, ids)

            # Reset researcher FKs, then clear clusters table.
            session.execute(update(Researcher).values(cluster_id=None))
            session.execute(delete(Cluster))
            session.flush()

            unique_labels = sorted(set(int(x) for x in labels.tolist()))
            label_to_cluster_id: Dict[int, int] = {}
            cluster_sizes: Dict[str, int] = {}
            display_index = 0

            for lbl in unique_labels:
                mask = labels == lbl
                size = int(mask.sum())
                member_ids = [ids[i] for i in range(len(ids)) if mask[i]]
                top_areas = _top_areas(member_ids, expertise_by_rid, k=3)

                if lbl == -1:
                    cname = "Cluster noise"
                else:
                    cname = f"Cluster {display_index}"
                    display_index += 1

                desc = (
                    "Top areas: " + ", ".join(top_areas)
                    if top_areas
                    else "(no expertise)"
                )
                row = Cluster(
                    name=cname,
                    description=desc,
                    algorithm=algorithm,
                    silhouette_score=float(silhouette),
                )
                session.add(row)
                session.flush()
                label_to_cluster_id[lbl] = row.cluster_id
                cluster_sizes[cname] = size

            for lbl, cid in label_to_cluster_id.items():
                rid_list = [ids[i] for i in range(len(ids)) if int(labels[i]) == lbl]
                if rid_list:
                    session.execute(
                        update(Researcher)
                        .where(Researcher.researcher_id.in_(rid_list))
                        .values(cluster_id=cid)
                    )
            # commit handled by get_db() context manager

        # STEP 6 — message bus
        n_clusters = len([lbl for lbl in unique_labels if lbl != -1])
        payload = {
            "algorithm": algorithm,
            "n_clusters": n_clusters,
            "silhouette_score": float(silhouette),
            "cluster_sizes": cluster_sizes,
            "noise_points": int(noise_count),
        }
        self.model.message_bus[self.name] = payload
        logger.info("AgentCluster: done %s", payload)
        print(
            f"AgentCluster: done algorithm={algorithm}, n_clusters={n_clusters}, "
            f"silhouette={silhouette:.4f}, noise={noise_count}"
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
    agent = AgentCluster(AgentCluster.name, model)
    agent.step()

    print("\n=== message_bus[cluster] ===")
    for k, v in model.message_bus[AgentCluster.name].items():
        print(f"  {k}: {v}")
