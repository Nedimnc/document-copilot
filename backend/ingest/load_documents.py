"""Load converted Markdown filings into source_documents."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.database.documents import (
    add_source_document,
    get_source_document_by_accession,
)
from app.database.models import SourceDocument
from app.database.session import get_session_factory
from ingest.paths import load_source_manifest
from ingest.source_records import LOADABLE_STATUSES, document_from_filing

REPO_ROOT = _BACKEND_ROOT.parent
MARKDOWN_DIR = REPO_ROOT / "data" / "markdown"


def apply_document_fields(target: SourceDocument, source: SourceDocument) -> None:
    target.ticker = source.ticker
    target.company_name = source.company_name
    target.cik = source.cik
    target.filing_type = source.filing_type
    target.filing_date = source.filing_date
    target.report_date = source.report_date
    target.fiscal_year = source.fiscal_year
    target.primary_document = source.primary_document
    target.source_url = source.source_url
    target.markdown_content = source.markdown_content


async def load_documents(*, force: bool = False, limit: int | None = None) -> dict[str, int]:
    source = load_source_manifest(MARKDOWN_DIR / "manifest.json")
    filings = [
        filing
        for filing in source["filings"]
        if filing.get("status") in LOADABLE_STATUSES
    ]
    if limit is not None:
        filings = filings[:limit]

    counts = {"inserted": 0, "updated": 0, "skipped": 0, "missing": 0}
    factory = get_session_factory()
    async with factory() as session:
        for filing in filings:
            md_rel = Path(filing["local_path"])
            md_path = MARKDOWN_DIR / md_rel
            if not md_path.is_file():
                counts["missing"] += 1
                print(f"missing {md_rel}")
                continue

            document = document_from_filing(filing, md_path.read_text(encoding="utf-8"))
            existing = await get_source_document_by_accession(
                session, document.accession_number
            )
            if existing is None:
                await add_source_document(session, document)
                counts["inserted"] += 1
                print(f"insert {document.ticker} {document.accession_number}")
                continue

            if not force:
                counts["skipped"] += 1
                print(f"skip {document.ticker} {document.accession_number}")
                continue

            apply_document_fields(existing, document)
            counts["updated"] += 1
            print(f"update {document.ticker} {document.accession_number}")

        await session.commit()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite markdown and metadata when the accession already exists",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Load only the first N loadable filings",
    )
    args = parser.parse_args()
    # psycopg async cannot run on Windows ProactorEventLoop.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    counts = asyncio.run(load_documents(force=args.force, limit=args.limit))
    print(
        "source_documents "
        f"inserted={counts['inserted']} updated={counts['updated']} "
        f"skipped={counts['skipped']} missing={counts['missing']}"
    )


if __name__ == "__main__":
    main()
