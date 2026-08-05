---
name: docx
description: Word↔Markdown round-trip workflow — transcribe .docx to markdown, iterate on markdown (AI/human comparison, git diff), render back to .docx, convert to PDF on demand. Daily delivery is Word; PDF only when actually needed.
argument-hint: <command> [docx-file] [md-file]
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
---

# /docx — Word ↔ Markdown round-trip

Markdown is the **working format** (iteration, comparison, diffing); `.docx` is the **delivery format**; PDF is **on demand only**. The pipeline lives in `scripts/` — see `AGENT.md` for the engineering contract.

## Workflow map

| Phase | File | Command | What happens |
|-------|------|---------|--------------|
| Extract | `01-extract.md` | `python scripts/docx2md.py <in.docx> [out.md]` | Transcribe to markdown; stamps invisible `ccxN` bookmarks into the docx so content can be patched back |
| Edit | `02-edit.md` | edit the `.md` | The daily loop: AI and human iterate on markdown; anchors (`<!-- ccxN -->`) are the map, don't delete them |
| Render | `03-render.md` | `python scripts/md2docx.py <in.md> <template.docx> [out.docx]` | Patch the edited markdown back into the original template, styles preserved |
| PDF | `04-pdf.md` | `python scripts/to_pdf.py <in.docx> [out.pdf]` | Word COM conversion — only when a PDF is actually needed |

## How to execute

Read the phase file for the step you're at and follow it. This file is the map; phase files are the playbook. Default output is `out/` for rendered docx and `work/<name>/` for transcripts.

## Hard rules

1. **Markdown is authoritative** for content; the template docx is read-only input for renders.
2. `<!-- ccxN -->` comments and the matching `ccxN` bookmarks are the round-trip map — never delete or reorder them.
3. To fill a blank answer slot: write the text on the same line as its anchor (`<!-- ccx7 --> My answer`). An anchor line alone keeps the block empty.
4. New content (no anchor) is inserted after the previous anchored block at the position where you wrote it.
5. Verify every render: re-extract the output and diff against the input md.
6. PDF last, never first. Ask: does the user need a PDF, or a Word file? Default is Word.

## Examples

```bash
# transcribe a template
python scripts/docx2md.py "ref/Workplan.docx" work/ktp-proposal/workplan.md

# ...edit work/ktp-proposal/workplan.md...

# render the filled Word deliverable (never overwrite the template)
python scripts/md2docx.py work/ktp-proposal/workplan.md "ref/Workplan.docx" out/Workplan-filled.docx

# PDF only when needed
python scripts/to_pdf.py out/Workplan-filled.docx
```
