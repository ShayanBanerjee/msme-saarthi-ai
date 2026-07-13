# Deterministic Eligibility Engine

**Status:** Pre-implementation specification  
**Last updated:** 2026-07-13  
**Related:** [Data model](../architecture/DATA_MODEL.md), [ADR-0002](../architecture/adr/0002-deterministic-eligibility-boundary.md)

## 1. Non-negotiable boundary

Only the deterministic eligibility engine decides whether supplied profile facts satisfy a published scheme rule set. An LLM may collect missing facts and explain a stored result, but it may not write executable rules, supply inferred facts as user facts, call a hidden alternate decision path, or change any outcome.

An `eligible` result means “the provided facts satisfy this encoded rule-set version.” It does not predict or guarantee programme approval. If required facts are unknown, the result is `insufficient_information`; technical errors never become `ineligible`.

## 2. Package design

`packages/eligibility-engine` is a pure, typed package with no database, network, framework, clock, random, model, or environment dependencies. Inputs include every variable that can affect output. It exposes:

- rule-schema parsing and semantic validation;
- profile normalization contract validation;
- deterministic evaluation;
- structured per-rule outcomes and missing fact paths;
- canonical input/rule hashing; and
- stable reason codes suitable for separately rendered explanations.

Persistence, authorization, rule publication, localization, citations, and prose generation remain outside the package.

## 3. Versioned inputs

```text
EvaluationInput
  profile_schema_version
  normalized_facts
  scheme_version_id
  rule_set_version_id
  engine_schema_version
  evaluation_as_of_date

EvaluationOutput
  decision: eligible | ineligible | insufficient_information
  rule_outcomes[]
  missing_fact_paths[]
  input_hash
  rules_hash
  engine_version
```

The service resolves and freezes all dates, versions, and facts before calling the engine. Canonical serialization defines Unicode, decimals, date formats, key ordering, set ordering, and null/unknown behavior so identical inputs hash and evaluate identically.

## 4. Rule model

The MVP supports a deliberately small allowlist:

- MVP comparison: `equals`, `in`, `less_than_or_equal`, `greater_than_or_equal`, `between`, and `exists`;
- composition: `all`, `any`, and `not`.

Additional membership, temporal, collection, or inequality operators require a later schema version and the compatibility process in section 10.

Each atomic rule contains a stable key, fact path, expected typed value, operator, missing policy, reason code/template key, and supporting citation. Rules are declarative data conforming to a versioned schema; no expressions, code snippets, SQL, regex from untrusted authors, or model-generated functions execute.

Synthetic example only:

```json
{
  "rule_key": "synthetic_location",
  "operator": "in",
  "fact_path": "facts.state_code",
  "expected_value": ["EX-A", "EX-B"],
  "missing_policy": "insufficient_information",
  "citation_id": "synthetic-citation-1"
}
```

The names and values above are invented test data and do not describe a real scheme.

## 5. Three-valued evaluation

Atomic outcomes are `passed`, `failed`, or `unknown`. Composition follows strong three-valued logic:

| Operator | Passed | Failed | Unknown |
|---|---|---|---|
| `all` | all children passed | any child failed | otherwise |
| `any` | any child passed | all children failed | otherwise |
| `not` | child failed | child passed | child unknown |

Evaluation may short-circuit for performance but must return stable documented outcome detail. Rules skipped after a decisive result are `not_evaluated`, never falsely satisfied/failed.

Root mapping:

- `passed` -> `eligible`;
- `failed` -> `ineligible`;
- `unknown` -> `insufficient_information`.

Missing facts, explicit unknown facts, invalid fact types, and rule-definition errors are different cases. Missing required facts yield `unknown`; invalid caller data or invalid rules fail validation and produce no decision.

## 6. Type and numeric semantics

- Facts are validated by a versioned profile schema before evaluation.
- Money and decimal quantities use exact decimal semantics, never binary floating point.
- Units are explicit and normalized outside comparisons; no implicit conversion without a versioned deterministic converter.
- Dates are ISO calendar dates and use the supplied `evaluation_as_of_date`; the engine never reads today implicitly.
- Enumerations use stable codes, not display labels.
- String comparisons define Unicode normalization and case behavior per field.
- Arrays that represent sets are de-duplicated and canonicalized.
- Threshold boundaries receive explicit tests for equality and adjacent values.

## 7. Rule authoring and lifecycle

1. Ingestion may identify candidate eligibility language from approved evidence.
2. A content reviewer authors or edits a draft typed rule set, linking each criterion to citations.
3. Schema/semantic validation and golden boundary tests run.
4. A permitted reviewer approves publication; separation of duties is a policy decision.
5. Publication creates an immutable rule-set version tied to an immutable scheme version.
6. New assessments use the active applicable version; prior assessments retain old versions.

Material source changes create a review task, never an automatic executable rule change. Effective periods may select a rule-set version in the service layer; overlapping/gapped periods fail publication validation.

## 8. Service integration

- Service authenticates, authorizes, loads a published rule set, and creates a profile snapshot.
- It invokes the engine in-process in the modular monolith.
- It persists input/rule hashes, exact version IDs, output, engine version, and rule outcomes atomically.
- Optional explanations consume the persisted result and citations after completion.
- Client, model, and retrieved documents cannot pass an arbitrary rule set into public assessment endpoints.
- Reassessment creates a new record; completed assessments are immutable.

## 9. Explanation contract

The engine emits facts, not polished advice: decision, reason codes, rule keys, safe actual/expected representations, missing paths, and citation IDs. A deterministic template renderer must always be available. An LLM renderer is optional and must be checked against the structured output; if it fails, the deterministic result and templates remain available.

## 10. Validation and testing

- Schema tests reject unknown fields/operators, type mismatches, invalid fact paths, missing citations, cycles, empty compositions, excessive depth/size, and ambiguous dates.
- Table-driven tests cover each operator, three-valued truth tables, boundaries, nesting, and deterministic order.
- Property tests cover determinism, canonical hashes, De Morgan properties where applicable, and no decision on invalid inputs.
- Golden tests use invented schemes and profiles, reviewer-approved expected outcomes, and fixed engine/rule versions.
- Mutation tests are recommended for comparison and composition code.
- Integration tests prove only published rules are selected and completed records are immutable.
- Adversarial tests prove prompts/documents cannot inject rules or decision values.

Any engine schema change requires compatibility tests, an engine version change where behavior changes, migration guidance for stored rules, and replay against the golden corpus.

## 11. Later-phase considerations

Later phases may add reviewed operators, deterministic derived facts, rule-authoring UI, simulation, and batch assessment. None may weaken the deterministic boundary. Statistical ranking may prioritize schemes for review but must be labeled separately from eligibility.

## 12. Open decisions

- Final profile fact taxonomy and rule JSON schema.
- Whether the package is Python-only or generated from a language-neutral schema for client-side preview (server remains authoritative).
- Reviewer roles and required approval count.
- Rules for schemes with discretionary or qualitative criteria that cannot be deterministically encoded.
- Retention/redaction policy for safe actual values in rule outcomes.
