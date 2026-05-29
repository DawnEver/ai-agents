# Memory Index

<!-- Sorted by date, newest first. Keep at most 20 entries. -->

- [2026-05-28 E2E tests](../memory/2026-05-28/project_e2e_tests.md) — strict e2e tests against known IEEE PDF with LaTeX ground truth; conftest.py extracted shared fixtures; Pillow corrupted in venv
- [2026-05-28 Ingest package refactor](../memory/2026-05-28/project_ingest_rewrite.md) — split into paper_pdf_ingest (src layout), ruff+pytest, 49 tests; pymupdf4llm heading limitation on 2-column IEEE
- [2026-05-28 Directory restructure](../memory/2026-05-28/project_directory_restructure.md) — pipeline layout: 0-raw.pdf / 1-paper-text / 2-review / 3-response
- [2026-05-27 paper-review ingest setup](../memory/2026-05-27/project_paper_review_ingest.md) — scripts/ingest.py routes PDF→md: GPU≥4GB→marker-pdf, else pymupdf4llm; venv at ~/.local/share/paper-review-venv