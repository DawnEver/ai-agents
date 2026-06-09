---
name: reply-email:style-learning
description: Learn email style from profile.md or archived replies.
disable-model-invocation: true
---

# Style Learning

Read at step 3 to learn the user's email style.

`style/profile.md` is the authoritative style source. Archived replies are only scanned when the profile doesn't exist yet — to bootstrap it.

## Procedure

1. Read `style/profile.md`. If it exists, apply its rules directly — skip archived replies.
2. If `style/profile.md` doesn't exist yet, infer patterns from archived replies:
   - List `archived/` subdirectories sorted by date (descending). Use `ls -d archived/*/*/*/*/reply.md archived/*/*/reply.md 2>/dev/null` to cover both nested (`YYYY/MM/DD`) and flat (`YYYY-MM-DD`) layouts.
   - Read `reply.md` from the most recent threads (up to 5).
   - Note patterns: greeting, closing, signature, tone, paragraph style, contractions, scenario handling.
3. If neither exists (first use), rely on the Reply Style fallback (→ `reply-email/reply-style.md`).
