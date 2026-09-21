from __future__ import annotations

from openai import AsyncOpenAI

from app.config import settings


async def embed_query(
    client: AsyncOpenAI,
    *,
    text: str,
    model: str | None = None,
    dimensions: int | None = None,
) -> list[float]:
    model_name = model or settings.openai_embedding_model
    dim = dimensions or settings.openai_embedding_dimensions
    response = await client.embeddings.create(
        model=model_name,
        input=text,
        dimensions=dim,
    )
    vector = response.data[0].embedding
    if len(vector) != dim:
        raise ValueError(f"Expected {dim}-dim query embedding, got {len(vector)}")
    return vector
