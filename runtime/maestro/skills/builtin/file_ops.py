"""Builtin file operation skills: read_file, write_file, list_dir."""

from __future__ import annotations
from pathlib import Path
from typing import Any

from ..skill_base import Skill


class ReadFileTool(Skill):
    id = "read_file"
    description = "Read the contents of a file at the given path."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file to read.",
                }
            },
            "required": ["path"],
        }

    def invoke(self, path: str, **_: Any) -> str:
        p = Path(path)
        if not p.exists():
            raise ValueError(f"File not found: {path}")
        if not p.is_file():
            raise ValueError(f"Not a file: {path}")
        return p.read_text()


class WriteFileTool(Skill):
    id = "write_file"
    description = "Write content to a file at the given path. Creates parent directories if needed."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to write.",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file.",
                },
            },
            "required": ["path", "content"],
        }

    def invoke(self, path: str, content: str, **_: Any) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written {len(content)} characters to {path}"


class ListDirTool(Skill):
    id = "list_dir"
    description = "List files and directories at a given path."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list.",
                }
            },
            "required": ["path"],
        }

    def invoke(self, path: str, **_: Any) -> str:
        p = Path(path)
        if not p.exists():
            raise ValueError(f"Path not found: {path}")
        if not p.is_dir():
            raise ValueError(f"Not a directory: {path}")
        entries = sorted(p.iterdir())
        lines = []
        for entry in entries:
            kind = "dir" if entry.is_dir() else "file"
            lines.append(f"{kind}  {entry.name}")
        return "\n".join(lines) if lines else "(empty directory)"
