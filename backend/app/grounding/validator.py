"""Citation validation against retrieved passages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from app.database.models import MessageCitation
from app.grounding.types import CitationDraft
from app.retrieval.types import RetrievedPassage

_CITATION_LABEL_RE = re.compile(r"\[(\d+)\]")


@dataclass(frozen=True, slots=True)
class GroundingValidationResult:
    ok: bool
    cited_labels: tuple[int, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CanonicalizedAnswer:
    """Answer text with contiguous [1]..[k] markers; cited_labels are retrieval labels."""

    text: str
    cited_labels: tuple[int, ...]


def extract_citation_labels(answer_text: str) -> list[int]:
    labels: list[int] = []
    for match in _CITATION_LABEL_RE.finditer(answer_text):
        labels.append(int(match.group(1)))
    return labels


def validate_answer_citations(
    answer_text: str,
    passages: list[RetrievedPassage],
    *,
    require_citation_when_evidence: bool = True,
) -> GroundingValidationResult:
    citable = [p for p in passages if p.citation_label is not None]
    labels = extract_citation_labels(answer_text)
    errors: list[str] = []

    if not citable:
        if require_citation_when_evidence and _looks_like_factual_claim(answer_text):
            errors.append("answer cites facts but no passages were retrieved")
        return GroundingValidationResult(
            ok=not errors,
            cited_labels=tuple(labels),
            errors=tuple(errors),
        )

    valid_labels = {p.citation_label for p in citable if p.citation_label is not None}
    for label in labels:
        if label not in valid_labels:
            errors.append(f"citation [{label}] is not in retrieved passages")

    if (
        require_citation_when_evidence
        and not labels
        and _looks_like_factual_claim(answer_text)
        and not _is_insufficient_evidence_answer(answer_text)
    ):
        errors.append("factual answer missing citation labels like [1]")

    return GroundingValidationResult(
        ok=not errors,
        cited_labels=tuple(labels),
        errors=tuple(errors),
    )


def canonicalize_answer_citations(
    answer_text: str,
    passages: list[RetrievedPassage],
) -> CanonicalizedAnswer | None:
    """Validate citations, then rewrite markers to contiguous [1]..[k] for the UI."""
    validation = validate_answer_citations(answer_text, passages)
    if not validation.ok:
        return None

    labels_in_order: list[int] = []
    seen: set[int] = set()
    for label in extract_citation_labels(answer_text):
        if label not in seen:
            seen.add(label)
            labels_in_order.append(label)

    if not labels_in_order:
        return CanonicalizedAnswer(text=answer_text, cited_labels=())

    mapping = {old: new for new, old in enumerate(labels_in_order, start=1)}

    def _replace(match: re.Match[str]) -> str:
        old = int(match.group(1))
        if old in mapping:
            return f"[{mapping[old]}]"
        return match.group(0)

    rewritten = _CITATION_LABEL_RE.sub(_replace, answer_text)
    return CanonicalizedAnswer(text=rewritten, cited_labels=tuple(labels_in_order))


def build_message_citations(
    passages: list[RetrievedPassage],
    cited_labels: list[int],
    *,
    excerpt_max_chars: int = 500,
) -> list[CitationDraft]:
    by_label = {
        p.citation_label: p
        for p in passages
        if p.citation_label is not None
    }
    citations: list[CitationDraft] = []
    seen: set[int] = set()
    sort_order = 0
    for label in cited_labels:
        if label in seen or label not in by_label:
            continue
        seen.add(label)
        passage = by_label[label]
        excerpt = passage.content.strip()
        if len(excerpt) > excerpt_max_chars:
            excerpt = excerpt[: excerpt_max_chars - 1].rstrip() + "…"
        citations.append(
            CitationDraft(
                chunk_id=passage.chunk_id,
                document_id=passage.document_id,
                excerpt=excerpt,
                page=passage.page,
                sort_order=sort_order,
            )
        )
        sort_order += 1
    return citations


def drafts_to_message_citations(
    message_id: UUID,
    drafts: list[CitationDraft],
) -> list[MessageCitation]:
    return [
        MessageCitation(
            message_id=message_id,
            chunk_id=draft.chunk_id,
            document_id=draft.document_id,
            excerpt=draft.excerpt,
            page=draft.page,
            sort_order=draft.sort_order,
        )
        for draft in drafts
    ]


def passage_by_label(
    passages: list[RetrievedPassage],
) -> dict[int, RetrievedPassage]:
    return {
        p.citation_label: p
        for p in passages
        if p.citation_label is not None
    }


def _looks_like_factual_claim(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 40:
        return False
    lowered = stripped.lower()
    if _is_insufficient_evidence_answer(stripped):
        return False
    refusal_phrases = (
        "i don't know",
        "i cannot",
        "i can't",
        "not enough evidence",
        "insufficient evidence",
    )
    return not any(phrase in lowered for phrase in refusal_phrases)


def _is_insufficient_evidence_answer(text: str) -> bool:
    lowered = text.lower()
    return (
        "not enough evidence" in lowered
        or "insufficient evidence" in lowered
        or "does not contain enough evidence" in lowered
        or "don't have enough evidence" in lowered
    )
