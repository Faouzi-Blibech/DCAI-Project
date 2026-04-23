from __future__ import annotations

import logging

from mesa import Agent
from sqlalchemy import select

from observatory.db.database import get_db
from observatory.db.models import Publication

logger = logging.getLogger(__name__)


class AgentPublicationScraper(Agent):
    name = "publication_scraper"

    def step(self) -> None:
        with get_db() as session:
            rows = session.scalars(select(Publication)).all()
            data = [
                {
                    "publication_id": p.publication_id,
                    "title": p.title,
                    "year": p.year,
                    "citation_count": p.citation_count,
                    "venue": p.venue,
                    "abstract": p.abstract,
                }
                for p in rows
            ]

        self.model.message_bus[self.name] = {"count": len(data), "data": data}
        logger.info("AgentPublicationScraper: loaded %d publications", len(data))
        print(f"AgentPublicationScraper: loaded {len(data)} publications")
