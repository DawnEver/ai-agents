"""PDF text extraction and section splitting.

Absorbed from ReviewAgent extract_text.py and AeroWdg pipeline_extract.py.
"""

from __future__ import annotations

import re
from pathlib import Path

from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

# Canonical section headers in academic papers, ordered by typical appearance.
_SECTION_PATTERNS = [
    (r"\babstract\b", "abstract"),
    (r"\bintroduction\b", "introduction"),
    (r"\b(?:related\s+)?(?:background|literature\s+review)\b", "background"),
    (r"\bmethods?\b|\bmethodology\b|\bexperimental\s+(?:setup|design)\b", "methods"),
    (r"\bresults?\b|\bfindings?\b", "results"),
    (r"\bdiscussion\b", "discussion"),
    (r"\bconclusions?\b|\bsummary\b", "conclusion"),
    (r"\breferences?\b|\bbibliography\b", "references"),
]


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all textual content from a PDF file using PyPDF2."""
    text_parts: list[str] = []
    try:
        with Path(pdf_path).open("rb") as fh:
            reader = PdfReader(fh)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except (PdfReadError, OSError):
        return ""


def extract_sections(text: str) -> dict[str, str]:
    """Split paper text into named sections using heuristic header matching.

    Returns a dict mapping section names (e.g. 'introduction', 'methods')
    to their text content. Unmatched trailing text is stored under '_tail'.
    """
    # Find all section header positions
    hits: list[tuple[int, int, str]] = []  # (start, end, label)
    for pattern, label in _SECTION_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            hits.append((m.start(), m.end(), label))

    if not hits:
        return {"_tail": text}

    hits.sort(key=lambda h: h[0])

    # Merge overlapping hits (keep the first for each region)
    merged: list[tuple[int, int, str]] = [hits[0]]
    for start, end, label in hits[1:]:
        if start < merged[-1][1]:
            continue  # overlaps previous; skip
        merged.append((start, end, label))

    sections: dict[str, str] = {}
    for i, (start, end, label) in enumerate(merged):
        next_start = merged[i + 1][0] if i + 1 < len(merged) else len(text)
        body = text[end:next_start].strip()
        # If a section with the same label already exists, append to it
        if label in sections:
            sections[label] += "\n\n" + body
        else:
            sections[label] = body

    # Text before the first section header
    if merged[0][0] > 0:
        sections["_preamble"] = text[: merged[0][0]].strip()

    return sections
