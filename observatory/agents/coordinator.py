from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from mesa import Agent, Model
from mesa.time import BaseScheduler

from observatory.agents.observer.lab_scraper import AgentLabScraper
from observatory.agents.observer.publication_scraper import AgentPublicationScraper
from observatory.agents.observer.researcher_scraper import AgentResearcherScraper
from observatory.analysis.agent_cluster import AgentCluster
from observatory.analysis.agent_expertise import AgentExpertiseMatcher
from observatory.config import BASE_DIR
from observatory.recommendation.agent_collab_advisor import AgentCollabAdvisor
from observatory.recommendation.agent_negotiator import AgentNegotiator

logger = logging.getLogger(__name__)

# Strict execution order: observers → analysis → recommendation.
AGENT_SEQUENCE = (
    AgentResearcherScraper,
    AgentPublicationScraper,
    AgentLabScraper,
    AgentCluster,
    AgentExpertiseMatcher,
    AgentCollabAdvisor,
    AgentNegotiator,
)


class AgentCoordinator(Model):
    def __init__(self) -> None:
        super().__init__()
        self.message_bus: Dict[str, Dict[str, Any]] = {}
        self.schedule = BaseScheduler(self)  # insertion-order activation
        self.ordered_agents: List[Agent] = []

        for cls in AGENT_SEQUENCE:
            agent = cls(cls.name, self)
            self.schedule.add(agent)
            self.ordered_agents.append(agent)

        self._file_logger = self._setup_file_logger()

    @staticmethod
    def _setup_file_logger() -> logging.Logger:
        log_dir = Path(BASE_DIR) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "mas.log"

        flog = logging.getLogger("observatory.mas")
        flog.setLevel(logging.INFO)
        flog.propagate = False

        already_attached = any(
            isinstance(h, logging.FileHandler)
            and Path(getattr(h, "baseFilename", "")).resolve() == log_path.resolve()
            for h in flog.handlers
        )
        if not already_attached:
            handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
            handler.setFormatter(
                logging.Formatter(
                    fmt="[%(asctime)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            flog.addHandler(handler)
        return flog

    def run(self, steps: int = 1) -> None:
        for i in range(steps):
            print(f"\n=== Step {i + 1}/{steps} ===")
            for agent in self.ordered_agents:
                agent.step()
                self._log_agent_metric(agent)
            self._print_step_summary(i + 1)

    def _log_agent_metric(self, agent: Agent) -> None:
        payload = self.message_bus.get(agent.name, {})
        line = self._format_metric(agent, payload)
        self._file_logger.info(line)

    @staticmethod
    def _format_metric(agent: Agent, payload: Dict[str, Any]) -> str:
        cls_name = type(agent).__name__
        n = agent.name

        if n == "researcher_scraper":
            return f"{cls_name}: {payload.get('count', 0)} researchers loaded"
        if n == "publication_scraper":
            return f"{cls_name}: {payload.get('count', 0)} publications loaded"
        if n == "lab_scraper":
            return f"{cls_name}: {payload.get('count', 0)} labs loaded"
        if n == "cluster":
            sil = payload.get("silhouette_score")
            sil_txt = f"{sil:.2f}" if isinstance(sil, (int, float)) else "n/a"
            return (
                f"{cls_name}: {payload.get('n_clusters', 0)} clusters, "
                f"silhouette={sil_txt} (algo={payload.get('algorithm')})"
            )
        if n == "expertise_matcher":
            return (
                f"{cls_name}: {payload.get('candidates_inserted', 0)} pairs inserted "
                f"(evaluated={payload.get('total_pairs_evaluated', 0)}), "
                f"avg_sim={payload.get('avg_similarity', 0.0):.2f}"
            )
        if n == "collab_advisor":
            top = payload.get("top_recommendation")
            top_txt = (
                f"{top[0]} ↔ {top[1]} ({top[2]:.2f})"
                if top else "n/a"
            )
            return (
                f"{cls_name}: {payload.get('recommended', 0)} recommended "
                f"(evaluated={payload.get('evaluated', 0)}, "
                f"avg_sim={payload.get('avg_similarity', 0.0):.2f}, top={top_txt})"
            )
        if n == "negotiator":
            return (
                f"{cls_name}: {payload.get('accepted', 0)} accepted / "
                f"{payload.get('rejected', 0)} rejected, "
                f"nash={payload.get('avg_nash_value', 0.0):.2f}"
            )
        return f"{cls_name}: {payload}"

    def _print_step_summary(self, step_num: int) -> None:
        print(f"--- Summary after step {step_num} ---")
        for agent in self.ordered_agents:
            payload = self.message_bus.get(agent.name, {})
            print(f"  {agent.name:<20} {self._format_metric(agent, payload)}")
