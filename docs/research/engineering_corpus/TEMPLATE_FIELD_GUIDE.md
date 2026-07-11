# Engineering Microtopic Template v2.1 Field Guide

## Purpose

A microtopic is the smallest engineering unit that can be explained, verified and assessed without importing an entire chapter. The retrievable record stores the corrected canonical knowledge, not a history of rejected claims.

## Atomicity rule

Create a separate microtopic when the governing equation, assumptions, validity range, boundary conditions, numerical method or assessment target changes independently. Do not split mere notation changes.

## Field interpretation

- `identity` gives a stable canonical identifier and record type.
- `classification` places the record in course, domain and subdomain.
- `source_evidence` contains file hash, exact locator and authority. It proves provenance only.
- `knowledge` contains the corrected definition, physical meaning, equations, variables, assumptions, validity, procedure and relations.
- `verification` records the methods that justify the canonical content and controls whether it can be exported.
- `assessment` proposes benchmark uses without embedding solutions or gold.
- `jarvis` separates deterministic tool authority from AI interpretation.
- `governance.retention_policy` must equal `canonical_verified_knowledge_only`.

## Verification ladder

1. `unreviewed` — candidate only; never export.
2. `source_supported` — coherent with the source but not independently reproduced.
3. `dimensionally_checked` — units and dimensions are consistent.
4. `numerically_reproduced` — calculations or data transformations have been independently reproduced.
5. `cross_source_verified` — derivation, reference or independent formulation agrees.
6. `expert_verified` — assumptions and interpretation have received domain review.

`knowledge_exportable` is a separate explicit gate. A high-confidence source is not sufficient by itself.

## Handling source errors

Correct them during QA. Store only the corrected canonical statement in `knowledge`. Preserve source file hash and locator so the decision can be reproduced, but do not teach the model the rejected value or an anecdote about the error.
