---
name: post-new-source-generalization
description: /post-new accepts github/local-dir/local-file sources; repo-*→source-* rename; pipeline mis-scope lesson (format word ≠ platform restriction)
metadata:
  type: project
---

# post-new source generalization + two-article dogfood (2026-07-08)

## feat(post-new): accept local codebase & research-report sources — commit `27b5bf4`

`/post-new` was hardwired to a GitHub URL. Now Step 01 is a **source resolver** that
classifies the argument and records it in `ongoing/<slug>/1-research/source.md` (the
pointer every later step reads). Three kinds:

- **github** — clone into `repos/<repo-slug>/` (unchanged). `resolved_path = repos/<repo-slug>`.
- **local-dir** — a codebase referenced **in place, never copied**; optional reusable one-line
  pointer `repos/<repo-slug>.src` (a text file naming a rel/abs path — the "文本文件指向路径").
- **local-file** — a research report (pdf/md/txt) read in place as the primary material.

Pointer-file rule: a `.src` is always a pointer; any other text file is a pointer only if its
whole content is a single line that resolves to an existing path (so `report.txt` prose ≠ pointer).

**Step 02** gained a report-ingest branch (thesis / findings-with-traceable-numbers / method /
caveats) alongside code exploration; both branches write the same `source-exploration.md`, so
everything downstream stays source-agnostic. **Rename** runtime artifacts
`repo-exploration.md`→`source-exploration.md`, `repo-analysis.md`→`source-analysis.md` across
steps 03-06, `_writer-base`, `zhihu-writer`, `templates/zhihu`, all 3 post-review consumers,
and the SKILL resume table (+ a legacy fallback for in-flight old runs). **Step 04** analysis has
code-vs-report template variants; **Step 05** persona falls back to ask/deep-user when there is no
git owner; **archive cleanup** is pointer-safe (symlink guard, exact slug-boundary `case` match,
never deletes the external path). 17 files.

`chore(memory)` commit `55cd743` — rem frontmatter→`_meta.json` migration, kept as a separate commit.

## sharp-review triage — see `sharp-review.md` (same day)

11 findings. Fixed the change's own: SR-005 (AGENT.md line 25 rename miss), SR-006 (resolver
`|| resolved=` dead-code fallback → resolve parent dir separately + test), SR-007 (README usage),
SR-009/010/011 (cleanup glob over-match + grep-regex injection, symlink guard, `<slug>`→`$slug`).
**SR-001/002 verified FALSE POSITIVE** — reviewer read-encoding artifacts; on-disk files are clean
UTF-8 (wechat-writer frontmatter fine; zero mojibake via grep). SR-003/004/008 pre-existing, out of
scope. Two HIGHs being encoding artifacts is the pattern to remember: verify on-disk encoding before
acting on a mojibake/"malformed frontmatter" finding.

## Pipeline lesson (gotcha): "推文/文章" is a FORMAT word, not a platform restriction

Step 01's rule: default is **ALL platforms** unless the user *explicitly restricts* scope. A request
for "写一篇推文 / 两篇推文" names a format — still generate all platforms; the thread is one output,
not the whitelist. This session initially mis-scoped two articles as Twitter-only; the user corrected
it. **Twitter is the lowest-priority platform** — focus fire on 小红书/微信/知乎.

## In-progress (NOT committed) — two all-platform articles dogfooding local-dir sources

- `ongoing/dawneever--cc-market__fabric/` — angle: **takeover 长成了 fabric** (rename via first-principles
  "single-vs-many is just call count"; persistent sessions "server is the daemon"; 8 tools/5 modes;
  zero-dep; dogfooding). Source = local `../../claude/cc-market/fabric`.
- `ongoing/dawneever--cc-lab__effort-cache/` — angle: **effort cache partitions on /effort** (round-trip
  10,896→1,355 verbatim recovery; cache-key includes effort) + cc-lab (PTY+tap) built on fabric's
  observe-proxy. Source = local `../cc-lab` + fabric.

Twitter drafts written for both (v1). Written **English-only** per the current `templates/twitter.md`
(SSOT), though prior takeover v1/v2 corpus is bilingual — flagged to user, cheap to revert. Awaiting
per-platform angle confirmation before spawning the three Chinese-platform writers. Persona = author.

## Minor
`style/published/twitter/2026-06-11-dawneever--cc-market.md` has genuine on-disk mojibake in its
Chinese lines (historical corpus) — candidate for a later cleanup pass.
