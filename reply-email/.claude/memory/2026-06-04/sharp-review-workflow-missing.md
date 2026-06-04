---
name: sharp-review-workflow-missing
description: sharp-review workflow script not on disk — reviews run inline instead of via Workflow
metadata:
  type: reference
created: 2026-06-04
accessed: 2026-06-04
tier: short
---

The sharp-review skill references `~/.claude/workflows/sharp-review.js` but neither that file nor a `~/.claude/workflows/` directory exists. The Codex takeover reviewer also failed with a model routing error (passed "sonnet" instead of a valid DeepSeek model name). As a result, sharp reviews currently run with inline parallel Agent calls rather than the structured Workflow orchestration the skill prescribes.

**How to apply:** Until the workflow script is created, run `/sharp-review` by spawning 2-3 parallel reviewers manually (general-purpose agents) and merging findings by hand. Write results to `.claude/sharp-review/YYYY-MM-DD.md`.
