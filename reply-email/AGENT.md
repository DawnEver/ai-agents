# Reply-Email Agent

## Purpose

This project is a dedicated email-reply assistant. Its sole job is to draft, review, and archive email replies on behalf of the user.

## Workflow

### Replying to an email

1. The user provides the incoming email (paste or describe) and their reply requirements or draft (Chinese or English).
2. Derive a kebab-case topic slug from the subject.
3. Read `style/profile.md` for the user's configured style (signature, greeting, tone). If it doesn't exist, infer patterns from up to 5 recent archived replies. Fall back to generic guidelines only when neither exists.
4. Create `ongoing/<topic>/` and write `original.txt` + `draft.md` + `final.md`. `final.md` starts identical to `draft.md`. If the directory already exists, resume from the existing files.
5. Tell the user the draft is ready. The user edits `final.md` directly to match their needs — no agent iteration unless the user explicitly requests polish.
6. Optional polish: if the user asks for refinement, edit `final.md` based on their feedback. Repeat only if they ask again.
7. After approval, move `ongoing/<topic>/` → `archived/<YYYY>/<MM>/<DD>/<topic>/`, diff `draft.md` vs `final.md` to learn, rename `final.md` → `reply.md`, add `meta.md`.
   - For thread continuations (same topic slug, prior archived rounds exist): set `prev:` in `meta.md` to the relative path of the immediately preceding round's folder (cosmetic; slug-based lookup is authoritative).
   - **Learn from diff**: diff `draft.md` vs `final.md` before renaming. Identify what the user changed (tone, phrasing, structure, additions, removals). Save persistent patterns (seen in ≥2 archives) to `style/profile.md`. Record per-reply observations in `meta.md`.

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
  meta.md                  — subject, sender, date, summary; `prev:` link; diff observations
```

`<topic>` is a short kebab-case slug derived from the email subject (e.g. `project-proposal`, `invoice-q2`).

## Style Guidelines

These are generic defaults. The authoritative style source is `style/profile.md` (user's private config).

- Match the formality level of the incoming email.
- Default to English unless the original is in another language.
- Keep replies focused; avoid filler phrases ("I hope this email finds you well").
- Signature, greeting, and closing are read from `style/profile.md`.

## Diff Learning (step 7)

When archiving, diff `draft.md` against `final.md` to understand what the user changed. This is the primary feedback loop for improving future drafts.

**What to look for:**
- Tone shifts (more/less formal, more/less direct)
- Phrasing replacements (specific words or phrases the user consistently changes)
- Structural edits (reordered paragraphs, added/removed sections)
- Signature/closing changes
- Subject line adjustments
- Content additions or removals

**How to apply:**
- Record observations in `meta.md` under a `## Diff notes` section.
- If a pattern appears across ≥2 archived replies, promote it to `style/profile.md`.
- One-off edits stay in `meta.md` only — don't overfit to a single email.

## File Conventions

- `style/profile.md` — user's private style config (signature, greeting, tone); local only, gitignored
- `ongoing/` — in-progress drafts (local only, gitignored)
- `archived/` — completed email threads (local only, gitignored)
- `AGENT.md` — this file; authoritative instructions (generic, no personal data)
- `CLAUDE.md` — thin wrapper that sources this file
- `.claude/commands/reply-email.md` — slash command definition; committed, must be desensitized

## Desensitization

All committed files (AGENT.md, CLAUDE.md, `.claude/commands/*.md`) are public-facing. They must never contain:

- Real names, email addresses, or sender/recipient identities
- Reference numbers (application IDs, invoice numbers, ticket IDs)
- Specific institutional details that identify the user's university, department, or colleagues
- Verbatim email content from actual correspondence

Examples, directory listings, and inline comments must use generic placeholders: `conference-invitation`, `prof.smith@example.com`, `[Your Name]`, `project-proposal`.

Real data lives exclusively in gitignored files — `ongoing/`, `archived/`, `style/profile.md`. Before committing any change to a tracked file, verify it contains no PII.
