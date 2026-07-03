# btw-isolation — is `/btw` an isolated side-thread?

**Answer: isolation is forward-only, and `/btw` is _not_ tool-free.** A `/btw` question
fired during an in-flight main turn produces a **separate** API request that (a) does
**not** leak into later main-thread requests, but (b) **carries the full tools array and
the entire main-thread history**, plus a special `<system-reminder>` that constrains it
to a quick, no-action answer. This partially refutes the PLAN hypothesis ("carries no
`tools`").

## Method

`cases/btw-isolation.case.mjs`: launch → submit a long text turn (250-word essay,
marker **ZEBRAMAIN**) with no tools so it streams for several seconds → while it is
in-flight, fire `/btw what is the capital of France? … QUOKKABTW` → let both settle →
(best-effort) a follow-up main turn. Assertions read the trace DB via `driver/tap.mjs`.
Reproduced across two runs (`83e73c8f…`, `dae4d154…`).

## Evidence (main-thread + side requests, tools > 0)

| turn | role in session | msgs | ZEBRAMAIN | QUOKKABTW | /btw system-reminder |
|------|-----------------|------|-----------|-----------|----------------------|
| 3 | main turn (essay) | 1 | ✓ | — | no |
| 4 | **/btw side request** | 1 | ✓ | ✓ | **yes** |
| 6 | later main thread | 3 | ✓ | **—** | no |

The `/btw` request (turn 4) is unambiguously identifiable by an appended reminder:

> `<system-reminder>` … Simply answer the question with the information you have.
> If you don't know the answer, say so — do not offer to look it up or investigate.

## What is (and isn't) isolated

- **Separate request:** yes — `/btw` is its own `/v1/messages` call, distinct from the
  main turn it overlapped.
- **Forward isolation:** yes — the trailing main-thread request (turn 6) contains the
  main history (ZEBRAMAIN essay) but **not** the `/btw` Q&A (QUOKKABTW). The side
  question never enters the main conversation going forward.
- **Backward isolation:** **no** — the `/btw` request *includes* the full prior
  main-thread history as read context (ZEBRAMAIN present in turn 4).
- **Tools:** **not stripped** — turn 4 carries the same 35-tool array and the same
  3-block system prompt as the main turn. `/btw` is steered to answer directly by the
  extra system-reminder, **not** by removing its tools. (PLAN hypothesis refuted.)
- Same `X-Claude-Code-Session-Id` across main and `/btw` requests — it is one session,
  not a nested/child session.

## Notes / pitfalls discovered

- **`/btw` needs an in-flight turn.** On a fast model the main turn finishes before the
  `/btw` is typed, and the text merges into the next normal turn — no side-thread. Force
  a genuinely long main turn (long text generation; a `sleep` tool call would need
  dropping the permission sandbox, which we do not do unprompted).
- **Robust submission matters.** A bare `send()` races its `\r` against long/pasted
  input and can leave text unsubmitted, gluing a following `/btw` into the same user
  message (observed: a literal `\r/btw…` inside one turn). Type → confirm the text
  landed → send Enter as a separate keystroke. Right after a turn settles the input can
  briefly drop keystrokes, so the type helper retries once.
