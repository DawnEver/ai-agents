# cc-uon

## Purpose

Browser-driven admin chores for the University of Nottingham, done on the user's behalf:

| Command | Task | Canonical procedure |
| --- | --- | --- |
| `/expense` | Fill a staff expense claim in Oracle from receipts | `.claude/commands/expense.md` |
| `/hub-expense` | Fill a PGR exceptional expense claim on NottinghamHub | `.claude/commands/hub-expense.md` |
| `/supervision` | Finalise pending PGR supervision-record forms as supervisor | `.claude/commands/supervision.md` |

In Codex use `$expense` / `$hub-expense` / `$supervision`. This file is the single source of truth
for layout, authorization, and shared portal pitfalls; the command files hold only their task's
sequence.

## Authorization

The user has authorized submitting in the Oracle expense and supervision workflows. On the
NottinghamHub claim the user ticks the certification and clicks Submit themselves; the agent
fills, saves, and verifies. Always stop and report — never guess — when a required field needs
information the user or student has not provided.

## Personal values

`profile.md` (gitignored, synced through the agent-data link; template `profile.example.md`)
records the user's cost codes and fixed choices. It is the only place these values live — do
not copy them into command files or memory. A recorded code is history, not a default: confirm
it with the user before using it on a new claim.

## Layout

```
profile.md                      — recorded codes and rules (synced, local only)
ongoing/<YYYY-MM-DD>-<slug>/    — in-progress claim (synced, local only)
  receipts/                     — receipts and pre-approval PDF
  lines.md                      — one row per expense line
archived/<YYYY>/<claim-no>/     — finished claims, moved from ongoing/ after submission
```

`profile.md`, `ongoing/` and `archived/` are gitignored links into the synced agent-data root,
provisioned by `../scripts/link-agent-data.sh`.

## Browser pitfalls (UoN Oracle and Campus Solutions pages)

- `read_page` / `find` error or miss elements on these sites; work from screenshots and JS.
- Fields shift after every server round-trip; re-screenshot before every click — old
  coordinates are stale.
- Typing into a pre-filled field appends rather than replaces. Set values via JS, then dispatch
  `input` and `change` events. A JS change can re-render the row and clear a sibling field;
  read the values back after each one.
- Campus Solutions numeric fields that drive a computed total (e.g. Exchange rate) ignore a JS
  value: clear the field via JS, focus it, then type the value and press Tab.
- Campus Solutions file attachments open in a nested modal iframe (`ptModFrame_0`) that
  `file_upload` cannot reach: create and type the attachment rows, Save, and hand the uploads
  to the user with a row-to-file table. Uploads persist only after Save or Submit.
- Do not reload or navigate the user's tab while they are working in a form; a reload discards
  their unsaved uploads. Verify after they report Save or Submit.
- Never use the browser Back button or the portal's Home link mid-form; both discard input.
