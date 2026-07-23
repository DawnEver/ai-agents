---
name: literature-review-rerun
description: Re-run a single step of the literature-review pipeline against an existing topic. Preserves audit trail and never overwrites archived runs.
argument-hint: <step> <topic>
allowed-tools: "Read,Write,Bash,Glob,Grep,Agent,Skill"
---

# /literature-review:rerun — Re-run one step

Usage:
```
/literature-review:rerun 5 edge-ai        # re-run ingest (step 05)
/literature-review:rerun 4 edge-ai        # re-run acquisition (step 04)
/literature-review:rerun 3 edge-ai        # re-run search + screen (step 03)
/literature-review:rerun 2 edge-ai        # re-plan queries (step 02)
/literature-review:rerun 1 edge-ai        # re-write brief (step 01)
/literature-review:rerun 9 edge-ai        # re-sync Zotero (step 09)
```

## How it works

1. Read `.claude/skills/literature-review/<step>-*.md` for the requested step (e.g. `0` → `00-workspace.md`, `1` → `01-brief.md`, `5` → `05-ingest.md`). Match the step token exactly — `1` must not pick up `01-*` files other than `01-brief.md`.
2. Determine the workspace: derive the slug from the topic name and locate `workspaces/<slug>/`. If the slug is archived (glob-match `archived/*/<slug>/`), operate against the archive — any new output is written with a `.<timestamp>` suffix, never overwriting the archived snapshot.
3. Execute that step's playbook against the workspace.
4. Steps 1, 2, and 3 are the most common rerun cases (iterating on the brief or queries). Steps 4–9 are less common but fully supported.

## Hard rules

- **Archive-safe**: reruns against `archived/*/<slug>/` never overwrite the existing snapshot; suffix outputs with a `.<timestamp>` (e.g. `queries.2026-07-23T14-30-00.yaml`).
- **Re-validate gates**: any step whose output is gated (brief, queries, download queue, ingest confirmation) must re-validate the gate with the user. An old approval is not a blank cheque.
- **SHA-256 chain**: if a rerun changes the brief, all downstream approvals are invalidated. Warn the user and confirm before proceeding.
- **Preserve raw responses**: never delete original search responses, screening decisions, or download manifests. Append new results alongside old ones.
