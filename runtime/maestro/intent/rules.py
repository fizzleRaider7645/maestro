"""Deterministic routing rules — applied before LLM-based routing."""

from __future__ import annotations
import re

from ..core.types import RoutingDecision


# Known agent ID aliases (including common shorthand)
_AGENT_ALIASES: dict[str, str] = {
    "architect": "system_design_architect",
    "design": "system_design_architect",
    "sda": "system_design_architect",
    "engineer": "software_engineer",
    "dev": "software_engineer",
    "swe": "software_engineer",
    "qa": "qa_engineer",
    "tester": "qa_engineer",
    "devops": "devops_engineer",
    "infra": "devops_engineer",
    "ops": "devops_engineer",
}

# Known artifact types → producing stage
_ARTIFACT_TO_STAGE: dict[str, str] = {
    "architecture_overview": "design",
    "component_diagram": "design",
    "nfr_baseline": "design",
    "adr": "design",
    "tech_stack_recommendation": "design",
    "risk_register": "design",
    "source_code": "implementation",
    "api_contracts": "implementation",
    "unit_tests": "implementation",
    "test_strategy": "testing",
    "test_plan": "testing",
    "test_results": "testing",
    "infrastructure_as_code": "deployment",
    "deployment_runbook": "deployment",
    "cicd_pipeline_definition": "deployment",
}

# Stage keywords → stage_id
_STAGE_KEYWORDS: dict[str, str] = {
    "design": "design",
    "architecture": "design",
    "implement": "implementation",
    "implementation": "implementation",
    "code": "implementation",
    "test": "testing",
    "testing": "testing",
    "qa": "testing",
    "deploy": "deployment",
    "deployment": "deployment",
    "infra": "deployment",
    "infrastructure": "deployment",
}


def apply_rules(text: str, known_agent_ids: list[str]) -> RoutingDecision | None:
    """
    Try to resolve routing deterministically from the text.
    Returns None if no rule matches (fall through to LLM routing).
    """
    text_lower = text.lower()

    # Rule 1: Exact agent ID in text
    for agent_id in known_agent_ids:
        if agent_id in text_lower or agent_id.replace("_", " ") in text_lower:
            return RoutingDecision(agent_id=agent_id, confidence=1.0, reasoning=f"Exact agent ID match: {agent_id}")

    # Rule 2: Known agent aliases
    for alias, agent_id in _AGENT_ALIASES.items():
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, text_lower):
            return RoutingDecision(agent_id=agent_id, confidence=0.9, reasoning=f"Alias match: {alias} → {agent_id}")

    # Rule 3: Known artifact type → route to producing stage
    for artifact_type, stage_id in _ARTIFACT_TO_STAGE.items():
        if artifact_type.replace("_", " ") in text_lower or artifact_type in text_lower:
            return RoutingDecision(stage_id=stage_id, confidence=0.85, reasoning=f"Artifact type match: {artifact_type} → stage {stage_id}")

    # Rule 4: Stage keyword
    for keyword, stage_id in _STAGE_KEYWORDS.items():
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, text_lower):
            return RoutingDecision(stage_id=stage_id, confidence=0.8, reasoning=f"Stage keyword match: {keyword} → {stage_id}")

    # Rule 5: "run pipeline" / "start pipeline"
    if re.search(r"\b(run|start|begin|kick off)\b.*\b(pipeline|workflow|project)\b", text_lower):
        return RoutingDecision(pipeline_id="se-pipeline", confidence=0.95, reasoning="Pipeline start intent")

    return None
