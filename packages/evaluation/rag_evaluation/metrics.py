"""Pure ranking and citation metrics; no model is used as an evaluator."""

import math
from collections.abc import Mapping, Sequence

from rag_evaluation.models import (
    CaseResult,
    EvaluationCase,
    ManifestSource,
    ModeMetrics,
    RankedCitation,
    SearchMode,
    SourceKind,
)

_MODES: tuple[SearchMode, ...] = ("lexical", "vector", "hybrid")


def _canonical_url(value: object) -> str:
    return str(value).rstrip("/")


def _first_relevant_rank(ranking: Sequence[RankedCitation], expected: set[str]) -> int | None:
    return next(
        (rank for rank, item in enumerate(ranking, start=1) if item.document_id in expected),
        None,
    )


def _ndcg(ranking: Sequence[RankedCitation], expected: set[str], *, k: int) -> float:
    gains = [1.0 if item.document_id in expected else 0.0 for item in ranking[:k]]
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, start=1))
    ideal_count = min(len(expected), k)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
    return dcg / ideal if ideal else 0.0


def _metrics_for(
    cases: Sequence[EvaluationCase],
    rankings: Mapping[str, Mapping[SearchMode, Sequence[RankedCitation]]],
    manifest: Mapping[str, ManifestSource],
) -> dict[SearchMode, ModeMetrics]:
    output: dict[SearchMode, ModeMetrics] = {}
    expected_union = {item for case in cases for item in case.expected_document_ids}
    for mode in _MODES:
        ranks: list[int | None] = []
        ndcgs: list[float] = []
        resolved = 0
        complete = 0
        citation_count = 0
        covered: set[str] = set()
        for case in cases:
            ranking = tuple(rankings[case.case_id][mode])
            expected = set(case.expected_document_ids)
            rank = _first_relevant_rank(ranking, expected)
            ranks.append(rank)
            ndcgs.append(_ndcg(ranking, expected, k=10))
            covered.update(
                item.document_id for item in ranking[:10] if item.document_id in expected
            )
            for citation in ranking[:10]:
                citation_count += 1
                source = manifest.get(citation.document_id)
                if source is not None and _canonical_url(source.url) == _canonical_url(
                    citation.source_url
                ):
                    resolved += 1
                if (
                    citation.citation_id
                    and citation.source_label
                    and citation.page >= 1
                    and citation.section
                ):
                    complete += 1
        count = len(cases)
        output[mode] = ModeMetrics(
            case_count=count,
            hit_rate_at_5=sum(rank is not None and rank <= 5 for rank in ranks) / count,
            recall_at_10=sum(rank is not None and rank <= 10 for rank in ranks) / count,
            mean_reciprocal_rank=sum(1 / rank if rank else 0.0 for rank in ranks) / count,
            ndcg_at_10=sum(ndcgs) / count,
            expected_source_coverage=len(covered) / len(expected_union),
            citation_accuracy_at_5=sum(rank is not None and rank <= 5 for rank in ranks) / count,
            citation_resolvability=resolved / citation_count if citation_count else 0.0,
            citation_metadata_completeness=complete / citation_count if citation_count else 0.0,
        )
    return output


def evaluate_rankings(
    *,
    cases: Sequence[EvaluationCase],
    rankings: Mapping[str, Mapping[SearchMode, Sequence[RankedCitation]]],
    manifest: Mapping[str, ManifestSource],
) -> tuple[
    dict[SearchMode, ModeMetrics],
    dict[SourceKind, dict[SearchMode, ModeMetrics]],
    tuple[CaseResult, ...],
]:
    """Calculate aggregate and evidence-class metrics from unique-document rankings."""
    overall = _metrics_for(cases, rankings, manifest)
    kinds = {case.source_kind for case in cases}
    by_kind = {
        kind: _metrics_for(
            tuple(case for case in cases if case.source_kind == kind), rankings, manifest
        )
        for kind in kinds
    }
    case_results = tuple(
        CaseResult(
            case_id=case.case_id,
            source_kind=case.source_kind,
            expected_document_ids=case.expected_document_ids,
            ranks={
                mode: _first_relevant_rank(
                    rankings[case.case_id][mode], set(case.expected_document_ids)
                )
                for mode in _MODES
            },
        )
        for case in cases
    )
    return overall, by_kind, case_results
