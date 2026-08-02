---
name: sharp-review-2026-08-02
description: Sharp review findings — 8 total
metadata:
  type: project
---


## Review 2026-08-02 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer claude (claude): skipped
- Reviewer codex (codex): skipped
- Reviewer deepseek (deepseek): OK
- Reviewer kimi (kimi): skipped

### Confirmed findings

---

### [SR-20260802-001] [MEDIUM] README.md — README still names the takeover plugin / call_model MCP as post-review's fan-out dependency, but the code moved to the fabric plugin.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update README §Dependencies and the pipeline diagram: post-review fan-out now uses `mcp__plugin_fabric_fabric__call` (fabric), and `takeover`/`call_model` is deprecated.

README.md:19 lists 'takeover (cc-market plugin) — multi-model fan-out via the call_model MCP tool' and README.md:12 says '三方会审 (takeover fan-out …)'. But .claude/skills/post-review/03-execution.md:7 states 'takeover 已并入 fabric —— 旧的 mcp__plugin_takeover_takeover__call_model 已废弃' and the skill's allowed-tools is `mcp__plugin_fabric_fabric__call`. The README's dependency/setup instructions are stale.

---

### [SR-20260802-002] [MEDIUM] .claude/skills/post-new/07-images.md — Step-07 image manifest still instructs generating an AI 小红书 cover (`xhs-cover-v1.png`) and lists it as the 小红书 cover, contradicting the new script-rendered title-card cover model.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove the 小红书 `xhs-cover` plan from the manifest template and Summary table, or mark it optional. The 小红书 cover is now `xhs-page-01.png` (title card) rendered by scripts/post-publish/gen_xhs_pages.py.

07-images.md:51-55 plans a '小红书 Cover (xhs-cover)' with Path `../../images/xhs-cover-v1.png`, and :76 lists `xhs-cover-v1.png (3:4)` as the cover. This contradicts the publish-time rule that the script's title card is the cover and no AI cover is needed.

---

### [SR-20260802-003] [MEDIUM] templates/_platform-registry.md — SSOT registry still records `xhs-cover.png` as the 小红书 cover, inconsistent with the script-rendered title-card cover and with the versioned `xhs-cover-vN.png` naming used elsewhere.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the Cover Image Conventions row for xiaohongshu to reflect that the cover is the script-rendered title card `xhs-page-01.png` (3:4, from gen_xhs_pages.py), or mark the AI `xhs-cover` optional.

_platform-registry.md:25 lists xiaohongshu cover filename as `xhs-cover.png` with 'Hook text overlaid' design notes. This declared single source of truth predates the gen_xhs_pages title-card cover change and contradicts both the platform publish doc and the versioned `xhs-cover-vN.png` refs.

---

### [SR-20260802-004] [MEDIUM] templates/xiaohongshu.md — Emoji-heavy writing rules and an `xhs-cover` cover example coexist with a generator (gen_xhs_pages.py) that now strips all emoji from the rendered cards and renders the cover from the H1 title card.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document the recent change in the template and the publish doc: gen_xhs_pages.py strips emoji from title and body cards, so emoji the writer adds will not appear on the cards. Either tell writers emoji won't render on cards or make the template's emoji guidance consistent with what actually ships.

The recent session change added strip_emoji() to gen_xhs_pages.py; parse_article() strips emoji from the H1 title and every body paragraph before layout. templates/xiaohongshu.md still mandates ~8-15 emojis per article and 'every bullet starts with one', and post-publish/_platforms/xiaohongshu.md counts the H1 title 'incl emoji' for the title card. No doc mentions that rendered cards are emoji-free.

---

### [SR-20260802-005] [LOW] scripts/post-publish/char_count.py — char_count.py hardcodes platform char/title limits, contradicting the documented single-source-of-truth (templates/_platform-registry.md) claim.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either source LIMITS from templates/_platform-registry.md, or explicitly document that char_count.py is a mirrored copy that must be kept in sync with the registry.

AGENT.md 'Shared reference files are the single source of truth' and post-publish/_platforms/*.md tell users to reference the registry for limits, while char_count.py:27-32 hardcodes the same values. Values currently match, so this is a maintainability/SSOT-contract gap rather than value drift.

---

### [SR-20260802-006] [LOW] .claude/skills/post-review/SKILL.md — post-review/SKILL.md still uses 'takeover fan-out' while its own sub-playbooks (02-reviewers.md, 03-execution.md) describe the fabric MCP call.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update SKILL.md's description, the identity diagram, and the Phase table row to say 'fabric MCP fan-out (`mcp__plugin_fabric_fabric__call`)' to match 03-execution.md.

post-review/SKILL.md:3, 21-22, 42 say 'takeover fan-out', but 03-execution.md:7 and 02-reviewers.md:3 note 'takeover 已并入 fabric —— 旧的 mcp__plugin_takeover_takeover__call_model 已废弃'. The skill's map is internally inconsistent with its own playbook.


## Review 2026-08-02 (follow-up)

## Review 2026-08-02 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer claude (claude): skipped
- Reviewer codex (codex): FAILED
- Reviewer deepseek (deepseek): OK
- Reviewer kimi (kimi): skipped
- Warning: only 1/2 reviewers succeeded

### Confirmed findings

---

### [SR-20260802-007] [MEDIUM] templates/xiaohongshu.md — 发布期改动 note (L110-113) makes the AI xhs-cover optional/replaced by the script title card, but the trailing 配图 manifest examples and Generation Checklist still require an AI `xhs-cover-vN.png` as 配图第1条.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update Example Structure (L92), 封面图 Output (L138), 终版配图清单示例 (L156), and the Generation Checklist (L179) to drop the required AI cover from the 配图 manifest and mark xhs-cover-vN as optional (interleaved supplement, as L112 says).

The partial cover-model change left internal contradiction. The new convention (per registry + _platforms/xiaohongshu.md + 07-images.md) is: 封面 = `xhs-page-01.png` 标题卡, script-rendered from H1, no AI cover needed; 配图清单 is optional supplement. But templates/xiaohongshu.md L92 (Example Structure manifest) still lists `1. 封面（3:4）：![钩子文字](../../images/xhs-cover-v1.png)` as the first required upload, L138 says the cover is 文末配图清单第1条 as `xhs-cover-vN.png`, L156 (终版配图清单示例) still shows `xhs-cover-v2.png` first, and L179 (checklist) still requires a 封面（3:4）entry. A writer following the examples/checklist will still plan a required AI cover, contradicting '封面无需再单独 AI 生图'. The update note only qualifies the prose section, not the concrete manifest examples/checklist.

---

### [SR-20260802-008] [MEDIUM] scripts/post-publish/char_count.py — The comment 'LIMITS is a mirror of templates/_platform-registry.md (SSOT)' is not actually true: the wechat summary limit 120 does not exist in the registry, and the registry's wechat/zhihu char_limits are absent from LIMITS.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either move the wechat 摘要≤120 value into the registry (add a summary-limit column/field) so it really is the SSOT, or reword the comment to name the true sources (xiaohongshu/twitter from registry; wechat 摘要 from .claude/skills/post-publish/_platforms/wechat.md).

The docstring/comment (L27-35) claims '这些限制值是 templates/_platform-registry.md 的镜像副本（SSOT 在 registry）。改 platform 上限时必须同步改这里'. Cross-checked against templates/_platform-registry.md: xiaohongshu (title 20, caption 1000) and twitter (280) do match. But the registry has NO summary field — its wechat char_limit is a 2000-5000 range and its zhihu is 1500-4000, neither of which appears in LIMITS (wechat={'summary':120}, zhihu={}). The 120 wechat summary limit actually lives in .claude/skills/post-publish/_platforms/wechat.md (L35 '摘要 ≤120 字'), not the registry. So the registry is not the SSOT for the wechat summary value, and a registry edit would not keep the 120 in sync, contradicting the mirror invariant.
