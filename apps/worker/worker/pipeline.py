"""Allowlisted source fetch, extraction, chunking and OpenSearch indexing."""

import hashlib
import ipaddress
import re
import socket
from collections.abc import Iterable
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(pattern=r"^[a-z0-9-]{3,80}$")
    label: str = Field(min_length=3, max_length=200)
    url: HttpUrl
    allowed_host: str = Field(min_length=4, max_length=253)
    valid_from: date
    language: str = Field(default="en", pattern=r"^[a-z]{2}$")
    state_codes: tuple[str, ...] = ()


class IndexedChunk(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: str
    chunk_text: str
    citation_id: str
    document_id: str
    source_label: str
    source_url: HttpUrl
    page: int = 1
    section: str = "Web page"
    state_codes: tuple[str, ...]
    scheme_status: str = "published"
    language: str
    valid_from: date
    valid_until: date | None = None
    embedding: tuple[float, ...]
    content_checksum: str


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"script", "style", "noscript"}:
            self._ignored += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored:
            self._ignored -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored:
            self.parts.append(data)


def extract_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return " ".join(" ".join(parser.parts).split())


def chunk_text(text: str, *, words_per_chunk: int = 220, overlap: int = 30) -> tuple[str, ...]:
    if not 20 <= words_per_chunk <= 1_000 or not 0 <= overlap < words_per_chunk:
        raise ValueError("invalid chunk parameters")
    words = text.split()
    step = words_per_chunk - overlap
    return tuple(
        " ".join(words[start : start + words_per_chunk])
        for start in range(0, len(words), step)
        if words[start : start + words_per_chunk]
    )


def deterministic_embedding(text: str, *, dimensions: int = 32) -> tuple[float, ...]:
    values = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9]+", text.casefold()):
        digest = hashlib.sha256(token.encode()).digest()
        values[int.from_bytes(digest[:2]) % dimensions] += 1.0 if digest[2] % 2 else -1.0
    magnitude = sum(value * value for value in values) ** 0.5 or 1.0
    return tuple(value / magnitude for value in values)


def _is_public_host(host: str) -> bool:
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise ValueError("source host could not be resolved") from error
    return all(not ipaddress.ip_address(item[4][0]).is_private for item in addresses)


class HttpSourceFetcher:
    def __init__(self, *, max_bytes: int = 5_000_000, timeout_seconds: float = 20.0) -> None:
        self._max_bytes = max_bytes
        self._timeout = timeout_seconds

    async def fetch(self, source: SourceSpec) -> str:
        parsed = urlparse(str(source.url))
        if parsed.scheme != "https" or parsed.hostname != source.allowed_host:
            raise ValueError("source URL must use HTTPS and the allowlisted host")
        if not _is_public_host(source.allowed_host):
            raise ValueError("source host must resolve only to public addresses")
        async with httpx.AsyncClient(follow_redirects=True, timeout=self._timeout) as client:
            response = await client.get(
                str(source.url), headers={"User-Agent": "MSME-Saarthi-Source-Monitor/0.1"}
            )
            response.raise_for_status()
        final = urlparse(str(response.url))
        if final.scheme != "https" or final.hostname != source.allowed_host:
            raise ValueError("source redirect left the allowlisted host")
        if len(response.content) > self._max_bytes:
            raise ValueError("source exceeds the configured size limit")
        return response.text


class OpenSearchChunkSink:
    def __init__(self, *, base_url: str, index: str = "msme-schemes-v1") -> None:
        self._base_url = base_url.rstrip("/")
        self._index = index

    async def index(self, chunks: Iterable[IndexedChunk]) -> int:
        count = 0
        async with httpx.AsyncClient(timeout=20.0) as client:
            await client.put(
                f"{self._base_url}/{self._index}",
                json={
                    "settings": {"index.knn": True},
                    "mappings": {
                        "properties": {
                            "embedding": {"type": "knn_vector", "dimension": 32},
                            "chunk_text": {"type": "text"},
                        }
                    },
                },
            )
            for chunk in chunks:
                response = await client.put(
                    f"{self._base_url}/{self._index}/_doc/{chunk.chunk_id}",
                    json=chunk.model_dump(mode="json"),
                )
                response.raise_for_status()
                count += 1
        return count


async def ingest_source(
    source: SourceSpec, *, fetcher: HttpSourceFetcher, sink: OpenSearchChunkSink
) -> int:
    """Fetch one allowlisted source and index derived untrusted text as evidence only."""
    html = await fetcher.fetch(source)
    text = extract_text(html)
    checksum = hashlib.sha256(html.encode()).hexdigest()
    chunks = tuple(
        IndexedChunk(
            chunk_id=f"{source.source_id}-{index:04d}",
            chunk_text=content,
            citation_id=f"{source.source_id}-{index:04d}",
            document_id=source.source_id,
            source_label=source.label,
            source_url=source.url,
            state_codes=source.state_codes,
            language=source.language,
            valid_from=source.valid_from,
            embedding=deterministic_embedding(content),
            content_checksum=checksum,
        )
        for index, content in enumerate(chunk_text(text), start=1)
    )
    return await sink.index(chunks)
