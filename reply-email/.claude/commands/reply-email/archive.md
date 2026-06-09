---
name: reply-email:archive
description: Archive procedure, meta.md format, diff learning, style profile update.
disable-model-invocation: true
---

# Archive Procedure

Read when reaching step 9 (Archive).

## Steps

1. Move `ongoing/<topic>/` → `archived/<YYYY>/<MM>/<DD>/<topic>/` (use `mv`).
2. Diff `draft.md` vs `final.md` and learn (see Diff learning below).
3. Rename `final.md` → `reply.md` (`mv final.md reply.md`).
4. Create `meta.md` with diff observations.

Final archived structure:
```
archived/<YYYY>/<MM>/<DD>/<topic>/
  original.txt   — raw incoming email
  draft.md       — AI's initial draft (preserved for learning)
  reply.md       — sent reply (user's final.md, renamed)
  meta.md        — metadata + diff notes
```

## meta.md format

```markdown
---
subject: <email subject>
sender: <sender name / address>
date: <original email date, normalized to YYYY-MM-DD>
thread: <topic-slug>
position: <N>
---

<1-2 sentence summary of this message in the thread>

## Diff notes

<what the user changed from draft.md to final.md: tone, phrasing, structure, additions, removals>
```

- `thread` — kebab-case topic slug, same across all messages in the thread.
- `position` — this message's position in the thread (1-indexed).
- `prev` — relative path to the preceding round's folder (e.g. `../../../../2026/06/04/conference-invitation`). Omit for first message. Cosmetic convenience; thread reconstruction always uses slug-based lookup (`archived/*/*/*/<topic>/`).

## Thread example

```
archived/2026/05/20/conference-invitation/
  original.txt   — initial invitation email
  draft.md       — AI's initial draft
  reply.md       — sent reply
  meta.md        — thread: conference-invitation, position: 1

archived/2026/05/25/conference-invitation/
  original.txt   — reply with logistics details
  draft.md       — AI's initial draft
  reply.md       — sent reply
  meta.md        — thread: conference-invitation, position: 2, prev: ../../../../2026/05/20/conference-invitation
```

Messages in the same thread share a topic slug across archive dates.

## Diff learning

```bash
diff -u draft.md final.md
```

Analyze the differences:
- **Tone shifts** — more/less formal, more/less direct?
- **Phrasing** — specific words/phrases the user replaced
- **Structure** — reordered paragraphs, merged/split sections
- **Additions** — what did the user add that the AI missed?
- **Removals** — what did the user remove (filler, redundancy)?

Record observations in `meta.md` under `## Diff notes`. If a pattern recurs across ≥2 archived replies, promote it to `style/profile.md`. One-off edits stay in `meta.md` only.

## Update style profile

After archiving, check whether the diff reveals new style patterns. Only update `style/profile.md` when a pattern appears in ≥2 archived replies — one-off choices don't get baked in.

Profile format:
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

Read existing profile first, merge new observations, write back.
