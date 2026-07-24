---
name: literature-review
description: Conduct a systematic literature review — define scope, search across providers, screen abstracts, acquire PDFs, ingest, and choose from deep-read/synthesis/Zotero/bibliography options.
argument-hint: <topic-name>
allowed-tools: "Read,Write,Bash,Glob,Grep,Agent,Skill,WebFetch,WebSearch"
---

# /literature-review — Systematic literature review

You are the orchestrator. Given a topic name, guide the user through a flexible review workflow. The pipeline is suggestive, not rigid — the user can skip, reorder, or branch at any point.

## Pipeline

| Step | File | CLI | What happens |
|------|------|-----|--------------|
| 01 | `01-define.md` | `lit-review init` | Define topic & scope → `workspace.toml` + `research_brief.toml` |
| 02 | `02-search.md` | `lit-review search` | AI queries → multi-provider search → dedupe → screening packet |
| 03 | `03-acquire.md` | `lit-review acquire` | Script-first batch PDF acquisition with auth analysis |
| 04 | `04-ingest.md` | `lit-review ingest` | On-demand decomposition with cache reuse |
| — | `05-options.md` | `read`/`synthesize`/`export`/`stats` | Post-acquisition capabilities as a menu |

## How to execute

At the start of each step, Read the corresponding sub-file and follow it. This file is the map — sub-files are the playbook.

## Core principles

- **User in control**: every step is a suggestion. User can skip, branch, or go back.
- **Script-first**: deterministic operations use CLI scripts. Agent orchestrates, doesn't micro-manage.
- **No crypto theater**: no SHA-256 locking. User's verbal confirmation is the gate.
- **Cache everything**: already-searched, downloaded, or decomposed content is never re-processed without asking.
- **Single state file**: `run_state.json` tracks progress — one file to check for resume.

## Resume

Re-invoking `/literature-review <topic>` checks `workspaces/<slug>/run_state.json`:

| Step status | Action |
|-------------|--------|
| `ingest: done` | Show stats → options menu |
| `acquire: done` | Offer ingest or options menu |
| `search: done` | Offer acquire |
| `define: done` | Resume from search (step 02) |
| No state / fresh | Start from step 01 |

## Slug

Derive `<slug>` from the topic name (lowercase, non-alphanum → `-`, strip leading/trailing `-`).
