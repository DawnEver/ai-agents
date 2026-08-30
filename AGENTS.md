# agents workspace

This repository contains independent agent projects. Before changing a child project, read and follow that project's `AGENTS.md`; it is the authoritative project contract. Root `.agents/skills/` entries are thin workspace launchers that point to each child's canonical workflow; resolve their commands and linked paths from the named child directory.

| Directory | Purpose |
| --- | --- |
| `ai-post/` | Multi-platform article generation, review, publishing, and archiving |
| `cc-docx/` | Word ↔ Markdown round-trip and delivery tooling |
| `cc-lab/` | Claude Code PTY and trace experiment harness; not a Codex behavior harness |
| `literature-review/` | Systematic literature-review pipeline |
| `manuscript-review/` | Academic manuscript-review pipeline |
| `reply-email/` | Drafting and archiving email replies |
| `reviewer-discovery/` | Matching submissions to candidate reviewers |

Do not run outward-facing publishing, email, browser, paid-model, or destructive archive actions without explicit user confirmation. Prefer each project's lightweight tests when validating cross-project changes.
