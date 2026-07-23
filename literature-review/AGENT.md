# Literature-Review

Claude Code agent for systematic literature reviews. Discover papers from multiple academic sources, screen abstracts with AI, acquire PDFs, decompose them into markdown, deep-read with domain-specific lenses, and sync paper notes to Zotero.

## Setup

```bash
# Install Python dependencies (includes paper_pdf_ingest from GitHub)
pip install -r requirements.txt

# Install Playwright browser binaries (required for IEEE search + PDF acquisition)
python -m playwright install chromium
```

The ingest step (`scripts/pdf_decompose.py`) calls the `ingest` CLI provided by `paper_pdf_ingest`.

## Architecture

`/literature-review:new <topic>` walks a 10-step pipeline — see `.claude/skills/literature-review/SKILL.md` for the step table.
Progressive disclosure: each step reads its sub-file from `.claude/skills/literature-review/{00..09}-*.md`.

## Commands

| Command | Description |
|---------|-------------|
| `/literature-review:new <topic>` | Main pipeline. Re-invoking with a topic resumes from the latest non-empty artifact (see SKILL.md resume table). |
| `/literature-review:rerun <step> <topic>` | Re-run any single step against an existing workspace/run. |

## Pipeline

Full step-by-step: see `.claude/skills/literature-review/SKILL.md` pipeline table. The orchestrator walks 00→09 in order.

**Core principle**: Brief before query. Query before search. Gate before acquire. Ingest requires explicit confirm. No opinion without reading the paper.

Progressive disclosure: `.claude/skills/literature-review/SKILL.md` is the map; each step's sub-file under `.claude/skills/literature-review/` is the playbook.

## Directory Layout

```
.claude/
  skills/
    literature-review/       — main pipeline (progressive disclosure SKILL.md + 00–09)
    literature-review-rerun/ — re-run any single step
  agents/               — query-reviewer, abstract-screener, paper-reader
  commands/             — slash-command entry points
schemas/                — shared JSON Schema contracts (all skills)
providers/              — literature source adapters (IEEE, arXiv, Semantic Scholar, ...)
scripts/                — deterministic Python operations (CLI, validation, acquisition)
templates/              — reference templates & checklists
lenses/                 — domain-specific appraisal lenses
workspaces/             — per-topic research contexts
  <topic>/
    workspace.yaml      — topic config (Zotero binding, defaults, active lenses)
    briefs/             — research briefs (reusable)
    runs/               — execution runs
      <run_id>/
        research_brief.yaml
        queries.yaml
        search/         — raw records, normalized candidates
        screening/      — agent screening output
        download/       — approved queue, downloaded PDFs
        handoff/        — download manifest
        ingest/         — PDF decomposition artifacts
        reading/        — reading queue, paper cards
        notes/          — rendered paper cards, synthesis
        _audit/         — provenance & logs
    notes/              — cross-run synthesis
```

## Model Routing

| Agent | Role | Default Model | Reasoning |
|-------|------|---------------|-----------|
| query-reviewer | Review/refine Boolean queries | gpt-5.6-luna | high |
| abstract-screener | Screen abstracts against criteria | gpt-5.6-luna | high |
| paper-reader | Deep reading with domain lens | gpt-5.6-luna | high |

Model routing is configurable per skill via `.claude/agents/*.md` frontmatter. The orchestrator reads agent configs at invocation time.

## Provider Support

| Provider | Status | Search | PDF Acquire |
|----------|--------|--------|-------------|
| IEEE Xplore | Phase 1 | ✅ REST API via `IeeeXploreProvider` | ✅ CLI via `scripts/lit_review.py acquire-pdf` (Playwright; `IeeeXploreProvider.acquire()` stub) |
| arXiv | Phase 4 | Planned | Planned |
| Semantic Scholar | Phase 4 | Planned | N/A (metadata only) |
| CrossRef | Phase 4 | Planned | N/A (metadata only) |
