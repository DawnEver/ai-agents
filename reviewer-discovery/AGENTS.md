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
