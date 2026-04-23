"""Skill: read or update persistent KPI data for a rental property."""

from __future__ import annotations
import datetime
import json
from typing import Any

from maestro.skills.skill_base import Skill


class UpdatePropertyKpisSkill(Skill):
    id = "update_property_kpis"
    description = (
        "Read or update persistent KPI data for a rental property. "
        "Use mode='read' to retrieve current KPIs, mode='update' to merge new values, "
        "mode='list' to see all tracked property IDs."
    )

    def __init__(self, project_id: str | None = None):
        self._project_id = project_id

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["read", "update", "list"],
                    "description": "'read' returns current KPIs for a property, 'update' merges new values, 'list' shows all tracked property IDs.",
                },
                "property_id": {
                    "type": "string",
                    "description": "Unique identifier for the property (e.g., '123-main-st'). Required for read and update modes.",
                },
                "updates": {
                    "type": "object",
                    "description": "Key-value pairs to merge into the property's KPI record. Required for mode='update'.",
                },
            },
            "required": ["mode"],
        }

    def invoke(
        self,
        mode: str,
        property_id: str | None = None,
        updates: dict | None = None,
        **_: Any,
    ) -> str:
        if not self._project_id:
            raise ValueError(
                "No project_id available — cannot persist KPIs. Use the --project flag when invoking the agent."
            )

        from maestro.memory.project_memory import ProjectMemory
        mem = ProjectMemory(self._project_id)
        kpis: dict[str, Any] = mem.get("property_kpis", {"properties": {}})

        if mode == "list":
            ids = list(kpis.get("properties", {}).keys())
            return f"Tracked properties: {', '.join(ids)}" if ids else "No properties tracked yet."

        if not property_id:
            raise ValueError("property_id is required for mode='read' and mode='update'.")

        if mode == "read":
            data = kpis.get("properties", {}).get(property_id)
            if data is None:
                return f"No KPIs found for '{property_id}'. Run an intake first."
            return json.dumps(data, indent=2)

        if mode == "update":
            if not updates:
                raise ValueError("'updates' dict is required for mode='update'.")
            props: dict[str, Any] = kpis.setdefault("properties", {})
            record: dict[str, Any] = props.setdefault(property_id, {})
            record.update(updates)
            record["last_updated"] = datetime.date.today().isoformat()
            mem.set("property_kpis", kpis)
            return f"KPIs updated for '{property_id}'. Fields: {', '.join(str(k) for k in updates.keys())}"

        raise ValueError(f"Unknown mode: '{mode}'. Use 'read', 'update', or 'list'.")
