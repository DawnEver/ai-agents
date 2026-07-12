# cc-market Token Consumption Audit

**Date:** 2026-07-12
**Tap session:** `38dea5ec-8496-4573-b719-4f78cbe81a09`
**Model:** claude-haiku-4-5-20251001

## Baseline: Per-Request Fixed Overhead

| Component | Chars | Est. Tokens | % |
|---|---|---|---|
| System prompt (CC built-in) | 15,969 | 5,323 | 10.5% |
| Built-in tools (31 tools) | 127,448 | 42,483 | 83.4% |
| REM tools (TaskCreate/Update/List/Get) | 9,364 | 3,121 | 6.1% |
| **Total** | **152,781** | **50,927** | 100% |

Fabric MCP tools were NOT captured in this run (config bootstrap issue). Estimated from source: **7,463 chars / 2,488 tok** additional if fabric MCP active.

## cc-market Contribution Breakdown

### 1. MCP Tool Schemas (per-request)

**Fabric MCP TOOLS** (14 tools, `fabric/scripts/mcp-server.mjs:60-274`):

| Tool | Chars | Tok | Params | Notes |
|---|---|---|---|---|
| `call` | 2,205 | 735 | 14 | Big description + many params |
| `fan_out` | 919 | 306 | 2 | tasks[] array schema |
| `team_spawn` | 787 | 262 | 1 | workers[] array schema |
| `spawn_session` | 631 | 210 | 5 | |
| `session_send` | 503 | 168 | 3 | |
| `resolve_model` | 408 | 136 | 2 | |
| `team_send` | 381 | 127 | 3 | |
| `session_close` | 270 | 90 | 1 | |
| `codex_status` | 261 | 87 | 1 | |
| `team_status` | 239 | 80 | 1 | |
| `team_synthesize` | 236 | 79 | 1 | |
| `team_close` | 223 | 74 | 1 | |
| `list_providers` | 220 | 73 | 0 | |
| `list_sessions` | 180 | 60 | 0 | |
| **Total** | **7,463** | **2,488** | | |

**REM tools** (4 built-in tools, owned by rem plugin): 9,364 chars / 3,121 tok

### 2. SKILL.md Files (injected as skill descriptions)

| Skill | Size | Est. Tok |
|---|---|---|
| `evolve` | 7,604 | 2,535 |
| `sharp-review` | 7,133 | 2,378 |
| `rem:refresh-docs` | 6,070 | 2,023 |
| `watch` | 5,830 | 1,943 |
| `rem` | 4,354 | 1,451 |
| `traceme:insights` | 3,751 | 1,250 |
| `rem:todo` | 3,728 | 1,243 |
| `traceme` | 2,535 | 845 |
| `rem:investigate` | 1,808 | 603 |
| `fabric:takeover-result` | 891 | 297 |
| `fabric:codex-image-result` | 628 | 209 |
| **Total** | **44,332** | **14,777** |

### 3. AGENTS.md Files (agent definitions + project context)

| File | Size | Est. Tok |
|---|---|---|
| `sharp-review/AGENTS.md` | 8,167 | 2,722 |
| `fabric/AGENTS.md` | 7,134 | 2,378 |
| `AGENTS.md` (root) | 6,774 | 2,258 |
| `rem/AGENTS.md` | 5,120 | 1,707 |
| `traceme/AGENTS.md` | 4,969 | 1,656 |
| `watch/AGENTS.md` | 3,941 | 1,314 |
| `evolve/AGENTS.md` | 3,864 | 1,288 |
| **Total** | **39,969** | **13,323** |

### 4. Fabric Prompts (sent as system prompt on every fabric call)

| File | Size | Sent when |
|---|---|---|
| `review.md` | 1,206 | mode=review |
| `task.md` | 676 | mode=task |

### 5. Reference Docs (on-demand, not in system prompt)

Total: 75,489 chars across 26 files. Loaded only when skill reads them — no per-request cost.

## Results: Applied Optimizations

### Fabric MCP TOOLS (`fabric/scripts/mcp-server.mjs`)

**Before:** 7,463 chars / 2,488 tok → **After:** 5,383 chars / 1,794 tok
**Saved: 2,080 chars / 694 tok per request (28% reduction)**

- Shortened all 14 tool descriptions to 1 sentence max
- Trimmed parameter descriptions: removed redundant qualifiers, parentheticals, examples
- Dropped `passthroughAuth` and `runDir` params from `call` (auto-detected/rarely used)
- Flattened verbose multi-sentence descriptions to terse one-liners

All 25 MCP server tests pass. Full fabric suite: 183 pass, 0 fail.

### Fabric Prompts

| File | Before | After | Saved |
|---|---|---|---|
| `prompts/review.md` | 1,206 chars | 366 chars | 840 chars / 280 tok |
| `prompts/task.md` | 676 chars | 252 chars | 424 chars / 141 tok |
| **Total** | **1,882 chars** | **618 chars** | **1,264 chars / 421 tok** |

### SKILL.md Descriptions

| Skill | Before | After |
|---|---|---|
| `evolve` | 190 chars | 93 chars |
| `watch` | 230+ chars | 85 chars |
| `rem:todo` | 200+ chars | 112 chars |
| `rem:investigate` | 4-line folded scalar | 1 line |
| `rem:refresh-docs` | 7-line folded scalar | 1 line |

### Total Savings

| Layer | Per-Request | Per-Session |
|---|---|---|
| Fabric TOOLS schema | **694 tok** | — |
| Fabric prompts (review/task mode) | **421 tok** | — |
| SKILL.md descriptions | — | ~300 tok |
| **Total** | **~1,115 tok** | **~300 tok** |

For a typical 20-turn session: **~22,600 tok saved** (mostly cache-eligible system prompt content).

## Unchanged / Intentionally Kept

- **REM tools** (TaskCreate/Update/List/Get): CC built-in tools, cannot edit from cc-market
- **Built-in tools** (Workflow 21k, Bash 11.7k, etc.): CC core, outside cc-market scope
- **AGENTS.md files**: dev-only context, not injected at runtime (per `.claude/rules/invariants.md`)
- **Reference docs**: already progressive disclosure, loaded on-demand only
- **Agent definitions** (`fabric/agents/takeover.md`, `sharp-review/agents/sharp-review.md`): loaded only when agent spawns, not per-request
