from datetime import date

import pytest

from ingest.source_records import (
    LOADABLE_STATUSES,
    company_name_for,
    document_from_filing,
)


def _filing(**overrides):
    filing = {
        "ticker": "AAPL",
        "cik": "0000320193",
        "form": "10-K",
        "filing_date": "2025-10-31",
        "report_date": "2025-09-27",
        "accession_number": "0000320193-25-000079",
        "primary_document": "aapl-20250927.htm",
        "source_url": "https://www.sec.gov/Archives/edgar/data/320193/aapl.htm",
        "status": "success",
    }
    filing.update(overrides)
    return filing


def test_document_from_filing_maps_manifest_fields():
    document = document_from_filing(_filing(), "# Apple 10-K\n")

    assert document.ticker == "AAPL"
    assert document.company_name == "Apple Inc."
    assert document.cik == "0000320193"
    assert document.filing_type == "10-K"
    assert document.filing_date == date(2025, 10, 31)
    assert document.report_date == date(2025, 9, 27)
    assert document.fiscal_year == 2025
    assert document.accession_number == "0000320193-25-000079"
    assert document.primary_document == "aapl-20250927.htm"
    assert document.markdown_content == "# Apple 10-K\n"


def test_fiscal_year_falls_back_to_filing_date():
    document = document_from_filing(_filing(report_date=""), "# body\n")

    assert document.report_date is None
    assert document.fiscal_year == 2025


def test_unknown_ticker_fails_loudly():
    with pytest.raises(ValueError, match="Unknown ticker"):
        document_from_filing(_filing(ticker="XYZ"), "x")


def test_loadable_statuses_match_markdown_manifest():
    assert "success" in LOADABLE_STATUSES
    assert "exists" in LOADABLE_STATUSES
    assert company_name_for("MSFT") == "Microsoft Corporation"
