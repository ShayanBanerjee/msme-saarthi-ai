"""Application-owned OpenSearch query builders; callers cannot submit raw DSL."""

from app.retrieval.client import JsonObject
from app.retrieval.models import RetrievalFilters

SOURCE_FIELDS = [
    "chunk_id",
    "chunk_text",
    "citation_id",
    "document_id",
    "source_label",
    "source_url",
    "page",
    "section",
    "state_codes",
    "scheme_status",
    "language",
    "valid_from",
    "valid_until",
    "captured_at",
    "source_kind",
    "license_label",
]


def build_filter_clauses(filters: RetrievalFilters) -> list[JsonObject]:
    """Build exact/range filters from validated fields only."""
    clauses: list[JsonObject] = [
        {"term": {"scheme_status.keyword": filters.scheme_status.value}},
    ]
    if filters.state is not None:
        clauses.append({"term": {"state_codes.keyword": filters.state}})
    if filters.language is not None:
        clauses.append({"term": {"language.keyword": filters.language.value}})
    if filters.source_kind is not None:
        clauses.append({"term": {"source_kind.keyword": filters.source_kind.value}})
    if filters.effective_on is not None:
        effective_on = filters.effective_on.isoformat()
        clauses.extend(
            [
                {"range": {"valid_from": {"lte": effective_on}}},
                {
                    "bool": {
                        "should": [
                            {"range": {"valid_until": {"gte": effective_on}}},
                            {"bool": {"must_not": {"exists": {"field": "valid_until"}}}},
                        ],
                        "minimum_should_match": 1,
                    }
                },
            ]
        )
    if filters.captured_after is not None or filters.captured_before is not None:
        capture_range: JsonObject = {}
        if filters.captured_after is not None:
            capture_range["gte"] = filters.captured_after.isoformat()
        if filters.captured_before is not None:
            capture_range["lte"] = filters.captured_before.isoformat()
        clauses.append({"range": {"captured_at": capture_range}})
    return clauses


def build_bm25_query(*, query: str, filters: RetrievalFilters, candidates: int) -> JsonObject:
    return {
        "size": candidates,
        "_source": SOURCE_FIELDS,
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "chunk_text": {
                                "query": query,
                                "operator": "or",
                                "minimum_should_match": "20%",
                            }
                        }
                    }
                ],
                "should": [{"match_phrase": {"chunk_text": {"query": query, "boost": 3}}}],
                "filter": build_filter_clauses(filters),
            }
        },
    }


def build_vector_query(
    *, vector: tuple[float, ...], filters: RetrievalFilters, candidates: int
) -> JsonObject:
    return {
        "size": candidates,
        "_source": SOURCE_FIELDS,
        "query": {
            "knn": {
                "embedding": {
                    "vector": list(vector),
                    "k": candidates,
                    "filter": {"bool": {"filter": build_filter_clauses(filters)}},
                }
            }
        },
    }
