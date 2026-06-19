# 04 — Cleanup, Postmortem & Report

## Step 7: Clean Up Cached Repo & Drop `ongoing/<slug>`

The clone cache is keyed on `<repo-slug>` (= `<slug>` with any `__<topic>` suffix stripped) and is **shared across every article from that repo**. Only delete it when no other article still needs it.

```bash
repo_slug="${slug%%__*}"   # strip the __<topic> suffix, if any
# Are there OTHER ongoing or archived articles from the same repo?
others=$( (ls -d ongoing/"$repo_slug"* archived/*/"$repo_slug"* 2>/dev/null) | grep -v "/$slug\$\|/$slug/" )
if [ -z "$others" ]; then
  rm -rf "repos/$repo_slug"
  echo "🗑️ 已清理：repos/$repo_slug"
else
  echo "↩️ 保留 repos/$repo_slug（仍有其他文章使用同一仓库克隆）"
fi

# FINAL destructive cleanup — deferred from Step 3 until every read from the
# 2-draft/vN version chain (Steps 3–6) has completed. This MUST be the last action.
rm -rf "ongoing/<slug>"
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
