"""OpenSearch BM25/vector orchestration behind the chat Retriever protocol."""

import asyncio
import math
import re
from collections.abc import Callable
from datetime import date

from app.agents.chat.state import Citation, RetrievedEvidence
from app.retrieval.client import HttpOpenSearchClient, OpenSearchClient
from app.retrieval.embedding import EmbeddingProvider
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import (
    OpenSearchResponse,
    RetrievalFilters,
    RetrievalQuery,
    RetrievalResult,
    SourceKind,
)
from app.retrieval.queries import build_bm25_query, build_vector_query

_INDEX_PATTERN = r"^[a-z0-9][a-z0-9._-]{0,127}$"


class OpenSearchHybridRetriever:
    """Run filtered lexical/vector searches concurrently and fuse their ranks."""

    def __init__(
        self,
        *,
        client: OpenSearchClient,
        embedder: EmbeddingProvider,
        index: str,
        candidate_count: int = 50,
        clock: Callable[[], date] = date.today,
    ) -> None:
        self._client = client
        self._embedder = embedder
        self._index = index
        if re.fullmatch(_INDEX_PATTERN, self._index) is None:
            raise ValueError("index contains unsupported characters")
        if not 1 <= candidate_count <= 1_000:
            raise ValueError("candidate_count must be between 1 and 1000")
        self._candidate_count = candidate_count
        self._clock = clock

    async def search(self, request: RetrievalQuery) -> tuple[RetrievalResult, ...]:
        vector = await self._embedder.embed_query(request.query)
        if not vector or any(not math.isfinite(value) for value in vector):
            raise ValueError("embedding must contain finite values")
        lexical_body = build_bm25_query(
            query=request.query,
            filters=request.filters,
            candidates=self._candidate_count,
        )
        vector_body = build_vector_query(
            vector=vector,
            filters=request.filters,
            candidates=self._candidate_count,
        )
        lexical_raw, vector_raw = await asyncio.gather(
            self._client.search(index=self._index, body=lexical_body),
            self._client.search(index=self._index, body=vector_body),
        )
        lexical = OpenSearchResponse.model_validate(lexical_raw)
        semantic = OpenSearchResponse.model_validate(vector_raw)
        return reciprocal_rank_fusion(
            lexical_hits=lexical.hits.hits,
            vector_hits=semantic.hits.hits,
            limit=request.limit,
        )

    async def retrieve(self, query: str) -> tuple[RetrievedEvidence, ...]:
        """Return a deliberate balance of official paths and general business guidance."""
        official, guides = await asyncio.gather(
            self.search(
                RetrievalQuery(
                    query=query,
                    filters=RetrievalFilters(
                        effective_on=self._clock(), source_kind=SourceKind.OFFICIAL_SCHEME
                    ),
                    limit=3,
                )
            ),
            self.search(
                RetrievalQuery(
                    query=query,
                    filters=RetrievalFilters(
                        effective_on=self._clock(), source_kind=SourceKind.BUSINESS_GUIDE
                    ),
                    limit=2,
                )
            ),
        )
        results = tuple(
            {item.source_chunk_id: item for item in (*official, *guides)}.values()
        )
        return tuple(
            RetrievedEvidence(
                content=result.content,
                citation=Citation(
                    citation_id=result.citation_id,
                    document_id=result.document_id,
                    source_label=result.source_label,
                    source_url=result.source_url,
                    page=result.page,
                    section=result.section,
                    excerpt=result.content[:500],
                    source_kind=result.source_kind.value,
                    license_label=result.license_label,
                ),
            )
            for result in results
        )


__all__ = ["HttpOpenSearchClient", "OpenSearchHybridRetriever"]
