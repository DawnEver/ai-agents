# Phase 4 — PDF: on demand only

```bash
python scripts/to_pdf.py <input.docx> [output.pdf]
```

Default output: `<input-stem>.pdf` next to the input.

## When to use

- Uploads to IFS/Innovate UK (commercial impacts table, workplan, JCS) — these require PDF
- Final review before submission, external sharing

**Not** for the daily loop. If the user asks for "the Word file" or "update the doc", that's Phase 3 — don't reach for PDF.

## Caveats

- Requires MS Word installed (Word COM via pywin32). Fails if the file is open in Word — close it first.
- Conversion is invisible (no Word window), but the process is heavyweight — don't batch-convert unless asked.
- Converting the anchored template is fine; the bookmarks don't appear in the PDF.
