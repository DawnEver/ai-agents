# literature-review — workspaces

The code and skill workflow ship in the public **cc-academia** plugin. This
workspace does not assume where the plugin is installed.

What remains here is data and personal configuration:

| Path | What it is |
|------|------------|
| `ongoing/` | topics under review — briefs, candidates, PDFs, reading cards |
| `archived/` | finished reviews |
| `.env` | API keys for this machine |
| `.claude/memory/` | engineering notes from building the pipeline |

## Using it

| Host | Invocation |
|------|------------|
| Claude Code only | Install `cc-academia`, then run `/cc-academia:literature-review <topic>` |
| Codex only | Install `cc-academia`, then invoke the `literature-review` skill with `<topic>` |

The package contains independent native manifests for both hosts; neither
installation requires the other host.

The plugin finds this directory by walking up from wherever you are, so nothing
needs configuring. `ACADEMIA_DATA_ROOT` overrides that if you keep research data
somewhere else.

## Personal overrides

Custom lenses or config live under a directory of your choosing, named by
`ACADEMIA_LENS_DIR` / `ACADEMIA_CONFIG_DIR`. Anything absent falls back to the
plugin defaults. That is an override relationship, not a fork — do not copy the
whole default set here to change one value.
