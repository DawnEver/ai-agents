---
name: manuscript-review-ingest-setup
description: manuscript-review ingest pipeline — tool routing, venv location, script path
metadata:
  type: project
---

`scripts/ingest.py` handles PDF → markdown conversion with automatic tool selection:
- VRAM ≥ 4 GB → marker-pdf (ML, best layout fidelity)
- otherwise → pymupdf4llm (rule-based, seconds)
- fallback → pdfplumber (plain text, no images)

Python deps live in `/Users/linxu/.local/share/manuscript-review-venv/` (not uv tool, not system).
Run as: `/Users/linxu/.local/share/manuscript-review-venv/bin/python3 scripts/ingest.py <pdf> <out-dir>`

marker-pdf installed via `uv tool install marker-pdf` (provides `marker_single` CLI).

**Why:** marker-pdf takes many minutes on CPU; pymupdf4llm finishes in seconds. GPU detection added so the pipeline auto-upgrades on machines with a discrete GPU.

**How to apply:** Step 01 of manuscript-review pipeline calls this script. On Apple Silicon (no discrete GPU reported by system_profiler) pymupdf4llm is used automatically.
