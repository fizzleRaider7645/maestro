"""Routes feedback loops between agents when gates are rejected."""

from __future__ import annotations

from ..core.types import PipelineConfig, StageStatus
from .run_state import RunStateManager


class FeedbackRouter:
    """
    Routes rejected gates and feedback loops back to the appropriate stage.

    Implements the feedback_loops defined in pipeline.yaml:
    - On gate rejection: returns to the stage specified in on_reject.return_to
    - On explicit feedback loop trigger: routes to the target agent
    """

    def __init__(self, pipeline: PipelineConfig, run_manager: RunStateManager):
        self.pipeline = pipeline
        self.run_manager = run_manager

    def handle_rejection(self, stage_id: str, feedback: str) -> str:
        """
        Reset a rejected stage for re-execution.
        Returns the stage_id to re-run.
        """
        # Find the stage config to get on_reject.return_to
        stage_cfg = self._get_stage(stage_id)
        if not stage_cfg or not stage_cfg.gate:
            return stage_id

        return_to = stage_cfg.gate.on_reject_return_to or stage_id

        # Reset the return_to stage to PENDING
        run_state = self.run_manager.get_state()
        if return_to in run_state.stages:
            revision = self.run_manager.increment_revision(return_to)
            self.run_manager.set_stage_status(return_to, StageStatus.PENDING)

            # Store rejection feedback for the stage runner to inject as context
            run_state.stages[return_to].error = None
            print(f"\n  Gate rejected — returning to '{return_to}' (revision {revision})")
            if feedback:
                print(f"  Feedback: {feedback}")

        # Check escalation: more than 3 revisions triggers human review
        revision_count = run_state.stages[return_to].revision_count
        if revision_count > 3:
            print(
                f"\n  WARNING: Stage '{return_to}' has been revised {revision_count} times. "
                f"Escalation trigger: consider human review."
            )

        return return_to

    def get_feedback_loop(self, from_agent: str, trigger_type: str) -> str | None:
        """
        Look up the target agent for a feedback loop.
        Returns the target agent_id, or None if no matching loop.
        """
        for loop in self.pipeline.feedback_loops:
            if loop.from_agent == from_agent and trigger_type in loop.trigger.lower():
                return loop.to_agent
        return None

    def _get_stage(self, stage_id: str):
        for stage in self.pipeline.stages:
            if stage.id == stage_id:
                return stage
        return None
