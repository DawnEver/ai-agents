---
name: word-export-gotchas
description: export_article.py (python-docx) gotchas — single run ignores \n, verbatim code/markdown fences, $/$$ formula raw-preservation, currency false-positive
metadata:
  type: retrospect
created: 2026-06-18
accessed: 2026-06-18
tier: short
access_count: 0
---

# Word Export Gotchas (export_article.py / python-docx)

Session: made `/post-publish` Word export preserve code blocks and formulas 原样, per user request.

## python-docx: a single run IGNORES "\n"
`run.add_run("a\nb")` does NOT create a line break — the whole string renders on one line, so multi-line code blocks silently collapse. Fix: split on "\n" and emit `run.add_break()` between lines (one run per line). This was the root cause of code blocks looking mangled.

## Code blocks: preserve 原样 as markdown
User wanted code kept verbatim INCLUDING the ``` fences and language tag, as raw markdown source (so it round-trips on import). So in the fence handler, keep the opening fence line (`line.rstrip()`, incl. lang) and re-emit a closing ``` — don't strip them. Render monospace (Consolas via `w:rFonts` ascii/hAnsi), non-italic, **no grey shading** (user rejected the `w:shd` F0F0F0 fill).

## Formulas: keep raw, never render
`$$...$$` (block) and `$...$` (inline) are preserved verbatim (incl. delimiters) as code-style runs — no LaTeX rendering. Two real bugs to avoid when adding this:
- **Currency false-positive**: `\$[^$]+\$` matches prose like "$5 and $10". Fix: require the opening `$` to be followed by a non-space, non-digit char → `\$[^\s\d$][^$\n]*\$`. Currency ($ + digits) no longer matches; real formulas ($x, $a+b$) still do.
- **Unterminated `$$` swallows the document**: scanning to a closing `$$` that never comes consumes every remaining line into one block. Fix: look ahead for the closing `$$` first; if absent, treat the opener as literal text and fall through.

## Clipboard is manual, not in the script
`/post-publish` populates the clipboard via PowerShell `Set-Clipboard` in the skill steps — `export_article.py` only writes the .docx. So sharp-review "doc/impl mismatch" findings about clipboard format are false positives: the platform `.md` docs describe the manual clipboard step, which no script enforces. The Word doc is the 插图参照 (image-insertion reference); the markdown goes to clipboard for import.
