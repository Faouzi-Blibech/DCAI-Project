from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from observatory.db.models import Researcher


# Fixed 15 expertise areas — must match the order used in observatory/db/seed.py.
EXPERTISE_AREAS: List[str] = [
    "Machine Learning",
    "Deep Learning",
    "NLP",
    "Computer Vision",
    "Data Mining",
    "Reinforcement Learning",
    "Graph Neural Networks",
    "Federated Learning",
    "Explainable AI",
    "Bioinformatics",
    "Robotics",
    "Cybersecurity",
    "IoT",
    "Cloud Computing",
    "Optimization",
]

# Module-level singletons — fit once, transform thereafter so repeated step()
# calls stay consistent across runs.
_scaler: Optional[StandardScaler] = None
_vectorizer: Optional[TfidfVectorizer] = None


def get_expertise_areas() -> List[str]:
    return list(EXPERTISE_AREAS)


def get_scaler() -> Optional[StandardScaler]:
    return _scaler


def get_vectorizer() -> Optional[TfidfVectorizer]:
    return _vectorizer


def reset_singletons() -> None:
    global _scaler, _vectorizer
    _scaler = None
    _vectorizer = None


def _load_researchers(session: Session) -> List[Researcher]:
    stmt = (
        select(Researcher)
        .options(selectinload(Researcher.expertise))
        .order_by(Researcher.researcher_id)
    )
    return list(session.scalars(stmt).all())


def build_researcher_feature_matrix(
    session: Session,
) -> Tuple[np.ndarray, List[int]]:
    """Build the scaled numeric feature matrix for clustering.

    Feature vector per researcher (18 dims total):
        [h_index,
         log1p(citation_count),
         log1p(publication_count),
         expertise_vec_15d]   # binary, one slot per area in EXPERTISE_AREAS order
    """
    global _scaler

    researchers = _load_researchers(session)
    area_index = {area: i for i, area in enumerate(EXPERTISE_AREAS)}
    n_areas = len(EXPERTISE_AREAS)

    rows: List[np.ndarray] = []
    ids: List[int] = []
    for r in researchers:
        expertise_vec = np.zeros(n_areas, dtype=float)
        for e in r.expertise:
            idx = area_index.get(e.area)
            if idx is not None:
                expertise_vec[idx] = 1.0

        numeric = np.array(
            [
                float(r.h_index or 0),
                float(np.log1p(r.citation_count or 0)),
                float(np.log1p(r.publication_count or 0)),
            ],
            dtype=float,
        )
        rows.append(np.concatenate([numeric, expertise_vec]))
        ids.append(r.researcher_id)

    if not rows:
        return np.empty((0, 3 + n_areas), dtype=float), []

    X = np.vstack(rows)

    if _scaler is None:
        _scaler = StandardScaler()
        X_scaled = _scaler.fit_transform(X)
    else:
        X_scaled = _scaler.transform(X)

    return X_scaled, ids


def build_expertise_tfidf_matrix(
    session: Session,
) -> Tuple[np.ndarray, List[int], TfidfVectorizer]:
    """Build a TF-IDF matrix over each researcher's combined expertise keywords."""
    global _vectorizer

    researchers = _load_researchers(session)

    docs: List[str] = []
    ids: List[int] = []
    for r in researchers:
        parts: List[str] = []
        for e in r.expertise:
            if e.area:
                parts.append(e.area)
            if e.keywords:
                parts.append(e.keywords)
        docs.append(" ".join(parts) if parts else "")
        ids.append(r.researcher_id)

    if not docs:
        empty = np.empty((0, 0), dtype=float)
        return empty, [], TfidfVectorizer(max_features=100)

    if _vectorizer is None:
        _vectorizer = TfidfVectorizer(max_features=100)
        matrix = _vectorizer.fit_transform(docs)
    else:
        matrix = _vectorizer.transform(docs)

    return matrix.toarray(), ids, _vectorizer


if __name__ == "__main__":
    from observatory.db.database import SessionLocal

    with SessionLocal() as s:
        X, ids = build_researcher_feature_matrix(s)
        tfidf, tfidf_ids, vec = build_expertise_tfidf_matrix(s)

    print(f"[feature matrix] shape={X.shape}, n_ids={len(ids)}")
    print(f"  feature order: [h_index, log1p(cite), log1p(pub), *{len(EXPERTISE_AREAS)} expertise areas]")
    if len(ids) > 0:
        print(f"  sample row (researcher_id={ids[0]}): {np.round(X[0], 3).tolist()}")

    print(f"\n[tfidf matrix]   shape={tfidf.shape}, n_ids={len(tfidf_ids)}")
    print(f"  vocabulary size: {len(vec.get_feature_names_out())}")
    if tfidf.shape[0] > 0 and tfidf.shape[1] > 0:
        row = tfidf[0]
        top_idx = np.argsort(row)[::-1][:5]
        vocab = vec.get_feature_names_out()
        top_terms = [(vocab[i], round(float(row[i]), 3)) for i in top_idx if row[i] > 0]
        print(f"  top terms for researcher_id={tfidf_ids[0]}: {top_terms}")
