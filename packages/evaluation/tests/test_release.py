from datetime import date
from pathlib import Path
from typing import Literal, cast

from rag_evaluation.models import EvaluationDataset, EvaluationReport
from rag_evaluation.release import ReleaseThresholds, validate_release


def _dataset(split: Literal["tuning", "held_out"]) -> EvaluationDataset:
    return EvaluationDataset.model_validate(
        {
            "schema_version": "1",
            "dataset_version": "1.0.0",
            "description": "Synthetic candidate judgments for release gate testing only.",
            "corpus_manifest_sha256": "a" * 64,
            "split": split,
            "judgment_status": "candidate",
            "require_full_manifest_coverage": False,
            "cases": [
                {
                    "case_id": f"{split.replace('_', '-')}-case",
                    "query": "Find the synthetic reviewed source for this test",
                    "expected_document_ids": ["synthetic-source"],
                    "source_kind": "official_scheme",
                }
            ],
        }
    )


def test_release_rejects_candidate_judgments_before_alias_work() -> None:
    thresholds = ReleaseThresholds.model_validate(
        {
            "schema_version": "1",
            "alias": "synthetic-read",
            "required_document_count": 1,
            "fusion_rank_constant": 60,
            "fusion_lexical_weight": 0.8,
            "fusion_vector_weight": 1.0,
            "fusion_max_chunks_per_document": 1,
            "minimum_tuning_hybrid_hit_rate_at_5": 0.9,
            "minimum_heldout_hybrid_hit_rate_at_5": 0.9,
            "minimum_heldout_official_hit_rate_at_5": 0.9,
            "minimum_heldout_guide_hit_rate_at_5": 0.9,
            "minimum_heldout_hybrid_mrr": 0.7,
            "minimum_heldout_hybrid_ndcg_at_10": 0.7,
            "required_citation_resolvability": 1.0,
            "required_citation_metadata_completeness": 1.0,
        }
    )
    unavailable_report = cast(EvaluationReport, object())

    try:
        validate_release(
            tuning_dataset=_dataset("tuning"),
            tuning_dataset_sha256="b" * 64,
            heldout_dataset=_dataset("held_out"),
            heldout_dataset_sha256="c" * 64,
            tuning_report=unavailable_report,
            heldout_report=unavailable_report,
            thresholds=thresholds,
        )
    except ValueError as error:
        assert "human-approved" in str(error)
    else:
        raise AssertionError("candidate judgments must block alias promotion")


def test_current_candidate_metrics_pass_after_explicit_human_approval() -> None:
    package_root = Path(__file__).parents[1]
    tuning_dataset = EvaluationDataset.model_validate_json(
        (package_root / "datasets/msme-rag-v1.json").read_text()
    ).model_copy(
        update={
            "judgment_status": "human_approved",
            "reviewed_by": "Synthetic Test Reviewer",
            "reviewed_at": date(2026, 7, 17),
        }
    )
    heldout_dataset = EvaluationDataset.model_validate_json(
        (package_root / "datasets/msme-rag-heldout-v1.json").read_text()
    ).model_copy(
        update={
            "judgment_status": "human_approved",
            "reviewed_by": "Synthetic Test Reviewer",
            "reviewed_at": date(2026, 7, 17),
        }
    )
    tuning_report = EvaluationReport.model_validate_json(
        (package_root / "reports/msme-saarthi-semantic-v1-tuning-candidate.json").read_text()
    ).model_copy(update={"judgment_status": "human_approved", "dataset_sha256": "b" * 64})
    heldout_report = EvaluationReport.model_validate_json(
        (package_root / "reports/msme-saarthi-semantic-v1-heldout-candidate.json").read_text()
    ).model_copy(update={"judgment_status": "human_approved", "dataset_sha256": "c" * 64})
    thresholds = ReleaseThresholds.model_validate_json(
        (package_root / "release-gates-v1.json").read_text()
    )

    validate_release(
        tuning_dataset=tuning_dataset,
        tuning_dataset_sha256="b" * 64,
        heldout_dataset=heldout_dataset,
        heldout_dataset_sha256="c" * 64,
        tuning_report=tuning_report,
        heldout_report=heldout_report,
        thresholds=thresholds,
    )
