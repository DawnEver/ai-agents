# agents

Host-neutral workspaces for Claude Code and Codex. Each workflow can be used by
someone who has installed only one of the two hosts; no host depends on the
other's configuration directory or environment variables.

## Projects

| Directory | Purpose |
|-----------|---------|
| `reply-email/` | Draft and archive email replies (`$reply-email` in Codex, `/reply-email` in Claude Code) |
| `ai-post/` | — |
| `manuscript-review/` | Confidential academic-paper review data for the public `cc-academia` plugin (`manuscript-review` skill in Codex, `/cc-academia:manuscript-review` in Claude Code) |
| `literature-review/` | Systematic-review data for the public `cc-academia` plugin (`literature-review` skill in Codex, `/cc-academia:literature-review` in Claude Code) |
| `reviewer-discovery/` | Confidential submission-to-reviewer matching data for the public `cc-academia` plugin (`reviewer-discovery` skill in Codex, `/cc-academia:reviewer-discovery` in Claude Code) |
| `cc-lab/` | PTY + claude-tap experiment harness for observing Claude Code behavior (see `cc-lab/PLAN.md`) |
| `cc-docx/` | Word ↔ Markdown round-trip harness — iterate in markdown, deliver .docx, PDF on demand (`$docx` / `/docx`) |

Codex may start either here or in a child project. Always read the target
child's `AGENTS.md`; Claude Code reaches the same contract through that child's
`CLAUDE.md`. Workflow implementations may live in a public plugin rather than
this data repository, so resolve them from the installed package and never from
a developer-specific absolute path. Native Claude and Codex manifests are
independent: install only the host and plugin variant you use.
