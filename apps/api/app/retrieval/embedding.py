"""Provider-neutral embedding interface for vector retrieval."""

import hashlib
import re
from typing import Protocol


class EmbeddingProvider(Protocol):
    async def embed_query(self, query: str) -> tuple[float, ...]:
        """Return a finite, non-empty embedding for a validated query."""
        ...


class DeterministicHashEmbeddingProvider:
    """Stable development embedding matching the worker's 32-dimension index."""

    async def embed_query(self, query: str) -> tuple[float, ...]:
        values = [0.0] * 32
        for token in re.findall(r"[a-z0-9]+", query.casefold()):
            digest = hashlib.sha256(token.encode()).digest()
            values[int.from_bytes(digest[:2]) % 32] += 1.0 if digest[2] % 2 else -1.0
        magnitude = sum(value * value for value in values) ** 0.5 or 1.0
        return tuple(value / magnitude for value in values)
