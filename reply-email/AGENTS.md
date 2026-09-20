# Reply-Email Agent

## Purpose

This project is a dedicated email-reply assistant. Its sole job is to draft, review, and
archive email replies on behalf of the user.

Invoke the workflow as `/reply-email` in Claude Code or `$reply-email` in Codex; a natural-language
request is also valid. Both hosts follow the canonical `.claude/commands/reply-email.md` workflow.

This file (`AGENTS.md`) is the **single source of truth** for directory layout, naming
conventions, the meta.md schema, glob patterns, diff-learning rules, and desensitization.
The slash-command files under `.claude/commands/` are procedural glue only — they reference
this file and must never restate the conventions defined here.

---

## Workflow

### Replying to an email

1. The user provides the incoming email (paste or describe) and their reply requirements or
   draft (any language). Check for thread continuation (a referenced archive, or "接着之前的继续").
2. Derive a kebab-case topic slug from the subject. For continuations, reuse the existing slug
   (see **Naming conventions**).
3. Read `style/profile.md` for the user's configured style (see **Style**). If it doesn't
   exist, infer patterns from up to 5 recent archived replies. Fall back to generic guidelines
   only when neither exists.
4. For continuations, load thread history (see **Thread reconstruction**) so the draft is aware
   of everything said before — don't re-ask answered questions.
5. Create `ongoing/<topic>/` and write `original.txt` + `draft.md`. Then copy `draft.md` to
   `final.md` with a shell command (`cp`), never by regenerating the content. If the directory
   already exists, resume from the existing files (jump to step 6 — the user is editing).
   **Never archive until the user explicitly says "归档" (or "archive").** Creating the ongoing
   directory and presenting the draft is the end of this step — wait.
6. Tell the user the draft is ready. The user edits `final.md` directly. Never touch `draft.md`
   after creation. Optional polish: only if the user explicitly asks, edit `final.md`.
   - 6a. Build the importable files (see **Mail and calendar generation**) so the round can be
     opened in a mail client instead of hand-pasted. Regenerate after every edit to `final.md`.
     This is a convenience, not an approval — the archive gate below is unchanged.
7. After approval (user says "归档" or "archive"), archive the round:
   - 7a. Move `ongoing/<topic>/` → `archived/<YYYY>/<MM>/<DD>/<topic>/` (apply the `-r<N>`
     suffix rule from **Naming conventions** if the same slug already archived today).
   - 7b. Diff `draft.md` vs `final.md` (before renaming) to identify what the user changed
     (see **Diff learning**).
   - 7c. Update style: promote patterns seen in ≥2 archives to `style/profile.md`; record
     per-reply observations in `meta.md` under `## Diff notes`.
   - 7d. Rename `final.md` → `reply.md` and write `meta.md` (see **meta.md schema**).
   - 7e. For continuations, set `prev:` in `meta.md` to the repo-root-relative path of the
     immediately preceding round's folder (cosmetic; slug-based lookup is authoritative).

---

## Reference

### Directory structure

```
style/
  profile.md               — accumulated style data (signature, greeting, tone)

ongoing/<topic>/           — in-progress (local only, gitignored)
  original.txt             — raw incoming email (this round only)
  draft.md                 — AI's initial draft
  final.md                 — user-edited version (starts identical to draft.md)
  <topic>.eml, <topic>.ics — generated importables, named after the round directory
                             (see Mail and calendar generation)

archived/<YYYY>/<MM>/<DD>/<topic>/  — one folder per exchange round (local only, gitignored)
  original.txt             — raw incoming email for this round only
  draft.md                 — AI's initial draft (preserved for diff learning)
  reply.md                 — sent reply (user's final.md, renamed after diff)
  meta.md                  — metadata + diff observations
  <topic>.eml, <topic>.ics — the generated importables, moved here with the round
  (attachments)            — any material that came with the email (image/*.png, *.csv, …);
                             filenames are unconstrained, not part of the spec
```

- `draft.md` = AI's raw output, preserved untouched for diff learning. `final.md` = user's version.
- `original.txt` = raw email (plain text). `.md` files = structured reply content.

### Naming conventions

- `<topic>` is a short kebab-case slug derived from the email subject (e.g. `project-proposal`,
  `invoice-q2`). The slug binds a whole thread together — reuse it across every round.
- **Same slug, different dates:** each round lives under its own dated path, plain slug
  (`archived/2026/06/22/<topic>/`, `archived/2026/06/23/<topic>/`).
- **Same slug, same date (≥2 rounds in one day):** suffix the directory with `-r<N>`, N starting
  at 2 (`<topic>/`, `<topic>-r2/`, `<topic>-r3/` …). The first round of the day has no suffix.

### Legacy archive quirks

Archives from early June 2026 predate the current conventions. Known deviations, kept as-is
(no backfill):

- `original.md` instead of `original.txt` (all archives before 2026-06-16).
- No `draft.md` — so no diff notes exist for those rounds.
- `position: N/M` frontmatter field instead of `round: N` (earliest metas).
- `archived/2026/06/05/torque-correlation-check-v2/` uses a `-v2` suffix that the canonical
  thread glob below does **not** match; treat that round as orphaned unless looked up directly.
- `prev:` paths written in various formats (see schema note below).

### Thread reconstruction & globs

Thread linkage is by slug, not by `prev:`. To find every round of a thread, match all layouts
with one canonical glob set (legacy flat layout used `YYYY-MM-DD` single dirs):

```bash
# directories for a thread (nested + flat, incl. -rN suffix rounds)
ls -d archived/*/*/*/<topic> archived/*/*/*/<topic>-r* archived/*/<topic> archived/*/<topic>-r* 2>/dev/null
```

Read every `original.txt` and `reply.md` in date order to reconstruct the conversation. The new
reply is round N+1.

> Scalability note: reconstruction globs the whole archive tree each continuation. Fine at the
> current corpus size; if archives grow large, make the `prev:` chain authoritative instead.

### meta.md schema

```markdown
---
subject: <email subject>
sender: <sender name / address>   # for a user follow-up with no new incoming email: "[User follow-up — no new incoming email]"
recipient: <recipient>      # optional — only for outgoing-initiated mail
date: <original email date, normalized to YYYY-MM-DD>
thread: <topic-slug>
round: <N>                  # 1-indexed position in the thread
prev: <path to preceding round's folder>   # omit for round 1
---

<1-2 sentence summary of this message in the thread>

## Diff notes

<what the user changed from draft.md to final.md: tone, phrasing, structure, additions, removals>
```

- `prev:` is always a repo-root-relative path: `archived/YYYY/MM/DD/<topic>` (trailing slash
  optional). Never `../..`-style relative — older archives mix formats; write the canonical one.
- The summary may optionally sit under a `## Summary` heading; bare text is the default.

### Diff learning

When archiving, diff `draft.md` against `final.md` — the primary feedback loop for better drafts.

```bash
diff -u draft.md final.md
```

Look for: tone shifts (more/less formal/direct), phrasing replacements, structural edits
(reordered/merged/split sections), additions the AI missed, removals (filler, redundancy),
signature/closing/subject changes.

Apply: record observations in `meta.md` under `## Diff notes`. If a pattern appears across ≥2
archived replies, promote it to `style/profile.md`. One-off edits stay in `meta.md` only — don't
overfit to a single email.

### Style

The authoritative style source is `style/profile.md` (signature, greeting, closing, tone). These
generic defaults apply only when it's absent:

- Match the formality level of the incoming email.
- Default to the language of the original email.
- Keep replies focused; avoid filler ("I hope this email finds you well").

### Desensitization

All committed files (`AGENTS.md`, `CLAUDE.md`, `.claude/commands/*.md`, memory) are public-facing.
They must never contain:

- Real names, email addresses, or sender/recipient identities
- Reference numbers (application IDs, invoice numbers, ticket IDs)
- Specific institutional details identifying the user's university, department, or colleagues
- Verbatim content from actual correspondence

Use generic placeholders: `conference-invitation`, `prof.smith@example.com`, `[Your Name]`,
`project-proposal`. Real data lives exclusively in gitignored paths — `ongoing/`, `archived/`,
`style/profile.md`.

### Mail and calendar generation

`scripts/build_mail.py` turns a finished `final.md` into an `.eml` and an `.ics` next to it, so
the round can be double-clicked into a mail client rather than pasted by hand. Zero
dependencies (Python stdlib only), so it runs on any machine with `python3`.

```bash
python scripts/build_mail.py ongoing/<topic>/final.md
```

Addressing and event details live in a **flat frontmatter block** at the top of `final.md` —
`key: value` lines split on the first colon only, so `subject: Re: something` needs no quoting
and no YAML parser. Everything below the closing `---` is the email body.

```
---
to: alice@example.com, "Smith, Bob" <bob@example.com>
cc:
subject: Re: Project meeting
attach: booking-confirmation.pdf, image-1.png
event.title: Project meeting
event.start: 2026-03-04 09:00
event.end: 2026-03-04 10:00
event.timezone: Europe/Berlin
event.location: Meeting room 2
---
```

- **Address keys** — `to`, `cc`, `bcc`, `from`, `reply-to`. `to:`, or `event.title` +
  `event.start`, is what makes the corresponding file get written; with neither, the command
  has nothing to build.
- **`attach`** — paths relative to the draft, comma-separated.
- **Images** — `![alt](image-1.png)` anywhere in the body becomes an inline image, not an
  attachment. Unreferenced files in the folder are ignored.
- **`event.*`** — `title`, `start`, `end`, `timezone`, `utc`, `location`, `description`,
  `attendees`, `organizer`, `method`, `uid`. `start` alone is an all-day event; add a time and
  a `timezone` for a timed one. An all-day `end` is **exclusive** per RFC 5545, so a
  two-day event on the 4th–5th is written `start: 2026-03-04` / `end: 2026-03-06`. The
  builder warns whenever `end` is given, restating the last day actually included.
- **Calendar semantics** — the default is a bare `VEVENT`: a personal appointment that
  notifies nobody. `event.method: request` (with `event.organizer`) upgrades it to a real
  meeting request.

Behaviour worth knowing, because each is deliberate:

- The `.eml` carries `X-Unsent: 1`, which is what makes Outlook open it as an **editable draft
  with a Send button** instead of a received message. Clients that ignore the header still open
  the file, just not in compose mode.
- `From`, `Date` and `Message-ID` are **omitted** by default. Outlook supplies the account
  identity for a draft, and a `From` it cannot resolve makes Send fail with "You can't send a
  message on behalf of this user". Override with `--from` / `--date` only for non-Outlook use.
- Output names come from the **round directory** (the topic slug), not the markdown filename,
  because archiving renames `final.md` to `reply.md` at step 7d.
- Warnings go to stderr and never block; `--strict` turns them into a non-zero exit. An
  unknown frontmatter key is a warning — a typo silently dropping an attachment is the worst
  failure available here.
- Nothing is sent, ever. The command writes two local files.

### File conventions

- `AGENTS.md` — this file; authoritative spec (generic, no personal data).
- `CLAUDE.md` — thin `@AGENTS.md` include; kept separate so the parent multi-project `agents/`
  tree can compose project specs uniformly.
- `.claude/commands/reply-email.md` — slash-command entry; procedure glue + sub-skill pointers.
- `.claude/commands/reply-email/{archive,reply-style,build-mail}.md` — sub-skills for the archive
  procedure, the no-profile fallback style, and the `.eml`/`.ics` build.
- `scripts/build_mail.py` — the generator CLI, with `mail_frontmatter.py` (frontmatter),
  `mail_render.py` (body → HTML/plain) and `mail_ics.py` (calendar) beside it. Stdlib only,
  cross-platform; `tests/test_mail.py` covers all four.
- `style/profile.md`, `ongoing/`, `archived/` — local only, gitignored; never commit, never store
  in memory. Generated `.eml`/`.ics` files live in the round folder and are covered by the same
  rule — they contain real addresses and reference numbers.
