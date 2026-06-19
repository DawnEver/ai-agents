# 01 — Identify Slug & Verify Final

## Step 1: Identify the Slug

If `slug` is provided:
1. Verify `ongoing/<slug>/` exists.
2. Verify `2-draft/` exists and `brief.md` has `finalized: true` — if not, abort: "No finalized articles found. Complete review and step 10 final confirmation first."
3. **Review-verdict gate (BLOCKING):** Locate the latest `2-draft/v<N>/review-verdict.md` by walking the version chain down from the highest `v<N>` (if the highest N lacks one, fall back to the next lower N). If no verdict artifact exists at all, abort: "未找到 review-verdict.md — 请先完成 /post-review (三方会审)，不能归档未经会审的草稿。" Parse it: read the ACTIVE platform list from `brief.md` (`platforms:` line, comma-separated; default to all registry platforms if absent). If ANY active platform's verdict is failing/❌/rejected (i.e. not passing/✅), abort: "<platform> 在最近一次会审中未通过，不能归档被驳回的草稿。" Only proceed when the actual review artifact shows every active platform passing.
4. Assemble the full version set by walking back through versions for each active platform. Verify at least one platform file exists.

Never archive incomplete, unreviewed, or rejected work — only passing drafts may be frozen.

If not provided:
1. List slugs by scanning `ongoing/` directories where `brief.md` has `finalized: true`
2. Present a numbered list: "Ready to archive — which one?"
3. Read the user's choice

If no slugs found: "No articles ready for archive. Run `/post-new <url>` first."

## Step 2: Verify Articles are Final

Present a summary of what will be archived:

```
📦 准备归档

**项目**：<slug>
**版本链**：v1 → v2 → ... → v<N> (final)
**平台**：render ONLY the ACTIVE platforms from `brief.md`'s `platforms:` line (default to the full `templates/_platform-registry.md` set if absent) — one row each, e.g.:
  - 小红书：v<N> — <char_count> chars
  - 微信公众号：v<N> — <char_count> chars
  - 知乎：v<N> — <char_count> chars
  - Twitter/X：v<N> — <tweet_count> tweets

(Do not list platforms that are not active — a single-platform run shows a single row.)

归档到 archived/<YYMMDD>/<slug>/？
```
