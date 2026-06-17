# Step 10 — Final Confirmation + Image Generation + Publish

## 1. Assemble Full Version Set

Walk back through `2-draft/v<N>/` → `v<N-1>/` → ... → `v1/` to collect each platform's latest file. The result must be complete — if any platform is missing from the entire chain, re-spawn it from step 06 first.

Present the assembled final set:

```
📊 三方会审通过，最终版本确认

| Platform | Title | Latest Version | Status |
|----------|-------|---------------|--------|
| 小红书 | `<title>` | v<N> | ✅ / ⚠️ |
| 微信公众号 | `<title>` | v<N> | ✅ / ⚠️ |
| 知乎 | `<title>` | v<N> | ✅ / ⚠️ |
| Twitter/X | `<title>` | v<N> | ✅ / ⚠️ |

版本链：v1 (AI) → v2 (用户编辑) → v3 (会审修复) → ... → v<N> (当前)
已修复的问题：<汇总>
图片计划：ongoing/<slug>/2-draft/v<N>/images.md（经版本链回溯到的最新 manifest）— X 张待生成

标题最终确认？内容还有需要微调的吗？确认后生成图片。
```

Wait for user to confirm. User may:
- Request final title tweaks → update file + brief.md
- Request content tweaks → create new version with changes
- Confirm → proceed to image generation

## 2. Generate Images

After user confirms, generate all planned images. Walk back versions to find the latest `images.md`, then run Phase 2 from `07-images.md`:

- Pre-check: `codex --version`
- Batch 1: All cover images in parallel
- Batch 2: All content images in parallel
- On failure: retry once, then note `⚠️ <image-id> generation failed`

## 3. Update Image References

After images are generated, replace `[IMAGE: ...]` placeholders in the latest version files with real markdown references: `![alt](../../images/<image-id>-v<N>.png)`. Use the versioned filenames from the manifest. Articles in `2-draft/v<N>/` — path is two levels up to slug root.

## 4. Confirm Final State

Update `brief.md`:
```
finalized: true
current_version: v<N>
review_completed: true
```

The latest version in `2-draft/v<N>/` IS the published version. No separate `3-final/` directory.

## 5. Next Steps

- **Publish**: `/post-publish <platform> <slug>`
- **After publishing all platforms**: archive with `/post-archive <slug>`

For platforms that failed review (❌):
- Manual rewrite, then re-run `/post-review <slug> <platform>`
