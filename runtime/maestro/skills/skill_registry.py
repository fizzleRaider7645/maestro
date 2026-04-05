"""Discovers and indexes all skills; builds Anthropic tool_definitions lists."""

from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
from typing import Any

from .skill_base import Skill
from .builtin.file_ops import ReadFileTool, WriteFileTool, ListDirTool
from .builtin.artifact_store import ReadArtifactTool, WriteArtifactTool, ListArtifactsTool


# Built-in skills that ship with the runtime
_BUILTIN_SKILLS: list[type[Skill]] = [
    ReadFileTool,
    WriteFileTool,
    ListDirTool,
    ReadArtifactTool,
    WriteArtifactTool,
    ListArtifactsTool,
]


class SkillRegistry:
    """
    Loads all skills (builtin + user-defined) and provides:
    - to_anthropic_tools(agent_id): filtered list for messages.create()
    - invoke(tool_name, **kwargs): execute a skill with permission enforcement
    """

    def __init__(
        self,
        user_skills_dir: Path | None = None,
        project_id: str | None = None,
    ):
        self._skills: dict[str, Skill] = {}
        self._project_id = project_id

        # Register builtins (instantiate with project context if needed)
        for skill_cls in _BUILTIN_SKILLS:
            skill = self._instantiate(skill_cls, project_id=project_id)
            self._skills[skill.id] = skill

        # Register user-defined skills
        if user_skills_dir and user_skills_dir.exists():
            self._load_user_skills(user_skills_dir, project_id=project_id)

    def _instantiate(self, skill_cls: type[Skill], **kwargs: Any) -> Skill:
        """Instantiate a skill class, passing kwargs only if accepted."""
        try:
            return skill_cls(**{k: v for k, v in kwargs.items() if v is not None})
        except TypeError:
            return skill_cls()

    def _load_user_skills(self, skills_dir: Path, project_id: str | None = None) -> None:
        """Discover and load skill.py files from user skills directory."""
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "skill.py"
            if not skill_file.exists():
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    f"maestro_skill_{skill_dir.name}", skill_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = module
                    spec.loader.exec_module(module)
                    # Look for a class named Skill or any Skill subclass
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, Skill)
                            and attr is not Skill
                        ):
                            skill = self._instantiate(attr, project_id=project_id)
                            self._skills[skill.id] = skill
            except Exception as e:
                print(f"Warning: failed to load skill from {skill_file}: {e}")

    def to_anthropic_tools(self, agent_id: str | None = None, allowlist: list[str] | None = None) -> list[dict]:
        """
        Return the Anthropic tool definitions list for the given agent.
        If allowlist is None, all skills are included.
        If allowlist is an empty list, no skills are included.
        """
        skills = self._skills.values()
        if allowlist is not None:
            skills = [s for s in skills if s.id in allowlist]
        return [s.definition() for s in skills]

    def invoke(self, tool_name: str, **kwargs: Any) -> str:
        """Execute a skill by name. Raises KeyError if not found."""
        if tool_name not in self._skills:
            return f"Error: skill '{tool_name}' not found in registry."
        skill = self._skills[tool_name]
        try:
            return skill.invoke(**kwargs)
        except ValueError as e:
            return f"Error: invalid input to '{tool_name}': {e}"
        except Exception as e:
            return f"Error executing '{tool_name}': {e}"

    def list_skills(self) -> list[dict]:
        """Return metadata for all registered skills."""
        return [
            {"id": s.id, "description": s.description}
            for s in self._skills.values()
        ]
