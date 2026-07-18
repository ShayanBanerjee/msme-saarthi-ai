from typing import cast

from pydantic import HttpUrl, TypeAdapter

from rag_evaluation.metrics import evaluate_rankings
from rag_evaluation.models import EvaluationCase, ManifestSource, RankedCitation, SearchMode


def _citation(document_id: str, *, url: str | None = None) -> RankedCitation:
    return RankedCitation(
        document_id=document_id,
        citation_id=f"citation-{document_id}",
        source_url=TypeAdapter(HttpUrl).validate_python(
            url or f"https://example.gov.in/{document_id}"
        ),
        source_label=f"Source {document_id}",
        page=1,
        section="Synthetic section",
    )


def test_metrics_measure_rank_coverage_and_resolvable_citations() -> None:
    cases = (
        EvaluationCase(
            case_id="official-one",
            query="Find the synthetic official programme source",
            expected_document_ids=("official-a",),
            source_kind="official_scheme",
        ),
        EvaluationCase(
            case_id="guide-one",
            query="Find the synthetic business guidance source",
            expected_document_ids=("guide-a",),
            source_kind="business_guide",
        ),
    )
    manifests = TypeAdapter(tuple[ManifestSource, ...]).validate_python(
        [
            {
                "source_id": "official-a",
                "label": "Official A",
                "url": "https://example.gov.in/official-a",
                "source_kind": "official_scheme",
            },
            {
                "source_id": "guide-a",
                "label": "Guide A",
                "url": "https://example.gov.in/guide-a",
                "source_kind": "business_guide",
            },
        ]
    )
    rankings = cast(
        dict[str, dict[SearchMode, tuple[RankedCitation, ...]]],
        {
            "official-one": {
                "lexical": (_citation("official-a"),),
                "vector": (_citation("other"), _citation("official-a")),
                "hybrid": (_citation("official-a"),),
            },
            "guide-one": {
                "lexical": (_citation("other"),),
                "vector": (_citation("guide-a"),),
                "hybrid": (_citation("guide-a"),),
            },
        },
    )

    overall, by_kind, results = evaluate_rankings(
        cases=cases,
        rankings=rankings,
        manifest={item.source_id: item for item in manifests},
    )

    assert overall["lexical"].hit_rate_at_5 == 0.5
    assert overall["vector"].mean_reciprocal_rank == 0.75
    assert overall["hybrid"].expected_source_coverage == 1.0
    assert overall["hybrid"].citation_resolvability == 1.0
    assert by_kind["official_scheme"]["vector"].mean_reciprocal_rank == 0.5
    assert results[1].ranks["lexical"] is None


def test_unknown_or_mismatched_url_is_not_resolvable() -> None:
    case = EvaluationCase(
        case_id="official-one",
        query="Find the synthetic official programme source",
        expected_document_ids=("official-a",),
        source_kind="official_scheme",
    )
    source = ManifestSource(
        source_id="official-a",
        label="Official A",
        url=TypeAdapter(HttpUrl).validate_python("https://example.gov.in/official-a"),
        source_kind="official_scheme",
    )
    bad = _citation("official-a", url="https://spoof.invalid/official-a")
    rankings = cast(
        dict[str, dict[SearchMode, tuple[RankedCitation, ...]]],
        {case.case_id: {"lexical": (bad,), "vector": (bad,), "hybrid": (bad,)}},
    )

    overall, _, _ = evaluate_rankings(
        cases=(case,), rankings=rankings, manifest={source.source_id: source}
    )

    assert overall["hybrid"].citation_accuracy_at_5 == 1.0
    assert overall["hybrid"].citation_resolvability == 0.0
