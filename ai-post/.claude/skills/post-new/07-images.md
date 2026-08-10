# Step 07 — Plan Image Manifest (from Drafts)

Images are planned AFTER drafts exist so the manifest reflects actual article content. Generation happens AFTER review (step 10).

## Phase 1: Plan Manifest

Read all draft files in `ongoing/<slug>/2-draft/v1/<platform>.md` to:
1. Find `[IMAGE: ...]` placeholders left by writers
2. Identify natural image opportunities: diagrams, terminal output, architecture overview, before/after comparisons
3. Plan cross-platform reuse — same visual concept at different aspect ratios

Write `ongoing/<slug>/2-draft/v1/images.md` — initial image plan, versioned alongside drafts. Later versions (v2, v3, ...) may update it via post-review.

**Three-layer AI Prompt (MANDATORY)**: Every `AI Prompt` MUST follow the three-layer composition spec — see `templates/_image-prompt-spec.md` (前景/后景/文字排版, single source of truth). A flat single-color background is a defect.

**Image versioning**: All generated images use a `-v<N>` suffix (e.g., `product-shot-v1.png`). Edits via takeover image-edit create a new versioned file — never overwrite. Article files reference the specific version. Old versions stay on disk; only the final-used versions survive archive.

**Path convention**: Image files at `ongoing/<slug>/images/<id>-v<N>.png`. Manifest at `2-draft/v1/images.md` (later versions may update it). Article path references: `../../images/<id>-v<N>.png`.

**Manifest format** (`ongoing/<slug>/2-draft/v1/images.md`):

```markdown
# Image Manifest: <repo-name>

> Image files are versioned (`-v1`, `-v2`, …). Edits create a new version; articles always reference the latest.
> Real screenshots take priority over AI-generated images.

## Real Visual Assets from Repo

| ID | Description | Source URL / Path | Used by |
|----|-------------|-------------------|---------|
| `hero` | Project main UI screenshot | <url from README> | 微信(content), 知乎(content), Twitter |

_(If no real visuals exist, mark: "CLI/text only — all images AI-generated")_

## Shared AI-Generated Images (cross-platform reusable)

### `product-shot` (v1)
- **描述**: <中文描述，1句>
- **Scene**: <what to depict>
- **AI Prompt** (English): Foreground: <focal subject>. Background: <textured, layered backdrop — gradient/depth/ambient motifs, never flat>. Text: <exact characters, position, hierarchy, style>.
- **Source**: Draft reference — `[IMAGE: ...]` in 2-draft/v1/<platform>.md line N
- **Used by**: 小红书 (content), 微信公众号 (content), 知乎 (content)
- **Aspect ratios**: 3:4 for 小红书 · 16:9 for 微信/知乎 (generate both or crop)
- **Path**: `../../images/product-shot-v1.png`

_(Add more shared images as needed — one per concept)_

## Platform-Specific Images

### 小红书 Cover — 脚本渲染标题卡（无需 AI 生成）
- 小红书封面 = `xhs-page-01.png`（标题卡），由 `scripts/post-publish/gen_xhs_pages.py` 从 H1 标题渲染（3:4）。**不需要 AI 生成封面**。
- 若额外想补一张 AI 封面（纯视觉、不带钩子文字）作轮图补充，可规划为 `../../images/xhs-cover-v1.png`（可选）。

### 微信公众号 Cover (`wechat-cover`) (v1)
- **AI Prompt**: <prompt>
- **Aspect ratio**: see `templates/_platform-registry.md` (2.35:1 for 微信公众号)
- **Path**: `../../images/wechat-cover-v1.png`

### 知乎 Cover (`zhihu-cover`) (v1)
- **AI Prompt**: <prompt>
- **Aspect ratio**: see `templates/_platform-registry.md` (16:9 for 知乎)
- **Path**: `../../images/zhihu-cover-v1.png`

### Twitter Cover (`twitter-cover`) (v1)
- **AI Prompt**: <prompt>
- **Aspect ratio**: see `templates/_platform-registry.md` (16:9 for Twitter)
- **Path**: `../../images/twitter-cover-v1.png`

## Summary

| Platform | Cover | Content Images |
|----------|-------|----------------|
| 小红书 | `xhs-page-01.png` 标题卡 (3:4, 脚本渲染) | ... |
| 微信公众号 | `wechat-cover-v1.png` (2.35:1) | ... |
| 知乎 | `zhihu-cover-v1.png` (16:9) | ... |
| Twitter/X | `twitter-cover-v1.png` (16:9) | (optional) ... |

Aspect ratios per `templates/_platform-registry.md`.
```

### After Manifest is Written

Present a brief summary to the user (this is informational — the real review happens in step 08):

```
🖼️ 图片计划已生成

封面图：X 张（<platforms>）
内容配图：Y 张（<image-ids>）

图片将在终稿确认后生成。现在进入 user review。
```

Then proceed to User Review (08-user-review).

---

## Phase 2: Generate Images (called from step 10 after user confirms final)

This phase is NOT run during step 07. It is invoked from step 10 after review passes and user confirms final.

### Host-specific image backend

- **Claude Code:** pre-check `codex --version`, then spawn the `takeover-image` named agent defined by `.claude/agents/takeover-image.md`. If Codex CLI is missing, report the install/login requirement.
- **Codex:** call the built-in `imagegen` skill/tool directly. Never spawn `codex exec` from inside Codex (no Codex-in-Codex). Preserve the same prompt, dimensions, and output-path contract.
- **Codex result handling:** inspect the image tool result and its `output_hint`. Materialize the
  returned image at the manifest's exact versioned path (copy/move the hinted local artifact when
  necessary), then verify that the target is a non-empty image file before marking the entry
  complete. A UI-only/generated-image response is not proof that the repository asset exists.
  If no local artifact can be materialized, report that entry as failed and follow the retry rule;
  never invent a path or update article references to a missing file.

### Batch 1: Cover Images

Generate covers for all target platforms in parallel. For each cover entry, use the host-specific image backend above with: `Generate: <AI Prompt from manifest>, save to ongoing/<slug>/images/<cover-id>-v1.png`.

Spawn ALL cover agents in ONE message for parallel execution.

### Batch 2: Content Images

After covers complete, generate content images. Skip entries where real screenshots already exist.

Same parallel spawn pattern. Save as `<image-id>-v1.png`.

### Error Handling

If an agent fails:
1. Retry once with the same prompt.
2. If retry also fails, note: `⚠️ <image-id> generation failed — needs manual creation`.
3. Do NOT block the pipeline.

For both hosts, success means the exact manifest path exists and is non-empty. Validate every
generated file after each batch; treat a missing/empty target as a generation failure.
