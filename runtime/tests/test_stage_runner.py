"""Tests for StageRunner._gather_context and _build_task_message."""

from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from maestro.memory.artifact_store import ArtifactStore
from maestro.orchestration.stage_runner import StageRunner
from maestro.core.types import (
    StageConfig,
    StageDependency,
    RunState,
    StageState,
    StageStatus,
)


def _make_runner(artifact_store: ArtifactStore) -> StageRunner:
    return StageRunner(
        agent_registry=MagicMock(),
        skill_registry=MagicMock(),
        artifact_store=artifact_store,
        run_manager=MagicMock(),
    )


def _make_impl_stage() -> StageConfig:
    return StageConfig(
        id="implementation",
        name="Software Engineering",
        agent_id="software_engineer",
        description="Implement the design.",
        inputs=["architecture_overview", "nfr_baseline"],
        outputs=["source_code"],
        depends_on=[StageDependency(stage="design", condition="approved")],
    )


def _make_run_state() -> RunState:
    return RunState(
        run_id="run_test",
        project_id="test-project",
        pipeline_name="SE Agent Pipeline",
        stages={
            "design": StageState(stage_id="design", status=StageStatus.APPROVED),
            "implementation": StageState(stage_id="implementation", status=StageStatus.PENDING),
        },
    )


class TestGatherContext:
    def test_falls_back_to_primary_output_when_no_typed_artifact(
        self, tmp_artifact_store: ArtifactStore
    ) -> None:
        """If no typed artifact exists, primary_output from the dep stage is included."""
        tmp_artifact_store.write("design", "primary_output", "# Full design output", ext="md")

        runner = _make_runner(tmp_artifact_store)
        context = runner._gather_context(_make_impl_stage(), _make_run_state())

        assert "design_output" in context
        assert context["design_output"] == "# Full design output"

    def test_typed_artifact_takes_precedence_over_primary_output(
        self, tmp_artifact_store: ArtifactStore
    ) -> None:
        """When a typed artifact exists, it replaces the fallback key."""
        tmp_artifact_store.write("design", "primary_output", "# Full design output", ext="md")
        tmp_artifact_store.write("design", "architecture_overview", "# Architecture", ext="md")

        runner = _make_runner(tmp_artifact_store)
        context = runner._gather_context(_make_impl_stage(), _make_run_state())

        # Typed artifact present under its own key
        assert context["architecture_overview"] == "# Architecture"
        # Fallback still included for other outputs from the same stage
        assert "design_output" in context

    def test_scoped_to_dependency_stages_only(
        self, tmp_artifact_store: ArtifactStore
    ) -> None:
        """Artifacts from stages NOT in depends_on are excluded."""
        # Write an artifact for a non-dependent stage
        tmp_artifact_store.write("deployment", "primary_output", "# Deploy output", ext="md")
        tmp_artifact_store.write("design", "primary_output", "# Design output", ext="md")

        runner = _make_runner(tmp_artifact_store)
        context = runner._gather_context(_make_impl_stage(), _make_run_state())

        assert "deployment_output" not in context
        assert "design_output" in context

    def test_input_stage_artifacts_always_included(
        self, tmp_artifact_store: ArtifactStore
    ) -> None:
        """The 'input' stage (requirements) is always in scope regardless of depends_on."""
        tmp_artifact_store.write("input", "primary_output", "# Requirements", ext="md")

        runner = _make_runner(tmp_artifact_store)
        context = runner._gather_context(_make_impl_stage(), _make_run_state())

        assert "input_output" in context
        assert context["input_output"] == "# Requirements"

    def test_empty_context_when_no_artifacts_exist(
        self, tmp_artifact_store: ArtifactStore
    ) -> None:
        """Returns empty dict when no artifacts have been written yet."""
        runner = _make_runner(tmp_artifact_store)
        context = runner._gather_context(_make_impl_stage(), _make_run_state())
        assert context == {}

    def test_multiple_dep_stages(self, tmp_artifact_store: ArtifactStore) -> None:
        """Artifacts from all dep stages are gathered."""
        stage = StageConfig(
            id="deployment",
            name="DevOps",
            agent_id="devops_engineer",
            description="Deploy.",
            inputs=["test_results", "architecture_overview"],
            outputs=["infrastructure_as_code"],
            depends_on=[
                StageDependency(stage="design", condition="approved"),
                StageDependency(stage="testing", condition="quality_gate_passed"),
            ],
        )
        run_state = RunState(
            run_id="run_test",
            project_id="test-project",
            pipeline_name="SE Agent Pipeline",
            stages={
                "design": StageState(stage_id="design", status=StageStatus.APPROVED),
                "testing": StageState(stage_id="testing", status=StageStatus.APPROVED),
                "deployment": StageState(stage_id="deployment", status=StageStatus.PENDING),
            },
        )

        tmp_artifact_store.write("design", "primary_output", "# Design", ext="md")
        tmp_artifact_store.write("testing", "primary_output", "# Test results", ext="md")

        runner = _make_runner(tmp_artifact_store)
        context = runner._gather_context(stage, run_state)

        assert "design_output" in context
        assert "testing_output" in context


class TestBuildTaskMessage:
    def test_includes_stage_name(self, tmp_artifact_store: ArtifactStore) -> None:
        runner = _make_runner(tmp_artifact_store)
        msg = runner._build_task_message(_make_impl_stage(), {})
        assert "Software Engineering" in msg

    def test_includes_context_artifacts(self, tmp_artifact_store: ArtifactStore) -> None:
        runner = _make_runner(tmp_artifact_store)
        context = {"architecture_overview": "# Arch overview content"}
        msg = runner._build_task_message(_make_impl_stage(), context)
        assert "architecture_overview" in msg
        assert "Arch overview content" in msg

    def test_long_content_is_truncated(self, tmp_artifact_store: ArtifactStore) -> None:
        runner = _make_runner(tmp_artifact_store)
        long_content = "x" * 600
        context = {"architecture_overview": long_content}
        msg = runner._build_task_message(_make_impl_stage(), context)
        assert "..." in msg
        # Should not include the full 600 chars
        assert "x" * 600 not in msg
