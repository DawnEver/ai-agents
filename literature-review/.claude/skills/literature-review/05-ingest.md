# Step 05 — PDF decomposition

Decompose acquired PDFs into structured markdown via `paper_pdf_ingest`. This step requires **explicit user confirmation** — never infer consent from earlier approvals.

## Inputs
- `workspaces/<slug>/runs/<run-id>/handoff/download_manifest.json` — manifest of acquired PDFs

## Output

```
workspaces/<slug>/runs/<run-id>/
  ingest/
    ingest_manifest.json       ← per-paper decomposition outcomes
    <candidate_id>/
      1-paper-text/
        paper.md               ← title, abstract, section index
        md/                    ← per-section markdown files
        img/                   ← extracted figures and tables
          sec*/
        INDEX.md               ← figure-number ↔ file mapping
```

## Steps

1. **Read the download manifest**. List every paper: candidate ID, title, venue, and PDF path.

2. **EXPLICITLY ASK the user** whether to proceed with decomposition. Show:
   - Number of papers to decompose
   - Each paper's title and candidate ID
   - The target output directory
   - A warning that decomposition can be resource-intensive

   **Never infer consent.** The user must explicitly confirm decomposition, regardless of prior approvals (download queue, screening, etc.). "Yes" to downloading is not "yes" to decomposing.

3. **Run decomposition** only after explicit user confirmation:
   ```bash
   python scripts/lit_review.py decompose-pdfs --manifest workspaces/<slug>/runs/<run-id>/handoff/download_manifest.json --run-dir workspaces/<slug>/runs/<run-id> --confirmed-by-user
   ```
   The `--confirmed-by-user` flag is required and will not proceed without it.

   The script calls the `ingest` CLI provided by `paper_pdf_ingest` (installed via `pip install -r requirements.txt`). Output follows the `1-paper-text/` layout: `paper.md`, per-section `md/` files, extracted images in `img/sec*/`, and an `INDEX.md`.

4. **Report outcomes**. The script writes `ingest_manifest.json` with per-paper status:
   - `succeeded` — decomposition completed, file counts
   - `failed` — error message, recommended action
   - `skipped` — already decomposed (resume case)

   Present a summary to the user. Do not read or interpret the decomposed artifacts at this step — that is the role of step 06 (triage).

5. Proceed to step 06 (triage).

## Resume rule

If `ingest/ingest_manifest.json` exists, check for any `failed` entries. Re-run only failed papers after confirming with the user. Skip successfully decomposed papers. If all papers are `succeeded` or `skipped`, proceed to step 06.
