"""Path management helpers for workspace and run directories."""

from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path | str) -> Path:
    """Ensure a directory exists, creating it (and parents) if needed.

    Returns the resolved :class:`Path` for chaining.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def workspace_path(slug: str, base: Path | str | None = None) -> Path:
    """Return the canonical workspace directory for a topic *slug*.

    ``runs/<slug>`` is appended to *base* (default: current directory).
    The directory is **not** created — use :func:`ensure_dir` when needed.
    """
    root = Path(base) if base else Path.cwd()
    return root / "runs" / slug
