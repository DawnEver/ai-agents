---
name: slides
description: Template-faithful PowerPoint decks — reuse slides of the user's template as patterns, pour figures/text/tables into their slots from a deck.toml spec, build a new .pptx, lint it and render it with Microsoft PowerPoint to look at the result. Also rewords existing decks via anchored markdown. PDF only on demand.
argument-hint: <task or deck> [template.pptx] [figures dir]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# /slides — template-faithful decks

The spec (`deck.toml`) is the **working copy**; the user's template `.pptx` is read-only input;
the built `.pptx` is the **delivery**; the rendered preview is how you **see** it. Engineering
contract: `AGENTS.md`. Run scripts from the `cc-slides/` directory.

## Workflow map

| Phase | File | Command | What happens |
|-------|------|---------|--------------|
| Inspect | `01-inspect.md` | `python3 scripts/inspect_slides.py <template> [--slides N]` | Find the pattern slide(s); read their slot labels |
| Spec | `02-spec.md` | write `deck.toml` | Map inputs → patterns and slots; `keep` template slides |
| Build | `03-build.md` | `python3 scripts/build_slides.py <deck.toml>` | New dated deck in the task's `out/` |
| Verify | `04-verify.md` | `lint_slides.py` then `preview_slides.py`, read `contact.png` | Mandatory after every build |
| Reword | `05-reword.md` | `slides2md.py` → edit → `md2slides.py` | Text-only edits of an existing deck |
| PDF | `06-pdf.md` | `python3 scripts/to_pdf.py <deck>` | Only when a PDF is actually needed |

## How to execute

Read the phase file for the step you're at and follow it. Tasks live in
`workspace/ongoing/<yyMMdd>-<slug>/` (`deck.toml`, `project.toml`, `src/`, `figures/`, `out/`);
bump `iteration` in `project.toml` on each substantive rebuild and append delivered files to
`outputs`.

## Hard rules

1. Never modify the template or the user's original files; copy them into the task's `src/` /
   `figures/`. Builds write new files only.
2. Every build → `lint` → `preview` → **read `contact.png`** (then single slides if anything looks
   off) before telling the user it is done. Report remaining warnings plainly.
3. Keep image aspect (`contain` default, `cover` if the user wants boxes filled). `stretch` only on request.
4. No invented wording: titles/captions come from the inputs or the user. If a name is a guess,
   say so and ask.
5. The first preview in a session opens PowerPoint in the background — say so once.
6. PDF last, never first.
