# 03 — Build

```bash
python3 scripts/build_slides.py <task>/deck.toml            # → <task>/out/<template-stem>-<yyMMdd>.pptx
python3 scripts/build_slides.py <task>/deck.toml <task>/out/Custom.pptx
```

- Errors are specific (slot counts, missing files, unknown pattern, out-of-range slide) — fix the
  spec, don't work around the script.
- Rebuilding the same day overwrites that day's output; if the user may have the file open in
  PowerPoint, write to a new name instead.
- Bump `iteration` in `project.toml`. Go straight to `04-verify.md`.
