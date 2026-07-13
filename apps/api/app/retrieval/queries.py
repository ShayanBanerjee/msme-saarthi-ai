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
    return clauses


def build_bm25_query(*, query: str, filters: RetrievalFilters, candidates: int) -> JsonObject:
    return {
        "size": candidates,
        "_source": SOURCE_FIELDS,
        "query": {
            "bool": {
                "must": [{"match": {"chunk_text": {"query": query, "operator": "or"}}}],
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

