# Ingest Error Triage

Common `paper_pdf_ingest` failure modes and their fixes.

## Error Patterns

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `marker_single: command not found` | marker-pdf not installed | Auto-fallback to pymupdf4llm. Install marker-pdf for better layout fidelity: `pip install marker-pdf` |
| `CUDA out of memory` | GPU VRAM insufficient for marker-pdf | Auto-fallback to pymupdf4llm. Or reduce batch size in marker config. |
| `No sections found` | Poorly structured PDF (scanned, no TOC) | pymupdf4llm fallback handles this; if both fail, the PDF may be image-only — needs OCR. |
| `PDF is encrypted` | DRM-protected PDF | Cannot ingest. Report to user, skip this paper. |
| `File not found` | PDF was moved or deleted after download | Check `handoff/download_manifest.json` for correct path. Re-acquire if needed. |
| `Timeout after 300s` | Very large PDF or slow hardware | Increase timeout in pdf_decompose.py config. Consider splitting PDF first. |
| `Permission denied` | Output directory not writable | Check `PAPER_INGEST_ROOT` and run directory permissions. |

## Tool Selection Logic

The ingest script selects the best available tool:
1. **marker-pdf** (preferred): Best layout fidelity, figure/table preservation. Requires GPU with ≥4 GB VRAM.
2. **pymupdf4llm** (fallback): Fast, rule-based, works on CPU. Lower layout fidelity but reliable.

## Output Structure

After successful ingest:
```
1-paper-text/
  paper.md          ← title + abstract + section index (entry point)
  md/               ← per-section markdown (01-intro.md, 02-..., ...)
  img/sec*/         ← per-section images + rendered figure/table pages
  INDEX.md          ← figure/table number ↔ file mapping
```

## Hard Rules

- Never read, interpret, or analyze PDFs or decomposed artifacts during ingest. That's the read skill's job.
- Ingest requires a SEPARATE explicit user confirmation. Never infer it from download approval.
- Report per-paper outcomes: succeeded / failed / skipped.
