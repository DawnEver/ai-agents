# Step 04 — Fanout 锐评

Spawn one reviewer per angle **in parallel** (one message, multiple tool calls).

## Inputs
- `ongoing/<slug>/2-review/angles.md` (chosen angles + optional router overrides)
- `ongoing/<slug>/2-review/summary.md`, `1-paper-text/paper.md`, `1-paper-text/md/`, `1-paper-text/img/`, `1-paper-text/INDEX.md`
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

**Before spawning, tell the user**: "Launching <N> reviewers in parallel — results will arrive in ~2–5 minutes. You'll see each critique appear as the reviewers finish."

## Prompt contract — Sonnet subagents (Agent call)

Each Agent invocation receives:
1. Paper slug + absolute paths to `summary.md`, `1-paper-text/paper.md`, `1-paper-text/md/`, `1-paper-text/img/`, `1-paper-text/INDEX.md`.
2. Angle definition copied verbatim from `angles.md`.
3. Instruction: read `2-review/summary.md` first; consult `1-paper-text/INDEX.md` to locate figures by number.
4. Output path: `ongoing/<slug>/2-review/critiques/<angle>.md`.
5. Output structure per point: `## claim` / `- Evidence:` / `- Severity:` / `- Suggested action:`.

## Prompt contract — Takeover (Codex / DeepSeek)

Takeover runs in a separate process and **cannot read this conversation**. File-system reads from within Codex/DeepSeek are also unreliable on paths with spaces/OneDrive sync.

The prompt MUST be **fully self-contained**:
1. **Inline the entire `summary.md`** verbatim into the prompt.
2. **Inline the angle definition** from `angles.md`.
3. **Inline relevant section excerpts** the reviewer needs (e.g. for methodology angle: Method + Theory + relevant appendix; copy the actual markdown body into the prompt, do not just give paths).
4. State the output path explicitly (use forward-slash absolute path), but also instruct the agent to RETURN the critique text in the response, so the orchestrator can write it locally if the agent's file write fails.
5. Same output structure (`## claim` / `Evidence` / `Severity` / `Suggested action`).
6. If the included text would exceed ~30k tokens, prioritise: summary + angle + Method section + Theory section + caption text. Drop appendices.

After takeover returns, the orchestrator writes the returned text to `2-review/critiques/<angle>.md` if the file isn't already there.

## After fanout

Wait for all reviewers to complete. Check every expected `2-review/critiques/<angle>.md` exists and is non-empty (one file per angle in `angles.md`).

**Partial-recovery protocol**: if one or more critique files are missing, empty, or truncated after a reasonable wait, present the user with a choice:

1. **Retry missing reviewers** — re-spawn only the agents that failed (recommended). The orchestrator re-reads `angles.md` and re-launches only the missing-angle agents with the same prompt contract.
2. **Skip missing angles** — proceed to step 05 with only the available critiques. Note in `critiques.md` which angles were skipped.
3. **Continue with partial (re-try later)** — write a placeholder file (e.g. `critiques/<angle>.md` containing `# <angle> — PENDING`) and proceed to step 05. The user can fill it in or re-run via `/paper-review:rerun 04 <slug>`.

Do not silently enter step 05 with a partial set.
