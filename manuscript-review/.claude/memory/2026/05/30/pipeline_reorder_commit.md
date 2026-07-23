---
name: pipeline-reorder-language-step
description: Pipeline reordered — literature before consensus, new 00-language step, venue-calibrated gaps, standardized critique format
metadata:
  type: project
---

Pipeline restructured in 9ff0881 (2026-05-30). 20 files, +201/−97.

**Why:** The old ordering (consensus before literature) meant the summary couldn't reference the research landscape. Literature now runs first so consensus can fold in positioning and author background. Language selection was implicit — now explicit at step 00.

**Changes:**
- **Step reorder**: `02-consensus` → deleted; `02b-literature` → `02-literature` (now step 02); new `02b-consensus` (now step 02b, runs after literature)
- **New 00-language step**: user picks `en`/`zh` for intermediate files stored in `review-config.md`; `final.md` always English
- **Venue-calibrated Obvious gaps**: EE conference papers (electric machines, power electronics, drives) — no hardware/code/data expectations. Journal papers (IEEE Transactions) — experimental validation is expected.
- **Critique format standardization**: numbered points (1, 2, 3…) in descending severity (Major → Minor → Nit); header format `## <N> · <short claim>`
- **Figure-extraction caveat**: reviewers warned that image rendering flaws may be extraction artifacts; cite exact image path, cap severity at minor
- **Rerun skill updates**: step matching by exact token (`2` ≠ `02b`); archived path convention `archived/YYMMDD/<slug>/`
- **AGENT.md architecture diagram**: reflects new 00–08 numbering

**Validation:** No tests run — the commit captured pre-staged changes from a prior session. The edits are purely markdown/config; no code paths changed.

**How to apply:** Existing `ongoing/` runs that completed step 02 under the old numbering have `summary.md` but no `literature.md`. Re-running `/manuscript-review:new <slug>` will resume correctly — step 02 will generate `literature.md` fresh, step 02b will detect existing `summary.md` and offer to keep or regenerate. The two-step split (`2` vs `2b`) in the rerun skill avoids ambiguity.
