# manuscript-review — papers under review

The workflow ships in the public **cc-academia** plugin. This workspace does not
assume where the plugin is installed.

What remains here is material and data:

| Path | What it is |
|------|------------|
| `ongoing/` | papers currently under review |
| `archived/` | finished reviews |
| `critiques-library/` | reusable critique angles |
| `style/` | reviewer voice profile |

## Using it

| Host | Invocation |
|------|------------|
| Claude Code only | Install `cc-academia`, then run `/cc-academia:manuscript-review <pdf>` |
| Codex only | Install `cc-academia`, then invoke the `manuscript-review` skill with `<pdf>` |

The package contains independent native manifests for both hosts; neither
installation requires the other host.

The plugin finds `ongoing/` by walking up from wherever you are; nothing needs
configuring.

Reviewer prompt templates (`critiques-template.md`, `reviewer-voice.md` and the
rest) now ship as plugin defaults under `configs/templates/`; keep only your own
overrides here.
