"""One-off Phase 3 corpus validation. Not imported by the app."""

from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from openai import AsyncOpenAI
from sqlalchemy import func, select, text

from app.config import get_settings
from app.database.models import DocumentChunk, SourceDocument
from app.database.session import get_session_factory
from app.retrieval.retriever import (
    DocumentRetriever,
    RetrievalOptions,
    citable_passages,
)
from ingest.docling_chunking import looks_like_triplet_table_serialization

REPO_ROOT = _BACKEND_ROOT.parent
DOWNLOADS_MANIFEST = REPO_ROOT / "data" / "downloads" / "manifest.json"
MARKDOWN_MANIFEST = REPO_ROOT / "data" / "markdown" / "manifest.json"
SAMPLE_QUERIES = [
    "Apple risk factors related to supply chain",
    "NVIDIA data center revenue",
    "Microsoft cloud Azure operating income",
]


def _load_filings(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["filings"]


async def validate() -> int:
    settings = get_settings()
    download_filings = _load_filings(DOWNLOADS_MANIFEST)
    markdown_filings = _load_filings(MARKDOWN_MANIFEST)
    expected_accessions = {filing["accession_number"] for filing in download_filings}
    triplet_hits = 0

    factory = get_session_factory()
    async with factory() as session:
        documents = list(
            (
                await session.execute(
                    select(SourceDocument).order_by(
                        SourceDocument.ticker, SourceDocument.filing_date
                    )
                )
            ).scalars()
        )
        doc_count = len(documents)
        chunk_count = int(
            (await session.execute(select(func.count()).select_from(DocumentChunk))).scalar_one()
        )
        missing_embedding = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(DocumentChunk)
                    .where(DocumentChunk.embedding.is_(None))
                )
            ).scalar_one()
        )
        empty_search = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(DocumentChunk)
                    .where(DocumentChunk.search_vector.is_(None))
                )
            ).scalar_one()
        )
        over_limit = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(DocumentChunk)
                    .where(DocumentChunk.token_count > 8192)
                )
            ).scalar_one()
        )
        empty_content = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(DocumentChunk)
                    .where(func.length(func.trim(DocumentChunk.content)) == 0)
                )
            ).scalar_one()
        )
        with_page = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(DocumentChunk)
                    .where(DocumentChunk.page.is_not(None))
                )
            ).scalar_one()
        )
        with_section = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(DocumentChunk)
                    .where(DocumentChunk.section.is_not(None))
                )
            ).scalar_one()
        )
        token_stats = (
            await session.execute(
                select(
                    func.min(DocumentChunk.token_count),
                    func.avg(DocumentChunk.token_count),
                    func.max(DocumentChunk.token_count),
                )
            )
        ).one()
        dim_row = (
            await session.execute(
                text(
                    "select vector_dims(embedding) as dims, count(*) "
                    "from document_chunks group by 1 order by 2 desc"
                )
            )
        ).all()
        docs_without_chunks = (
            await session.execute(
                select(SourceDocument.ticker, SourceDocument.accession_number)
                .outerjoin(DocumentChunk, DocumentChunk.document_id == SourceDocument.id)
                .group_by(SourceDocument.id)
                .having(func.count(DocumentChunk.id) == 0)
            )
        ).all()
        chunks_per_ticker = (
            await session.execute(
                select(SourceDocument.ticker, func.count(DocumentChunk.id))
                .join(DocumentChunk, DocumentChunk.document_id == SourceDocument.id)
                .group_by(SourceDocument.ticker)
                .order_by(SourceDocument.ticker)
            )
        ).all()
        metadata_sample = (
            await session.execute(
                select(DocumentChunk.chunk_metadata).limit(5)
            )
        ).scalars().all()
        missing_meta = int(
            (
                await session.execute(
                    text(
                        """
                        select count(*) from document_chunks
                        where chunk_metadata->>'ticker' is null
                           or chunk_metadata->>'accession_number' is null
                           or chunk_metadata->>'fiscal_year' is null
                        """
                    )
                )
            ).scalar_one()
        )
        heading_stats = (
            await session.execute(
                text(
                    """
                    select
                      count(*) filter (
                        where jsonb_array_length(
                          coalesce(chunk_metadata->'headings', '[]'::jsonb)
                        ) > 0
                      ) as with_headings,
                      count(*) filter (
                        where jsonb_array_length(
                          coalesce(chunk_metadata->'captions', '[]'::jsonb)
                        ) > 0
                      ) as with_captions
                    from document_chunks
                    """
                )
            )
        ).one()
        metadata_examples = (
            await session.execute(
                text(
                    """
                    select left(content, 180) as content,
                           chunk_metadata->'headings' as headings,
                           chunk_metadata->'captions' as captions
                    from document_chunks
                    order by chunk_index
                    limit 6
                    """
                )
            )
        ).all()
        index_rows = (
            await session.execute(
                text(
                    """
                    select indexname from pg_indexes
                    where tablename = 'document_chunks'
                    order by indexname
                    """
                )
            )
        ).scalars().all()

        print("=== local corpus ===")
        print(f"download_filings={len(download_filings)}")
        print(f"markdown_filings={len(markdown_filings)}")
        print(f"download_accessions={len(expected_accessions)}")

        print("\n=== source_documents ===")
        print(f"rows={doc_count}")
        db_accessions = {doc.accession_number for doc in documents}
        print(f"missing_vs_download={sorted(expected_accessions - db_accessions)}")
        print(f"extra_vs_download={sorted(db_accessions - expected_accessions)}")
        print(f"empty_markdown={sum(1 for doc in documents if not doc.markdown_content.strip())}")
        print(f"tickers={sorted({doc.ticker for doc in documents})}")
        print(f"filing_types={sorted({doc.filing_type for doc in documents})}")
        print(f"docs_without_chunks={docs_without_chunks}")

        print("\n=== document_chunks ===")
        print(f"rows={chunk_count}")
        print(f"missing_embedding={missing_embedding}")
        print(f"empty_search_vector={empty_search}")
        print(f"over_token_limit={over_limit}")
        print(f"empty_content={empty_content}")
        print(f"with_page={with_page} ({with_page / chunk_count:.1%})")
        print(f"with_section={with_section} ({with_section / chunk_count:.1%})")
        print(
            "token_min_avg_max="
            f"{token_stats[0]} {float(token_stats[1]):.1f} {token_stats[2]}"
        )
        print(f"embedding_dims={dim_row}")
        print(f"missing_required_metadata={missing_meta}")
        print(f"with_headings={heading_stats.with_headings}")
        print(f"with_captions={heading_stats.with_captions}")
        print(f"chunks_per_ticker={chunks_per_ticker}")
        for example in metadata_examples:
            print(
                "chunk_example "
                f"headings={example.headings} captions={example.captions} "
                f"content={example.content!r}"
            )
        print(f"chunk_indexes={index_rows}")
        print(f"metadata_sample_keys={[sorted(row.keys()) for row in metadata_sample]}")

        triplet_sample = (
            await session.execute(
                select(DocumentChunk.content).order_by(func.random()).limit(400)
            )
        ).scalars().all()
        triplet_hits = sum(
            1 for content in triplet_sample if looks_like_triplet_table_serialization(content)
        )
        print("\n=== chunk text quality (sample) ===")
        print(f"triplet_artifact_chunks={triplet_hits} of {len(triplet_sample)} sampled")

        print("\n=== sample retrieval ===")
        retriever = DocumentRetriever(
            openai_client=AsyncOpenAI(api_key=settings.openai_api_key)
        )
        retrieval_ok = True
        for query in SAMPLE_QUERIES:
            passages = await retriever.retrieve(
                session,
                query=query,
                options=RetrievalOptions(include_neighbors=True),
            )
            citable = citable_passages(passages)
            neighbors = [p for p in passages if p.is_neighbor]
            tickers = Counter(p.ticker for p in citable)
            print(
                f"query={query!r} citable={len(citable)} neighbors={len(neighbors)} "
                f"tickers={dict(tickers)}"
            )
            for passage in citable[:3]:
                snippet = " ".join(passage.content.split())[:140]
                print(
                    f"  [{passage.citation_label}] {passage.ticker} "
                    f"{passage.fiscal_year} {passage.section or '-'} "
                    f"page={passage.page} score={passage.rrf_score:.4f} {snippet}"
                )
            if len(citable) == 0:
                retrieval_ok = False

    expected_docs = 25
    expected_chunks = 7013
    expected_dim = settings.openai_embedding_dimensions
    failures: list[str] = []
    if doc_count != expected_docs:
        failures.append(f"expected {expected_docs} source_documents, got {doc_count}")
    if chunk_count != expected_chunks:
        failures.append(f"expected {expected_chunks} chunks, got {chunk_count}")
    if expected_accessions != db_accessions:
        failures.append("source_documents accessions do not match download manifest")
    if missing_embedding:
        failures.append("chunks missing embeddings")
    if empty_search:
        failures.append("chunks missing search_vector")
    if over_limit:
        failures.append("chunks exceed embedding token limit")
    if empty_content:
        failures.append("chunks have empty content")
    if missing_meta:
        failures.append("chunks missing ticker/accession/fiscal_year metadata")
    if docs_without_chunks:
        failures.append("source documents without chunks")
    if any(dims != expected_dim for dims, _count in dim_row):
        failures.append(f"embedding dims not {expected_dim}: {dim_row}")
    if "document_chunks_embedding_hnsw" not in index_rows:
        failures.append("missing HNSW embedding index")
    if "document_chunks_search_vector_gin" not in index_rows:
        failures.append("missing GIN search_vector index")
    if not retrieval_ok:
        failures.append("sample retrieval returned no citable passages")
    if triplet_hits > 0:
        failures.append(
            f"{triplet_hits} sampled chunks look like triplet table serialization; "
            "re-run ingest.chunk_and_embed --force after deploying markdown table chunks"
        )

    print("\n=== verdict ===")
    if failures:
        for item in failures:
            print(f"FAIL {item}")
        return 1
    print("PASS corpus + sample retrieval look complete for Phase 3")
    return 0


def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(validate()))


if __name__ == "__main__":
    main()
