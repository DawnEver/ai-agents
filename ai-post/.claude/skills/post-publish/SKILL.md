---
name: post-publish
description: Export a finalized article for publishing — image verification, clipboard export, platform-specific publishing guidance. Does NOT edit content.
argument-hint: <platform> [project-slug]
allowed-tools: "Read,Write,Bash,Glob"
---

# /post-publish — Platform Publishing

You handle the mechanics of getting content onto the platform. The article text is final — you do NOT edit, polish, or suggest content changes. All quality assurance (三遍审校, 三方会审, user review) has already happened upstream.

## Supported Platforms

- `xiaohongshu` — 小红书
- `wechat` — 微信公众号
- `zhihu` — 知乎
- `twitter` — Twitter/X

## Workflow

### Step 1: Identify the Article

If `project-slug` is provided, load `ongoing/<slug>/3-final/<platform>.md`. If it does not exist, abort: "No review-passed article found. Run `/post-review <slug>` first." Never fall back to 2-draft/ — that bypasses the mandatory 三方会审 gate.

If not provided:
1. List recent projects by scanning `ongoing/` directories for existing article files
2. Present a numbered list: "Recent articles — which one to publish?"
3. Read the user's choice

If no articles exist yet: "No articles found. Run `/post-new <github-url>` first."

If the platform is not supported: "Supported platforms: xiaohongshu, wechat, zhihu, twitter."

### Step 2: Verify Images — BLOCKING GATE

**Do NOT proceed past this step until all images are present.**

1. Read `ongoing/<slug>/3-final/<platform>.md` and parse all `![alt](../images/<filename>)` markdown image references.
2. For each reference, check that `ongoing/<slug>/images/<filename>` exists on disk (use Glob).
3. Also read `ongoing/<slug>/3-final/images.md` for context on what each image should be.

**If any images are missing:**
```
🛑 配图缺失，无法发布

以下图片文件不存在：
  - images/xxx.png — <description from images.md>
  - images/yyy.png — <description from images.md>

请补全后再发布。
```
- If `images.md` lists AI prompts for the missing images, suggest: "可运行图片生成来补全这些图片。"
- If they are real screenshots, tell the user: "请将对应截图下载到 `ongoing/<slug>/images/` 目录。"
- **Loop here** — re-check after user provides images. Do not move on.

**Only when all images exist:**
```
✅ 配图已齐全 (<N> 张)

准备发布到 <platform>？
```

### Step 3: Platform-Specific Publishing Prep

Format the article for the target platform's editor. Do NOT modify the article file — only format for clipboard.

#### 小红书

- **Publish URL**: `https://creator.xiaohongshu.com/publish/publish?target=image`
- **Clipboard format**: Plain Chinese text with emoji preserved. Hashtags on a separate line at end. Image references replaced with `[此处上传配图]`.
- **Cover image**: `ongoing/<slug>/images/xhs-cover.png` (3:4). Hook text should already be overlaid on the image.
- **Image upload order**: Cover first, then body images in order.
- **Restrictions**: No external links in body — use "评论区/主页自取" CTA (should already be in article).
- **Hashtags**: Remind user to add 3-5 hashtags if the article has them.

#### 微信公众号

- **Publish URL**: `https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token=` (requires login — open URL, user navigates after auth)
- **Word export**: Run `python .claude/skills/post-publish/export_article.py <slug> wechat` to generate `ongoing/<slug>/<title>.docx`. This embeds all images and formats code blocks — easier to import than plain text paste.
- **Clipboard format**: Full text as plain text. Code blocks annotated with `[代码：<language>]` above each block (WeChat editor needs manual code block insertion via its toolbar). Image references become `[此处插入配图]`.
- **Title**: Paste title separately in the title field at top of editor.
- **Cover image**: `ongoing/<slug>/images/wechat-cover.png` (16:9). Note: WeChat overlays title text at bottom of cover — title-safe zone in upper portion.
- **Code blocks**: WeChat does not support markdown fences. User must select code text and apply the editor's code block tool.
- **"阅读原文" link**: Should point to the GitHub repo URL.
- **Process**: Generate Word → import or paste → format code blocks → preview on mobile → publish.

#### 知乎

- **Word export**: Run `python .claude/skills/post-publish/export_article.py <slug> zhihu` to generate `ongoing/<slug>/<title>.docx`. Handles markdown tables (renders as Word table with blue header row).
- **Publish URL**: `https://zhuanlan.zhihu.com/write`
- **Clipboard format**: Full markdown preserved. Comparison tables kept as markdown table syntax (知乎 editor renders markdown tables). Image references become `[此处插入图片]`.
- **Title**: Paste separately in title field.
- **Cover image**: `ongoing/<slug>/images/zhihu-cover.png` (16:9, professional/academic style). Upload via editor UI.
- **Comparison table**: Markdown tables should render correctly — verify after pasting.
- **Sources**: Remind user to add sources for any performance claims if not already cited.
- **原创**: Remind user to check "原创" checkbox before publishing.

#### X/Twitter

- **Publish URL**: `https://x.com/home`
- **Clipboard format**: Each tweet as a separate block:
  ```
  [Tweet 1] (<N> chars)
  <content>

  [Tweet 2] (<N> chars)
  <content>
  ---
  ```
- **How to compose**: Twitter threads must be built tweet-by-tweet:
  1. Open `https://x.com/home`
  2. Compose Tweet 1, paste content, attach image if any
  3. Click "+" to add each subsequent tweet
- **Character count**: Each tweet verified against 280-char limit. Flag any over limit.
- **Image**: Attach to Tweet 1 (the hook visual). `ongoing/<slug>/images/twitter-cover.png` if available.
- **Thread verify**: After composing, read top-to-bottom to verify flow.

### Step 4: Copy to Clipboard + Open Browser

**微信公众号 / 知乎 — generate Word first:**
```bash
python .claude/skills/post-publish/export_article.py <slug> wechat
python .claude/skills/post-publish/export_article.py <slug> zhihu
```
Open the resulting `.docx`, then copy-paste from Word into the WeChat editor (preserves paragraph structure). Proceed with clipboard export below for code block annotation reference.

1. **Format content** per platform rules from Step 3.
2. **Copy to clipboard**:
   - Windows: `Set-Clipboard -Value @'<content>'@`
   - macOS: `echo "<content>" | pbcopy` (use heredoc for multiline)
   - Linux: `echo "<content>" | xclip -selection clipboard`
3. **Open publish URL** in browser:
   - Windows: `start "" "<url>"`
   - macOS: `open "<url>"`
   - Linux: `xdg-open "<url>"`
4. Report: "📋 内容已复制到剪贴板，浏览器已打开 <publish-url>"

If clipboard copy or browser open fails, display the content and URL prominently for manual action.

### Step 5: Publish Checklist & Next Steps

Present a platform-specific pre-publish checklist:

**通用**:
- [ ] 标题已粘贴到标题栏
- [ ] 正文格式正确（分段、代码块、表格）
- [ ] 所有配图已上传并放置在正确位置

**小红书**: [ ] 封面图 3:4 已上传 / [ ] Hook 文字在封面上 / [ ] Hashtags 已添加 / [ ] 无外部链接

**微信公众号**: [ ] Word 已生成（`export_article.py <slug> wechat`）/ [ ] 封面图 16:9 已上传 / [ ] 代码块已通过编辑器工具格式化 / [ ] "阅读原文" 链接已添加 / [ ] 手机预览已检查

**知乎**: [ ] Word 已生成（`export_article.py <slug> zhihu`）/ [ ] 封面图 16:9 已上传 / [ ] 对比表格渲染正确 / [ ] 原创声明已勾选 / [ ] 引用来源已标注

**X/Twitter**: [ ] 每条推文 ≤280 字符 / [ ] Tweet 1 以 🧵👇 结尾 / [ ] 配图已附加 / [ ] GitHub 链接仅在最后推文

After checklist, suggest:
- "发布后，归档到个人风格库：`/post-archive <slug>`"
