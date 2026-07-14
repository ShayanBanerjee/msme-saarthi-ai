"""Filter validation and OpenSearch DSL construction tests."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.retrieval.models import LanguageCode, RetrievalFilters, SchemeStatus, SourceKind
from app.retrieval.queries import build_bm25_query, build_filter_clauses, build_vector_query


def test_all_supported_filters_are_applied_to_both_queries() -> None:
    filters = RetrievalFilters(
        state="exa",
        scheme_status=SchemeStatus.PUBLISHED,
        language=LanguageCode.ENGLISH,
        effective_on=date(2026, 7, 13),
        captured_after=date(2026, 4, 14),
        captured_before=date(2026, 7, 13),
        source_kind=SourceKind.OFFICIAL_SCHEME,
    )

    clauses = build_filter_clauses(filters)
    lexical = build_bm25_query(query="synthetic support", filters=filters, candidates=20)
    vector = build_vector_query(vector=(0.1, 0.2), filters=filters, candidates=20)

    assert filters.state == "EXA"
    assert {"term": {"state_codes.keyword": "EXA"}} in clauses
    assert {"term": {"scheme_status.keyword": "published"}} in clauses
    assert {"term": {"language.keyword": "en"}} in clauses
    assert {"term": {"source_kind.keyword": "official_scheme"}} in clauses
    assert {"range": {"valid_from": {"lte": "2026-07-13"}}} in clauses
    assert {
        "range": {"captured_at": {"gte": "2026-04-14", "lte": "2026-07-13"}}
    } in clauses
    assert lexical["query"] == {
        "bool": {
            "must": [
                {
                    "match": {
                        "chunk_text": {
                            "query": "synthetic support",
                            "operator": "or",
                            "minimum_should_match": "20%",
                        }
                    }
                }
            ],
            "should": [
                {
                    "match_phrase": {
                        "chunk_text": {"query": "synthetic support", "boost": 3}
                    }
                }
            ],
            "filter": clauses,
        }
    }
    assert vector["query"] == {
        "knn": {
            "embedding": {
                "vector": [0.1, 0.2],
                "k": 20,
                "filter": {"bool": {"filter": clauses}},
            }
        }
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("state", "invalid-state"),
        ("scheme_status", "invented"),
        ("language", "xx"),
        ("unknown", "value"),
        ("source_kind", "invented"),
        ("captured_after", "not-a-date"),
    ],
)
def test_invalid_filter_values_are_rejected(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        RetrievalFilters.model_validate({field: value})
