# Security Policy

MSME Saarthi AI handles identity, enterprise-profile, conversation, and eligibility-assessment data. Security reports are welcome and should be handled privately.

## Supported versions

The project is pre-release. Only the current default branch is maintained, and it is not approved for production customer data. There is no security support commitment for old commits, forks, local modifications, or unofficial deployments.

## Reporting a vulnerability

Do not open a public issue or include exploit details in a public pull request. Use the repository host's private security-advisory feature. If private advisories are unavailable, contact the repository owner through a private channel before sharing technical details.

Include, where possible:

- the affected commit, component, endpoint, or configuration;
- impact and realistic attack prerequisites;
- minimal reproduction steps using synthetic data;
- relevant logs with secrets, tokens, personal data, and private URLs removed; and
- a suggested mitigation, if known.

The maintainers will handle reports on a best-effort basis while the project is pre-release; no formal response or remediation SLA is currently offered. Please coordinate disclosure so users have time to update.

## High-priority report areas

- authentication, session fixation, account recovery, or authorization bypass;
- cross-tenant access or exposure of encrypted profile/chat data;
- cryptographic key, password, token, or provider-secret disclosure;
- ingestion SSRF, redirect/DNS bypass, parser abuse, or unsafe file handling;
- prompt injection that invokes an unauthorized action or produces an uncited material claim;
- any path that lets an LLM create, override, or independently decide eligibility;
- citation forgery, draft-content publication, or scheme-version integrity failure;
- dependency, container, CI/CD, Terraform, or cloud privilege escalation.

## Responsible testing

Test against a local environment or an environment you own, using synthetic data. Do not access another person's account or data, degrade a service, persist access, use social engineering, send unsolicited traffic, or exfiltrate data. Stop once you have enough evidence to report the issue safely.

## Secrets and local deployment

Never commit or transmit `.env` files, API keys, session cookies, database dumps, or encryption keys. If a secret is exposed, revoke or rotate it immediately; deleting it from the latest commit is not sufficient.

The Docker Compose credentials, loopback bindings, and disabled OpenSearch security are for local development only. They must never be exposed to a network or reused in staging or production. Production requires managed secrets, TLS, private data services, least-privilege identities, encryption at rest, audited key management, backups, and tested recovery.

The detailed engineering threat model and release gates are in [docs/security/THREAT_MODEL.md](docs/security/THREAT_MODEL.md).
