"""Synthetic OpenSearch retrieval fixtures."""

from collections.abc import Callable

from app.retrieval.client import JsonObject


def make_source(
    *,
    chunk_id: str,
    text: str,
    page: int = 1,
    section: str = "Synthetic section",
    captured_at: str | None = "2026-07-01T00:00:00Z",
) -> JsonObject:
    return {
        "chunk_id": chunk_id,
        "chunk_text": text,
        "citation_id": f"citation-{chunk_id}",
        "document_id": f"document-{chunk_id}",
        "source_label": "Synthetic retrieval fixture",
        "source_url": f"https://example.invalid/synthetic/{chunk_id}",
        "page": page,
        "section": section,
        "state_codes": ["EXA"],
        "scheme_status": "published",
        "language": "en",
        "valid_from": "2026-01-01",
        "valid_until": None,
        "captured_at": captured_at,
    }


def make_hit(*, chunk_id: str, text: str, score: float, page: int = 1) -> JsonObject:
    return {
        "_id": f"hit-{chunk_id}",
        "_score": score,
        "_source": make_source(chunk_id=chunk_id, text=text, page=page),
    }


def make_response(*hits: JsonObject) -> JsonObject:
    return {"hits": {"hits": list(hits)}}


type SourceFactory = Callable[..., JsonObject]
