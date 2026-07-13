"""OpenSearch REST integration test using the documented synthetic HTTP fixture."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.retrieval.client import HttpOpenSearchClient
from app.retrieval.models import RetrievalFilters, RetrievalQuery
from app.retrieval.opensearch import OpenSearchHybridRetriever

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "responses.json"


class FixtureEmbedder:
    async def embed_query(self, query: str) -> tuple[float, ...]:
        assert query == "synthetic hybrid fixture"
        return (0.25, 0.5, 0.75)


@pytest.mark.integration
def test_http_fixture_executes_bm25_vector_filters_and_preserves_citations() -> None:
    async def scenario() -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        captured_bodies: list[dict[str, object]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.url.path == "/synthetic-schemes-v1/_search"
            body = json.loads(request.content)
            assert isinstance(body, dict)
            captured_bodies.append(body)
            response_key = "vector" if "knn" in str(body) else "lexical"
            return httpx.Response(200, json=fixture[response_key])

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = HttpOpenSearchClient(
                client=http_client,
                base_url="https://opensearch.example.invalid",
            )
            retriever = OpenSearchHybridRetriever(
                client=client,
                embedder=FixtureEmbedder(),
                index="synthetic-schemes-v1",
            )
            results = await retriever.search(
                RetrievalQuery(
                    query="synthetic hybrid fixture",
                    filters=RetrievalFilters(
                        state="EXA",
                        scheme_status="published",
                        language="en",
                        effective_on="2026-07-13",
                    ),
                )
            )

        assert {result.source_chunk_id for result in results} == {
            "fixture-lexical",
            "fixture-vector",
        }
        assert {result.page for result in results} == {4, 7}
        assert {result.section for result in results} == {"Lexical fixture", "Vector fixture"}
        assert all(result.citation_id.startswith("fixture-citation-") for result in results)
        assert any("match" in str(body) for body in captured_bodies)
        assert any("knn" in str(body) for body in captured_bodies)
        assert all("state_codes.keyword" in str(body) for body in captured_bodies)
        assert all("2026-07-13" in str(body) for body in captured_bodies)

    asyncio.run(scenario())

