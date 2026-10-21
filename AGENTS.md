# agents workspace

This repository contains independent agent projects. Before changing a child project, read and follow that project's `AGENTS.md`; it is the authoritative project contract. Root `.agents/skills/` entries are thin workspace launchers that point to each child's canonical workflow; resolve their commands and linked paths from the named child directory.

| Directory | Purpose |
| --- | --- |
| `ai-post/` | Multi-platform article generation, review, publishing, and archiving |
| `cc-docx/` | Word ↔ Markdown round-trip and delivery tooling |
| `cc-slides/` | Template-faithful PowerPoint decks: spec → build → lint → PowerPoint preview |
| `cc-uon/` | UoN admin chores: expense claims, PGR supervision records |
| `cc-lab/` | Claude Code PTY and trace experiment harness; not a Codex behavior harness |
| `literature-review/` | Systematic literature-review pipeline |
| `manuscript-review/` | Academic manuscript-review pipeline |
| `reply-email/` | Drafting and archiving email replies |
| `reviewer-discovery/` | Matching submissions to candidate reviewers |

Do not run outward-facing publishing, email, browser, paid-model, or destructive archive actions without explicit user confirmation. Prefer each project's lightweight tests when validating cross-project changes.

## Change the tool at its source

The executable tooling ships as a plugin; these projects are data and workflow.
A behaviour fix is therefore a change to the plugin's **source checkout**, never
to the copy the host installed under `~/.claude/plugins/` or `~/.codex/`. That
copy is a cache: an edit there is overwritten at the next update, invisible on
every other machine, and missing from the history that explains it.

Discover the source — a checkout the user has named, a repository whose `origin`
matches the installed copy's remote, or a sibling checkout of it. **If none
resolves, ask the user for the path**; do not fall back to editing the installed
copy and do not guess. Never commit an absolute path to anyone's checkout: these
projects sync across machines and hosts, where such a path is right on exactly
one of them.

Run the tests and commit in the source checkout. If the running session needs
the change immediately, re-sync the installed copy from the source rather than
editing it in place.
