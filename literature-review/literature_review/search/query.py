"""Query construction — keyword grouping and Boolean expression generation."""

from __future__ import annotations

from literature_review.models import Concept


def build_keyword_groups(concepts: list[Concept]) -> dict[str, list[Concept]]:
    """Group concepts by their role: ``must``, ``should``, ``context``, ``evidence``, ``exclude``.

    Only selected concepts are included.  The returned dict maps each role
    name to a (possibly empty) list of concepts.
    """
    groups: dict[str, list[Concept]] = {}
    for concept in concepts:
        if not concept.selected:
            continue
        role = concept.role or "should"
        groups.setdefault(role, []).append(concept)
    return groups


def _concept_terms(concept: Concept) -> list[str]:
    """Collect *term* and *synonyms* into a deduplicated list."""
    terms = [concept.term]
    for syn in (concept.synonyms or []):
        if syn and syn not in terms:
            terms.append(syn)
    return terms


def _quoted(term: str) -> str:
    """Quote a term for exact-phrase matching when it contains whitespace."""
    return f'"{term}"' if " " in term else term


def _or_group(concepts: list[Concept]) -> str:
    """Build an OR-clause from a list of concepts and their synonyms."""
    terms: list[str] = []
    for c in concepts:
        terms.extend(_quoted(t) for t in _concept_terms(c))
    if not terms:
        return ""
    if len(terms) == 1:
        return terms[0]
    return "(" + " OR ".join(terms) + ")"


def build_boolean_query(
    groups: dict[str, list[Concept]], provider: str = "ieee_xplore"
) -> str:
    """Build a Boolean search expression from role-grouped concepts.

    ``must`` and ``should`` concepts are AND-ed; ``context`` / ``evidence``
    are appended with AND; ``exclude`` concepts are negated with NOT.
    """
    parts: list[str] = []

    for role in ("must", "should"):
        clause = _or_group(groups.get(role, []))
        if clause:
            parts.append(clause)

    ctx_concepts = groups.get("context", []) + groups.get("evidence", [])
    ctx_clause = _or_group(ctx_concepts)
    if ctx_clause:
        parts.append(ctx_clause)

    expression = " AND ".join(parts) if parts else ""

    exclude = _or_group(groups.get("exclude", []))
    if exclude:
        expression = (
            f"({expression}) NOT ({exclude})"
            if expression
            else f"NOT ({exclude})"
        )

    return expression
