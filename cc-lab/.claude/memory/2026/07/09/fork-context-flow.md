---
name: fork-context-flow
description: /fork is a result-callback worker — main gets a <task-notification> with the fork's <result> on each stop, never the user<->fork conversation
created: 2026-07-09
tags: [fork, subagent, agents-view, task-notification, session-jsonl, cc-2.1.205, driver]
---

# /fork → main: result-callback, not shared transcript

New case `cases/fork-context-flow.case.mjs` + report `reports/fork-context-flow.md` +
harness helper `driver/session.mjs`. cc 2.1.205, `CLAUDE_CODE_FORK_SUBAGENT=1`, Haiku
(client-side routing — model-agnostic).

## Finding (answers "does main receive my chat with the fork each time?")

**No shared transcript.** `/fork <directive>` spawns a **worker subagent** that inherits
the parent history *at spawn* (by reference: `fork-context-ref` + `<fork-boilerplate>` "the
transcript above is the parent's history … you are NOT a continuation"), then runs
forward-isolated. What flows back to MAIN is **only** a `<task-notification>` carrying the
fork's final `<result>` — **one each time the fork stops** (`<note>`: "fires each time this
agent stops … the same task-id may notify more than once"). Verified: two notifications
(`FORKBORN`, then `FORKRESULT-GAMMA`) for one task-id. The user's message to the fork
(token `OKAPI`) and the fork's thinking/tools appear **nowhere** in main's history. Main
auto-processes each notification into a one-line assistant turn. Fork burns its own
~46k-token context; main pays only for the small notification.

## Harness gotchas (cc 2.1.205 agents view)

- **`/fork` must be one atomic write** — the slash autocomplete otherwise eats the
  directive (submits `/fork` alone → "Usage: /fork <directive>").
- **Reach the fork composer:** from main prompt **DOWN** (manage) → **DOWN** (select fork
  row) → **ENTER** (view → "send the fork your next instruction" composer). NOT SPACE.
  `←`+**ENTER** = *return to main* — the trap: follow-ups silently route to main, which
  answers them itself (looks like the fork replied).
- **tap DOES see forks (corrected — earlier draft was wrong).** A fork is a separate child
  process (12 orphan `claude.exe` after runs) but inherits the proxy env, so its turns —
  initial AND resumed — land in the SAME tap session under the SAME session-id as main
  (clean run `a941d056`: `turn#8` fork carries `OKAPI`→`FORKRESULT-GAMMA`, `turn#9` main
  has no `OKAPI`). The "resumed fork bypasses tap" claim was inferred from failed-nav runs
  where the reply never reached the fork — a confound. Finding confirmed by BOTH tap and
  jsonl. `driver/session.mjs` is a convenience (structured per-agent transcripts +
  `taskNotifications` parsing), not a necessity.
- **Oracle = poll the fork jsonl**, not the screen: the alt-screen buffer echoes typed
  input, so `waitOutput` on your own text is a false positive. Case retries every TUI
  action until the token is actually persisted.

## Layout

`<configDir>/projects/<cwd>/<mainId>.jsonl` (main) and
`…/<mainId>/subagents/agent-<name>-<hash>.jsonl` (fork) — the fork is literally a subagent
child of the main session dir.
