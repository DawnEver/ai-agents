# Data directories and Claude Code permissions

Every project's data directory (`ongoing/`, `archived/`, `workspace/`, …) is a
link into a synced data root outside the repository. Where that root lives
differs per workstation and per OS (macOS, Windows); the repository only ever
sees the link.

Claude Code checks permissions against the **resolved** path, not the link. A
permission glob written against the repository path (`*/<project>/ongoing/**`)
therefore never matches, on any workstation.

## Rule

- Access to data directories is decided by resolving the project's own data
  links at runtime, on the machine where the session runs — never by a path
  written into the repository.
- Nothing committed may contain an absolute path, drive letter, home directory
  or path-separator assumption for the data root.
- Do not add per-project `ongoing/` or `archived/` permission globs to a
  project's `.claude/settings.json`; they cannot match and they drift.

## Mechanism

`node .claude/hooks/allow-data-links.js` (from the repository root) resolves
every project's data links on the current workstation and writes them into that
project's git-ignored `.claude/settings.local.json`. Run it once per
workstation, and again after adding a project or a link. `--check` shows what it
would write.

If an agent is prompted for a path under a data link, the mechanism above is
missing or broken: say so and point here. Agents do not edit permission
settings or permission hooks themselves; the user installs or changes them.
