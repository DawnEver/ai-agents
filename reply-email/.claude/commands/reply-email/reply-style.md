---
name: reply-email:reply-style
description: Fallback style, structure, and example — only when no profile or archives exist.
disable-model-invocation: true
---

# Reply Style (Fallback)

Read at step 6 only when neither `style/profile.md` nor archived replies exist.

## Style

- Conversational but professional — real conversation tone, not stiff corporate speak
- Fluent and natural — no awkward translation feel
- Concise and clear — no filler phrases ("I hope this email finds you well")
- Friendly and positive
- Reply in the same language as the incoming email

## Structure

```
Subject: Re: [Original subject]

Hi [Name],

[Body]

Best,
[Your Name]
```

## Example

**Received:**
```
From: prof.smith@example.com
Subject: Meeting about research project

Dear [Name],

I'd like to discuss your research project progress. Are you free this Friday afternoon?

Best,
Prof. Smith
```

**User requirements:** "Okay, Friday 3pm works, please let me know the meeting room location"

**AI generates `draft.md` + `final.md` (identical):**
```
Subject: Re: Meeting about research project

Hi Prof. Smith,

Thanks for reaching out! Friday afternoon at 3pm works perfectly for me. Could you let me know which meeting room we'll be in?

Looking forward to our discussion.

Best,
[Your Name]
```
