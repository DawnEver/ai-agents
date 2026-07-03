# env-var-matrix (PLAN M3.3) — which layer does each env var act on?

Runs one trivial turn ("say PINEAPPLE") under several env vars in **fresh, isolated**
launches and classifies each var by the layer where its effect is observable:
**API-request** (in the request body) / **state-persistence** (files on disk) /
**UI-render** (tty escapes) / **no-op** (no observable effect in this build).

`cases/env-var-matrix.case.mjs`, run `2026-07-03T…-envmatrix-*`.

## Evidence

| config | env var | main `max_tokens` | session transcripts on disk | tty alt-screen | verdict |
|--------|---------|-------------------|------------------------------|----------------|---------|
| baseline | — | 32000 | 1 | none | reference |
| max-output-256 | `CLAUDE_CODE_MAX_OUTPUT_TOKENS=256` | **256** | 1 | none | **API-request** |
| no-persistence | (unset `…FORCE_SESSION_PERSISTENCE`) | 32000 | **0** | none | **state-persistence** |
| disable-nonessential | `DISABLE_NON_ESSENTIAL_MODEL_CALLS=1` | 32000 | 1 | none | **no-op** |
| no-alt-screen | `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1` | 32000 | 1 | none | **no-op** |

All configs emitted the same 27 records incl. the same auxiliary calls (1 title-gen,
1 `max_tokens:1` quota probe, etc.).

## Classification

- **`CLAUDE_CODE_MAX_OUTPUT_TOKENS` → API-request layer.** It sets the main turn's
  `max_tokens` directly in the request body (32000 → 256). Nothing else changes; it is a
  pure request-shaping var. This is the cleanest positive in the matrix — the value is
  visible in the trace, so it is authoritative.
- **`CLAUDE_CODE_FORCE_SESSION_PERSISTENCE` → state-persistence layer.** It does **not**
  appear in any API request. Its only effect is on disk: with it set, the run writes a
  session `.jsonl` transcript under `config/projects/…`; without it, a session launched
  from a parent Claude Code (`CLAUDE_CODE_CHILD_SESSION=1`) writes **zero** transcripts
  and is excluded from resume/history. Confirms the AGENT.md pitfall empirically.

## No-ops (this build, cc 2.1.199, under the PTY harness)

- **`DISABLE_NON_ESSENTIAL_MODEL_CALLS`** had no effect: the title-generation call and
  the `max_tokens:1` quota probe still fire (record counts identical to baseline). The
  var is likely renamed or removed — treat its documented behavior as stale here.
- **`CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN`** produced no tty-structure difference. Claude
  Code does not use the classic `ESC[?1049h` alternate-screen buffer in this build — it
  renders full-screen via clear (`ESC[2J`) + cursor positioning — and the private-mode
  escape sequences (`?9001h ?1004h ?2026 …`) are byte-identical with and without the var.
  So the "changes rendering" caveat in AGENT.md does not manifest as an alt-screen toggle
  here; if it matters, detect it by a different signal than `?1049`.

## Layer taxonomy (populated by what was verified)

| layer | how to detect | verified example |
|-------|---------------|------------------|
| API-request | field differs in the trace request body | `CLAUDE_CODE_MAX_OUTPUT_TOKENS` (`max_tokens`) |
| state-persistence | files appear/absent under `config/` | `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE` (session `.jsonl`) |
| UI-render | tty escape/structure differs | *(none — the alt-screen var is a no-op here)* |
| tool-env | only visible when a tool runs (e.g. `BASH_DEFAULT_TIMEOUT_MS`) | *(not exercised — trivial turn runs no tools)* |
| no-op / stale | no observable effect in any layer | `DISABLE_NON_ESSENTIAL_MODEL_CALLS`, `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN` |

## Notes

- The authoritative layer for any var is the one where it shows up: check the trace body
  first (API-request), then `config/` (state), then tty (UI). A var absent from all three
  is either tool-env (needs a tool call to surface) or a no-op/stale name.
- tool-env vars need a case that actually invokes a tool; that requires either an
  approved tool or dropping the permission sandbox (not done unprompted), so it is left
  as a follow-up.
