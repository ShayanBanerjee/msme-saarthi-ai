# OpenSearch HTTP fixture

The retrieval integration test uses `httpx.MockTransport` as a deterministic OpenSearch REST fixture. It exercises the production HTTP adapter, request URLs, BM25 and k-NN request bodies, response parsing, hybrid fusion, and citation metadata without requiring Docker in the baseline repository.

The response data in `responses.json` is entirely synthetic. Its structure mirrors the `_search` fields consumed by the application. A future infrastructure task should add a scheduled compatibility test against the pinned production OpenSearch image; that test must use the same index mapping and fixture documents.

