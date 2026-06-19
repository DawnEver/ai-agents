# 03 — Style Accumulation

## Step 4: Write Text-Only Archive to style/published/

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

## Step 5: Extract Style Fingerprints

From each platform's article body, extract:

- **Opening**: The first 1-2 substantive sentences. Skip frontmatter, image references, and heading lines — find the first actual prose the reader encounters.
- **Closing**: The last 1-2 substantive sentences before any signature, hashtags, or CTA lines.
- **Voice markers**: 2-3 distinctive phrases, transitions, or framing patterns that are characteristic. Look for specific metaphors, unique transition phrases ("说实话", "一个冷知识"), recurring syntactic patterns. Avoid generic phrases like "GitHub:" or hashtags.

Each fingerprint must be a direct quote, trimmed to reasonable length.

## Step 6: Update `style/profile.md`

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
