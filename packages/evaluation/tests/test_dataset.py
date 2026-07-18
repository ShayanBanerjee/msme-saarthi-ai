import json
from pathlib import Path

from rag_evaluation.models import EvaluationDataset


def test_v1_dataset_covers_all_reviewed_sources_without_crossing_evidence_classes() -> None:
    package_root = Path(__file__).parents[1]
    repository_root = package_root.parents[1]
    dataset = EvaluationDataset.model_validate_json(
        (package_root / "datasets/msme-rag-v1.json").read_text()
    )
    manifest = json.loads(
        (repository_root / "apps/worker/sources/official-central.json").read_text()
    )
    source_kinds = {item["source_id"]: item["source_kind"] for item in manifest}
    covered = {source_id for case in dataset.cases for source_id in case.expected_document_ids}

    assert covered == set(source_kinds)
    assert len(dataset.cases) == 31
    assert all(
        source_kinds[source_id] == case.source_kind
        for case in dataset.cases
        for source_id in case.expected_document_ids
    )


def test_heldout_dataset_is_separate_and_requires_human_review() -> None:
    package_root = Path(__file__).parents[1]
    dataset = EvaluationDataset.model_validate_json(
        (package_root / "datasets/msme-rag-heldout-v1.json").read_text()
    )

    assert dataset.split == "held_out"
    assert dataset.judgment_status == "candidate"
    assert dataset.require_full_manifest_coverage is False
    assert len(dataset.cases) == 20
    assert {case.source_kind for case in dataset.cases} == {
        "official_scheme",
        "business_guide",
    }
