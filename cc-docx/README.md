# cc-docx

Word ↔ Markdown round-trip harness for Codex and Claude Code. Markdown is the working format (AI/human iteration, git diff); `.docx` is the delivery format; PDF is generated **on demand only**.

## Why markdown-first

- **AI/human comparison**: both read the same `.md` working copy; git diff shows exactly what changed between iterations
- **Format safety**: rendering never overwrites the template; extraction only adds invisible round-trip bookmarks
- **Deterministic**: extraction and rendering are scripted, not hand-edited

## Pipeline

```text
  template.docx ──docx2md──▶ workspace/ongoing/<yyMMdd>-<project>/*.md
                                     │
                    edit .md ◀───────┤  ← AI/human iterate here (the daily loop)
                                     │
  delivery.docx ◀──md2docx───────────┘  (patch back into template, styles preserved)
       │
       └──to_pdf──▶ delivery.pdf   (on demand: uploads / final review only)
```

Each active project lives in `workspace/ongoing/<yyMMdd>-<project>/`
(`260805-ktp-proposal/` etc.) with a `project.toml` recording the source
template paths, the iteration count, and the delivery outputs.

Two converters, one contract:

| Script | Direction | What it does |
|--------|-----------|--------------|
| `scripts/docx2md.py` | docx → md | Full-fidelity transcript: headings, emphasis, code, links, lists, tables (merged-cell aware), headers/footers. Every block gets an invisible bookmark anchor (`ccxN`) in the docx and a `<!-- ccxN -->` comment in the md |
| `scripts/md2docx.py` | md → docx | Patch-back: walks the **original** template, finds each anchor, replaces that block's content. Unanchored (new) blocks insert after the previous anchor. Original styles/layout survive |
| `scripts/to_pdf.py` | docx → pdf | Word COM (win32com). Not part of the daily loop — call only when a PDF is actually needed |

## Usage

Install Python dependencies first:

```bash
python -m pip install -r requirements.txt
```

PDF conversion additionally requires Microsoft Word on Windows. DOCX extraction and rendering do not require Word.

```bash
# 1. transcribe a Word template into the project working copy
python scripts/docx2md.py ref/Form.docx workspace/ongoing/260805-myproject/form.md

# 2. ...edit workspace/ongoing/260805-myproject/form.md...
#    ...and bump `iteration` in that project's project.toml

# 3. render the patched Word deliverable (default name gets today's date)
python scripts/md2docx.py workspace/ongoing/260805-myproject/form.md ref/Form.docx --track-changes
#    → workspace/ongoing/260805-myproject/out/Form-260805.docx

# 4. PDF only when needed
python scripts/to_pdf.py workspace/ongoing/260805-myproject/out/Form-260805.docx
```

## Invariants

- The original template `.docx` is **never edited in place** — `md2docx` writes to the Markdown project's `out/`
- Never delete bookmark anchors from the md (they are the round-trip map); unanchored blocks insert, they don't overwrite
- Re-extract to verify after any render: `docx2md` on the output should equal the input md (modulo your edits)
- PDF conversion opens Word invisibly; OneDrive-synced files are fine, but don't convert a file Word has open

## Work areas

- `workspace/ongoing/<yyMMdd>-<project>/` — active OneDrive-backed task directories
- `workspace/archived/<yyMMdd>/<yyMMdd>-<project>/` — completed tasks, moved intact
- `scripts/` — the converters (see `AGENTS.md` for the contract)
- `.agents/skills/docx/` — the Codex `$docx` skill; `.claude/skills/docx/` is the Claude Code wrapper

## Data lifecycle

- `workspace/ongoing/<yyMMdd>-<project>/` contains active OneDrive-backed tasks.
- `workspace/archived/<yyMMdd>/<yyMMdd>-<project>/` contains completed tasks, moved intact.
- Each task keeps templates in `src/`, authoritative Markdown and `project.toml` at its root, and rendered DOCX/PDF deliverables in its own `out/`.
- There is deliberately no repository-level `out/`; this prevents deliverables becoming detached from their source task.

## Conventions

Mirrors the other projects in `Sync/agents` (see root `README.md`): agent-specific skill folders, `.claude/memory/` for session memory (per `/rem` conventions), and `AGENTS.md` for shared operating notes.
