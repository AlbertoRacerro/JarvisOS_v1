# Structural Validator Retry Loop Design

Milestone: 1F - Structural validator + retry loop design

## Executive Summary

JarvisOS structural validation checks whether a model-filled form obeys the
expected shape and authority limits. It does not prove that the model is
semantically right.

Core principle:

```text
structural validation enforces form shape and authority boundaries; it does not prove semantic truth
```

The future retry loop is bounded and machine-readable. It may ask a model to
repair narrow structural errors, but retry failure must end in review,
clarification, `not_decided`, or block. The retry loop must never expand into
unbounded conversation, hidden retrieval, provider calls, tool execution,
memory promotion, or BlueRev modeling.

This milestone is documentation-only. It does not add validator runtime,
Pydantic models, JSON schemas, scorer code, harnesses, tests, routes, APIs,
model calls, memory runtime, retrieval runtime, Context Pack Broker runtime,
provider calls, tool execution, or BlueRev modeling.

## Scope And Non-Goals

This document designs:

- what future structural validators should check;
- what validators must not claim to decide;
- bounded retry-loop shape;
- final submission outcomes;
- machine-readable error categories;
- conceptual validation and retry contracts;
- relationships to the form protocol catalog, holdout set, progressive
  retrieval contract, and future smoke harness.

This document does not implement:

- backend code;
- frontend code;
- routes or APIs;
- database migrations;
- SQLAlchemy models;
- Pydantic runtime models;
- JSON schemas;
- repository or storage classes;
- runtime validator functions;
- retry-loop code;
- scorers;
- harnesses;
- tests;
- model calls;
- Gemma, Ollama, Qwen, or external provider calls;
- retrieval runtime;
- memory runtime;
- Context Pack Broker runtime;
- compression runtime;
- provider/tool execution;
- hooks;
- MCP;
- worker or viewer;
- BlueRev modeling;
- external reference audit;
- vendored code;
- start of `1G - Gemma form-fill smoke test harness`.

## Validation Principle

### Structure Is Validated

JarvisOS may validate that a form:

- names an expected schema version;
- includes required fields;
- uses valid enum values;
- uses booleans where booleans are required;
- stays within field length limits;
- stays within confidence bounds;
- carries source references when required;
- carries workspace, project, and milestone scope;
- requests only allowed effects;
- marks review-required paths;
- preserves model authority restrictions;
- avoids forbidden provider/tool/retrieval/memory-promotion effects.

### Semantics Are Not Proven

Structural validation does not prove:

- semantic fidelity;
- factual truth;
- source interpretation;
- strategic correctness;
- final sensitivity correctness;
- memory completeness;
- retrieval sufficiency;
- BlueRev material, geometry, process, parameter, or modeling validity.

A structurally valid form can still be wrong. It can still require review,
clarification, full evidence, source-grounding, or `not_decided`.

### JarvisOS Owns Policy And Authority

Models propose form content. JarvisOS owns:

- validation;
- retry decisions;
- policy;
- persistence;
- promotion;
- retrieval gates;
- provider/tool gates;
- execution;
- audit;
- final decisions.

No validated form can authorize runtime action by itself.

## Validator Responsibilities

Future structural validators should check:

- schema version;
- form family and form ID;
- required fields;
- enum values;
- boolean fields;
- numeric bounds;
- field lengths;
- list lengths;
- confidence bounds;
- source refs;
- source-ref shape;
- scope fields;
- workspace/project/milestone shape;
- allowed effect;
- review requirements;
- model authority restrictions;
- lifecycle/status values;
- source-class policy values;
- retrieval behavior values;
- sensitivity bucket values;
- forbidden provider/tool effects;
- forbidden retrieval bypass effects;
- forbidden memory-promotion effects;
- forbidden BlueRev assumption acceptance effects;
- obvious secret or forbidden path hard overrides.

Structural validators may also classify validation errors into stable
machine-readable categories. They must not silently repair semantic content.

## Non-Validator Responsibilities

Structural validators do not decide:

- technical truth;
- factual source interpretation;
- final sensitivity;
- memory promotion;
- accepted memory;
- canonical state;
- BlueRev assumption acceptance;
- provider execution;
- tool execution;
- route selection;
- retrieval permission;
- full-body evidence access;
- source-grounded decision validity;
- model runtime approval.

Those decisions require JarvisOS policy, source-grounded review, user
confirmation, future promotion logic, or separate execution gates.

## Bounded Retry Loop

The future retry loop is narrow and finite.

Conceptual flow:

```text
first model form output
-> structural validation
-> machine-readable error report
-> retry with narrow correction request
-> structural validation
-> max attempt limit
-> final outcome
```

### First Model Form Output

The first output is parsed as a candidate form. If it is not parseable or has
the wrong root type, the validator emits a structural error and may allow one
bounded repair attempt later.

### Structural Validation

Validation checks shape, enums, bounds, required fields, scope, source refs,
allowed effects, and forbidden authority claims.

It does not score semantic quality.

### Machine-Readable Error Report

Errors must be concise and machine-readable. They should identify:

- field path;
- error category;
- expected value or enum;
- received value summary;
- whether retry is allowed;
- whether the error is safety-critical;
- required safe fallback when retry is not allowed.

The error report must not include raw secrets, raw prompts, raw model output, or
large source text.

### Retry With Narrow Correction Request

Retry requests should ask only for structural repair. They should not add new
context, broaden the task, invite reasoning from memory, or ask the model to
decide policy.

Allowed retry instruction pattern:

```text
Repair only these fields to match the schema and allowed enums. Do not add new
claims. If evidence is insufficient, use not_decided.
```

Disallowed retry behavior:

- unbounded chat;
- arbitrary new retrieval;
- provider escalation;
- tool execution;
- prompt expansion with sensitive raw content;
- memory promotion;
- BlueRev decision acceptance.

### Max Attempt Limit

Retries must have a small fixed maximum. Future implementation should choose a
default such as one initial attempt plus one or two structural repair attempts,
then fail closed.

Repeated invalid output is evidence about model/protocol reliability, not a
reason to silently loosen policy.

### Final Outcome

Every submission ends in one final outcome:

- `accepted_structurally`;
- `accepted_with_review_required`;
- `clarification_required`;
- `not_decided`;
- `blocked`;
- `schema_failed`.

## Final Outcomes

### `accepted_structurally`

The form is structurally valid and requests only an allowed low-authority
effect. This does not mean the form is semantically true.

Allowed next step later:

- pass to JarvisOS policy or downstream review path.

Forbidden interpretation:

- accepted memory, canonical state, provider/tool permission, final
  sensitivity, or BlueRev assumption.

### `accepted_with_review_required`

The form is structurally valid, but the requested content is high-impact,
sensitive, review-only, under-sourced, contradictory, or otherwise gated.

Allowed next step later:

- queue or require review when a review workflow exists.

### `clarification_required`

The form cannot be safely resolved because scope, source target, user intent, or
decision state is ambiguous.

Allowed next step later:

- ask a bounded clarification.

### `not_decided`

The safe result is to preserve uncertainty because evidence is insufficient.

Allowed next step later:

- stop, report `not_decided`, or request source-grounded context.

### `blocked`

The form contains a hard policy violation such as secret handling, forbidden
path access, provider/tool bypass, retrieval bypass, memory-promotion attempt,
or BlueRev assumption acceptance.

Allowed next step later:

- block and audit.

### `schema_failed`

The form could not be repaired within the bounded retry limit.

Allowed next step later:

- fail closed, report validation failure, and collect structural diagnostics.

## Machine-Readable Error Categories

Future validators should use stable error categories such as:

- `missing_required_field`;
- `invalid_enum`;
- `invalid_lifecycle_status`;
- `invalid_source_class_policy`;
- `invalid_retrieval_behavior`;
- `forbidden_authority_claim`;
- `missing_source_reference`;
- `missing_scope`;
- `confidence_out_of_range`;
- `field_too_long`;
- `unsafe_provider_tool_intent`;
- `attempted_memory_promotion`;
- `attempted_bluerev_assumption_acceptance`.

Additional likely categories:

- `invalid_boolean`;
- `invalid_number`;
- `list_too_long`;
- `unexpected_field`;
- `invalid_schema_version`;
- `invalid_allowed_effect`;
- `review_required_missing`;
- `secret_or_forbidden_path`;
- `retrieval_bypass_attempt`;
- `full_body_required_missing`;
- `not_decided_required`.

Error category meanings:

| Category | Meaning | Retry allowed |
| --- | --- | --- |
| `missing_required_field` | Required field absent. | yes, if not safety-critical |
| `invalid_enum` | Value outside allowed enum. | yes |
| `invalid_lifecycle_status` | Lifecycle value outside canonical set. | yes |
| `invalid_source_class_policy` | Source policy is not allowed. | yes |
| `invalid_retrieval_behavior` | Retrieval behavior is not allowed. | yes |
| `forbidden_authority_claim` | Form claims authority it cannot have. | no or review |
| `missing_source_reference` | Important claim lacks source ref. | maybe; otherwise review/not_decided |
| `missing_scope` | Workspace/project/milestone scope is missing. | maybe; otherwise clarification |
| `confidence_out_of_range` | Confidence outside numeric bounds. | yes |
| `field_too_long` | Field exceeds length cap. | yes |
| `unsafe_provider_tool_intent` | Provider/tool use bypasses policy. | no |
| `attempted_memory_promotion` | Model tries accepted/canonical memory. | no |
| `attempted_bluerev_assumption_acceptance` | Model accepts BlueRev assumption. | no |

## Conceptual Contracts Only

These contracts are documentation-only. They are not Pydantic models, JSON
schemas, API schemas, routes, services, migrations, validators, tests, runtime
files, or implementation code.

### `validation_result_v0`

```json
{
  "schema_version": "validation_result_v0",
  "validation_id": "string",
  "form_id": "string|null",
  "form_family": "string",
  "valid_structure": false,
  "semantic_truth_proven": false,
  "errors": [
    {
      "path": "string",
      "category": "missing_required_field|invalid_enum|invalid_lifecycle_status|invalid_source_class_policy|invalid_retrieval_behavior|forbidden_authority_claim|missing_source_reference|missing_scope|confidence_out_of_range|field_too_long|unsafe_provider_tool_intent|attempted_memory_promotion|attempted_bluerev_assumption_acceptance",
      "expected": "string|null",
      "received_summary": "string|null",
      "retry_allowed": true,
      "safety_critical": false
    }
  ],
  "requires_review": false,
  "requires_clarification": false,
  "requires_not_decided": false,
  "blocked": false,
  "allowed_effect": "proposal_only|candidate_discovery_only|evidence_fetch_only|none",
  "model_authority": "none"
}
```

### `retry_instruction_v0`

```json
{
  "schema_version": "retry_instruction_v0",
  "retry_id": "string",
  "form_id": "string|null",
  "attempt_number": 1,
  "max_attempts": 2,
  "retry_scope": "structural_repair_only",
  "allowed_corrections": [
    "missing_required_field",
    "invalid_enum",
    "field_too_long"
  ],
  "forbidden_corrections": [
    "new_claims",
    "new_sources",
    "provider_calls",
    "tool_calls",
    "memory_promotion",
    "bluerev_assumption_acceptance"
  ],
  "instruction": "Repair only the listed structural fields. Do not add new claims. Use not_decided if evidence is insufficient."
}
```

### `form_submission_outcome_v0`

```json
{
  "schema_version": "form_submission_outcome_v0",
  "submission_id": "string",
  "form_id": "string|null",
  "attempts": 1,
  "final_outcome": "accepted_structurally|accepted_with_review_required|clarification_required|not_decided|blocked|schema_failed",
  "valid_structure": false,
  "semantic_truth_proven": false,
  "requires_review": false,
  "requires_clarification": false,
  "blocked_reason": "string|null",
  "next_safe_action": "none|review|ask_clarification|return_not_decided|block|record_diagnostic",
  "model_authority": "none"
}
```

## Relationship To Form Protocol Catalog

The form protocol catalog defines conceptual form families and shared metadata.
This document defines how those future forms should be structurally validated
and how bounded repair attempts should behave.

The validator design inherits these catalog rules:

- local models fill bounded forms only;
- model output is advisory;
- JarvisOS owns policy and final decisions;
- valid structure does not prove semantic truth;
- `not_decided` is required when evidence is insufficient;
- source refs and scope are required when claims matter.

## Relationship To Holdout Intake Set

The 1D-G holdout set provides stable docs/data-only cases for future testing.
It is not a scorer or harness.

Future validators and smoke tests may use holdout expectations to check:

- canonical lifecycle values;
- source-class policy values;
- retrieval behavior values;
- `not_decided` behavior;
- review-gate behavior;
- full-body-required behavior;
- secret/path blocking;
- provider/tool direct-query blocking;
- cross-project leakage;
- BlueRev assumption boundaries.

This milestone does not run the holdout set through any model.

## Relationship To Progressive Retrieval Contract

Structural validation should enforce the shape and authority limits of future
retrieval-related forms.

Validators can check:

- `expected_source_class_policy` enum shape;
- `expected_retrieval_behavior` enum shape;
- missing scope;
- missing source refs;
- full-body-required markers;
- review-only source-class gates;
- provider/tool as invalid direct requesters.

Validators cannot decide:

- whether a snippet is true;
- whether full evidence proves a claim;
- whether retrieval should promote memory;
- whether a provider/tool may use retrieved context.

## Relationship To Future Gemma Form-Fill Smoke Harness

`1G - Gemma form-fill smoke test harness` may later test whether a model can
fill forms and whether validator/retry behavior produces useful diagnostics.

This 1F design does not create that harness. It does not call Gemma, Ollama,
Qwen, or any model. It defines only the conceptual validation and retry
contracts the future harness may exercise.

## Failure Taxonomy

`schema_invalid`:

- Form cannot be parsed or required structure is absent.

`structurally_valid_semantically_wrong`:

- Form passes shape checks but assigns wrong meaning, source, project, or
  decision state.

`retry_overfit`:

- Retry fixes syntax while preserving or adding a wrong semantic claim.

`unbounded_retry_loop`:

- Repeated retries become hidden chat or policy negotiation.

`error_report_leaks_sensitive_text`:

- Validation diagnostics include raw secrets, prompt text, tool output, or
  sensitive source bodies.

`missing_not_decided`:

- Model chooses a value when scope or evidence is insufficient.

`review_required_but_accepted`:

- Structurally valid form bypasses review gates.

`unsafe_provider_tool_intent`:

- Form proposes provider/tool use as if valid structure were permission.

`retrieval_bypass_attempt`:

- Form attempts arbitrary storage or full-body retrieval.

`memory_promotion_attempt`:

- Form attempts accepted memory or canonical state.

`bluerev_assumption_acceptance_attempt`:

- Form accepts a BlueRev technical assumption from model output.

`validator_claims_semantic_truth`:

- Validator result is misread as proof of factual correctness.

## Future Implementation Acceptance Criteria

Future implementation may proceed only when:

- validators are form-family specific;
- schema versions are explicit;
- required fields and enum values are checked;
- field lengths and list lengths are bounded;
- confidence bounds are checked;
- source refs and scope fields are validated;
- allowed effects are narrow;
- review-required paths are preserved;
- model authority is always `none` for runtime decisions;
- forbidden provider/tool/retrieval/memory-promotion effects are blocked;
- BlueRev assumption acceptance attempts are blocked or forced to review;
- retry instructions are machine-readable and structural only;
- max attempts are fixed and small;
- final outcomes are explicit;
- failed retries end in review, clarification, `not_decided`, block, or
  `schema_failed`;
- diagnostics avoid raw secrets, raw prompts, raw model output, and large source
  bodies;
- tests cover malformed forms, invalid enums, missing source refs, missing
  scope, review gates, blocked effects, and `not_decided` requirements.

## Milestone Boundary Confirmation

1F is a docs-only design milestone.

It adds no:

- backend code;
- frontend code;
- routes or APIs;
- database migration;
- SQLAlchemy or Pydantic runtime models;
- JSON schemas;
- repository or storage classes;
- validator runtime;
- retry-loop runtime;
- scorer;
- harness;
- tests;
- model calls;
- Gemma or Ollama calls;
- provider calls;
- retrieval runtime;
- memory runtime;
- Context Pack Broker runtime;
- compression runtime;
- tool execution;
- hooks;
- MCP;
- worker or viewer;
- BlueRev modeling;
- external reference audit;
- vendored code.

This milestone does not start `1G - Gemma form-fill smoke test harness`.
