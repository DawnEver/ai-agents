# literature-review — workspaces

The code and the skill workflow moved to the **cc-academia** plugin:

```
Sync/claude/cc-market/cc-academia/
```

What remains here is data and personal configuration:

| Path | What it is |
|------|------------|
| `workspaces/` | topic workspaces — briefs, candidates, PDFs, reading cards |
| `.env` | API keys for this machine |
| `.claude/memory/` | engineering notes from building the pipeline |

## Using it

```
/cc-academia:literature-review <topic>
```

Point the plugin at these workspaces by setting, once:

```
ACADEMIA_DATA_ROOT = <this repo>
```

in `~/.claude/settings.json` under `env`. The plugin then reads
`literature-review/<slug>/` from here.

## Personal overrides

Custom lenses or config live under a directory of your choosing, named by
`ACADEMIA_LENS_DIR` / `ACADEMIA_CONFIG_DIR`. Anything absent falls back to the
plugin defaults. That is an override relationship, not a fork — do not copy the
whole default set here to change one value.
