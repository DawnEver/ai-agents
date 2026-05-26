---
name: post-new
description: Generate platform-adapted articles from a GitHub repo URL — spawns platform-specific agents for generation.
argument-hint: <github-url> [platform]
allowed-tools: "Read,Write,Bash,Glob,Grep,Agent,Skill,WebFetch"
---

# /post:new — Generate Articles from GitHub Repo

You are the orchestrator. Given a GitHub repo URL, clone and deeply explore the codebase, write a structured analysis, then spawn platform-specific agents to generate articles.

## Pipeline Overview

| Step | File | What Happens |
|------|------|-------------|
| 1-3 | `01-clone.md` | Parse URL, clone repo, fetch gh metadata |
| 4 | `02-explore.md` | Deep code exploration |
| 5 | `03-analysis.md` | Write `repo-analysis.md` |
| 5.5 | `04-brief-gate.md` | ⭐ 选题确认 — angles + titles, iterate until approved |
| 6-6.5 | `05-images.md` | Output dirs + image manifest |
| 7 | `06-spawn.md` | Spawn platform writer agents in parallel |
| 8 | `07-user-review.md` | ⭐ Mandatory user read-through before review |
| 9 | `08-review.md` | 🔒 三方会审 — MANDATORY, cannot skip |
| 10 | `09-summary.md` | Present results + next steps |

## How to Execute

Run each step in order. **At the start of each step, Read the corresponding sub-file** and follow its instructions. The sub-file is the detailed playbook — this SKILL.md is just the map.

Key principles:
- Research and brief ALWAYS come before writing. Never skip the user confirmation gates.
- Gates (Steps 5.5 and 8) are **iterative** — go back and forth until the user explicitly approves.
- Never run 三方会审 before the user has read and okayed the drafts.
- 三方会审 (Step 9) is **mandatory**. No article reaches publish without passing review.
