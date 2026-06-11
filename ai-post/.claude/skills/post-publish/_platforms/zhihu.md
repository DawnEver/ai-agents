# 知乎 Publish Rules

## Publish URL
https://zhuanlan.zhihu.com/write

## Export
Run `python .claude/skills/post-publish/export_article.py <slug> zhihu` to generate `ongoing/<slug>/<title>.docx`. Handles markdown tables (renders as Word table with blue header row).

## Clipboard Format
Full markdown preserved. Comparison tables kept as markdown table syntax (知乎 editor renders markdown tables). Image references become `[此处插入图片]`.

## Cover Image
- File: `zhihu-cover.png` (16:9 — see `templates/_platform-registry.md`)
- Professional/academic style. Upload via editor UI.
- Paste title separately in title field

## Comparison Table
Markdown tables should render correctly — verify after pasting.

## Sources & Original
- Remind user to add sources for any performance claims if not already cited
- Remind user to check "原创" checkbox before publishing

## Pre-Publish Checklist
- [ ] Word 已生成（`export_article.py <slug> zhihu`）
- [ ] 封面图 16:9 已上传
- [ ] 对比表格渲染正确
- [ ] 原创声明已勾选
- [ ] 引用来源已标注
