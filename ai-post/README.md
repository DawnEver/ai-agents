# AI-Post

Generate platform-adapted social media content from GitHub repositories. Clones repos locally for deep code exploration, researches market landscape, then spawns platform-specific agents to generate articles for 小红书, 微信公众号, 知乎, and Twitter/X.

## Pipeline

```
/post-new <github-url> [platform]
  → clone → explore + market research (parallel)
  → analysis → brief gate (angles + titles, user confirms)
  → parallel writer agents → image manifest
  → user review → 三方会审 (powered by sharp-review engine) → final confirm → generate images
/post-publish <platform> → clipboard + browser (separate cmd)
/post-archive <slug> → archive + style update (separate cmd)
```

## Dependencies

- [sharp-review](https://github.com/anthropics/claude-code) (cc-market plugin) — generalized multi-model review engine. post-review configures it for content review with custom reviewer identities and finding schemas.

## Shared Reference Files

Platform rules are centralized in `templates/_platform-registry.md` (metadata: aspect ratios, char limits, agent mapping) and `templates/_writing-craft.md` (universal writing techniques: anti-AI, connectives, rhythm). These are the single source of truth — all pipeline steps, agents, and templates reference them instead of copying rules.

## Prerequisites

- [Codex CLI](https://github.com/openai/codex) v0.124.0+ with `codex login` (for image generation)
- Install the Codex image plugin (`codex-image-in-cc`) — see plugin repo for install instructions

## Commands

| Command | Description |
|---------|-------------|
| `/post-new <url>` | Full pipeline — clone through final confirmation + image generation |
| `/post-publish <platform>` | Export for publishing (clipboard + guidance) |
| `/post-archive <slug>` | Archive completed article, update style profile |
| `/post-review <slug>` | 三方会审 quality review |

## Acknowledgments

- [auto-claude-writing-agent-pub](https://github.com/MapleShaw/auto-claude-writing-agent-pub) by MapleShaw — original project architecture and inspiration.
- [codex-image-in-cc](https://github.com/KingGyuSuh/codex-image-in-cc) by KingGyuSuh — bridges Codex CLI's built-in `imagegen` skill (gpt-image-2) into Claude Code. Powers the `takeover-image` agent.
