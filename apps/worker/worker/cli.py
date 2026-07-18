"""Explicit operator CLI for reviewed source ingestion."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from pydantic import TypeAdapter

from worker.pipeline import (
    DocumentEmbeddingProvider,
    HttpSourceFetcher,
    LocalFeatureEmbeddingProvider,
    OpenAIDocumentEmbeddingProvider,
    OpenSearchChunkSink,
    SourceSpec,
    ingest_source,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest allowlisted official source evidence")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--opensearch-url", default="http://127.0.0.1:9200")
    parser.add_argument("--index", default="msme-schemes-v2")
    parser.add_argument("--embedding-provider", choices=("local", "openai"), default="local")
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument("--embedding-dimensions", type=int, default=384)
    parser.add_argument(
        "--index-profile", choices=("development", "production"), default="development"
    )
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Ingest only the named reviewed source; may be repeated",
    )
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Attempt every selected source, then fail the job if any source failed",
    )
    args = parser.parse_args()
    sources = TypeAdapter(tuple[SourceSpec, ...]).validate_python(
        json.loads(args.manifest.read_text())
    )
    if args.source_ids:
        selected_ids = set(args.source_ids)
        sources = tuple(source for source in sources if source.source_id in selected_ids)
        found_ids = {source.source_id for source in sources}
        missing_ids = selected_ids - found_ids
        if missing_ids:
            parser.error(f"unknown source id(s): {', '.join(sorted(missing_ids))}")
    if args.validate_only:
        print(
            f"Validated {len(sources)} allowlisted sources; no network or index writes performed."
        )
        return

    async def run() -> None:
        fetcher = HttpSourceFetcher()
        embedder: DocumentEmbeddingProvider = LocalFeatureEmbeddingProvider(
            dimensions=args.embedding_dimensions
        )
        if args.embedding_provider == "openai":
            api_key = os.getenv("MSME_SAARTHI_OPENAI_API_KEY", "")
            embedder = OpenAIDocumentEmbeddingProvider(
                api_key=api_key,
                model=args.embedding_model,
                dimensions=args.embedding_dimensions,
            )
        sink = OpenSearchChunkSink(
            base_url=args.opensearch_url,
            index=args.index,
            embedding_dimensions=args.embedding_dimensions,
            index_profile=args.index_profile,
        )
        failed: list[str] = []
        for source in sources:
            try:
                count = await ingest_source(source, fetcher=fetcher, sink=sink, embedder=embedder)
            except Exception as error:
                if not args.continue_on_error:
                    raise
                failed.append(source.source_id)
                print(f"{source.source_id}: FAILED ({type(error).__name__})", flush=True)
                continue
            print(f"{source.source_id}: indexed {count} chunks", flush=True)
        if failed:
            raise RuntimeError(f"ingestion failed for {len(failed)} source(s): {', '.join(failed)}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
