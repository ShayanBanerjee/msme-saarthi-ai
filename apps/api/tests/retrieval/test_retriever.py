"""Hybrid retrieval orchestration tests with typed in-process adapters."""

import asyncio
from datetime import date

from app.agents.chat.retrieval import Retriever
from app.retrieval.client import JsonObject
from app.retrieval.models import RetrievalFilters, RetrievalQuery
from app.retrieval.opensearch import OpenSearchHybridRetriever

from .conftest import make_hit, make_response


class RecordingClient:
    def __init__(self) -> None:
        self.bodies: list[JsonObject] = []

    async def search(self, *, index: str, body: JsonObject) -> JsonObject:
        assert index == "synthetic-schemes-v1"
        self.bodies.append(body)
        if "match" in str(body):
            return make_response(
                make_hit(
                    chunk_id="lexical-only",
                    text="Exact synthetic terminology appears here.",
                    score=10.0,
                    page=2,
                ),
                make_hit(chunk_id="shared", text="Shared synthetic content.", score=8.0),
            )
        return make_response(
            make_hit(
                chunk_id="semantic-only",
                text="Related synthetic meaning appears here.",
                score=0.95,
                page=3,
            ),
            make_hit(chunk_id="shared", text="Shared synthetic content.", score=0.9),
        )


class RecordingEmbedder:
    def __init__(self) -> None:
        self.queries: list[str] = []

    async def embed_query(self, query: str) -> tuple[float, ...]:
        self.queries.append(query)
        return (0.1, 0.2, 0.3)


def test_hybrid_search_finds_lexical_and_semantic_results_with_metadata() -> None:
    async def scenario() -> None:
        client = RecordingClient()
        embedder = RecordingEmbedder()
        retriever = OpenSearchHybridRetriever(
            client=client,
            embedder=embedder,
            index="synthetic-schemes-v1",
            candidate_count=20,
        )

        results = await retriever.search(
            RetrievalQuery(
                query="synthetic terminology",
                filters=RetrievalFilters(state="EXA", language="en"),
            )
        )

        by_id = {result.source_chunk_id: result for result in results}
        assert by_id["lexical-only"].lexical_rank == 1
        assert by_id["lexical-only"].vector_rank is None
        assert by_id["semantic-only"].vector_rank == 1
        assert by_id["semantic-only"].lexical_rank is None
        assert by_id["semantic-only"].page == 3
        assert by_id["semantic-only"].section == "Synthetic section"
        assert str(by_id["semantic-only"].source_url).startswith("https://example.invalid/")
        assert len(by_id) == 3
        assert embedder.queries == ["synthetic terminology"]
        assert len(client.bodies) == 2

    asyncio.run(scenario())


def test_existing_retriever_interface_returns_citation_evidence() -> None:
    async def scenario() -> None:
        retriever = OpenSearchHybridRetriever(
            client=RecordingClient(),
            embedder=RecordingEmbedder(),
            index="synthetic-schemes-v1",
            clock=lambda: date(2026, 7, 13),
        )
        compatible_retriever: Retriever = retriever

        evidence = await compatible_retriever.retrieve("synthetic terminology")

        assert evidence
        assert evidence[0].citation.document_id
        assert evidence[0].citation.page >= 1
        assert evidence[0].citation.section == "Synthetic section"
        assert evidence[0].citation.source_url.host == "example.invalid"

    asyncio.run(scenario())


def test_retrieve_fails_closed_for_stale_or_missing_capture_metadata() -> None:
    class StaleClient:
        async def search(self, *, index: str, body: JsonObject) -> JsonObject:
            del index, body
            stale = make_hit(
                chunk_id="stale",
                text="Synthetic terminology with stale evidence metadata.",
                score=1,
            )
            stale["_source"]["captured_at"] = "2025-01-01T00:00:00Z"  # type: ignore[index]
            return make_response(stale)

    async def scenario() -> None:
        retriever = OpenSearchHybridRetriever(
            client=StaleClient(),
            embedder=RecordingEmbedder(),
            index="synthetic-schemes-v1",
            clock=lambda: date(2026, 7, 13),
            official_max_age_days=90,
        )

        assert await retriever.retrieve("synthetic terminology") == ()

    asyncio.run(scenario())
