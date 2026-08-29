# reviewer-discovery — submissions under review

Implemented in the public **cc-academia** plugin and usable from Claude Code or
Codex. The workspace never assumes where that plugin is installed.

| Host | Invocation |
|------|------------|
| Claude Code only | Install `cc-academia` from its marketplace, then run `/cc-academia:reviewer-discovery <manuscript-pdf-or-slug>` |
| Codex only | Install `cc-academia` from its marketplace, then invoke the `reviewer-discovery` skill (or ask Codex to run reviewer discovery) with the same argument |

The package contains native manifests for both hosts. Neither installation
depends on the other host; the playbook derives its package root from its own
loaded path, without any plugin-root environment variable.

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

Implementation and design records belong in the plugin repository; this public
workspace contains only host-neutral usage guidance and review data.
