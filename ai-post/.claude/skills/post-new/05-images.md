# Step 6-6.5: Image Manifest

## Step 6: Ensure Output Dirs Exist

```bash
mkdir -p "articles/<slug>/images"
```

## Step 6.5: Generate Image Manifest

Before spawning writers, create `articles/<slug>/images.md` — the single source of truth for all images across all platforms. Agents will reference image paths from this manifest.

**How to build the manifest:**

1. **Scan the repo for real visual assets** — check README for embedded screenshots, GIFs, demo videos. Note their URLs/paths. Real project screenshots are always preferred over AI-generated images.
2. **Identify key scenes** that need visuals across all platforms:
   - Project UI / dashboard / terminal output (the "product shot")
   - Before/after or problem→solution comparison
   - Architecture or workflow diagram
   - Feature close-up or result demo
3. **Plan cross-platform reuse** — the same visual concept often works for multiple platforms (different aspect ratios). List each logical image once, mark which platforms use it.
4. **Platform-specific images** — covers and any platform-only needs (小红书 cover must be 3:4, 微信/知乎/Twitter covers are 16:9).

**Manifest format** (`articles/<slug>/images.md`):

```markdown
# Image Manifest: <repo-name>

> Single source of truth for all article images. Writers reference `images/<filename>` paths.
> Real screenshots take priority over AI-generated images.

## Real Visual Assets from Repo

| ID | Description | Source URL / Path | Used by |
|----|-------------|-------------------|---------|
| `hero` | Project main UI screenshot | <url from README> | 微信(content), 知乎(content), Twitter |
| `demo-gif` | Feature demo animation | <url> | 微信(content) |

_(If no real visuals exist, mark: "CLI/text only — all images AI-generated")_

## Shared AI-Generated Images (cross-platform reusable)

### `img-product-shot`
- **描述**: <中文描述，1句>
- **Scene**: <what to depict — project dashboard / terminal output / key feature in action>
- **AI Prompt** (English): <detailed prompt>
- **Used by**: 小红书 (content), 微信公众号 (content), 知乎 (content)
- **Aspect ratios**: 3:4 for 小红书 · 16:9 for 微信/知乎 (generate both or crop)
- **Path**: `images/product-shot.png`

### `img-comparison`
- **描述**: <中文描述>
- **Scene**: Before/after or side-by-side comparison showing the problem being solved
- **AI Prompt**: <prompt>
- **Used by**: 小红书 (content), 知乎 (content)
- **Aspect ratios**: 3:4 · 16:9
- **Path**: `images/comparison.png`

_(Add more shared images as needed)_

## Platform-Specific Images

### 小红书 Cover (`img-xhs-cover`)
- **Hook text on image**: "<直接来自文章钩子句>"
- **AI Prompt**: <prompt> --ar 3:4
- **Path**: `images/xhs-cover.png`

### 微信公众号 Cover (`img-wechat-cover`)
- **AI Prompt**: <prompt> --ar 16:9
- **Path**: `images/wechat-cover.png`

### 知乎 Cover (`img-zhihu-cover`)
- **AI Prompt**: <prompt> --ar 16:9
- **Path**: `images/zhihu-cover.png`

### Twitter Cover (`img-twitter-cover`)
- **AI Prompt**: <prompt> --ar 16:9
- **Path**: `images/twitter-cover.png`

## Summary

| Platform | Cover | Content Images |
|----------|-------|----------------|
| 小红书 | `xhs-cover.png` (3:4) | `product-shot.png`, `comparison.png` |
| 微信公众号 | `wechat-cover.png` (16:9) | `hero` (real), `product-shot.png`, ... |
| 知乎 | `zhihu-cover.png` (16:9) | `comparison.png`, `product-shot.png` |
| Twitter/X | `twitter-cover.png` (16:9) | (optional) `product-shot.png` |
```
