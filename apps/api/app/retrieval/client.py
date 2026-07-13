"""Narrow asynchronous OpenSearch REST client boundary."""

from typing import Protocol

import httpx
from pydantic import HttpUrl, TypeAdapter

type JsonObject = dict[str, object]


class OpenSearchClient(Protocol):
    async def search(self, *, index: str, body: JsonObject) -> JsonObject:
        """Execute an application-constructed search body."""
        ...


class HttpOpenSearchClient:
    """HTTP adapter using an injected client for credentials, TLS, and lifecycle."""

    def __init__(self, *, client: httpx.AsyncClient, base_url: str) -> None:
        self._client = client
        self._base_url = str(TypeAdapter(HttpUrl).validate_python(base_url)).rstrip("/")

    async def search(self, *, index: str, body: JsonObject) -> JsonObject:
        response = await self._client.post(f"{self._base_url}/{index}/_search", json=body)
        response.raise_for_status()
        parsed = response.json()
        if not isinstance(parsed, dict):
            raise ValueError("OpenSearch response must be a JSON object")
        return parsed

