"""Path management helpers for workspace and run directories."""

from __future__ import annotations

import os
from pathlib import Path


def ensure_dir(path: Path | str) -> Path:
    """Ensure a directory exists, creating it (and parents) if needed.

    Returns the resolved :class:`Path` for chaining.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def find_root(start: Path | str | None = None) -> Path:
    """Resolve the project root that holds ``workspaces/`` and ``lenses/``.

    Resolution order:
    1. ``LIT_REVIEW_ROOT`` environment variable, if set.
    2. Walk up from *start* (default: cwd) to the first directory containing
       a ``workspaces/`` folder.
    3. Fall back to *start* itself.
    """
    env = os.environ.get("LIT_REVIEW_ROOT")
    if env:
        return Path(env)

    base = Path(start) if start else Path.cwd()
    for candidate in (base, *base.parents):
        if (candidate / "workspaces").is_dir():
            return candidate
    return base


def workspace_path(slug: str, base: Path | str | None = None) -> Path:
    """Return the canonical workspace directory for a topic *slug*.

    ``workspaces/<slug>`` under *base* (default: :func:`find_root`).
    The directory is **not** created — use :func:`ensure_dir` when needed.
    """
    root = Path(base) if base else find_root()
    return root / "workspaces" / slug
