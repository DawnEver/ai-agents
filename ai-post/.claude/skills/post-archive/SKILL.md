---
name: post-archive
description: Archive a finalized article and accumulate personal style fingerprints — moves to archived/YYMMDD/, updates style/profile.md
argument-hint: <slug>
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

# /post-archive — Archive & Style Accumulation

Archive a completed article slug. Moves the entire `ongoing/<slug>/` to a frozen archive at `archived/YYMMDD/<slug>/`, extracts style fingerprints, and updates `style/profile.md`. No editing — the article text is final.

## Workflow

### Step 1: Identify the Slug

If `slug` is provided:
1. Verify `ongoing/<slug>/` exists.
2. Verify `2-draft/` exists and `brief.md` has `finalized: true` — if not, abort: "No finalized articles found. Complete review and step 10 final confirmation first."
3. Assemble the full version set by walking back through versions for each platform. Verify at least one platform file exists.

Never archive incomplete work — unreviewed drafts must not be frozen.

If not provided:
1. List slugs by scanning `ongoing/` directories where `brief.md` has `finalized: true`
2. Present a numbered list: "Ready to archive — which one?"
3. Read the user's choice

If no slugs found: "No articles ready for archive. Run `/post-new <url>` first."

### Step 2: Verify Articles are Final

Present a summary of what will be archived:

```
📦 准备归档

**项目**：<slug>
**版本链**：v1 → v2 → ... → v<N> (final)
**平台** (see `templates/_platform-registry.md`)：
  - 小红书：v<N> — <char_count> chars
  - 微信公众号：v<N> — <char_count> chars
  - 知乎：v<N> — <char_count> chars
  - Twitter/X：v<N> — <tweet_count> tweets

归档到 archived/<YYMMDD>/<slug>/？
```

### Step 3: Assemble Final & Move to Archive

First, assemble the final version set by walking the version chain for each platform and images.md. Then create a clean archive with only the final output:

```
archived/YYMMDD/<slug>/
  1-research/          ← preserved from ongoing (analysis, brief, market research)
  xiaohongshu.md       ← final assembled version
  wechat.md            ← final assembled version
  zhihu.md             ← final assembled version
  twitter.md           ← final assembled version
  images.md            ← final assembled version
  images/              ← preserved from ongoing (generated image files)
```

Archive structure is flat with `1-research/` for reference and the final articles at root level. The raw `2-draft/` chain is NOT preserved — only the assembled final output matters.

```bash
mkdir -p "archived/$(date +%y%m%d)/<slug>/1-research" "archived/$(date +%y%m%d)/<slug>/images"
# Copy research notes
cp -r "ongoing/<slug>/1-research/"* "archived/$(date +%y%m%d)/<slug>/1-research/"
# Copy assembled final articles (one per platform, walk version chain)
cp "<assembled final>" "archived/$(date +%y%m%d)/<slug>/<platform>.md"
# Copy only images referenced by final articles (parse src from all final platform files)
# Do NOT copy all of images/ — only the specific -v<N> files actually used
cp "<only referenced images>" "archived/$(date +%y%m%d)/<slug>/images/"
# Clean up ongoing
rm -rf "ongoing/<slug>"
```

### Step 4: Write Text-Only Archive to style/published/

Assemble the full set from the version chain: for each platform, walk back `2-draft/v<N>/` → `v1/` to find the latest copy.

For each platform found, write `style/published/<platform>/<YYYY-MM-DD>-<slug>.md` with YAML frontmatter:

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

The clone cache is keyed on `<repo-slug>` (= `<slug>` with any `__<topic>` suffix stripped) and is **shared across every article from that repo**. Only delete it when no other article still needs it.

```bash
repo_slug="${slug%%__*}"   # strip the __<topic> suffix, if any
# Are there OTHER ongoing or archived articles from the same repo?
others=$( (ls -d ongoing/"$repo_slug"* archived/*/"$repo_slug"* 2>/dev/null) | grep -v "/$slug\$\|/$slug/" )
if [ -z "$others" ]; then
  rm -rf "repos/$repo_slug"
  echo "🗑️ 已清理：repos/$repo_slug"
else
  echo "↩️ 保留 repos/$repo_slug（仍有其他文章使用同一仓库克隆）"
fi
```

The frozen archive at `archived/YYMMDD/<slug>/` is never deleted.

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

<clone-cleanup line from Step 7: 🗑️ 已清理 repos/<repo-slug>  OR  ↩️ 保留 repos/<repo-slug>>

📊 Style profile — <N> articles accumulated.
```

## Hard Rule

Never modify files under `archived/YYMMDD/<slug>/` except for `postmortem.md`. The frozen snapshot is the source of truth.
