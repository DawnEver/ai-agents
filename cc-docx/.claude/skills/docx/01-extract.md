# Phase 1 — Extract: docx → markdown

```bash
python scripts/docx2md.py <input.docx> [output.md]
```

Default output name: `<input-stem>.md` next to the input. For KTP work, keep transcripts under `work/ktp-proposal/`.

## What happens

- Every body block (paragraph, list item, heading, table) is transcribed in document order, in markdown:
  - headings → `#`–`######`, bold/italic/code → `**x**` / `*x*` / `` `x` ``, hyperlinks → `[text](url)`
  - lists → `1.` / `-` with indent by level
  - tables → markdown tables, **grid-indexed**: merged cells (gridSpan/vMerge) repeat content at every spanned position, so md ↔ docx map 1:1
  - headers/footers → `> **HEADER**` blockquotes at the top (anchored too)
- The input docx is **saved in place** with an invisible `ccxN` bookmark pair on every block — these are the patch-back anchors. Bookmarks are invisible in Word.
- Idempotent: re-running on an anchored docx reuses existing ids and only anchors new blocks.

## Anchor format in the md

| Block | Markdown |
|-------|----------|
| paragraph / heading / list item | `<!-- ccx5 --> text` (anchor inline, at line start) |
| empty paragraph | `<!-- ccx7 -->` (anchor alone) |
| table | `<!-- ccx8 -->` on its own line, then the table |

## Verify

Spot-check that the transcript is faithful: content order matches the source, tables kept their shape, no `****` artifacts (adjacent same-format runs are merged — if you see `**a** **b**`, the source has genuinely separate styled runs).
