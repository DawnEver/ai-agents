# fork-context-flow — what the MAIN agent receives when you converse with a `/fork`

**Question.** After `/fork <directive>`, the user switches into the fork (agents view) and
chats with it directly. Does the **main** agent receive each user↔fork exchange —
every turn, only on completion, or never?

**Answer.** It is a **result-callback model, not a shared transcript.** The fork inherits
the parent conversation *at spawn* (by reference) and then runs forward-isolated. The only
thing that flows back to main is a `<task-notification>` carrying the fork's final
`<result>` — **one each time the fork stops.** Main never sees the user's message to the
fork, nor the fork's thinking / tool calls. So "does main get my conversation with the
fork each time?" → **main gets the fork's *result* each time it stops; it does not get the
conversation.**

Build: cc **2.1.205**, `CLAUDE_CODE_FORK_SUBAGENT=1`, model Haiku (client-side context
routing — model-agnostic). Case: `cases/fork-context-flow.case.mjs`.

## The fork lifecycle (from the persisted transcripts)

`/fork` is listed in-client as *"Spawn a background agent that inherits the full
conversation."* The fork is persisted as a **subagent of main**:

```
<configDir>/projects/<cwd>/<mainSessionId>.jsonl                       ← main
<configDir>/projects/<cwd>/<mainSessionId>/subagents/agent-<name>.jsonl ← the fork
```

The fork transcript opens with a `fork-context-ref` (pointer to the parent session) and a
`<fork-boilerplate>` first message that states the model contract verbatim:

> *You are a worker fork. The transcript above is the parent's history — inherited
> reference, not your situation. You are NOT a continuation…*

So the fork is framed as a **one-shot worker seeded with the parent history**, not a live
co-participant in the same conversation.

## What crosses back to main — and what doesn't

The experiment plants distinct tokens: `MAINOK-ALPHA` (main), the fork directive result
`FORKBORN`, and an interactive follow-up whose *user message* carries `GAMMA-OKAPI` while
the fork's *directed output* is `FORKRESULT-GAMMA`. Reading both persisted transcripts:

**Fork transcript (7 entries).** Inherited parent context (ref) → directive → `FORKBORN` →
then the user's follow-up, surfaced as:

> *The user sent a new message while you were working:* New codeword GAMMA-OKAPI. Reply
> with exactly: FORKRESULT-GAMMA — *…this is how Claude Code surfaces messages the user
> sends mid-turn, within the running turn…*

→ `FORKRESULT-GAMMA`.

**Main transcript.** Two — and only two — things about the fork appear, both
`<task-notification>` **user** events, one per fork stop:

| # | main entry | `<result>` | usage |
|---|------------|-----------|-------|
| 1 | after the directive completes | `FORKBORN` | `subagent_tokens=46512` |
| 2 | after the interactive reply completes | `FORKRESULT-GAMMA` | `subagent_tokens=46762` |

Each notification is exactly:

```xml
<task-notification>
  <task-id>asay-exactly-forkborn-<hash></task-id>
  <output-file>…/tasks/<task-id>.output</output-file>
  <status>completed</status>
  <summary>Agent "say exactly FORKBORN …" finished</summary>
  <note>A task-notification fires each time this agent stops with no live background
        children of its own. The user can send it another message and resume it, so the
        same task-id may notify more than once.</note>
  <result>FORKRESULT-GAMMA</result>
  <usage><subagent_tokens>46762</subagent_tokens><tool_uses>0</tool_uses>…</usage>
</task-notification>
```

The decisive negative: the `OKAPI` token — present only in the **user's message to the
fork** — appears **nowhere** in main's history. Main's second notification carries
`FORKRESULT-GAMMA` (the fork's `<result>`) but not the message the user typed to the fork.
Main auto-processes each notification into a short assistant turn
("Fork completed with result: FORKRESULT-GAMMA").

The client's own `<note>` is the spec: **a notification fires *each time the agent stops*,
and the same task-id can notify more than once** — confirmed here (two notifications, one
task-id).

## Consequences

- **Main is not kept in sync with the fork conversation.** Your messages to the fork and
  the fork's intermediate reasoning stay in the fork; only the fork's `<result>` on each
  stop is injected into main.
- **Inheritance is one-way and point-in-time**: fork gets the parent history *at spawn*;
  later main turns are not pushed to the fork, and the fork's chat is not pushed to main.
- Context accounting: the notification reports the fork's own `subagent_tokens` (~46k
  here) — the fork burns its own context window; main pays only for the small result
  notification.

## Harness notes (capability added for this experiment)

- **Driving the fork:** `/fork` must be submitted as one atomic write (the slash
  autocomplete otherwise eats the directive). Reach the fork's reply composer from the
  main prompt with **DOWN** (enter "manage") → **DOWN** (select the fork row) → **ENTER**
  (view → *"send the fork your next instruction"* composer). `SPACE`/`←`+`ENTER` paths
  are unreliable (`←`+`ENTER` = *return to main*, which silently routes follow-ups to main
  — the initial trap in this study).
- **tap DOES see the fork (correction).** An earlier draft claimed the resumed fork "runs
  detached and bypasses the claude-tap proxy, so its turns are absent from the trace DB."
  **That was wrong** — it was inferred from failed-navigation runs where the reply never
  reached the fork at all. On a clean run (tap session `a941d056…`), the resumed fork turn
  **is** captured: `turn#8` (fork) `msgs=5` carries `OKAPI` and emits `FORKRESULT-GAMMA`,
  under the **same** tap session and **same** `X-Claude-Code-Session-Id` (`64623545…`) as
  main. Forks/background agents are separate processes, but they inherit the proxy env
  (`ANTHROPIC_BASE_URL`), so claude-tap — an HTTP proxy, not a per-process attach — records
  them. The finding is thus confirmed by **both** layers independently: `turn#8` (fork)
  contains `OKAPI`; the next `turn#9` (main) does not.
- **When to reach for `driver/session.mjs`:** not because tap is blind, but for
  convenience — it reads the structured per-agent transcripts and parses the
  `<task-notification>` results (`findTranscripts` / `loadTranscript` /
  `taskNotifications`) without the tap main-turn heuristics, and it distinguishes
  main-vs-fork by file location rather than by scanning message content. Both layers agree.
  (Caveat not tested: a background agent that outlives the terminal — the agents view says
  they "keep running even if you close the terminal" — may lose the proxy once the parent
  exits; all turns here were captured while the parent session was alive.)
- **Oracle:** on-screen confirmation is unreliable (the alt-screen buffer echoes typed
  input, yielding false-positive `waitOutput` matches). The case verifies each TUI action
  by **polling the fork jsonl** until the expected token is actually persisted.
