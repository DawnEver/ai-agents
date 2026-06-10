# Step 07 — Plan Image Manifest (from Drafts)

Images are planned AFTER drafts exist so the manifest reflects actual article content. Generation happens AFTER review (step 10).

## Phase 1: Plan Manifest

Read all draft files in `ongoing/<slug>/2-draft/v1/<platform>.md` to:
1. Find `[IMAGE: ...]` placeholders left by writers
2. Identify natural image opportunities: diagrams, terminal output, architecture overview, before/after comparisons
3. Plan cross-platform reuse — same visual concept at different aspect ratios

Write `ongoing/<slug>/2-draft/v1/images.md` — single source of truth for all planned images, versioned alongside drafts.

**Path convention**: Image files stored at `ongoing/<slug>/images/`. Manifest at `2-draft/v1/images.md` (later versions may update it). Path references from versioned platform files use `../../images/<filename>`.

**Manifest format** (`ongoing/<slug>/2-draft/v1/images.md`):

```markdown
# Image Manifest: <repo-name>

> Single source of truth for all article images. Planned from drafts, generated after review.
> Real screenshots take priority over AI-generated images.

## Real Visual Assets from Repo

| ID | Description | Source URL / Path | Used by |
|----|-------------|-------------------|---------|
| `hero` | Project main UI screenshot | <url from README> | 微信(content), 知乎(content), Twitter |

_(If no real visuals exist, mark: "CLI/text only — all images AI-generated")_

## Shared AI-Generated Images (cross-platform reusable)

### `product-shot`
- **描述**: <中文描述，1句>
- **Scene**: <what to depict>
- **AI Prompt** (English): <detailed prompt>
- **Source**: Draft reference — `[IMAGE: ...]` in 2-draft/v1/<platform>.md line N
- **Used by**: 小红书 (content), 微信公众号 (content), 知乎 (content)
- **Aspect ratios**: 3:4 for 小红书 · 16:9 for 微信/知乎 (generate both or crop)
- **Path**: `../../images/product-shot.png`

_(Add more shared images as needed — one per concept)_

## Platform-Specific Images

### 小红书 Cover (`xhs-cover`)
- **Hook text on image**: "<hook from draft opening>"
- **AI Prompt**: <prompt> --ar 3:4
- **Path**: `../images/xhs-cover.png`

### 微信公众号 Cover (`wechat-cover`)
- **AI Prompt**: <prompt> --ar 16:9
- **Path**: `../images/wechat-cover.png`

### 知乎 Cover (`zhihu-cover`)
- **AI Prompt**: <prompt> --ar 16:9
- **Path**: `../images/zhihu-cover.png`

### Twitter Cover (`twitter-cover`)
- **AI Prompt**: <prompt> --ar 16:9
- **Path**: `../images/twitter-cover.png`

## Summary

| Platform | Cover | Content Images |
|----------|-------|----------------|
| 小红书 | `xhs-cover.png` (3:4) | ... |
| 微信公众号 | `wechat-cover.png` (16:9) | ... |
| 知乎 | `zhihu-cover.png` (16:9) | ... |
| Twitter/X | `twitter-cover.png` (16:9) | (optional) ... |
```

### After Manifest is Written

Present a brief summary to the user (this is informational — the real review happens in step 08):

```
🖼️ 图片计划已生成

封面图：X 张（<platforms>）
内容配图：Y 张（<image-ids>）

图片将在终稿确认后生成。现在进入 user review。
```

Then proceed to User Review (08-user-review).

---

## Phase 2: Generate Images (called from step 10 after user confirms final)

This phase is NOT run during step 07. It is invoked from step 10 after review passes and user confirms final.

### Pre-Check: Codex CLI

```bash
codex --version
```
If `codex` is not found, report: "Codex CLI 未安装。请先 `npm install -g @openai/codex && codex login`。"

### Batch 1: Cover Images

Generate covers for all target platforms in parallel. For EACH cover entry in the manifest, spawn a takeover-image agent:

```
Agent({
  subagent_type: "takeover-image",
  description: "Generate <cover-id>",
  prompt: "Generate: <AI Prompt from manifest>, save to ongoing/<slug>/images/<filename>.png"
})
```

Spawn ALL cover agents in ONE message for parallel execution.

### Batch 2: Content Images

After covers complete, generate content images. Skip entries where real screenshots already exist.

Same parallel spawn pattern.

### Error Handling

If an agent fails:
1. Retry once with the same prompt.
2. If retry also fails, note: `⚠️ <image-id> generation failed — needs manual creation`.
3. Do NOT block the pipeline.
