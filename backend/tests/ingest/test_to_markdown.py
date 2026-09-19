import json
from pathlib import Path

from ingest.paths import load_source_manifest, markdown_relative_path


def test_markdown_relative_path_keeps_year_and_renames_suffix():
    assert markdown_relative_path(
        r"2025\aapl_10-k_2025-10-31_0000320193-25-000079.htm"
    ) == Path("2025") / "aapl_10-k_2025-10-31_0000320193-25-000079.md"


def test_load_source_manifest_reads_filings(tmp_path: Path):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps({"filings": [{"local_path": r"2025\aapl.htm"}]}) + "\n",
        encoding="utf-8",
    )

    assert load_source_manifest(path)["filings"][0]["local_path"].endswith("aapl.htm")
