from datetime import date
from uuid import UUID

from app.grounding.context import format_grounding_system_addendum
from app.retrieval.types import RetrievedPassage


def test_format_includes_citation_labels_and_rules():
    passage = RetrievedPassage(
        chunk_id=UUID("22222222-2222-4222-8222-222222222222"),
        document_id=UUID("11111111-1111-4111-8111-111111111111"),
        chunk_index=0,
        content="Products and services net sales were $383 billion.",
        page=42,
        section="Item 7 > Net sales",
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_type="10-K",
        filing_date=date(2024, 11, 1),
        fiscal_year=2024,
        source_url="https://example.com",
        rrf_score=0.2,
        citation_label=1,
    )
    text = format_grounding_system_addendum([passage])
    assert "[1]" in text
    assert "Answer only using the passages below" in text
    assert "383 billion" in text
    assert "[context]" not in text


def test_format_omits_neighbor_passages():
    citable = RetrievedPassage(
        chunk_id=UUID("22222222-2222-4222-8222-222222222222"),
        document_id=UUID("11111111-1111-4111-8111-111111111111"),
        chunk_index=0,
        content="Citable body.",
        page=1,
        section="Item 7",
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_type="10-K",
        filing_date=date(2024, 11, 1),
        fiscal_year=2024,
        source_url="https://example.com",
        rrf_score=0.2,
        citation_label=1,
    )
    neighbor = RetrievedPassage(
        chunk_id=UUID("33333333-3333-4333-8333-333333333333"),
        document_id=UUID("11111111-1111-4111-8111-111111111111"),
        chunk_index=1,
        content="Neighbor only.",
        page=1,
        section="Item 7",
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_type="10-K",
        filing_date=date(2024, 11, 1),
        fiscal_year=2024,
        source_url="https://example.com",
        rrf_score=None,
        citation_label=None,
        is_neighbor=True,
    )
    text = format_grounding_system_addendum([citable, neighbor])
    assert "Citable body." in text
    assert "Neighbor only." not in text
