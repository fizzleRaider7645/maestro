"""Executes a single pipeline stage."""

from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Any

from ..core.types import StageConfig, StageStatus, Handoff
from ..agents.base_agent import AgentRunner
from ..agents.agent_registry import AgentRegistry
from ..memory.artifact_store import ArtifactStore
from ..memory.session_memory import SessionMemory
from ..skills.skill_registry import SkillRegistry
from .run_state import RunStateManager


class StageRunner:
    """
    Executes a single pipeline stage by:
    1. Loading the stage's agent
    2. Gathering input artifacts from the artifact store
    3. Running the agent
    4. Persisting output artifacts
    5. Returning the Handoff
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        skill_registry: SkillRegistry,
        artifact_store: ArtifactStore,
        run_manager: RunStateManager,
        verbose: bool = False,
    ):
        self.agent_registry = agent_registry
        self.skill_registry = skill_registry
        self.artifact_store = artifact_store
        self.run_manager = run_manager
        self.verbose = verbose

    async def run(
        self,
        stage_config: StageConfig,
        additional_context: dict[str, Any] | None = None,
    ) -> Handoff:
        """Run a stage and return its Handoff."""
        run_state = self.run_manager.get_state()
        stage_id = stage_config.id

        self.run_manager.set_stage_status(stage_id, StageStatus.RUNNING)
        print(f"\n[Stage: {stage_config.name}]  agent={stage_config.agent_id}")

        # Load agent config
        try:
            agent = self.agent_registry.get(stage_config.agent_id)
        except KeyError as e:
            self.run_manager.get_state().stages[stage_id].error = str(e)
            self.run_manager.set_stage_status(stage_id, StageStatus.FAILED)
            raise

        # Build context from upstream artifacts
        context = self._gather_context(stage_config, run_state)
        if additional_context:
            context.update(additional_context)

        # Build the user task message
        user_message = self._build_task_message(stage_config, context)

        # Set up session memory
        session_id = f"{run_state.run_id}_{stage_id}_{agent.id}"
        session = SessionMemory(session_id)

        # Run the agent
        runner = AgentRunner(
            agent=agent,
            skill_registry=self.skill_registry,
            session=session,
            artifact_store=self.artifact_store,
            verbose=self.verbose,
        )
        handoff = await asyncio.to_thread(
            runner.run, user_message, context=context, stage_id=stage_id
        )

        # Persist the primary output artifact
        ref = self.artifact_store.write(
            stage_id=stage_id,
            artifact_type="primary_output",
            content=handoff.raw_output,
            ext="md",
        )
        self.run_manager.add_artifact(stage_id, ref)

        return handoff

    def _gather_context(self, stage_config: StageConfig, run_state: Any) -> dict[str, Any]:
        """Collect upstream artifacts relevant to this stage's input requirements."""
        context: dict[str, Any] = {}
        # Only search stages this stage explicitly depends on, plus the input stage
        dep_stage_ids = {dep.stage for dep in stage_config.depends_on} | {"input"}

        # Fallback: include primary_output from each upstream dep stage (always present
        # after a stage completes, even when agents don't call write_artifact explicitly)
        for dep_stage_id in dep_stage_ids:
            primary = self.artifact_store.read(dep_stage_id, "primary_output")
            if primary:
                context[f"{dep_stage_id}_output"] = primary

        # Override with typed artifacts where available (agents using write_artifact skill)
        for input_type in stage_config.inputs:
            for dep_stage_id in dep_stage_ids:
                content = self.artifact_store.read(dep_stage_id, input_type)
                if content:
                    context[input_type] = content
                    break

        return context

    def _build_task_message(self, stage_config: StageConfig, context: dict[str, Any]) -> str:
        """Build the task description message for the agent."""
        lines = [
            f"You are now executing the **{stage_config.name}** stage.",
            f"\n{stage_config.description}",
            f"\nYour required inputs are: {', '.join(stage_config.inputs) or 'none'}.",
            f"Your expected outputs are: {', '.join(stage_config.outputs) or 'none'}.",
        ]
        if context:
            lines.append("\nThe following input artifacts have been provided:")
            for artifact_type, content in context.items():
                preview = content[:500] + "..." if len(content) > 500 else content
                lines.append(f"\n### {artifact_type}\n{preview}")

        lines.append(
            "\nProduce all required output artifacts. Use write_artifact to store each output. "
            "When complete, provide a summary of what you produced."
        )
        return "\n".join(lines)
