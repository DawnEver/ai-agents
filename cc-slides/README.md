# cc-slides

Template-faithful slide decks for Codex and Claude Code. You keep your own PowerPoint template;
the agent writes a small spec that pours figures, text and tables into slides of that template,
builds a new `.pptx`, and **renders it with Microsoft PowerPoint to check what it produced**.

## Why spec-first (not markdown-first)

Word documents are text flows, so `cc-docx` round-trips through Markdown. Slides are 2-D: the
position of every box carries meaning. So the working copy is `deck.toml`, which reuses template
slides as *patterns* (their title, picture, text and table boxes become numbered slots), and the
verification step is visual. Markdown is used only to reword an existing deck.

## Pipeline

```text
template.pptx ──inspect──▶ slot map (title, image[0], image[1] …)
                               │
                  write deck.toml ◀──┐   ← agent/human iterate here
                               │     │
out/<stem>-<yyMMdd>.pptx ◀─build─┘     │
        │                            │
        ├─lint───▶ distortion / off-slide / overlap / overflow
        └─preview▶ out/preview/…/contact.png ──look──┘
                         (PDF via PowerPoint → PNG via Ghostscript)

existing.pptx ──slides2md──▶ deck.md ──edit wording──▶ md2slides ──▶ new .pptx
```

| Script | What it does |
|--------|--------------|
| `scripts/inspect_slides.py` | Shapes, geometry and slot labels of a deck (markdown or `--json`) |
| `scripts/build_slides.py` | `deck.toml` + template → new deck; patterns, `keep`, contain/cover images, text, tables, notes |
| `scripts/lint_slides.py` | Deterministic layout checks |
| `scripts/preview_slides.py` | Per-slide PNGs + contact sheet via PowerPoint |
| `scripts/to_pdf.py` | PDF on demand via PowerPoint |
| `scripts/slides2md.py` / `md2slides.py` | Anchored wording round-trip for existing decks |

## Example

```toml
# workspace/ongoing/260930-byd-map-fill/deck.toml
template = "src/Reference.pptx"
base = "figures"

[patterns.three-up]
slide = 19          # image[0] top-left, image[1] top-right, image[2] bottom-centre

[[slides]]
keep = 1            # the template's cover slide, unchanged

[[slides]]
pattern = "three-up"
title = "Efficiency Map"
images = ["map_efficiency.png", "lines_efficiency.png", "cells_efficiency.png"]
notes = "Stations solved on a 14 x 23 grid."
```

```bash
python3 scripts/inspect_slides.py src/Reference.pptx --slides 19
python3 scripts/build_slides.py workspace/ongoing/260930-byd-map-fill/deck.toml
python3 scripts/lint_slides.py  workspace/ongoing/260930-byd-map-fill/out/Reference-260930.pptx
python3 scripts/preview_slides.py workspace/ongoing/260930-byd-map-fill/out/Reference-260930.pptx
```

Full spec reference: `scripts/build_slides.py` docstring; engineering contract: `AGENTS.md`.

## Requirements

```bash
python3 -m pip install -r requirements.txt
```

Preview/PDF: Microsoft PowerPoint (macOS or Windows) and Ghostscript (`brew install ghostscript`).
Building, inspecting, linting and the wording round-trip need neither.

## Work areas

- `workspace/ongoing/<yyMMdd>-<slug>/` — active tasks (`deck.toml`, `project.toml`, `src/`, `figures/`, `out/`)
- `workspace/archived/<yyMMdd>/<slug>/` — completed tasks, moved intact
- `.claude/skills/slides/` — the `/slides` skill; `.agents/skills/slides/` is the Codex `$slides` launcher
