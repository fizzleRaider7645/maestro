"""Loads pipeline.yaml into a PipelineConfig."""

from __future__ import annotations
from pathlib import Path

import yaml

from .types import (
    PipelineConfig,
    StageConfig,
    StageDependency,
    GateConfig,
    GateType,
    FeedbackLoop,
)
from .constants import PIPELINE_FILE


def load_pipeline(pipeline_file: Path = PIPELINE_FILE) -> PipelineConfig:
    """Load the pipeline definition from pipeline.yaml."""
    if not pipeline_file.exists():
        raise FileNotFoundError(f"Pipeline file not found: {pipeline_file}")

    with open(pipeline_file) as f:
        raw = yaml.safe_load(f)

    return _parse_pipeline(raw)


def _parse_pipeline(raw: dict) -> PipelineConfig:
    stages = [_parse_stage(s) for s in raw.get("stages", [])]
    feedback_loops = [_parse_feedback_loop(fl) for fl in raw.get("feedback_loops", [])]
    escalation = raw.get("escalation", {}).get("immediate_human_review", [])

    return PipelineConfig(
        pipeline_version=raw.get("pipeline_version", "1.0.0"),
        name=raw.get("name", ""),
        description=raw.get("description", ""),
        stages=stages,
        feedback_loops=feedback_loops,
        escalation_triggers=escalation,
        agent_registry=raw.get("agent_registry", []),
    )


def _parse_stage(raw: dict) -> StageConfig:
    gate_raw = raw.get("gate")
    gate = _parse_gate(gate_raw) if gate_raw else None

    depends_on = [
        StageDependency(stage=d["stage"], condition=d["condition"])
        for d in raw.get("depends_on", [])
    ]

    return StageConfig(
        id=raw["id"],
        name=raw.get("name", raw["id"]),
        agent_id=raw.get("agent", ""),
        description=raw.get("description", ""),
        inputs=raw.get("inputs", []),
        outputs=raw.get("outputs", []),
        depends_on=depends_on,
        gate=gate,
    )


def _parse_gate(raw: dict) -> GateConfig:
    gate_type_str = raw.get("type", "human_approval")
    # Map pipeline.yaml type names to GateType enum
    type_map = {
        "human_approval": GateType.HUMAN_APPROVAL,
        "peer_review": GateType.PEER_REVIEW,
        "automated_plus_human": GateType.AUTOMATED_PLUS_HUMAN,
        "automated_only": GateType.AUTOMATED_ONLY,
    }
    gate_type = type_map.get(gate_type_str, GateType.HUMAN_APPROVAL)

    on_reject = raw.get("on_reject", {})

    return GateConfig(
        type=gate_type,
        approver=raw.get("approver"),
        reviewer=raw.get("reviewer"),
        approval_criteria=raw.get("approval_criteria", []),
        automated_criteria=raw.get("automated_criteria", []),
        human_approval_required=raw.get("human_approval_required", False),
        on_reject_action=on_reject.get("action", "revise"),
        on_reject_return_to=on_reject.get("return_to", ""),
        on_reject_with_feedback=on_reject.get("with_feedback", True),
    )


def _parse_feedback_loop(raw: dict) -> FeedbackLoop:
    return FeedbackLoop(
        id=raw.get("id", ""),
        trigger=raw.get("trigger", ""),
        from_agent=raw.get("from", ""),
        to_agent=raw.get("to", ""),
        payload=raw.get("payload", []),
        outcome=raw.get("outcome", ""),
    )
