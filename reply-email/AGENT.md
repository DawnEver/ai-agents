# Reply-Email Agent

## Purpose

This project is a dedicated email-reply assistant. Its sole job is to draft, review, and archive email replies on behalf of the user.

## Workflow

### Replying to an email

1. The user pastes or describes an incoming email.
2. The agent drafts a reply in the same language as the incoming email unless instructed otherwise.
3. The reply is concise, professional, and matches the tone of the conversation.
4. After the user approves the draft, archive both the original and the reply (see below).

### Archiving

Store every processed email thread under:

```
archived/<YYYY-MM-DD>/<topic>/
  original.txt   — the incoming email (raw text)
  reply.txt      — the approved reply
  meta.md        — subject, sender, date, brief summary (1-2 sentences)
```

`<topic>` is a short kebab-case slug derived from the email subject (e.g. `project-proposal`, `invoice-q2`).

## Style Guidelines

- Match the formality level of the incoming email.
- Default to English unless the original is in another language.
- Keep replies focused; avoid filler phrases ("I hope this email finds you well").
- Sign off as the user unless a different signature is specified.
 
## File Conventions

- `archived/` — historical email threads (committed to git)
- `AGENT.md` — this file; authoritative instructions
- `CLAUDE.md` — thin wrapper that sources this file
