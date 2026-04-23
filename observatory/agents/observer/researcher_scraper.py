from __future__ import annotations

import logging

from mesa import Agent
from sqlalchemy import select

from observatory.db.database import get_db
from observatory.db.models import Researcher

logger = logging.getLogger(__name__)


class AgentResearcherScraper(Agent):
    name = "researcher_scraper"

    def step(self) -> None:
        with get_db() as session:
            rows = session.scalars(select(Researcher)).all()
            data = [
                {
                    "researcher_id": r.researcher_id,
                    "lab_id": r.lab_id,
                    "name": r.name,
                    "department": r.department,
                    "h_index": r.h_index,
                    "citation_count": r.citation_count,
                    "publication_count": r.publication_count,
                    "email": r.email,
                    "cluster_id": r.cluster_id,
                }
                for r in rows
            ]

        self.model.message_bus[self.name] = {"count": len(data), "data": data}
        logger.info("AgentResearcherScraper: loaded %d researchers", len(data))
        print(f"AgentResearcherScraper: loaded {len(data)} researchers")
