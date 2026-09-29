---
name: cc-slides-plan
description: "cc-slides harness implemented (PPTX, PowerPoint renderer)"
metadata:
  type: project
---

cc-slides/ implemented 2026-09-30 (skill /slides, Codex $slides). Scripts: inspect_slides, build_slides (deck.toml: template, base, [patterns.x] slide/static, [[slides]] keep|pattern+title/images/texts/tables/notes; fits contain/cover/stretch; unfilled slots dropped), lint_slides, preview_slides (PowerPoint PDF -> Ghostscript PNG + contact.png), to_pdf, slides2md/md2slides (anchors <!-- s<slide_id>/<shape_id> -->). Tests: unittest, synthetic fixtures; CC_SLIDES_POWERPOINT=1 for real PowerPoint. PowerPoint mac gotchas: sandbox (stage in ~/Library/Containers/com.microsoft.Powerpoint/Data/tmp/cc-slides/<token>/ with unique filename), scripted open -> -9074 (use open -g -a), save as PNG writes nothing, no 'whose' filter (-1750). workspace linked to agent-data/cc-slides (link-agent-data.sh mapping + root .gitignore entry for symlink). First task: workspace/ongoing/260930-byd-map-fill (6 three-up slides, verified via contact sheet).
