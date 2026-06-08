# Step 06 — Image Manifest

## Ensure Output Dirs Exist

```bash
mkdir -p "ongoing/<slug>/images"
```

## Generate Image Manifest

Before spawning writers, create `ongoing/<slug>/2-draft/images.md` — the single source of truth for all images across all platforms. Agents will reference image paths from this manifest.

**How to build the manifest:**

1. **Scan the repo for real visual assets** — check README for embedded screenshots, GIFs, demo videos. Note their URLs/paths. Real project screenshots are always preferred over AI-generated images.
2. **Identify key scenes** that need visuals across all platforms:
   - Project UI / dashboard / terminal output (the "product shot")
   - Before/after or problem→solution comparison
   - Architecture or workflow diagram
   - Feature close-up or result demo
3. **Plan cross-platform reuse** — the same visual concept often works for multiple platforms (different aspect ratios). List each logical image once, mark which platforms use it.
4. **Platform-specific images** — covers and any platform-only needs (小红书 cover must be 3:4, 微信/知乎/Twitter covers are 16:9).

**Path convention**: Image files are stored at `ongoing/<slug>/images/`. The manifest lives at `ongoing/<slug>/2-draft/images.md`. Writers in `2-draft/` reference images as `../images/<filename>`.

**Manifest format** (`ongoing/<slug>/2-draft/images.md`):

```markdown
# Image Manifest: <repo-name>

> Single source of truth for all article images. Writers reference `../images/<filename>` paths.
> Real screenshots take priority over AI-generated images.

## Real Visual Assets from Repo

| ID | Description | Source URL / Path | Used by |
|----|-------------|-------------------|---------|
| `hero` | Project main UI screenshot | <url from README> | 微信(content), 知乎(content), Twitter |
| `demo-gif` | Feature demo animation | <url> | 微信(content) |

_(If no real visuals exist, mark: "CLI/text only — all images AI-generated")_

## Shared AI-Generated Images (cross-platform reusable)

### `product-shot`
- **描述**: <中文描述，1句>
- **Scene**: <what to depict — project dashboard / terminal output / key feature in action>
- **AI Prompt** (English): <detailed prompt>
- **Used by**: 小红书 (content), 微信公众号 (content), 知乎 (content)
- **Aspect ratios**: 3:4 for 小红书 · 16:9 for 微信/知乎 (generate both or crop)
- **Path**: `../images/product-shot.png`

### `comparison`
- **描述**: <中文描述>
- **Scene**: Before/after or side-by-side comparison showing the problem being solved
- **AI Prompt**: <prompt>
- **Used by**: 小红书 (content), 知乎 (content)
- **Aspect ratios**: 3:4 · 16:9
- **Path**: `../images/comparison.png`

_(Add more shared images as needed)_

## Platform-Specific Images

### 小红书 Cover (`xhs-cover`)
- **Hook text on image**: "<直接来自文章钩子句>"
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
| 小红书 | `xhs-cover.png` (3:4) | `product-shot.png`, `comparison.png` |
| 微信公众号 | `wechat-cover.png` (16:9) | `hero` (real), `product-shot.png`, ... |
| 知乎 | `zhihu-cover.png` (16:9) | `comparison.png`, `product-shot.png` |
| Twitter/X | `twitter-cover.png` (16:9) | (optional) `product-shot.png` |
```

---

## Phase 2: Generate Images (user confirms)

Image generation consumes ~30K+ tokens per image plus Codex API quota. Always present a summary and ask before generating.

After the manifest is written, count planned AI-generated images (exclude real screenshots). Present:

```
🖼️ 图片生成计划

封面图：X 张（<platforms>）
内容配图：Y 张（<image-ids>）
预估消耗：~Z K tokens + Codex 图片额度

生成？选项：all / covers-only / skip
```

- **all** → generate covers then content images (two parallel batches)
- **covers-only** → generate only platform covers; writers use placeholder refs for content images
- **skip** → no generation now; writers use placeholder refs; post-publish will catch missing images later

If user chooses `skip` or `covers-only`, note it in the manifest: `generated: covers-only` or `generated: false`. Post-publish will use this to know whether to auto-offer generation.

### Pre-Check: Codex CLI

Before spawning any image agents, verify Codex CLI is installed:
```bash
codex --version
```
If `codex` is not found, report: "Codex CLI 未安装。请先 `npm install -g @openai/codex && codex login`，然后重新运行此步骤。" Do not proceed until Codex is available.

### Batch 1: Cover Images

Generate covers for all target platforms in parallel. Covers derive from angles/titles confirmed in step 05 — they don't depend on draft content.

For EACH cover entry in the manifest (`xhs-cover`, `wechat-cover`, `zhihu-cover`, `twitter-cover`), spawn a takeover-image agent:

```
Agent({
  subagent_type: "takeover-image",
  description: "Generate <cover-id>",
  prompt: "Generate: <AI Prompt from manifest>, save to ongoing/<slug>/images/<filename>.png at <WxH>"
})
```

Spawn ALL cover agents in ONE message for parallel execution.

### Batch 2: Content Images (generate if no real screenshots)

After covers complete, generate content images (product-shot, comparison, architecture diagram, etc.). Skip entries where the repo already provides real screenshots.

Same parallel spawn pattern per image.

### Batch Requests (multiple variations)

To request N variations in one agent call, append to the prompt:
```
"...at <WxH>. Generate 5 variations."
```
This costs a single agent turn instead of N. Token cost varies with prompt length and image resolution; ~30K+ tokens per turn is a rough baseline — measure actuals to calibrate.

### Error Handling

If an agent fails:
1. Retry once with the same prompt.
2. If retry also fails, note: `⚠️ <image-id> generation failed — needs manual creation`.
3. Do NOT block the pipeline — writers reference image paths as markdown; missing files don't break drafting.

### Cost Estimate (rough baseline — measure to calibrate)

| Batch | Images | Est. tokens |
|-------|--------|-------------|
| Covers (4 platforms) | 4 | ~120K+ |
| Content (3-4 shared) | 3-4 | ~90-120K+ |
| **Total** | 7-8 | ~210-240K+ |
