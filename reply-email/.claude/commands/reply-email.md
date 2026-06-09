---
name: reply-email
description: Generate natural, conversational English email replies, then archive the thread.
disable-model-invocation: true
allowed-tools: "Read,Write,Bash"
---

# Email Reply Generator

## Workflow

1. **Gather input** — ask for the received email + reply requirements/draft (Chinese or English). Check for thread continuation (e.g. `@archived/2026/06/01` or "接着之前的继续").
2. **Identify** — sender, subject, date, language, tone. Derive kebab-case topic slug. For continuations, reuse existing slug.
3. **Learn style** — read `style/profile.md` (authoritative). If missing, infer from archives. → `.claude/commands/reply-email/style-learning.md`
4. **Thread history** — if continuation, load all prior `original.txt` + `reply.md` for the topic slug. → `.claude/commands/reply-email/continue-thread.md`
5. **Create ongoing** — `ongoing/<topic>/`: write `original.txt` (raw email) + `draft.md` (AI draft) + `final.md` (copy of draft). If dir exists: read existing files, jump to step 7 (user edits).
6. **Draft** — write reply into `draft.md`, copy to `final.md`. If no profile and no archives exist, → `.claude/commands/reply-email/reply-style.md`
7. **User edits** — tell user `final.md` is ready. User edits `final.md` directly. Never touch `draft.md` after creation.
8. **Optional polish** — only if user explicitly asks, edit `final.md`. Keep `draft.md` untouched.
9. **Archive** — move to `archived/<YYYY>/<MM>/<DD>/<topic>/`, diff `draft.md` vs `final.md`, rename `final.md` → `reply.md`, add `meta.md`. → `.claude/commands/reply-email/archive.md`

## Key rules

- `draft.md` = AI's raw output, preserved untouched for diff learning. `final.md` = user's version.
- `original.txt` = raw email (plain text). `.md` files = structured reply content.
- Thread linkage via slug-based lookup. Try both globs: `archived/*/*/*/<topic>/` (nested) and `archived/*/<topic>/` (flat, legacy). `prev:` in meta.md is cosmetic.
- All data in `ongoing/`, `archived/`, `style/` is local only, gitignored — never commit, never store in memory.
- `AGENT.md` is the authoritative reference for directory structure, file conventions, and desensitization rules.
