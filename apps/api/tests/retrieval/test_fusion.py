"""Reciprocal-rank fusion and deduplication tests."""

from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import OpenSearchHit

from .conftest import make_hit


def _hit(chunk_id: str, score: float) -> OpenSearchHit:
    return OpenSearchHit.model_validate(
        make_hit(chunk_id=chunk_id, text=f"Synthetic content {chunk_id}", score=score)
    )


def test_rrf_combines_ranks_and_deduplicates_source_chunks() -> None:
    shared = _hit("shared", 9.0)
    lexical = (shared, shared, _hit("lexical", 8.0))
    vector = (_hit("vector", 7.0), shared)

    results = reciprocal_rank_fusion(
        lexical_hits=lexical,
        vector_hits=vector,
        limit=10,
        rank_constant=60,
    )

    assert [result.source_chunk_id for result in results] == ["shared", "vector", "lexical"]
    assert results[0].lexical_rank == 1
    assert results[0].vector_rank == 2
    assert len({result.source_chunk_id for result in results}) == len(results)


def test_rrf_rejects_invalid_rank_constant() -> None:
    try:
        reciprocal_rank_fusion(lexical_hits=(), vector_hits=(), limit=1, rank_constant=0)
    except ValueError as error:
        assert str(error) == "rank_constant must be positive"
    else:
        raise AssertionError("Expected invalid rank constant to fail")


def test_rrf_limits_chunks_per_document_before_fusion() -> None:
    first = _hit("source-a-1", 4.0)
    second_payload = make_hit(
        chunk_id="source-a-2", text="Synthetic second chunk", score=3.0
    )
    second_source = second_payload["_source"]
    assert isinstance(second_source, dict)
    second_source["document_id"] = first.source.document_id
    second = OpenSearchHit.model_validate(second_payload)
    third = _hit("source-b-1", 2.0)

    limited = reciprocal_rank_fusion(
        lexical_hits=(first, second, third),
        vector_hits=(first, second, third),
        limit=3,
        max_chunks_per_document=1,
    )

    assert [item.source_chunk_id for item in limited] == ["source-a-1", "source-b-1"]
