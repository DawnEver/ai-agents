# 04 — Verify (mandatory)

```bash
python3 scripts/lint_slides.py <deck.pptx>
python3 scripts/preview_slides.py <deck.pptx>     # → <deck dir>/preview/<stem>/contact.png
```

1. Lint errors (`distorted-image`, `off-slide`) must be fixed before delivery.
2. Warnings: `overlap` inherited from the user's own pattern is legitimate — mention it, don't
   rearrange their design unasked. `text-overflow` is an estimate; confirm in the preview.
3. **Read `contact.png`.** Check: every slot filled with the intended figure, titles right, nothing
   clipped, reading order sensible, footer/slide numbers present. Open single `slide-NN.png` files
   for detail.
4. Report: output path, slide count, what each slide holds, remaining warnings.

If preview fails on macOS, see "Renderer notes" in `AGENTS.md` (sandbox staging, Ghostscript).
