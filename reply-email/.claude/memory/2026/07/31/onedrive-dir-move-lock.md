# OneDrive locks `ongoing/` dirs on archive move (2026-07-31)

When archiving, `mv ongoing/<topic> archived/...` can fail with `Device or resource busy` —
OneDrive sync holds a handle on the directory while it scans the new files.

**Workaround:** `cp -r ongoing/<topic> <archive-path>` first (this succeeds), verify the copy,
then `rm -rf ongoing/<topic>`. The rm may still fail on the now-empty directory shell while
OneDrive holds it; retry later or leave the empty dir — it contains no data.

**Why:** All archive data lived safely in the copied destination; only the empty source shell
was stuck. No data-loss risk, just cosmetic litter in `ongoing/`.

**Scope:** Applies to any file moves within the OneDrive-synced repo root (`Sync/agents/...`),
not just archiving.
