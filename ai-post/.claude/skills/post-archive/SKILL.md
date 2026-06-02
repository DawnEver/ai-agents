---
name: post-archive
description: Archive a finalized article and accumulate personal style fingerprints — moves to archived/YYMMDD/, updates style/profile.md
argument-hint: <slug>
allowed-tools: "Read,Write,Bash,Glob"
---

# /post-archive — Archive & Style Accumulation

Archive a completed article slug. Moves the entire `ongoing/<slug>/` to a frozen archive at `archived/YYMMDD/<slug>/`, extracts style fingerprints, and updates `style/profile.md`. No editing — the article text is final.

## Workflow

### Step 1: Identify the Slug

If `slug` is provided:
1. Verify `ongoing/<slug>/` exists.
2. Verify `3-final/` exists and contains at least one file — if empty or missing, abort: "No review-passed articles found. Run `/post-review <slug>` first."
3. For every platform file in `2-draft/`, a corresponding file must exist in `3-final/`. If any draft lacks a final, abort: "Not all platforms have passed review. Missing from 3-final/: <list>. Run `/post-review <slug>` first." If a platform was intentionally dropped, delete its draft from `2-draft/` first.

Never archive incomplete work — unreviewed drafts must not be frozen.

If not provided:
1. List slugs by scanning `ongoing/` directories with files in `3-final/`
2. Present a numbered list: "Ready to archive — which one?"
3. Read the user's choice

If no slugs found: "No articles ready for archive. Run `/post-new <url>` first."

### Step 2: Verify Articles are Final

Present a summary of what will be archived:

```
📦 准备归档

**项目**：<slug>
**平台**：
  - 小红书：<char_count> chars
  - 微信公众号：<char_count> chars
  - 知乎：<char_count> chars
  - Twitter/X：<tweet_count> tweets

归档到 archived/<YYMMDD>/<slug>/？
```

### Step 3: Move to Archive

Instead of deleting working files, move the entire slug directory to a date-prefixed archive:

```bash
mkdir -p "archived/$(date +%y%m%d)" && mv "ongoing/<slug>" "archived/$(date +%y%m%d)/<slug>"
```

The archive path is now `archived/YYMMDD/<slug>/` (e.g. `archived/260602/dawnever--cc-market/`). The internal structure (`1-research/`, `2-draft/`, `3-final/`) is preserved as a frozen snapshot.

### Step 4: Write Text-Only Archive to style/published/

For each platform with a file in `archived/YYMMDD/<slug>/3-final/`:

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

### Step 5: Extract Style Fingerprints

From each platform's article body, extract:

- **Opening**: The first 1-2 substantive sentences. Skip frontmatter, image references, and heading lines — find the first actual prose the reader encounters.
- **Closing**: The last 1-2 substantive sentences before any signature, hashtags, or CTA lines.
- **Voice markers**: 2-3 distinctive phrases, transitions, or framing patterns that are characteristic. Look for specific metaphors, unique transition phrases ("说实话", "一个冷知识"), recurring syntactic patterns. Avoid generic phrases like "GitHub:" or hashtags.

Each fingerprint must be a direct quote, trimmed to reasonable length.

### Step 6: Update `style/profile.md`

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

### Step 7: Clean Up Cached Repo

```bash
rm -rf repos/<slug>
```

The cached clone is no longer needed. The frozen archive at `archived/YYMMDD/<slug>/` is never deleted.

### Step 8: Offer Postmortem (Optional)

> Want to score each article's AI味 and reader reception? This helps calibrate future generation.

If yes, create `archived/YYMMDD/<slug>/postmortem.md`:
```markdown
# Postmortem — <slug>

## Per-Platform Scores
- 小红书: AI味 🟢/🟡/🔴 | 读者反馈: <notes>
- 微信公众号: AI味 🟢/🟡/🔴 | 读者反馈: <notes>
- 知乎: AI味 🟢/🟡/🔴 | 读者反馈: <notes>
- Twitter/X: AI味 🟢/🟡/🔴 | 读者反馈: <notes>

## Lessons
- <what worked, what didn't, what to try next time>
```

### Step 9: Report

```
📦 已归档 — archived/<YYMMDD>/<slug>/

🎨 风格积累：
  - 开头: <added or "已存在，跳过">
  - 结尾: <added or "已存在，跳过">
  - 语气标记: <N added, M skipped>

🗑️ 已清理：repos/<slug>

📊 Style profile — <N> articles accumulated.
```

## Hard Rule

Never modify files under `archived/YYMMDD/<slug>/` except for `postmortem.md`. The frozen snapshot is the source of truth.
