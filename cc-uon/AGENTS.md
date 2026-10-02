# cc-uon

## Purpose

Browser-driven admin chores for the University of Nottingham, done on the user's behalf:

| Command | Task | Canonical procedure |
| --- | --- | --- |
| `/expense` | Fill an expense claim in Oracle from receipts | `.claude/commands/expense.md` |
| `/supervision` | Finalise pending PGR supervision-record forms as supervisor | `.claude/commands/supervision.md` |

In Codex use `$expense` / `$supervision`. This file is the single source of truth for layout,
authorization, and shared portal pitfalls; the command files hold only their task's sequence.

## Authorization

The user has authorized submitting in both workflows (expense claim Submit, supervision Submit
form). Still stop and report — never guess — when a required field needs information the user
or student has not provided.

## Personal values

`profile.md` (gitignored; template `profile.example.md`) holds the user's cost codes and fixed
choices. Read it before filling any expense form. It is the only place these values live —
do not copy them into command files or memory.

## Layout

```
profile.md                      — personal fixed values (local only)
ongoing/<YYYY-MM-DD>-<slug>/    — in-progress claim (local only)
  receipts/                     — receipt PDFs/images as given by the user
  lines.md                      — one row per expense line (see expense.md)
archived/<YYYY>/<claim-no>/     — finished claims, moved from ongoing/ after submission
```

`ongoing/` and `archived/` are gitignored and provisioned by `../scripts/link-agent-data.sh`.

## Browser pitfalls (UoN Oracle and Campus Solutions pages)

- `read_page` / `find` error on these sites; work from screenshots and JS.
- Fields shift after every server round-trip; re-screenshot before every click — old
  coordinates are stale.
- Typing into a pre-filled field appends rather than replaces. Set values via JS, then dispatch
  `input` and `change` events.
- Never use the browser Back button or the portal's Home link mid-form; both discard input.
