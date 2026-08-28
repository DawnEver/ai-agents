# reviewer-discovery — workspaces

Implemented as part of the **cc-academia** plugin:

```
Sync/claude/cc-market/cc-academia/skills/reviewer-discovery/
```

```
/cc-academia:reviewer-discovery <manuscript-pdf-or-slug>
```

This directory holds per-submission workspaces under `ongoing/<slug>/`, plus any
journal policy overrides you keep for yourself.

`Suggestions.md` is the original design conversation, kept for provenance. Where
it and the implementation disagree, the implementation won on evidence — the
reasoning is recorded in `../PLAN-cc-academia.md` §0.2.

## Confidentiality

Submissions are unpublished. Only `0-raw.pdf` and `1-manuscript/sanitized.json`
exist here per workspace, and only the sanitized record is ever read by an agent.
