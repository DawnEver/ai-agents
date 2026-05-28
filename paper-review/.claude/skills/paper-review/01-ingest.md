# Step 01 — Ingest PDF → Markdown

Convert the PDF into a per-section markdown folder with per-section images, using `scripts/ingest.py`.

## Inputs
- `<pdf-path>` — argument to `/paper-review:new`

## Output layout

```
ongoing/<slug>/
  0-raw.pdf             ← original PDF
  1-paper-text/         ← step 01: ingested text + images
    paper.md            ← MAIN FILE: title, abstract, and an index of section files
    md/
      01-introduction.md
      02-related-work.md
      03-method.md
      04-experiments.md
      ...
    img/
      sec01/            ← images extracted from section 01
      sec02/
      sec03/
      ...
    INDEX.md            ← figure-number ↔ file mapping (built after split)
    appended/           ← if PDF contains multiple papers (e.g. conference versions
      01-<title-slug>/    appended as reference), each gets its own subdirectory
        paper.md          with the same layout as the main paper
        md/
        img/
        INDEX.md
      ...
```

## Steps

1. **Derive slug** from the PDF filename (lowercase, non-alphanum → `-`, strip leading/trailing `-`). Create `ongoing/<slug>/`, copy the PDF in as `0-raw.pdf`.

2. **Run `scripts/ingest.py`** — it handles tool selection, splitting, noise filtering, multi-paper separation, image distribution, and index building automatically:
   ```bash
   /Users/linxu/.local/share/paper-review-venv/bin/python3 scripts/ingest.py \
     "ongoing/<slug>/0-raw.pdf" "ongoing/<slug>"
   ```
   Tool selection logic (built into the script):
   - Detects GPU VRAM via `system_profiler` (Metal), `torch.cuda`, or `nvidia-smi`
   - VRAM ≥ 4 GB → **marker-pdf** (best layout fidelity)
   - otherwise → **pymupdf4llm** (fast, rule-based; seconds not minutes)
   - fallback → **pdfplumber** (plain text, no images)

   **Section splitting**: picks the shallowest heading level (fewer `#`) that has ≥3 matches, avoiding over-fragmentation from deep subsection headings. Falls back to all-heading split for poorly-structured PDFs.

   **Noise filtering**: sections with < 80 characters of meaningful text (after stripping markdown/images) are discarded — catches OCR garbage like isolated bold words from figure fragments.

   **Multi-paper detection**: when a PDF contains appended conference papers (common in journal submissions that include prior versions), the script detects paper boundaries via:
   - Author blocks with affiliations + emails appearing after the main content
   - IEEE copyright banners (`© 20XX IEEE`, "Authorized licensed use limited to")
   - Roman-numeral section restarts (`I. INTRODUCTION`) after Arabic-numbered sections
   - IEEE-style abstracts (`Abstract—`) appearing mid-document

   Appended papers are saved to `ongoing/<slug>/1-paper-text/appended/` with their own `paper.md` + `md/` + `INDEX.md`. The main pipeline only reviews the primary paper.

   The script outputs `1-paper-text/paper.md`, `1-paper-text/md/`, `1-paper-text/img/sec*/`, `1-paper-text/INDEX.md` in one shot.
   If it fails completely, STOP and report the error to the user.

3. **Build `INDEX.md`** — figure-number ↔ file mapping. Grep all section files for `Figure \d+` / `Fig. \d+` / `Table \d+` references; correlate with image filenames in order of first appearance. **Captions are not auto-extracted** — the Caption column will contain "—". Write:
   ```markdown
   # Figure / Table index

   | Number | File | Referenced in | Caption (first line) |
   |--------|------|---------------|----------------------|
   | Figure 1 | img/sec01-introduction/_page_2_Figure_1.jpeg | md/01-introduction.md | — |
   | Figure 2 | img/sec03/_page_5_Figure_2.jpeg | md/03-method.md | — |
   | Table 1 | img/sec04-experiments/_page_7_Table_1.jpeg | md/04-experiments.md | — |
   ```
   This lets vision reviewers find "Figure 2" without scanning every file — they open the image directly to see the caption.

4. **Cleanup** `_marker_tmp/`.

5. **Verify**: `1-paper-text/paper.md` exists, `1-paper-text/md/` non-empty, `1-paper-text/img/` exists. Report counts to the user (sections, figures, tables) before continuing to step 02.

## Failure triage

When `scripts/ingest.py` fails, match the error message against this table before asking the user to debug:

| Error message | Diagnosis | Action |
|---------------|-----------|--------|
| `marker_single: command not found` | `marker-pdf` not installed in the venv | Ingest falls back to `pymupdf4llm` automatically. No user action needed — the summary will note "ingested via pymupdf4llm (marker-pdf unavailable)". |
| `No module named 'pymupdf4llm'` | venv is missing dependencies | Re-create venv: `rm -rf ~/.local/share/paper-review-venv && python3 -m venv ~/.local/share/paper-review-venv && ~/.local/share/paper-review-venv/bin/pip install pymupdf4llm pdfplumber` |
| `No module named 'torch'` or CUDA/Metal errors | GPU detection failed, but ingest should still work | The script falls back to `pymupdf4llm`. If that also fails, run `~/.local/share/paper-review-venv/bin/pip install pymupdf4llm` manually. |
| `PDF appears to be scanned (no extractable text)` | The PDF is image-only — OCR needed | Tell the user: "This PDF has no selectable text. Please run OCR (e.g. Adobe Acrobat, ocrmypdf) and re-submit." |
| `Permission denied` on output path | File locked by sync service (e.g. OneDrive) | Wait a few seconds and retry. If persistent, move the PDF outside the OneDrive folder and re-run. |
| Empty `md/` directory after ingest | PDF text extraction produced nothing usable | Check `0-raw.pdf` opens correctly. If the PDF is password-protected or corrupted, ask the user to provide an unprotected copy. |
| Multi-paper detection false positive (appended/ has content from main paper) | Boundary detection split mid-paper | Delete `ongoing/<slug>/1-paper-text/` and re-ingest with `--reingest`. The user may need to manually split if the PDF has unusual formatting. |

## Resume rule

If `ongoing/<slug>/1-paper-text/paper.md` already exists, skip ingestion and proceed to step 02 unless the user passes `--reingest`.  To fix a bad ingest (e.g. sections merged, noise included, appended papers not separated), delete `ongoing/<slug>/1-paper-text/paper.md` and re-invoke `/paper-review:new <slug>` — it will re-enter step 01.
