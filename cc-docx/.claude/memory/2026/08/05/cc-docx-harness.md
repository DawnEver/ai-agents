---
name: cc-docx-harness
description: Design decisions for the cc-docx Word↔Markdown round-trip harness
metadata:
  type: project
---

# cc-docx harness — build record (2026-08-05)

Built at user request to support KTP proposal work (Word form filling). Decided with user:

1. **Markdown-first**: all content transcribed to `.md`; iteration (AI + human comparison) happens in markdown; git diff is the review surface.
2. **docx = delivery**: daily output is a patched Word file (`md2docx`), not PDF.
3. **PDF on demand only**: `to_pdf.py` (Word COM) exists but is never part of the daily loop.
4. **Patch-back architecture** (not rebuild): `docx2md.py` anchors every block with invisible `ccxN` bookmarks; `md2docx.py` edits the original template in place of those anchors, preserving layout/styles. Chosen because KTP templates must stay on the official template.
5. Environment: Python 3.13 + python-docx + pywin32 on Windows; MS Word Office 16 installed; no LibreOffice/pandoc.

Work area: `workspace/260805-ktp_proposal/` holds the 4 KTP ref docs transcribed (fact find form, application form, workplan, commercial impacts).

Repo reality (learned 2026-08-05): cc-docx has NO nested .git (an earlier `git init` vanished, likely OneDrive sync) — it's tracked in the **root agents repo** (`DawnEver/ai-agents` on GitHub). User's PII policy: `workspace/` transcripts (real contact emails) are **local-only** — enforced via `cc-docx/workspace/` in the root `.gitignore`; never `git add` them. Harness files (scripts, skill, docs) are safe to commit.
