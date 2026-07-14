"""Embedding boundary tests use synthetic text and no provider network calls."""

import asyncio
import math

from app.retrieval.embedding import LocalFeatureEmbeddingProvider


def test_local_feature_embedding_is_deterministic_and_normalized() -> None:
    async def scenario() -> None:
        provider = LocalFeatureEmbeddingProvider(dimensions=384)
        first = await provider.embed_query("synthetic working capital finance")
        second = await provider.embed_query("synthetic working capital funding")

        assert len(first) == 384
        assert first == await provider.embed_query("synthetic working capital finance")
        assert math.isclose(sum(value * value for value in first), 1.0)
        assert sum(left * right for left, right in zip(first, second, strict=True)) > 0.5

    asyncio.run(scenario())
