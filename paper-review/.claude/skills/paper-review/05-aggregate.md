# Step 05 — Aggregate critiques

Merge `critiques/*.md` into a single ranked `critiques.md`, then present a numbered menu for the user to select which issues to include in their draft.

## Inputs
- `ongoing/<slug>/2-review/critiques/*.md`

## Output
- `ongoing/<slug>/2-review/critiques.md`

## Steps

1. Read every `critiques/<angle>.md`.
2. Assign each **angle** a descriptive prefix based on its name from `angles.md`:
   - `N` for **novelty**
   - `M` for **methodology**
   - `E` for **experiments**
   - `F` for **freestyle**
   - For custom angles, derive a prefix from the first letter or abbreviation of the angle name (e.g. `S` for soundness, `W` for writing, `R` for reproducibility). If two angles would collide on the same letter, use 2-letter abbreviations (e.g. `So` for soundness, `St` for statistical-rigour).
3. Within each angle, collect all critique points and number them **1, 2, 3, …** in descending severity order (Major first, then Minor, then Nit).
4. Dedupe across angles: if two angles raise the same issue, keep it under the primary angle and note the other in `From:`.
5. **Flag conflicts**: if one angle calls X a strength and another calls X a weakness, mark both points with `⚡ CONFLICT` and cross-reference.
6. Write `critiques.md` with this structure:

   ```markdown
   # Critiques — <slug>

   ## N · Novelty
   ### N1 · <point title>
   - Severity: Major
   - From: novelty (+ methodology)
   - Claim: ...
   - Evidence: ...
   - Suggested action: ...

   ### N2 · <point title>
   ...

   ## M · Methodology
   ### M1 · ...
   ...

   ## Conflicts
   ### ⚡ N3 vs M2 · <topic>
   - N3 says: ...
   - M2 says: ...
   ```

7. After writing the file, display a **compact selection menu** inline to the user:

   ```
   ── Critiques ready ──────────────────────────────
   N · Novelty
     N1 [Major] <point title>
     N2 [Minor] <point title>
   M · Methodology
     M1 [Major] <point title>
     ...
   ⚡ Conflicts: N3 vs M2

   Type codes to include in your draft (e.g. N1 M2 E1 F1):
   ─────────────────────────────────────────────────
   ```

8. **Wait for the user's selection.** Do not proceed to step 06 until the user responds with selection codes (or `all` / `none`).
