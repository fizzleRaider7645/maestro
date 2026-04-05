"""Abstract base class for all Maestro skills (tools agents can invoke)."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class Skill(ABC):
    """
    Base class for a Maestro skill.

    A skill is a Python callable that an agent can invoke via the Anthropic
    tool_use protocol. Subclass this and implement `invoke()`.

    The `definition` property returns the Anthropic-compatible tool definition
    dict used in the `tools` parameter of messages.create().
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique snake_case skill identifier (matches tool_name in API calls)."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """One-sentence description shown to the agent."""
        ...

    @property
    @abstractmethod
    def parameters_schema(self) -> dict[str, Any]:
        """JSON Schema for the skill's input parameters."""
        ...

    @abstractmethod
    def invoke(self, **kwargs: Any) -> str:
        """
        Execute the skill. Returns a string result to be fed back to the agent.
        Raise ValueError for invalid inputs, RuntimeError for execution failures.
        """
        ...

    def definition(self) -> dict[str, Any]:
        """Anthropic tool definition dict."""
        return {
            "name": self.id,
            "description": self.description,
            "input_schema": {
                "type": "object",
                **self.parameters_schema,
            },
        }
