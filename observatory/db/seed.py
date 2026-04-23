from __future__ import annotations

import argparse
import random
from collections import defaultdict
from typing import Dict, List

import numpy as np
from faker import Faker
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from observatory.db.database import SessionLocal, engine, init_db
from observatory.db.models import (
    Base,
    Cluster,
    Collaboration,
    Expertise,
    Lab,
    Publication,
    Researcher,
    ResearcherPublication,
)

fake = Faker()

UNIVERSITIES = ["University of Tunis", "INSAT", "ESPRIT"]
COUNTRIES = ["Tunisia", "France", "Germany"]
DEPARTMENTS = [
    "Computer Science",
    "Artificial Intelligence",
    "NLP",
    "Computer Vision",
    "Data Science",
]
LAB_PREFIXES = [
    "Applied", "Advanced", "Intelligent", "Distributed", "Cognitive",
    "Adaptive", "Autonomous", "Scalable", "Interactive", "Next-Gen",
]

VENUES = [
    "ICML", "NeurIPS", "AAAI", "IJCAI", "CVPR", "ICCV", "ECCV",
    "ACL", "EMNLP", "NAACL", "KDD", "ICLR", "IEEE Access", "TPAMI", "JMLR",
]

EXPERTISE_AREAS: List[str] = [
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Data Mining",
    "Reinforcement Learning", "Graph Neural Networks", "Federated Learning",
    "Explainable AI", "Bioinformatics", "Robotics", "Cybersecurity",
    "IoT", "Cloud Computing", "Optimization",
]

EXPERTISE_KEYWORDS: Dict[str, List[str]] = {
    "Machine Learning": ["supervised learning", "regression", "classification",
                         "ensemble methods", "feature engineering", "model selection"],
    "Deep Learning": ["CNN", "RNN", "transformers", "backpropagation",
                      "GANs", "autoencoders"],
    "NLP": ["transformers", "BERT", "tokenization", "sentiment analysis",
            "named entity recognition", "language models"],
    "Computer Vision": ["object detection", "segmentation", "image classification",
                        "optical flow", "3D reconstruction", "face recognition"],
    "Data Mining": ["clustering", "pattern mining", "association rules",
                    "anomaly detection", "frequent itemsets", "time series"],
    "Reinforcement Learning": ["Q-learning", "policy gradients", "actor-critic",
                               "multi-agent RL", "reward shaping", "exploration"],
    "Graph Neural Networks": ["GCN", "GAT", "message passing", "graph embedding",
                              "node classification", "link prediction"],
    "Federated Learning": ["distributed training", "privacy", "aggregation",
                           "client selection", "non-IID data", "differential privacy"],
    "Explainable AI": ["SHAP", "LIME", "interpretability", "feature importance",
                       "counterfactuals", "model transparency"],
    "Bioinformatics": ["genomics", "protein folding", "sequence alignment",
                       "drug discovery", "phylogenetics", "single-cell"],
    "Robotics": ["SLAM", "motion planning", "manipulation", "perception",
                 "control", "human-robot interaction"],
    "Cybersecurity": ["intrusion detection", "malware analysis", "cryptography",
                      "network security", "zero trust", "authentication"],
    "IoT": ["edge computing", "MQTT", "sensor networks", "LoRaWAN",
            "smart devices", "low-power"],
    "Cloud Computing": ["containers", "Kubernetes", "serverless", "microservices",
                        "auto-scaling", "orchestration"],
    "Optimization": ["convex optimization", "gradient descent", "linear programming",
                     "metaheuristics", "Bayesian optimization", "stochastic methods"],
}


def seed_labs(session: Session, n: int = 20) -> List[Lab]:
    labs: List[Lab] = []
    for _ in range(n):
        dept = random.choice(DEPARTMENTS)
        labs.append(
            Lab(
                name=f"{random.choice(LAB_PREFIXES)} {dept} Lab",
                department=dept,
                university=random.choice(UNIVERSITIES),
                country=random.choice(COUNTRIES),
                num_researchers=0,
                active_projects=random.randint(2, 15),
                avg_h_index=0.0,
            )
        )
    session.add_all(labs)
    session.flush()
    return labs


def seed_researchers(session: Session, labs: List[Lab], n: int = 200) -> List[Researcher]:
    raw = np.random.lognormal(mean=2.0, sigma=0.8, size=n)
    h_indices = np.clip(np.round(raw), 1, 50).astype(int)

    researchers: List[Researcher] = []
    for i in range(n):
        h = int(h_indices[i])
        lab = random.choice(labs)
        researchers.append(
            Researcher(
                lab_id=lab.lab_id,
                name=fake.name(),
                department=lab.department,
                h_index=h,
                citation_count=h * random.randint(80, 200),
                publication_count=h * random.randint(3, 8),
                email=fake.unique.email(),
            )
        )
    session.add_all(researchers)
    session.flush()
    return researchers


def update_lab_stats(session: Session, labs: List[Lab], researchers: List[Researcher]) -> None:
    by_lab: Dict[int, List[int]] = defaultdict(list)
    for r in researchers:
        by_lab[r.lab_id].append(r.h_index)
    for lab in labs:
        arr = by_lab.get(lab.lab_id, [])
        lab.num_researchers = len(arr)
        lab.avg_h_index = float(np.mean(arr)) if arr else 0.0
    session.flush()


def seed_publications(session: Session, n: int = 500) -> List[Publication]:
    raw = np.random.pareto(a=1.2, size=n) * 5.0
    cites = np.clip(raw, 0, 5000).astype(int)

    pubs: List[Publication] = []
    for i in range(n):
        title = fake.sentence(nb_words=8).rstrip(".")
        abstract = " ".join(fake.sentences(nb=5))
        pubs.append(
            Publication(
                title=title,
                year=random.randint(2010, 2024),
                citation_count=int(cites[i]),
                venue=random.choice(VENUES),
                abstract=abstract,
            )
        )
    session.add_all(pubs)
    session.flush()
    return pubs


def seed_researcher_publications(
    session: Session,
    researchers: List[Researcher],
    publications: List[Publication],
) -> List[ResearcherPublication]:
    assigned: set[tuple[int, int]] = set()
    pub_has_author: set[int] = set()
    rps: List[ResearcherPublication] = []
    pub_ids = [p.publication_id for p in publications]

    for r in researchers:
        k = random.randint(3, 8)
        chosen = random.sample(pub_ids, k=min(k, len(pub_ids)))
        for idx, pid in enumerate(chosen):
            key = (r.researcher_id, pid)
            if key in assigned:
                continue
            assigned.add(key)
            role = "first_author" if idx == 0 else "co_author"
            rps.append(
                ResearcherPublication(
                    researcher_id=r.researcher_id,
                    publication_id=pid,
                    role=role,
                )
            )
            pub_has_author.add(pid)

    orphans = set(pub_ids) - pub_has_author
    for pid in orphans:
        for _ in range(10):
            r = random.choice(researchers)
            key = (r.researcher_id, pid)
            if key not in assigned:
                assigned.add(key)
                rps.append(
                    ResearcherPublication(
                        researcher_id=r.researcher_id,
                        publication_id=pid,
                        role="co_author",
                    )
                )
                break

    session.add_all(rps)
    session.flush()
    return rps


def seed_expertise(session: Session, researchers: List[Researcher]) -> List[Expertise]:
    expertise: List[Expertise] = []
    for r in researchers:
        k = random.randint(2, 4)
        chosen_areas = random.sample(EXPERTISE_AREAS, k=k)
        for area in chosen_areas:
            pool = EXPERTISE_KEYWORDS[area]
            n_kw = random.randint(3, min(5, len(pool)))
            picked = random.sample(pool, k=n_kw)
            expertise.append(
                Expertise(
                    researcher_id=r.researcher_id,
                    area=area,
                    keywords=", ".join(picked),
                    tfidf_score=round(random.uniform(0.3, 1.0), 4),
                )
            )
    session.add_all(expertise)
    session.flush()
    return expertise


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed_all() -> Dict[str, int]:
    with SessionLocal() as session:
        labs = seed_labs(session)
        researchers = seed_researchers(session, labs)
        update_lab_stats(session, labs, researchers)
        publications = seed_publications(session)
        seed_researcher_publications(session, researchers, publications)
        seed_expertise(session, researchers)
        session.commit()

        counts = {
            "Labs": session.scalar(select(func.count()).select_from(Lab)),
            "Researchers": session.scalar(select(func.count()).select_from(Researcher)),
            "Publications": session.scalar(select(func.count()).select_from(Publication)),
            "ResearcherPublications": session.scalar(
                select(func.count()).select_from(ResearcherPublication)
            ),
            "Expertise": session.scalar(select(func.count()).select_from(Expertise)),
            "Clusters": session.scalar(select(func.count()).select_from(Cluster)),
            "Collaborations": session.scalar(
                select(func.count()).select_from(Collaboration)
            ),
        }
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the observatory database with mock data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables before seeding.",
    )
    args = parser.parse_args()

    if args.reset:
        reset_db()
    else:
        init_db()

    counts = seed_all()
    print("Seed complete. Row counts:")
    for name, n in counts.items():
        print(f"  {name:<25} {n}")


if __name__ == "__main__":
    main()
