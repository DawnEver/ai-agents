# AI-Post

Generate platform-adapted social media content from GitHub repositories. Clones repos locally for deep code exploration, researches market landscape, then spawns platform-specific agents to generate articles for 小红书, 微信公众号, 知乎, and Twitter/X.

## Pipeline

```
/post-new <github-url> [platform]
  → clone → explore + market research (parallel)
  → analysis → brief gate (angles + titles, user confirms)
  → parallel writer agents → image manifest
  → user review → 三方会审 (takeover fan-out + sharp-review merge engine) → final confirm → generate images
/post-publish <platform> → clipboard + browser (separate cmd)
/post-archive <slug> → archive + style update (separate cmd)
```

## Dependencies

- [takeover](https://github.com/anthropics/claude-code) (cc-market plugin) — multi-model fan-out via the `call_model` MCP tool. post-review calls each reviewer identity's models (Opus + DeepSeek + Codex) directly.
- [sharp-review](https://github.com/anthropics/claude-code) (cc-market plugin) — provides `merge-findings.js`: dedup + confidence tagging over the raw reviewer findings (no memory write). post-review owns its own persistence.

## Shared Reference Files

Platform rules are centralized in `templates/_platform-registry.md` (metadata: aspect ratios, char limits, agent mapping) and `templates/_writing-craft.md` (universal writing techniques: anti-AI, connectives, rhythm). These are the single source of truth — all pipeline steps, agents, and templates reference them instead of copying rules.

## Prerequisites

- [Codex CLI](https://github.com/openai/codex) v0.124.0+ with `codex login` (for image generation). The `takeover-image` agent spawns `codex exec --full-auto` directly to trigger Codex's built-in `imagegen` skill — no third-party plugin required.

## Commands

| Command | Description |
|---------|-------------|
| `/post-new <url>` | Full pipeline — clone through final confirmation + image generation |
| `/post-publish <platform>` | Export for publishing (clipboard + guidance) |
| `/post-archive <slug>` | Archive completed article, update style profile |
| `/post-review <slug>` | 三方会审 quality review |

## Acknowledgments

- [auto-claude-writing-agent-pub](https://github.com/MapleShaw/auto-claude-writing-agent-pub) by MapleShaw — original project architecture and inspiration.
- [Codex CLI](https://github.com/openai/codex) — its built-in `imagegen` skill (gpt-image-2) powers the `takeover-image` agent, which spawns `codex exec` directly with no third-party plugin.
- [codex-image-in-cc](https://github.com/KingGyuSuh/codex-image-in-cc) by KingGyuSuh — historical inspiration for bridging Codex's `imagegen` into Claude Code (no longer a dependency).
