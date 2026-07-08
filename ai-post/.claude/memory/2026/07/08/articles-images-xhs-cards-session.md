---
name: articles-images-xhs-cards-session
description: Two all-platform articles (fabric + cc-lab) drafted/reviewed/published-prepped; 小红书 text-card feature; AI-image + fabric-slowness findings
metadata:
  type: project
---

# Session 2026-07-08 — fabric + cc-lab articles, 小红书 text-card feature, image gen

Very long session. Two articles taken from draft → review → publish-prep; a new
publish-time feature built; several reusable findings.

## feat 小红书 text-card carousel (NOT committed yet)
- `scripts/post-publish/gen_xhs_pages.py` — Pillow renders the finalized `xiaohongshu.md`
  into a **bold title card + capacity-fill body cards** → `images/xhs-page-NN.png`
  (3:4, 1080×1440). Editable `images/xhs-pages.yaml` (per-page text / size / color /
  background / align / bold; global canvas / margin / line_spacing / fonts).
- Color emoji via **Segoe UI Emoji `embedded_color`** (cross-platform font resolve:
  msyh / PingFang / Noto). Auto-fit font per page (binary search). `--reinit` re-derives
  config from the article; edit yaml + re-run to regenerate.
- Wired: `post-publish/02-prepare.md` (runs it for 小红书), `_platforms/xiaohongshu.md`
  (text cards = primary carousel), `requirements.txt` (+Pillow +PyYAML),
  `templates/xiaohongshu.md` callout. `__pycache__` was accidentally staged →
  `git rm --cached` + added `__pycache__/`,`*.pyc` to `ai-post/.gitignore` (unstaged).

## Articles (both all-platform; ongoing/, gitignored)
- `dawneever--cc-market__fabric` (takeover→fabric, user-value framing) +
  `dawneever--cc-lab__effort-cache` (effort-cache-partition finding + cc-lab/fabric harness).
- Heavy multi-round edits (forks + user): model common-sense (Claude/Opus top-tier
  总控 · DeepSeek 便宜量大走量粗活 · Codex 代码强+原生生图但官方 CLI 别扭); "织物"→"编织";
  takeover→fabric told as a **growth story**, not "how it folded in"; cc-lab link
  `github.com/DawnEver/ai-agents/tree/main/cc-lab`; 小红书 rewritten payoff-first + 活人味,
  mechanics pushed to 微信/知乎.
- Reviews were **single-model (Opus) inline** (fast, at user request) → `review-verdict.md`
  written for both (Chinese platforms ✅, Twitter ⚠️ stale v1). Publish-prep: 小红书
  clipboard+cards, 知乎 Word (`export_article.py`). 微信 pending.

## Image generation (13 AI images via takeover-image / codex gpt-image-2)
- **gpt-image renders Chinese labels WELL** — the garble fear was overblown; covers +
  diagram labels came out correct. Still visually verify.
- **codex `exec --full-auto` is BLOCKED by the auto-mode permission classifier** → agents
  fall back to fabric MCP `image-generate`, which is **3–5× slower** (6–10 min vs 2–3 min).
  Top lead for "why is fabric slow" → a Bash permission rule for `codex exec --full-auto`
  likely fixes it.
- **Same-basename collision**: two concurrent takeover-image agents both writing
  `zhihu-cover-v1.png` (different dirs) **cross-contaminated** outputs → run same-basename
  gens sequentially.
- One agent rendered wrong content (blindspot → a harness pipeline) → always eyeball.
- Data charts with exact numbers: render a **number-free concept** version (worked well).
- `images.md` manifest per article (`2-draft/v2/images.md`) using
  `templates/_image-prompt-spec.md` three-layer (前景/后景/文字排版); AI-garble risk tagged.

## 三方会审 slowness + a doc bug
- post-review fan-out via fabric is slow (sequential model calls, codex slowest, per-call
  cold-start). What worked: **parallel per-platform reviewers + `--fast`** (drop codex),
  or just **single-model inline**.
- **DOC BUG (todo)**: `post-review/03-execution.md` + `02-reviewers.md` still call the
  RETIRED `mcp__plugin_takeover_takeover__call_model`; must be
  `mcp__plugin_fabric_fabric__call` (params 1:1 except `userPrompt`→`prompt`).

## Craft + pipeline lessons
- AI-taste sentence tells recorded (电报体断句 / 生硬比喻当过渡 / 硬凑花哨) → `_writing-craft.md`
  Anti-AI + Replacement Table + `feedback-ai-taste-patterns.md`.
- "写一篇推文" is a **format word ≠ platform restriction** (default = ALL platforms).
- **小红书 title hard-limit ≤20** (fabric title was 30 → trimmed to "指挥一支会记事的 AI 团队").
- post-publish gates: `brief.md` needs `finalized: true` **and** a `review-verdict.md`.

## Open / deferred
crystallize (index at 20); fabric-slowness dig; inline code-review of `gen_xhs_pages.py`;
commit the text-card feature + article work; Twitter reworks (both stale v1); 微信 publish
for both.
