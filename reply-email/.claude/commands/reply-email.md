---
name: reply-email
description: Generate natural, conversational email replies, then archive the thread.
disable-model-invocation: true
allowed-tools: "Read,Write,Bash"
---

# Email Reply Generator

`AGENT.md` is the single source of truth for directory layout, naming, the meta.md schema,
globs, diff learning, and desensitization. This file is the operational sequence only — it
does not restate those conventions.

## Sequence

1. **Gather input** — ask for the received email + reply requirements/draft (any language).
   Check for thread continuation (a referenced archive, or "接着之前的继续").
2. **Identify** — sender, subject, date, language, tone. Derive the kebab-case slug
   (AGENT.md → Naming conventions). For continuations, reuse the existing slug.
3. **Learn style** — `style/profile.md` is authoritative; apply its rules directly. If it
   doesn't exist, bootstrap from archived replies: list recent threads and read up to 5
   `reply.md` files for greeting/closing/tone/structure. If neither exists, use the fallback
   → `reply-email/reply-style.md`.
4. **Thread history** — for continuations, locate all rounds by slug and read every
   `original.txt` + `reply.md` in date order (AGENT.md → Thread reconstruction & globs).
   Draft with full context; don't re-ask answered questions.
5. **Create ongoing** — `ongoing/<topic>/`: write `original.txt` + `draft.md` + `final.md`
   (copy of draft). If the dir exists, read existing files and jump to step 7.
6. **Draft** — write the reply into `draft.md`, copy to `final.md`.
7. **User edits** — tell the user `final.md` is ready; they edit it directly. Never touch
   `draft.md`. Polish `final.md` only if the user explicitly asks.
8. **Archive** — run the archive procedure → `reply-email/archive.md`.

## Key rules

- `draft.md` = AI's raw output, preserved untouched for diff learning. `final.md` = user's version.
- All data in `ongoing/`, `archived/`, `style/` is local only, gitignored — never commit, never
  store in memory.
