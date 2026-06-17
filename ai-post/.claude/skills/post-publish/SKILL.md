---
name: post-publish
description: Export a finalized article for publishing — image verification, clipboard export, platform-specific publishing guidance. Does NOT edit content.
argument-hint: <platform> [project-slug]
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

# /post-publish — Platform Publishing

You handle the mechanics of getting content onto the platform. The article text is final — you do NOT edit, polish, or suggest content changes. All quality assurance (三方会审, user review) has already happened upstream.

## Supported Platforms

- `xiaohongshu` — 小红书
- `wechat` — 微信公众号
- `zhihu` — 知乎
- `twitter` — Twitter/X

## Workflow

### Step 1: Identify the Article

If `project-slug` is provided, load the target platform's draft with **walk-back inheritance** (mirroring `export_article.py`): later versions store ONLY the files that changed, so an unchanged platform inherits from an earlier version and may be absent at the highest vN. Locate the highest version N, then search `2-draft/v<N>/<platform>.md` from vN down to v1 and use the first match. If the file is found in no version, or no versions exist, or `brief.md` does not have `finalized: true`, abort.

**Review-verdict gate (BLOCKING):** Do not trust `brief.md` alone. Locate the latest `2-draft/v<N>/review-verdict.md` (walk the version chain back if the highest N lacks one). If no verdict artifact exists, abort: "未找到 review-verdict.md — 请先完成 /post-review (三方会审)。" If the verdict marks the target `<platform>` as failing/rejected (not passing), abort: "<platform> 在最近一次会审中未通过，不能发布。" Only proceed when the actual review artifact shows the platform passing.

If not provided: list recent projects by scanning `ongoing/` directories. Present a numbered list for user choice.

If no articles exist: "No articles found. Run `/post-new <github-url>` first."

If platform unsupported: "Supported platforms: xiaohongshu, wechat, zhihu, twitter."

### Step 2: Verify Images — BLOCKING GATE

1. Read the latest article file and parse all `![alt](../../images/<image-id>-v<N>.png)` references.
2. For each reference, check that the file exists on disk (use Glob).
3. Walk version chain to find the latest `images.md` for context.

**If images missing:** report each missing image. If `images.md` lists AI prompts for them, offer generation via takeover-image. Loop until all present.

**Only when all images exist:** "✅ 配图已齐全 (<N> 张). 准备发布到 <platform>？"

### Step 3: Platform-Specific Publishing Prep

Read `.claude/skills/post-publish/_platforms/<platform>.md` for:
- Publish URL
- Clipboard format
- Cover image specs
- Platform restrictions
- Pre-publish checklist items

Format the article for clipboard per the platform rules. Do NOT modify the article file.

### Step 4: Copy to Clipboard + Open Browser

**微信公众号 / 知乎 — generate Word first:**

Pre-check: `python -c "import docx; print('ok')"`
If missing: warn about python-docx dependency.
If OK: run `python .claude/skills/post-publish/export_article.py <slug> wechat` (or zhihu).

1. Format content per platform rules from Step 3.
2. Copy to clipboard (Set-Clipboard on Windows, pbcopy on macOS, xclip on Linux).
3. Open publish URL in browser.
4. Report: "📋 内容已复制到剪贴板，浏览器已打开 <publish-url>"

### Step 5: Publish Checklist & Next Steps

Present the platform-specific checklist from the platform sub-file, plus:
- 通用: 标题已粘贴到标题栏 / 正文格式正确 / 所有配图已上传

After checklist: "发布后，归档到个人风格库：`/post-archive <slug>`"
