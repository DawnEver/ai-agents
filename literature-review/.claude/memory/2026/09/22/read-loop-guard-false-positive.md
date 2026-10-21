---
name: read-loop-guard-false-positive-2026-09-22
description: The read loop-guard keys on path-string similarity, so files sharing a long directory prefix trip it even on first read — and a blocked reader silently changes method
metadata:
  type: engineering
---

# The read loop-guard fires on path similarity, not on repetition

`created: 2026-09-22, accessed: 2026-09-22`

## What happened

Three separate subagents reported being blocked by the read loop-guard while
working in the same workspace. The guard reported "4–9 prior near-identical
calls" — including, in one agent's account, **on files it had never read**.

The mechanism is visible in the guard's own message: it compares the `file_path`
strings it was called with. Every file in a single workspace shares a long
directory prefix, and a batch of reads of sibling files therefore looks like
near-duplicate calls. **The guard is measuring path similarity, not semantic
repetition**, so a reader working through a directory of same-prefix files trips
it as a matter of course.

## Why this matters more than the friction

Each blocked agent fell back to a shell read and carried on — and *said so* in
its report, which is the only reason this was noticed at all. A quieter failure
mode is available and worse: a reader that hits the guard, cannot find a
fallback, and reports a gap as "could not read" when the file was there and
fine.

Two habits that keep it honest:

- **When a guard blocks you, name the fallback in your report.** "Blocked by the
  loop-guard; read via shell instead" costs one clause and preserves the
  reader's ability to judge whether anything was skipped.
- **Never let a blocked read decay into an inferred value.** If the content
  could not be read, that is the finding — not an estimate dressed as one.

## Worth fixing

The guard should key on something that distinguishes *re-reading* from *reading
a sibling* — the file's identity, or a per-call signature including whatever
varies — rather than on the whole path string. Failing that, a batch-read
pattern is common enough that the guard should expect it.

Cheap mitigation available to a caller meanwhile: give readers the shortest
distinguishing paths you can, and expect the fallback.

## Corollary for anyone reading subagent reports

Three independent agents hit the same tool defect and all three worked around it
without complaint. That is the normal case: agents absorb tooling friction
silently. If the workarounds are not surfaced in the report, the defect is
invisible — so treat "I read it another way" as a signal worth acting on, not as
noise.
