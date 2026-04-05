"""Builtin artifact store skills: read_artifact, write_artifact, list_artifacts."""

from __future__ import annotations
from typing import Any

from ..skill_base import Skill


class ReadArtifactTool(Skill):
    id = "read_artifact"
    description = "Read a stored artifact by type and stage from the current project's artifact store."

    def __init__(self, project_id: str | None = None):
        self._project_id = project_id

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "Pipeline stage that produced the artifact (e.g., 'design', 'implementation').",
                },
                "artifact_type": {
                    "type": "string",
                    "description": "Artifact type (e.g., 'architecture_overview', 'nfr_baseline').",
                },
            },
            "required": ["stage_id", "artifact_type"],
        }

    def invoke(self, stage_id: str, artifact_type: str, **_: Any) -> str:
        if not self._project_id:
            raise ValueError("No project_id set — cannot read artifacts.")
        from ...memory.artifact_store import ArtifactStore
        store = ArtifactStore(self._project_id)
        content = store.read(stage_id, artifact_type)
        if content is None:
            return f"Artifact not found: {stage_id}/{artifact_type}"
        return content


class WriteArtifactTool(Skill):
    id = "write_artifact"
    description = "Write an artifact to the current project's artifact store."

    def __init__(self, project_id: str | None = None):
        self._project_id = project_id

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "Pipeline stage this artifact belongs to.",
                },
                "artifact_type": {
                    "type": "string",
                    "description": "Artifact type (e.g., 'architecture_overview').",
                },
                "content": {
                    "type": "string",
                    "description": "Content to store.",
                },
                "ext": {
                    "type": "string",
                    "description": "File extension (default: 'md').",
                    "default": "md",
                },
            },
            "required": ["stage_id", "artifact_type", "content"],
        }

    def invoke(self, stage_id: str, artifact_type: str, content: str, ext: str = "md", **_: Any) -> str:
        if not self._project_id:
            raise ValueError("No project_id set — cannot write artifacts.")
        from ...memory.artifact_store import ArtifactStore
        store = ArtifactStore(self._project_id)
        ref = store.write(stage_id, artifact_type, content, ext=ext)
        return f"Artifact written: {ref.path}"


class ListArtifactsTool(Skill):
    id = "list_artifacts"
    description = "List all artifacts available in the current project's artifact store."

    def __init__(self, project_id: str | None = None):
        self._project_id = project_id

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "properties": {
                "stage_id": {
                    "type": "string",
                    "description": "Optional stage to filter by. Omit to list all stages.",
                }
            },
            "required": [],
        }

    def invoke(self, stage_id: str | None = None, **_: Any) -> str:
        if not self._project_id:
            raise ValueError("No project_id set — cannot list artifacts.")
        from ...memory.artifact_store import ArtifactStore
        store = ArtifactStore(self._project_id)
        if stage_id:
            refs = store.list_stage(stage_id)
            lines = [f"  {r.artifact_type} ({r.format})" for r in refs]
            return f"{stage_id}:\n" + ("\n".join(lines) if lines else "  (none)")
        all_artifacts = store.list_all()
        output = []
        for sid, refs in all_artifacts.items():
            output.append(f"{sid}:")
            for r in refs:
                output.append(f"  {r.artifact_type} ({r.format})")
        return "\n".join(output) if output else "(no artifacts)"
