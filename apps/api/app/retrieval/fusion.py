"""Deterministic reciprocal-rank fusion and source-chunk deduplication."""

from dataclasses import dataclass

from app.retrieval.models import OpenSearchHit, RetrievalResult


@dataclass
class _FusedHit:
    hit: OpenSearchHit
    score: float = 0.0
    lexical_rank: int | None = None
    vector_rank: int | None = None


def _unique_ranked(hits: tuple[OpenSearchHit, ...]) -> tuple[OpenSearchHit, ...]:
    seen: set[str] = set()
    unique: list[OpenSearchHit] = []
    for hit in hits:
        chunk_id = hit.source.chunk_id
        if chunk_id not in seen:
            seen.add(chunk_id)
            unique.append(hit)
    return tuple(unique)


def reciprocal_rank_fusion(
    *,
    lexical_hits: tuple[OpenSearchHit, ...],
    vector_hits: tuple[OpenSearchHit, ...],
    limit: int,
    rank_constant: int = 60,
) -> tuple[RetrievalResult, ...]:
    """Fuse ranks, deduplicate by source chunk, and use chunk ID as stable tie-breaker."""
    if rank_constant < 1:
        raise ValueError("rank_constant must be positive")
    fused: dict[str, _FusedHit] = {}
    for source, hits in (
        ("lexical", _unique_ranked(lexical_hits)),
        ("vector", _unique_ranked(vector_hits)),
    ):
        for rank, hit in enumerate(hits, start=1):
            chunk_id = hit.source.chunk_id
            item = fused.setdefault(chunk_id, _FusedHit(hit=hit))
            item.score += 1.0 / (rank_constant + rank)
            if source == "lexical":
                item.lexical_rank = rank
            else:
                item.vector_rank = rank

    ordered = sorted(fused.values(), key=lambda item: (-item.score, item.hit.source.chunk_id))
    return tuple(_to_result(item) for item in ordered[:limit])


def _to_result(item: _FusedHit) -> RetrievalResult:
    source = item.hit.source
    return RetrievalResult(
        source_chunk_id=source.chunk_id,
        content=source.chunk_text,
        rrf_score=item.score,
        lexical_rank=item.lexical_rank,
        vector_rank=item.vector_rank,
        citation_id=source.citation_id,
        document_id=source.document_id,
        source_label=source.source_label,
        source_url=source.source_url,
        page=source.page,
        section=source.section,
        scheme_status=source.scheme_status,
        language=source.language,
        valid_from=source.valid_from,
        valid_until=source.valid_until,
    )

