"""Reciprocal Rank Fusion — fuse ranked chunk-id lists without mixing score scales.

Same algorithm as ai-cookbook knowledge/hybrid-retrieval (k=60, rank-based).
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

RRF_K = 60


def reciprocal_rank_fusion(
    rankings: list[list[UUID]], *, k: int = RRF_K
) -> list[tuple[UUID, float]]:
    scores: dict[UUID, float] = defaultdict(float)
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: -item[1])
