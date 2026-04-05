"""Reads and writes typed artifacts to the filesystem artifact store."""

from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json

from ..core.constants import PROJECTS_DIR
from ..core.types import ArtifactRef


class ArtifactStore:
    """
    Stores and retrieves agent output artifacts.

    Layout:
      ~/.maestro/projects/<project_id>/artifacts/<stage_id>/<artifact_type>.<ext>
    """

    def __init__(self, project_id: str, data_dir: Path = PROJECTS_DIR):
        self.project_id = project_id
        self.artifacts_dir = data_dir / project_id / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        stage_id: str,
        artifact_type: str,
        content: str,
        ext: str = "md",
    ) -> ArtifactRef:
        """Write artifact content to disk and return its ArtifactRef."""
        stage_dir = self.artifacts_dir / stage_id
        stage_dir.mkdir(parents=True, exist_ok=True)
        path = stage_dir / f"{artifact_type}.{ext}"
        path.write_text(content)
        return ArtifactRef(
            artifact_type=artifact_type,
            stage_id=stage_id,
            path=path,
            format=ext,
        )

    def read(self, stage_id: str, artifact_type: str) -> str | None:
        """Read artifact content. Returns None if not found."""
        for path in (self.artifacts_dir / stage_id).glob(f"{artifact_type}.*"):
            return path.read_text()
        return None

    def exists(self, stage_id: str, artifact_type: str) -> bool:
        stage_dir = self.artifacts_dir / stage_id
        if not stage_dir.exists():
            return False
        return any(stage_dir.glob(f"{artifact_type}.*"))

    def list_stage(self, stage_id: str) -> list[ArtifactRef]:
        """List all artifacts for a stage."""
        stage_dir = self.artifacts_dir / stage_id
        if not stage_dir.exists():
            return []
        refs = []
        for path in sorted(stage_dir.iterdir()):
            if path.is_file():
                refs.append(ArtifactRef(
                    artifact_type=path.stem,
                    stage_id=stage_id,
                    path=path,
                    format=path.suffix.lstrip("."),
                ))
        return refs

    def list_all(self) -> dict[str, list[ArtifactRef]]:
        """List all artifacts across all stages."""
        result: dict[str, list[ArtifactRef]] = {}
        if not self.artifacts_dir.exists():
            return result
        for stage_dir in sorted(self.artifacts_dir.iterdir()):
            if stage_dir.is_dir():
                result[stage_dir.name] = self.list_stage(stage_dir.name)
        return result

    def get_ref(self, stage_id: str, artifact_type: str) -> ArtifactRef | None:
        """Get an ArtifactRef without reading the content."""
        stage_dir = self.artifacts_dir / stage_id
        if not stage_dir.exists():
            return None
        for path in stage_dir.glob(f"{artifact_type}.*"):
            return ArtifactRef(
                artifact_type=artifact_type,
                stage_id=stage_id,
                path=path,
                format=path.suffix.lstrip("."),
            )
        return None
