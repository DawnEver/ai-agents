# 04 — Cleanup, Postmortem & Report

## Step 7: Clean Up Cached Source & Drop `ongoing/<slug>`

The source cache is keyed on `<repo-slug>` (= `<slug>` with any `__<topic>` suffix stripped) and is
**shared across every article from that source**. It holds either a **clone** (`repos/<repo-slug>/`,
a github source) or a **one-line pointer** (`repos/<repo-slug>.src`, a local-dir source). A
`local-file` research report leaves nothing under `repos/`. Only delete when no other article needs it.

**Never delete the pointed-to path.** For a local-dir/local-file source, the material lives at an
external path the user owns — cleanup removes only the *clone* or the *pointer file*, never the target.

```bash
repo_slug="${slug%%__*}"   # strip the __<topic> suffix, if any
# Are there OTHER ongoing or archived articles from the same source?
# Match on a real slug boundary (exact repo_slug or repo_slug__<topic>) — a bare
# prefix glob would over-match siblings (foo matching foo-bar), and comparing by
# exact string avoids feeding the slug (which may contain regex-special '.') to grep.
others=""
for d in ongoing/"$repo_slug"* archived/*/"$repo_slug"*; do
  [ -e "$d" ] || continue
  name="${d##*/}"
  case "$name" in
    "$slug") continue ;;                       # the article we're archiving — skip
    "$repo_slug" | "$repo_slug"__*) others="$d" ; break ;;
  esac
done
if [ -z "$others" ]; then
  # Guard: only ever remove a real clone dir or the pointer file — never follow a
  # symlink out to user-owned material (a local source lives at an external path).
  [ -L "repos/$repo_slug" ] && { echo "⚠️ repos/$repo_slug 是符号链接，跳过删除以保护外部源"; } || rm -rf "repos/$repo_slug"
  rm -f "repos/$repo_slug.src"       # local-dir/local-file pointer, if any — the pointer ONLY, not its target
  echo "🗑️ 已清理：repos/$repo_slug（克隆/指针；外部源路径不动）"
else
  echo "↩️ 保留 repos/$repo_slug（仍有其他文章使用同一来源）"
fi

# FINAL destructive cleanup — deferred from Step 3 until every read from the
# 2-draft/vN version chain (Steps 3–6) has completed. This MUST be the last action.
rm -rf "ongoing/$slug"
```

The frozen archive at `archived/YYMMDD/<slug>/` is never deleted.

## Step 8: Offer Postmortem (Optional)

> Want to score each article's AI味 and reader reception? This helps calibrate future generation.

If yes, create `archived/YYMMDD/<slug>/postmortem.md`:
```markdown
# Postmortem — <slug>

## Per-Platform Scores
<!-- One row per ACTIVE platform from brief.md (not all four). E.g.: -->
- 小红书: AI味 🟢/🟡/🔴 | 读者反馈: <notes>
- 微信公众号: AI味 🟢/🟡/🔴 | 读者反馈: <notes>
- 知乎: AI味 🟢/🟡/🔴 | 读者反馈: <notes>
- Twitter/X: AI味 🟢/🟡/🔴 | 读者反馈: <notes>

## Lessons
- <what worked, what didn't, what to try next time>
```

## Step 9: Report

```
📦 已归档 — archived/<YYMMDD>/<slug>/

🎨 风格积累：
  - 开头: <added or "已存在，跳过">
  - 结尾: <added or "已存在，跳过">
  - 语气标记: <N added, M skipped>

<clone-cleanup line from Step 7: 🗑️ 已清理 repos/<repo-slug>  OR  ↩️ 保留 repos/<repo-slug>>

📊 Style profile — <N> articles accumulated.
```
