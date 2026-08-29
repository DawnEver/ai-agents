---
name: sharp-review-2026-08-28
description: Sharp review findings — 16 total
metadata:
  type: project
---

## Review 2026-08-28 (session) — diff review + security audit (安全锐评)

### Reviewer Status
- Reviewer claude (claude): OK
- Reviewer codex (codex): skipped
- Reviewer deepseek (deepseek): skipped
- Reviewer gmi (gmi): skipped
- Reviewer kimi (kimi): OK

### Confirmed findings

---

### [SR-20260828-001] [HIGH] cc-academia/src/academia/reviewer/discover.py — _match_expression builds unescaped FTS5 phrases that crash on profile topics containing double quotes.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Strip or escape double quotes and other FTS5 phrase-boundary characters when quoting topic strings; add an adversarial test with quoted input.

A topic such as '3" pipe' or 'foo"bar' becomes an unterminated FTS5 string. _bm25_scores swallows the resulting sqlite3.OperationalError and returns {}, silently collapsing the candidate pool to nothing.

---

### [SR-20260828-002] [HIGH] cc-academia/src/academia/store/repository.py — set_person_topics is append-only, so stale topics persist forever and inflate candidate vocabularies across runs.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add source and seen_at columns to person_topics and replace or prune topics per source on re-enrichment; or expose a clear_person_topics helper called before each enrichment pass.

INSERT ... ON CONFLICT(person_id, term) DO NOTHING means if OpenAlex later returns ['C'] instead of ['A','B'], the store ends up with ['A','B','C']. Because word_overlap rewards coverage of profile terms, accumulated stale terms can artificially boost a candidate's topic and method scores in later runs with no audit trail.

---

### [SR-20260828-003] [MEDIUM] cc-academia/src/academia/core/text.py — word_overlap's asymmetric coverage metric is trivially saturated by broad or prolific candidates.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Blend coverage with a precision term (Jaccard or intersection over sqrt of the product of sizes), or weight profile words by inverse document frequency.

_candidate_vocabulary concatenates OpenAlex topics with every paper term from evidence, and word_overlap returns intersection size over profile size. A candidate with a wide vocabulary can cover all profile words and score 1.0 even when no single paper is strongly on topic. Volume leaks into the 60%-weighted topic/method components.

---

### [SR-20260828-004] [MEDIUM] cc-academia/src/academia/cli/rev_disc.py — take() preserves blocked candidates in the report but silently removes them from candidate_scores persistence.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Decide whether candidate_scores audits every considered candidate or only scorable ones, then either record blocked rows with their -inf score/components or document the exclusion.

Previously rank(...)[:top] could include blocked candidates when top was large; now take() always appends them but the record_score loop skips candidate.blocked, so the audit table no longer contains the row.

---

### [SR-20260828-005] [MEDIUM] cc-academia/src/academia/reviewer/discover.py — _match_expression can emit useless all-stopword phrases and exact duplicate terms.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Skip a phrase if none of its words survive filtering, and seed 'seen' before appending phrases to avoid duplicates.

For a topic such as 'a an the' the function emits the phrase with no word disjunctions, matching nothing. For a single-word topic 'one' it emits the same term twice.

---

### [SR-20260828-006] [MEDIUM] cc-academia/src/academia/ingest/pdf.py — _read_title can over-capture author lists, affiliations, or subtitles because it stops only at blank lines, the abstract, or an IEEE membership byline.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Reject continuation lines that look like author names (commas, 'and', '@') or affiliation markers ('University', 'Institute'), or are much shorter than the seed line.

A line like 'Department of Electrical Engineering' satisfies the word-count and not-isupper checks and could be folded into the title. The byline regex only catches 'member/fellow/student member, IEEE'.

---

### [SR-20260828-007] [MEDIUM] cc-academia/src/academia/store/repository.py — repository.py is 704 lines and mixes papers, people, authorships, institutions, emails, runs, and reviewer history in one module.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split into repository/papers.py, people.py, institutions.py, audits.py, re-exporting through __init__.py.

Files over 600 lines should be split. Adding person_topics accessors to an already oversized catch-all increases coupling.

---

### [SR-20260828-008] [LOW] cc-academia/src/academia/reviewer/discover.py — Discovery and scoring use inconsistent stopword and length normalization rules.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Share a single tokenization/normalization helper between _match_expression and word_overlap.

_match_expression filters words of 2 chars or fewer with a small _MATCH_STOPWORDS set, while word_overlap uses tokenize() with a larger STOP_WORDS list, so the same topic produces different tokens in retrieval vs scoring.

---

### [SR-20260828-009] [LOW] cc-academia/src/academia/reviewer/rank.py — take() does not validate negative top values.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Guard for top < 0, or validate --top >= 0 at the CLI layer.

invitable[:top] with a negative value silently drops the highest-ranking invitable candidates. The 'if not top' check only guards zero.

---

### [SR-20260828-010] [LOW] cc-academia/src/academia/store/schema.sql — person_topics has no source or timestamp provenance.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add source TEXT and seen_at TEXT columns.

Without provenance an editor cannot trace why a topic is attached to a candidate, and stale terms cannot be attributed to an enrichment run.

---

### [SR-20260828-011] [LOW] cc-academia/src/academia/reviewer/rank.py — _candidate_vocabulary treats every paper term equally, ignoring relevance score and source.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Weight terms by BM25 relevance or term source score, or only include terms from the strongest evidence papers.

It selects all terms from every evidence paper; paper_terms already has score and kind columns that are ignored.

---

### [SR-20260828-012] [HIGH] cc-academia/src/academia/reviewer/discover.py — FTS5 MATCH expression built by string interpolation of attacker-controlled topic text; double quotes never escaped, allowing query injection or silent discovery failure

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Strip/escape quotes before quoting (double the quote per FTS5 rules), drop tokens that become empty, and log rather than swallow sqlite3.OperationalError.

_match_expression (discover.py:117-136) wraps each topic in a quoted phrase with no sanitisation. profile.primary_topics ultimately derives from the manuscript PDF's own keyword line - fully attacker-controlled. (1) Injection: a keyword containing a quote plus OR terms makes MATCH hit essentially every stored paper, so BM25 becomes noise and the submitting author steers which reviewers surface - reviewer-selection manipulation. (2) DoS: an unbalanced quote yields an invalid expression; _bm25_scores catches OperationalError and returns empty, silently producing an empty candidate set with no error shown to the editor.

---

### [SR-20260828-013] [MEDIUM] cc-academia/src/academia/ingest/pdf.py — Title continuation loop can absorb abstract/body text into the title, propagating manuscript body text downstream past the init boundary

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Bound continuation to 2-3 lines and a total word/char cap, and stop on any line that looks like prose start (contains a sentence break, matches _ABSTRACT_START anywhere, or exceeds ~20 words).

_read_title appends every contiguous non-empty following line, stopping only at a blank line, an anchored _ABSTRACT_START match, or the IEEE byline. Extractors frequently emit a page with no blank lines and no byline, in which case the joined title swallows authors, affiliations and abstract prose. The title is written into the sanitized profile and read by every downstream command, which by the stated invariant must never see body text. No length bound exists on the joined result.

---

### [SR-20260828-014] [LOW] cc-academia/src/academia/reviewer/report.py — write_all unconditionally deletes every *.md under the output dossiers directory before writing

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Delete only files matching the generator's own filename pattern, or write to a temp dir and swap.

report.py:243-246 globs *.md in directory/'dossiers' and unlinks each. The glob is a fixed literal so there is no traversal or injection from candidate names, but directory is a user-supplied --out path. Pointing it at a directory that already contains markdown silently destroys those files.

---

### [SR-20260828-015] [INFO] cc-academia/src/academia/store/repository.py — person_topics writes and reads are correctly parameterised; no SQL injection in the new store code

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** No change needed.

set_person_topics uses executemany with placeholders and _candidate_vocabulary uses bound parameters, so topic strings never reach SQL text. The only unparameterised SQL introduced is the FTS5 MATCH expression. Schema addition uses a proper composite PK with ON DELETE CASCADE. No hardcoded secrets, deserialization, SSRF or crypto usage in the changed files.

---

### [SR-20260828-016] [LOW] literature-review/.gitignore — Dropping the 'workspaces/' ignore exposes any still-on-disk workspace files to accidental commit

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Confirm literature-review/workspaces/ is actually gone before committing; if it still exists, keep the ignore until the OneDrive lock clears.

The removed comment stated the directory is still on disk because OneDrive holds a lock. Untracked files there become visible to git add -A. If that directory holds manuscript PDFs or reviewer data, that is a data-exposure risk.
