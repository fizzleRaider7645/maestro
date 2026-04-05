"""Validates agent.yaml and skill.yaml files against their schemas."""

from __future__ import annotations
from pathlib import Path
from typing import Any

import yaml

from .constants import AGENT_SCHEMA_FILE, SKILL_SCHEMA_FILE, AGENTS_DIR


def validate_agent(agent_yaml_path: Path) -> list[str]:
    """
    Validate an agent.yaml file. Returns a list of error messages.
    An empty list means the file is valid.
    """
    if not agent_yaml_path.exists():
        return [f"File not found: {agent_yaml_path}"]

    with open(agent_yaml_path) as f:
        raw = yaml.safe_load(f)

    errors: list[str] = []
    errors.extend(_check_required_section(raw, "identity", ["id", "name", "version", "discipline", "role", "persona_file"]))
    errors.extend(_check_required_section(raw, "behavior", ["tone", "verbosity", "reasoning_style"]))
    errors.extend(_check_section_exists(raw, "capabilities"))
    errors.extend(_check_section_exists(raw, "io"))
    errors.extend(_check_section_exists(raw, "handoffs"))
    errors.extend(_check_section_exists(raw, "constraints"))
    errors.extend(_check_section_exists(raw, "evaluation"))

    # Validate enum values
    valid_tones = {"analytical", "collaborative", "pragmatic", "critical"}
    valid_verbosities = {"concise", "balanced", "thorough"}
    valid_reasoning = {"first_principles", "pattern_matching", "trade_off_analysis", "hypothesis_driven"}
    valid_disciplines = {"system_design", "software_engineering", "testing_qa", "devops_infra"}

    behavior = raw.get("behavior", {})
    if behavior.get("tone") and behavior["tone"] not in valid_tones:
        errors.append(f"behavior.tone must be one of {valid_tones}, got '{behavior['tone']}'")
    if behavior.get("verbosity") and behavior["verbosity"] not in valid_verbosities:
        errors.append(f"behavior.verbosity must be one of {valid_verbosities}")
    if behavior.get("reasoning_style") and behavior["reasoning_style"] not in valid_reasoning:
        errors.append(f"behavior.reasoning_style must be one of {valid_reasoning}")

    identity = raw.get("identity", {})
    if identity.get("discipline") and identity["discipline"] not in valid_disciplines:
        errors.append(f"identity.discipline must be one of {valid_disciplines}")

    # Validate confidence threshold
    constraints = raw.get("constraints", {})
    threshold = constraints.get("confidence_threshold")
    if threshold is not None:
        try:
            val = float(threshold)
            if not 0.0 <= val <= 1.0:
                errors.append(f"constraints.confidence_threshold must be between 0.0 and 1.0, got {val}")
        except (TypeError, ValueError):
            errors.append(f"constraints.confidence_threshold must be a float, got {threshold!r}")

    return errors


def validate_all_agents(agents_dir: Path = AGENTS_DIR) -> dict[str, list[str]]:
    """
    Validate all agent.yaml files in the agents directory.
    Returns a dict of agent_id → list of errors.
    """
    results: dict[str, list[str]] = {}
    for agent_dir in sorted(agents_dir.iterdir()):
        if not agent_dir.is_dir():
            continue
        yaml_file = agent_dir / "agent.yaml"
        if not yaml_file.exists():
            continue
        errors = validate_agent(yaml_file)
        agent_id = agent_dir.name
        results[agent_id] = errors
    return results


def validate_skill(skill_yaml_path: Path) -> list[str]:
    """Validate a skill.yaml file. Returns list of error messages."""
    if not skill_yaml_path.exists():
        return [f"File not found: {skill_yaml_path}"]

    with open(skill_yaml_path) as f:
        raw = yaml.safe_load(f)

    errors: list[str] = []
    errors.extend(_check_required_section(raw, None, ["id", "name", "description"], root=True))
    errors.extend(_check_section_exists(raw, "parameters"))

    return errors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_required_section(
    raw: dict, section: str | None, required_fields: list[str], root: bool = False
) -> list[str]:
    errors = []
    data = raw if root else raw.get(section, {})
    if not root and section not in raw:
        errors.append(f"Missing required section: '{section}'")
        return errors
    for field in required_fields:
        if field not in data or data[field] is None:
            prefix = "" if root else f"{section}."
            errors.append(f"Missing required field: '{prefix}{field}'")
    return errors


def _check_section_exists(raw: dict, section: str) -> list[str]:
    if section not in raw:
        return [f"Missing required section: '{section}'"]
    return []
