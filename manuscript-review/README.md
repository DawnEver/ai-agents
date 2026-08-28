# manuscript-review — papers under review

The workflow moved to the **cc-academia** plugin:

```
Sync/claude/cc-market/cc-academia/
```

What remains here is material and data:

| Path | What it is |
|------|------------|
| `ongoing/` | papers currently under review |
| `archived/` | finished reviews |
| `critiques-library/` | reusable critique angles |
| `style/` | reviewer voice profile |
| `paper_pdf_ingest/` | the upstream ingest package checkout |

## Using it

```
/cc-academia:manuscript-review <pdf>
```

Set `ACADEMIA_DATA_ROOT` to this repository in `~/.claude/settings.json` so the
plugin finds `ongoing/`.

Reviewer prompt templates (`critiques-template.md`, `reviewer-voice.md` and the
rest) now ship as plugin defaults under `configs/templates/`; keep only your own
overrides here.
