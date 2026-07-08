# 02 — Platform Prep & Clipboard Export

## Step 3: Platform-Specific Publishing Prep

Read `.claude/skills/post-publish/_platforms/<platform>.md` for:
- Publish URL
- Clipboard format
- Cover image specs
- Platform restrictions
- Pre-publish checklist items

Format the article for clipboard per the platform rules. Do NOT modify the article file.

## Step 4: Copy to Clipboard + Open Browser

**微信公众号 / 知乎 — generate Word first:**

Pre-check: `python -c "import docx; print('ok')"`
If missing: install the dependency, then retry: `pip install -r scripts/post-publish/requirements.txt` (or, as a fallback, `pip install python-docx`).
If OK: run `python scripts/post-publish/export_article.py <slug> wechat` (or zhihu).

**小红书 — generate the text-card carousel first (script, NOT AI):**

Pre-check: `python -c "import PIL, yaml"`
If missing: `pip install -r scripts/post-publish/requirements.txt`.
Then run: `python scripts/post-publish/gen_xhs_pages.py <slug>`
- Produces `images/xhs-page-01.png … NN.png` (title card + capacity-filled body cards, 3:4) and an editable `images/xhs-pages.yaml`.
- Tell the user: 「分页文字卡已生成（共 N 张，第 1 张标题卡）。要调整每页字体 / 文字格式 / 分页，编辑 `ongoing/<slug>/images/xhs-pages.yaml` 后重跑同一命令即可重生成。」
- These text cards are the primary carousel; any AI supplements from `images.md` are inserted between them. See `_platforms/xiaohongshu.md`.

1. Format content per platform rules from Step 3.
2. Copy to clipboard (Set-Clipboard on Windows, pbcopy on macOS, xclip on Linux).
3. Open publish URL in browser.
4. Report: "📋 内容已复制到剪贴板，浏览器已打开 <publish-url>"
