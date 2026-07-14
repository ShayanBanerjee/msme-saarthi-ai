"""Provider-neutral query embeddings with a production adapter and offline fallback."""

import hashlib
import math
import re
from itertools import pairwise
from typing import Protocol

import httpx

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_CANONICAL_TERMS = {
    "funding": "finance",
    "fund": "finance",
    "loans": "loan",
    "credits": "credit",
    "customers": "customer",
    "selling": "sales",
    "marketing": "market",
    "manufacturer": "manufacturing",
    "manufacturers": "manufacturing",
    "factories": "factory",
    "enterprises": "enterprise",
    "businesses": "business",
}


class EmbeddingProvider(Protocol):
    async def embed_query(self, query: str) -> tuple[float, ...]:
        """Return a finite, non-empty embedding for a validated query."""
        ...


def feature_hash_embedding(text: str, *, dimensions: int = 384) -> tuple[float, ...]:
    """Create a deterministic local lexical-feature vector for offline development."""
    if not 64 <= dimensions <= 3_072:
        raise ValueError("embedding dimensions must be between 64 and 3072")
    tokens = [
        _CANONICAL_TERMS.get(token, token)
        for token in _TOKEN_PATTERN.findall(text.casefold())
    ]
    features: list[tuple[str, float]] = [(token, 1.0) for token in tokens]
    features.extend((f"{left}::{right}", 1.6) for left, right in pairwise(tokens))
    values = [0.0] * dimensions
    for feature, weight in features:
        digest = hashlib.sha256(feature.encode()).digest()
        values[int.from_bytes(digest[:4]) % dimensions] += weight
    magnitude = math.sqrt(sum(value * value for value in values)) or 1.0
    return tuple(value / magnitude for value in values)


class LocalFeatureEmbeddingProvider:
    """Key-free fallback; useful locally but not represented as semantic understanding."""

    def __init__(self, *, dimensions: int = 384) -> None:
        self._dimensions = dimensions

    async def embed_query(self, query: str) -> tuple[float, ...]:
        return feature_hash_embedding(query, dimensions=self._dimensions)


class OpenAIEmbeddingProvider:
    """OpenAI embeddings adapter; provider response types remain at this boundary."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimensions: int,
        base_url: str,
        timeout_seconds: float,
    ) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def embed_query(self, query: str) -> tuple[float, ...]:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "input": query,
                    "model": self._model,
                    "dimensions": self._dimensions,
                    "encoding_format": "float",
                },
            )
            response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        first = data[0] if isinstance(data, list) and data else None
        raw = first.get("embedding") if isinstance(first, dict) else None
        if not isinstance(raw, list) or len(raw) != self._dimensions:
            raise ValueError("OpenAI embedding response has an invalid dimension")
        vector = tuple(float(value) for value in raw)
        if any(not math.isfinite(value) for value in vector):
            raise ValueError("OpenAI embedding response contains non-finite values")
        return vector


# Backwards-compatible name for callers that still import the old development adapter.
DeterministicHashEmbeddingProvider = LocalFeatureEmbeddingProvider
