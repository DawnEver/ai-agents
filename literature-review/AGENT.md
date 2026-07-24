# Literature-Review

Claude Code agent for systematic literature reviews. Discover papers from multiple academic sources, screen abstracts with AI, acquire PDFs via script, decompose on demand, and choose from deep-reading, synthesis, Zotero sync, or bibliography export.

## Setup

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Architecture

`/literature-review:new <topic>` guides a 4-step core pipeline + flexible options menu.

**Core principle**: Define → Search → Acquire → Ingest → user chooses what to do next. Not linear, not forced.

## Commands

| Command | Description |
|---------|-------------|
| `lit-review init <topic>` | Create workspace + workspace.toml |
| `lit-review search --topic <slug>` | End-to-end: queries → probe → search → dedupe → screening packet |
| `lit-review acquire --topic <slug>` | End-to-end: queue → auth → download → match → manifest |
| `lit-review ingest --topic <slug>` | On-demand PDF decomposition with cache reuse |
| `lit-review import-screening --topic <slug> --batch ...` | Import agent-authored screening decisions |
| `lit-review read --topic <slug> --paper <id> [--lens <name>]` | Deep-read a paper with optional domain lens |
| `lit-review synthesize --topic <slug>` | Cross-paper synthesis from reading cards |
| `lit-review export --topic <slug> [--format ...]` | Export paper cards to markdown/csv/bibtex/json |
| `lit-review stats --topic <slug> [--plots]` | Summary statistics + charts |
| `lit-review login [--profile ...]` | Browser login for publisher authentication |

## Pipeline

| Step | What happens |
|------|-------------|
| 01 Define | Interactive topic scoping + concept taxonomy → `workspace.toml` + `research_brief.toml` |
| 02 Search & Screen | Agent generates queries → `lit-review search` runs probe→search→dedupe→packet → AI screens all abstracts |
| 03 Acquire | Agent analyzes auth once → user configures → `lit-review acquire` batch-downloads all PDFs |
| 04 Ingest | `lit-review ingest --dry-run` checks cache → user picks papers → `lit-review ingest` decomposes |
| Options | `lit-review read` / `synthesize` / `export` / `stats` — user picks, non-linear |

## Directory Layout

```
.claude/
  skills/literature-review/  — pipeline orchestrator + step playbooks (01-05)
  agents/                    — query-reviewer, abstract-screener, paper-reader
  commands/literature-review/ — slash-command entry point
literature_review/           — Python package
  cli.py                     — unified CLI (12 commands)
  models.py                  — all dataclass models
  providers/                 — literature source adapters (IEEE + abstract base)
  pipeline/                  — orchestrator + step implementations
  review/                    — screen, reader, synthesis, extract
  search/                    — query engine, dedup
  acquire/                   — PDF download (Playwright)
  export/                    — render (markdown/csv) + plot (matplotlib)
  ai/                        — LiteLLM client + model registry
  utils/                     — state tracking, schema, paths, log
lenses/                      — domain-specific appraisal lenses (.toml)
workspaces/                  — per-topic research contexts
  <topic>/
    workspace.toml           — topic config
    research_brief.toml      — approved scope + concept taxonomy
    queries.toml             — Boolean search queries
    run_state.json           — single-file progress tracking
    search/                  — raw records, candidates, deduped results
    screening/               — AI screening output
    download/                — queue, PDFs, match reports
    handoff/                 — download manifest
    ingest/                  — per-paper decomposition artifacts (cached)
    reading/                 — paper cards from deep reading
    notes/                   — cross-paper synthesis
    export/                  — rendered exports + plots
```

## Model Routing

| Agent | Role | Default Model | Reasoning |
|-------|------|---------------|-----------|
| query-reviewer | Review/refine Boolean queries | gpt-5.6-luna | high |
| abstract-screener | Screen abstracts against criteria | gpt-5.6-luna | high |
| paper-reader | Deep reading with domain lens | gpt-5.6-luna | high |

## Provider Support

| Provider | Status | Search | PDF Acquire |
|----------|--------|--------|-------------|
| IEEE Xplore | Phase 1 | REST API | Playwright (script-first) |
| arXiv | Planned | Planned | Planned |
| Semantic Scholar | Planned | N/A (metadata) | N/A |
| CrossRef | Planned | N/A (metadata) | N/A |
