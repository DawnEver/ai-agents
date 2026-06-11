---
name: gitignore-recursive-reinclude
description: ai-post/.gitignore memory re-include must be recursive or migrate untracks memory content
metadata:
  type: project
---

`ai-post/.gitignore` once used a non-recursive re-include (`!.claude/memory/*`)
under a `.claude/*` exclusion. Because `.claude/*` excludes the `memory`
directory itself, git cannot re-include anything inside an excluded parent, so
ALL `.claude/memory/**/*.md` read as ignored. The `/migrate` untrack pass then
`git rm --cached`'d every memory content file.

**Why:** ai-post is NOT its own git repo — it lives inside the top `agents`
repo. migrate only normalizes git-root `.gitignore`s, so a stale nested
`ai-post/.gitignore` overrode the root template for the ai-post subtree, and
migrate's repo-wide untrack pass acted on that stale state.

**How to apply:** keep ai-post/.gitignore on the depth-agnostic template with
BOTH the directory line and recursive glob: `!**/.claude/memory/` plus
`!**/.claude/memory/**` (same for rules/skills/etc). Generated files
(`MEMORY.md`, `_meta.json`, `tasks/`) stay ignored by design. After any
migrate run touching this monorepo, verify `git check-ignore` on a sample
memory file returns exit 1 (not ignored).
