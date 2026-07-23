---
name: paper-pdf-ingest-standalone
description: paper_pdf_ingest extracted to standalone git repo at manuscript-review/paper_pdf_ingest/
metadata:
  type: project
---

`manuscript-review/paper_pdf_ingest/` is now a standalone git repo (independent `.git`, not tracked by manuscript-review).

**Why:** Library is reusable outside manuscript-review; needs its own release cycle, CI, and versioning.

**How to apply:**
- manuscript-review's `.gitignore` has `paper_pdf_ingest/` — it will never be re-added to manuscript-review tracking
- To work on the library, open `manuscript-review/paper_pdf_ingest/` as its own project in Claude Code
- The library uses `hatchling` build backend, `dynamic = ["version"]` from `__init__.__version__`
- CI is at `.github/workflows/ci.yml` (uv, Python 3.12 & 3.13, ruff + pytest --cov)
- Dev workflow: `uv sync --all-extras` → `uv run pytest` (no --cov in addopts; use `make test-cov` for coverage)

**Bugs fixed during sharp-review before extraction:**
- `route_images`: iterdir() now sorted (was non-deterministic)
- `_rewrite` closure: orphan images now get `../img/orphan/{fname}` refs (were left broken)
- `__main__.py`: both silent sys.exit(1) calls now print to stderr
- `_build_crop_rect`: warns when graphic_rects empty and falling back to half-page estimate
- `pyproject.toml`: removed dead `archived`/`ongoing` ruff excludes; stripped --cov from addopts
- `tests/`: removed 5 duplicate top-level test files (were identical to tests/unit/)
