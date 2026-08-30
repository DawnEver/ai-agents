# reviewer-discovery (data only)

The executable workflow ships in the public `cc-academia` plugin. Read the
plugin's `AGENTS.md` for principles and `skills/reviewer-discovery/` for the
step-by-step playbook; never depend on the plugin's location on one developer's
machine.

Submissions are confidential and unpublished. An agent may read only
`1-manuscript/sanitized.json`, never `ongoing/*/0-raw.pdf`. Only the CLI `init`
command may ingest the raw PDF. Search requests contain derived keywords, not
the abstract or manuscript body.

Work in `ongoing/`; move completed work to `archived/` only when explicitly
asked. Do not publish, email candidates, open a browser, or invoke a paid model
without explicit confirmation.

This data workspace must work with either host independently:

- Codex discovers these instructions from `AGENTS.md` and runs the installed
  `reviewer-discovery` skill.
- Claude Code reads `CLAUDE.md`, which delegates to this same contract, and runs
  `/cc-academia:reviewer-discovery`.

Do not add machine-specific absolute paths or require configuration files from
the other host.

## Working across machines

`ongoing/` and `archived/` are symlinks into synced storage; `./scripts/link-agent-data.sh`
creates them from a fresh clone. The SQLite store is *not* synced — WAL mode and
a file-level syncer corrupt each other — so what travels instead is the five
things it cannot re-derive: invitations and their outcomes, verified ranks,
addresses, corrected affiliations and doctorate years.

`ACADEMIA_FACTS_SYNC=1` (set for this directory in `.claude/settings.json`) turns
that export on; the folder follows the data root, so it lands in
`cc-academia-facts/`, itself a symlink into the same synced storage. Every
command merges the folder in on the way in and publishes on the way out, one
subdirectory per device.

These files hold real people's addresses and employment. Turning the export on
is a deliberate act, which is why it is off by default and why nothing discovers
a cloud folder on its own.
