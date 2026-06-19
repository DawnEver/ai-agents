# 01 — Identify Article & Verify Images

## Step 1: Identify the Article

If `project-slug` is provided, load the target platform's draft with **walk-back inheritance** (mirroring `export_article.py`): later versions store ONLY the files that changed, so an unchanged platform inherits from an earlier version and may be absent at the highest vN. Locate the highest version N, then search `2-draft/v<N>/<platform>.md` from vN down to v1 and use the first match. If the file is found in no version, or no versions exist, or `brief.md` does not have `finalized: true`, abort.

**Review-verdict gate (BLOCKING):** Do not trust `brief.md` alone. Locate the latest `2-draft/v<N>/review-verdict.md` (walk the version chain back if the highest N lacks one). If no verdict artifact exists, abort: "未找到 review-verdict.md — 请先完成 /post-review (三方会审)。" If the verdict marks the target `<platform>` as failing/rejected (not passing), abort: "<platform> 在最近一次会审中未通过，不能发布。" Only proceed when the actual review artifact shows the platform passing.

If not provided: list recent projects by scanning `ongoing/` directories. Present a numbered list for user choice.

If no articles exist: "No articles found. Run `/post-new <github-url>` first."

If platform unsupported: "Supported platforms: xiaohongshu, wechat, zhihu, twitter."

## Step 2: Verify Images — BLOCKING GATE

1. Read the latest article file and parse all `![alt](../../images/<image-id>-v<N>.png)` references.
2. For each reference, check that the file exists on disk (use Glob).
3. Walk version chain to find the latest `images.md` for context.

**If images missing:** report each missing image. If `images.md` lists AI prompts for them, offer generation via takeover-image. Loop until all present.

**Only when all images exist:** "✅ 配图已齐全 (<N> 张). 准备发布到 <platform>？"
