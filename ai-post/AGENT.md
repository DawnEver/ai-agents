# AI-Post

Generate platform-adapted social media content from GitHub repositories. Clone → explore → market research → spawn platform agents → review → publish.

## Architecture

```
/post-new (pipeline entry) → /post-review (三方会审) → /post-publish → /post-archive
```

All commands are skills under `.claude/skills/<name>/`. Each uses progressive disclosure: `SKILL.md` is the map, `0X-*.md` sub-files are the playbook.

## Directory Layout

```
.claude/
  skills/           — slash command definitions
  agents/           — platform writer sub-agents (thin wrappers)
    _writer-base.md — shared generation workflow for all platform writers
templates/          — generation rules (single source of truth)
  _writing-craft.md — universal writing techniques (anti-AI, connectives, rhythm)
  _platform-registry.md — single source of truth for platform metadata
ongoing/<slug>/     — in-progress (gitignored)
  1-research/       — repo-exploration, market-research, repo-analysis, brief
  2-draft/vN/       — versioned drafts (v1=AI gen, v2=user edit, v3+=review fixes)
  images/           — generated images
archived/YYMMDD/<slug>/ — published articles, frozen snapshot (gitignored)
style/profile.md    — auto-accumulated personal style
repos/              — cached clones (gitignored)
```

## Platform Agents

| Agent | Platform |
|-------|----------|
| `xiaohongshu-writer` | 小红书 |
| `wechat-writer` | 微信公众号 |
| `zhihu-writer` | 知乎 |
| `twitter-writer` | Twitter/X |
| `takeover-image` | Image generation via Codex |

## Key Principles

- **Templates are the single source of truth** for generation rules. Agents are thin wrappers that load templates.
- **Shared reference files (`_` prefix) are the single source of truth**. Templates and agents reference them — never copy rules across files.
- **Research before writing**: market research → analysis → brief gate → spawn. Never skip user confirmation gates.
- **三方会审 is mandatory**: every article passes review before publish. Verdicts persist in `2-draft/vN/review-verdict.md`.
- **repos/, ongoing/, archived/ are gitignored**. style/ and config/ are committed.
- **Version chain**: v1 (AI baseline) → v2 (user edits) → v3+ (review rounds). Missing files inherit from previous version. The latest vN IS the final article.
