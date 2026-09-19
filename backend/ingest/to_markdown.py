"""Convert downloaded SEC HTML filings to Markdown with Docling.

Reuse one HTML-only converter. Output mirrors data/downloads/ year folders
under data/markdown/ so later chunking can walk a stable tree.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from docling.datamodel.backend_options import HTMLBackendOptions
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.document_converter import DocumentConverter, HTMLFormatOption
from docling.exceptions import ConversionError

from ingest.paths import load_source_manifest, markdown_relative_path

REPO_ROOT = _BACKEND_ROOT.parent
DOWNLOADS_DIR = REPO_ROOT / "data" / "downloads"
MARKDOWN_DIR = REPO_ROOT / "data" / "markdown"


def build_converter() -> DocumentConverter:
    # HTML only — do not load the PDF/OCR stack for 10-K HTML.
    return DocumentConverter(
        allowed_formats=[InputFormat.HTML],
        format_options={
            InputFormat.HTML: HTMLFormatOption(
                backend_options=HTMLBackendOptions(fetch_images=False)
            )
        },
    )


def convert_filing(
    converter: DocumentConverter, html_path: Path
) -> tuple[ConversionStatus, str]:
    result = converter.convert(html_path)
    if result.status not in {
        ConversionStatus.SUCCESS,
        ConversionStatus.PARTIAL_SUCCESS,
    }:
        raise RuntimeError(f"Docling status {result.status.value}")
    return result.status, result.document.export_to_markdown()


def convert_corpus(
    *,
    downloads_dir: Path = DOWNLOADS_DIR,
    markdown_dir: Path = MARKDOWN_DIR,
    force: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    source = load_source_manifest(downloads_dir / "manifest.json")
    filings = source["filings"]
    if limit is not None:
        filings = filings[:limit]

    markdown_dir.mkdir(parents=True, exist_ok=True)
    converter = build_converter()

    converted: list[dict[str, Any]] = []
    for filing in filings:
        html_rel = Path(filing["local_path"])
        md_rel = markdown_relative_path(str(html_rel))
        html_path = downloads_dir / html_rel
        md_path = markdown_dir / md_rel
        record = {
            **filing,
            "source_html_path": html_rel.as_posix(),
            "local_path": md_rel.as_posix(),
        }

        if not html_path.is_file():
            record["status"] = "missing_html"
            converted.append(record)
            print(f"missing {html_rel}")
            continue

        if md_path.is_file() and not force:
            record["status"] = "exists"
            converted.append(record)
            print(f"skip {md_rel}")
            continue

        print(f"convert {html_rel}")
        try:
            status, markdown = convert_filing(converter, html_path)
        except (ConversionError, RuntimeError, ValueError, OSError) as exc:
            record["status"] = "failed"
            record["error"] = str(exc)
            converted.append(record)
            print(f"failed {html_rel}: {exc}")
            continue

        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
        record["status"] = status.value
        converted.append(record)

    manifest = {
        "source": source.get("source", "SEC EDGAR"),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "form": source.get("form", "10-K"),
        "converted_count": sum(
            1
            for item in converted
            if item["status"] in {"success", "partial_success", "exists"}
        ),
        "filings": converted,
    }
    manifest_path = markdown_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reconvert filings even if the Markdown file already exists",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Convert only the first N filings from the download manifest",
    )
    args = parser.parse_args()
    result = convert_corpus(force=args.force, limit=args.limit)
    print(
        f"Converted {result['converted_count']} filing(s) to {MARKDOWN_DIR}"
    )
    print(f"Manifest: {MARKDOWN_DIR / 'manifest.json'}")


if __name__ == "__main__":
    main()
