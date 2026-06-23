# Fast Secretary JSON Schema Design

Milestone: `1G-B2-F0 - Structured-output reference audit and schema-first redesign`

This document is design-only. It adds no runtime memory, retrieval, backend,
provider routing, queue behavior, database schema, tool execution, model call,
or BlueRev modeling.

## Executive Summary

The Qwen fast secretary should move from prompt-only JSON generation to a
schema-first `FastIntakeDraft` contract before any default-queue or runtime
approval.

1G-B2-E evidence showed:

```text
qwen_hybrid_parse_safe_v0_4
32 holdout cases
28/32 parse
169/256 hard
103/160 soft exact
104/160 soft tolerant
4 critical gates
```

Prompt wording improved the profile, but it did not eliminate structural
failures. The next experiment should use local Ollama structured output with an
explicit JSON Schema.

## Goals

- Make the output shape explicit and machine-checkable.
- Reduce malformed JSON and missing field failures.
- Keep policy-sensitive fields in enums and booleans.
- Separate schema-facing field names from canonical internal field names.
- Preserve manual review and JarvisOS authority.

## Non-Goals

- No runtime memory writes.
- No retrieval runtime.
- No provider routing runtime.
- No default queue approval.
- No backend route or frontend UI.
- No new model installation.
- No external provider calls.
- No new dependency.
- No full 32-case rerun in this design milestone.

## Target Contract

The structured-output object is named `FastIntakeDraft`.

It is a model proposal only. JarvisOS still owns:

- structural validation;
- deterministic policy overrides;
- scoring;
- retry decisions;
- persistence decisions;
- memory promotion;
- retrieval gates;
- provider/tool gates;
- audit and final decisions.

## Two-Layer Output

### Layer 1: Required Core

The first structured-output experiment should require a compact core object:

```json
{
  "summary_short": "string",
  "project_bucket": "enum",
  "primary_domain": "enum",
  "domain_tags": ["string"],
  "storage_relevance": "enum",
  "lifecycle_status_proposal": "enum",
  "sensitivity_bucket_proposal": "enum",
  "source_policy_for_future_retrieval": "enum",
  "allowed_future_retrieval_behavior": "enum",
  "not_decided": true,
  "clarification_required": false,
  "redaction_required": false,
  "external_provider_allowed": false,
  "recommended_reasoning_route": "enum",
  "data_package_needed": "enum",
  "requires_manual_review": true,
  "brief_reason_code": "enum",
  "uncertain_fields": ["string"]
}
```

### Layer 2: Deferred Review Details

Optional free-text fields should wait until the core schema is stable:

```json
{
  "brief_rationale": "string",
  "risk_notes": ["string"],
  "suggested_followup_question": "string"
}
```

Free-text fields are deferred because they increase malformed string risk and
can encourage model explanations rather than bounded form filling.

## Schema-Facing Field Names

Canonical internal names can remain stable while schema-facing names become more
instructional for the model.

| Internal field | Schema-facing field |
|---|---|
| `source_class_policy_proposal` | `source_policy_for_future_retrieval` |
| `retrieval_behavior_proposal` | `allowed_future_retrieval_behavior` |
| `reasoning_route_proposal` | `recommended_reasoning_route` |
| `api_or_model_escalation_recommended` | `external_provider_allowed` plus `recommended_reasoning_route` |
| `brief_rationale` | `brief_reason_code` and deferred optional rationale |

Schema-facing names are not storage names. A future implementation must map
them back into the canonical internal form before scoring or persistence.

## Canonical Mapping

| Schema field | Canonical internal target |
|---|---|
| `summary_short` | `summary` |
| `project_bucket` | `project_bucket` |
| `primary_domain` | `primary_domain` |
| `domain_tags` | `domain_tags` |
| `storage_relevance` | `storage_relevance` |
| `lifecycle_status_proposal` | `lifecycle_status_proposal` |
| `sensitivity_bucket_proposal` | `sensitivity_bucket_proposal` |
| `source_policy_for_future_retrieval` | `source_class_policy_proposal` |
| `allowed_future_retrieval_behavior` | `retrieval_behavior_proposal` |
| `not_decided` | `not_decided` |
| `clarification_required` | `clarification_required` |
| `redaction_required` | `redaction_required` |
| `external_provider_allowed` | derived provider gate input |
| `recommended_reasoning_route` | `reasoning_route_proposal` |
| `data_package_needed` | `data_package_needed` |
| `requires_manual_review` | review/audit metadata |
| `brief_reason_code` | compact rationale category |
| `uncertain_fields` | `uncertain_fields` |

## JSON Schema v0.1

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "FastIntakeDraftV0_1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "summary_short",
    "project_bucket",
    "primary_domain",
    "domain_tags",
    "storage_relevance",
    "lifecycle_status_proposal",
    "sensitivity_bucket_proposal",
    "source_policy_for_future_retrieval",
    "allowed_future_retrieval_behavior",
    "not_decided",
    "clarification_required",
    "redaction_required",
    "external_provider_allowed",
    "recommended_reasoning_route",
    "data_package_needed",
    "requires_manual_review",
    "brief_reason_code",
    "uncertain_fields"
  ],
  "properties": {
    "summary_short": {
      "type": "string",
      "maxLength": 180,
      "description": "Short factual summary. No reasoning. Max 25 words."
    },
    "project_bucket": {
      "type": "string",
      "enum": ["jarvisos", "bluerev", "coursework", "personal", "general", "unknown"]
    },
    "primary_domain": {
      "type": "string",
      "enum": ["memory", "software", "retrieval", "local_ai", "modeling", "bioprocess", "reactor_design", "coursework", "personal", "security", "general", "unknown"]
    },
    "domain_tags": {
      "type": "array",
      "minItems": 0,
      "maxItems": 6,
      "items": {
        "type": "string",
        "maxLength": 32
      }
    },
    "storage_relevance": {
      "type": "string",
      "enum": ["none", "low", "medium", "high"]
    },
    "lifecycle_status_proposal": {
      "type": "string",
      "enum": ["raw_input", "fast_intake", "proposed_memory", "enriched_memory", "accepted_memory", "canonical_state", "superseded", "unknown"]
    },
    "sensitivity_bucket_proposal": {
      "type": "string",
      "enum": ["public", "internal", "sensitive", "secret", "unknown"]
    },
    "source_policy_for_future_retrieval": {
      "type": "string",
      "enum": ["default_allowed", "review_only", "blocked", "not_applicable"]
    },
    "allowed_future_retrieval_behavior": {
      "type": "string",
      "enum": ["none", "candidate_discovery_only", "full_body_required", "review_gate_required", "clarification_required", "blocked"]
    },
    "not_decided": {
      "type": "boolean"
    },
    "clarification_required": {
      "type": "boolean"
    },
    "redaction_required": {
      "type": "boolean"
    },
    "external_provider_allowed": {
      "type": "boolean"
    },
    "recommended_reasoning_route": {
      "type": "string",
      "enum": ["none", "local_fast_model", "local_senior_model", "external_provider", "human_review"]
    },
    "data_package_needed": {
      "type": "string",
      "enum": ["none", "draft_only", "draft_batch_summary", "redacted_summary", "full_context", "raw_input"]
    },
    "requires_manual_review": {
      "type": "boolean"
    },
    "brief_reason_code": {
      "type": "string",
      "enum": [
        "memory_boundary",
        "retrieval_boundary",
        "unresolved_bluerev_assumption",
        "secret_or_credential",
        "provider_routing_risk",
        "clarification_needed",
        "full_body_needed",
        "contradiction_or_superseded",
        "low_value",
        "general_useful_note",
        "unknown"
      ]
    },
    "uncertain_fields": {
      "type": "array",
      "maxItems": 8,
      "items": {
        "type": "string",
        "maxLength": 48
      }
    }
  }
}
```

## Experiment Plan

### Experiment A: Difficult Cases

Use only the most informative difficult cases from 1G-B2-E:

```text
HG-007, HG-017, HG-018, HG-024, HG-010, HG-013, HG-025, HG-015
```

Compare:

- existing CLI prompt-only result as historical baseline;
- local Ollama structured-output API with JSON Schema v0.1.

Maximum model calls for the first prototype:

```text
8 structured-output local calls
```

No full 32-case rerun in the prototype milestone.

### Experiment B: Small Risk Panel

Only if Experiment A is promising, run a 12-case panel:

- the four parse failures;
- top hard-risk cases;
- two regression cases such as `HG-001` and `HG-016`.

## Acceptance Criteria

The schema-first direction is promising if:

- schema-valid output is 8/8 on the difficult-case panel;
- critical gates are 0 or clearly reduced;
- no new severe secret/provider failures appear;
- hard score improves or remains comparable;
- every output validates strictly against JSON Schema before semantic scoring.

## Prototype Deferral

In `1G-B2-F0`, this milestone did not add
`scripts/local_model_structured_output_probe.py`.

Reason:

- F0 is the design and reference-audit milestone;
- the next milestone is already scoped as the Ollama structured-output schema
  smoke prototype;
- adding code here would blur the boundary between design and experiment.

The next milestone should implement the local-only stdlib Ollama API probe.

## F1 Prototype Result

`1G-B2-F1` implemented the local-only structured-output prototype:

- schema: `schemas/fast_secretary_intake_v0_1.schema.json`;
- probe: `scripts/local_model_structured_output_probe.py`;
- reports: `reports/local_model_smoke/1G-B2-F1/`.

The difficult-case panel used only `qwen3:8b`,
`qwen_hybrid_parse_safe_v0_4`, and:

```text
HG-007, HG-017, HG-018, HG-024, HG-010, HG-013, HG-025, HG-015
```

Observed result:

```text
parse: 8/8
schema-valid: 8/8
validation failures: none
enum/type validation failures: none
```

Interpretation:

- JSON Schema structured output repaired the structural parse/schema problem on
  this bounded difficult-case panel.
- The result does not prove semantic truth or runtime readiness.
- `HG-018` still showed a provider/memory-boundary semantic risk by returning
  `review_only` and `none` where the expected policy was `blocked` and
  `blocked`; `external_provider_allowed` remained `false`.
- The next milestone should run
  `1G-B2-F2 - Structured-output 12-case Qwen panel` to test whether the
  schema-first path generalizes beyond the eight-case smoke.
