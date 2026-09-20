---
name: onedrive-dir-move-lock
description: "Moving a round out of ongoing/ into archived/ fails with 'Device or resource busy' under OneDrive — copy, verify with diff -r, then remove"
metadata:
  type: project
---

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

---

**Recurrence 2026-09-20** (archiving `jmag-user-conference-2026`): identical failure, identical
workaround — `mv` → `Device or resource busy`, `cp -r` + `diff -r` verification + `rm -rf` →
clean. So this is the normal path, not an occasional glitch: expect the `mv` to fail and go
straight to copy-verify-remove.

Two refinements learned:

- **The harness's own working directory is a contributing cause.** When the session cwd is
  *inside* the directory being moved, the move fails even before OneDrive's scan enters the
  picture. `cd` out of the source directory (to the repo root) before attempting the move.
- **`rm -rf` on the source may be permission-denied** by the harness's own tooling rather than by
  OneDrive, leaving full duplicate copies of the round in `ongoing/`. The archive is already
  complete and verified at that point, so the duplicates are harmless litter — but flag them to
  the user rather than retrying the denied command verbatim.
