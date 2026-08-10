# AI-Post

Generate platform-adapted social media content from a **source** — a GitHub repo, a local codebase, or a research report. Explores code (or mines the report), researches the market landscape, then spawns platform-specific agents to generate articles for 小红书, 微信公众号, 知乎, and Twitter/X.

## Pipeline

Claude Code uses `/skill`; Codex uses `$skill` (natural-language invocation is also supported):

```
/post-new | $post-new <github-url|local-path> [platform]
  → resolve source → ingest (explore code / mine report) + market research
  → analysis → brief gate (angles + titles, user confirms)
  → parallel writer agents → image manifest
  → user review → 三方会审 (fabric MCP fan-out + sharp-review merge engine) → final confirm → generate images
/post-publish | $post-publish <platform> → clipboard + browser (separate cmd)
/post-archive | $post-archive <slug> → archive + style update (separate cmd)
```

## Dependencies

- [fabric](https://github.com/anthropics/claude-code) (cc-market plugin) — multi-model fan-out via the `mcp__plugin_fabric_fabric__call` MCP tool. post-review calls each reviewer identity's models directly (formerly takeover/call_model, now merged into fabric).
- [sharp-review](https://github.com/anthropics/claude-code) (cc-market plugin) — provides `merge-findings.js`: dedup + confidence tagging over the raw reviewer findings (no memory write). post-review owns its own persistence.

## Shared Reference Files

Platform rules are centralized in `templates/_platform-registry.md` (metadata: aspect ratios, char limits, agent mapping) and `templates/_writing-craft.md` (universal writing techniques: anti-AI, connectives, rhythm). These are the single source of truth — all pipeline steps, agents, and templates reference them instead of copying rules.

## Prerequisites

- **When hosted by Claude Code:** [Codex CLI](https://github.com/openai/codex) v0.124.0+
  with `codex login`; the `takeover-image` agent uses it for image generation.
- **When hosted by Codex:** no nested Codex CLI is required; the workflow calls Codex's built-in
  `imagegen` tool directly.

## Commands

| Claude Code | Codex | Description |
|---|---|---|
| `/post-new <source\|slug> [platform]` | `$post-new <source\|slug> [platform]` | Full pipeline or resume |
| `/post-publish <platform>` | `$post-publish <platform>` | Export for publishing |
| `/post-archive <slug>` | `$post-archive <slug>` | Archive and update style profile |
| `/post-review <slug>` | `$post-review <slug>` | 三方会审 quality review |

## Acknowledgments

- [auto-claude-writing-agent-pub](https://github.com/MapleShaw/auto-claude-writing-agent-pub) by MapleShaw — original project architecture and inspiration.
- [Codex](https://github.com/openai/codex) — its built-in `imagegen` capability is used directly
  on Codex, and through the `takeover-image` bridge when Claude Code is the host.
- [codex-image-in-cc](https://github.com/KingGyuSuh/codex-image-in-cc) by KingGyuSuh — historical inspiration for bridging Codex's `imagegen` into Claude Code (no longer a dependency).
