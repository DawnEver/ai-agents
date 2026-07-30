---
name: reply-email:archive
description: Archive procedure — move, diff-learn, update style, rename, write meta.md.
disable-model-invocation: true
---

# Archive Procedure

Run at the **Archive** step, and only after the user has explicitly said "归档" / "archive".
All formats referenced here are defined once in `AGENT.md` (Reference section) — do not
restate them. Step order mirrors AGENT.md → Workflow step 7.

## Steps

1. Move `ongoing/<topic>/` → `archived/<YYYY>/<MM>/<DD>/<topic>/` with `mv`. If the same slug
   already archived today, apply the `-r<N>` suffix (AGENT.md → Naming conventions).
2. Diff `draft.md` vs `final.md` **before renaming** and learn from it
   (AGENT.md → Diff learning).
3. Update style: promote any pattern seen in ≥2 archived replies to `style/profile.md`
   (read it first, merge, write back, bump `## Last checked`). One-off edits stay in
   `meta.md` only.
4. Rename `final.md` → `reply.md` (`mv final.md reply.md`). Keep `draft.md` untouched.
5. Write `meta.md` (AGENT.md → meta.md schema): frontmatter + summary + `## Diff notes`.
   For continuations, set `round:` and `prev:` (repo-root-relative path to the preceding
   round's folder; round N = previous rounds + 1, per the slug glob).
