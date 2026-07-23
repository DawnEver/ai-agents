"""Lightweight data loading and validation — no JSON Schema dependency."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_data(path: Path) -> Any:
    """Load YAML or JSON data from path."""
    with path.open("r", encoding="utf-8") as f:
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(f)
        return json.load(f)


def require_keys(data: dict, *keys: str) -> list[str]:
    """Check that *data* has all *keys*. Returns list of missing key names."""
    return [k for k in keys if k not in data]
