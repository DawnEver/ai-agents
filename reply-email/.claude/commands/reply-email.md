---
name: reply-email
description: Generate natural, conversational English email replies, then archive the thread. Provide the received email and your draft/key points to get a polished reply.
disable-model-invocation: true
allowed-tools: "Read,Write,Bash"
---

# Email Reply Generator

Generate natural, fluent, conversational English email replies, then archive the original and reply for future reference.

## Workflow

1. **Gather input** — ask the user to paste the received email if not already provided, plus their reply draft or key points (Chinese or English accepted).
2. **Identify** — sender, subject, date, language, tone, and derive a kebab-case topic slug from the subject.
3. **Learn existing style** — read `style/profile.md` first (authoritative). If it doesn't exist, infer patterns from up to 5 recent `reply.txt` files in `archived/`. See Style Learning section below.
4. **Create or resume ongoing directory** — if `ongoing/<topic>/` doesn't exist, create it and write `original.txt` + initial `draft.md`. If it already exists, read the existing `draft.md` and jump to step 6 (iteration).
5. **Draft the reply** — write the initial draft into `draft.md`. Use the learned style from step 3. If step 3 found no patterns (first use, no profile, no archive), use the Reply Style fallback section below.
6. **Iterate** — tell the user the draft is ready at `ongoing/<topic>/draft.md`. The user reviews and gives feedback; you edit `draft.md` directly. Repeat until approved. Every revision round starts by re-reading `draft.md`.
7. **Archive** — move `ongoing/<topic>/` to `archived/<YYYY-MM-DD>/<topic>/`, rename `draft.md` → `reply.txt`, add `meta.md`, then update `style/profile.md`. All files are local only — never commit, never store in memory.

## Reply Style (fallback)

Only used when neither `style/profile.md` nor archived replies exist. Once a profile is established, this section is ignored.

- Conversational but professional — real conversation tone, not stiff corporate speak
- Fluent and natural — no awkward translation feel
- Concise and clear — no filler phrases ("I hope this email finds you well")
- Friendly and positive
- Reply in the same language as the incoming email

## Reply Structure

```
Subject: Re: [Original subject]

Hi [Name],

[Body]

Best,
[Your Name]
```

## Usage Example

**Received email:**
```
From: prof.smith@example.com
Subject: Meeting about research project

Dear [Name],

I'd like to discuss your research project progress. Are you free this Friday afternoon?

Best,
Prof. Smith
```

**User draft:** "Okay, Friday 3pm works, please let me know the meeting room location"

**Output:**
```
Subject: Re: Meeting about research project

Hi Prof. Smith,

Thanks for reaching out! Friday afternoon at 3pm works perfectly for me. Could you let me know which meeting room we'll be in?

Looking forward to our discussion.

Best,
[Your Name]
```

## Style Learning (step 3)

`style/profile.md` is the authoritative style source. Archived replies are only scanned when the profile doesn't exist yet — to bootstrap it.

**How to learn:**

1. Read `style/profile.md`. If it exists, apply its rules directly — skip archived replies.
2. If `style/profile.md` doesn't exist yet, infer patterns from archived replies:
   - List `archived/` subdirectories sorted by date (descending).
   - Read `reply.txt` from the most recent threads (up to 5; fewer is fine).
   - Note patterns: greeting, closing, signature, tone, paragraph style, contractions, scenario handling (scheduling, declining, asking questions, thanking).
3. If neither exists (first use), rely on the Reply Style fallback below.

## Ongoing (step 4–6)

The `ongoing/` directory holds in-progress drafts. Every reply is drafted here first, then moved to `archived/` on approval.

```
ongoing/<topic>/
  original.txt   — raw incoming email (written once)
  draft.md       — working reply draft (read + written every iteration)
```

Conversation between you and the user revolves around `draft.md`:
- You write the initial draft into it.
- The user reads it and gives feedback.
- You re-read `draft.md`, apply the feedback, and write it back.
- Repeat until approved.

## Archive (step 7)

After approval:

1. Move `ongoing/<topic>/` → `archived/<YYYY-MM-DD>/<topic>/` (use `mv` — the ongoing directory is gone after this).
2. Rename `draft.md` → `reply.txt`.
3. Create `meta.md`.

Final archived structure:
```
archived/<YYYY-MM-DD>/<topic>/
  original.txt   — raw incoming email
  reply.txt      — approved reply
  meta.md        — structured metadata
```

### meta.md format

```markdown
---
subject: <email subject>
sender: <sender name / address>
date: <original email date, normalized to YYYY-MM-DD>
---

<1-2 sentence summary of the thread>
```

Archived and ongoing files are local only — both are gitignored. Never commit them and never write email content into the memory system.

### After archiving: update style profile

After each archive, check whether the just-archived reply reveals new style patterns. Only update `style/profile.md` when a pattern appears in **at least 2 archived replies** — a one-off choice shouldn't get baked into the profile. When creating the profile for the first time, bootstrap it from the first reply but mark uncertain entries with `(tentative)`.

The profile should record:

```markdown
# Email Style Profile

## Signature
[Your Name]

## Greeting
- Default: Hi [Name],
- Formal recipients: Dear [Title] [Surname],

## Closing
- Default: Best,

## Tone
- Conversational but professional
- [add other persistent patterns]
```

If `style/profile.md` already exists, read it first, merge in new observations, and write it back. This profile accumulates knowledge — it should only grow more accurate over time.

## Style Profile (`style/`)

```
style/
  profile.md    — accumulated style data (signature, greeting, tone, etc.)
```

- `style/` is local only, gitignored — same as `archived/` and `ongoing/`.
- `profile.md` is the authoritative style source for step 3. Updated when patterns appear in ≥2 archived replies.
- Contains no raw email content — only distilled style patterns.
