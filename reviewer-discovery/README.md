# reviewer-discovery — submissions under review

Implemented in the **cc-academia** plugin:

```
Sync/claude/cc-market/cc-academia/skills/reviewer-discovery/
```

```
/cc-academia:reviewer-discovery <manuscript-pdf-or-slug>
```

| Path | What it is |
|------|------------|
| `ongoing/<slug>/` | submissions currently being matched to reviewers |
| `archived/<slug>/` | finished runs |

The plugin finds this directory by walking up from wherever you are, so nothing
needs configuring. Set `ACADEMIA_CONTACT` to your own address in your personal
settings if you want OpenAlex's polite pool — it is per-person, so it does not
belong in a file that syncs across machines.

## Confidentiality

Submissions are unpublished. Each workspace holds `0-raw.pdf` and
`1-manuscript/sanitized.json`, and only the sanitized record is ever read by an
agent — enforced in the CLI, with a permission rule as a second lock.

The design record, including which API assumptions turned out to be wrong, is in
`.claude/memory/2026/08/28/cc-academia-migration.md`.
