"""Allowlisted source fetch, extraction, chunking and OpenSearch indexing."""

import hashlib
import ipaddress
import math
import re
import socket
from collections.abc import Iterable
from datetime import UTC, date, datetime
from enum import StrEnum
from html.parser import HTMLParser
from io import BytesIO
from itertools import pairwise
from typing import Literal, Protocol
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from pypdf import PdfReader
from pypdf.errors import PdfReadError


class SourceKind(StrEnum):
    OFFICIAL_SCHEME = "official_scheme"
    BUSINESS_GUIDE = "business_guide"


class SourceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(pattern=r"^[a-z0-9-]{3,80}$")
    label: str = Field(min_length=3, max_length=200)
    url: HttpUrl
    allowed_host: str = Field(min_length=4, max_length=253)
    valid_from: date
    language: str = Field(default="en", pattern=r"^[a-z]{2}$")
    state_codes: tuple[str, ...] = ()
    document_type: Literal["html", "pdf"] = "html"
    source_kind: SourceKind = SourceKind.OFFICIAL_SCHEME
    license_label: str | None = Field(default=None, min_length=3, max_length=100)


class FetchedSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    body: bytes
    content_type: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExtractedPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    page: int = Field(ge=1)
    section: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=2_000_000)


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
    captured_at: datetime
    embedding: tuple[float, ...]
    embedding_model: str
    content_checksum: str
    source_kind: SourceKind
    license_label: str | None = None


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


def extract_pdf_pages(
    payload: bytes, *, max_pages: int = 800, max_extracted_characters: int = 6_000_000
) -> tuple[ExtractedPage, ...]:
    """Extract text-bearing PDF pages without executing links, scripts, or attachments."""
    if not payload.startswith(b"%PDF"):
        raise ValueError("PDF source is missing the PDF signature")
    reader = PdfReader(BytesIO(payload), strict=False)
    if reader.is_encrypted:
        raise ValueError("encrypted PDFs are not supported")
    if not 1 <= len(reader.pages) <= max_pages:
        raise ValueError("PDF page count is outside the allowed range")
    pages: list[ExtractedPage] = []
    extracted_characters = 0
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = " ".join((page.extract_text() or "").split())
        except PdfReadError:
            continue
        if not text:
            continue
        extracted_characters += len(text)
        if extracted_characters > max_extracted_characters:
            raise ValueError("PDF extracted text exceeds the configured limit")
        pages.append(
            ExtractedPage(page=page_number, section=f"PDF page {page_number}", text=text)
        )
    if not pages:
        raise ValueError("PDF contains no extractable text; OCR is not enabled")
    return tuple(pages)


def extract_pages(source: SourceSpec, fetched: FetchedSource) -> tuple[ExtractedPage, ...]:
    if source.document_type == "pdf":
        if fetched.content_type not in {"application/pdf", "application/octet-stream"}:
            raise ValueError("PDF source returned an unsupported content type")
        return extract_pdf_pages(fetched.body)
    if fetched.content_type not in {"text/html", "application/xhtml+xml"}:
        raise ValueError("HTML source returned an unsupported content type")
    text = extract_text(fetched.body.decode("utf-8", errors="replace"))
    if not text:
        raise ValueError("HTML source contains no visible text")
    return (ExtractedPage(page=1, section="Web page", text=text),)


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


def deterministic_embedding(text: str, *, dimensions: int = 384) -> tuple[float, ...]:
    """Match the API's key-free feature embedding for reproducible local indexes."""
    if not 64 <= dimensions <= 3_072:
        raise ValueError("embedding dimensions must be between 64 and 3072")
    canonical_terms = {
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
    tokens = [
        canonical_terms.get(token, token)
        for token in re.findall(r"[a-z0-9]+", text.casefold())
    ]
    features: list[tuple[str, float]] = [(token, 1.0) for token in tokens]
    features.extend((f"{left}::{right}", 1.6) for left, right in pairwise(tokens))
    values = [0.0] * dimensions
    for feature, weight in features:
        digest = hashlib.sha256(feature.encode()).digest()
        values[int.from_bytes(digest[:4]) % dimensions] += weight
    magnitude = sum(value * value for value in values) ** 0.5 or 1.0
    return tuple(value / magnitude for value in values)


class DocumentEmbeddingProvider(Protocol):
    dimensions: int
    model_id: str

    async def embed_documents(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        ...


class LocalFeatureEmbeddingProvider:
    model_id = "local-feature-hash-v2"

    def __init__(self, *, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    async def embed_documents(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        return tuple(deterministic_embedding(text, dimensions=self.dimensions) for text in texts)


class OpenAIDocumentEmbeddingProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimensions: int,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 60.0,
        batch_size: int = 64,
    ) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self._api_key = api_key
        self.model_id = model
        self.dimensions = dimensions
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._batch_size = batch_size

    async def embed_documents(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        vectors: list[tuple[float, ...]] = []
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            for start in range(0, len(texts), self._batch_size):
                batch = texts[start : start + self._batch_size]
                response = await client.post(
                    f"{self._base_url}/embeddings",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "input": list(batch),
                        "model": self.model_id,
                        "dimensions": self.dimensions,
                        "encoding_format": "float",
                    },
                )
                response.raise_for_status()
                payload = response.json()
                data = payload.get("data") if isinstance(payload, dict) else None
                if not isinstance(data, list) or len(data) != len(batch):
                    raise ValueError("OpenAI embedding response count does not match input")
                ordered = sorted(data, key=lambda item: item.get("index", -1))
                for item in ordered:
                    raw = item.get("embedding") if isinstance(item, dict) else None
                    if not isinstance(raw, list) or len(raw) != self.dimensions:
                        raise ValueError("OpenAI embedding response has an invalid dimension")
                    vector = tuple(float(value) for value in raw)
                    if any(not math.isfinite(value) for value in vector):
                        raise ValueError("OpenAI embedding response contains non-finite values")
                    vectors.append(vector)
        return tuple(vectors)


def _is_public_host(host: str) -> bool:
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise ValueError("source host could not be resolved") from error
    return all(not ipaddress.ip_address(item[4][0]).is_private for item in addresses)


class HttpSourceFetcher:
    def __init__(self, *, max_bytes: int = 140_000_000, timeout_seconds: float = 30.0) -> None:
        self._max_bytes = max_bytes
        self._timeout = timeout_seconds

    async def fetch(self, source: SourceSpec) -> FetchedSource:
        parsed = urlparse(str(source.url))
        if parsed.scheme != "https" or parsed.hostname != source.allowed_host:
            raise ValueError("source URL must use HTTPS and the allowlisted host")
        if not _is_public_host(source.allowed_host):
            raise ValueError("source host must resolve only to public addresses")
        async with (
            httpx.AsyncClient(follow_redirects=True, timeout=self._timeout) as client,
            client.stream(
                "GET",
                str(source.url),
                headers={"User-Agent": "MSME-Saarthi-Source-Monitor/0.1"},
            ) as response,
        ):
            response.raise_for_status()
            final = urlparse(str(response.url))
            if final.scheme != "https" or final.hostname != source.allowed_host:
                raise ValueError("source redirect left the allowlisted host")
            declared_length = response.headers.get("content-length")
            if declared_length is not None and int(declared_length) > self._max_bytes:
                raise ValueError("source exceeds the configured size limit")
            body = bytearray()
            async for part in response.aiter_bytes():
                body.extend(part)
                if len(body) > self._max_bytes:
                    raise ValueError("source exceeds the configured size limit")
            content_type = (
                response.headers.get("content-type", "")
                .split(";", maxsplit=1)[0]
                .lower()
            )
        return FetchedSource(body=bytes(body), content_type=content_type)


class OpenSearchChunkSink:
    def __init__(
        self, *, base_url: str, index: str = "msme-schemes-v2", embedding_dimensions: int = 384
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._index = index
        self._embedding_dimensions = embedding_dimensions

    async def index(self, chunks: Iterable[IndexedChunk]) -> int:
        count = 0
        async with httpx.AsyncClient(timeout=20.0) as client:
            await client.put(
                f"{self._base_url}/{self._index}",
                json={
                    "settings": {"index.knn": True},
                    "mappings": {
                        "properties": {
                            "embedding": {
                                "type": "knn_vector",
                                "dimension": self._embedding_dimensions,
                            },
                            "embedding_model": {"type": "keyword"},
                            "chunk_text": {"type": "text"},
                            "source_kind": {
                                "type": "text",
                                "fields": {"keyword": {"type": "keyword"}},
                            },
                            "license_label": {"type": "keyword"},
                            "captured_at": {"type": "date"},
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
    source: SourceSpec,
    *,
    fetcher: HttpSourceFetcher,
    sink: OpenSearchChunkSink,
    embedder: DocumentEmbeddingProvider | None = None,
) -> int:
    """Fetch one allowlisted source and index derived untrusted text as evidence only."""
    fetched = await fetcher.fetch(source)
    pages = extract_pages(source, fetched)
    checksum = hashlib.sha256(fetched.body).hexdigest()
    resolved_embedder = embedder or LocalFeatureEmbeddingProvider()
    pending: list[tuple[int, ExtractedPage, str]] = []
    index = 0
    for page in pages:
        for content in chunk_text(page.text):
            index += 1
            pending.append((index, page, content))
    embeddings = await resolved_embedder.embed_documents(
        tuple(content for _, _, content in pending)
    )
    if len(embeddings) != len(pending):
        raise ValueError("embedding count does not match chunk count")
    chunks: list[IndexedChunk] = []
    for (index, page, content), embedding in zip(pending, embeddings, strict=True):
        chunks.append(
            IndexedChunk(
                chunk_id=f"{source.source_id}-{index:04d}",
                chunk_text=content,
                citation_id=f"{source.source_id}-{index:04d}",
                document_id=source.source_id,
                source_label=source.label,
                source_url=source.url,
                page=page.page,
                section=page.section,
                state_codes=source.state_codes,
                language=source.language,
                valid_from=source.valid_from,
                captured_at=fetched.captured_at,
                embedding=embedding,
                embedding_model=resolved_embedder.model_id,
                content_checksum=checksum,
                source_kind=source.source_kind,
                license_label=source.license_label,
            )
        )
    return await sink.index(chunks)
