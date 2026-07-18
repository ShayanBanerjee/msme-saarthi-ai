# RAG retrieval comparison — 2026-07-16

Dataset: `msme-rag-v1` (`1.0.0`, 31 cases, 16 official sources, 15 books).

| Index / mode | Hit and citation accuracy @5 | Recall @10 | MRR | nDCG @10 | Resolvable citations |
|---|---:|---:|---:|---:|---:|
| Local hash / lexical | 48.39% | 48.39% | 0.406 | 0.422 | 100% of returned |
| Local hash / vector | 35.48% | 45.16% | 0.202 | 0.238 | 100% of returned |
| Local hash / hybrid | 48.39% | 48.39% | 0.336 | 0.369 | 100% of returned |
| Semantic / lexical | 87.10% | 87.10% | 0.745 | 0.774 | 100% of returned |
| Semantic / vector | **90.32%** | **90.32%** | **0.828** | **0.838** | **100% of returned** |
| Semantic / hybrid | 87.10% | 87.10% | 0.747 | 0.774 | 100% of returned |

## Evidence-class results

- All semantic modes achieved 100% hit@5, recall@10, expected-source coverage, citation resolvability, and citation metadata completeness across the 15 books.
- Semantic vector retrieval achieved 81.25% hit@5 across the 16 official-source cases. Hybrid achieved 75%.
- The local index's official cohort scored zero because its 497 legacy official chunks have no `captured_at`; production freshness filtering correctly fails closed.
- The semantic index contains 12,073 chunks across 29 sources: all 15 books and 14 of 16 official sources. The official TIDE page returned an empty client-rendered shell to the bounded fetcher, and the official ASPIRE host timed out after bounded retries.
- The one-chunk Startup India Seed Fund source was indexed but did not enter the top 10 for its pilot query. The one-chunk SAMRIDH source ranked third in vector retrieval but was crowded out of the top hybrid chunk pool.

## Decision

`msme-saarthi-semantic-v1` is a separate, production-profile local index built with `text-embedding-3-large` at 1,024 dimensions, strict provenance fields, Lucene HNSW cosine search, one replica, and idempotent bulk writes. It is a measured candidate, not a production deployment or approved launch gate. Before promotion, resolve the two upstream source gaps, expand relevance judgements, tune hybrid fusion/source crowding against a held-out set, complete licence/privacy review, and deploy the same mapping to a managed multi-node OpenSearch environment.
