---
name: paper-rerun
description: Re-run a single step of the paper-review pipeline against an existing slug. Replaces the old paper-archive / paper-repolish skills.
argument-hint: <step-number> <slug>
allowed-tools: "Read,Write,Bash,Glob,Grep,Agent,Skill"
---

# /paper-review:rerun — Re-run one step

Usage:
```
/paper-review:rerun 7 majestic-book        # re-polish (regenerate final.md from draft.md)
/paper-review:rerun 8 majestic-book        # re-archive (move + update style + angles)
/paper-review:rerun 5 majestic-book        # re-aggregate critiques.md
/paper-review:rerun 2 majestic-book        # rewrite summary.md
```

## How it works

1. Read `.claude/skills/paper-review/0<N>-*.md` for the requested step.
2. Execute that step's playbook against `ongoing/<slug>/` (or `archived/<slug>/` if the slug is already archived — in that case any new output is written next to the old with a `.<timestamp>` suffix, never overwriting the archive).
3. Steps 7 and 8 are the common cases; steps 1–6 work too but should be rare.

## Convenience aliases

| Old call | Now |
|----------|-----|
| `/paper-review:archive <slug>` | `/paper-review:rerun 8 <slug>` |
| `/paper-review:repolish <slug>` | `/paper-review:rerun 7 <slug>` |

## Hard rules

- Reruns against `archived/<slug>/` never overwrite the existing snapshot; suffix outputs with a timestamp.
- For step 7 specifically: enforce plain-text output (see `07-polish.md`).
- For step 8: dedup + rolling caps still apply.
