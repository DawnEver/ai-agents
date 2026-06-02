# AI-Post

Generate platform-adapted social media content from GitHub repositories. Clones repos locally for deep code exploration, researches market landscape, then spawns platform-specific agents to generate articles for 小红书, 微信公众号, 知乎, and Twitter/X.

## Architecture

```
/post-new (唯一入口，管线主体)
  ├── 01-clone → 02-explore → 03-market-research
  ├── 04-analysis (folds in market research)
  ├── ⭐ 05-brief-gate (选题确认: angles + titles, 多轮迭代)
  ├── 06-images → 07-spawn (并行 agents)
  ├── ⭐ 08-user-review (强制用户阅读初稿)
  ├── 09-review → 10-summary
  └── 下游工具:
      ├── /post-publish    (发布出口: 剪贴板导出 + 平台发布指引, 不改文本)
      ├── /post-archive    (归档: 移动到 archived/YYMMDD/, 更新 style/profile.md)
      └── /post-regenerate (独立重做, 不经过 clone)
```

## Commands

| Command | Description |
|---------|-------------|
| `/post-new <github-url> [platform]` | 主线 — clone → explore → market research → gate → spawn → review → publish |
| `/post-publish <platform> [slug]` | 发布出口 — image verification + clipboard export + platform publishing guidance |
| `/post-archive <slug>` | 归档 — move to `archived/YYMMDD/`, update style/profile.md, optional postmortem |
| `/post-regenerate <slug> <platform>` | Redo one platform's article from existing analysis (no re-clone) |
| `/post-review <slug> [platform]` | 三方会审 — 2-reviewer 3-model fanout quality review |


## Pipeline Flow

```
/post-new <repo>
  → clone + deep explore
  → market research (WebSearch: similar repos, trending, content gaps)
  → write repo-analysis.md (folds in market research)
  → ⭐ BRIEF REVIEW GATE: 选题确认 (angles + titles, iterate until user approves)
  → user confirms angles, selects titles (multi-round discussion OK)
  → write images.md (image manifest: real screenshots + AI prompts, cross-platform reuse)
  → spawn writers in parallel (创意排水 → draft → 三遍审校)
    writers use markdown image refs ![alt](../1-research/images/<file>) from images.md
  → ⭐ USER DRAFT REVIEW: mandatory read-through before review
  → user reads drafts, requests changes (iterate until approved)
  → 三方会审 (3-model fanout per identity)
  → fix (auto-offer /post-regenerate on ❌)
  → copy passed drafts to 3-final/
  → /post-publish (图片校验 → 剪贴板导出 + 平台发布指引)
  → /post-archive (移动到 archived/YYMMDD/ → 更新 style/profile.md)
```

**Core principle**: Market research before analysis. Research and brief ALWAYS come before writing. Never skip the user confirmation gates.

post-new uses **progressive disclosure** — SKILL.md is the map, each step's sub-file is the detailed playbook:
`.claude/skills/post-new/{01-clone,02-explore,03-market-research,04-analysis,05-brief-gate,06-images,07-spawn,08-user-review,09-review,10-summary}.md`

## Directory Layout

```
.claude/
  skills/           — skill definitions (slash commands)
    post-new/       — main pipeline: progressive disclosure SKILL.md + 01-10 sub-files
    post-publish/   — platform publishing: image gate + clipboard + browser
    post-archive/   — archiving: move to archived/YYMMDD/, update style/profile.md
    post-review/    — 三方会审: 3-model fanout quality review
    post-regenerate/— redo one platform from existing analysis
  agents/           — platform-specific sub-agents for parallel generation
  settings.json     — tool permissions and model config
templates/          — platform-specific generation instructions (single source of truth)
templates/审校checklist.md  — 3-pass review checklist template
ongoing/            — articles currently in progress (gitignored)
  <slug>/
    1-research/
      repo-exploration.md  — step 02: deep code exploration notes
      market-research.md   — step 03: similar repos, trending, content gap
      repo-analysis.md     — step 04: consolidated analysis + article angles
      images.md            — step 06: image manifest
      images/              — step 06: image files (screenshots, AI-generated)
    2-draft/
      xiaohongshu.md       — step 07: generated articles
      wechat.md
      zhihu.md
      twitter.md
    3-final/
      xiaohongshu.md       — step 10: review-passed, ready-to-publish
      wechat.md
      zhihu.md
      twitter.md
archived/YYMMDD/<slug>/ — completed articles, frozen snapshot (gitignored)
  postmortem.md         — optional: per-platform AI味 scores + notes
repos/              — cached git clones (gitignored)
style/published/    — text-only published archive, organized by platform
style/profile.md    — auto-accumulated personal style (generated from published articles)
config/             — user preferences and platform accounts
```

## Sub-Agents

Each platform has a thin agent that loads the template (single source of truth) and generates:

| Agent | Platform | Key Rules (from template) |
|-------|----------|--------------------------|
| `xiaohongshu-writer` | 小红书 | 800-1000 chars, 8-15 emoji, no links, --ar 3:4 |
| `wechat-writer` | 微信公众号 | 2000-5000 chars, 2-3+ code blocks, 三遍审校 |
| `zhihu-writer` | 知乎 | 1500-4000 chars, comparison table REQUIRED, no hype words |
| `twitter-writer` | Twitter/X | 4-6 tweets, each <280 chars, EN+CN bilingual |

Chinese platform agents (xiaohongshu/wechat/zhihu) are written in Chinese and execute 创意排水 + 三遍审校 as part of their generation workflow.

## Platform Quick Reference

| Platform | Length | Emoji | Code | Language | Cover Image | Signature |
|----------|--------|-------|------|----------|-------------|-----------|
| 小红书 | 800-1000 chars | Heavy (8-15) | None | 中文 | 3:4, hook text on image, separately designed | Emoji bullets + pain-point hook |
| 微信公众号 | 2000-5000 chars | Moderate (3-8) | 2-3+ blocks | 中文 | 16:9, project name hero, title-safe zone | Deep tutorial with install steps |
| 知乎 | 1500-4000 chars | Minimal (0-3) | Optional | 中文 | 16:9, professional/academic, project name focal | Comparison table + honest limits |
| Twitter/X | 280/tweet × 4-6 | 1-2/tweet | None | EN+CN | N/A (no cover needed) | Thread format, one idea per tweet |

## Quality Standards — 三方会审 🔄 审查中

Every generated article goes through `/post-review` (三方会审) before publishing.
Two reviewer identities, each independently run by 3 models. No cross-contamination, verdicts consolidated by orchestrator:

| 身份 | 工具（×3并行）| 审什么 |
|------|--------------|--------|
| A 读者代理人 | Claude Sonnet + DeepSeek + Codex | AI味/开头钩子/微幽默/情感共鸣 |
| B 技术核查员 | Claude Sonnet + DeepSeek + Codex | 代码正确性/技术事实/安装步骤 |

> **审查中**：3-model fanout per identity 的性价比待验证。全平台一次 review 会产生 18+ agent 调用。当前保留此设计，后续可能简化为默认 2-model（Claude + DeepSeek），Codex 仅 `--full-review` 触发。

AI味 grades: 🟢 人味足 | 🟡 轻微AI腔 | 🔴 明显AI腔 (must rewrite before publish)

Ruling: ✅ 可发布 / ⚠️ 有条件通过 / ❌ 不可发布

Banned phrases (all CN platforms): 这篇文章 / 本文将 / 总的来说 / 值得注意的是 / 综上所述 / 显著提升 / 充分利用  
Additional banned for 小红书: 随着XX发展 / 今天来分享一个  
Additional banned for 知乎: 惊艳 / 震撼 / 逆天 / 神器 / 通过对比可以发现 / 需要承认的是 / 解决的是一个边界很清晰的问题  
Banned formats (小红书): structured emoji-bullet feature catalogs (`🛠️ 核心功能：` + emoji:label per feature) — weave features into conversation  
Banned section headers (知乎): 项目概览 / 问题背景 / 上手体验 / 适用场景与局限 / 总结 — use conversational headers or skip entirely

## Notes

- Templates are the SINGLE SOURCE OF TRUTH for generation rules. Agents are thin wrappers that load templates.
- Agents run in PARALLEL via post-new for efficient multi-platform generation.
- `repos/`, `ongoing/`, and `archived/` are gitignored. `style/` and `config/` are committed.
- Publishing is manual copy-paste. API integration planned for future.

## Personal Style — Auto-Accumulating

No manual curation. Personal style accumulates as a byproduct of publishing.

**How it works:**
1. `/post-archive` archives a slug → moves `ongoing/<slug>/` to `archived/YYMMDD/<slug>/`
2. Extracts style fingerprints (opening patterns, voice markers, closings) from final articles
3. Incrementally updates `style/profile.md` — each archive enriches the profile
4. Writer agents read `style/profile.md` before generating → personal voice compounds over time

**What `style/profile.md` contains** (machine-usable, example-driven):
```markdown
---
updated: YYYY-MM-DD
articles: N
---

## Openings I Use
### 小红书
- "<actual opening from published article>"
### 微信公众号
- "<actual opening>"

## Closings I Use
### 小红书
- "<actual closing pattern>"

## Voice Markers
- <recurring phrases, transitions, framing patterns>
```

Writer agents use this as "write like this person" examples — not statistical analysis, but concrete excerpts to match tone against.
