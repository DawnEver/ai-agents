# 微信公众号 Publish Rules

## Publish URL
See `templates/_platform-registry.md` (## Publish URLs). Requires login — open the URL, user navigates after auth.

## Export
Run `python .claude/skills/post-publish/export_article.py <slug> wechat` to generate `ongoing/<slug>/<title>.docx`. Embeds all images and formats code blocks. **The Word doc is the 插图参照 (image-insertion reference)** — user imports the markdown, then inserts each image at the position the Word shows.

## Clipboard Format
**Full markdown, for import.** User imports the markdown into the editor, then inserts images per the Word doc. Keep code fences as-is. Keep image references as `![alt](path)` markdown (do NOT strip to placeholder — the Word doc is the visual guide for where each image goes).

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
Generate Word (插图参照) → copy markdown to clipboard → user imports markdown → user inserts images per the Word doc → format code blocks → preview on mobile → publish.

## Pre-Publish Checklist
- [ ] Word 已生成（`export_article.py <slug> wechat`）
- [ ] 摘要 ≤120 字已填入摘要栏
- [ ] 封面图已上传（比例见 registry）
- [ ] 代码块已通过编辑器工具格式化
- [ ] "阅读原文" 链接已添加
- [ ] 手机预览已检查
