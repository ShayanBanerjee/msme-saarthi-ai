"""Fail-closed release gates and atomic OpenSearch alias promotion."""

import argparse
import asyncio
import hashlib
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from rag_evaluation.models import EvaluationDataset, EvaluationReport


class ReleaseThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"]
    alias: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
    required_document_count: int = Field(ge=1)
    fusion_rank_constant: int = Field(ge=1)
    fusion_lexical_weight: float = Field(gt=0)
    fusion_vector_weight: float = Field(gt=0)
    fusion_max_chunks_per_document: int = Field(ge=1)
    minimum_tuning_hybrid_hit_rate_at_5: float = Field(ge=0, le=1)
    minimum_heldout_hybrid_hit_rate_at_5: float = Field(ge=0, le=1)
    minimum_heldout_official_hit_rate_at_5: float = Field(ge=0, le=1)
    minimum_heldout_guide_hit_rate_at_5: float = Field(ge=0, le=1)
    minimum_heldout_hybrid_mrr: float = Field(ge=0, le=1)
    minimum_heldout_hybrid_ndcg_at_10: float = Field(ge=0, le=1)
    required_citation_resolvability: float = Field(ge=0, le=1)
    required_citation_metadata_completeness: float = Field(ge=0, le=1)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_release(
    *,
    tuning_dataset: EvaluationDataset,
    tuning_dataset_sha256: str,
    heldout_dataset: EvaluationDataset,
    heldout_dataset_sha256: str,
    tuning_report: EvaluationReport,
    heldout_report: EvaluationReport,
    thresholds: ReleaseThresholds,
) -> None:
    """Raise with an actionable reason unless every immutable release gate passes."""
    if tuning_dataset.split != "tuning" or heldout_dataset.split != "held_out":
        raise ValueError("release requires distinct tuning and held-out datasets")
    if (
        tuning_dataset.judgment_status != "human_approved"
        or heldout_dataset.judgment_status != "human_approved"
    ):
        raise ValueError("alias promotion requires named human-approved relevance judgments")
    if tuning_report.judgment_status != "human_approved" or heldout_report.judgment_status != (
        "human_approved"
    ):
        raise ValueError("reports must be regenerated after human judgment approval")
    if tuning_report.dataset_sha256 != tuning_dataset_sha256 or (
        heldout_report.dataset_sha256 != heldout_dataset_sha256
    ):
        raise ValueError("report dataset hash does not match the reviewed dataset")
    if tuning_report.index_name != heldout_report.index_name:
        raise ValueError("tuning and held-out reports must evaluate the same index")
    if tuning_report.indexed_document_count != thresholds.required_document_count or (
        heldout_report.indexed_document_count != thresholds.required_document_count
    ):
        raise ValueError("semantic index does not contain every reviewed source")
    expected_fusion = (
        thresholds.fusion_rank_constant,
        thresholds.fusion_lexical_weight,
        thresholds.fusion_vector_weight,
        thresholds.fusion_max_chunks_per_document,
    )
    for report in (tuning_report, heldout_report):
        actual_fusion = (
            report.fusion_rank_constant,
            report.fusion_lexical_weight,
            report.fusion_vector_weight,
            report.fusion_max_chunks_per_document,
        )
        if actual_fusion != expected_fusion:
            raise ValueError("report fusion configuration does not match the release contract")
    tuning = tuning_report.overall["hybrid"]
    heldout = heldout_report.overall["hybrid"]
    official = heldout_report.by_source_kind["official_scheme"]["hybrid"]
    guides = heldout_report.by_source_kind["business_guide"]["hybrid"]
    gates = {
        "tuning hybrid hit@5": (
            tuning.hit_rate_at_5,
            thresholds.minimum_tuning_hybrid_hit_rate_at_5,
        ),
        "held-out hybrid hit@5": (
            heldout.hit_rate_at_5,
            thresholds.minimum_heldout_hybrid_hit_rate_at_5,
        ),
        "held-out official hit@5": (
            official.hit_rate_at_5,
            thresholds.minimum_heldout_official_hit_rate_at_5,
        ),
        "held-out guide hit@5": (
            guides.hit_rate_at_5,
            thresholds.minimum_heldout_guide_hit_rate_at_5,
        ),
        "held-out hybrid MRR": (
            heldout.mean_reciprocal_rank,
            thresholds.minimum_heldout_hybrid_mrr,
        ),
        "held-out hybrid nDCG@10": (
            heldout.ndcg_at_10,
            thresholds.minimum_heldout_hybrid_ndcg_at_10,
        ),
        "citation resolvability": (
            heldout.citation_resolvability,
            thresholds.required_citation_resolvability,
        ),
        "citation metadata completeness": (
            heldout.citation_metadata_completeness,
            thresholds.required_citation_metadata_completeness,
        ),
    }
    failures = [name for name, (actual, required) in gates.items() if actual < required]
    if failures:
        raise ValueError(f"release thresholds failed: {', '.join(failures)}")


async def promote_alias(*, base_url: str, index: str, alias: str) -> None:
    """Atomically move the read alias after all offline gates have passed."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        index_response = await client.head(f"{base_url.rstrip('/')}/{index}")
        index_response.raise_for_status()
        aliases_response = await client.get(f"{base_url.rstrip('/')}/_alias/{alias}")
        existing: tuple[str, ...] = ()
        if aliases_response.status_code == 200:
            payload = aliases_response.json()
            if isinstance(payload, dict):
                existing = tuple(str(item) for item in payload)
        elif aliases_response.status_code != 404:
            aliases_response.raise_for_status()
        actions: list[dict[str, dict[str, object]]] = [
            {"remove": {"index": item, "alias": alias}} for item in existing
        ]
        actions.append({"add": {"index": index, "alias": alias, "is_write_index": False}})
        response = await client.post(f"{base_url.rstrip('/')}/_aliases", json={"actions": actions})
        response.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description="Gate and promote a semantic index alias")
    parser.add_argument("--tuning-dataset", type=Path, required=True)
    parser.add_argument("--heldout-dataset", type=Path, required=True)
    parser.add_argument("--tuning-report", type=Path, required=True)
    parser.add_argument("--heldout-report", type=Path, required=True)
    parser.add_argument("--thresholds", type=Path, required=True)
    parser.add_argument("--opensearch-url", default="http://127.0.0.1:9200")
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    tuning_dataset = EvaluationDataset.model_validate_json(args.tuning_dataset.read_text())
    heldout_dataset = EvaluationDataset.model_validate_json(args.heldout_dataset.read_text())
    tuning_report = EvaluationReport.model_validate_json(args.tuning_report.read_text())
    heldout_report = EvaluationReport.model_validate_json(args.heldout_report.read_text())
    thresholds = ReleaseThresholds.model_validate_json(args.thresholds.read_text())
    validate_release(
        tuning_dataset=tuning_dataset,
        tuning_dataset_sha256=_sha256(args.tuning_dataset),
        heldout_dataset=heldout_dataset,
        heldout_dataset_sha256=_sha256(args.heldout_dataset),
        tuning_report=tuning_report,
        heldout_report=heldout_report,
        thresholds=thresholds,
    )
    if args.promote:
        asyncio.run(
            promote_alias(
                base_url=args.opensearch_url,
                index=heldout_report.index_name,
                alias=thresholds.alias,
            )
        )
        print(f"Promoted {thresholds.alias} -> {heldout_report.index_name}")
    else:
        print("Release gates passed; alias was not changed (use --promote to apply).")


if __name__ == "__main__":
    main()
