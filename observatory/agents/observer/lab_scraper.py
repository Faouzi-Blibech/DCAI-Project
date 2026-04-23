from __future__ import annotations

import logging

from mesa import Agent
from sqlalchemy import select

from observatory.db.database import get_db
from observatory.db.models import Lab

logger = logging.getLogger(__name__)


class AgentLabScraper(Agent):
    name = "lab_scraper"

    def step(self) -> None:
        with get_db() as session:
            rows = session.scalars(select(Lab)).all()
            data = [
                {
                    "lab_id": lab.lab_id,
                    "name": lab.name,
                    "department": lab.department,
                    "university": lab.university,
                    "country": lab.country,
                    "num_researchers": lab.num_researchers,
                    "active_projects": lab.active_projects,
                    "avg_h_index": lab.avg_h_index,
                }
                for lab in rows
            ]

        self.model.message_bus[self.name] = {"count": len(data), "data": data}
        logger.info("AgentLabScraper: loaded %d labs", len(data))
        print(f"AgentLabScraper: loaded {len(data)} labs")
