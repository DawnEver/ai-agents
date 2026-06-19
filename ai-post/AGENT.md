# AI-Post

Generate platform-adapted social media content from GitHub repositories. Clone → explore → market research → spawn platform agents → review → publish.

## Architecture

```
/post-new (pipeline entry) → /post-review (三方会审) → /post-publish → /post-archive
```

All commands are skills under `.claude/skills/<name>/` and use progressive disclosure: `SKILL.md` is the map, `0X-*.md` sub-files are the playbook.

## Directory Layout

```
.claude/
  skills/           — slash command definitions
  agents/           — platform writer sub-agents (thin wrappers)
    _writer-base.md — shared generation workflow for all platform writers
scripts/<skill>/    — executable helpers for skills (e.g. post-publish/export_article.py, char_count.py + requirements.txt)
templates/          — generation rules (single source of truth)
  _writing-craft.md — universal writing techniques (anti-AI, connectives, rhythm); sectioned with a top Section Index
  _platform-registry.md — single source of truth for platform metadata
ongoing/<slug>/     — in-progress (gitignored)
  1-research/       — repo-exploration, market-research, repo-analysis, brief
  2-draft/vN/       — versioned drafts (v1=AI gen, v2=user edit, v3+=review fixes)
  images/           — generated images
archived/YYMMDD/<slug>/ — published articles, frozen snapshot (gitignored)
style/
  profile.md        — auto-accumulated personal style (committed)
  published/<platform>/ — text-only style corpus profile.md accumulates from; post-archive Step 4 writes here (committed)
  private/          — persona identity (e.g. author-identity.md) (gitignored)
repos/<repo-slug>/  — cached clones, keyed by repo, shared across articles (gitignored)
```

> **Slug**: `<repo-slug>` = `owner--repo` keys the clone cache. `<slug>` (article-slug) keys `ongoing/`+`archived/` — defaults to `<repo-slug>`, but a second article from the same repo uses `<repo-slug>__<topic>` so the repo can yield multiple distinct articles without clobbering. See `post-new/SKILL.md` ## Slug.

## Platform Agents

**Writer Agents** — one per platform:

| Agent | Platform |
|-------|----------|
| `xiaohongshu-writer` | 小红书 |
| `wechat-writer` | 微信公众号 |
| `zhihu-writer` | 知乎 |
| `twitter-writer` | Twitter/X |

**Utility Agents** — no platform, support the pipeline:

| Agent | Role |
|-------|------|
| `takeover-image` | Image generation via Codex |

## Key Principles

- **Templates are the single source of truth** for generation rules. Agents are thin wrappers that load templates.
- **Shared reference files (`_` prefix) are the single source of truth**. Templates and agents reference them — never copy rules across files.
- **Research before writing**: market research → analysis → brief gate → spawn. Never skip user confirmation gates.
- **三方会审 is mandatory**: every article passes review before publish. Verdicts persist in `2-draft/vN/review-verdict.md`.
- **repos/, ongoing/, archived/, style/private/ are gitignored**. style/profile.md, style/published/, and config/ are committed.
- **Version chain**: v1 (AI baseline) → v2 (user edits) → v3+ (review rounds). Missing files inherit from previous version. The latest vN IS the final article.
