# 微信公众号 Publish Rules

## Publish URL
https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token= (requires login — open URL, user navigates after auth)

## Export
Run `python .claude/skills/post-publish/export_article.py <slug> wechat` to generate `ongoing/<slug>/<title>.docx`. Embeds all images and formats code blocks.

## Clipboard Format
Full text as plain text. Code blocks annotated with `[代码：<language>]` above each block (WeChat editor needs manual code block insertion via its toolbar). Image references become `[此处插入配图]`.

## Cover Image
- File: `wechat-cover.png` (16:9 — see `templates/_platform-registry.md`)
- WeChat overlays title text at bottom of cover — title-safe zone in upper portion
- Paste title separately in the title field at top of editor

## Code Blocks
WeChat does not support markdown fences. User must select code text and apply the editor's code block tool.

## 阅读原文 Link
Should point to the GitHub repo URL.

## Process
Generate Word → import or paste → format code blocks → preview on mobile → publish.

## Pre-Publish Checklist
- [ ] Word 已生成（`export_article.py <slug> wechat`）
- [ ] 封面图 16:9 已上传
- [ ] 代码块已通过编辑器工具格式化
- [ ] "阅读原文" 链接已添加
- [ ] 手机预览已检查
