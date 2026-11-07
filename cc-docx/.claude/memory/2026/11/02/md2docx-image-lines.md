---
name: md2docx-image-lines
description: "md2docx inserts pictures from ![caption](path) lines"
metadata:
  type: project
---

md2docx.py now supports unanchored lines made only of ![caption](path) tokens: inserts one centred picture paragraph, multiple images share text width, paths relative to the md, missing file raises. In track mode each picture run is wrapped in w:ins, so python-docx inline_shapes does not see them; tests count .//w:drawing instead. docx2md does not transcribe pictures back, so re-extract diffs drop those lines. Added for IEMDC 2027 tutorial form (2026-11-02); uncommitted at session end.
