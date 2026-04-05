"""
Main pipeline orchestrator — executes a full multi-agent pipeline run.

Reads pipeline.yaml, discovers runnable stages, runs them (concurrently
where dependencies allow), manages gates and feedback loops.
"""

from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Any

from ..core.types import StageStatus, GateStatus, GateType, GateState
from ..core.pipeline_loader import load_pipeline
from ..core.constants import PIPELINE_FILE
from ..agents.agent_registry import AgentRegistry
from ..agents.evaluator_agent import EvaluatorAgent
from ..memory.artifact_store import ArtifactStore
from ..memory.project_memory import ProjectMemory
from ..skills.skill_registry import SkillRegistry
from .run_state import RunStateManager
from .stage_runner import StageRunner
from .gate_manager import GateManager
from .feedback_router import FeedbackRouter


class Orchestrator:
    """
    Executes a pipeline run end-to-end.

    Usage:
        orch = Orchestrator(project_id="my-project")
        await orch.run(requirements_text)
    """

    def __init__(
        self,
        project_id: str,
        pipeline_file: Path = PIPELINE_FILE,
        resume_run_id: str | None = None,
        interactive: bool = True,
        verbose: bool = False,
        user_skills_dir: Path | None = None,
    ):
        self.project_id = project_id
        self.pipeline = load_pipeline(pipeline_file)
        self.interactive = interactive
        self.verbose = verbose

        # Registry and skills
        self.agent_registry = AgentRegistry()
        self.skill_registry = SkillRegistry(
            user_skills_dir=user_skills_dir,
            project_id=project_id,
        )
        self.artifact_store = ArtifactStore(project_id)
        self.project_memory = ProjectMemory(project_id)

        # Run state
        stage_ids = [s.id for s in self.pipeline.stages]
        if resume_run_id:
            self.run_manager = RunStateManager.load(resume_run_id)
        else:
            self.run_manager = RunStateManager.create(
                project_id=project_id,
                pipeline_name=self.pipeline.name,
                stage_ids=stage_ids,
            )
            self.project_memory.record_run(
                self.run_manager.run_id, self.pipeline.name
            )

        self.stage_runner = StageRunner(
            agent_registry=self.agent_registry,
            skill_registry=self.skill_registry,
            artifact_store=self.artifact_store,
            run_manager=self.run_manager,
            verbose=verbose,
        )
        self.gate_manager = GateManager(interactive=interactive)
        self.feedback_router = FeedbackRouter(self.pipeline, self.run_manager)
        self.evaluator = EvaluatorAgent()

        print(f"\nPipeline: {self.pipeline.name}")
        print(f"Run ID:   {self.run_manager.run_id}")
        print(f"Project:  {project_id}")

    async def run(self, requirements: str) -> str:
        """
        Execute the full pipeline starting from requirements.
        Returns the run_id on completion.
        """
        # Store requirements as the first artifact
        self.artifact_store.write(
            stage_id="input",
            artifact_type="requirements_doc",
            content=requirements,
            ext="md",
        )

        while not self.run_manager.get_state().completed:
            runnable = self.run_manager.get_runnable_stages(self.pipeline.stages)
            if not runnable:
                # Check if all stages are done
                all_states = self.run_manager.get_state().stages
                active = [
                    s for s in all_states.values()
                    if s.status not in (StageStatus.COMPLETED, StageStatus.APPROVED, StageStatus.FAILED)
                ]
                if not active:
                    self.run_manager.complete()
                    break
                # Waiting on gates
                await asyncio.sleep(0.1)
                continue

            # Run all currently runnable stages concurrently
            await asyncio.gather(*[self._run_stage(stage) for stage in runnable])

        run_id = self.run_manager.run_id
        state = self.run_manager.get_state()
        failed = [sid for sid, ss in state.stages.items() if ss.status == StageStatus.FAILED]
        if failed:
            print(f"\nPipeline completed with failures: {failed}")
        else:
            print(f"\nPipeline complete. Run ID: {run_id}")
        return run_id

    async def _run_stage(self, stage_cfg) -> None:
        """Run a single stage including gate handling."""
        stage_id = stage_cfg.id
        try:
            # Get rejection feedback if this is a revision
            stage_state = self.run_manager.get_state().stages[stage_id]
            additional_context = {}
            if stage_state.revision_count > 0 and stage_state.gate:
                feedback = stage_state.gate.rejection_feedback
                if feedback:
                    additional_context["rejection_feedback"] = (
                        f"Previous submission was rejected. Feedback:\n{feedback}"
                    )

            handoff = await self.stage_runner.run(stage_cfg, additional_context=additional_context)

            # Handle gate if present
            if stage_cfg.gate:
                await self._handle_gate(stage_cfg, handoff)
            else:
                self.run_manager.set_stage_status(stage_id, StageStatus.COMPLETED)

        except Exception as e:
            self.run_manager.get_state().stages[stage_id].error = str(e)
            self.run_manager.set_stage_status(stage_id, StageStatus.FAILED)
            print(f"\n  ERROR in stage '{stage_id}': {e}")
            raise

    async def _handle_gate(self, stage_cfg, handoff) -> None:
        """Run evaluator then present gate to human if needed."""
        stage_id = stage_cfg.id
        gate_config = stage_cfg.gate

        # Run automated evaluator first
        evaluator_report = None
        try:
            agent = self.agent_registry.get(stage_cfg.agent_id)
            output = handoff.raw_output
            passed, evaluator_report = self.evaluator.evaluate(
                agent=agent,
                gate_config=gate_config,
                output_content=output,
                stage_name=stage_cfg.name,
            )
            if not passed and gate_config.type == GateType.AUTOMATED_ONLY:
                print(f"\n  Evaluator FAIL — gate blocked automatically")
                return_to = self.feedback_router.handle_rejection(stage_id, evaluator_report)
                return
        except Exception as e:
            evaluator_report = f"Evaluator error: {e}"

        # Build artifacts summary
        artifacts = self.run_manager.get_state().stages[stage_id].artifacts
        artifacts_summary = "\n".join(
            f"  • {r.artifact_type} ({r.format}) → {r.path.name}"
            for r in artifacts
        )

        # Open gate
        gate_state = self.gate_manager.open_gate(
            stage_id=stage_id,
            gate_config=gate_config,
            artifacts_summary=artifacts_summary,
        )
        gate_state.evaluator_report = evaluator_report
        self.run_manager.set_stage_status(stage_id, StageStatus.AWAITING_GATE)
        self.run_manager.set_gate(stage_id, gate_state)

        # Skip human approval for automated_only gates
        if gate_config.type == GateType.AUTOMATED_ONLY:
            self.run_manager.update_gate_status(stage_id, GateStatus.APPROVED)
            self.run_manager.set_stage_status(stage_id, StageStatus.APPROVED)
            print(f"  Gate auto-approved (automated_only).")
            return

        # Await human decision
        approved, feedback = await self.gate_manager.await_decision(
            gate_state, gate_config, evaluator_report
        )

        if approved:
            self.run_manager.update_gate_status(stage_id, GateStatus.APPROVED)
            self.run_manager.set_stage_status(stage_id, StageStatus.APPROVED)
            print(f"  Stage '{stage_id}' approved.")
        else:
            self.run_manager.update_gate_status(stage_id, GateStatus.REJECTED, feedback=feedback)
            return_to = self.feedback_router.handle_rejection(stage_id, feedback)
