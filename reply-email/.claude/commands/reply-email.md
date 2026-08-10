---
name: reply-email
description: Generate natural, conversational email replies, then archive the thread.
disable-model-invocation: true
allowed-tools: "Read,Write,Bash"
---

# Email Reply Generator

`AGENTS.md` is the single source of truth for directory layout, naming, the meta.md schema,
globs, diff learning, and desensitization. This file is the operational sequence only — it
does not restate those conventions.

## Host-neutral style loading

Before drafting, apply `.claude/output-styles/Email.md` as the prose-system prompt. Claude Code
may already have injected it through the project's output-style setting; if so, do not inject or
read it a second time. On hosts such as Codex where it is not already present, read it explicitly
and treat it as authoritative for prose only. `style/profile.md` still overrides its generic voice
defaults, as specified by that file.

## Sequence

1. **Gather input** — ask for the received email + reply requirements/draft (any language).
   Check for thread continuation (a referenced archive, or "接着之前的继续").
2. **Identify** — sender, subject, date, language, tone. Derive the slug (AGENTS.md → Naming
   conventions). For continuations, reuse the existing slug.
3. **Learn style** — `style/profile.md` is authoritative; apply its rules directly. If absent,
   bootstrap from archived replies (AGENTS.md → Workflow step 3). If neither exists, use the
   fallback → `reply-email/reply-style.md`.
4. **Thread history** — for continuations, reconstruct the thread by slug (AGENTS.md → Thread
   reconstruction & globs). Draft with full context; don't re-ask answered questions.
5. **Create ongoing & draft** — create `ongoing/<topic>/` with `original.txt` + `draft.md`,
   then copy `draft.md` to `final.md` with a shell `cp` (AGENTS.md → Workflow step 5). If the
   directory already exists, the user is mid-edit — resume from the existing files instead.
6. **User edits** — tell the user `final.md` is ready; they edit it directly. Polish `final.md`
   only if the user explicitly asks.
7. **Wait for explicit approval.** **Never archive until the user says "归档" (or "archive").**
   Presenting the draft is the end of this sequence — stop and wait.
8. **Archive** — only after explicit approval: run the archive procedure →
   `reply-email/archive.md`.
