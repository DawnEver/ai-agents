---
name: reviewer-discovery-tte-run-state
description: "State of the TTE-2026-08-2905 reviewer run, what is unpushed in both repos, and the next action"
metadata:
  type: project
---

# Reviewer discovery: TTE-Reg-2026-08-2905 — run state

First full end-to-end run of the cc-academia reviewer pipeline on a real IEEE
Transactions on Transportation Electrification submission (rotating load
reconstruction for EM noise orders in a DRSS-AFPM machine, Southeast Univ /
NUAA).

Workspace: `reviewer-discovery/ongoing/tte-2026-08-2905/`

## Result

476 papers → 47 candidates (≥2 relevant papers each) → 25 shortlisted + 1
blocked. COI correctly blocked **Wei Hua** (Southeast University), a submitting
author who is also an author of related work — the rule engine working as
designed.

14 of 47 have an address; 20 have an academic position.

**The position column immediately earned itself:** three shortlisted candidates
are PhD students — Donovin D. Lewis (#6), Matin Vatani (#8), Omolbanin Taqavi
(#13). Lewis was reading as "Engineer" because his only ORCID employment is an
industry post; corrected against the SPARK Lab people page.

## Two data-quality flags to check before inviting

- **"Dashuai Shi — Electric Power University — VN"** is almost certainly a
  mis-parsed North China Electric Power University (CN). Country feeds the
  geographic score.
- **"Akira Chibá — Akita University"** — his ORCID address resolves to
  `@ee.eng.isct.ac.jp`, i.e. Institute of Science Tokyo, not Akita.

Also worth knowing: the candidate pool leans AFPM *topology* over
*vibro-acoustics*. Recognised EM noise/vibration names are thin; queries around
"force harmonics" and "modal analysis" phrased differently would likely surface
them.

## Unpushed work in two repos

| Repo | Branch | Commits |
|---|---|---|
| `Sync/claude/cc-market` | `fix/cc-academia-ci` | 6 — `e7cf35b` CI fix, `2e37a5a` front-matter, `33bc02f` scoring, `45c860d` email discovery, `4d1ad5e` position, `f552bce` ms-review ingest |
| `Sync/agents` | `main` | 1 — `4ac6a34` gitignore + sharp-review entry |

**cc-market `main` is currently red in CI** and `e7cf35b` is the fix, so that
commit is worth pushing as its own PR ahead of the feature work.

Engineering findings (measured discovery ceilings, the URL-not-value rule, the
parsed-then-dropped bug class) are recorded in the cc-market scope:
`cc-market/.claude/memory/2026/08/29/cc-academia-contact-discovery-ceilings.md`

## Next action

38 candidates still need an email and/or a position. The loop is:

```bash
rev-disc contacts --slug tte-2026-08-2905 --json     # who needs what
# search each staff page, collect URLs (+ optional rank/rank_source)
rev-disc enrich --slug tte-2026-08-2905 --homepages ongoing/tte-2026-08-2905/homepages.json
rev-disc coi --slug tte-2026-08-2905 && rev-disc report --slug tte-2026-08-2905
```

Roughly 30 searches. This is the main path, not a fallback — automatic discovery
genuinely tops out near a fifth for both fields in this literature.

## Sharp review

Ran against the diff mid-session: 16 findings, 9 fixed. Two declined on purpose —
splitting the 704-line `repository.py` is an out-of-scope refactor, and
`candidate_scores` excluding blocked candidates is correct because
`coi_evidence` already audits them. Detail:
`.claude/memory/2026/08/28/sharp-review.md`
