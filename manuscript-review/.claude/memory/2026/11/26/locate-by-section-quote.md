---
name: locate-evidence-by-section-and-quote
created: 2026-11-26
accessed: 2026-11-26
access_count: 1
tier: long
---

# Locate review evidence by page + section + verbatim quote, never by line numbers

User correction during ieee-sensors-261119 (IEEE Sensors Journal, colleague's paper):
"第 9 页第 24–28 行" style is bad. Always write: 第 X 页 Section Y（章节名）"原句" —
in English final: Page X, Section Y (Title) states: "<verbatim sentence>".
Applies to draft.md AND final.md from the first draft onward. Verify each quote verbatim
against the PDF text (hyphenated line breaks cause false misses).

Other learnings from this run:
- tone: friendly → Minor Revision, every costly ask gets a "if not feasible, narrow claims" fallback.
- External citation check found real errors (mis-cited Informer, Dropout cited for ConvNeXt-1D,
  unlocatable 2027 ref) — new `reference-integrity` angle.
- Plugin issues (fix in cc-academia source, not yet done): ingest breaks on paths with spaces and
  writes to ~/cc-academia-data when run elsewhere; fanout script's `import` from node:crypto is
  rejected by Workflow runtime; fanout agentType `reviewer-<angle>` does not match
  `manuscript-reviewer-<angle>`; polisher agent not registered.
- ScholarOne Sensors form: "Suggested references" textarea is required — fill "None." if none.
- Archive on OneDrive: mv denied; PowerShell robocopy /E /MOVE works (rc=1 = OK).
