# 小红书 Publish Rules

## Publish URL
https://creator.xiaohongshu.com/publish/publish?target=image

## Clipboard Format
Plain Chinese text with emoji preserved. Hashtags on a separate line at end. Image references replaced with `[此处上传配图]`.

## Body Images
- **小红书正文不支持内嵌图片。** 不要将配图引用写入正文。
- 发布时单独告知用户图片文件路径，由用户手动在编辑器上传到指定位置。
- 封面图单独上传（3:4，hook 文字已渲染在图上）。

## Character Limit — BLOCKING
- **1000 字硬上限**（不含图片引用路径和 hashtag 行）。发布前必须检查：如果超限，拒绝发布并要求精简。
- Check: strip all `![...](...)` references, then count. If >1000, abort and report the overage.

## Restrictions
- No external links in body — use "评论区/主页自取" CTA
- Hashtags: remind user to add 3-5 hashtags if the article has them

## Pre-Publish Checklist
- [ ] 封面图 3:4 已上传
- [ ] Hook 文字在封面上
- [ ] Hashtags 已添加
- [ ] 无外部链接
