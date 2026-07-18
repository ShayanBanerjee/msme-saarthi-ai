# Reviewed RAG source manifest

`official-central.json` is an explicit operator allowlist, not a crawler seed list. Each entry fixes the URL, host, document type, evidence class, language, and effective date used by the ingestion boundary.

| Source | Evidence class | Rights / authority | Purpose |
|---|---|---|---|
| Ministry of MSME · PMEGP | Official scheme | Government of India source page | Current source discovery and programme overview |
| Ministry of MSME · Udyam Registration | Official scheme | Government of India source page | Official registration evidence |
| DC MSME · Schemes Booklet 2025–26 | Official scheme PDF | Government of India publication | Consolidated MSME programme evidence |
| Startup India · Government Schemes Playbook, June 2026 | Official scheme PDF | Government of India publication | Current startup scheme discovery by stage and need |
| Ministry of MSME · MSME Connect, Jan–Mar 2026 | Official scheme PDF | Government of India publication | Current programme landscape and Ministry updates |
| Ministry of Food Processing Industries · PMFME Guidelines | Official scheme PDF | Government of India publication | Food-processing formalisation, credit, infrastructure and market-support evidence; users must verify current windows |
| 15 reviewed open-access books | Business guide PDFs | CC BY, CC BY-SA, or explicitly labelled non-commercial Creative Commons licences | Entrepreneurship, small-business finance, marketing, digital commerce, sustainable enterprise, and SME transformation techniques |

Business guides may support general techniques only. They cannot support a government-scheme, effective-date, benefit, application, or eligibility claim. Official evidence is descriptive and cannot become an eligibility rule without separate deterministic encoding and review.

The PDFs are fetched at ingestion time and are not committed to this repository. Text extraction is bounded to 140 MB, 800 pages, and six million extracted characters per source. Encrypted, non-PDF, image-only, wrong-host, private-network, oversized, and unsupported-content responses are rejected. Retrieved instructions, links, scripts, and attachments are never executed.

The reviewed business library is listed entry-by-entry in `official-central.json`. It contains 15 distinct books from university repositories and open-access publishers. Non-commercial licences require a legal/product review before any paid use. The two legacy OpenStax documents were removed because the publisher's current pages prohibit LLM ingestion.

Review source status, effective dates, licensing, and URL ownership before every production refresh. The current manifest review date is 2026-07-17. The local `msme-schemes-v2` index contains 11,565 business-guide chunks across exactly 15 books after the reviewed refresh with the 384-dimensional `local-feature-hash-v2` adapter. The manifest-hashed `packages/evaluation/datasets/msme-rag-v1.json` pilot covers every listed source. Production embedding runs must use a separate index name and the same model/dimensions at ingestion and query time.

On 2026-07-17, the non-extractable MeitY TIDE shell was replaced by MeitY Startup Hub's official administrative-approval PDF, and the unreachable ASPIRE host was replaced by the accessible Ministry of MSME scheme page. `msme-saarthi-semantic-v1` now contains all 31 reviewed sources and 12,090 chunks.
