# Step 04 — Fanout 锐评

Spawn one reviewer per angle **in parallel** (one message, multiple tool calls).

## Inputs
- `ongoing/<slug>/2-review/angles.md` (chosen angles + optional router overrides)
- `ongoing/<slug>/2-review/summary.md`, `ongoing/<slug>/2-review/literature.md` (if present)
- `1-paper-text/paper.md`, `1-paper-text/md/`, `1-paper-text/img/`, `1-paper-text/INDEX.md`
- Each reviewer agent's frontmatter `router:`

## Output
- `ongoing/<slug>/2-review/critiques/<angle>.md` — one per angle

## Routing resolution

For each angle in `angles.md`:
1. If `Router override:` is non-empty, use it.
2. Else use the agent's frontmatter `router:` field.

| Router value | How to invoke | Typical for |
|--------------|---------------|-------------|
| `sonnet-vision` | `Agent(subagent_type: reviewer-<angle>)` — Sonnet, vision-capable | novelty, experiments, freestyle |
| `takeover-codex` | `Skill(takeover:continue)` with model=codex | methodology / heavy reasoning |
| `takeover-deepseek` | `Skill(takeover:continue)` with model=deepseek | second opinion, dense technical reasoning |

**Spawn all reviewers in a single message** with multiple tool calls. Do not serialise.

## Venue-type calibration (pass to every reviewer)

Read the **Venue type** field from `summary.md` and inject it into every reviewer prompt. Reviewers must hold critique to the standard of the actual venue:
- **Electrical-engineering conference paper** (electric machines, power electronics, drives): simulation-only validation is acceptable; do NOT penalise missing hardware experiments, missing public code, or missing public data. Focus on novelty, method soundness, and whether the simulation supports the claims.
- **Journal paper** (esp. IEEE Transactions): experimental / hardware validation, robustness, and completeness are fair game — absence is a legitimate weakness.
- The methodology and experiments reviewers in particular must respect this; a missing-code/missing-hardware critique against an EE conference paper is out of scope and should not be raised.

**Before spawning, tell the user**: "Launching <N> reviewers in parallel — results will arrive in ~2–5 minutes. You'll see each critique appear as the reviewers finish."

## Figures are machine-extracted (pass to every reviewer)

The images in `1-paper-text/img/` are cropped by a local PDF-parsing library and may be mis-cropped, mislabeled, or rendered too small / low-resolution — extraction artifacts, not paper defects. Instruct **every** reviewer that references a figure:
- Do **not** state image-quality problems (blurriness, low resolution, truncation, unreadable labels) as firm defects — they may be extraction artifacts.
- Raise such observations only as a **flag for the user to verify against the original PDF**, severity `minor` at most, and **attach the exact image path** used (e.g. `img/sec3-experiments/figure3.png`).
- Critiques about experimental *content* (missing baselines, table-vs-prose mismatch, etc.) are unaffected and stand on their own.

## Prompt contract — all reviewers

Every reviewer receives the same core brief (common to Sonnet and Takeover):
1. Read `summary.md` first — calibrate critique to its **Venue type** (see above).
2. Read `literature.md` (if present) for research landscape context.
3. Angle definition verbatim from `angles.md`.
4. Output to `ongoing/<slug>/2-review/critiques/<angle>.md`.
5. Format: numbered points (1, 2, 3…) descending severity (Major → Minor → Nit). Per point:
   `## <N> · <claim>` / `- Evidence:` / `- Severity: major|minor|nit` / `- Suggested action:`.
6. Language: read `lang:` from `review-config.md` (default `en`). Critique prose in that language; quoted paper text stays verbatim.

### Router-specific

**Sonnet** (`Agent` call) — pass paths directly; subagent reads files from disk.

**Takeover** (Codex/DeepSeek) — runs in a separate process, cannot read this conversation or OneDrive paths.
The prompt is fully self-contained — inline **verbatim**:
- Entire `summary.md` + `literature.md` + angle definition
- Relevant section excerpts (e.g. Method + Theory; actual markdown body)
- Restate venue-type calibration rule inline; state target language explicitly
- If text exceeds ~30k tokens, prioritise: summary + literature + angle + Method + Theory + captions

After takeover returns, orchestrator writes returned text to `critiques/<angle>.md` if not already there.

## After fanout

Wait for all reviewers to complete. Check every expected `2-review/critiques/<angle>.md` exists and is non-empty (one file per angle in `angles.md`).

**Partial-recovery protocol**: if one or more critique files are missing, empty, or truncated after a reasonable wait, present the user with a choice:

1. **Retry missing reviewers** — re-spawn only the agents that failed (recommended). The orchestrator re-reads `angles.md` and re-launches only the missing-angle agents with the same prompt contract.
2. **Skip missing angles** — proceed to step 05 with only the available critiques. Note in `critiques.md` which angles were skipped.
3. **Continue with partial (re-try later)** — write a placeholder file (e.g. `critiques/<angle>.md` containing `# <angle> — PENDING`) and proceed to step 05. The user can fill it in or re-run via `/paper-review:rerun 04 <slug>`.

Do not silently enter step 05 with a partial set.
