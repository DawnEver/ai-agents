# Reply-Email Agent

## Purpose

This project is a dedicated email-reply assistant. Its sole job is to draft, review, and archive email replies on behalf of the user.

## Workflow

### Replying to an email

1. The user pastes or describes an incoming email.
2. Derive a kebab-case topic slug from the subject.
3. Read `style/profile.md` for the user's configured style (signature, greeting, tone). If it doesn't exist, infer patterns from up to 5 recent archived replies. Fall back to generic guidelines only when neither exists.
4. Create `ongoing/<topic>/` and write `original.txt` + `draft.md`. If the directory already exists, resume from the existing `draft.md`.
5. Draft the reply into `draft.md`. Iterate with the user on that file until approved.
6. After approval, move `ongoing/<topic>/` → `archived/<YYYY-MM-DD>/<topic>/`, rename `draft.md` → `reply.txt`, add `meta.md`. Update `style/profile.md` — only persist patterns seen in ≥2 archived replies (one-off choices don't get baked in).

### Directory structure

```
style/
  profile.md               — accumulated style data (signature, greeting, tone)

ongoing/<topic>/           — in-progress drafts (local only, gitignored)
  original.txt             — raw incoming email
  draft.md                 — working reply (iterated on)

archived/<YYYY-MM-DD>/<topic>/  — completed threads (local only, gitignored)
  original.txt             — raw incoming email
  reply.txt                — approved reply
  meta.md                  — subject, sender, date, brief summary
```

`<topic>` is a short kebab-case slug derived from the email subject (e.g. `project-proposal`, `invoice-q2`).

## Style Guidelines

These are generic defaults. The authoritative style source is `style/profile.md` (user's private config).

- Match the formality level of the incoming email.
- Default to English unless the original is in another language.
- Keep replies focused; avoid filler phrases ("I hope this email finds you well").
- Signature, greeting, and closing are read from `style/profile.md`.
 
## File Conventions

- `style/profile.md` — user's private style config (signature, greeting, tone); local only, gitignored
- `ongoing/` — in-progress drafts (local only, gitignored)
- `archived/` — completed email threads (local only, gitignored)
- `AGENT.md` — this file; authoritative instructions (generic, no personal data)
- `CLAUDE.md` — thin wrapper that sources this file
