# 知乎 Publish Rules

## Publish URL
See `templates/_platform-registry.md` (## Publish URLs).

## Export
Run `python scripts/post-publish/export_article.py <slug> zhihu` to generate `ongoing/<slug>/<title>.docx`. Handles markdown tables (renders as Word table with blue header row). **The Word doc is the 插图参照 (image-insertion reference)** — user imports the markdown, then inserts each image at the position the Word shows.

## Clipboard Format
**Full markdown, for import.** User imports the markdown, then inserts images per the Word doc. Comparison tables kept as markdown table syntax (知乎 editor renders markdown tables). Keep image references as `![alt](path)` markdown (do NOT strip to placeholder — the Word doc is the visual guide for where each image goes).

## Cover Image
- File: `zhihu-cover.png` (aspect ratio — see `templates/_platform-registry.md`)
- Professional/academic style. Upload via editor UI.
- Paste title separately in title field

## Comparison Table
Markdown tables should render correctly — verify after pasting.

## Sources & Original
- Remind user to add sources for any performance claims if not already cited
- Remind user to check "原创" checkbox before publishing

## Pre-Publish Checklist
- [ ] Word 已生成（`export_article.py <slug> zhihu`）
- [ ] 封面图已上传（比例见 registry）
- [ ] 对比表格渲染正确
- [ ] 原创声明已勾选
- [ ] 引用来源已标注
