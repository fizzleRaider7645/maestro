"""Core dataclasses shared across the Maestro runtime."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Enums matching agent.schema.yaml
# ---------------------------------------------------------------------------

class Tone(str, Enum):
    ANALYTICAL = "analytical"
    COLLABORATIVE = "collaborative"
    PRAGMATIC = "pragmatic"
    CRITICAL = "critical"


class Verbosity(str, Enum):
    CONCISE = "concise"
    BALANCED = "balanced"
    THOROUGH = "thorough"


class ReasoningStyle(str, Enum):
    FIRST_PRINCIPLES = "first_principles"
    PATTERN_MATCHING = "pattern_matching"
    TRADE_OFF_ANALYSIS = "trade_off_analysis"
    HYPOTHESIS_DRIVEN = "hypothesis_driven"


class Discipline(str, Enum):
    SYSTEM_DESIGN = "system_design"
    SOFTWARE_ENGINEERING = "software_engineering"
    TESTING_QA = "testing_qa"
    DEVOPS_INFRA = "devops_infra"


class GateType(str, Enum):
    HUMAN_APPROVAL = "human_approval"
    PEER_REVIEW = "peer_review"
    AUTOMATED_PLUS_HUMAN = "automated_plus_human"
    AUTOMATED_ONLY = "automated_only"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_GATE = "awaiting_gate"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class GateStatus(str, Enum):
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Agent configuration (loaded from agent.yaml + persona.md)
# ---------------------------------------------------------------------------

@dataclass
class IOSpec:
    type: str
    format: str
    required: bool = False
    schema_ref: str | None = None


@dataclass
class TriggerCondition:
    condition: str
    to: str
    payload: list[str] = field(default_factory=list)


@dataclass
class HandoffConfig:
    upstream: list[str] = field(default_factory=list)
    downstream: list[str] = field(default_factory=list)
    trigger_conditions: list[TriggerCondition] = field(default_factory=list)


@dataclass
class ConstraintsConfig:
    scope_limits: list[str] = field(default_factory=list)
    escalation_triggers: list[str] = field(default_factory=list)
    confidence_threshold: float = 0.75


@dataclass
class EvaluationConfig:
    success_criteria: list[str] = field(default_factory=list)
    self_check_prompts: list[str] = field(default_factory=list)
    review_checklist: list[str] = field(default_factory=list)


@dataclass
class RuntimeConfig:
    model: str | None = None
    tool_allowlist: list[str] | None = None  # None = all skills allowed
    max_turns: int = 10


@dataclass
class AgentConfig:
    """Full agent definition loaded from agent.yaml + persona.md."""
    # Identity
    id: str
    name: str
    version: str
    discipline: Discipline
    role: str
    persona_file: Path

    # Behavior
    tone: Tone
    verbosity: Verbosity
    reasoning_style: ReasoningStyle

    # Capabilities
    primary_capabilities: list[str] = field(default_factory=list)
    secondary_capabilities: list[str] = field(default_factory=list)
    anti_patterns: list[str] = field(default_factory=list)

    # IO
    accepts: list[IOSpec] = field(default_factory=list)
    produces: list[IOSpec] = field(default_factory=list)

    # Handoffs
    handoffs: HandoffConfig = field(default_factory=HandoffConfig)

    # Constraints
    constraints: ConstraintsConfig = field(default_factory=ConstraintsConfig)

    # Evaluation
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)

    # Runtime
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

    # The full persona.md content used as system prompt
    system_prompt: str = ""


# ---------------------------------------------------------------------------
# Pipeline configuration (loaded from pipeline.yaml)
# ---------------------------------------------------------------------------

@dataclass
class GateConfig:
    type: GateType
    approver: str | None = None
    reviewer: str | None = None
    approval_criteria: list[str] = field(default_factory=list)
    automated_criteria: list[str] = field(default_factory=list)
    human_approval_required: bool = False
    on_reject_action: str = "revise"
    on_reject_return_to: str = ""
    on_reject_with_feedback: bool = True


@dataclass
class StageDependency:
    stage: str
    condition: str


@dataclass
class StageConfig:
    id: str
    name: str
    agent_id: str
    description: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    depends_on: list[StageDependency] = field(default_factory=list)
    gate: GateConfig | None = None


@dataclass
class FeedbackLoop:
    id: str
    trigger: str
    from_agent: str
    to_agent: str
    payload: list[str] = field(default_factory=list)
    outcome: str = ""


@dataclass
class PipelineConfig:
    pipeline_version: str
    name: str
    description: str
    stages: list[StageConfig] = field(default_factory=list)
    feedback_loops: list[FeedbackLoop] = field(default_factory=list)
    escalation_triggers: list[str] = field(default_factory=list)
    agent_registry: list[dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Runtime state (tracks a live pipeline execution)
# ---------------------------------------------------------------------------

@dataclass
class ArtifactRef:
    """Typed pointer to an artifact stored on the filesystem."""
    artifact_type: str
    stage_id: str
    path: Path
    format: str = ""


@dataclass
class GateState:
    gate_id: str
    stage_id: str
    gate_type: GateType
    status: GateStatus = GateStatus.OPEN
    evaluator_report: str | None = None
    rejection_feedback: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class StageState:
    stage_id: str
    status: StageStatus = StageStatus.PENDING
    artifacts: list[ArtifactRef] = field(default_factory=list)
    gate: GateState | None = None
    revision_count: int = 0
    error: str | None = None


@dataclass
class RunState:
    """Complete state of a pipeline run, persisted to disk."""
    run_id: str
    project_id: str
    pipeline_name: str
    stages: dict[str, StageState] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    completed: bool = False


# ---------------------------------------------------------------------------
# Handoff (agent output package passed between agents)
# ---------------------------------------------------------------------------

@dataclass
class Handoff:
    """Typed transfer package between agents."""
    from_agent: str
    to_agent: str
    trigger: str
    artifacts: dict[str, ArtifactRef] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    open_questions: list[str] = field(default_factory=list)
    raw_output: str = ""


# ---------------------------------------------------------------------------
# Intent routing
# ---------------------------------------------------------------------------

@dataclass
class IntentRequest:
    """A natural language request from the user."""
    text: str
    project_id: str | None = None
    run_id: str | None = None


@dataclass
class RoutingDecision:
    """Resolved routing for an intent request."""
    pipeline_id: str | None = None
    stage_id: str | None = None
    agent_id: str | None = None
    confidence: float = 1.0
    reasoning: str = ""
    requires_clarification: bool = False
    clarification_prompt: str = ""
