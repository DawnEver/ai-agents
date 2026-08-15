# Session review: [project] — where the agent actually got stuck

Post-hoc analysis of **real** persisted sessions (evidence layer 2), not a launched
experiment. Tool: `scripts/analyze-session.mjs` (detectors in `driver/struggle.mjs`),
run against `~/.claude/projects/D--Documents-[user]-[project]` (346
session files). Subjects, the two largest sessions of the [subsystem] work:

- `[session]` (2026-07-24→26, 12 270 entries, 3 876 assistant turns) — 66 episodes:
  28 repeated-command, 17 edit-thrash, 14 bash-retry, 5 permission-denial,
  2 long-stall (plus 9 waits-on-subagents, excluded).
- `[session]` (2026-07-26→27, 9 288 entries, 3 878 assistant turns) — 145 episodes:
  67 repeated-command, 43 bash-retry, 17 edit-thrash, 16 long-stall,
  1 tool-error-repeat, 1 permission-denial (plus 15 waits-on-subagents, excluded).

Zero `isApiErrorMessage` in both — infra was not the problem. All friction below is
**workflow-level**, and it clusters into four recurring patterns.

## 1. The single biggest sink: `[src].py` edited ×18 over two days ([session])

The [module]-registry redesign never converged in one pass. The same meta-gate test
failed **6 times** with the identical assertion
(`test_[feature] — assert {...} == {...}`),
plus 4× `test_every_row_still_exists[[src].py:[registry]]` and repeated
[engine] failures (`KeyError: 'fea'` ×4, `ValueError: sweep engine supports…` ×2).
Full-suite runs kept coming back red: `15 failed, 4456 passed` → `57 failed, 6761
passed` → `4 failed, 6828 passed` — each a 6–13 minute pytest run.

Root pattern: the agent edits the registry, runs the **whole** suite, discovers the
meta-gate test encodes an invariant it broke, patches, re-runs everything. The
oracle (the meta-gate test's expectations) was never read up-front; it was discovered
by collision, repeatedly.

**Fix direction:** before touching a registry guarded by a meta-test, read the
meta-test first and state the invariant in the plan; run the *targeted* test file
(0.8 s) not the full suite (6–13 min) until green.

## 2. Pre-commit / commit retry loop (bash-retry ×42 in [session], ×14 in [session])

The dominant repeated failure string across both sessions is a commit that exits 1
because `ruff-format` **modified files** (`hook id: ruff-format — files were modified
by this hook, N files reformatted`) or because a hook skipped with "no files to
check". The agent then re-stages and re-commits — the signature `git add … &&
git commit -F - <<'EOF'` appears again and again. This is benign but costly: dozens
of two-step commit dances.

**Fix direction:** always `git add -A` *immediately before* `git commit` in the same
command (already done in later commits — early ones staged separately), or run
`pre-commit run -a` once before the first commit attempt of a batch.

## 3. Long-stalls are mostly NOT struggles — and the detector now says so

v1 of the analyzer fired 43 long-stalls across both sessions; v2 classifies each by
what CLOSED the span. Result: **24 of them were waits-on-subagents** (spans ending in
`<task-notification>` or teammate idle-messages — the main agent correctly waiting on
fan-out) and are now excluded from the struggle list by default. The genuine residue:

- `[session]`: only **2** real stalls.
- `[session]`: **16**, several closing on real user text like `继续迭代啊` /
  `去做 持续迭代 直到完成全部任务及 follow up项目` (190, 135, 118 assistant entries)
  — the user came back and had to re-push an agent that had stopped short of the
  standing "iterate until done" instruction. The user repeating "继续" across
  sessions is the clearest human-visible symptom of under-completion.

**Fix direction:** the "iterate until done" contract needs an explicit done-criterion
checklist the agent ticks off, rather than stopping at the first green test run.

## 3b. The newly-visible loop: re-reading the same region dozens of times

The `repeated-command` detector (near-identical Bash, normalized paths/numbers/strings)
surfaced a pattern invisible to v1: the agent **re-reads the same file region over and
over instead of retaining it** — `sed -n '<range>' [plan].md` ×104
([session]), `sed -n '100,140p' [src].py` ×35 ([session]), the same [registry] probe
`python -c "from [project].[subsystem].[module] import …"` ×26/×14, the same grep for
`[script]` ×13. This is the context-window tax made visible: after compaction or
long fan-out, knowledge evaporates and is re-bought with shell commands. It is the
single most frequent episode kind (95 across two sessions).

**Fix direction:** stable facts (plan state, registry shapes, gate results) belong in
scratchpad files the agent writes once and re-reads deliberately — or the harness's
memory; ad-hoc `sed`/`grep` re-reads are the expensive way to "remember".

## 4. Edit-thrash on plans/memory files is healthy; on tests it signals spec drift

17 edit-thrash episodes per session split cleanly:

- `.claude/memory/**plan**.md` / `fanout.md` edited ×3–6 — plans evolving, fine.
- **Test files edited ×4–6 right after the source was edited**
  (`test_[module].py` ×6, `test_[module].py` ×6,
  `test_[module].py` ×4, `test_[module].py` ×3) —
  tests repeatedly rewritten to match a shifting implementation. Some of this is
  TDD refactoring, but ×6 on one test file within one worktree lane means the
  contract was being negotiated *through* the tests instead of before them.
- One genuine bug found via this lens: `[src].py` shipped an
  `unflatten_[field]` with a spurious `r0` factor whose "tests passed only because
  the same spurious `r0` was inserted on both sides" (docstring edit at entry 1649,
  [session]) — exactly the failure mode of test-and-implementation co-evolution.

## Detector quality notes

v1 → v2 fixes, all verified on these two sessions:

- ~~`tool-error-repeat` over-clusters~~ — fixed: clusters are now keyed per
  (tool, normalized error) via tool_use_id attribution, and split into 300-entry
  windows. The bogus whole-session ×4 episode (entries 43–8520) is gone.
- ~~`long-stall` needs the task-notification exclusion~~ — fixed: episodes are
  classified by their closing message; notification-closed spans become
  `wait-on-subagents` and are excluded by default (24 of 43 stalls were waits).
- ~~`identical-loop` fired 0 times — real loops are near-identical~~ — fixed: new
  `repeated-command` detector normalizes Bash commands (paths/numbers/strings
  stripped) and flags ≥3 runs. It immediately became the most frequent episode kind
  and exposed the re-reading loop of §3b.
- Remaining soft spot: `repeated-command` cannot distinguish "re-read because context
  was lost" from "legitimately polling a file" (e.g. `tail` of a running task's
  output, ×7/×11 — that one is healthy). Interpretation still needs the parent
  Claude's judgment; the detector only guarantees the candidate list is complete.

## Bottom line

The agent's repeated 纠结 was not tool failures or API flakiness — it was
**discovering encoded invariants by collision** (meta-gate tests, pre-commit hooks,
registry contracts) instead of reading them first, **re-buying lost context with
shell re-reads** (§3b, the most frequent loop), and **stopping short** of a
user-defined done-state on long autonomous runs. All three are prompt/workflow-fixable;
none is a model-capability issue.

---

Reproduce: `node scripts/analyze-session.mjs --project [project] --session <id>`
(session ids above; full dumps were intermediate and are not kept — `.scratch/`).
