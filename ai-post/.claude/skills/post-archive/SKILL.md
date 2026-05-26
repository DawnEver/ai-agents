---
name: post-archive
description: Archive a finalized article and accumulate personal style fingerprints — writes to style/published/ and updates style/profile.md
argument-hint: <platform> [project-slug]
allowed-tools: "Read,Write,Glob"
---

# /post:archive — Archive & Style Accumulation

Archive a final published article to the personal style library. Extracts style fingerprints (openings, closings, voice markers) and incrementally updates `style/profile.md`. No editing — the article text is final.

## Supported Platforms

- `xiaohongshu` — 小红书
- `wechat` — 微信公众号
- `zhihu` — 知乎
- `twitter` — Twitter/X

## Workflow

### Step 1: Identify the Article

If `project-slug` is provided, load `articles/<slug>/<platform>.md`.

If not provided:
1. List recent projects by scanning `articles/` directories for existing article files
2. Present a numbered list: "Recent articles — which one to archive?"
3. Read the user's choice

If no articles exist yet: "No articles found. Run `/post:new <github-url>` first."

If the platform is not supported: "Supported platforms: xiaohongshu, wechat, zhihu, twitter."

### Step 2: Verify Article is Final

Read the article file.

Check if it has already been archived — scan `style/published/<platform>/` for files matching `*-<slug>.md`. If found, warn:
"⚠️ 已归档过此文章：`style/published/<platform>/<existing-file>`。覆盖归档？"

Present the article briefly for confirmation:
```
📦 准备归档

**平台**：<platform>
**项目**：<slug>
**标题**：<extracted title>
**字符数**：<count>

归档到 style/published/<platform>/<YYYY-MM-DD>-<slug>.md？
```

### Step 3: Create Archive File

Write `style/published/<platform>/<YYYY-MM-DD>-<slug>.md` with YAML frontmatter:

```yaml
---
platform: <platform>
slug: <slug>
published: YYYY-MM-DD
title: <first heading or first line of article>
---
```

Followed by the full article body with **image references stripped** — remove all `![alt](...)` lines. Style archives are text-only; images are transient working files.

### Step 4: Extract Style Fingerprints

From the article body, extract:

- **Opening**: The first 1-2 substantive sentences. Skip frontmatter, image references, and heading lines — find the first actual prose the reader encounters.
- **Closing**: The last 1-2 substantive sentences before any signature, hashtags, or CTA lines.
- **Voice markers**: 2-3 distinctive phrases, transitions, or framing patterns that are characteristic. Look for specific metaphors, unique transition phrases ("说实话", "一个冷知识"), recurring syntactic patterns. Avoid generic phrases like "GitHub:" or hashtags.

Each fingerprint must be a direct quote, trimmed to reasonable length.

### Step 5: Update `style/profile.md`

If `style/profile.md` does NOT exist, create it:

```markdown
---
updated: YYYY-MM-DD
articles: 1
---

## Openings I Use
### <platform>
- "<opening quote>"

## Closings I Use
### <platform>
- "<closing quote>"

## Voice Markers
- <marker quote>
- <marker quote>
```

If `style/profile.md` exists:
1. Read the current file
2. Increment `articles` count in YAML frontmatter, update `updated` date
3. For each fingerprint:
   - **Deduplicate**: if the new quote shares >50% content-word overlap with an existing entry, skip as duplicate
   - **Cap per platform per category**: keep max 3 openings and 3 closings per platform. If >3, keep the most distinctive ones (prefer longer, more specific quotes over shorter generic ones)
   - Voice Markers: keep max 8 total, remove least distinctive when over cap
4. Write updated file

### Step 6: Clean Up Working Files

After archiving, delete all working files for the slug — both the cloned repo and the articles directory:

```bash
rm -rf repos/<slug>
rm -rf articles/<slug>
```

Both are transient working space. The final text lives in `style/published/`, style fingerprints in `style/profile.md`.

If either directory does not exist, skip silently.

### Step 7: Report

```
📦 已归档 — style/published/<platform>/<YYYY-MM-DD>-<slug>.md

🎨 风格积累：
  - 开头: <added or "已存在，跳过">
  - 结尾: <added or "已存在，跳过">
  - 语气标记: <N added, M skipped>

🗑️ 已清理：repos/<slug>、articles/<slug>

📊 Style profile — <N> articles accumulated.
```
