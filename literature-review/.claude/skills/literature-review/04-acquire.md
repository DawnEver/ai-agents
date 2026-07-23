# Step 04 — PDF acquisition

Build a download queue from screened candidates, present to the user for selection, and acquire PDFs via browser-based download.

## Inputs
- `workspaces/<slug>/runs/<run-id>/screening/screening_stage1.jsonl` — screened candidates

## Output

```
workspaces/<slug>/runs/<run-id>/
  download/
    download_queue.json        ← queue with user selections + approval
    download_queue.csv         ← human-readable queue summary
    pdf_match/
      match_report.json        ← candidate-to-PDF matches
    pdfs/                      ← acquired PDF files
      <candidate_id>.pdf
      ...
  handoff/
    download_manifest.json     ← manifest for step 05 ingest
    download_manifest.md       ← human-readable manifest summary
```

## Steps

1. **Make the download queue** from screened-in candidates:
   ```bash
   python scripts/lit_review.py make-download-queue --screening workspaces/<slug>/runs/<run-id>/screening/screening_stage1.jsonl --out workspaces/<slug>/runs/<run-id>/download/
   ```
   Only candidates marked `include` in screening are added to the queue.
   Produces `download/download_queue.json` and `download/download_queue.csv`.

2. **Present the queue to the user**. Show candidate IDs, titles, venues, and screening decisions. The user selects which candidates to download. Do NOT auto-download anything.

3. **Approve selections**:
   ```bash
   python scripts/lit_review.py approve-download-queue --queue workspaces/<slug>/runs/<run-id>/download/download_queue.json --candidate-id <id>... --approved-by <name>
   ```
   Only approved candidates proceed to download.

4. **Browser login** — if publisher authentication is required:
   ```bash
   python scripts/lit_review.py browser-login --profile <profile-path>
   ```
   This opens a browser for the user to log in. The session is saved for subsequent PDF acquisition.

   **Hard rule**: browser profiles live OUTSIDE the repository at `%LOCALAPPDATA%/literature-review/browser-profiles/`. Never commit cookies or session data.

5. **Acquire PDFs** for approved candidates:
   ```bash
   python scripts/lit_review.py acquire-pdf --queue workspaces/<slug>/runs/<run-id>/download/download_queue.json --run-dir workspaces/<slug>/runs/<run-id> --profile <profile-path>
   ```
   Downloads are sequential with polite delays between requests. Failed downloads are logged with the reason.

6. **Match** downloaded PDFs to candidates:
   ```bash
   python scripts/lit_review.py match-pdfs --queue workspaces/<slug>/runs/<run-id>/download/download_queue.json --run-dir workspaces/<slug>/runs/<run-id>
   ```
   Produces `download/pdf_match/match_report.json` mapping candidate IDs to PDF file paths. Reports any candidates that could not be matched.

7. **Create the download manifest** for step 05:
   ```bash
   python scripts/lit_review.py make-download-manifest --matches workspaces/<slug>/runs/<run-id>/download/pdf_match/match_report.json --out workspaces/<slug>/runs/<run-id>/handoff/
   ```
   Produces `handoff/download_manifest.json` and `handoff/download_manifest.md`.

8. Report acquisition statistics (requested, downloaded, failed) and proceed to step 05 (ingest).

## Resume rule

| Existing artifact | Action |
|-------------------|--------|
| `handoff/download_manifest.json` | Skip to step 05 |
| `download/pdf_match/match_report.json` | Skip to step 7 (make manifest) |
| `download/download_queue.json` (all approved) | Skip to step 4 (browser login) |
| `download/download_queue.json` (partial approval) | Resume at step 2 (present queue) |
| `screening/screening_stage1.jsonl` | Start from step 1 |
