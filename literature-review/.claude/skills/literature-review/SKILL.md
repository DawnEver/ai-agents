---
name: literature-review
description: Conduct a systematic literature review — define brief, plan queries, search across providers, screen abstracts, acquire PDFs, ingest, triage, deep-read, synthesise, and sync to Zotero.
argument-hint: <topic-name>
allowed-tools: "Read,Write,Bash,Glob,Grep,Agent,Skill,WebFetch,WebSearch,Workflow"
---

# /literature-review — Systematic literature review

You are the orchestrator. Given a topic name, walk the pipeline below in order. The pipeline is gated: briefing before querying, querying before searching, and explicit user approval before acquisition or decomposition.

## Pipeline

| Step | File | What happens |
|------|------|--------------|
| 0 | `00-workspace.md` | Create/select workspace → `workspace.yaml` |
| 1 | `01-brief.md` | Research brief + concept taxonomy → user gate |
| 2 | `02-queries.md` | Query planning → user gate (SHA-256 binding) |
| 3 | `03-search-screen.md` | Multi-provider probe → search → dedupe → agent abstract screen |
| 4 | `04-acquire.md` | Download queue → user gate → browser PDF acquire |
| 5 | `05-ingest.md` | PDF decomposition via paper_pdf_ingest (explicit user confirm) |
| 6 | `06-triage.md` | Portfolio triage — rank papers → reading queue  (Phase 2) |
| 7 | `07-read.md` | Deep reading + domain lens → paper cards  (Phase 2) |
| 8 | `08-synthesis.md` | Cross-paper comparison → synthesis (optional)  (Phase 2) |
| 9 | `09-zotero.md` | Zotero bridge bidirectional sync  (Phase 3) |

## How to execute

At the start of each step, Read the corresponding sub-file and follow it. This file is the map — sub-files are the playbook.

## Resume table (which step to enter on re-invocation)

Re-invoking `/literature-review <topic>` resumes from the latest non-empty artifact:

| Existing artifact | Enter step |
|-------------------|-----------|
| `archived/*/<slug>/` (glob) | Confirm rerun — use `/literature-review:rerun` instead |
| `runs/<id>/ingest/ingest_manifest.json` | 06 |
| `runs/<id>/handoff/download_manifest.json` | 05 |
| `runs/<id>/download/download_queue.json` (all approved) | 04 |
| `runs/<id>/screening/screening_stage1.jsonl` | 04 |
| `runs/<id>/search/records.jsonl` | 03 (skip to dedupe) |
| `runs/<id>/queries.yaml` (approved) | 03 |
| `runs/<id>/research_brief.yaml` (approved) | 02 |
| `workspaces/<slug>/workspace.yaml` exists | 01 |
| nothing | 00 |

## Hard rules

- **Brief before query**: step 01 must complete with an approved brief before step 02 begins.
- **Query before search**: step 02 must complete with approved queries before step 03 begins.
- **Gate before acquire**: step 04 must have explicit user approval of the download queue before any PDF is acquired.
- **Ingest requires explicit confirm**: step 05 must explicitly ask the user before decomposition. Never infer decomposition consent from download approval.
- **Preserve raw responses, provenance, and audit logs**: every step records its inputs, outputs, and decisions so the run is reproducible and auditable.
- **Respect publisher terms and rate limits**: throttle searches, honour robots.txt, and never bulk-scrape publisher sites.

## Slug

Derive `<slug>` from the topic name (lowercase, non-alphanum → `-`, strip leading/trailing `-`). If the user passes an existing slug, use the resume table above.
