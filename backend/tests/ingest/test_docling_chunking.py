"""Regression tests for chunk table serialization (requires docling dev deps)."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "sec_revenue_table.html"

pytest.importorskip("docling")

from ingest.chunk_and_embed import (
    build_chunker,
    build_html_converter,
    convert_html,
    iter_kept_chunks,
)
from ingest.docling_chunking import looks_like_triplet_table_serialization


@pytest.fixture(scope="module")
def table_chunk_texts() -> list[str]:
    converter = build_html_converter()
    chunker = build_chunker("text-embedding-3-small")
    document = convert_html(converter, FIXTURE)
    kept = iter_kept_chunks(chunker, document)
    return [text for _chunk, text in kept]


def test_table_chunks_use_markdown_not_triplets(table_chunk_texts: list[str]):
    assert table_chunk_texts, "expected at least one chunk from revenue table fixture"
    combined = "\n".join(table_chunk_texts)
    assert "Total net sales" in combined
    assert "383,285" in combined or "383285" in combined.replace(",", "")
    assert not looks_like_triplet_table_serialization(combined)
    # Pipe-table serialization should appear when a table is present in a chunk.
    assert any("|" in text for text in table_chunk_texts)


def test_triplet_detector_flags_legacy_shape():
    noisy = (
        "(3), 23 = %. Services (3), 24 = . Total net sales, 1 = Total net sales. "
        "Products (1), 22 = 100."
    )
    assert looks_like_triplet_table_serialization(noisy)
