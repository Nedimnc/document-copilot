"""Parse local SEC HTML, HybridChunk, embed, and write document_chunks.

Does not run on import. HybridChunker already uses HierarchicalChunker internally.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

import tiktoken
from openai import AsyncOpenAI

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from docling.chunking import HybridChunker
from docling.datamodel.backend_options import HTMLBackendOptions
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.document_converter import DocumentConverter, HTMLFormatOption
from docling.exceptions import ConversionError
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

from app.config import get_settings
from app.database.documents import (
    add_chunks,
    delete_chunks_for_document,
    get_chunks_for_document,
    get_source_document_by_accession,
)
from app.database.session import get_session_factory
from ingest.chunks import (
    MAX_EMBED_TOKENS,
    doc_chunk_to_row,
    should_keep_chunk,
)
from ingest.paths import load_source_manifest

REPO_ROOT = _BACKEND_ROOT.parent
DOWNLOADS_DIR = REPO_ROOT / "data" / "downloads"
EMBED_BATCH_SIZE = 64


def build_html_converter() -> DocumentConverter:
    return DocumentConverter(
        allowed_formats=[InputFormat.HTML],
        format_options={
            InputFormat.HTML: HTMLFormatOption(
                backend_options=HTMLBackendOptions(fetch_images=False)
            )
        },
    )


def build_chunker(model: str) -> HybridChunker:
    tokenizer = OpenAITokenizer(
        tokenizer=tiktoken.encoding_for_model(model),
        max_tokens=MAX_EMBED_TOKENS,
    )
    return HybridChunker(tokenizer=tokenizer, merge_peers=True)


def convert_html(converter: DocumentConverter, html_path: Path) -> Any:
    result = converter.convert(html_path)
    if result.status not in {
        ConversionStatus.SUCCESS,
        ConversionStatus.PARTIAL_SUCCESS,
    }:
        raise RuntimeError(f"Docling status {result.status.value}")
    return result.document


def iter_kept_chunks(
    chunker: HybridChunker, document: Any
) -> list[tuple[object, str]]:
    kept: list[tuple[object, str]] = []
    for chunk in chunker.chunk(dl_doc=document):
        text = chunker.contextualize(chunk)
        if should_keep_chunk(text):
            kept.append((chunk, text))
    return kept


async def embed_texts(
    client: AsyncOpenAI,
    *,
    model: str,
    texts: list[str],
    dimensions: int,
) -> list[list[float]]:
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start : start + EMBED_BATCH_SIZE]
        response = await client.embeddings.create(model=model, input=batch)
        ordered = sorted(response.data, key=lambda item: item.index)
        if len(ordered) != len(batch):
            raise ValueError("Embedding batch size mismatch")
        for item in ordered:
            if len(item.embedding) != dimensions:
                raise ValueError(
                    f"Expected {dimensions}-dim embedding, got {len(item.embedding)}"
                )
            vectors.append(item.embedding)
    return vectors


async def chunk_and_embed(
    *,
    force: bool = False,
    limit: int | None = None,
) -> dict[str, int]:
    settings = get_settings()
    source = load_source_manifest(DOWNLOADS_DIR / "manifest.json")
    filings = list(source["filings"])
    if limit is not None:
        filings = filings[:limit]

    converter = build_html_converter()
    chunker = build_chunker(settings.openai_embedding_model)
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    counts = {
        "documents": 0,
        "chunks": 0,
        "skipped": 0,
        "missing_html": 0,
        "missing_document": 0,
        "failed": 0,
    }

    factory = get_session_factory()
    async with factory() as session:
        for filing in filings:
            html_rel = Path(filing["local_path"])
            html_path = DOWNLOADS_DIR / html_rel
            accession = filing["accession_number"]
            ticker = filing["ticker"]

            if not html_path.is_file():
                counts["missing_html"] += 1
                print(f"missing html {html_rel}")
                continue

            document = await get_source_document_by_accession(session, accession)
            if document is None:
                counts["missing_document"] += 1
                print(f"missing source_documents {ticker} {accession}")
                continue

            existing = await get_chunks_for_document(session, document.id)
            if existing and not force:
                counts["skipped"] += 1
                print(f"skip {ticker} {accession} ({len(existing)} chunks)")
                continue

            print(f"chunk {ticker} {accession}")
            try:
                dl_doc = convert_html(converter, html_path)
                kept = iter_kept_chunks(chunker, dl_doc)
                texts = [text for _chunk, text in kept]
                embeddings = await embed_texts(
                    client,
                    model=settings.openai_embedding_model,
                    texts=texts,
                    dimensions=settings.openai_embedding_dimensions,
                )
            except (ConversionError, RuntimeError, ValueError, OSError) as exc:
                counts["failed"] += 1
                print(f"failed {ticker} {accession}: {exc}")
                continue

            if force and existing:
                await delete_chunks_for_document(session, document.id)

            rows = _rows_for_document(
                document_id=document.id,
                filing={**filing, "company_name": document.company_name},
                kept=kept,
                embeddings=embeddings,
                tokenizer=chunker.tokenizer,
            )
            await add_chunks(session, rows)
            counts["documents"] += 1
            counts["chunks"] += len(rows)
            print(f"wrote {len(rows)} chunks for {ticker} {accession}")

        await session.commit()
    return counts


def _rows_for_document(
    *,
    document_id: UUID,
    filing: dict[str, Any],
    kept: list[tuple[object, str]],
    embeddings: list[list[float]],
    tokenizer: OpenAITokenizer,
) -> list[Any]:
    rows = []
    for index, ((chunk, text), embedding) in enumerate(zip(kept, embeddings, strict=True)):
        rows.append(
            doc_chunk_to_row(
                document_id=document_id,
                chunk_index=index,
                content=text,
                token_count=tokenizer.count_tokens(text),
                embedding=embedding,
                chunk=chunk,
                filing=filing,
            )
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and rewrite chunks when the document already has rows",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N filings from the download manifest",
    )
    args = parser.parse_args()
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    counts = asyncio.run(chunk_and_embed(force=args.force, limit=args.limit))
    print(
        "document_chunks "
        f"documents={counts['documents']} chunks={counts['chunks']} "
        f"skipped={counts['skipped']} missing_html={counts['missing_html']} "
        f"missing_document={counts['missing_document']} failed={counts['failed']}"
    )


if __name__ == "__main__":
    main()
