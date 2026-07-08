# 小红书 Publish Rules

## Publish URL
See `templates/_platform-registry.md` (## Publish URLs).

## Clipboard Format
Plain Chinese text with emoji preserved. Hashtags on a separate line at end. Image references replaced with `[此处上传配图]`.

## Body Images — 分页文字卡轮图（图文分离）
- **小红书正文不支持内嵌图片。** 正文纯文字；配图单独上传。
- **主体轮图 = 脚本生成的分页文字卡**（用脚本，不用 AI 生图——文字要清晰、可复现）：
  ```bash
  python scripts/post-publish/gen_xhs_pages.py <slug>
  ```
  - 首次运行从终版 `xiaohongshu.md` 按容量拆页，生成：
    - `images/xhs-pages.yaml` —— 可编辑配置（每页 `text` / `size` / `color` / `background` / `align` / `bold`，以及全局 `canvas` / `margin` / `line_spacing` / `fonts`）。
    - `images/xhs-page-01.png … xhs-page-NN.png` —— 3:4 卡片，**第 1 张是标题卡**（H1 渲染成封面），其后为正文卡。
  - **调整每页字体 / 格式 / 分页** → 编辑 `xhs-pages.yaml` 后**重跑同一命令**即可重生成（不带 `--reinit` 时读配置；`--reinit` 用文章重新拆页、丢弃编辑）。
  - 字号默认按每页自适应缩放（在 `body.min_size`~`max_size` 内）；在某页写死 `size:` 即固定该页字号。
- **AI 配图为可选补充**：README 截图、对比图等仍可来自 `images.md`，穿插在文字卡之间；不再需要 AI 封面（标题卡已由脚本渲染）。
- 上传顺序：`xhs-page-01`（标题卡）→ 其余文字卡，按需在中间插入 AI 补充配图。
- 若正文里还残留 `[IMAGE: 描述]` 占位标记 → 视为未完成，先处理再发布。

## Character Limit — BLOCKING
- **标题、正文上限见 `templates/_platform-registry.md`（title_limit / char_limit）**（正文含空格+换行，小红书都计入；图片 markdown 引用和「## 配图」清单不计）。
- **用脚本核对，别手数**：`python scripts/post-publish/char_count.py <article.md> xiaohongshu`（exit 1 = 超限）。超限拒绝发布并精简。

## Restrictions
- No external links in body — use "评论区/主页自取" CTA
- Hashtags: remind user to add 3-5 hashtags if the article has them

## Title — BLOCKING
- **标题硬上限见 `templates/_platform-registry.md`（title_limit）**（含标点/emoji）。发布前数一遍 H1 标题；超出 registry 上限必须精简后才能发。

## Pre-Publish Checklist
- [ ] 标题在 registry title_limit 内
- [ ] 分页文字卡已生成并检查（`xhs-page-*.png`，第 1 张为标题卡）
- [ ] （可选）AI 补充配图已就绪、插入位置已定
- [ ] Hashtags 已添加
- [ ] 无外部链接
