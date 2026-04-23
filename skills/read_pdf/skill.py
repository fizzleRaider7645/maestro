"""Skill: extract text from a PDF file using pypdf."""

from __future__ import annotations
from typing import Any

from maestro.skills.skill_base import Skill


class ReadPdfSkill(Skill):
    id = "read_pdf"
    description = "Extract text from a PDF file. Returns the text content of each page."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the PDF file.",
                },
                "pages": {
                    "type": "string",
                    "description": "Optional page range, e.g. '1-3' or '2'. Omit for all pages.",
                },
            },
            "required": ["path"],
        }

    def invoke(self, path: str, pages: str | None = None, **_: Any) -> str:
        try:
            import pypdf
        except ImportError:
            raise RuntimeError("pypdf is not installed. Run: pip install pypdf>=4.0")

        from pathlib import Path
        p = Path(path).expanduser()
        if not p.exists():
            raise ValueError(f"File not found: {path}")

        reader = pypdf.PdfReader(str(p))
        total = len(reader.pages)

        if pages:
            if "-" in pages:
                start, end = pages.split("-", 1)
                indices = list(range(int(start) - 1, min(int(end), total)))
            else:
                indices = [int(pages) - 1]
        else:
            indices = list(range(total))

        extracted = []
        for i in indices:
            if 0 <= i < total:
                text = reader.pages[i].extract_text() or ""
                extracted.append(f"--- Page {i + 1} ---\n{text.strip()}")

        if not extracted:
            return "(no text extracted — document may be a scanned image; OCR not supported)"
        return "\n\n".join(extracted)
