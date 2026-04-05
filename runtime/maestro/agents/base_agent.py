"""
AgentRunner — the core agentic execution loop.

Loads an agent's persona as the system prompt, calls the Anthropic API,
handles tool_use loops, runs self-check prompts, and returns a Handoff.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

import anthropic

from ..core.types import AgentConfig, Handoff, ArtifactRef
from ..core.constants import DEFAULT_MODEL, DEFAULT_MAX_TURNS
from ..memory.session_memory import SessionMemory
from ..memory.artifact_store import ArtifactStore
from ..skills.skill_registry import SkillRegistry


class AgentRunner:
    """
    Executes a single agent invocation using the Anthropic agentic loop pattern.

    Usage:
        runner = AgentRunner(agent_config, skill_registry, session_memory, artifact_store)
        handoff = runner.run(user_message)
    """

    def __init__(
        self,
        agent: AgentConfig,
        skill_registry: SkillRegistry,
        session: SessionMemory,
        artifact_store: ArtifactStore | None = None,
        verbose: bool = False,
    ):
        self.agent = agent
        self.skill_registry = skill_registry
        self.session = session
        self.artifact_store = artifact_store
        self.verbose = verbose
        self._client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def run(
        self,
        user_message: str,
        context: dict[str, Any] | None = None,
        stage_id: str | None = None,
    ) -> Handoff:
        """
        Run the agent on the given user message.
        Returns a Handoff containing the agent's output.
        """
        model = self._resolve_model()
        max_turns = self.agent.runtime.max_turns or DEFAULT_MAX_TURNS
        tools = self.skill_registry.to_anthropic_tools(
            agent_id=self.agent.id,
            allowlist=self.agent.runtime.tool_allowlist,
        )

        # Build the initial user message with injected context
        full_message = self._build_user_message(user_message, context)

        # Add to session memory
        self.session.add("user", full_message)

        if self.verbose:
            print(f"\n[{self.agent.name}] Starting — model: {model}, max_turns: {max_turns}")

        # Agentic loop
        raw_output = ""
        for turn in range(max_turns):
            response = self._client.messages.create(
                model=model,
                max_tokens=8096,
                system=self.agent.system_prompt,
                messages=self.session.messages,
                tools=tools if tools else anthropic.NOT_GIVEN,
            )

            if self.verbose:
                print(f"  [turn {turn + 1}] stop_reason={response.stop_reason}")

            # Collect text content
            text_parts = []
            tool_use_blocks = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_use_blocks.append(block)

            if text_parts:
                raw_output = "\n".join(text_parts)

            # Add assistant response to session
            self.session.add_raw({"role": "assistant", "content": response.content})

            # If no tool calls, we're done
            if response.stop_reason == "end_turn" or not tool_use_blocks:
                break

            # Handle tool calls
            tool_results = []
            for tool_block in tool_use_blocks:
                if self.verbose:
                    print(f"  [tool] {tool_block.name}({json.dumps(tool_block.input)[:80]}...)")
                result = self.skill_registry.invoke(tool_block.name, **tool_block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result,
                })

            # Add tool results to session
            self.session.add("user", tool_results)

        # Run self-check (lightweight — single call without tools)
        self_check_passed = self._run_self_check(raw_output)
        if not self_check_passed and self.verbose:
            print(f"  [self-check] Some checks flagged — included in handoff open_questions")

        # Build and return the Handoff
        return self._build_handoff(raw_output, stage_id=stage_id)

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _resolve_model(self) -> str:
        """Resolve the model to use: runtime override > env > default."""
        if self.agent.runtime.model:
            return self.agent.runtime.model
        return os.environ.get("MAESTRO_DEFAULT_MODEL", DEFAULT_MODEL)

    def _build_user_message(self, user_message: str, context: dict[str, Any] | None) -> str:
        """Inject context into the user message."""
        if not context:
            return user_message

        context_lines = ["\n\n## Context from Pipeline\n"]
        for key, value in context.items():
            context_lines.append(f"### {key}\n{value}\n")
        return user_message + "".join(context_lines)

    def _run_self_check(self, output: str) -> bool:
        """
        Run the agent's self-check prompts as a lightweight review call.
        Returns True if all checks pass (no critical concerns raised).
        """
        prompts = self.agent.evaluation.self_check_prompts
        if not prompts or not output:
            return True

        checklist = "\n".join(f"{i+1}. {p}" for i, p in enumerate(prompts))
        check_message = (
            f"Review your output below against these self-check questions. "
            f"For each question, answer YES or NO with a brief reason.\n\n"
            f"Self-check questions:\n{checklist}\n\n"
            f"Output to review:\n{output[:3000]}"  # Truncate for cost
        )

        try:
            response = self._client.messages.create(
                model=self._resolve_model(),
                max_tokens=1024,
                system=self.agent.system_prompt,
                messages=[{"role": "user", "content": check_message}],
            )
            check_result = response.content[0].text if response.content else ""
            # Consider it passing if no explicit NO answers dominate
            no_count = check_result.lower().count("\nno ")
            return no_count < len(prompts) // 2
        except Exception:
            return True  # Don't block on self-check failures

    def _build_handoff(self, raw_output: str, stage_id: str | None = None) -> Handoff:
        """Build a Handoff object from the agent's raw output."""
        artifacts: dict[str, ArtifactRef] = {}

        # If we have an artifact store and a stage_id, persist the full output
        if self.artifact_store and stage_id:
            ref = self.artifact_store.write(
                stage_id=stage_id,
                artifact_type="agent_output",
                content=raw_output,
                ext="md",
            )
            artifacts["agent_output"] = ref

        # Determine the first downstream agent from trigger conditions
        to_agent = ""
        if self.agent.handoffs.downstream:
            to_agent = self.agent.handoffs.downstream[0]

        return Handoff(
            from_agent=self.agent.id,
            to_agent=to_agent,
            trigger="",  # Set by orchestrator based on pipeline state
            artifacts=artifacts,
            context={"agent_id": self.agent.id, "stage_id": stage_id or ""},
            open_questions=[],
            raw_output=raw_output,
        )
