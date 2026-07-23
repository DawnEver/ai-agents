"""Shared utility functions reused across pipeline stages."""

from __future__ import annotations

import json
from typing import Any


def normalize_text(value: Any) -> str:
    """Convert an arbitrary value to a compact single-line string."""
    if value is None:
        return ""
    text = str(value).strip()
    return " ".join(text.split())


def paper_key(item: dict[str, str]) -> str:
    """Build a stable deduplication key — DOI first, then title."""
    doi = normalize_text(item.get("DOI", "")).lower()
    if doi:
        return f"doi:{doi}"
    title = normalize_text(item.get("Title", "")).lower()
    return f"title:{title}"


def strip_markdown_code_fence(text: str) -> str:
    """Remove leading/trailing markdown code fences from model output."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        first_nl = cleaned.find("\n")
        cleaned = cleaned[first_nl + 1:] if first_nl != -1 else ""
        cleaned = cleaned.removesuffix("```").strip()
    return cleaned


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Best-effort JSON object extraction from text (handles code fences)."""
    cleaned = strip_markdown_code_fence(text)
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        data = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def extract_json_list(text: str) -> list[dict[str, Any]]:
    """Best-effort JSON list extraction from text (handles code fences)."""
    cleaned = strip_markdown_code_fence(text)
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except json.JSONDecodeError:
        pass
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        data = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return []
    return [x for x in data if isinstance(x, dict)] if isinstance(data, list) else []
