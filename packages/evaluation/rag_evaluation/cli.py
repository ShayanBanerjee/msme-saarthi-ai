"""Command-line entry point for versioned retrieval evaluation."""

import argparse
import asyncio
import hashlib
import os
from pathlib import Path

from rag_evaluation.runner import load_inputs, report_json, run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate MSME RAG retrieval and citations")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--opensearch-url", default="http://127.0.0.1:9200")
    parser.add_argument("--index", required=True)
    parser.add_argument("--embedding-provider", choices=("local", "openai"), default="local")
    parser.add_argument("--embedding-model", default="local-feature-hash-v2")
    parser.add_argument("--embedding-dimensions", type=int, default=384)
    parser.add_argument("--openai-base-url", default="https://api.openai.com/v1")
    parser.add_argument("--candidates", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--fusion-rank-constant", type=int, default=60)
    parser.add_argument("--fusion-lexical-weight", type=float, default=0.8)
    parser.add_argument("--fusion-vector-weight", type=float, default=1.0)
    parser.add_argument("--fusion-max-chunks-per-document", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 10 <= args.candidates <= 1_000:
        parser.error("candidates must be between 10 and 1000")
    if not 1 <= args.concurrency <= 16:
        parser.error("concurrency must be between 1 and 16")

    dataset, manifest = load_inputs(args.dataset, args.manifest)
    report = asyncio.run(
        run_evaluation(
            dataset=dataset,
            dataset_sha256=hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
            manifest=manifest,
            base_url=args.opensearch_url,
            index=args.index,
            embedding_provider=args.embedding_provider,
            embedding_model=args.embedding_model,
            embedding_dimensions=args.embedding_dimensions,
            api_key=os.getenv("MSME_SAARTHI_OPENAI_API_KEY", ""),
            openai_base_url=args.openai_base_url,
            candidates=args.candidates,
            concurrency=args.concurrency,
            fusion_rank_constant=args.fusion_rank_constant,
            fusion_lexical_weight=args.fusion_lexical_weight,
            fusion_vector_weight=args.fusion_vector_weight,
            fusion_max_chunks_per_document=args.fusion_max_chunks_per_document,
        )
    )
    rendered = report_json(report)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
