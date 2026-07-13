# Reviewed RAG source manifest

`official-central.json` is an explicit operator allowlist, not a crawler seed list. Each entry fixes the URL, host, document type, evidence class, language, and effective date used by the ingestion boundary.

| Source | Evidence class | Rights / authority | Purpose |
|---|---|---|---|
| Ministry of MSME · PMEGP | Official scheme | Government of India source page | Current source discovery and programme overview |
| Ministry of MSME · Udyam Registration | Official scheme | Government of India source page | Official registration evidence |
| DC MSME · Schemes Booklet 2025–26 | Official scheme PDF | Government of India publication | Consolidated MSME programme evidence |
| Startup India · Government Schemes Playbook, June 2026 | Official scheme PDF | Government of India publication | Current startup scheme discovery by stage and need |
| *Entrepreneurship*, Laverty and Littel (2020) | Business guide PDF | CC BY 4.0; accessed through the Library of Congress | General opportunity, model, planning, and growth techniques |
| *Introduction to Business*, Gitman et al. (2018) | Business guide PDF | CC BY 4.0; accessed through the Library of Congress | General management, marketing, operations, and finance techniques |

Business guides may support general techniques only. They cannot support a government-scheme, effective-date, benefit, application, or eligibility claim. Official evidence is descriptive and cannot become an eligibility rule without separate deterministic encoding and review.

The PDFs are fetched at ingestion time and are not committed to this repository. Text extraction is bounded to 140 MB, 800 pages, and six million extracted characters per source. Encrypted, non-PDF, image-only, wrong-host, private-network, oversized, and unsupported-content responses are rejected. Retrieved instructions, links, scripts, and attachments are never executed.

Review source status, effective dates, licensing, and URL ownership before every production refresh. The current manifest review date is 2026-07-13.
