# 微信公众号 Publish Rules

## Publish URL
See `templates/_platform-registry.md` (## Publish URLs). Requires login — open the URL, user navigates after auth.

## Export
Run `python .claude/skills/post-publish/export_article.py <slug> wechat` to generate `ongoing/<slug>/<title>.docx`. Embeds all images and formats code blocks.

## Clipboard Format
Full text as plain text. Code blocks annotated with `[代码：<language>]` above each block (WeChat editor needs manual code block insertion via its toolbar). Image references become `[此处插入配图]`.

## Cover Summary (摘要) — REQUIRED
WeChat shows a 摘要 under the title in the article list and share card. Generate ONE for every 微信 publish:
- **≤120 characters**, usually a single sentence.
- Distill the article's hook/payoff — the pain + what rem does. Author voice, no marketing fluff, no banned phrases.
- Present it to the user to paste into the editor's 摘要 field. If the user leaves it blank, WeChat auto-uses the first 54 chars of the body (worse) — so always offer one.
- Count and report the char length; if >120, tighten before presenting.

## Cover Image
- File: `wechat-cover.png` (aspect ratio — see `templates/_platform-registry.md`)
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
- [ ] 摘要 ≤120 字已填入摘要栏
- [ ] 封面图已上传（比例见 registry）
- [ ] 代码块已通过编辑器工具格式化
- [ ] "阅读原文" 链接已添加
- [ ] 手机预览已检查
