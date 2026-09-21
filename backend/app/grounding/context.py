"""Format retrieved passages for LLM grounding prompts."""

from __future__ import annotations

from app.grounding.refusal import INSUFFICIENT_EVIDENCE_INSTRUCTION
from app.retrieval.types import RetrievedPassage

_GROUNDING_RULES = """\
Answer only using the passages below. Cite evidence with bracket labels like [1], [2].
Do not cite labels that are not listed below. Do not give investment advice.
If the passages do not contain enough evidence, say so explicitly.\
"""


def format_grounding_system_addendum(passages: list[RetrievedPassage]) -> str:
    citable = [p for p in passages if p.citation_label is not None]
    if not citable:
        return f"{INSUFFICIENT_EVIDENCE_INSTRUCTION}\n\n{_GROUNDING_RULES}\n\n(No passages retrieved.)"

    blocks: list[str] = [_GROUNDING_RULES, "", "Retrieved passages:", ""]
    for passage in citable:
        blocks.append(_format_passage_block(passage))
        blocks.append("")
    return "\n".join(blocks).rstrip()


def _format_passage_block(passage: RetrievedPassage) -> str:
    header = _passage_header(passage)
    label = passage.citation_label
    assert label is not None
    return f"[{label}] {header}\n{passage.content.strip()}"


def _passage_header(passage: RetrievedPassage) -> str:
    page = f", page {passage.page}" if passage.page is not None else ""
    section = f" — {passage.section}" if passage.section else ""
    return (
        f"{passage.ticker} {passage.filing_type} "
        f"FY{passage.fiscal_year} (filed {passage.filing_date.isoformat()}"
        f"{page}){section}"
    )
