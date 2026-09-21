from uuid import UUID

from app.retrieval.fusion import reciprocal_rank_fusion


def _id(name: str) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{name:0>12}")


def test_rrf_boosts_docs_present_in_both_lists():
    a, b, c = _id("000000000001"), _id("000000000002"), _id("000000000003")
    semantic = [a, c]
    lexical = [b, a]
    fused = reciprocal_rank_fusion([semantic, lexical], k=60)
    assert next(chunk_id for chunk_id, _ in fused) == a


def test_rrf_respects_rank_within_single_list():
    first, second = _id("000000000010"), _id("000000000011")
    fused = reciprocal_rank_fusion([[first, second]], k=60)
    assert fused[0][0] == first
    assert fused[0][1] > fused[1][1]
