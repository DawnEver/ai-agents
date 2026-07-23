# Paper Card Template

Specification for the compact paper reading note (`paper_card.json` + rendered `.md`).

## Output Contract

- **English**: ~700 words maximum
- **Chinese (中文)**: ~1200 characters maximum
- Every factual claim must have a **source anchor**: `(source-file.md, locator)` — e.g. `(page-07.md, Fig. 8)`
- Use markers for uncertain information:
  - `not reported` — paper does not address this
  - `parse uncertain` — text is ambiguous, this is the agent's best interpretation
  - `inference` — not stated explicitly, inferred from context

## JSON Schema

See `schemas/paper_card.schema.json`. Key fields:

```yaml
candidate_id: "C001"
title: "..."
verdict: deep-read          # deep-read | targeted-read | archive
confidence: 0.90            # 0.0–1.0

one_sentence: "..."         # Single sentence capturing the paper's core contribution

technical_core:             # 3–5 key technical points
  - "..."

evidence:                   # Claim-evidence-condition triples
  - claim: "..."
    source: "1-paper-text/md/page-07.md"
    locator: "Fig. 8 and Table II"

limitations:                # Honest assessment
  - "..."

research_use:               # How this paper informs your research
  - type: adapt             # adapt | compare | baseline | cite | discard
    note: "..."

next_action: "..."          # Concrete next step
open_questions:             # What remains unclear
  - "..."
```

## Verdict Semantics

| Verdict | Meaning | Next Action |
|---------|---------|-------------|
| `deep-read` | High-value paper, read all sections | Produce full paper card, track evidence |
| `targeted-read` | Specific sections are valuable | Read only those sections, extract key claims |
| `archive` | Low relevance or quality | Store metadata, skip deep reading |

## Evidence Quality Ladder

1. **Application-scale prototype** (>1 kW, real-world conditions) — strongest
2. **Low-power prototype** (<1 kW, lab conditions)
3. **HIL (Hardware-in-the-Loop)** — partial real hardware
4. **Simulation only** — weakest, but may still be useful for method comparison
5. **No validation** — theoretical only

Mark evidence quality in the limitation section if below application-scale.
