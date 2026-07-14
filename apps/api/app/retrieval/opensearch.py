"""OpenSearch BM25/vector orchestration behind the chat Retriever protocol."""

import asyncio
import math
import re
from collections.abc import Callable
from datetime import date, timedelta
from itertools import pairwise

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
_STOP_WORDS = {
    "and",
    "are",
    "business",
    "for",
    "from",
    "have",
    "help",
    "into",
    "need",
    "next",
    "small",
    "that",
    "the",
    "this",
    "what",
    "with",
}


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
        official_max_age_days: int = 90,
        guide_max_age_days: int = 3_650,
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
        if not 1 <= official_max_age_days <= 3_650:
            raise ValueError("official_max_age_days must be between 1 and 3650")
        if not 1 <= guide_max_age_days <= 7_300:
            raise ValueError("guide_max_age_days must be between 1 and 7300")
        self._official_max_age_days = official_max_age_days
        self._guide_max_age_days = guide_max_age_days

    def _is_fresh(self, result: RetrievalResult) -> bool:
        """Fail closed when capture/effective metadata cannot prove currentness."""
        today = self._clock()
        if result.scheme_status.value != "published" or result.valid_from > today:
            return False
        if result.valid_until is not None and result.valid_until < today:
            return False
        if result.captured_at is None:
            return False
        captured_on = result.captured_at.date()
        max_age = (
            self._official_max_age_days
            if result.source_kind == SourceKind.OFFICIAL_SCHEME
            else self._guide_max_age_days
        )
        age_days = (today - captured_on).days
        return 0 <= age_days <= max_age

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

    @staticmethod
    def _diversify(
        results: tuple[RetrievalResult, ...], *, limit: int, per_document: int
    ) -> tuple[RetrievalResult, ...]:
        counts: dict[str, int] = {}
        selected: list[RetrievalResult] = []
        for result in results:
            count = counts.get(result.document_id, 0)
            if count >= per_document:
                continue
            selected.append(result)
            counts[result.document_id] = count + 1
            if len(selected) == limit:
                break
        return tuple(selected)

    @staticmethod
    def _relevance_score(query: str, content: str) -> float:
        def tokens(value: str) -> tuple[str, ...]:
            return tuple(
                token
                for token in re.findall(r"[a-z]+", value.casefold())
                if len(token) > 2 and token not in _STOP_WORDS
            )

        query_tokens = tokens(query)
        content_tokens = tokens(content)
        content_set = set(content_tokens)
        term_score = sum(1.0 for token in set(query_tokens) if token in content_set)
        content_bigrams = set(pairwise(content_tokens))
        phrase_score = sum(
            3.0 for phrase in set(pairwise(query_tokens)) if phrase in content_bigrams
        )
        return term_score + phrase_score

    @classmethod
    def _select_relevant(
        cls,
        query: str,
        results: tuple[RetrievalResult, ...],
        *,
        limit: int,
    ) -> tuple[RetrievalResult, ...]:
        ranked = sorted(
            results,
            key=lambda result: (-cls._relevance_score(query, result.content), -result.rrf_score),
        )
        supported = tuple(
            result for result in ranked if cls._relevance_score(query, result.content) >= 2
        )
        return cls._diversify(supported, limit=limit, per_document=1)

    async def retrieve(self, query: str) -> tuple[RetrievedEvidence, ...]:
        """Return a deliberate balance of official paths and general business guidance."""
        today = self._clock()
        official, guides = await asyncio.gather(
            self.search(
                RetrievalQuery(
                    query=query,
                    filters=RetrievalFilters(
                        effective_on=today,
                        captured_after=today - timedelta(days=self._official_max_age_days),
                        captured_before=today,
                        source_kind=SourceKind.OFFICIAL_SCHEME,
                    ),
                    limit=12,
                )
            ),
            self.search(
                RetrievalQuery(
                    query=query,
                    filters=RetrievalFilters(
                        effective_on=today,
                        captured_after=today - timedelta(days=self._guide_max_age_days),
                        captured_before=today,
                        source_kind=SourceKind.BUSINESS_GUIDE,
                    ),
                    limit=8,
                )
            ),
        )
        official = self._select_relevant(
            query, tuple(item for item in official if self._is_fresh(item)), limit=3
        )
        guides = self._select_relevant(
            query, tuple(item for item in guides if self._is_fresh(item)), limit=1
        )
        results = tuple({item.source_chunk_id: item for item in (*official, *guides)}.values())
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
