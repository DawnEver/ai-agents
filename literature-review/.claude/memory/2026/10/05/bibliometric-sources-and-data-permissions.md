---
name: bibliometric-sources-and-data-permissions-2026-10-05
description: Scopus web API pacing, Nottingham DSpace thesis API, author-matching pitfall, and why per-project data-dir permission globs never match
metadata:
  type: engineering
---

# Bibliometric sources and data-dir permissions

`created: 2026-10-05, accessed: 2026-10-05`

## Scopus web internal API
- `POST /api/documents/search` with JSON `{query, sort, itemcount<=200, offset}` works from a signed-in scopus.com tab (same-origin fetch).
- Returns 429 ("usage increased beyond our threshold") after a few hundred rapid queries; lockout ~10 min. Pace ~4.5 s/query and back off 10 min on 429.
- Items carry year, document type, source type and author IDs, but no per-author affiliations; classify by campus with `AFFIL()` query filters (document level).

## Nottingham repository (DSpace 7)
- Public REST `/server/api/discover/search/objects?query=...&dsoType=ITEM` (no auth, cross-origin blocked from other sites; use stdlib urllib).
- Thesis metadata: `dc.contributor.supervisor`, `uon.type.thesis` (PhD/EngD/MPhil), `dc.relation.orgunit`, `uon.depositnote` (contains UNMC/UNNC campus hints).
- `dc.relation.orgunit` is missing or just "Faculty of Engineering" for many 2015–2020 theses; filtering by department alone misses most of them, search by supervisor too. The repository is not a complete list of graduates (embargoed or undeposited theses absent).

## Author matching
- Name-only Scopus author matching mis-identifies common names (wrong profile, inflated counts). Require co-authorship with a known collaborator (e.g. supervisor); treat ties, profiles with implausibly early first publication, and one profile claimed by two people as excluded.

## Data-dir permissions
- Project data dirs are symlinks into the synced `agent-data` root; permission checks see the resolved path, so per-project `*/<project>/ongoing/**` globs never match.
- Repo rule: `ai-agents/.claude/rules/DATA-PERMISSIONS.md`. The fix is one user-level rule on `**/agent-data/**` plus `additionalDirectories`; agents cannot edit settings themselves (blocked as self-modification), so the user must apply it.

## White Rose eTheses (EPrints 3.4)
- JSON/view exports return error pages. Department year pages `/view/iau/<Dept>/<year>.html` list `/id/eprint/<id>` links.
- Item pages carry `eprints.*` meta tags whose attribute order varies (`content` before `name`); parse attributes per tag. Supervisors appear only in the page body after "Supervisors:".

## Supervisor name matching
- Repositories write "Surname, Given" and "Given, Surname", mixed case, with titles. Try both orders, strip titles, and require surname plus given-name prefix to avoid namesakes.

## Scopus plausibility rule
- Apply per-person within that person's own year window only; otherwise later careers trigger it. Count journal papers, not all documents (conference-heavy students are genuine).

## Browser <-> disk data transfer
- Console output truncates at ~1000 chars; large javascript payloads make the tab unresponsive.
- A 127.0.0.1 bridge needs CORS plus `Access-Control-Allow-Private-Network`, and may trigger Chrome's local-network permission prompt, which freezes the tab until the user answers.

## Background processes (Windows)
- Background shells can be reaped under system memory pressure.
- `pkill` does not stop background python; find processes via `Get-CimInstance Win32_Process` CommandLine.
- Two concurrent crawlers sharing a cache file overwrite each other; run one at a time.

## Data-dir permission fix
- Shipped as `ai-agents/.claude/hooks/allow-data-links.js`: the user runs it once per workstation; it resolves data links and writes git-ignored `.claude/settings.local.json` per project.
