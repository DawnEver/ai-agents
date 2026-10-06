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

1. The user provides the incoming email — pasted, described, or as a saved `.msg`/`.eml` file
   (see **Reading incoming mail**) — plus their reply requirements or draft (any language).
   Check for thread continuation (a referenced archive, or "接着之前的继续").
2. Derive a kebab-case topic slug from the subject. For continuations, reuse the existing slug
   (see **Naming conventions**).
3. Read `style/profile.md` for the user's configured style (see **Style**). If it doesn't
   exist, infer patterns from up to 5 recent archived replies. Fall back to generic guidelines
   only when neither exists.
4. For continuations, load thread history (see **Thread reconstruction**) so the draft is aware
   of everything said before — don't re-ask answered questions, and don't re-answer them either
   (see **Reply scope**).
5. Create `ongoing/<topic>/` and write `original.txt` + `draft.md`. When the incoming mail
   arrived as a file, let the reader write `original.txt` and its attachments rather than
   retyping the body. Then copy `draft.md` to `final.md` with a shell command (`cp`), never by
   regenerating the content. If the directory already exists, resume from the existing files
   (jump to step 6 — the user is editing).
   **Never archive until the user explicitly says "归档" (or "archive").** Creating the ongoing
   directory and presenting the draft is the end of this step — wait.
6. Tell the user the draft is ready. The user edits `final.md` directly. Never touch `draft.md`
   after creation. Optional polish: only if the user explicitly asks, edit `final.md`.
   - **Read `final.md` first, and edit it — never `Write` over it.** The user annotates `final.md`
     in place, including inline comments in their own language that are *instructions to resolve
     into prose*, not text to send. A blind `Write` destroys them silently, and the loss stays
     invisible until the user notices. Fold each comment's meaning into the sentence it sits on,
     drop the comment itself, and ask when the intent is ambiguous.
   - The user's own edits to `final.md` win: keep their wording and structure, and add nothing
     back that they cut. Fix only outright language errors — a translation slip such as
     "experience formula" for "empirical formula" — and report each fix so it can be reverted.
   - 6a. Build the importable files (see **Mail and calendar generation**) so the round can be
     opened in a mail client instead of hand-pasted. Regenerate after every edit to `final.md`.
     This is a convenience, not an approval — the archive gate below is unchanged.
7. After approval (user says "归档" or "archive"), archive the round:
   - 7a. Move `ongoing/<topic>/` → `archived/<YYYY>/<MM>/<DD>/<topic>/` (apply the `-r<N>`
     suffix rule from **Naming conventions** if the same slug already archived today). A plain
     `mv` fails with "Device or resource busy" under OneDrive, so copy and verify instead:
     `cp -r`, then `diff -r` the two, then clear the source with
     `python scripts/clear_ongoing.py ongoing/<topic>` — the script refuses unless the
     archived copy is proven to cover every file, so it doubles as the check that the copy
     landed. It knows `final.md` becomes `reply.md` (step 7d) and is not confused by it.
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

### Reply scope

`original.txt` holds the whole quoted thread, but a reply answers **only the newest message** in
it. Every earlier quoted turn is context for understanding that message — never a to-do list, and
never something to answer again.

- **Answer only what's new.** The latest message is the sole prompt. If a line could have been
  written without reading it, cut the line.
- **Never restate the correspondent's own instructions.** Playing their method back to them ("as
  you described, I'll do A, then B, then C") is their text in your voice: it reads as filler and
  signals the mail wasn't thought about. Confirm by doing, or in one clause at most.
- **Never re-answer a settled point.** If an earlier round already supplied the operating point,
  the formula, or a commitment, it stays answered. Restating it spends the recipient's attention
  on nothing they didn't already have.
- **Acknowledgement is a word, not a paragraph.** "Understood", "Noted", "Will do" — then
  straight to the substance. A reply whose only new content is an acknowledgment is a short
  reply, not a padded one.
- **New substance earns length; repetition never does.** The proposal, the finding, the number
  the correspondent asked for — develop those. Everything inherited from the thread gets one
  clause or nothing.

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

### Reading incoming mail

`scripts/read_mail.py` turns a saved `.msg` or `.eml` into the round's `original.txt`, with
every attachment written beside it. Zero dependencies (Python stdlib only). It is the inbound
counterpart to `build_mail.py`: reading a mail in, versus sending a reply out.

```bash
python scripts/read_mail.py "~/Downloads/message.msg" --out ongoing/<topic>
```

- **Format is detected from content, not the extension.** A `.msg` is an OLE compound file,
  not RFC 822, so the stdlib `email` package cannot read it at all; `mail_msg.py` parses the
  container directly. A `.msg`-named file that is not a compound file is an error, never a
  silently mis-parsed `.eml`.
- **Without `--out`, nothing is written** — the rendered `original.txt` goes to stdout, so the
  message can be checked before it lands in a round folder. `--json` reports the envelope
  (`from`, `to`, `cc`, `date`, `subject`, attachments) for programmatic use.
- **`original.txt` carries a header block** — `From`, `To`, `Cc`, `Date`, `Subject`,
  `Message-ID`, `Source`, then the body, then an `Attachments:` list. Those fields are where
  the reply's frontmatter comes from: the addresses fill `to:`/`cc:`, and the `Message-ID`
  fills `in-reply-to:`. A `Source:` line records which file the round was read from.
- **Attachments are written with counter-suffixed names** when a message reuses one
  (`image.png`, `image-2.png`). Outlook names every inline image `image001.jpg`, so a naive
  write keeps only the last one. Names are also flattened to a bare filename, because they
  arrive from the network.
- **Inline images appear in the body as `[inline image: <name>]`**, so an HTML-only mail that
  carries its content in a screenshot is legible in the text file. `--plain` drops the markers.
- **An HTML-only body is converted to text** with paragraph structure preserved; a
  `text/plain` part, when present, is used verbatim instead.
- **A body that is empty of content warns.** A forwarded mail is often signature-only, with
  everything meaningful in a screenshot or attachment — read those images and write what they
  show into `original.txt`, because the images are unreadable to anything that reads only text.
- Warnings go to stderr and never block; `--strict` turns them into a non-zero exit.

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
from: me@example.com
subject: Re: Project meeting
in-reply-to: <abc123@example.com>
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
  has nothing to build. `from:` is your own address and is what Outlook's Reply will answer,
  so set it on any round built in the default received style.
- **Message-id keys** — `message-id`, `in-reply-to` and `references` take message-ids,
  comma- or space-separated, with or without angle brackets (they are added if missing).
  `references` defaults to the `in-reply-to` value, and `message-id` takes exactly one.
  Take ids from the round's `original.txt`, where the reader records the incoming
  `Message-ID`. A reply with neither `in-reply-to` nor `references` arrives as a new
  conversation rather than in the thread.
- **Two shapes the `.eml` can take**, decided entirely by the frontmatter — there is no mode
  flag, so any round can be built either way:
  - **Outgoing reply** — `to:` the correspondent, `in-reply-to:` their id. The file is the
    message you are about to send.
  - **Reply-ready scaffold** — `from:` the correspondent, `to:` yourself, `message-id:` set
    to *their* id, and no `in-reply-to:`. The file stands in for their message, so
    double-clicking it and pressing Reply opens a compose window already addressed to them
    and already in the thread, with the draft text in the quoted region. This is what makes
    a round answerable in one click instead of hunting for the original.
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

- The `.eml` opens as a **received message** by default, so double-clicking it gives a reading
  window with Reply and Reply All. `--as-draft` adds `X-Unsent: 1` instead, which opens a
  compose window with a Send button — and therefore *no* Reply, since it is already a reply.
  The two are mutually exclusive: no message is both already sent and not yet sent.
- `Date` and `Message-ID` are **omitted** by default, and so is `From` — but `From` matters in
  the default style, because it is the address Reply will answer. The builder warns when it is
  missing. In draft mode Outlook supplies the account identity, so an unresolvable `From` makes
  Send fail with "You can't send a message on behalf of this user"; set `from:` only when you
  need it. `--from` / `--date` override the frontmatter for non-Outlook use.
- Message-id headers are written **unencoded**. The stdlib folds an unregistered header over
  the line limit by RFC 2047-encoding it, which turns `<abc@x>` into `=3Cabc=40x=3E` — a value
  no client can thread on. `In-Reply-To` and `References` are registered as folded id lists
  instead, so a long id stays literal and a whole chain survives; `Message-ID` is registered
  as a single id by default and needs no help.
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
- `scripts/read_mail.py` — the reader CLI, with `mail_read.py` (shared `ParsedMail` model,
  HTML → text, `original.txt` rendering), `mail_msg.py` (Outlook `.msg`) and `mail_eml.py`
  (RFC 822) beside it. Stdlib only, cross-platform; `tests/test_read_mail.py` covers all four.
- `scripts/clear_ongoing.py` — the post-archive cleanup CLI (step 7a). Removes a round from
  `ongoing/` only after proving the archived copy holds every file, which is what makes it safe
  to run unattended. Stdlib only, cross-platform; `tests/test_clear_ongoing.py` covers it, and
  is mostly refusal cases — that is the part that matters.
- `style/profile.md`, `ongoing/`, `archived/` — local only, gitignored; never commit, never store
  in memory. Generated `.eml`/`.ics` files and extracted `original.txt`/attachments live in the
  round folder and are covered by the same rule — they contain real addresses and reference
  numbers.

## Change the tool at its source

The workflow for this project ships as a plugin. Fix it in the plugin's own
source checkout, never in the copy the host installed under `~/.claude/plugins/`
or `~/.codex/` — that is a cache and the edit will be overwritten. If the source
checkout cannot be discovered, ask the user for the path rather than guessing or
editing the cache. Never commit an absolute path to it. See
`../.claude/rules/TOOL-SOURCE.md`.
