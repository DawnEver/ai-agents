# 01 — Inspect the template

1. Copy the user's template into the task: `workspace/ongoing/<yyMMdd>-<slug>/src/` (never work on
   the original — it may be open in PowerPoint or synced).
2. Overview first, then the candidate pattern slides:

   ```bash
   python3 scripts/inspect_slides.py <task>/src/Template.pptx | head -40
   python3 scripts/inspect_slides.py <task>/src/Template.pptx --slides 19
   ```

3. If the user named a page ("like page 19"), that is the pattern. Otherwise preview the template
   (`preview_slides.py`) and pick by looking, not by layout names.
4. Note for each pattern: the slot labels (`title`, `image[0..]`, `text[0..]`, `table[0..]`) and
   which shapes should *not* be slots (a logo picture, a static label) → `static = [...]`.
5. Slot numbering is reading order: rows top→bottom, then left→right. A three-up with two boxes on
   top and one below is `image[0]` top-left, `image[1]` top-right, `image[2]` bottom.
