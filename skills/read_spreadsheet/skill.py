"""Skill: read an Excel or CSV file and return its contents as a markdown table."""

from __future__ import annotations
from typing import Any

from maestro.skills.skill_base import Skill


class ReadSpreadsheetSkill(Skill):
    id = "read_spreadsheet"
    description = "Read an Excel (.xlsx) or CSV file and return its contents as a markdown table."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the .xlsx or .csv file.",
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Sheet name for .xlsx files. Omit to use the first sheet.",
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows to return (default 200).",
                },
            },
            "required": ["path"],
        }

    def invoke(
        self,
        path: str,
        sheet_name: str | None = None,
        max_rows: int = 200,
        **_: Any,
    ) -> str:
        from pathlib import Path
        p = Path(path).expanduser()
        if not p.exists():
            raise ValueError(f"File not found: {path}")
        suffix = p.suffix.lower()
        if suffix == ".csv":
            return self._read_csv(p, max_rows)
        elif suffix in (".xlsx", ".xls"):
            return self._read_excel(p, sheet_name, max_rows)
        else:
            raise ValueError(f"Unsupported file type: {suffix}. Supported: .csv, .xlsx")

    def _read_csv(self, p: Any, max_rows: int) -> str:
        import csv
        rows: list[list[str]] = []
        with open(p, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i >= max_rows + 1:
                    rows.append([f"... ({i - max_rows} rows truncated)"])
                    break
                rows.append([str(v) for v in row])
        return self._to_markdown(rows)

    def _read_excel(self, p: Any, sheet_name: str | None, max_rows: int) -> str:
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError("openpyxl not installed. Run: pip install openpyxl>=3.1")
        wb = openpyxl.load_workbook(str(p), read_only=True, data_only=True)
        ws = wb[sheet_name] if sheet_name else wb.active
        rows: list[list[str]] = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= max_rows + 1:
                rows.append([f"... truncated at {max_rows} rows"])
                break
            rows.append([str(v) if v is not None else "" for v in row])
        return self._to_markdown(rows)

    def _to_markdown(self, rows: list[list[str]]) -> str:
        if not rows:
            return "(empty)"
        # Normalize column count
        width = max(len(r) for r in rows)
        normalized = [r + [""] * (width - len(r)) for r in rows]
        header = normalized[0]
        sep = ["---"] * width
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(sep) + " |",
        ]
        for row in normalized[1:]:
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)
