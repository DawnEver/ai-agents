# Reply-Email Agent

## Purpose

This project is a dedicated email-reply assistant. Its sole job is to draft, review, and
archive email replies on behalf of the user.

This file (`AGENT.md`) is the **single source of truth** for directory layout, naming
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
5. Create `ongoing/<topic>/` and write `original.txt` + `draft.md` + `final.md`. `final.md`
   starts identical to `draft.md`. If the directory already exists, resume from the existing
   files (jump to step 6 — the user is editing).
6. Tell the user the draft is ready. The user edits `final.md` directly. Never touch `draft.md`
   after creation. Optional polish: only if the user explicitly asks, edit `final.md`.
7. After approval, archive the round:
   - 7a. Move `ongoing/<topic>/` → `archived/<YYYY>/<MM>/<DD>/<topic>/` (apply the `-r<N>`
     suffix rule from **Naming conventions** if the same slug already archived today).
   - 7b. Diff `draft.md` vs `final.md` (before renaming) to identify what the user changed
     (see **Diff learning**).
   - 7c. Update style: promote patterns seen in ≥2 archives to `style/profile.md`; record
     per-reply observations in `meta.md` under `## Diff notes`.
   - 7d. Rename `final.md` → `reply.md` and write `meta.md` (see **meta.md schema**).
   - 7e. For continuations, set `prev:` in `meta.md` to the relative path of the immediately
     preceding round's folder (cosmetic; slug-based lookup is authoritative).

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

archived/<YYYY>/<MM>/<DD>/<topic>/  — one folder per exchange round (local only, gitignored)
  original.txt             — raw incoming email for this round only
  draft.md                 — AI's initial draft (preserved for diff learning)
  reply.md                 — sent reply (user's final.md, renamed after diff)
  meta.md                  — metadata + diff observations
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
sender: <sender name / address>
recipient: <recipient>      # optional — only for outgoing-initiated mail
date: <original email date, normalized to YYYY-MM-DD>
thread: <topic-slug>
round: <N>                  # 1-indexed position in the thread
prev: <relative path to preceding round's folder>   # omit for round 1
---

<1-2 sentence summary of this message in the thread>

## Diff notes

<what the user changed from draft.md to final.md: tone, phrasing, structure, additions, removals>
```

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

All committed files (`AGENT.md`, `CLAUDE.md`, `.claude/commands/*.md`, memory) are public-facing.
They must never contain:

- Real names, email addresses, or sender/recipient identities
- Reference numbers (application IDs, invoice numbers, ticket IDs)
- Specific institutional details identifying the user's university, department, or colleagues
- Verbatim content from actual correspondence

Use generic placeholders: `conference-invitation`, `prof.smith@example.com`, `[Your Name]`,
`project-proposal`. Real data lives exclusively in gitignored paths — `ongoing/`, `archived/`,
`style/profile.md`. A pre-commit hook (`.claude/hooks/check-pii.sh`) greps staged tracked files
for email-address and obvious PII patterns as a backstop; it is a safety net, not a substitute
for the rules above.

### File conventions

- `AGENT.md` — this file; authoritative spec (generic, no personal data).
- `CLAUDE.md` — thin `@AGENT.md` include; kept separate so the parent multi-project `agents/`
  tree can compose project specs uniformly.
- `.claude/commands/reply-email.md` — slash-command entry; procedure glue + sub-skill pointers.
- `.claude/commands/reply-email/{archive,reply-style}.md` — sub-skills for the archive procedure
  and the no-profile fallback style.
- `style/profile.md`, `ongoing/`, `archived/` — local only, gitignored; never commit, never store
  in memory.
