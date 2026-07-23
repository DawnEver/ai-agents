# Manuscript-Review

Claude Code agent for reviewing academic papers. Ingest a PDF, profile the literature, build a shared summary (folding in that landscape and the venue type), fan out 4-angle 锐评 across Sonnet subagents and Codex/DeepSeek takeover, then polish an orchestrator-generated draft (user-edited) into publishable **plain-text** reviewer comments.

## Setup

```bash
# Clone the ingest library alongside this repo
git clone https://github.com/DawnEver/paper_pdf_ingest.git

# Create shared venv and install it
python -m venv ~/.local/share/manuscript-review-venv
~/.local/share/manuscript-review-venv/bin/pip install -e paper_pdf_ingest/
```

The ingest step (`scripts/ingest.py`) delegates to `paper_pdf_ingest.__main__:main`.

## Architecture

`/manuscript-review:new <pdf>` walks a 9-step pipeline — see `SKILL.md` for the step table.
Progressive disclosure: each step reads its sub-file from `.claude/skills/manuscript-review/{00..08}-*.md`.

## Commands

| Command | Description |
|---------|-------------|
| `/manuscript-review:new <pdf>` | Main pipeline. Re-invoking with a slug resumes from the latest non-empty artifact (see SKILL.md resume table). |
| `/manuscript-review:rerun <step> <slug>` | Re-run any single step (replaces old archive/repolish skills). |

## Pipeline

Full step-by-step: see `SKILL.md` pipeline table. The orchestrator walks 00→08 in order.

**Core principle**: Literature before consensus. Consensus before fanout. Fanout before draft. Draft before polish. No opinion without reading `summary.md`. Polisher never invents.

Progressive disclosure: `SKILL.md` is the map; each step's sub-file under `.claude/skills/manuscript-review/` is the playbook.

## Directory Layout

```
paper_pdf_ingest/       — STANDALONE git repo (not tracked here); PDF→markdown library
.claude/
  skills/
    manuscript-review/       — main pipeline (progressive disclosure SKILL.md + 01–08)
    manuscript-rerun/        — re-run any single step
  agents/               — 4 reviewers + polisher
ongoing/                — papers currently under review
  <slug>/
    review-config.md    — step 00: lang: en|zh (intermediate-file language)
    0-raw.pdf           — original (gitignored at folder level)
    1-paper-text/       — step 01: ingested text + images
      paper.md          — title + abstract + section index (entry point)
      md/               — per-section markdown (01-intro.md, 02-..., ...)
      img/sec*/         — per-section images + rendered figure/table pages
      INDEX.md          — figure/table number ↔ file mapping
      appended/         — if PDF contains multiple papers (e.g. conference versions)
    2-review/           — steps 02–05: review materials
      summary.md        — consensus (every agent reads first, incl. Obvious gaps)
      angles.md         — chosen angles + optional router overrides
      critiques/        — one .md per reviewer agent
      critiques.md      — aggregated, deduped, ranked
    3-response/         — steps 06–07: generated draft → publishable response
      draft.md          — orchestrator-generated draft (user-edited)
      final.md          — polished plain-text review
archived/YYMMDD/<slug>/  — completed reviews, date-prefixed for chronological sorting (mirrors ongoing/ 0-1-2-3 structure)
style/profile.md        — GLOBAL: synthesised voice + 10-slug rolling samples
critiques-library/
  angles.md             — GLOBAL: deduped angle library (name, aliases, hit-count, precision, sample)
templates/              — default-angles, polish-checklist, summary-template
```

## Model Routing

| Agent | Default router |
|-------|---------------|
| novelty, experiments, freestyle | `sonnet-vision` |
| methodology | `takeover-codex` (deep reasoning; DeepSeek as alternative) |

Per-paper overrides in `angles.md`; step 04 invokes the `manuscript-review-fanout` workflow which resolves routing: `angles.md` override > agent frontmatter default.
Sonnet reviewers run directly; Codex/DeepSeek reviewers use MCP-takeover relay (inlines summary + literature + sections via `call_model`).
