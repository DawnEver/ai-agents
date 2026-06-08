# AI-Post

Generate platform-adapted social media content from GitHub repositories. Clones repos locally for deep code exploration, researches market landscape, then spawns platform-specific agents to generate articles for 小红书, 微信公众号, 知乎, and Twitter/X.

## Pipeline

```
/post-new <github-url> [platform]
  → clone → explore → market research → analysis
  → brief gate (angles + titles, user confirms)
  → image manifest + user-confirmed gen via takeover-image (covers → content)
  → parallel writer agents → user review → 三方会审 → publish → archive
```

## Prerequisites

- [Codex CLI](https://github.com/openai/codex) v0.124.0+ with `codex login` (for image generation)
- Install the image plugin: `claude plugin install codex-image@codex-image-in-cc --scope project`

## Commands

| Command | Description |
|---------|-------------|
| `/post-new <url>` | Full pipeline — clone through archive |
| `/post-publish <platform>` | Export for publishing (clipboard + guidance) |
| `/post-archive <slug>` | Archive completed article, update style profile |
| `/post-regenerate <slug> <platform>` | Redo one platform from existing analysis |
| `/post-review <slug>` | 三方会审 quality review |

## Acknowledgments

- [auto-claude-writing-agent-pub](https://github.com/MapleShaw/auto-claude-writing-agent-pub) by MapleShaw — original project architecture and inspiration.
- [codex-image-in-cc](https://github.com/KingGyuSuh/codex-image-in-cc) by KingGyuSuh — bridges Codex CLI's built-in `imagegen` skill (gpt-image-2) into Claude Code. Powers the `takeover-image` agent.
