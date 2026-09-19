from types import SimpleNamespace
from uuid import UUID

import pytest

from ingest.chunks import (
    MAX_EMBED_TOKENS,
    MODEL_TOKEN_LIMIT,
    doc_chunk_to_row,
    extract_page,
    extract_section,
    should_keep_chunk,
)

DOCUMENT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _chunk(*, headings=None, captions=None, page=None):
    items = []
    if page is not None:
        items.append(SimpleNamespace(prov=[SimpleNamespace(page_no=page)]))
    return SimpleNamespace(
        text="body",
        meta=SimpleNamespace(
            doc_items=items,
            headings=headings,
            captions=captions,
        ),
    )


def _filing(**overrides):
    filing = {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "form": "10-K",
        "filing_date": "2025-10-31",
        "report_date": "2025-09-27",
        "accession_number": "0000320193-25-000079",
        "local_path": r"2025\aapl_10-k_2025-10-31_0000320193-25-000079.htm",
    }
    filing.update(overrides)
    return filing


def test_token_budget_stays_under_embedding_limit():
    assert MAX_EMBED_TOKENS == 512
    assert MAX_EMBED_TOKENS < MODEL_TOKEN_LIMIT
    assert MODEL_TOKEN_LIMIT == 8192


def test_should_keep_chunk_drops_empty_sec_tables():
    assert should_keep_chunk("Item 1A. Risk Factors")
    assert not should_keep_chunk("   \n")
    assert not should_keep_chunk("|    |    |\n|----|----|")


def test_extract_page_uses_first_provenance_and_does_not_invent():
    assert extract_page(_chunk(page=12)) == 12
    assert extract_page(_chunk()) is None


def test_extract_section_joins_headings():
    assert (
        extract_section(_chunk(headings=["Part I", "Item 1A. Risk Factors"]))
        == "Part I > Item 1A. Risk Factors"
    )
    assert extract_section(_chunk(headings=[])) is None


def test_doc_chunk_to_row_maps_page_section_and_metadata():
    embedding = [0.0] * 8
    row = doc_chunk_to_row(
        document_id=DOCUMENT_ID,
        chunk_index=3,
        content="Part I\nRisks about supply.",
        token_count=12,
        embedding=embedding,
        chunk=_chunk(headings=["Part I"], captions=["Risk table"], page=7),
        filing=_filing(),
    )

    assert row.document_id == DOCUMENT_ID
    assert row.chunk_index == 3
    assert row.page == 7
    assert row.section == "Part I"
    assert row.token_count == 12
    assert row.chunk_metadata["ticker"] == "AAPL"
    assert row.chunk_metadata["fiscal_year"] == 2025
    assert row.chunk_metadata["headings"] == ["Part I"]
    assert row.chunk_metadata["captions"] == ["Risk table"]
    assert row.chunk_metadata["source_html_path"].endswith(".htm")


def test_doc_chunk_to_row_rejects_over_limit_tokens():
    with pytest.raises(ValueError, match="exceeds embedding limit"):
        doc_chunk_to_row(
            document_id=DOCUMENT_ID,
            chunk_index=0,
            content="too long",
            token_count=MODEL_TOKEN_LIMIT + 1,
            embedding=[0.0],
            chunk=_chunk(),
            filing=_filing(),
        )
