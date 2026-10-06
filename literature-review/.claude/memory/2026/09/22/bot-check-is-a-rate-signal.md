---
name: bot-check-is-a-rate-signal-2026-09-22
description: A fresh anti-automation challenge during batch downloading is a rate signal — stop, do not retry — and the downloader should have exposed a frequency control in the first place
metadata:
  type: engineering
---

# A bot check is a rate signal, not a failure to retry

`created: 2026-09-22, accessed: 2026-09-22`

## The sequence

An authenticated browser session that had cleared the publisher's challenge once
made automated downloads work — that is what the saved profile buys. Roughly
fifteen consecutive papers later, a **fresh challenge appeared**.

That is not a transient error. The documented worst case for this class of
defence is an IP-level ban that no session, cookie or retry recovers, and the
second challenge is the warning that precedes it — the first one having already
been cleared by a human. **The correct response is to stop the batch
immediately**, not to slow it a little and continue, and the cost of stopping is
one batch of un-downloaded items that can be resumed later.

Everything already fetched was clean: a log of fourteen rows, all successful, no
ban marker. Stopping at the warning preserved that.

## The gap this exposed

**The download command has no rate-limiting parameter at all** — no delay, no
throttle, no requests-per-minute. An operator who wants to slow down cannot,
except by hand-running the tool in small batches with pauses in between. That is
the wrong shape for a tool whose normal operation can trigger a counterparty's
anti-automation defence: the one knob most likely to be needed is the one
missing.

Worth fixing with a conservative default rather than an opt-in flag — the
operator who needs it is by definition the one who did not anticipate needing
it.

## Diagnostics that actually distinguish stalled from slow

- Output is block-buffered when redirected, so **a long silent run is not by
  itself evidence of a hang**. Do not kill on silence alone.
- **A zero-byte output file plus a browser window titled with the challenge
  interstitial means stalled.** Check the window title before waiting longer.
- Cookies for the session live at `<profile>/Default/Network/Cookies`, and that
  SQLite file is **locked while the browser is open** — so failing to copy it is
  itself proof the browser is still running. Copy it aside before reading; never
  read in place.
- A profile that a human has cleared the challenge in is the whole mechanism.
  A fresh automated browser context lands on the interstitial and waits
  indefinitely.

## The general rule

Rate limits and anti-automation defences are **feedback about pace**, and the
tooling around them must treat a challenge as a stop condition rather than an
error to retry. Retrying is what converts a stoppable warning into an
unrecoverable ban — and the ban lands on the institution's address, not on the
script.
