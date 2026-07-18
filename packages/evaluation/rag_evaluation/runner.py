"""Production-retrieval adapter used by the offline evaluator."""

import asyncio
import hashlib
import json
import time
from collections.abc import Mapping
from datetime import date, timedelta
from pathlib import Path

import httpx
from app.retrieval.client import HttpOpenSearchClient
from app.retrieval.embedding import (
    EmbeddingProvider,
    LocalFeatureEmbeddingProvider,
    OpenAIEmbeddingProvider,
)
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import (
    OpenSearchHit,
    OpenSearchResponse,
    RetrievalFilters,
    SourceKind,
)
from app.retrieval.queries import build_bm25_query, build_vector_query
from pydantic import TypeAdapter

from rag_evaluation.metrics import evaluate_rankings
from rag_evaluation.models import (
    EvaluationDataset,
    EvaluationReport,
    ManifestSource,
    RankedCitation,
    SearchMode,
)


def load_inputs(
    dataset_path: Path, manifest_path: Path
) -> tuple[EvaluationDataset, dict[str, ManifestSource]]:
    manifest_bytes = manifest_path.read_bytes()
    dataset = EvaluationDataset.model_validate_json(dataset_path.read_text())
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    if digest != dataset.corpus_manifest_sha256:
        raise ValueError("dataset corpus manifest hash does not match the reviewed manifest")
    sources = TypeAdapter(tuple[ManifestSource, ...]).validate_json(manifest_bytes)
    manifest = {source.source_id: source for source in sources}
    expected = {item for case in dataset.cases for item in case.expected_document_ids}
    if dataset.require_full_manifest_coverage and expected != set(manifest):
        missing = sorted(set(manifest) - expected)
        unknown = sorted(expected - set(manifest))
        raise ValueError(f"dataset source coverage mismatch; missing={missing}, unknown={unknown}")
    for case in dataset.cases:
        if any(
            manifest[item].source_kind != case.source_kind for item in case.expected_document_ids
        ):
            raise ValueError(f"case {case.case_id} crosses evidence classes")
    return dataset, manifest


def _rank_hits(hits: tuple[OpenSearchHit, ...]) -> tuple[RankedCitation, ...]:
    seen: set[str] = set()
    ranked: list[RankedCitation] = []
    for hit in hits:
        source = hit.source
        if source.document_id in seen:
            continue
        seen.add(source.document_id)
        ranked.append(
            RankedCitation(
                document_id=source.document_id,
                citation_id=source.citation_id,
                source_url=source.source_url,
                source_label=source.source_label,
                page=source.page,
                section=source.section,
            )
        )
    return tuple(ranked)


async def _inspect_index(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    index: str,
    embedding_model: str,
    embedding_dimensions: int,
) -> tuple[int, int]:
    mapping_response = await client.get(f"{base_url.rstrip('/')}/{index}/_mapping")
    mapping_response.raise_for_status()
    mapping = mapping_response.json()[index]["mappings"]["properties"]["embedding"]
    if mapping.get("dimension") != embedding_dimensions:
        raise ValueError("index embedding dimension does not match evaluator configuration")
    stats_response = await client.post(
        f"{base_url.rstrip('/')}/{index}/_search",
        json={
            "size": 0,
            "track_total_hits": True,
            "query": {"term": {"embedding_model": embedding_model}},
            "aggs": {"documents": {"cardinality": {"field": "document_id.keyword"}}},
        },
    )
    stats_response.raise_for_status()
    payload = stats_response.json()
    chunk_count = int(payload["hits"]["total"]["value"])
    document_count = int(payload["aggregations"]["documents"]["value"])
    if chunk_count < 1 or document_count < 1:
        raise ValueError("index has no chunks for the configured embedding model")
    return chunk_count, document_count


async def run_evaluation(
    *,
    dataset: EvaluationDataset,
    dataset_sha256: str,
    manifest: Mapping[str, ManifestSource],
    base_url: str,
    index: str,
    embedding_provider: str,
    embedding_model: str,
    embedding_dimensions: int,
    api_key: str = "",
    openai_base_url: str = "https://api.openai.com/v1",
    candidates: int = 50,
    concurrency: int = 4,
    fusion_rank_constant: int = 60,
    fusion_lexical_weight: float = 0.8,
    fusion_vector_weight: float = 1.0,
    fusion_max_chunks_per_document: int = 1,
) -> EvaluationReport:
    started = time.perf_counter()
    embedder: EmbeddingProvider = LocalFeatureEmbeddingProvider(dimensions=embedding_dimensions)
    if embedding_provider == "openai":
        embedder = OpenAIEmbeddingProvider(
            api_key=api_key,
            model=embedding_model,
            dimensions=embedding_dimensions,
            base_url=openai_base_url,
            timeout_seconds=60.0,
        )
    elif embedding_provider != "local":
        raise ValueError("embedding_provider must be local or openai")

    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout) as http_client:
        chunk_count, document_count = await _inspect_index(
            http_client,
            base_url=base_url,
            index=index,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
        )
        search_client = HttpOpenSearchClient(client=http_client, base_url=base_url)
        semaphore = asyncio.Semaphore(concurrency)

        async def run_case(
            case_id: str,
        ) -> tuple[str, dict[SearchMode, tuple[RankedCitation, ...]]]:
            case = next(item for item in dataset.cases if item.case_id == case_id)
            max_age = 90 if case.source_kind == "official_scheme" else 3_650
            today = date.today()
            filters = RetrievalFilters(
                source_kind=SourceKind(case.source_kind),
                effective_on=today,
                captured_after=today - timedelta(days=max_age),
                captured_before=today,
            )
            async with semaphore:
                vector = await embedder.embed_query(case.query)
                lexical_raw, vector_raw = await asyncio.gather(
                    search_client.search(
                        index=index,
                        body=build_bm25_query(
                            query=case.query, filters=filters, candidates=candidates
                        ),
                    ),
                    search_client.search(
                        index=index,
                        body=build_vector_query(
                            vector=vector, filters=filters, candidates=candidates
                        ),
                    ),
                )
            lexical = OpenSearchResponse.model_validate(lexical_raw).hits.hits
            semantic = OpenSearchResponse.model_validate(vector_raw).hits.hits
            hybrid = reciprocal_rank_fusion(
                lexical_hits=lexical,
                vector_hits=semantic,
                limit=candidates,
                rank_constant=fusion_rank_constant,
                lexical_weight=fusion_lexical_weight,
                vector_weight=fusion_vector_weight,
                max_chunks_per_document=fusion_max_chunks_per_document,
            )
            hybrid_hits = tuple(
                RankedCitation(
                    document_id=item.document_id,
                    citation_id=item.citation_id,
                    source_url=item.source_url,
                    source_label=item.source_label,
                    page=item.page,
                    section=item.section,
                )
                for item in hybrid
            )
            deduplicated_hybrid: list[RankedCitation] = []
            seen: set[str] = set()
            for item in hybrid_hits:
                if item.document_id not in seen:
                    seen.add(item.document_id)
                    deduplicated_hybrid.append(item)
            return case_id, {
                "lexical": _rank_hits(lexical),
                "vector": _rank_hits(semantic),
                "hybrid": tuple(deduplicated_hybrid),
            }

        results = await asyncio.gather(*(run_case(case.case_id) for case in dataset.cases))

    rankings = dict(results)
    overall, by_kind, cases = evaluate_rankings(
        cases=dataset.cases, rankings=rankings, manifest=manifest
    )
    return EvaluationReport.model_validate(
        {
            "dataset_version": dataset.dataset_version,
            "dataset_sha256": dataset_sha256,
            "dataset_split": dataset.split,
            "judgment_status": dataset.judgment_status,
            "corpus_manifest_sha256": dataset.corpus_manifest_sha256,
            "index_name": index,
            "embedding_provider": embedding_provider,
            "embedding_model": embedding_model,
            "embedding_dimensions": embedding_dimensions,
            "fusion_rank_constant": fusion_rank_constant,
            "fusion_lexical_weight": fusion_lexical_weight,
            "fusion_vector_weight": fusion_vector_weight,
            "fusion_max_chunks_per_document": fusion_max_chunks_per_document,
            "indexed_chunk_count": chunk_count,
            "indexed_document_count": document_count,
            "duration_ms": round((time.perf_counter() - started) * 1_000),
            "overall": overall,
            "by_source_kind": by_kind,
            "cases": cases,
        }
    )


def report_json(report: EvaluationReport) -> str:
    return json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
