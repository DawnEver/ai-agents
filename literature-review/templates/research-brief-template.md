# Research Brief Template

Annotated reference for the agent when helping users define a research brief.
All fields map to `schemas/research_brief.schema.json`.

## Structure

```yaml
brief_id: "kebab-case-id"           # Unique identifier for this brief
topic_id: "parent-workspace"        # Optional workspace reference
artifact_version: 1
created_at: "2026-07-23T..."        # ISO 8601 timestamp
original_request: "..."             # User's natural-language request, verbatim
research_objective: "..."           # Refined one-sentence objective
inclusion_criteria: [...]           # What to include
exclusion_criteria: [...]           # What to exclude
constraints:
  year_from: 2018
  year_to: 2026
  content_types: [Journals, Conferences]
  preferred_venues: [...]           # Optional venue list
  defaults_applied: [...]           # Which defaults were auto-applied
concepts:
  - concept_id: "c01"
    role: must                      # must | should | context | evidence | exclude
    term: "..."                     # Canonical English term
    synonyms: [...]                 # Alternative search terms
    rationale: "..."                # Why this concept matters
    source: user                    # user | agent
    selected: true
approval:                           # Added by confirm-brief
  approved: true
  approved_at: "..."
  approved_by: "..."
  research_scope_sha256: "..."
```

## Concept Role Semantics

| Role | Meaning | Query Behavior |
|------|---------|---------------|
| `must` | Core topic — paper MUST address this | AND-ed in all queries |
| `should` | Desired but not required | OR-ed within must groups |
| `context` | Background/domain context | Used for query broadening if too few results |
| `evidence` | Empirical requirement (e.g. "experimental prototype") | May gate screening decisions |
| `exclude` | Explicitly exclude (e.g. "low power") | NOT-ed in queries |

## Example: LLC Wide Voltage Range

```yaml
brief_id: "llc-wide-voltage-2026"
topic_id: "llc-converters"
original_request: "LLC resonant converters with wide voltage range for EV chargers"
research_objective: "Find LLC topologies and control methods that maintain ZVS across >2:1 voltage range in EV on-board charger applications"
inclusion_criteria:
  - "LLC or CLLC topology variants"
  - "Experimental prototype with ≥500W rated power"
  - "Reports voltage gain range or input/output voltage specifications"
exclusion_criteria:
  - "Low-power IC applications (<100W)"
  - "Pure simulation without hardware validation"
constraints:
  year_from: 2018
  year_to: 2026
  content_types: [Journals, Conferences]
  preferred_venues:
    - IEEE Transactions on Power Electronics
    - IEEE Transactions on Industrial Electronics
concepts:
  - concept_id: "c01"
    role: must
    term: "LLC resonant converter"
    synonyms: ["LLC converter", "LLC resonant", "LLC DC-DC"]
    rationale: "Core topology under investigation"
    source: user
    selected: true
  - concept_id: "c02"
    role: must
    term: "wide voltage range"
    synonyms: ["wide input voltage", "wide gain range", "wide output range"]
    rationale: "Primary design requirement"
    source: user
    selected: true
  - concept_id: "c03"
    role: should
    term: "zero-voltage switching"
    synonyms: ["ZVS", "soft switching"]
    rationale: "Key performance requirement"
    source: user
    selected: true
  - concept_id: "c04"
    role: context
    term: "electric vehicle"
    synonyms: ["EV", "electric vehicle charger", "on-board charger"]
    rationale: "Application context"
    source: user
    selected: true
  - concept_id: "c05"
    role: evidence
    term: "hardware prototype"
    synonyms: ["experimental prototype", "hardware validation", "experimental results"]
    rationale: "Empirical validation required"
    source: agent
    selected: true
```

## Defaults Applied

When the user does not specify constraints, the agent applies:
- `year_from`: 10 years before current year
- `year_to`: current year
- `content_types`: [Journals, Conferences]
- These are recorded in `defaults_applied` for audit.
