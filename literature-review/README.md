# literature-review — workspaces

The code and the skill workflow moved to the **cc-academia** plugin:

```
Sync/claude/cc-market/cc-academia/
```

What remains here is data and personal configuration:

| Path | What it is |
|------|------------|
| `ongoing/` | topics under review — briefs, candidates, PDFs, reading cards |
| `archived/` | finished reviews |
| `.env` | API keys for this machine |
| `.claude/memory/` | engineering notes from building the pipeline |

## Using it

```
/cc-academia:literature-review <topic>
```

The plugin finds this directory by walking up from wherever you are, so nothing
needs configuring. `ACADEMIA_DATA_ROOT` overrides that if you keep research data
somewhere else.

## Personal overrides

Custom lenses or config live under a directory of your choosing, named by
`ACADEMIA_LENS_DIR` / `ACADEMIA_CONFIG_DIR`. Anything absent falls back to the
plugin defaults. That is an override relationship, not a fork — do not copy the
whole default set here to change one value.
