"""Long-term project context that persists across sessions."""

from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
from typing import Any

from ..core.constants import PROJECTS_DIR


class ProjectMemory:
    """
    Per-project persistent context: run history, active run, agent decisions.

    Stored at: ~/.maestro/projects/<project_id>/context.json
    """

    def __init__(self, project_id: str, data_dir: Path = PROJECTS_DIR):
        self.project_id = project_id
        self.project_dir = data_dir / project_id
        self.context_file = self.project_dir / "context.json"
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self._ctx: dict[str, Any] = self._load()

    @property
    def active_run_id(self) -> str | None:
        return self._ctx.get("active_run_id")

    @active_run_id.setter
    def active_run_id(self, value: str | None) -> None:
        self._ctx["active_run_id"] = value
        self._save()

    def record_run(self, run_id: str, pipeline_name: str) -> None:
        """Record a new run in the project history."""
        runs = self._ctx.setdefault("runs", [])
        runs.append({
            "run_id": run_id,
            "pipeline_name": pipeline_name,
            "started_at": datetime.now(timezone.utc).isoformat(),
        })
        self._ctx["active_run_id"] = run_id
        self._save()

    def record_decision(self, agent_id: str, stage_id: str, decision: str, context: str) -> None:
        """Record a significant agent decision for future reference."""
        decisions = self._ctx.setdefault("decisions", [])
        decisions.append({
            "agent_id": agent_id,
            "stage_id": stage_id,
            "decision": decision,
            "context": context,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        })
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        return self._ctx.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._ctx[key] = value
        self._save()

    def summary(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "active_run_id": self.active_run_id,
            "total_runs": len(self._ctx.get("runs", [])),
            "total_decisions": len(self._ctx.get("decisions", [])),
        }

    def _load(self) -> dict[str, Any]:
        if self.context_file.exists():
            with open(self.context_file) as f:
                return json.load(f)
        return {"project_id": self.project_id}

    def _save(self) -> None:
        self._ctx["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.context_file, "w") as f:
            json.dump(self._ctx, f, indent=2)
