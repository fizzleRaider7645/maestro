"""Loads an agent definition from agent.yaml + persona.md into an AgentConfig."""

from __future__ import annotations
from pathlib import Path

import yaml

from .types import (
    AgentConfig,
    Discipline,
    Tone,
    Verbosity,
    ReasoningStyle,
    IOSpec,
    TriggerCondition,
    HandoffConfig,
    ConstraintsConfig,
    EvaluationConfig,
    RuntimeConfig,
)
from .constants import AGENTS_DIR


def load_agent(agent_id: str, agents_dir: Path = AGENTS_DIR) -> AgentConfig:
    """Load a single agent by ID from its agent.yaml + persona.md pair."""
    agent_dir = agents_dir / agent_id.replace("_", "-")
    if not agent_dir.exists():
        # Try underscore-named directory too
        agent_dir = agents_dir / agent_id
    if not agent_dir.exists():
        raise FileNotFoundError(
            f"Agent directory not found for '{agent_id}' in {agents_dir}. "
            f"Expected: {agents_dir}/{agent_id.replace('_', '-')}/"
        )

    yaml_file = agent_dir / "agent.yaml"
    if not yaml_file.exists():
        raise FileNotFoundError(f"agent.yaml not found at {yaml_file}")

    with open(yaml_file) as f:
        raw = yaml.safe_load(f)

    return _parse_agent_config(raw, agent_dir)


def load_all_agents(agents_dir: Path = AGENTS_DIR) -> dict[str, AgentConfig]:
    """Load all agents found in the agents directory."""
    agents: dict[str, AgentConfig] = {}
    for agent_dir in sorted(agents_dir.iterdir()):
        if not agent_dir.is_dir():
            continue
        yaml_file = agent_dir / "agent.yaml"
        if not yaml_file.exists():
            continue
        with open(yaml_file) as f:
            raw = yaml.safe_load(f)
        agent_id = raw.get("identity", {}).get("id", agent_dir.name.replace("-", "_"))
        agents[agent_id] = _parse_agent_config(raw, agent_dir)
    return agents


def _parse_agent_config(raw: dict, agent_dir: Path) -> AgentConfig:
    identity = raw.get("identity", {})
    behavior = raw.get("behavior", {})
    caps = raw.get("capabilities", {})
    io = raw.get("io", {})
    handoffs_raw = raw.get("handoffs", {})
    constraints_raw = raw.get("constraints", {})
    evaluation_raw = raw.get("evaluation", {})
    runtime_raw = raw.get("runtime", {})

    # Load persona.md as system prompt
    persona_rel = identity.get("persona_file", "./persona.md")
    persona_path = (agent_dir / persona_rel).resolve()
    system_prompt = ""
    if persona_path.exists():
        system_prompt = persona_path.read_text()

    # Parse IO specs
    accepts = [
        IOSpec(
            type=item["type"],
            format=item.get("format", "text"),
            required=item.get("required", False),
        )
        for item in io.get("accepts", [])
    ]
    produces = [
        IOSpec(
            type=item["type"],
            format=item.get("format", "text"),
            schema_ref=item.get("schema_ref"),
        )
        for item in io.get("produces", [])
    ]

    # Parse handoffs
    trigger_conditions = [
        TriggerCondition(
            condition=t["condition"],
            to=t["to"],
            payload=t.get("payload", []),
        )
        for t in handoffs_raw.get("trigger_conditions", [])
    ]
    handoffs = HandoffConfig(
        upstream=handoffs_raw.get("upstream", []),
        downstream=handoffs_raw.get("downstream", []),
        trigger_conditions=trigger_conditions,
    )

    # Parse constraints
    constraints = ConstraintsConfig(
        scope_limits=constraints_raw.get("scope_limits", []),
        escalation_triggers=constraints_raw.get("escalation_triggers", []),
        confidence_threshold=float(constraints_raw.get("confidence_threshold", 0.75)),
    )

    # Parse evaluation
    evaluation = EvaluationConfig(
        success_criteria=evaluation_raw.get("success_criteria", []),
        self_check_prompts=evaluation_raw.get("self_check_prompts", []),
        review_checklist=evaluation_raw.get("review_checklist", []),
    )

    # Parse runtime overrides
    runtime = RuntimeConfig(
        model=runtime_raw.get("model"),
        tool_allowlist=runtime_raw.get("tool_allowlist"),
        max_turns=int(runtime_raw.get("max_turns", 10)),
    )

    return AgentConfig(
        id=identity.get("id", ""),
        name=identity.get("name", ""),
        version=identity.get("version", "0.1.0"),
        discipline=Discipline(identity.get("discipline", "software_engineering")),
        role=identity.get("role", ""),
        persona_file=persona_path,
        tone=Tone(behavior.get("tone", "pragmatic")),
        verbosity=Verbosity(behavior.get("verbosity", "balanced")),
        reasoning_style=ReasoningStyle(behavior.get("reasoning_style", "pattern_matching")),
        primary_capabilities=caps.get("primary", []),
        secondary_capabilities=caps.get("secondary", []),
        anti_patterns=caps.get("anti_patterns", []),
        accepts=accepts,
        produces=produces,
        handoffs=handoffs,
        constraints=constraints,
        evaluation=evaluation,
        runtime=runtime,
        system_prompt=system_prompt,
    )
