"""Short-term conversation memory — stores message history per session."""

from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
from typing import Any

from ..core.constants import SESSIONS_DIR


class SessionMemory:
    """
    In-memory message list (Anthropic messages format) that is persisted to disk.

    Each session corresponds to one agent invocation within a pipeline run.
    Session ID convention: <run_id>_<stage_id>_<agent_id>
    """

    def __init__(self, session_id: str, data_dir: Path = SESSIONS_DIR):
        self.session_id = session_id
        self.session_file = data_dir / f"{session_id}.json"
        data_dir.mkdir(parents=True, exist_ok=True)
        self._messages: list[dict[str, Any]] = self._load()

    @property
    def messages(self) -> list[dict[str, Any]]:
        return self._messages

    def add(self, role: str, content: str | list) -> None:
        """Add a message to the session. Persists immediately."""
        self._messages.append({"role": role, "content": content})
        self._save()

    def add_raw(self, message: dict[str, Any]) -> None:
        """Add a pre-built message dict. Persists immediately."""
        self._messages.append(message)
        self._save()

    def clear(self) -> None:
        """Clear all messages and delete the session file."""
        self._messages = []
        if self.session_file.exists():
            self.session_file.unlink()

    def _load(self) -> list[dict[str, Any]]:
        if self.session_file.exists():
            with open(self.session_file) as f:
                data = json.load(f)
                return data.get("messages", [])
        return []

    def _save(self) -> None:
        with open(self.session_file, "w") as f:
            json.dump(
                {
                    "session_id": self.session_id,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "messages": self._messages,
                },
                f,
                indent=2,
            )
