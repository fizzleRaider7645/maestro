"""Shared fixtures for Maestro tests."""

from __future__ import annotations
from pathlib import Path

import pytest

from maestro.memory.artifact_store import ArtifactStore
from maestro.core.types import (
    StageConfig,
    StageDependency,
    RunState,
    StageState,
    StageStatus,
)


@pytest.fixture
def tmp_artifact_store(tmp_path: Path) -> ArtifactStore:
    """ArtifactStore backed by a temp directory."""
    return ArtifactStore(project_id="test-project", data_dir=tmp_path)


@pytest.fixture
def simple_stage_config() -> StageConfig:
    """A stage config with no dependencies (like the design stage)."""
    return StageConfig(
        id="design",
        name="System Design",
        agent_id="system_design_architect",
        description="Produce architecture artifacts.",
        inputs=["requirements_doc"],
        outputs=["architecture_overview", "nfr_baseline"],
        depends_on=[],
    )


@pytest.fixture
def dependent_stage_config() -> StageConfig:
    """A stage config that depends on 'design' and 'input' (like implementation)."""
    return StageConfig(
        id="implementation",
        name="Software Engineering",
        agent_id="software_engineer",
        description="Implement the design.",
        inputs=["architecture_overview", "nfr_baseline"],
        outputs=["source_code", "api_contracts"],
        depends_on=[StageDependency(stage="design", condition="approved")],
    )


@pytest.fixture
def run_state_with_design(dependent_stage_config: StageConfig) -> RunState:
    """RunState that has a completed design stage and pending implementation."""
    return RunState(
        run_id="run_test",
        project_id="test-project",
        pipeline_name="SE Agent Pipeline",
        stages={
            "design": StageState(stage_id="design", status=StageStatus.APPROVED),
            "implementation": StageState(stage_id="implementation", status=StageStatus.PENDING),
        },
    )
