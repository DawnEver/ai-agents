# 小红书 Publish Rules

## Publish URL
See `templates/_platform-registry.md` (## Publish URLs).

## Clipboard Format
Plain Chinese text with emoji preserved. Hashtags on a separate line at end. Image references replaced with `[此处上传配图]`.

## Body Images — 图文分离
- **小红书正文不支持内嵌图片。** 正文是纯文字；配图单独上传。
- **终版必须给真实图片路径引用，不能只给描述。** 文末单独一个 `## 配图（单独上传）` 清单，按上传顺序列出每张图的真实路径 `![说明](../../images/<id>-vN.png)`（取自 `images.md`），让用户照单逐张上传。
- 若正文里还残留 `[IMAGE: 描述]` 占位标记 → 视为未完成，先替换成真实路径再发布。
- 封面图单独上传（比例见 `templates/_platform-registry.md`，hook 文字已渲染在图上）。

## Character Limit — BLOCKING
- **标题 ≤20 字、正文 ≤1000 字**（正文含空格+换行，小红书都计入；图片 markdown 引用和「## 配图」清单不计）。
- **用脚本核对，别手数**：`python .claude/skills/post-publish/char_count.py <article.md> xiaohongshu`（exit 1 = 超限）。超限拒绝发布并精简。

## Restrictions
- No external links in body — use "评论区/主页自取" CTA
- Hashtags: remind user to add 3-5 hashtags if the article has them

## Title — BLOCKING
- **标题 ≤20 字硬上限**（含标点/emoji）。发布前数一遍 H1 标题；超 20 字必须精简后才能发。

## Pre-Publish Checklist
- [ ] 标题 ≤20 字
- [ ] 封面图已上传（比例见 registry）
- [ ] Hook 文字在封面上
- [ ] Hashtags 已添加
- [ ] 无外部链接
