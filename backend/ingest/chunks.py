from __future__ import annotations

from typing import Any
from uuid import UUID

from app.database.models import DocumentChunk

# text-embedding-3-small hard limit is 8192. Retrieval chunks stay smaller
# because contextualize() prepends headings.
MODEL_TOKEN_LIMIT = 8192
MAX_EMBED_TOKENS = 512


def should_keep_chunk(text: str) -> bool:
    return any(char.isalnum() for char in text)


def extract_page(chunk: object) -> int | None:
    # First real provenance page only. HTML 10-Ks often have none — do not invent.
    items = getattr(getattr(chunk, "meta", None), "doc_items", None) or []
    for item in items:
        for provenance in getattr(item, "prov", None) or []:
            page = getattr(provenance, "page_no", None)
            if page is not None:
                return int(page)
    return None


def extract_section(chunk: object) -> str | None:
    headings = _string_list(getattr(getattr(chunk, "meta", None), "headings", None))
    if not headings:
        return None
    return " > ".join(headings)


def extract_captions(chunk: object) -> list[str]:
    return _string_list(getattr(getattr(chunk, "meta", None), "captions", None))


def extract_headings(chunk: object) -> list[str]:
    return _string_list(getattr(getattr(chunk, "meta", None), "headings", None))


def _string_list(value: object) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def filing_fiscal_year(filing: dict[str, Any]) -> int:
    report = filing.get("report_date") or filing["filing_date"]
    return int(str(report)[:4])


def doc_chunk_to_row(
    *,
    document_id: UUID,
    chunk_index: int,
    content: str,
    token_count: int,
    embedding: list[float],
    chunk: object,
    filing: dict[str, Any],
) -> DocumentChunk:
    if token_count > MODEL_TOKEN_LIMIT:
        raise ValueError(
            f"Chunk token_count {token_count} exceeds embedding limit {MODEL_TOKEN_LIMIT}"
        )
    page = extract_page(chunk)
    section = extract_section(chunk)
    return DocumentChunk(
        document_id=document_id,
        chunk_index=chunk_index,
        page=page,
        section=section,
        content=content,
        token_count=token_count,
        embedding=embedding,
        chunk_metadata={
            "ticker": filing["ticker"],
            "company_name": filing.get("company_name"),
            "filing_type": filing.get("form"),
            "filing_date": filing.get("filing_date"),
            "fiscal_year": filing_fiscal_year(filing),
            "accession_number": filing["accession_number"],
            "headings": extract_headings(chunk),
            "captions": extract_captions(chunk),
            "source_html_path": str(filing.get("local_path") or ""),
        },
    )
