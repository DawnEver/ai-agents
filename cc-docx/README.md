# cc-docx

Word ↔ Markdown round-trip harness for Claude Code. Markdown is the working format (AI/human iteration, git diff); `.docx` is the delivery format; PDF is generated **on demand only**.

## Why markdown-first

- **AI/human comparison**: both read the same `.md` working copy; git diff shows exactly what changed between iterations
- **Format safety**: no accidental Word corruption on every edit — the template `.docx` is only touched at render time
- **Deterministic**: extraction and rendering are scripted, not hand-edited

## Pipeline

```text
  template.docx ──docx2md──▶ work/<name>/<name>.md      (transcript, anchored)
                                  │
                    edit .md ◀────┤  ← AI/human iterate here (the daily loop)
                                  │
  delivery.docx ◀──md2docx────────┘  (patch back into template, styles preserved)
       │
       └──to_pdf──▶ delivery.pdf   (on demand: uploads / final review only)
```

Two converters, one contract:

| Script | Direction | What it does |
|--------|-----------|--------------|
| `scripts/docx2md.py` | docx → md | Full-fidelity transcript: headings, emphasis, code, links, lists, tables (merged-cell aware), headers/footers. Every block gets an invisible bookmark anchor (`ccxN`) in the docx and a `<!-- ccxN -->` comment in the md |
| `scripts/md2docx.py` | md → docx | Patch-back: walks the **original** template, finds each anchor, replaces that block's content. Unanchored (new) blocks insert after the previous anchor. Original styles/layout survive |
| `scripts/to_pdf.py` | docx → pdf | Word COM (win32com). Not part of the daily loop — call only when a PDF is actually needed |

## Usage

```bash
# 1. transcribe a Word template into the working copy
python scripts/docx2md.py ref/Form.docx work/form/form.md

# 2. ...edit work/form/form.md (that's the iteration surface)...

# 3. render the patched Word deliverable
python scripts/md2docx.py work/form/form.md ref/Form.docx out/Form-filled.docx

# 4. PDF only when needed
python scripts/to_pdf.py out/Form-filled.docx
```

## Invariants

- The original template `.docx` is **never edited in place** — `md2docx` reads it and writes a new file (default `out/`)
- Never delete bookmark anchors from the md (they are the round-trip map); unanchored blocks insert, they don't overwrite
- Re-extract to verify after any render: `docx2md` on the output should equal the input md (modulo your edits)
- PDF conversion opens Word invisibly; OneDrive-synced files are fine, but don't convert a file Word has open

## Work areas

- `work/` — per-document working copies (`.md`). One subdir per document: `work/<doc>/<doc>.md`
- `out/` — rendered deliverables (gitignored)
- `scripts/` — the converters (see `AGENT.md` for the contract)
- `.claude/skills/docx/` — the `/docx` skill wrapping this pipeline

## Conventions

Mirrors the other projects in `Sync/agents` (see root `README.md`): `.claude/skills/` for skills, `.claude/memory/` for session memory (per `/rem` conventions), `AGENT.md` for agent operating notes.
