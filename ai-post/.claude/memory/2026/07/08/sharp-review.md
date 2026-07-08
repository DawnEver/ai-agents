---
name: sharp-review-2026-07-08
description: Sharp review findings — 102 total
metadata:
  type: project
---













## Resolution 2026-07-08 (post-review triage)

Findings triaged against the source-generalization change (`feat(post-new)`: github/local-dir/local-file sources + `repo-*`→`source-*` rename):

- **FIXED (this change's own issues):**
  - SR-005 — AGENT.md line 25 rename miss → now `source (pointer), source-exploration, market-research, source-analysis, brief`.
  - SR-006 — 01-clone.md dead-code `|| resolved=` fallback → parent dir resolved + tested separately.
  - SR-007 — README `/post-new` command usage → shows `<github-url|local-path|slug> [platform]`.
  - SR-009 — cleanup others-detection: prefix glob + unescaped grep regex → exact slug-boundary `case` match.
  - SR-010 — cleanup: added symlink guard before `rm -rf repos/$repo_slug` (protect external source).
  - SR-011 — cleanup: `rm -rf "ongoing/<slug>"` → `rm -rf "ongoing/$slug"`.
- **FALSE POSITIVE (verified):**
  - SR-001 — wechat-writer.md frontmatter is clean (`platform: wechat` on its own line). Reviewer read-encoding artifact.
  - SR-002 — no mojibake on disk (grep for U+FFFD / mojibake sequences = 0). PowerShell/Codex read-encoding artifact.
- **OUT OF SCOPE (pre-existing, not this feature):** SR-003 (image-lifecycle template contradiction), SR-004 (dependency-docs completeness), SR-008 (post-publish supported-platforms formatting; likely same read artifact as SR-002).

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK — agent-mode, full-repo exploration
- Reviewer B (DeepSeek): FAILED — agent-mode timed out (600s)
- Reviewer C (Opus): OK — review-mode over gathered rename/safety-critical context

### Confirmed findings

---

### [SR-20260708-001] [HIGH] .claude/agents/wechat-writer.md — The WeChat agent frontmatter is malformed, so the documented wechat-writer agent metadata does not match a valid agent definition.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Put platform: wechat on its own YAML line and repair the corrupted description text.

The description: line contains platform: wechat inline instead of a separate key. Any loader expecting frontmatter keys will treat the whole text as the description and fail to see the platform field, despite AGENT.md and templates/_platform-registry.md advertising wechat-writer as the WeChat platform agent.

---

### [SR-20260708-002] [HIGH] templates/*.md, .claude/agents/*.md, .claude/skills/**/*.md, scripts/post-publish/*.py — Large parts of the project documentation and embedded script messages are mojibake, making critical Chinese workflow rules unreadable or semantically broken.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer (LIKELY FALSE POSITIVE — verify encoding)
- **Suggestion:** Recover these files from a correct UTF-8 source or manually rewrite the corrupted text; then add an encoding check that rejects replacement/mojibake markers.

Examples include .claude/agents/xiaohongshu-writer.md, .claude/skills/post-review/SKILL.md, templates/_platform-registry.md, and script literals in scripts/post-publish/char_count.py / export_article.py. NOTE: this is most likely a PowerShell/Codex read-encoding artifact, NOT on-disk corruption — verify the actual working-tree encoding (e.g. `git show :<file> | file -`) before acting; if the tree is genuinely UTF-8 this finding is a false positive and should be closed.

---

### [SR-20260708-003] [MEDIUM] .claude/agents/_writer-base.md, templates/xiaohongshu.md, templates/wechat.md, templates/zhihu.md, .claude/skills/post-new/10-summary.md — The image lifecycle docs contradict each other about whether drafts should contain [IMAGE: ...] placeholders or final markdown image references.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Separate draft-stage and final-stage requirements explicitly in every platform template: v1 writers emit only [IMAGE: ...]; finalization replaces them with markdown refs.

_writer-base.md says v1 generation must use only [IMAGE: ...] placeholders and must not write markdown image references. But platform templates such as templates/zhihu.md, templates/wechat.md, templates/xiaohongshu.md still include output/checklist requirements for markdown refs like ![...](../../images/<id>-vN.png). A writer following both documents gets incompatible instructions.

---

### [SR-20260708-004] [MEDIUM] README.md, .claude/skills/post-review/SKILL.md, .claude/skills/post-review/02-reviewers.md — The review dependency documentation is incomplete and points at generic repositories instead of actionable plugin installation/setup instructions.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document the exact required plugin names, install commands, expected MCP tool name, and expected merge-findings.js path; replace the generic GitHub links with the actual plugin references.

README.md says takeover and sharp-review are dependencies, but links both to https://github.com/anthropics/claude-code, which does not identify the cc-market plugins or how to install them. The skill then assumes mcp__plugin_takeover_takeover__call_model and a cached sharp-review/scripts/merge-findings.js. Setup docs do not tell a new user how to satisfy or verify these.

---

### [SR-20260708-005] [MEDIUM] ai-post/AGENT.md — Directory-layout line 25 still uses both pre-rename names repo-exploration and repo-analysis (rename miss).

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer (most on-target for the rename's consistency goal)
- **Suggestion:** Change line 25 to `1-research/       — source-exploration, market-research, source-analysis, brief` to match the renamed runtime artifacts.

The rename repo-exploration.md->source-exploration.md and repo-analysis.md->source-analysis.md was applied everywhere except the canonical Directory Layout in AGENT.md — the one place a contributor looks to learn artifact names. AGENT.md is the declared source of truth for layout, so this stale line contradicts SKILL.md's pipeline/resume tables (source-exploration.md / source-analysis.md). Confirmed by grep across the whole ai-post tree: this is the ONLY lingering old-name occurrence outside the deliberate SKILL.md legacy-fallback note (line 90) and the frozen memory entries.

---

### [SR-20260708-006] [MEDIUM] ai-post/.claude/skills/post-new/01-clone.md — Source resolver `|| resolved="$src_arg"` fallback is effectively dead code; a missing parent dir yields a garbage /basename path.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Resolve the dir separately and test it: `dir="$(cd "$(dirname "$src_arg")" 2>/dev/null && pwd)"; resolved="${dir:+$dir/}$(basename "$src_arg")"; [ -n "$dir" ] || resolved="$src_arg"`.

In `resolved="$(cd ... && pwd)/$(basename "$src_arg")" || resolved="$src_arg"`, the assignment exit status is that of the LAST command substitution — $(basename ...), which almost always succeeds — so the || fallback never fires. When cd $(dirname) fails (nonexistent parent), the first substitution is empty and resolved becomes `/<basename>`, a bogus path rooted at /. The -d/-f tests then fail and it exits 'Unrecognized source', which is tolerable, but the documented fallback semantics do not match the code. Confined to missing-parent inputs. (Slug traversal validation itself — lines 49-60 — is sound: rejects `..` and out-of-allowlist, and correctly exempts the source path.)

---

### [SR-20260708-007] [LOW] README.md, AGENT.md, .claude/skills/post-new/SKILL.md — Top-level command usage is stale/incomplete compared with the actual post-new skill arguments and resume behavior.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update README command examples to show /post-new <github-url|local-path|slug> [platform] and mention resume-by-slug behavior, matching .claude/skills/post-new/SKILL.md.

README.md documents /post-new <url> only, while the skill frontmatter and body support GitHub URLs, local paths, local files, existing slugs, and optional platform selection. AGENT.md has the richer source description, but README remains the likely first entry point and underspecifies supported usage.

---

### [SR-20260708-008] [LOW] .claude/skills/post-publish/SKILL.md — The Supported Platforms list is malformed, merging multiple bullets onto one line.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Put each platform on its own bullet and repair the corrupted Chinese labels.

The current section renders as - xiaohongshu ... - wechat ... - zhihu ... on one bullet line before Twitter. This makes the supported-platform list harder to scan and easier for agents to parse incorrectly. (May share root cause with the encoding artifact in SR-002 — verify.)

---

### [SR-20260708-009] [LOW] ai-post/.claude/skills/post-archive/04-cleanup.md — others-detection prefix glob "$repo_slug"* over-matches sibling slugs and injects raw slug into a grep regex.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Anchor to a real boundary: iterate `for d in ongoing/"$repo_slug"* archived/*/"$repo_slug"*; do case "${d##*/}" in "$repo_slug"|"$repo_slug"__*) ...; esac; done` and skip the current $slug by exact string compare, not grep -v with an unescaped regex.

Two non-catastrophic issues. (1) `ls -d ongoing/"$repo_slug"*` matches any sibling sharing the prefix (repo_slug foo matches foo-bar, foobar), so `others` gets false positives and the shared clone is retained when it could be freed — safe direction (cache leak, never a wrong delete). (2) `grep -v "/$slug\$\|/$slug/"` interpolates the slug straight into a BRE; slugs legally contain '.', which is regex any-char, so a.b would filter /axb. Because repo_slug scopes the eventual rm -rf, neither can delete another repo's cache.

---

### [SR-20260708-010] [LOW] ai-post/.claude/skills/post-archive/04-cleanup.md — The 'never delete the external source path' guarantee holds but rests on an implicit, unguarded invariant.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer (target-safety currently VERIFIED — this is hardening)
- **Suggestion:** State the invariant in a comment and add a defensive guard before the rm (e.g. refuse to rm if repos/$repo_slug is a symlink), so a future change that materializes repos/<repo-slug>/ as a real copy or symlink can't start deleting user-owned material.

Given the design (local-dir referenced in place -> only a .src pointer; local-file leaves nothing under repos/), the delete targets are repos/$repo_slug (absent for local sources -> no-op), repos/$repo_slug.src (the pointer, not its content), and the ongoing workspace — so target-safety currently holds and the prose is clear (the review's focus concern — cleanup never deleting an external path — is satisfied). Minor doc gap: cleanup claims a local-file 'leaves nothing under repos/', but a local-file reached via a user-created .src pointer would leave that pointer (harmlessly removed by rm -f).

---

### [SR-20260708-011] [LOW] ai-post/.claude/skills/post-archive/04-cleanup.md — Step 7 block mixes literal placeholder rm -rf "ongoing/<slug>" with real $repo_slug/$slug shell variables.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** For consistency use the real variable `rm -rf "ongoing/$slug"` in the executable block, matching the $repo_slug/$slug usage in the lines above it.

Surrounding lines dereference real variables (repos/$repo_slug, repos/$repo_slug.src, grep -v "/$slug..."), but the workspace-removal line reads `rm -rf "ongoing/<slug>"` with an angle-bracket placeholder. Across these skill docs <slug> is a documented template the agent substitutes, so this likely does not no-op at runtime — but mixing literal placeholders and live shell vars in one runnable block is an internal inconsistency that invites a copy-paste that silently fails to remove the workspace.


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-012] [HIGH] templates/_platform-registry.md — The registry still documents Xiaohongshu as an AI-cover/content-image platform, not a script-generated page-card carousel platform.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the Xiaohongshu rows to make xhs-page-01.png/xhs-page-NN.png the primary 3:4 carousel output, mark xhs-cover.png as deprecated or optional, and change content image count from required 2-3 to optional supplements.

gen_xhs_pages.py now creates the primary carousel from the finalized xiaohongshu.md, with page 1 as the title/cover card. The registry still says Xiaohongshu cover filename is xhs-cover.png and content images are 2-3. Since this file is repeatedly called the single source of truth, downstream templates and image planning keep inheriting stale instructions.

---

### [SR-20260708-013] [HIGH] templates/xiaohongshu.md — The Xiaohongshu template contradicts itself: it mentions script page cards, then continues to require a separate cover and image checklist.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Rewrite the cover/content-image sections around the new lifecycle: draft plain text, optional AI supplement manifest only, post-publish generates xhs-page-*.png; remove required xhs-cover-vN.png examples and required cover/content checklist items.

The template has a note saying the script now renders the main carousel and that AI supplements are optional, but the surrounding sections still say the cover must be separately designed, output as xhs-cover-vN.png, and listed in the final ## 配图 block. The Generation Checklist still requires a 配图清单 with 封面 + 1-2 配图 from images.md. A writer following the whole file gets incompatible requirements.

---

### [SR-20260708-014] [HIGH] .claude/skills/post-new/07-images.md — Image planning still generates a Xiaohongshu AI cover even though the new generator makes page 1 the cover/title card.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the manifest template and generation flow so Xiaohongshu skips mandatory xhs-cover planning; only plan optional supplemental images, and document that gen_xhs_pages.py owns the carousel/cover during /post-publish.

The manifest template still contains 小红书 Cover (xhs-cover) and Step 10 generates all cover images in parallel. That means the pipeline will waste effort creating an AI cover that the updated publish docs say is no longer needed, and it will keep pushing drafts toward xhs-cover-v1.png references instead of script-generated xhs-page-01.png.

---

### [SR-20260708-015] [MEDIUM] README.md — Setup docs do not mention the Python publish dependencies now required for Xiaohongshu page generation.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a Python dependency setup line, e.g. pip install -r scripts/post-publish/requirements.txt, and name Pillow/PyYAML as required for Xiaohongshu publishing.

scripts/post-publish/requirements.txt now includes Pillow>=10.0 and PyYAML>=6.0, and gen_xhs_pages.py exits without PyYAML/Pillow. README prerequisites only mention Codex CLI/imagegen, so a fresh user can reach /post-publish xiaohongshu with no documented setup path outside the skill internals.

---

### [SR-20260708-016] [MEDIUM] .claude/skills/post-publish/02-prepare.md — The Xiaohongshu publish workflow runs the generator but does not make inspection and rerun a blocking publish gate.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** After gen_xhs_pages.py, require opening/checking every xhs-page-*.png, editing images/xhs-pages.yaml if pagination/style is bad, rerunning without --reinit, and only then copying/opening the publish page.

The script creates editable YAML precisely because automatic pagination/style often needs human adjustment. The doc says to tell the user they can edit and rerun, but then continues directly to clipboard and browser. That makes a visual artifact that is now the primary carousel effectively unchecked.

---

### [SR-20260708-017] [MEDIUM] .claude/skills/post-publish/_platforms/xiaohongshu.md — The platform publish rules do not clearly separate caption clipboard text from generated carousel assets.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** State explicitly that clipboard content is only the caption body plus hashtags, while upload assets are ongoing/<slug>/images/xhs-page-*.png plus optional supplements; the trailing ## 配图 manifest is not copied.

The file says plain Chinese text with image references replaced by an upload marker, while the generator parses and excludes the 配图 manifest and renders the carousel separately. The publish operator needs an unambiguous split: what goes to clipboard, what gets uploaded, and what source sections are ignored by the card generator.

---

### [SR-20260708-018] [LOW] templates/xiaohongshu.md — The template still teaches writers to maintain final markdown image references for Xiaohongshu supplements, but the new primary images are not markdown refs in the article.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make markdown refs optional and limited to AI supplement planning, and add a note that xhs-page-*.png is generated outside the draft and should not be referenced in the article body.

Several lines still say final Xiaohongshu output must replace placeholders with real markdown image paths. That is no longer true for the primary carousel. Without narrowing this to optional supplement images, writers/reviewers may incorrectly fail a valid text-only Xiaohongshu draft.


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-019] [HIGH] .claude/skills/post-new/07-images.md — Xiaohongshu image planning still creates an AI cover even though the new publish generator makes page 1 the cover/title card.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove the mandatory `xhs-cover` manifest entry and cover-generation path for Xiaohongshu; document only optional supplemental images, with `gen_xhs_pages.py` owning the carousel and title card during `/post-publish`.

The live code in `scripts/post-publish/gen_xhs_pages.py` renders `xhs-page-01.png` from the H1 as the title/cover card. But `07-images.md` still tells the pipeline to plan `xhs-cover-v1.png`, generate it in Batch 1, and list it in the summary. That is stale and will waste image-generation calls and leave draft/image manifests teaching the old lifecycle.

---

### [SR-20260708-020] [HIGH] templates/xiaohongshu.md — The Xiaohongshu template still requires old final image references that contradict the new generated text-card carousel.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Rewrite the cover/content-image sections and final checklist around the current lifecycle: body is plain text, AI images are optional supplements, and `/post-publish` generates `xhs-page-*.png`; remove required `xhs-cover-vN.png` and required 1-2 markdown image refs.

The template says the generator now creates the primary carousel, but later sections still require a trailing `## 配图` list with `xhs-cover-vN.png` plus 1-2 content images from `images.md`. The generator does not consume that list for the primary cards; it stops before the image manifest and emits `ongoing/<slug>/images/xhs-page-*.png`. The checklist is therefore internally contradictory and will push writers back into the removed AI-cover workflow.

---

### [SR-20260708-021] [MEDIUM] .claude/skills/post-publish/01-identify.md — The publish gate verifies only markdown image refs in the article and does not verify the generated Xiaohongshu carousel assets.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a Xiaohongshu-specific gate after running `gen_xhs_pages.py`: verify `ongoing/<slug>/images/xhs-pages.yaml` and at least `xhs-page-01.png` exist, inspect the generated PNGs, and block publish if they are missing or stale.

Step 2 parses `![alt](../../images/...)` references from the article. The new Xiaohongshu flow intentionally keeps the body plain text and generates the actual upload assets later as `xhs-page-*.png`, so the current image verification can pass with zero images while the carousel has not been generated or checked.

---

### [SR-20260708-022] [MEDIUM] .claude/skills/post-publish/02-prepare.md — The Xiaohongshu generator is documented as a prep action, but inspection/rerun is not a blocking publish step.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make visual inspection explicit and blocking: after generating cards, require checking every `xhs-page-*.png`, editing `xhs-pages.yaml` if pagination/style is wrong, rerunning the same command, then continuing to clipboard/browser only after approval.

`gen_xhs_pages.py` does deterministic layout, auto-shrinks text, deletes stale cards, and supports manual YAML edits. The docs mention the YAML but immediately continue to clipboard and browser. That treats generated visual assets as fire-and-forget even though bad wrapping, missing emoji font, overlong title, or poor page breaks are now the primary publish risk.

---

### [SR-20260708-023] [MEDIUM] README.md — Fresh setup docs omit the Python dependencies now required for Xiaohongshu publishing.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a prerequisites/setup line for `pip install -r scripts/post-publish/requirements.txt`, naming `python-docx`, `Pillow`, and `PyYAML` by purpose.

`gen_xhs_pages.py` imports Pillow and PyYAML, and `export_article.py` imports python-docx. `requirements.txt` has all three, but README only mentions Codex CLI/imagegen. A fresh user can follow README and hit `/post-publish xiaohongshu` with missing dependencies.

---

### [SR-20260708-024] [MEDIUM] templates/_platform-registry.md — The registry is advertised as the single source of truth, but platform limits are still hardcoded in code and docs.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either make scripts read a machine-readable registry/config, or stop claiming the Markdown registry is the executable SSOT. At minimum, mention that `char_count.py` must be updated when limits change.

README and templates say `_platform-registry.md` owns char/title limits. But `scripts/post-publish/char_count.py` hardcodes `xiaohongshu` title 20/caption 1000, WeChat summary 120, and Twitter 280. A registry edit will not change the checker, which is exactly the kind of drift the docs claim to prevent.

---

### [SR-20260708-025] [LOW] .claude/skills/post-publish/_platforms/xiaohongshu.md — Caption text and carousel-upload responsibilities are blurred.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split the section into two concrete outputs: clipboard caption text copied from `xiaohongshu.md`, and upload assets generated as `xhs-page-*.png` plus optional supplemental AI images.

The file says clipboard format is plain Chinese text and also says the primary carousel is generated text cards. It does not clearly say the caption remains the publish text while `xhs-page-*.png` are separate upload assets. That ambiguity matters because Xiaohongshu publishing now has two payloads, not one article-with-images payload.

---

### [SR-20260708-026] [LOW] AGENT.md — Top-level helper-script examples omit the new Xiaohongshu generator.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the `scripts/<skill>/` layout example to include `post-publish/gen_xhs_pages.py`, since it is now a primary publish helper rather than an incidental script.

AGENT.md lists `export_article.py`, `char_count.py`, and `requirements.txt` as examples. After the new generator, Xiaohongshu publishing depends on `gen_xhs_pages.py`; omitting it makes the architecture overview stale for the most changed area.


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-027] [HIGH] templates/_platform-registry.md — Xiaohongshu registry still documents the old xhs-cover/content-image lifecycle, contradicting the new text-card generator.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the Xiaohongshu registry rows so xhs-page-01.png through xhs-page-NN.png are the primary 3:4 carousel output, and mark xhs-cover.png plus 2-3 content images as optional/deprecated supplements.

scripts/post-publish/gen_xhs_pages.py now renders the main carousel from the finalized xiaohongshu.md, with page 1 as the title/cover card. But the registry, which the docs repeatedly call the SSOT, still says Xiaohongshu's cover filename is xhs-cover.png and content images are 2-3. That stale SSOT keeps downstream docs and agents anchored to the removed AI-cover flow.

---

### [SR-20260708-028] [HIGH] templates/xiaohongshu.md — The Xiaohongshu template says the script owns the carousel, then still requires the old xhs-cover-vN.png and mandatory image-list workflow.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Rewrite the cover/content-image sections and final checklist around the current lifecycle: body is plain text, AI images are optional supplements, and /post-publish generates xhs-page-*.png; remove required xhs-cover-vN.png and required 1-2 markdown image refs.

The template includes a note saying gen_xhs_pages.py creates the primary carousel and that AI supplements are optional. Later sections still say the cover must be separately designed, output as xhs-cover-vN.png, and listed in the final image block. The Generation Checklist still requires cover + 1-2 images from images.md. A writer following the whole file gets incompatible instructions.

---

### [SR-20260708-029] [HIGH] .claude/skills/post-new/07-images.md — Image planning still mandates a Xiaohongshu AI cover even though publish now generates the cover/title card from text.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove the mandatory xhs-cover manifest entry and cover-generation path for Xiaohongshu; document only optional supplemental images, with gen_xhs_pages.py owning the carousel and title card during /post-publish.

The manifest template still contains 小红书 Cover (xhs-cover) and Step 10 generates all cover images in parallel. That means the pipeline will waste image-generation calls creating an AI cover that the updated publish docs say is no longer needed, and it will keep pushing drafts toward xhs-cover-v1.png references instead of script-generated xhs-page-01.png.

---

### [SR-20260708-030] [MEDIUM] .claude/skills/post-publish/01-identify.md — The publish image-verification gate does not cover the new Xiaohongshu upload assets.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a Xiaohongshu-specific gate after running gen_xhs_pages.py: verify ongoing/<slug>/images/xhs-pages.yaml and at least xhs-page-01.png exist, inspect the generated PNGs, and block publish if they are missing or stale.

Step 2 only parses markdown image references from the article. The new Xiaohongshu flow intentionally keeps the body plain text and creates the actual upload assets later as xhs-page-*.png. So the current gate can pass with zero article images before the primary carousel exists or has been checked.

---

### [SR-20260708-031] [MEDIUM] .claude/skills/post-publish/02-prepare.md — The Xiaohongshu publish flow treats generated cards as fire-and-forget instead of requiring visual inspection.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** After gen_xhs_pages.py, require opening/checking every xhs-page-*.png, editing images/xhs-pages.yaml if pagination/style is bad, rerunning without --reinit, and only then copying/opening the publish page.

The script does deterministic layout, auto-shrinks text, deletes stale cards, and supports manual YAML edits. The docs mention the YAML but immediately continue to clipboard and browser. Bad wrapping, missing emoji font, overlong title, or poor page breaks are now the primary publish risk, so visual inspection should be explicit and blocking.

---

### [SR-20260708-032] [MEDIUM] README.md — README prerequisites omit the Python dependencies required by both publishing scripts.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a setup line such as pip install -r scripts/post-publish/requirements.txt, naming python-docx, Pillow, and PyYAML by purpose.

gen_xhs_pages.py imports Pillow and PyYAML, and export_article.py imports python-docx. scripts/post-publish/requirements.txt has all three, but README only mentions Codex CLI/imagegen. A fresh user can follow README and hit /post-publish xiaohongshu with missing dependencies.

---

### [SR-20260708-033] [LOW] .claude/skills/post-publish/_platforms/xiaohongshu.md — The Xiaohongshu platform doc does not clearly separate clipboard caption text from upload assets.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split the section into two concrete outputs: clipboard caption text copied from xiaohongshu.md, and upload assets generated as xhs-page-*.png plus optional supplemental AI images.

The file says clipboard format is plain Chinese text and also says the primary carousel is generated text cards. It does not explicitly say the caption remains the publish text while xhs-page-*.png are separate upload assets. That ambiguity matters because Xiaohongshu publishing now has two payloads, not one article-with-images payload.

---

### [SR-20260708-034] [LOW] templates/_writing-craft.md — The Section Index contains at least one broken anchor for the Chinese identity section.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the anchor to the actual generated Markdown anchor, or avoid fragile non-ASCII anchors by adding a stable ASCII heading/anchor convention.

The index points to #我-as-subject, but the actual heading is 「我」as Subject — Identity Consistency. Standard Markdown anchor generation will not resolve that exact fragment. Templates tell agents to use the Section Index, so broken anchors make progressive loading brittle.


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-035] [HIGH] templates/xiaohongshu.md — 小红书封面规则自相矛盾：模板同时描述脚本生成 title card 与手动 xhs-cover-vN.png 两套不兼容流程

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove the mandatory xhs-cover-vN.png flow from the template, or clearly mark it as optional legacy/supplemental only.

Lines 105-107 say gen_xhs_pages.py owns the title card/cover and no AI cover is needed, but lines 109-133 still require a separately designed cover output as xhs-cover-vN.png; line 174 still requires 封面 + 1-2 配图 from images.md. A writer following the whole file gets two incompatible publishing models.

---

### [SR-20260708-036] [HIGH] .claude/skills/post-new/07-images.md — Image manifest still mandates a 小红书 AI cover that publish no longer uses

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the 小红书 manifest entry to optional supplemental images only; let gen_xhs_pages.py own xhs-page-01.png as the primary cover/title card.

Lines 51-55 define mandatory xhs-cover-v1.png, line 76 summarizes it as the 小红书 cover, and Batch 1 generates all covers. That wastes generation and pushes drafts toward stale xhs-cover references while publish docs say the carousel/title card is generated at publish time.

---

### [SR-20260708-037] [HIGH] .claude/skills/post-publish/01-identify.md — Publish image gate does not verify the actual 小红书 primary carousel (xhs-page-*.png)

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a 小红书-specific gate after gen_xhs_pages.py: require images/xhs-pages.yaml and xhs-page-*.png, plus a visual check before publish.

Step 2 only parses markdown image references from the article. The new 小红书 primary assets are generated later as images/xhs-page-*.png, so the gate can pass with zero markdown images and publish before the carousel exists or has been checked.

---

### [SR-20260708-038] [MEDIUM] templates/_platform-registry.md — Registry still advertises xhs-cover.png as the canonical 小红书 cover artifact

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Replace the 小红书 cover convention with xhs-page-01.png / script-generated title card; make AI cover naming explicitly optional if retained.

Line 25 still lists xhs-cover.png with hook-text design notes. That conflicts with the new script output documented in publish docs: xhs-page-01.png … xhs-page-NN.png.

---

### [SR-20260708-039] [MEDIUM] README.md / AGENT.md — Setup docs omit post-publish Python dependencies (Pillow, PyYAML, python-docx)

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a short setup section: pip install -r scripts/post-publish/requirements.txt, naming python-docx, Pillow, and PyYAML by purpose.

requirements.txt correctly contains all three dependencies, and 02-prepare.md documents reactive pre-checks, but top-level onboarding only mentions Codex CLI. A fresh user following README can hit /post-publish xiaohongshu before Pillow/PyYAML are installed.

---

### [SR-20260708-040] [MEDIUM] .claude/skills/post-review/05-images.md — Image review still treats 小红书 cover prompt review as mandatory despite script-generated title card

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the review checklist to review script-generated 小红书 cards separately from optional AI supplements.

Lines 17-28 focus on cover prompt/title matching and explicitly list 小红书封面: 3:4. With the new flow the title card comes from H1 via gen_xhs_pages.py, not an image prompt, so this review phase is pointed at the wrong artifact.

---

### [SR-20260708-041] [LOW] .claude/skills/post-publish/02-prepare.md — Claims per-page font editing that the script does not support (font is global-only)

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Say 字号 / 颜色 / 背景 / 对齐 / 加粗 / 分页; reserve font path changes for global fonts config.

Line 28 tells the user they can adjust 每页字体. The script schema supports per-page text/size/color/background/align/bold, while fonts is global config only.

---

### [SR-20260708-042] [LOW] templates/_writing-craft.md — Section index anchor for 「我」as Subject is likely broken/inexact

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the index anchor to match the generated Markdown anchor, or avoid anchor literals for non-ASCII headings.

Line 13 lists #我-as-subject, while the actual heading is ## 「我」as Subject — Identity Consistency at line 50. Most Markdown renderers strip punctuation and include more heading text, so this shortcut is unlikely to jump correctly.


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-043] [HIGH] templates/xiaohongshu.md — 小红书模板同时要求新脚本生成标题卡，又继续强制旧的 xhs-cover-vN.png / 配图清单流程

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 重写封面图、正文配图和 Generation Checklist：正文保持纯文本，AI 图只作为可选补充，主轮图和第 1 张封面卡由 /post-publish 的 gen_xhs_pages.py 生成。删除必填 xhs-cover-vN.png 和“封面 + 1-2 配图”要求。

gen_xhs_pages.py 从 H1 渲染 xhs-page-01.png 作为标题/封面卡，并从正文生成 xhs-page-*.png；它不消费文末配图清单来生成主体卡片。模板虽在发布期说明里承认新流程，但后续仍说封面必须单独设计、输出 xhs-cover-vN.png，并在最终清单和 checklist 中强制要求封面及 1-2 张配图。这会把写手拉回已经被脚本取代的 AI 封面流程。

---

### [SR-20260708-044] [HIGH] templates/_platform-registry.md — 平台 registry 仍把小红书定义成 xhs-cover.png + 2-3 内容图的平台，而不是脚本文字卡轮图平台

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 把小红书 cover/content image 约定改成 xhs-page-01.png 到 xhs-page-NN.png 为主轮图输出；xhs-cover.png 和 2-3 内容图若保留，只能标为可选补充或 legacy。

README 和 AGENT.md 都把 registry 称为平台元数据 SSOT。当前代码实际由 gen_xhs_pages.py 生成 primary carousel，page 1 是标题卡。registry 还写 xhs-cover.png、2-3 content images，会让 post-new、post-review、takeover-image 等继续继承旧事实。

---

### [SR-20260708-045] [HIGH] .claude/skills/post-new/07-images.md — 图片规划仍强制规划和生成小红书 AI 封面，和新发布脚本的 title card 流程冲突

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 小红书 image manifest 改为只规划可选 supplemental images；明确 gen_xhs_pages.py 在发布阶段负责主轮图和封面/title card。

该文件仍定义“小红书 Cover (xhs-cover)”、路径 xhs-cover-v1.png，并在批量封面生成阶段处理它。新脚本已经让 xhs-page-01.png 成为封面/title card，所以这会浪费生成成本，并继续把 drafts/images.md 推向旧的 xhs-cover 引用。

---

### [SR-20260708-046] [MEDIUM] .claude/skills/post-publish/01-identify.md — 发布前图片 gate 不验证小红书实际要上传的 xhs-page-*.png 轮图

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 为 xiaohongshu 增加专门 gate：运行 gen_xhs_pages.py 后要求存在 images/xhs-pages.yaml 和至少 xhs-page-01.png，检查所有 xhs-page-*.png 后才能继续发布。

Step 2 只解析文章中的 markdown 图片引用。新小红书流程故意让正文纯文本，实际主上传资产是在之后生成的 ongoing/<slug>/images/xhs-page-*.png。因此当前 gate 可以在 0 张图片时通过，而主轮图还不存在或没检查。

---

### [SR-20260708-047] [MEDIUM] .claude/skills/post-publish/02-prepare.md — 小红书生成卡片后没有把视觉检查和 rerun 设成阻塞步骤

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 在运行 gen_xhs_pages.py 后明确要求打开/检查每张 xhs-page-*.png；如分页、字号、emoji 字体或换行有问题，编辑 xhs-pages.yaml 并不带 --reinit 重跑；通过后再复制正文和打开浏览器。

脚本会自动缩放、清理旧 PNG，并支持 YAML 手工调整，说明生成结果需要人工看图确认。当前文档只提示可编辑 YAML，然后马上进入 clipboard/browser，容易把主发布资产当成 fire-and-forget。

---

### [SR-20260708-048] [MEDIUM] README.md — 顶层安装说明没有列出 post-publish 的 Python 依赖 (Pillow / PyYAML / python-docx)

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 在 Prerequisites 或 Dependencies 中加入 `pip install -r scripts/post-publish/requirements.txt`，并说明 python-docx 用于 Word 导出，Pillow/PyYAML 用于小红书卡片生成。

requirements.txt 正确包含 python-docx、Pillow、PyYAML；02-prepare.md 也有失败后的安装提示。但 README 只提 Codex CLI/imagegen。新用户按 README 配环境，到 /post-publish xiaohongshu 才会撞 Pillow/PyYAML 缺失。

---

### [SR-20260708-049] [MEDIUM] .claude/skills/post-publish/_platforms/xiaohongshu.md — 小红书发布规则没有清楚拆开“剪贴板正文”和“上传资产”

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 明确写成两个输出：剪贴板只复制 caption/body + hashtags；上传资产是 xhs-page-*.png 加可选 supplemental images；文末 ## 配图 manifest 不复制进正文。

文件一边说 clipboard format 是纯中文文本、图片引用替换成上传占位，一边说主轮图是脚本文字卡。char_count.py 和 gen_xhs_pages.py 都把 ## 配图 后面的内容视为不属于正文/卡片。当前文档没有明确告诉发布操作者哪些内容复制、哪些图片上传，容易把 manifest 或占位文字贴进正文。

---

### [SR-20260708-050] [MEDIUM] .claude/skills/post-review/05-images.md — 图片审查仍把小红书封面 hook / 图片 manifest 当成必审主资产

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 为小红书改审查目标：AI supplemental images 可按 images.md 审，但主封面/title card 应在 post-publish 由 gen_xhs_pages.py 生成并检查；不要再把 xhs-cover hook freshness 当成必审项。

post-review 的图片阶段仍围绕 images.md、封面标题匹配和比例审查。小红书主封面现在来自 xiaohongshu.md 的 H1 和 gen_xhs_pages.py，而不是 images.md 里的 cover prompt。审查目标已经偏离实际发布资产。

---

### [SR-20260708-051] [LOW] AGENT.md — 架构概览的 post-publish helper 示例漏掉了现在最关键的小红书生成脚本 gen_xhs_pages.py

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 把 scripts/<skill>/ 示例更新为包含 post-publish/gen_xhs_pages.py。

AGENT.md 只举 export_article.py、char_count.py 和 requirements.txt。gen_xhs_pages.py 现在是小红书发布路径的核心脚本，漏掉它让项目结构说明在最近变化点上过时。

---

### [SR-20260708-052] [LOW] templates/_writing-craft.md — Section Index 里的中文身份小节 anchor 很可能不匹配实际 Markdown 生成锚点

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 把 anchor 改成实际渲染器会生成的锚点，或给该小节改一个稳定 ASCII 标题/显式 anchor。

索引写 `#我-as-subject`，实际标题是 `## 「我」as Subject — Identity Consistency`。多数 Markdown 渲染器会保留更多标题文本并去掉引号/标点，生成的锚点不太可能正好是 `#我-as-subject`。这类跳转会悄悄失效。


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-053] [HIGH] .claude/skills/post-new/07-images.md — Still mandates generating an AI `xhs-cover-v1.png` even though the current Xiaohongshu publish flow uses `gen_xhs_pages.py` to render the title card as the cover.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove Xiaohongshu from mandatory cover generation and document optional supplemental images only.

The current code path for Xiaohongshu cover/carousel is `scripts/post-publish/gen_xhs_pages.py <slug>`, which creates `ongoing/<slug>/images/xhs-page-01.png` as the title card plus body cards. The image-planning docs still define `### 小红书 Cover (xhs-cover)`, path `../../images/xhs-cover-v1.png`, and batch cover generation for all target platforms. That makes the pipeline waste time generating an obsolete AI cover and pushes downstream docs/review toward a file the publish script never needs.

---

### [SR-20260708-054] [HIGH] templates/xiaohongshu.md — The template contradicts itself: it says the script-generated title card replaces the AI cover, then still requires a final cover image path from `images.md`.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Rewrite the cover/content-image sections so `xhs-page-01.png` is the normal cover and `images.md` entries are explicitly optional supplements.

Lines around the new publish note correctly say `gen_xhs_pages.py` produces the primary carousel and no separate AI cover is needed. Later sections still say the cover output is `![...](../../images/xhs-cover-vN.png)` and the generation checklist requires `配图清单 present at end: 封面（3:4）+ 1-2 配图`. That is not the current behavior: the script reads the article text and writes generated cards under `ongoing/<slug>/images/`, not versioned markdown refs in the article body.

---

### [SR-20260708-055] [MEDIUM] templates/_platform-registry.md — Xiaohongshu cover metadata still points to `xhs-cover.png`, which is stale under the new card-generation flow.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the Xiaohongshu cover convention to `xhs-page-01.png` or mark AI `xhs-cover` as optional legacy/supplemental.

The registry is documented as the single source of truth for image conventions, but its Xiaohongshu cover row still says `xhs-cover.png`. The actual publishing helper generates `xhs-page-01.png`, `xhs-page-02.png`, etc. This stale registry entry keeps poisoning other docs that rely on registry cover metadata.

---

### [SR-20260708-056] [MEDIUM] .claude/skills/post-publish/01-identify.md — The image verification gate only checks markdown image refs, so it does not verify the required Xiaohongshu text-card carousel.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a Xiaohongshu branch that verifies or triggers `xhs-page-*.png` generation and treats AI image refs as optional supplements.

Step 2 parses `![alt](../../images/<image-id>-v<N>.png)` references from the article and declares images ready when those exist. For the current Xiaohongshu flow, the primary publish assets are generated after this gate by `gen_xhs_pages.py` and are named `xhs-page-NN.png`, not markdown refs in `xiaohongshu.md`. A Xiaohongshu article with no AI supplements can pass this gate with zero checked carousel images.

---

### [SR-20260708-057] [MEDIUM] README.md — Setup docs omit the Python publishing dependencies now required for Xiaohongshu card generation.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add `pip install -r scripts/post-publish/requirements.txt` to prerequisites or a publish setup section, naming `python-docx`, `Pillow`, and `PyYAML`.

`scripts/post-publish/requirements.txt` now includes `Pillow>=10.0` and `PyYAML>=6.0` for `gen_xhs_pages.py`, in addition to `python-docx`. README prerequisites only mention Codex CLI for image generation. A fresh user following README can reach `/post-publish xiaohongshu` without Pillow/YAML installed and hit the script's import failures.

---

### [SR-20260708-058] [MEDIUM] README.md — The documented pipeline says final confirmation generates images, but it does not mention the new publish-time Xiaohongshu text-card generation step.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the pipeline summary and `/post-publish` command description to call out Xiaohongshu `gen_xhs_pages.py` card generation.

README currently describes `/post-new` ending with image generation and `/post-publish` as clipboard + guidance. The actual Xiaohongshu publish behavior now includes deterministic card rendering during post-publish, producing required upload assets. That is a material workflow step, not just guidance.

---

### [SR-20260708-059] [MEDIUM] .claude/skills/post-review/05-images.md — Image review still treats Xiaohongshu as requiring a 3:4 cover image, not the script-rendered title card.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Teach image review that Xiaohongshu AI covers are optional and the publish-time title card is produced by `gen_xhs_pages.py`.

The review checklist still says to verify `小红书封面: 3:4` and focuses on cover prompt freshness. Under the current code, the normal Xiaohongshu cover/title card is not an AI prompt in `images.md`; it is rendered from H1 by the publish script. This review doc will flag or update a non-required `xhs-cover` while missing the actual generated card flow.

---

### [SR-20260708-060] [LOW] .claude/skills/post-publish/SKILL.md — It says `_platforms/<platform>.md` contains reference data, but the Xiaohongshu platform file now contains executable workflow steps.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the map to say platform files can include platform-specific workflow steps, especially Xiaohongshu card generation.

The SKILL map calls platform files 'reference data, not workflow steps'. That is no longer true: `_platforms/xiaohongshu.md` documents the actual `python scripts/post-publish/gen_xhs_pages.py <slug>` command and upload order. The contradiction makes the workflow ownership unclear.


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-061] [HIGH] templates/_platform-registry.md — XHS metadata is stale and contradicts the new script-generated text-card carousel.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the XHS registry row and image conventions to make xhs-page-*.png / xhs-pages.yaml the primary publishing artifact, and mark AI cover/content images as optional supplements.

The registry is documented as the single source of truth, but it still says XHS uses xhs-cover.png plus 2-3 content images. Current publishing behavior in scripts/post-publish/gen_xhs_pages.py generates ongoing/<slug>/images/xhs-page-01.png... and xhs-pages.yaml, with page 1 as the title card. Docs that defer to the registry will keep planning and reviewing obsolete XHS covers.

---

### [SR-20260708-062] [HIGH] templates/xiaohongshu.md — The XHS template says the new text-card carousel replaces the AI cover, but its checklist still requires an old-style cover and 1-2 image refs from images.md.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Rewrite the XHS generation checklist around plain body text plus optional supplemental images, and remove the hard requirement for a cover entry in images.md. Add a publish-time requirement to run gen_xhs_pages.py.

The middle of the template correctly says gen_xhs_pages.py now renders the main carousel and no separate AI cover is needed. Later, the final checklist still requires 配图清单 present at end: 封面（3:4）+ 1-2 配图 with markdown image paths. That sends writers back to the old workflow and conflicts with the actual publish script.

---

### [SR-20260708-063] [MEDIUM] .claude/skills/post-new/07-images.md — Image planning still mandates an XHS AI cover even though XHS publishing now derives the title card from the article.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove the XHS cover entry from the mandatory manifest template, or clearly mark it as optional supplemental media. Mention that XHS primary cards are generated during /post-publish by gen_xhs_pages.py.

The manifest template includes 小红书 Cover (xhs-cover) and Phase 2 says to generate covers for all target platforms. That is stale against the new XHS publish behavior, where the primary carousel is generated deterministically from xiaohongshu.md and the H1 title.

---

### [SR-20260708-064] [MEDIUM] .claude/skills/post-review/05-images.md — The review checklist still reviews XHS cover prompts, not the actual primary XHS carousel artifacts.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add XHS-specific review guidance: either review the article text for later card rendering before publish, or require publish-time inspection of generated xhs-page-*.png and xhs-pages.yaml. Stop treating xhs-cover freshness as the primary XHS image risk.

The current image review checks cover-hook freshness and aspect ratios from images.md. For XHS, the primary user-visible images are now generated later by gen_xhs_pages.py, so this review can pass while the actual carousel is never inspected for overflow, bad pagination, font fallback, or stale generated YAML.

---

### [SR-20260708-065] [MEDIUM] .claude/skills/post-publish/SKILL.md — The publish skill claims platform metadata lives in _platforms/<platform>.md, but XHS hard limits and publish URLs are actually split across _platforms, the registry, and scripts.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make SKILL.md explicit that _platforms is a routing/checklist file and templates/_platform-registry.md is authoritative for limits/URLs; require running the relevant validation script before clipboard/browser steps.

SKILL.md says per-platform metadata such as publish URL and cover specs lives in _platforms/<platform>.md. The XHS platform file immediately delegates publish URL and limits to templates/_platform-registry.md, while enforcement depends on char_count.py and generation depends on gen_xhs_pages.py. The map understates the files needed for a correct publish.

---

### [SR-20260708-066] [LOW] templates/_writing-craft.md — The Section Index contains at least one broken/self-inconsistent anchor for the Chinese identity section.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Replace #我-as-subject with the actual generated Markdown anchor, or add explicit HTML anchors before each section and point the index to those stable IDs.

The index lists #我-as-subject for the heading ## 「我」as Subject — Identity Consistency. Standard Markdown anchor generation will not produce that exact anchor because the heading includes Chinese brackets and additional words. Templates tell writers to use this index, so the link is unreliable.

---

### [SR-20260708-067] [LOW] README.md — The dependency links for takeover and sharp-review point to the Claude Code repo, not the actual plugin/project locations.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Replace those URLs with the real plugin repository or local plugin documentation links, or remove the links if they are internal cc-market dependencies.

README lists takeover and sharp-review as cc-market plugin dependencies, but both links go to https://github.com/anthropics/claude-code. That is not a useful reference for installing or understanding those plugins.


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-068] [HIGH] .claude/skills/post-new/07-images.md — 小红书图片规划仍要求生成 xhs-cover AI 封面，和新的 gen_xhs_pages.py 发布流程冲突。

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 把小红书 cover 从 mandatory cover manifest 中移除，改成“发布期由 gen_xhs_pages.py 生成 xhs-page-01 标题卡；AI 图片只作为可选补充”。同步更新 Summary 示例。

当前 07-images.md 的 manifest 模板仍包含 `### 小红书 Cover (xhs-cover)`、`xhs-cover-v1.png` 和 Summary 中的小红书 cover。实际新脚本 scripts/post-publish/gen_xhs_pages.py 会从最终 xiaohongshu.md 生成 `images/xhs-page-01.png` 作为标题卡/封面，post-publish/_platforms/xiaohongshu.md 也说明不再需要 AI 封面。上游继续要求 xhs-cover 会制造多余产物，并让 writers/reviewers 继续围绕旧封面工作。

---

### [SR-20260708-069] [MEDIUM] templates/_platform-registry.md — 小红书图片元数据仍是旧的封面/内容图模型，没有反映分页文字卡是主体轮图。

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 更新 xiaohongshu 的 Cover Image Conventions 和 Content Image Conventions：cover filename 应指向 `xhs-page-01.png` 或标注脚本生成；content count/types 应说明 `xhs-page-*.png` 是主轮图，AI/真实截图为可选补充。

registry 仍写 `xhs-cover.png`，设计说明是 Hook text overlaid/dark saturated bg；Content Image Conventions 仍写 xiaohongshu count 2-3。实际发布脚本生成 `xhs-page-01.png ... xhs-page-NN.png`，且 xiaohongshu 平台文档说主体轮图是脚本生成的分页文字卡，AI 补充图可选。作为 SSOT 的 registry 现在会把其他文档/agent 拉回旧规则。

---

### [SR-20260708-070] [MEDIUM] templates/xiaohongshu.md — 模板内部一边说不需要 AI 封面，一边仍要求文末封面清单使用 xhs-cover-vN.png。

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 删掉或降级旧“封面图单独设计”硬性要求；示例和 checklist 改为脚本标题卡 `xhs-page-01.png`，补充图清单可空或只列真实/AI 补充图。

templates/xiaohongshu.md 已新增说明：发布期脚本会渲染分页文字卡，第 1 张即标题卡/封面，`images.md` 可空或只列补充图。但同一文件后面仍有 `封面图设计规范`、示例 `xhs-cover-v1.png`，Generation Checklist 仍要求“配图清单 present at end: 封面 + 1-2 配图”。这会让 writer 输出旧式配图清单，和发布期脚本生成的实际轮图重复。

---

### [SR-20260708-071] [MEDIUM] .claude/rules/MEMORY.md — Memory 文档引用的维护脚本在当前仓库不存在。

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 要么把这些命令改成实际可用的 rem/task-engine/plugin 命令，要么把脚本加入 repo。不要在项目规则里列不可执行维护命令。

MEMORY.md 指示运行 `node scripts/touch-memory.js`, `node scripts/prune-memory.js`, `node scripts/crystallize.js`。当前 repo 的 scripts/ 下只有 post-publish helper；这三个文件均不存在。按文档执行会直接失败。

---

### [SR-20260708-072] [LOW] README.md — README 的 pipeline 用法仍把 /post-new 参数写成 github-url 或 local-path，漏掉 research-report 和 resume slug。

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 把 pipeline 示例改成和 Commands 表一致：`/post-new <github-url|local-path|research-report-file|slug> [platform]`，并简短说明 local file is treated as a research report。

README 顶部描述和 Commands 表已经提到 GitHub repo、local codebase、research-report file、resume by slug；但 Pipeline 代码块仍写 `/post-new <github-url|local-path> [platform]`。这对近期新增的 research-report source 和 slug resume 是过时入口说明。

---

### [SR-20260708-073] [LOW] AGENT.md — AGENT.md 引用 `post-new/SKILL.md`，当前仓库没有这个路径。

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** 改为 `.claude/skills/post-new/SKILL.md` 或明确这是 slash-command shorthand 而不是文件路径。

AGENT.md 的 Slug 段写 “See `post-new/SKILL.md` ## Slug”。当前实际文件是 `.claude/skills/post-new/SKILL.md`，repo 根下不存在 `post-new/SKILL.md`。作为文档文件引用，这是断链。


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-074] [HIGH] templates/xiaohongshu.md — Xiaohongshu generation checklist still requires the old AI-cover/images.md flow even though publishing now uses script-generated text cards.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Replace the mandatory cover + 1-2 image checklist with the new required output: run gen_xhs_pages.py, inspect xhs-page-*.png, and treat images.md AI supplements as optional only.

Confirmed mismatch: scripts/post-publish/gen_xhs_pages.py creates ongoing/<slug>/images/xhs-page-01.png... and xhs-pages.yaml from the latest xiaohongshu.md; .claude/skills/post-publish/_platforms/xiaohongshu.md says the title card is the cover and AI supplements are optional. But templates/xiaohongshu.md still says the final checklist requires a 配图清单 with 封面(3:4) + 1-2 配图, each from images.md, and earlier examples still point to ../../images/xhs-cover-vN.png.

---

### [SR-20260708-075] [HIGH] .claude/skills/post-new/07-images.md — The image-planning step still mandates an xhs-cover AI image that the new publish flow explicitly no longer needs.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the manifest template and image generation batches so Xiaohongshu does not plan or generate xhs-cover by default; document optional supplemental images only, with the text-card carousel generated at post-publish time.

Confirmed mismatch: 07-images.md contains a required Platform-Specific Images section for 小红书 Cover (xhs-cover) with path ../../images/xhs-cover-v1.png and the summary table lists xhs-cover-v1.png. The actual new script generates xhs-page-01.png as the title/cover card, and _platforms/xiaohongshu.md says no AI cover is needed because the title card is rendered by the script.

---

### [SR-20260708-076] [MEDIUM] templates/_platform-registry.md — The registry's Xiaohongshu cover convention is stale and conflicts with the new generated-card cover.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the Xiaohongshu cover convention from xhs-cover.png AI cover guidance to xhs-page-01.png generated title card guidance, or explicitly mark xhs-cover as optional supplemental legacy/extra art.

Confirmed mismatch: templates/_platform-registry.md declares itself the single source of truth and lists Xiaohongshu cover filename as xhs-cover.png with hook-text AI-cover design notes. The current code path in gen_xhs_pages.py always writes xhs-page-01.png as page 1, while the platform publish rules say xhs-page-01 is the title card and upload order starts with it.

---

### [SR-20260708-077] [MEDIUM] .claude/skills/post-review/05-images.md — Image review still treats cover prompt freshness as mandatory for every platform, which is wrong for Xiaohongshu after scripted title-card generation.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split Xiaohongshu review rules from AI image manifest review: verify xhs-pages.yaml/xhs-page-*.png after generation, and only review images.md cover prompts for platforms that still use AI covers.

Confirmed mismatch: post-review/05-images.md requires checking cover image prompts against titles and lists Xiaohongshu cover aspect ratio 3:4. That made sense for xhs-cover-vN.png, but the current Xiaohongshu cover is generated from the H1 by gen_xhs_pages.py, not described by an AI prompt in images.md.

---

### [SR-20260708-078] [LOW] .claude/skills/post-publish/_platforms/xiaohongshu.md — The documented editable YAML fields are incomplete compared with the generated config.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document all supported config knobs that the script writes and consumes, especially page_number, para_spacing, title, body min_size/max_size, and per-page max_size behavior.

Confirmed mismatch: _platforms/xiaohongshu.md says xhs-pages.yaml supports per-page text/size/color/background/align/bold and global canvas/margin/line_spacing/fonts. gen_xhs_pages.py also creates and reads para_spacing, page_number, title settings, body min_size/max_size, and page-level max_size handling. Users editing the YAML are not told these supported controls exist.


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-079] [HIGH] templates/xiaohongshu.md — Xiaohongshu template still requires the old AI cover/image-list workflow even though publishing now uses script-generated text cards.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Rewrite the XHS cover/content-image sections and final checklist around the current lifecycle: draft plain text, optional supplemental images only, and `/post-publish` generates `xhs-page-*.png`. Remove required `xhs-cover-vN.png` and required 1-2 image refs from `images.md`.

The template says `gen_xhs_pages.py` now renders the primary carousel and page 1 is the title/cover card, but later sections still say the cover must be separately designed, output as `xhs-cover-vN.png`, and listed in a final `## 配图` block. The Generation Checklist still requires `封面（3:4）+ 1-2 配图` with markdown refs from `images.md`. That directly conflicts with the new script behavior, which stops before the 配图 manifest and emits `ongoing/<slug>/images/xhs-page-01.png...`.

---

### [SR-20260708-080] [HIGH] .claude/skills/post-new/07-images.md — Image planning still mandates a Xiaohongshu AI cover that the new publish flow no longer uses.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove the mandatory `小红书 Cover (xhs-cover)` manifest entry and skip XHS in Batch 1 cover generation, or mark it as optional supplemental art. Document that the XHS cover/title card is generated by `scripts/post-publish/gen_xhs_pages.py` during publishing.

The manifest template includes `小红书 Cover (xhs-cover)` with path `../../images/xhs-cover-v1.png`, and Phase 2 says to generate covers for all platforms. Current code generates `xhs-page-01.png` from the H1 as the title/cover card, while `_platforms/xiaohongshu.md` says AI cover is no longer needed. Following this doc wastes image generation and keeps drafts anchored to the removed cover workflow.

---

### [SR-20260708-081] [MEDIUM] templates/_platform-registry.md — The platform registry is stale for Xiaohongshu and will pull other docs back to the old cover/image model.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the XHS cover convention to `xhs-page-01.png` or explicitly mark `xhs-cover.png` as optional legacy/extra art. Change content image count from required-looking `2-3` to optional supplements, with `xhs-page-*.png` as the primary carousel output.

This file declares itself the single source of truth. It still lists Xiaohongshu cover filename as `xhs-cover.png` with hook-text cover design notes, and content images as `2-3`. The actual publish code writes `xhs-page-01.png ... xhs-page-NN.png`, and the platform publish rules say those text cards are the primary carousel with AI supplements optional.

---

### [SR-20260708-082] [HIGH] .claude/skills/post-publish/01-identify.md — The publish image gate can pass for Xiaohongshu before the actual carousel assets exist.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a Xiaohongshu-specific gate after or before Step 4: require `ongoing/<slug>/images/xhs-pages.yaml` and at least `xhs-page-01.png`, generated from the current final draft, then visually inspect all `xhs-page-*.png` before publish.

Step 2 only parses markdown image references from the article and checks those files. The new XHS flow intentionally keeps the body plain text and generates upload assets later as `xhs-page-*.png`, so this gate can report all images ready with zero refs while the primary carousel has not been generated at all.

---

### [SR-20260708-083] [MEDIUM] .claude/skills/post-publish/02-prepare.md — XHS generation is documented as fire-and-forget, but the generated PNGs are now the main publish artifact and need a blocking inspection loop.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** After running `gen_xhs_pages.py`, require opening/checking every generated card, editing `ongoing/<slug>/images/xhs-pages.yaml` if wrapping/style/page breaks are bad, rerunning without `--reinit`, and only then copying/opening the publish URL.

The doc mentions the editable YAML and then immediately proceeds to clipboard/browser. The script auto-packs text, auto-shrinks fonts, deletes stale cards, and depends on local fonts/emoji support. Bad pagination, fallback fonts, overlong title layout, or ugly wrapping are now the primary publish risk, not a secondary detail.

---

### [SR-20260708-084] [MEDIUM] .claude/skills/post-publish/_platforms/xiaohongshu.md — The XHS publish rules do not clearly separate caption clipboard text from upload assets.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** State explicitly that clipboard content is the caption body plus hashtags only, excluding the trailing `## 配图` manifest; upload assets are `ongoing/<slug>/images/xhs-page-*.png` plus optional supplemental images.

The file says clipboard format is plain Chinese text and image references become `[此处上传配图]`, while the generator excludes the `## 配图` manifest and renders the carousel separately. Operators need an unambiguous split between what gets copied, what gets uploaded, and which article sections the card generator ignores.

---

### [SR-20260708-085] [LOW] .claude/skills/post-publish/_platforms/xiaohongshu.md — The documented editable YAML fields are incomplete compared with what `gen_xhs_pages.py` actually supports.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document the remaining supported controls: `para_spacing`, `page_number`, `title` settings, `body.min_size`, `body.max_size`, and page-level `max_size`/`size` behavior.

The doc lists per-page `text/size/color/background/align/bold` and global `canvas/margin/line_spacing/fonts`. The generated config also includes `para_spacing`, `page_number`, title styling, body min/max sizing, and page-level max sizing. Users editing the YAML are not told these controls exist.

---

### [SR-20260708-086] [MEDIUM] .claude/skills/post-review/05-images.md — Image review still treats Xiaohongshu cover prompts as the main risk, but the live cover is script-generated from H1.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split XHS review from AI image prompt review: review optional supplemental images in `images.md`, and require publish-time inspection of `xhs-page-*.png`/`xhs-pages.yaml` for the primary carousel.

The review doc checks cover prompt/title freshness and aspect ratios from `images.md`, including Xiaohongshu cover 3:4. That matches the old `xhs-cover-vN.png` lifecycle, not the current code path where `gen_xhs_pages.py` renders the title card and body cards after review.

---

### [SR-20260708-087] [MEDIUM] README.md — Project prerequisites omit the Python dependencies now required for Xiaohongshu publishing.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a setup line such as `pip install -r scripts/post-publish/requirements.txt`, and name `Pillow`/`PyYAML` for XHS text-card generation plus `python-docx` for WeChat/Zhihu export.

`scripts/post-publish/requirements.txt` now includes `Pillow>=10.0`, `PyYAML>=6.0`, and `python-docx==1.1.2`. `gen_xhs_pages.py` exits without PyYAML/Pillow. The skill has an internal pre-check, but README prerequisites only mention Codex CLI/image generation, so fresh setup docs are incomplete.


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-088] [HIGH] .claude/skills/post-new/07-images.md — 小红书 image planning still mandates the old AI `xhs-cover` workflow even though the current publish code generates the cover/title card as `xhs-page-01.png`.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove the mandatory `小红书 Cover (xhs-cover)` manifest entry and skip Xiaohongshu in Batch 1 cover generation, or mark it as optional supplemental art. Document that the required XHS carousel is generated by `scripts/post-publish/gen_xhs_pages.py` during publish.

The manifest template lists `### 小红书 Cover (xhs-cover)` with path `../../images/xhs-cover-v1.png`, the Summary table lists `xhs-cover-v1.png`, and Batch 1 says to generate covers for all target platforms. But `gen_xhs_pages.py` writes `ongoing/<slug>/images/xhs-page-01.png` as the title/cover card, and the XHS publish rules say AI cover is no longer needed. Following this doc creates obsolete assets and keeps upstream review/generation focused on the wrong artifact.

---

### [SR-20260708-089] [HIGH] templates/xiaohongshu.md — The Xiaohongshu template contradicts itself: it mentions generated text cards, then still requires a separate `xhs-cover-vN.png` and mandatory image manifest entries.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Rewrite the cover/content-image sections and final checklist around the current lifecycle: draft plain text, optional supplemental images only, `/post-publish` generates `xhs-page-*.png`, and `xhs-page-01.png` is the cover/title card.

The template correctly notes that `gen_xhs_pages.py` now renders the primary carousel and page 1 is the title card/cover. Later sections still say the cover must be separately designed, output as `xhs-cover-vN.png`, and listed in the final `## 配图` block. The example and checklist still require `封面（3:4）+ 1-2 配图` with markdown refs from `images.md`. That conflicts with the script, which ignores the trailing 配图 manifest and emits `xhs-page-01.png ... xhs-page-NN.png` from the article body.

---

### [SR-20260708-090] [MEDIUM] templates/_platform-registry.md — The registry is stale for Xiaohongshu and will pull other docs back to the old cover/content-image model.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the Xiaohongshu cover convention from `xhs-cover.png` to generated `xhs-page-01.png`, and change content image guidance to say `xhs-page-*.png` is the primary carousel while screenshots/AI images are optional supplements.

This file declares itself the single source of truth. It still lists Xiaohongshu cover filename as `xhs-cover.png` with hook-text/dark-cover design notes, and content images as `2-3`. Current code writes `xhs-page-01.png ... xhs-page-NN.png`, and `.claude/skills/post-publish/_platforms/xiaohongshu.md` says those generated text cards are the primary carousel with AI supplements optional.

---

### [SR-20260708-091] [MEDIUM] .claude/skills/post-publish/01-identify.md — The publish-time image gate does not validate Xiaohongshu's required generated carousel assets.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a Xiaohongshu-specific gate after running `gen_xhs_pages.py`: require `ongoing/<slug>/images/xhs-pages.yaml` and at least `xhs-page-01.png`, verify all `xhs-page-*.png` exist, and require visual inspection before opening the publish URL.

Step 2 only parses markdown image references like `![alt](../../images/<image-id>-v<N>.png)`. The new XHS flow intentionally keeps the body plain text and generates upload assets later as `xhs-page-*.png`, so this gate can report images ready with zero refs while the primary carousel has not been generated or checked.

---

### [SR-20260708-092] [MEDIUM] .claude/skills/post-review/05-images.md — Image review still treats Xiaohongshu as an AI cover prompt workflow, not a script-generated title-card workflow.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split Xiaohongshu review from AI image prompt review: review optional supplemental images in `images.md`, and require publish-time inspection of `xhs-page-*.png`/`xhs-pages.yaml` for the primary carousel.

The review doc checks cover prompt/title freshness and aspect ratios from `images.md`, including Xiaohongshu cover 3:4. That matched the old `xhs-cover-vN.png` lifecycle. The current Xiaohongshu cover is generated from the H1 by `gen_xhs_pages.py`, so there may be no AI prompt to review and no `xhs-cover` file at all.

---

### [SR-20260708-093] [MEDIUM] README.md — Fresh setup docs omit the Python dependencies required by the current publish scripts.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a setup line such as `pip install -r scripts/post-publish/requirements.txt`, naming `Pillow`/`PyYAML` for Xiaohongshu text-card generation and `python-docx` for WeChat/Zhihu export.

`scripts/post-publish/requirements.txt` now includes `python-docx==1.1.2`, `Pillow>=10.0`, and `PyYAML>=6.0`. `gen_xhs_pages.py` exits if PyYAML is missing and imports Pillow unconditionally. The skill has an internal pre-check, but README prerequisites only mention Codex CLI/image generation, so a fresh user following repo setup docs will miss required Python packages.

---

### [SR-20260708-094] [LOW] .claude/skills/post-publish/_platforms/xiaohongshu.md — The documented editable `xhs-pages.yaml` fields are incomplete compared with what `gen_xhs_pages.py` actually supports.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document all supported YAML controls, including `para_spacing`, `page_number`, `title` settings, `body.min_size`, `body.max_size`, page-level `max_size`, and page-level `bold`.

The platform doc lists per-page `text` / `size` / `color` / `background` / `align` / `bold` and global `canvas` / `margin` / `line_spacing` / `fonts`. The script also creates and reads `para_spacing`, `page_number`, `title`, `body.min_size`, `body.max_size`, and page-level `max_size`. Users editing layout will not know these supported controls exist.

---

### [SR-20260708-095] [LOW] templates/_writing-craft.md — The Section Index has an unreliable anchor for the Chinese identity section.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add explicit HTML anchors before sections or replace `#我-as-subject` with the actual generated Markdown anchor used by the renderer.

The index lists `#我-as-subject` for heading `## 「我」as Subject — Identity Consistency`. Standard Markdown anchor generation usually incorporates punctuation/removes symbols differently and includes more of the heading text, so this internal reference is likely broken or renderer-dependent.


## Review 2026-07-08 (follow-up)

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260708-096] [HIGH] templates/xiaohongshu.md — Xiaohongshu generation checklist still requires an old cover/content image manifest even though publishing now uses gen_xhs_pages.py text cards as the primary carousel.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make the trailing image list optional for AI supplements only, and stop requiring xhs-cover-vN.png or 1-2 content images for every Xiaohongshu final.

The template correctly notes that gen_xhs_pages.py now renders the title card and body cards from xiaohongshu.md, but later sections still require a final image list with a cover and 1-2 images from images.md. That conflicts with scripts/post-publish/gen_xhs_pages.py, which creates ongoing/<slug>/images/xhs-page-*.png and xhs-pages.yaml from the article body and does not consume images.md or xhs-cover-vN.png.

---

### [SR-20260708-097] [HIGH] .claude/skills/post-new/07-images.md — The image manifest playbook still plans an AI Xiaohongshu cover that the current publish flow no longer needs.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove the mandatory xhs-cover manifest entry or mark it as optional supplemental art; document that gen_xhs_pages.py supplies the Xiaohongshu title card at publish time.

The manifest template includes a Platform-Specific Images section for 小红书 Cover (xhs-cover) with an AI Prompt and path ../../images/xhs-cover-v1.png. The current publish script generates xhs-page-01.png as the title/cover card from the H1, and the Xiaohongshu platform publish doc says the main carousel is script-generated text cards, not AI cover art.

---

### [SR-20260708-098] [MEDIUM] templates/_platform-registry.md — The registry still describes Xiaohongshu content images as 2-3 conventional images instead of script-generated text-card pages.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the Xiaohongshu cover/content image conventions to name xhs-page-*.png as the primary carousel and AI/real screenshots as optional supplements.

This file claims to be the single source of truth for platform metadata, but its Cover Image Conventions still lists xhs-cover.png and Content Image Conventions still says Xiaohongshu has 2-3 images. The current code path is scripts/post-publish/gen_xhs_pages.py, which produces an arbitrary number of xhs-page-*.png cards plus xhs-pages.yaml.

---

### [SR-20260708-099] [MEDIUM] .claude/skills/post-review/05-images.md — Image review instructions still require Xiaohongshu cover checks that are stale under the text-card publish flow.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the Xiaohongshu review checklist to inspect xhs-pages.yaml/xhs-page-*.png when generated, and treat AI cover prompt review as optional only when an AI cover exists.

The review phase tells reviewers to verify Xiaohongshu cover aspect ratio and cover prompt/title matching. gen_xhs_pages.py does not use an AI prompt or xhs-cover file for the primary cover; it renders the H1 into xhs-page-01.png. Keeping this as mandatory makes reviewers chase an artifact that may correctly not exist.

---

### [SR-20260708-100] [MEDIUM] AGENT.md — The documentation claims templates/registry are the single source of truth, but platform limits are duplicated in executable code.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either document char_count.py as a duplicated enforcement point that must be kept in sync, or change the script/docs to load limits from templates/_platform-registry.md.

AGENT.md says templates and shared reference files are the single source of truth. In reality, scripts/post-publish/char_count.py hardcodes LIMITS for xiaohongshu title/caption, wechat summary, and twitter tweet length instead of reading templates/_platform-registry.md. The current values may align, but the SSOT claim is false against the actual code.

---

### [SR-20260708-101] [MEDIUM] README.md — README dependency setup omits the Python packages required by the post-publish scripts.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a Python publishing dependency note: pip install -r scripts/post-publish/requirements.txt for python-docx, Pillow, and PyYAML.

README lists takeover, sharp-review, and Codex CLI, but the documented /post-publish flow depends on scripts/post-publish/export_article.py and gen_xhs_pages.py. Those require python-docx, Pillow, and PyYAML from scripts/post-publish/requirements.txt; the setup docs do not mention installing them.

---

### [SR-20260708-102] [LOW] AGENT.md — The slug section links to post-new/SKILL.md, but that path does not exist at the repository root.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the reference to .claude/skills/post-new/SKILL.md ## Slug.

AGENT.md says 'See post-new/SKILL.md ## Slug.' The actual file is .claude/skills/post-new/SKILL.md. As written, the cross-reference is a broken path for anyone navigating the repository directly.
