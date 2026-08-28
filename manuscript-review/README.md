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

## Using it

```
/cc-academia:manuscript-review <pdf>
```

The plugin finds `ongoing/` by walking up from wherever you are; nothing needs
configuring.

Reviewer prompt templates (`critiques-template.md`, `reviewer-voice.md` and the
rest) now ship as plugin defaults under `configs/templates/`; keep only your own
overrides here.
