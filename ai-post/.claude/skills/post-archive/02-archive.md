# 02 — Assemble Final & Move to Archive

## Step 3: Assemble Final & Move to Archive

First, assemble the final version set by walking the version chain for each platform and images.md. Then create the curated archive per the **Archive contract** in SKILL.md:

```
archived/YYMMDD/<slug>/
  1-research/          ← preserved from ongoing (analysis, brief, market research)
  xiaohongshu.md       ← final assembled version
  wechat.md            ← final assembled version
  zhihu.md             ← final assembled version
  twitter.md           ← final assembled version
  images.md            ← final assembled version
  images/              ← only the -v<N> image files referenced by the finals
  review-verdict.md    ← latest 2-draft/vN/review-verdict.md (audit record)
  <title>.docx         ← exported Word file (named after the article H1), if /post-publish produced one
```

Archive structure is flat: `1-research/` plus the final articles at root level, with the review verdict and any exported `.docx` kept as audit/output artifacts. The raw `2-draft/vN/` revision chain is NOT preserved — only the assembled final output (plus verdict and docx) survives.

> **Ordering (critical):** This step only COPIES out of the version chain — it must NOT delete `ongoing/<slug>` yet. Step 4 (style/published assembly) and Steps 5–6 (fingerprint extraction) still read `2-draft/vN/`. The destructive `rm -rf "ongoing/<slug>"` cleanup is deferred to Step 7, AFTER every read from the version chain has completed.

```bash
mkdir -p "archived/$(date +%y%m%d)/<slug>/1-research" "archived/$(date +%y%m%d)/<slug>/images"
# Copy research notes
cp -r "ongoing/<slug>/1-research/"* "archived/$(date +%y%m%d)/<slug>/1-research/"
# Copy assembled final articles (one per platform, walk version chain)
cp "<assembled final>" "archived/$(date +%y%m%d)/<slug>/<platform>.md"
# Copy only images referenced by final articles (parse src from all final platform files)
# Do NOT copy all of images/ — only the specific -v<N> files actually used
cp "<only referenced images>" "archived/$(date +%y%m%d)/<slug>/images/"
# Copy the latest review verdict (walk back the version chain to find it)
cp "<latest review-verdict.md>" "archived/$(date +%y%m%d)/<slug>/review-verdict.md"
# Copy the exported Word file if /post-publish produced one.
# export_article.py names the file after the article H1 (<title>.docx), NOT the slug —
# so glob for *.docx rather than a hardcoded <slug>.docx (handles zero/one/many gracefully).
for f in ongoing/<slug>/*.docx; do [ -e "$f" ] && cp "$f" "archived/$(date +%y%m%d)/<slug>/"; done
# NOTE: do NOT remove ongoing/<slug> here. Step 4 still reads the 2-draft/vN chain for
# style extraction. The destructive `rm -rf ongoing/<slug>` is deferred to Step 7 (last).
```
