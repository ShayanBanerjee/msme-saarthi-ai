"""Provider-neutral embedding interface for vector retrieval."""

from typing import Protocol


class EmbeddingProvider(Protocol):
    async def embed_query(self, query: str) -> tuple[float, ...]:
        """Return a finite, non-empty embedding for a validated query."""
        ...

