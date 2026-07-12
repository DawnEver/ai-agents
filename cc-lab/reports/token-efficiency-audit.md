# Token Efficiency Audit — Full-Project Analysis

**Date:** 2026-07-12 | **Build:** cc 2.1.207 | **Trace:** cc-lab session `1a882919` (Haiku, 16k records)

## Per-Request Token Budget (from trace)

Every `/v1/messages` request from a session with all plugins active:

| Component | Chars | Est. Tokens | % of Total |
|-----------|-------|-------------|------------|
| System prompt (3 blocks) | 16,327 | 5,367 | 10.7% |
| Tools schema (35 tools) | 134,024 | 44,675 | **89.1%** |
| User messages | variable | — | — |
| **Total fixed overhead** | **150,351** | **~50,042** | 100% |

**The tools schema is the dominant cost at 89% of the fixed per-request payload.** Every
turn sends this entire schema. Cached after first request, but still paid on cache miss.

## System Prompt Breakdown (5,367 tok)

| Block | Content | Chars | Est. Tok | Source |
|-------|---------|-------|----------|--------|
| 0 | Billing header | 95 | 32 | Claude Code built-in |
| 1 | Identity ("You are Claude Code...") | 130 | 43 | Claude Code built-in |
| 2 | Instructions + rules | 16,102 | 5,367 | Mixed (see below) |

### Block 2 Composition (5,367 tok)

| Source | Chars | Est. Tok | % Block 2 |
|--------|-------|----------|-----------|
| CC built-in instructions (~16k chars - 12.4k rules) | ~3,724 | ~1,241 | 23% |
| `.claude/rules/rem/*.md` (9 files) | 9,132 | 3,045 | 57% |
| `.claude/rules/MEMORY.md` | 3,246 | 1,082 | 20% |

**The 9 injected rules files consume ~58% of the instruction block.** The largest
contributors:

| Rule | Chars | Tok | Topic |
|------|-------|-----|-------|
| MEMORY.md | 3,246 | 1,082 | Memory index (grows over time) |
| no-terminal-flash.md | 2,137 | 534 | Windows spawn detail |
| providers.md | 1,963 | 491 | Provider config |
| migration.md | 1,372 | 343 | Migration tooling |
| hook.md | 1,244 | 311 | Hook behavior |

## Tools Schema Breakdown (44,675 tok)

The 35 tools come from: CC built-in (25), fabric MCP (8), rem MCP (2), traceme MCP (0 —
SQLite), evolve (0 — no MCP), sharp-review (0 — hook-only).

### Fabric MCP Tools (8 tools, ~3,910 tok = 8.8%)

| Tool | Schema chars | Est. Tok | Waste flag |
|------|-------------|----------|------------|
| `call` | ~2,200 | 733 | Long mode descriptions, 14 properties |
| `fan_out` | ~2,100 | 700 | Nested tasks schema, verbose description |
| `spawn_session` | ~650 | 217 | — |
| `session_send` | ~550 | 183 | — |
| `team_spawn` | ~900 | 300 | Nested workers schema |
| `team_send` | ~400 | 133 | — |
| `team_status` | ~300 | 100 | — |
| `team_synthesize` | ~300 | 100 | — |
| `team_close` | ~250 | 83 | — |
| `list_providers` | ~300 | 100 | — |
| `resolve_model` | ~350 | 117 | — |
| `codex_status` | ~250 | 83 | — |
| `list_sessions` | ~180 | 60 | — |

### Other Plugin Tools

| Plugin | Tools | Est. Tok | Notes |
|--------|-------|----------|-------|
| rem | task_create, task_update, etc. | ~2,500 | Task engine |
| sharp-review | (hook-only) | 0 | No MCP server |
| evolve | (workflow-only) | 0 | No MCP server |
| traceme | (SQLite) | 0 | No MCP server |
| watch | (Python) | 0 | No MCP server |

## cc-market Rules (NOT injected every session — progressive disclosure)

The 45,789 chars (~11,447 tok) of plugin-level invariants are NOT loaded every session.
They are loaded only when working inside a specific plugin directory. This is correct
behavior per the progressive disclosure design.

However, `cc-market/.claude/rules/invariants.md` (5,436 chars) and `cc-market/.claude/rules/MEMORY.md`
(4,277 chars) ARE injected when working in cc-market/. This adds ~2,428 tok to the system
prompt when working on plugins.

## Optimization Recommendations (ranked by impact)

### HIGH: Trim Fabric Tool Schemas (~2,000 tok saved)

The `fan_out` and `team_*` schemas have verbose descriptions. For example, `fan_out`'s
description is 450+ chars describing use cases. The JSON schema duplicates this in
`inputSchema.properties.tasks.description`. The LLM doesn't need a tutorial — just the
parameter names and types.

**What to trim:**
- `fan_out`: Cut description from 450 chars to 100 ("Run N tasks concurrently, return
  compact JSON"). The `tasks` array item descriptions are 100+ chars each → 20 chars.
- `call`: 14 properties with 80+ char descriptions → 30 char each.
- `team_spawn`: Nested workers schema descriptions → compact form.
- All tool descriptions: remove "For persistent multi-turn instead, use spawn_session"
  cross-references — the LLM will discover tools via tools/list.

**Estimated saving: ~2,000 tok (~4.5% of tools schema)**

### HIGH: Collapse Injected Rules (~1,500 tok saved)

The 9 `.claude/rules/rem/*.md` files consume ~3,045 tok. Several are internal dev notes
that an LLM doesn't need every session:

| Rule | Action | Saving |
|------|--------|--------|
| no-terminal-flash.md (534 tok) | Move to `invariants.md` in plugin dir (progressive disclosure) | 534 tok |
| providers.md (491 tok) | Already in AGENTS.md; remove duplicate | 491 tok |
| migration.md (343 tok) | Dev-only; move to cc-market/rem/ | 343 tok |
| hook.md (311 tok) | Dev-only; move to cc-market/rem/ | 311 tok |

**Estimated saving: ~1,679 tok (~31% of injected rules)**

### MEDIUM: MEMORY.md Index Compression (~500 tok saved)

MEMORY.md lists every memory entry with dates, paths, and created/accessed timestamps. At
11 entries and growing, this index gets proportionally larger. Options:
- Compress format: `[YYYY-MM-DD title](path)` instead of full markdown links with metadata
- Move volatile metadata (accessed timestamps) to `_meta.json` (already done)
- Remove entries older than 30 days from the index

**Estimated saving: ~500 tok (current size 1,082 → ~580)**

### MEDIUM: Tool Description Conventions (~1,000 tok across all tools)

All MCP tools across plugins follow verbose description patterns. A convention change:
- Description: one line (what it does)
- Detailed usage: in README/help, not in schema
- Cross-references: remove ("use X instead", "for Y see Z") — LLM discovers tools

### LOW: AGENTS.md Chain Compression

The AGENTS.md → CLAUDE.md → @AGENTS.md chain is ~8,000 chars total. Most of it is
architecture documentation useful for development but excessive for every session. However,
this is project-specific context that the LLM genuinely needs to understand the repo.

## Summary

| Optimization | Tokens Saved | % of Fixed Overhead | Effort |
|-------------|-------------|---------------------|--------|
| Trim fabric tool schemas | ~2,000 | 4.0% | 1 hour |
| Collapse injected rules | ~1,679 | 3.4% | 30 min |
| MEMORY.md compression | ~500 | 1.0% | 15 min |
| All-tool description trim | ~1,000 | 2.0% | 2 hours |
| **Total potential** | **~5,179** | **10.4%** | — |

At Fable 5 pricing ($10/MTok input), each cache-miss turn costs $0.50 for the 50k overhead.
Saving 5k tok saves $0.05/turn. For a session with 20 turns (10 cache misses), that's
$0.50 saved per session.

The dominant cost (89%) is tools — but tools ARE necessary. The rules (11%) can be trimmed
most easily. The biggest single win is collapsing the 9 injected rules files.

## Files

- `reports/token-efficiency-audit.md` — This report
- `.scratch/fabric-vs-fork-cost-model.mjs` — Fabric vs fork cost model
- `reports/fabric-vs-fork.md` — Fabric vs fork comparison
- `reports/prompt-anatomy.md` — System prompt block anatomy (prior work)
