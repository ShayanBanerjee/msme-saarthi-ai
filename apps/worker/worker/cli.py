"""Explicit operator CLI for reviewed source ingestion."""

import argparse
import asyncio
import json
from pathlib import Path

from pydantic import TypeAdapter

from worker.pipeline import HttpSourceFetcher, OpenSearchChunkSink, SourceSpec, ingest_source


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest allowlisted official source evidence")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--opensearch-url", default="http://127.0.0.1:9200")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    sources = TypeAdapter(tuple[SourceSpec, ...]).validate_python(
        json.loads(args.manifest.read_text())
    )
    if args.validate_only:
        print(
            f"Validated {len(sources)} allowlisted sources; no network or index writes performed."
        )
        return

    async def run() -> None:
        fetcher = HttpSourceFetcher()
        sink = OpenSearchChunkSink(base_url=args.opensearch_url)
        for source in sources:
            count = await ingest_source(source, fetcher=fetcher, sink=sink)
            print(f"{source.source_id}: indexed {count} chunks")

    asyncio.run(run())


if __name__ == "__main__":
    main()
