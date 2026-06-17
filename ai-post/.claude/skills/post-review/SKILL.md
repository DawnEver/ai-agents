---
name: post-review
description: 三方会审 — each reviewer identity is run independently by Claude Sonnet and DeepSeek via sharp-review workflow engine. Disagreements between models surface genuine issues.
argument-hint: <slug> [platform]
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - Skill
  - Workflow
---

# /post-review — 三方会审

Two reviewer identities, each independently run by 2 models by default (3 with `--full-review`) via sharp-review's generalized workflow engine. The engine handles parallel fanout, JSON Schema enforcement, dedup merge, and confidence tagging. post-review handles identity-specific configuration and pipeline integration.

```
身份A 读者代理人:  [Claude Sonnet] [DeepSeek V4 Pro]  → sharp-review workflow → merged findings
身份B 技术核查员:  [Claude Sonnet] [DeepSeek V4 Pro]  → sharp-review workflow → merged findings
                              ↓
                    Cross-identity synthesis
```

Two models independently review with the same prompt. **Both agree → confident. They disagree → needs human judgment.**

## 参数解析

- `<slug>` — 文章目录名，对应 `ongoing/<slug>/`
- `[platform]` — 可选，指定单一平台；不填则审所有已生成平台

Walk `ongoing/<slug>/2-draft/` to find the latest version number (highest N). For each platform, walk back through versions to find the latest copy. Also check for `images.md` in the version chain.

## Phase Table

| Phase | File | What Happens |
|-------|------|-------------|
| Setup | `01-identities.md` | 审稿身份 A/B prompts + finding JSON schemas + AI味 grades |
| Setup | `02-reviewers.md` | Reviewer model config arrays + `--full-review` + workflow path resolution |
| Phase 1-2 | `03-execution.md` | Parallel Workflow calls (1 per identity) + result collection |
| Phase 3-5 | `04-synthesis.md` | 分身份合议 (P3) → 综合裁决 (P4) → 全平台总览 (P5) |
| Phase 6 | `05-images.md` | **MANDATORY** image plan review (术语一致性, 残留引用, 封面标题匹配, 比例) |
| Phase 7 | `06-persist.md` | Write fixed articles + corrected `images.md` + `review-verdict.md` to `v<N+1>/` |

> Phase 6 is **not optional** — every review round (including single-platform re-reviews) must审 `images.md` against the latest drafts. If no `images.md` exists yet, note that in the verdict; otherwise the verdict MUST contain an `## Image plan review` section. A title/motivation change in the drafts almost always staleizes the cover hook — Phase 6 is what catches it.

## How to Execute

Run phases in order. **At the start of each phase, Read the corresponding sub-file** and follow its instructions. This SKILL.md is just the map.

Phase 1-2 run per platform. Phase 3-4 synthesize per-platform (per-identity 合议 → cross-identity verdict). Phase 5 runs once for the all-platform overview.

## Hard Rules

- **Twitter/X skips identity B** — no code to verify, text-only platform.
- **`--full-review`** adds Codex as a 3rd reviewer to each identity.
- **Failed reviewer → `⚠️ 未响应`**, don't block the other identity.
- **Verdict persists**: every round writes `review-verdict.md` to `v<N+1>/`. Check it to determine review status across sessions.
- **Image plan review is mandatory (Phase 6)**: every round审 `images.md`; `review-verdict.md` must include an `## Image plan review` section (or note "no images.md yet"). Cover-hook stale after a title/motivation change is the most common miss — always re-check covers against the latest title.
- **`❌` → manual rewrite needed, then re-review**; **`⚠️` → fix then re-check**; **`✅` → ready for publish**.

## Invocation

Called from `post-new/09-review.md` after version diff chain is collected. Also callable standalone via `/post-review <slug> [platform]`.
