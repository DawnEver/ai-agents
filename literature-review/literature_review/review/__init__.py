"""Review module — abstract screening and deep reading."""

from literature_review.review.extract import extract_sections, extract_text_from_pdf
from literature_review.review.reader import review_paper
from literature_review.review.screen import filter_by_keywords, import_agent_screening, write_screening_packet
from literature_review.review.synthesis import compare_papers, rank_by_relevance

__all__ = [
    "extract_text_from_pdf",
    "extract_sections",
    "write_screening_packet",
    "import_agent_screening",
    "filter_by_keywords",
    "review_paper",
    "compare_papers",
    "rank_by_relevance",
]
