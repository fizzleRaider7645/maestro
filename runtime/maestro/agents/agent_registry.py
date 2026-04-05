"""Discovers and indexes all agents from the agent-builder directory."""

from __future__ import annotations
from pathlib import Path

from ..core.agent_loader import load_all_agents, load_agent
from ..core.types import AgentConfig
from ..core.constants import AGENTS_DIR


class AgentRegistry:
    """
    Lazy-loading registry of all agents defined in agent-builder/agents/.

    Agents are loaded on first access to keep startup fast.
    """

    def __init__(self, agents_dir: Path = AGENTS_DIR):
        self._agents_dir = agents_dir
        self._cache: dict[str, AgentConfig] = {}
        self._loaded_all = False

    def get(self, agent_id: str) -> AgentConfig:
        """Get an agent by ID. Raises KeyError if not found."""
        if agent_id not in self._cache:
            try:
                self._cache[agent_id] = load_agent(agent_id, self._agents_dir)
            except FileNotFoundError:
                raise KeyError(f"Agent '{agent_id}' not found in {self._agents_dir}")
        return self._cache[agent_id]

    def list_ids(self) -> list[str]:
        """Return all available agent IDs without loading full configs."""
        ids = []
        for agent_dir in sorted(self._agents_dir.iterdir()):
            if agent_dir.is_dir() and (agent_dir / "agent.yaml").exists():
                ids.append(agent_dir.name.replace("-", "_"))
        return ids

    def list_all(self) -> dict[str, AgentConfig]:
        """Load and return all agents."""
        if not self._loaded_all:
            self._cache.update(load_all_agents(self._agents_dir))
            self._loaded_all = True
        return dict(self._cache)

    def summary(self) -> list[dict]:
        """Return a brief summary of all agents (id, name, version, status)."""
        summaries = []
        for agent_dir in sorted(self._agents_dir.iterdir()):
            if not agent_dir.is_dir():
                continue
            yaml_file = agent_dir / "agent.yaml"
            if not yaml_file.exists():
                continue
            import yaml
            with open(yaml_file) as f:
                raw = yaml.safe_load(f)
            identity = raw.get("identity", {})
            summaries.append({
                "id": identity.get("id", agent_dir.name),
                "name": identity.get("name", agent_dir.name),
                "version": identity.get("version", "?"),
                "discipline": identity.get("discipline", "?"),
            })
        return summaries
