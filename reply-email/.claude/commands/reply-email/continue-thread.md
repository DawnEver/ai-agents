---
name: reply-email:continue-thread
description: Thread continuation — locate history, identify position, draft with full context.
disable-model-invocation: true
---

# Continue Thread

Read when the user references a previous archive or asks to continue a conversation (step 4).

## Locate the thread

Find all archived directories matching the topic slug. Try both globs (old flat format may still exist): `ls -d archived/*/<topic> archived/*/*/*/<topic> 2>/dev/null`. Read every `original.txt` and `reply.md` in date order to reconstruct the full conversation.

## Identify position

Count existing messages in the thread. The new reply is position N+1.

## Draft with full context

The new reply should be aware of everything said before. Don't re-ask answered questions. Reference prior messages naturally when helpful.

## Same topic slug

Always reuse the original topic slug across the entire thread — the slug binds the thread together.
