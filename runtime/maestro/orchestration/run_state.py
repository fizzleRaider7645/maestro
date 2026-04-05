"""Tracks and persists pipeline run state to disk."""

from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

from ..core.constants import RUNS_DIR
from ..core.types import RunState, StageState, StageStatus, GateState, GateStatus, GateType, ArtifactRef


def new_run_id() -> str:
    return f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


class RunStateManager:
    """
    Manages a pipeline run's state: creates, updates, and persists it.

    State is stored at: ~/.maestro/runs/<run_id>/run_state.json
    Gate states are stored at: ~/.maestro/runs/<run_id>/gates/<gate_id>.json
    """

    def __init__(self, run_id: str, data_dir: Path = RUNS_DIR):
        self.run_id = run_id
        self.run_dir = data_dir / run_id
        self.gates_dir = self.run_dir / "gates"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.gates_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self.run_dir / "run_state.json"

    @classmethod
    def create(
        cls,
        project_id: str,
        pipeline_name: str,
        stage_ids: list[str],
        data_dir: Path = RUNS_DIR,
    ) -> "RunStateManager":
        """Create a new run."""
        run_id = new_run_id()
        manager = cls(run_id, data_dir)
        now = datetime.now(timezone.utc).isoformat()
        state = RunState(
            run_id=run_id,
            project_id=project_id,
            pipeline_name=pipeline_name,
            stages={sid: StageState(stage_id=sid) for sid in stage_ids},
            created_at=now,
            updated_at=now,
        )
        manager._run_state = state
        manager._persist()
        return manager

    @classmethod
    def load(cls, run_id: str, data_dir: Path = RUNS_DIR) -> "RunStateManager":
        """Load an existing run."""
        manager = cls(run_id, data_dir)
        manager._run_state = manager._load()
        return manager

    def get_state(self) -> RunState:
        return self._run_state

    def set_stage_status(self, stage_id: str, status: StageStatus) -> None:
        self._run_state.stages[stage_id].status = status
        self._touch()

    def add_artifact(self, stage_id: str, ref: ArtifactRef) -> None:
        self._run_state.stages[stage_id].artifacts.append(ref)
        self._touch()

    def set_gate(self, stage_id: str, gate: GateState) -> None:
        self._run_state.stages[stage_id].gate = gate
        self._persist_gate(gate)
        self._touch()

    def update_gate_status(self, stage_id: str, status: GateStatus, feedback: str | None = None) -> None:
        gate = self._run_state.stages[stage_id].gate
        if gate:
            gate.status = status
            if feedback:
                gate.rejection_feedback = feedback
            self._persist_gate(gate)
        self._touch()

    def increment_revision(self, stage_id: str) -> int:
        self._run_state.stages[stage_id].revision_count += 1
        self._touch()
        return self._run_state.stages[stage_id].revision_count

    def complete(self) -> None:
        self._run_state.completed = True
        self._touch()

    def get_runnable_stages(self, pipeline_stages: list) -> list:
        """Return stages whose dependencies are satisfied and that haven't started."""
        runnable = []
        for stage_cfg in pipeline_stages:
            stage_st = self._run_state.stages.get(stage_cfg.id)
            if not stage_st or stage_st.status != StageStatus.PENDING:
                continue
            if self._dependencies_met(stage_cfg):
                runnable.append(stage_cfg)
        return runnable

    def _dependencies_met(self, stage_cfg) -> bool:
        for dep in stage_cfg.depends_on:
            dep_state = self._run_state.stages.get(dep.stage)
            if not dep_state:
                return False
            required_status = {
                "approved": StageStatus.APPROVED,
                "peer_reviewed": StageStatus.APPROVED,
                "quality_gate_passed": StageStatus.APPROVED,
                "completed": StageStatus.COMPLETED,
            }.get(dep.condition, StageStatus.APPROVED)
            if dep_state.status != required_status:
                return False
        return True

    def _touch(self) -> None:
        self._run_state.updated_at = datetime.now(timezone.utc).isoformat()
        self._persist()

    def _persist(self) -> None:
        data = self._serialize()
        with open(self._state_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _persist_gate(self, gate: GateState) -> None:
        gate_file = self.gates_dir / f"{gate.gate_id}.json"
        with open(gate_file, "w") as f:
            json.dump(
                {
                    "gate_id": gate.gate_id,
                    "stage_id": gate.stage_id,
                    "gate_type": gate.gate_type.value,
                    "status": gate.status.value,
                    "evaluator_report": gate.evaluator_report,
                    "rejection_feedback": gate.rejection_feedback,
                    "payload": gate.payload,
                },
                f,
                indent=2,
                default=str,
            )

    def _serialize(self) -> dict:
        state = self._run_state
        return {
            "run_id": state.run_id,
            "project_id": state.project_id,
            "pipeline_name": state.pipeline_name,
            "created_at": state.created_at,
            "updated_at": state.updated_at,
            "completed": state.completed,
            "stages": {
                sid: {
                    "stage_id": ss.stage_id,
                    "status": ss.status.value,
                    "revision_count": ss.revision_count,
                    "error": ss.error,
                    "artifacts": [
                        {
                            "artifact_type": r.artifact_type,
                            "stage_id": r.stage_id,
                            "path": str(r.path),
                            "format": r.format,
                        }
                        for r in ss.artifacts
                    ],
                    "gate": {
                        "gate_id": ss.gate.gate_id,
                        "status": ss.gate.status.value,
                    } if ss.gate else None,
                }
                for sid, ss in state.stages.items()
            },
        }

    def _load(self) -> RunState:
        if not self._state_file.exists():
            raise FileNotFoundError(f"Run state not found: {self._state_file}")
        with open(self._state_file) as f:
            data = json.load(f)
        stages = {}
        for sid, sd in data.get("stages", {}).items():
            artifacts = [
                ArtifactRef(
                    artifact_type=a["artifact_type"],
                    stage_id=a["stage_id"],
                    path=Path(a["path"]),
                    format=a.get("format", "md"),
                )
                for a in sd.get("artifacts", [])
            ]
            gate = None
            if sd.get("gate"):
                gate_file = self.gates_dir / f"{sd['gate']['gate_id']}.json"
                if gate_file.exists():
                    with open(gate_file) as gf:
                        gd = json.load(gf)
                    gate = GateState(
                        gate_id=gd["gate_id"],
                        stage_id=gd["stage_id"],
                        gate_type=GateType(gd["gate_type"]),
                        status=GateStatus(gd["status"]),
                        evaluator_report=gd.get("evaluator_report"),
                        rejection_feedback=gd.get("rejection_feedback"),
                        payload=gd.get("payload", {}),
                    )
            stages[sid] = StageState(
                stage_id=sid,
                status=StageStatus(sd["status"]),
                artifacts=artifacts,
                gate=gate,
                revision_count=sd.get("revision_count", 0),
                error=sd.get("error"),
            )
        return RunState(
            run_id=data["run_id"],
            project_id=data["project_id"],
            pipeline_name=data["pipeline_name"],
            stages=stages,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            completed=data.get("completed", False),
        )
