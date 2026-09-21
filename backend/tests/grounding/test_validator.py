from datetime import date
from uuid import UUID

from app.grounding.validator import (
    build_message_citations,
    canonicalize_answer_citations,
    extract_citation_labels,
    validate_answer_citations,
)
from app.retrieval.types import RetrievedPassage


def _passage(label: int) -> RetrievedPassage:
    return RetrievedPassage(
        chunk_id=UUID(f"00000000-0000-4000-8000-{label:012d}"),
        document_id=UUID("11111111-1111-4111-8111-111111111111"),
        chunk_index=label - 1,
        content=f"Revenue increased in fiscal year {label}.",
        page=label,
        section="Item 7",
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_type="10-K",
        filing_date=date(2024, 11, 1),
        fiscal_year=2024,
        source_url="https://example.com",
        rrf_score=0.1,
        citation_label=label,
    )


def test_extract_citation_labels():
    assert extract_citation_labels("Net sales rose [1] and margins [2].") == [1, 2]


def test_validate_rejects_unknown_label():
    result = validate_answer_citations(
        "Claim [9] without support.",
        [_passage(1)],
    )
    assert not result.ok
    assert "not in retrieved" in result.errors[0]


def test_validate_allows_insufficient_evidence_without_citations():
    result = validate_answer_citations(
        "The corpus does not contain enough evidence to answer this question.",
        [_passage(1)],
    )
    assert result.ok


def test_build_message_citations_dedupes_labels():
    passages = [_passage(1), _passage(2)]
    drafts = build_message_citations(passages, [1, 1, 2])
    assert len(drafts) == 2
    assert drafts[0].sort_order == 0
    assert drafts[1].sort_order == 1


def test_canonicalize_rewrites_sparse_labels_to_contiguous():
    passages = [_passage(3), _passage(7)]
    result = canonicalize_answer_citations(
        "Products rose [3] while services [7] grew.",
        passages,
    )
    assert result is not None
    assert result.text == "Products rose [1] while services [2] grew."
    assert result.cited_labels == (3, 7)


def test_canonicalize_returns_none_when_validation_fails():
    result = canonicalize_answer_citations("Unsupported claim [9].", [_passage(1)])
    assert result is None
