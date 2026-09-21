from __future__ import annotations

from pydantic import BaseModel, Field


class AnswerCitation(BaseModel):
    """One bracket label tied to a retrieved passage (for structured / logged output)."""

    label: int = Field(description="Citation label matching [n] in the answer text")
    quote: str = Field(
        description="Short excerpt from the passage that supports the claim"
    )


class GroundedAnswer(BaseModel):
    answer: str = Field(description="Plain-English answer with [n] citation labels")
    citations: list[AnswerCitation] = Field(
        description="Passages backing the answer; at least one when stating facts"
    )
