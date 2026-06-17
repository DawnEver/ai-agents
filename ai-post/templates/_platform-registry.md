# Platform Registry

Single source of truth for all platform metadata. Reference this file instead of hardcoding platform properties.

| key | name_zh | name_en | cover_ar | content_ar | char_limit | title_limit | emoji_density | code_blocks | agent | template |
|-----|---------|---------|----------|------------|------------|-------------|---------------|-------------|-------|----------|
| xiaohongshu | 小红书 | RED | 3:4 | 3:4 | **≤1000** | **≤20字** | high | minimal | xiaohongshu-writer | xiaohongshu.md |
| wechat | 微信公众号 | WeChat Official | 2.35:1 | 16:9 | 2000-5000 | — | moderate | expected | wechat-writer | wechat.md |
| zhihu | 知乎 | Zhihu | 16:9 | 16:9 | 1500-4000 | — | minimal | fine | zhihu-writer | zhihu.md |
| twitter | Twitter/X | Twitter/X | 16:9 | 16:9 | 280/tweet | — | moderate | none | twitter-writer | twitter.md |

## Publish URLs

| key | url |
|-----|-----|
| xiaohongshu | `https://creator.xiaohongshu.com/publish/publish?target=image` |
| wechat | `https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token=` |
| zhihu | `https://zhuanlan.zhihu.com/write` |
| twitter | `https://x.com/home` |

## Cover Image Conventions

| key | filename | aspect_ratio | design_notes |
|-----|----------|-------------|-------------|
| xiaohongshu | `xhs-cover.png` | 3:4 | Hook text overlaid, dark/saturated bg, 30-50% text area, modern tech aesthetic |
| wechat | `wechat-cover.png` | 2.35:1 | Title-safe zone in upper portion, project name/logo as focal point |
| zhihu | `zhihu-cover.png` | 16:9 | Clean academic/professional, project name as focal point, neutral tech aesthetic |
| twitter | `twitter-cover.png` | 16:9 | Bold hook visual, can reuse product-shot with 16:9 crop |

## Content Image Conventions

| key | count | preferred_types |
|-----|-------|-----------------|
| xiaohongshu | 2-3 | Main UI screenshot, before/after comparison, feature close-up or demo result |
| wechat | 3-5 | Architecture diagram, terminal screenshots, code output, workflow diagram, benchmark chart |
| zhihu | 2-3 | Comparison table visualization, benchmark chart, architecture/workflow diagram |
| twitter | 1-2 | Hook visual for Tweet 1, demo/output screenshot |
