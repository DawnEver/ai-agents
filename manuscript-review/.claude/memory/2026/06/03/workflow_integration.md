---
name: workflow-integration
description: Steps 02 and 04 migrated to Workflow-based execution; MCP takeover enables multi-provider fanout
metadata:
  type: project
---

# Workflow Integration (2026-06-03)

Steps 02 (literature) and 04 (fanout) converted from manual Agent/Skill orchestration to Workflow-based execution.

**Why:** Steps 02 and 04 were already parallel at heart — literature had 5+ sequential WebSearch calls, fanout had 4 parallel Agent/Skill spawns. Workflows provide: deterministic parallel/pipeline patterns, structured output validation via schema, and cache for re-runs.

**How to apply:** When modifying the pipeline, prefer Workflow for any step that does parallel I/O (web searches, multi-model fanout). Keep user-gated steps (03 angle-gate, 06 draft) in the Skill orchestrator — workflows can't pause for user interaction.

## Step 02 — `manuscript-review-literature`

3-phase workflow: Extract → Search (parallel) → Merge → Verify.
- Phase 1: 1 agent reads paper → extracts refs + builds IEEE queries + identifies authors → schema-validated JSON
- Phase 2: `parallel([IEEE×3, authors×N])` agents run all WebSearch concurrently
- Phase 3: 1 agent deduplicates, ranks top N, writes literature.md
- Verify: checks file was actually written

Key fixes from adversarial review: `minLength: 1` on title/name, `?? 5` for n=0, empty-title filter, prompt injection guards, file-existence verification.

## Step 04 — `manuscript-review-fanout`

1-phase `parallel()` workflow:
- Sonnet reviewers: `agentType: reviewer-<angle>` with KNOWN_REVIEWERS whitelist; custom angles fall back to generic inline prompt
- Codex/DeepSeek reviewers: relay agent → `mcp__plugin_takeover_takeover__call_model` with inlined paper content, cap ~50K words
- All reviewers return `{angle, content}` via schema validation

Key fixes: agentType whitelist validation, MCP relay truncation strategy, prompt injection boundary markers, empty angles guard.

## Takeover MCP Dependency

Step 04's multi-provider fanout depends on the takeover plugin v2.0+ with MCP server registered. Without it, only direct Sonnet reviewers work. The takeover plugin at `cc-market/takeover/` was migrated to pure MCP in the same session.
