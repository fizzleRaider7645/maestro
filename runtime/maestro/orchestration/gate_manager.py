"""Manages human approval gates — pause/resume pipeline execution."""

from __future__ import annotations
import asyncio
import uuid
from typing import Callable

from ..core.types import GateConfig, GateState, GateStatus, GateType, StageConfig


class GateManager:
    """
    Manages gate lifecycle for a pipeline run.

    Gates block pipeline execution until a human approves or rejects.
    In CLI mode this is an interactive prompt.
    In API mode, gates are resolved via the /gates/{id}/decision endpoint.
    """

    def __init__(self, interactive: bool = True):
        self._interactive = interactive
        self._pending: dict[str, asyncio.Future] = {}

    def open_gate(
        self,
        stage_id: str,
        gate_config: GateConfig,
        artifacts_summary: str = "",
    ) -> GateState:
        """Create a gate state object and print summary."""
        gate_id = f"gate_{stage_id}_{uuid.uuid4().hex[:6]}"
        gate = GateState(
            gate_id=gate_id,
            stage_id=stage_id,
            gate_type=gate_config.type,
            status=GateStatus.OPEN,
            payload={"artifacts_summary": artifacts_summary},
        )
        return gate

    async def await_decision(
        self,
        gate: GateState,
        gate_config: GateConfig,
        evaluator_report: str | None = None,
    ) -> tuple[bool, str]:
        """
        Wait for a gate decision. Returns (approved: bool, feedback: str).

        In interactive mode: prompts the CLI user.
        In non-interactive mode: blocks until approve() or reject() is called.
        """
        self._print_gate_summary(gate, gate_config, evaluator_report)

        if self._interactive:
            return await self._cli_prompt(gate, gate_config)
        else:
            loop = asyncio.get_event_loop()
            future: asyncio.Future = loop.create_future()
            self._pending[gate.gate_id] = future
            result = await future
            return result

    def approve(self, gate_id: str) -> None:
        """Resolve a pending gate as approved (for API/programmatic use)."""
        if gate_id in self._pending:
            future = self._pending.pop(gate_id)
            if not future.done():
                future.set_result((True, ""))

    def reject(self, gate_id: str, feedback: str = "") -> None:
        """Resolve a pending gate as rejected with feedback."""
        if gate_id in self._pending:
            future = self._pending.pop(gate_id)
            if not future.done():
                future.set_result((False, feedback))

    def _print_gate_summary(
        self,
        gate: GateState,
        gate_config: GateConfig,
        evaluator_report: str | None,
    ) -> None:
        print(f"\n{'='*60}")
        print(f"  GATE: {gate.stage_id.upper()} — {gate.gate_type.value}")
        print(f"  Gate ID: {gate.gate_id}")
        print(f"{'='*60}")
        if gate_config.approval_criteria:
            print("\nApproval Criteria:")
            for criterion in gate_config.approval_criteria:
                print(f"  • {criterion}")
        if gate.payload.get("artifacts_summary"):
            print(f"\nArtifacts Produced:\n{gate.payload['artifacts_summary']}")
        if evaluator_report:
            print(f"\nEvaluator Report:\n{evaluator_report}")
        print()

    async def _cli_prompt(
        self, gate: GateState, gate_config: GateConfig
    ) -> tuple[bool, str]:
        """Interactive CLI prompt for gate decision."""
        while True:
            print("Decision: [a]pprove / [r]eject / [s]how artifacts  > ", end="", flush=True)
            try:
                choice = await asyncio.get_event_loop().run_in_executor(None, input)
            except (EOFError, KeyboardInterrupt):
                print("\nGate decision interrupted.")
                return False, "Interrupted"

            choice = choice.strip().lower()
            if choice in ("a", "approve", "yes", "y"):
                print("  Gate approved.")
                return True, ""
            elif choice in ("r", "reject", "no", "n"):
                print("  Feedback (press Enter when done): ", end="", flush=True)
                try:
                    feedback = await asyncio.get_event_loop().run_in_executor(None, input)
                except (EOFError, KeyboardInterrupt):
                    feedback = ""
                print("  Gate rejected.")
                return False, feedback
            elif choice in ("s", "show"):
                if gate.payload.get("artifacts_summary"):
                    print(gate.payload["artifacts_summary"])
            else:
                print("  Invalid choice. Enter 'a' to approve or 'r' to reject.")
