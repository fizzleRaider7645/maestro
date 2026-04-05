"""Scaffolds a new skill directory with skill.yaml + skill.py stubs."""

from __future__ import annotations
import sys
from pathlib import Path

# Skills live at project root /skills/, not inside agent-builder
SKILLS_DIR = Path(__file__).parent.parent.parent.parent / "skills"


def scaffold_skill(skill_id: str, skills_dir: Path = SKILLS_DIR) -> None:
    """
    Create a new skill directory with skill.yaml and skill.py stubs.
    """
    skill_dir = skills_dir / skill_id

    if skill_dir.exists():
        print(f"Error: skill directory already exists: {skill_dir}")
        sys.exit(1)

    skill_dir.mkdir(parents=True)

    # Write skill.yaml
    yaml_content = f"""\
# =============================================================================
# skill.yaml — {skill_id}
# Schema: agent-builder/v1 (skill)
# =============================================================================

id: {skill_id}
name: "{skill_id.replace('_', ' ').title()}"
description: "TODO: One-sentence description of what this skill does."
version: "0.1.0"
category: custom   # filesystem | artifact | network | code | custom

parameters:
  - name: input_param
    type: string
    description: "TODO: Description of this parameter."
    required: true

permissions:
  - custom   # filesystem_read | filesystem_write | network | code_exec | custom

allowed_agents:
  - "*"      # Allow all agents, or list specific agent IDs
"""

    (skill_dir / "skill.yaml").write_text(yaml_content)

    # Write skill.py
    py_content = f"""\
\"\"\"
{skill_id} — Maestro skill implementation.

This file is auto-loaded by the SkillRegistry when placed in the skills/ directory.
Implement the `invoke()` method and update `parameters_schema` to match skill.yaml.
\"\"\"

from __future__ import annotations
from typing import Any

# The SkillRegistry will discover any class that subclasses Skill
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'runtime'))

from maestro.skills.skill_base import Skill


class {_to_class_name(skill_id)}(Skill):
    id = "{skill_id}"
    description = "TODO: One-sentence description of what this skill does."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {{
            "properties": {{
                "input_param": {{
                    "type": "string",
                    "description": "TODO: Description of this parameter.",
                }},
            }},
            "required": ["input_param"],
        }}

    def invoke(self, input_param: str, **kwargs: Any) -> str:
        \"\"\"
        Execute the skill. Return a string result to be passed back to the agent.

        Raise ValueError for invalid inputs.
        Raise RuntimeError for execution failures.
        \"\"\"
        # TODO: Implement skill logic
        return f"TODO: {skill_id} received: {{input_param}}"
"""

    (skill_dir / "skill.py").write_text(py_content)

    print(f"Scaffolded skill: {skill_dir}")
    print(f"\nNext steps:")
    print(f"  1. Edit {skill_dir}/skill.yaml — fill in parameters and permissions")
    print(f"  2. Edit {skill_dir}/skill.py — implement the invoke() method")
    print(f"  3. Run: maestro list skills — to confirm it's registered")


def _to_class_name(skill_id: str) -> str:
    return "".join(word.capitalize() for word in skill_id.split("_")) + "Skill"
