"""Strict schemas for versioned evaluation inputs and machine-readable reports."""

from datetime import UTC, date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

SourceKind = Literal["official_scheme", "business_guide"]
SearchMode = Literal["lexical", "vector", "hybrid"]
DatasetSplit = Literal["tuning", "held_out"]
JudgmentStatus = Literal["candidate", "human_approved"]


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(pattern=r"^[a-z0-9-]{3,100}$")
    query: str = Field(min_length=8, max_length=500)
    expected_document_ids: tuple[str, ...] = Field(min_length=1)
    source_kind: SourceKind
    tags: tuple[str, ...] = ()


class EvaluationDataset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"]
    dataset_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    description: str = Field(min_length=20, max_length=500)
    corpus_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    split: DatasetSplit = "tuning"
    judgment_status: JudgmentStatus = "candidate"
    reviewed_by: str | None = Field(default=None, min_length=3, max_length=100)
    reviewed_at: date | None = None
    require_full_manifest_coverage: bool = True
    cases: tuple[EvaluationCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_case_ids(self) -> "EvaluationDataset":
        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("evaluation case IDs must be unique")
        if self.judgment_status == "human_approved" and (
            self.reviewed_by is None or self.reviewed_at is None
        ):
            raise ValueError("human-approved judgments require reviewer identity and date")
        if self.judgment_status == "candidate" and (
            self.reviewed_by is not None or self.reviewed_at is not None
        ):
            raise ValueError("candidate judgments cannot claim reviewer approval")
        return self


class ManifestSource(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    source_id: str
    label: str
    url: HttpUrl
    source_kind: SourceKind


class RankedCitation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    citation_id: str
    source_url: HttpUrl
    source_label: str
    page: int = Field(ge=1)
    section: str = Field(min_length=1)


class ModeMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_count: int = Field(ge=1)
    hit_rate_at_5: float = Field(ge=0, le=1)
    recall_at_10: float = Field(ge=0, le=1)
    mean_reciprocal_rank: float = Field(ge=0, le=1)
    ndcg_at_10: float = Field(ge=0, le=1)
    expected_source_coverage: float = Field(ge=0, le=1)
    citation_accuracy_at_5: float = Field(ge=0, le=1)
    citation_resolvability: float = Field(ge=0, le=1)
    citation_metadata_completeness: float = Field(ge=0, le=1)


class CaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    source_kind: SourceKind
    expected_document_ids: tuple[str, ...]
    ranks: dict[SearchMode, int | None]


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    report_schema_version: Literal["1"] = "1"
    dataset_version: str
    dataset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dataset_split: DatasetSplit
    judgment_status: JudgmentStatus
    corpus_manifest_sha256: str
    index_name: str
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    fusion_rank_constant: int = Field(ge=1)
    fusion_lexical_weight: float = Field(gt=0)
    fusion_vector_weight: float = Field(gt=0)
    fusion_max_chunks_per_document: int = Field(ge=1)
    indexed_chunk_count: int = Field(ge=1)
    indexed_document_count: int = Field(ge=1)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int = Field(ge=0)
    overall: dict[SearchMode, ModeMetrics]
    by_source_kind: dict[SourceKind, dict[SearchMode, ModeMetrics]]
    cases: tuple[CaseResult, ...]
