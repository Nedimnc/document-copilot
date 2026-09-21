"""Retrieve corpus passages and format grounding context for one chat turn."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.grounding.context import format_grounding_system_addendum
from app.grounding.refusal import INSUFFICIENT_EVIDENCE_USER_MESSAGE
from app.retrieval.retriever import DocumentRetriever, citable_passages
from app.retrieval.types import RetrievedPassage


@dataclass(frozen=True, slots=True)
class GroundedTurnContext:
    query: str
    passages: list[RetrievedPassage]
    system_addendum: str
    has_citable_evidence: bool
    refusal_message: str | None


async def prepare_grounded_turn(
    session: AsyncSession,
    *,
    query: str,
    retriever: DocumentRetriever | None = None,
) -> GroundedTurnContext:
    active = retriever or DocumentRetriever()
    passages = await active.retrieve(session, query=query)
    citable = citable_passages(passages)
    return GroundedTurnContext(
        query=query,
        passages=passages,
        system_addendum=format_grounding_system_addendum(passages),
        has_citable_evidence=bool(citable),
        refusal_message=None if citable else INSUFFICIENT_EVIDENCE_USER_MESSAGE,
    )
