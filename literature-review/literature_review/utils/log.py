"""Lightweight structured logging for the literature-review pipeline."""

from __future__ import annotations

import logging

_logger = logging.getLogger("literature_review")
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setLevel(logging.INFO)
    _handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.DEBUG)


def log(msg: str, level: str = "info", **kv: object) -> None:
    """Log *msg* with optional ``key=value`` context.

    Example::

        log("search complete", keyword="wind turbine", count=42)
    """
    extra = "".join(f" | {k}={v}" for k, v in kv.items())
    lvl = getattr(logging, level.upper(), logging.INFO)
    _logger.log(lvl, f"{msg}{extra}")
