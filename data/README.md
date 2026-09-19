# Data

Local data artifacts for development live here.

- `downloads/` holds raw HTML filings from SEC EDGAR, grouped by year, plus `manifest.json`.
- `markdown/` holds the Docling conversions of those filings, same year folders and a matching manifest.
- Both payload trees are gitignored because the corpus can get large.
- Fetch a sample corpus with `uv run data/download.py`.
- Convert HTML to Markdown from `backend/` with `uv run python -m ingest.to_markdown`.
- Load Markdown into `source_documents` with `uv run python -m ingest.load_documents`.
- Chunk HTML from `downloads/` and write embeddings to `document_chunks` with `uv run python -m ingest.chunk_and_embed`. 
