# 05 — Phase 6: 图片提示词会审（Image Prompt Review）

文章正文审完后，独立审查图片清单。

## 定位 images.md

Walk `2-draft/v<N>/` → `v1/` to find the latest `images.md`. This is the image manifest generated in step 07.

## 检查清单

### 1. 术语一致性
Each image's alt text and prompt description must use the same technical terms as the article. Cross-check against the article body: if the article says "JSON-RPC 2.0", the image prompt shouldn't say "REST API call".

### 2. 残留引用
Scan for orphaned image references — images mentioned in `images.md` but no longer referenced in the latest article version (e.g., an image for a paragraph that was deleted). Flag these for removal.

### 3. 封面标题匹配
Cover image prompts must match the article's actual title. If the article title changed between v1 and vN, the cover prompt may be stale.

### 4. 过时描述
Architecture diagram prompts that describe v1's design but the article now describes v2. Compare prompt content against the repo-analysis.md reference.

### 5. 比例正确
Verify aspect ratios match platform requirements per `templates/_platform-registry.md`:
- 小红书封面: 3:4
- 微信公众号封面: 2.35:1
- 知乎封面: 16:9
- Twitter 配图: 16:9 (optional)

## Image Editing

If an existing image needs content fixes (not just prompt text updates), spawn a takeover-image agent with an edit prompt to create a new version:

1. Spawn a takeover-image agent with the edit prompt and current image path
2. Save output as `<image-id>-v<N+1>.png` — do NOT overwrite the old version
3. Update `images.md`: bump version in the entry header, update **Path**
4. Update all article files (walk the version chain) that reference the old version: replace `-v<N>.png` → `-v<N+1>.png`

## 输出

修复后的 `images.md` 写入 `2-draft/v<N+1>/images.md`。如有无法确定的项，标注 `⚠️ 需人工确认`。
