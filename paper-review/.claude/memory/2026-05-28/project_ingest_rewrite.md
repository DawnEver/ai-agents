---
name: project-ingest-rewrite
description: ingest.py split into paper_pdf_ingest package (src layout) with ruff, pytest, 49 tests; pymupdf4llm limitation on 2-column IEEE papers identified
metadata:
  type: project
---

ingest.py was refactored from a single 800-line file into a Python package (2026-05-28).

**Why:** Single-file ingest.py was becoming unmaintainable. Needed proper code formatting, linting, and test coverage.

**Package structure (src layout):**
```
paper_pdf_ingest/                  ← Python project root
  pyproject.toml                   ← ruff, pytest, coverage config
  Makefile                         ← fmt, lint, test targets
  .pre-commit-config.yaml
  src/paper_pdf_ingest/
    __init__.py                    ← public API re-exports
    __main__.py                    ← CLI entry point
    convert.py                     ← GPU detection + PDF converters
    sections.py                    ← section splitting + cleaning
    figures.py                     ← figure cropping + rendering
    output.py                      ← file output + paper.md/index
    utils.py                       ← slug, strip_formatting
  tests/                           ← 49 tests across 5 files
```

**Changes from original:**
- All `_private` functions made public (package-internal)
- `paper_pdf_ingest` installed as `paper-pdf-ingest` package
- `scripts/ingest.py` → thin backward-compat wrapper
- Cleaned `.gitignore` (removed wdg-lab Rust/Cython entries)

**Validation:** ruff format + lint clean, 49/49 pytest pass.

**Known limitation:** pymupdf4llm produces flat text (no `#` headings) for 2-column IEEE papers. `split_sections` correctly falls back to single-section but title is "Untitled" and abstract is garbled. Two paths: use marker-pdf (GPU ≥4GB) or add plain-text heading heuristics.

**How to apply:** `cd paper_pdf_ingest && make install-dev && make all`. Run pipeline: `uv run python -m paper_pdf_ingest <pdf> <slug-dir>`.
