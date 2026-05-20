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
2. **Identify** — sender, subject, date, language, and tone.
3. **Draft the reply** — follow the style requirements below.
4. **Present and iterate** — show the draft; revise until the user approves.
5. **Archive** — write the three files below, then offer to commit.

## Reply Style

- Conversational but professional — real conversation tone, not stiff corporate speak
- Fluent and natural — no awkward translation feel
- Concise and clear — no filler phrases ("I hope this email finds you well")
- Friendly and positive

## Reply Structure

```
Subject: Re: [Original subject]

Hi [Name],

[Body]

Best,
Lin
```

## Usage Example

**Received email:**
```
From: prof.smith@nottingham.ac.uk
Subject: Meeting about research project

Dear Lin,

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
Lin
```

## Archive (after approval)

Write these files using today's date (`YYYY-MM-DD`) and a kebab-case topic slug from the subject:

- `archived/<YYYY-MM-DD>/<topic>/original.txt` — raw incoming email
- `archived/<YYYY-MM-DD>/<topic>/reply.txt` — approved reply
- `archived/<YYYY-MM-DD>/<topic>/meta.md` — structured metadata

### meta.md format

```markdown
---
subject: <email subject>
sender: <sender name / address>
date: <original email date>
---

<1-2 sentence summary of the thread>
```

After writing the files, offer to commit:
```
git add archived/ && git commit -m "archive: <topic>"
```
