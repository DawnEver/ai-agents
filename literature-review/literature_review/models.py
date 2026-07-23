"""Data models for Literature Review — replaces all JSON Schema files."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

@dataclass
class Approval:
    approved: bool = False
    approved_at: str | None = None
    approved_by: str | None = None
    hash: str | None = None  # research_scope_sha256 / queries_sha256 / screening_sha256


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------

@dataclass
class ZoteroBinding:
    collection_key: str = ""
    group_id: str | None = None
    sync_notes: bool = True
    sync_attachments: bool = False
    tags: list[str] = field(default_factory=list)


@dataclass
class WorkspaceConstraints:
    year_from: int = 2018
    year_to: int = 2026
    content_types: list[str] = field(default_factory=lambda: ["Journals", "Conferences"])
    preferred_venues: list[str] = field(default_factory=list)


@dataclass
class Workspace:
    workspace_id: str
    name: str
    description: str = ""
    created_at: str = ""
    zotero: ZoteroBinding = field(default_factory=ZoteroBinding)
    defaults: WorkspaceConstraints = field(default_factory=WorkspaceConstraints)
    lenses: list[str] = field(default_factory=list)
    providers: list[str] = field(default_factory=lambda: ["ieee_xplore"])
    pdf_store: str = ""
    parent: str = ""


# ---------------------------------------------------------------------------
# Research Brief
# ---------------------------------------------------------------------------

@dataclass
class Concept:
    concept_id: str
    role: str  # must | should | context | evidence | exclude
    term: str
    synonyms: list[str] = field(default_factory=list)
    rationale: str = ""
    source: str = "user"
    selected: bool = True


@dataclass
class ResearchBrief:
    brief_id: str
    original_request: str
    research_objective: str
    inclusion_criteria: list[str] = field(default_factory=list)
    exclusion_criteria: list[str] = field(default_factory=list)
    year_from: int = 2018
    year_to: int = 2026
    content_types: list[str] = field(default_factory=lambda: ["Journals", "Conferences"])
    preferred_venues: list[str] = field(default_factory=list)
    concepts: list[Concept] = field(default_factory=list)
    approval: Approval | None = None
    topic_id: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["constraints"] = {
            "year_from": d.pop("year_from"),
            "year_to": d.pop("year_to"),
            "content_types": d.pop("content_types"),
            "preferred_venues": d.pop("preferred_venues"),
        }
        return d


# ---------------------------------------------------------------------------
# Candidate & Screening
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    candidate_id: str
    source_provider: str
    title: str
    abstract: str = ""
    doi: str = ""
    authors: list[str] = field(default_factory=list)
    venue: str = ""
    publication_year: int | None = None
    content_type: str = ""
    keywords: list[str] = field(default_factory=list)
    citation_count: int = 0
    html_url: str = ""
    pdf_url: str = ""
    provider_raw: dict[str, Any] = field(default_factory=dict)
    query_id: str = ""
    page: int = 1
    rank: int = 0
    search_expression: str = ""


@dataclass
class ScreeningDecision:
    candidate_id: str
    decision: str  # include | maybe | exclude
    confidence: float = 0.0
    inclusion_reasons: list[str] = field(default_factory=list)
    exclusion_reasons: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    abstract_available: bool = True
    download_priority: str = "medium"  # none | low | medium | high


# ---------------------------------------------------------------------------
# Query Plan
# ---------------------------------------------------------------------------

@dataclass
class QueryItem:
    query_id: str
    purpose: str
    provider: str = "ieee_xplore"
    expression: str = ""
    year_from: int = 2018
    year_to: int = 2026
    content_types: list[str] = field(default_factory=lambda: ["Journals", "Conferences"])
    sort: str = "relevance"
    enabled: bool = True
    concept_ids: list[str] = field(default_factory=list)


@dataclass
class QueryPlan:
    queries: list[QueryItem] = field(default_factory=list)
    brief_ref: dict[str, str] = field(default_factory=dict)
    approval: Approval | None = None


# ---------------------------------------------------------------------------
# Download & Ingest manifests
# ---------------------------------------------------------------------------

@dataclass
class DownloadItem:
    candidate_id: str
    title: str
    pdf_path: str = ""
    sha256: str = ""
    pdf_bytes: int = 0
    acquisition_method: str = ""
    acquired_at: str = ""
    screening_reason: str = ""
    reading_questions: list[str] = field(default_factory=list)


@dataclass
class DownloadManifest:
    manifest_id: str
    run_id: str
    papers: list[DownloadItem] = field(default_factory=list)
    approved_brief_sha256: str = ""


@dataclass
class IngestItem:
    candidate_id: str
    pdf_path: str
    output_path: str
    status: str = "failed"  # succeeded | failed | skipped
    error: str = ""
    paper_md: str = ""
    index_md: str = ""
    page_markdown: list[str] = field(default_factory=list)
    figures: list[dict] = field(default_factory=list)


@dataclass
class IngestManifest:
    source_manifest: str
    source_manifest_sha256: str = ""
    confirmed_by_user: bool = False
    ingests: list[IngestItem] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Paper Card (deep reading output)
# ---------------------------------------------------------------------------

@dataclass
class Evidence:
    claim: str
    source: str = ""    # path to markdown file
    locator: str = ""   # e.g. "Fig. 8, Table II"


@dataclass
class ResearchUse:
    type: str  # adapt | compare | baseline | cite | discard
    note: str = ""


@dataclass
class PaperCard:
    candidate_id: str
    title: str
    verdict: str = "targeted-read"  # deep-read | targeted-read | archive
    confidence: float = 0.0
    one_sentence: str = ""
    technical_core: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    research_use: list[ResearchUse] = field(default_factory=list)
    next_action: str = ""
    open_questions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Reading Queue
# ---------------------------------------------------------------------------

@dataclass
class ScoreBreakdown:
    relevance: int = 0
    methodology: int = 0
    novelty: int = 0
    evidence: int = 0


@dataclass
class QueueItem:
    candidate_id: str
    title: str
    verdict: str = "targeted-read"
    confidence: float = 0.0
    scores: ScoreBreakdown = field(default_factory=ScoreBreakdown)
    reason: str = ""
    first_target: str = ""


@dataclass
class ReadingQueue:
    research_need: str
    papers: list[QueueItem] = field(default_factory=list)
    top_picks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
