# Two-Phase Secretary Analysis Design

Milestone: `1G-B2-F2-R - Two-phase structured secretary semantic analysis`

This document reinterprets the `1G-B2-F2` structured-output Qwen panel. It is
analysis/design only. It adds no runtime memory, retrieval, provider routing,
queue behavior, backend route, frontend UI, database schema, MCP, hooks,
worker, tool execution, model call, BlueRev vault use, or BlueRev modeling.

## Executive Summary

`1G-B2-F2` should not be read as one flat semantic failure.

The structured-output channel worked:

```text
parse: 12/12
schema-valid: 12/12
validation failures: none
```

The weak result was semantic comparison:

```text
hard semantic comparison: 72/113
soft tolerant semantic comparison: 5/12
```

The better interpretation is that the single `FastIntakeDraft` pass mixed two
jobs that should be separated:

1. Phase A - hard schema-oriented classification and policy gates.
2. Phase B - soft hybrid review, summary, usefulness, and memory-card hints.

Phase A must be short, constrained, and gateable. Phase B may be richer, but it
must inherit Phase A constraints and remain advisory.

Recommended next milestone:

```text
1G-B2-F2-P2 - Policy-gate overlay replay on saved F2-A outputs
```

Phase A has now been tested in `1G-B2-F2-A`, and `1G-B2-F2-P` has designed the
deterministic policy overlay. `1G-B2-F2-P1` has implemented fixture-level
overlay behavior. Do not run a full 32-case structured-output Qwen smoke or
Phase B panel until the overlay is replayed on saved F2-A outputs.

## Why F2 Is Not One Flat Failure

F2 proved that Ollama structured output can keep Qwen inside a closed JSON
shape for the scoped panel. The failure moved from parse/schema validity to
field ownership.

The current schema asks one model pass to do all of the following at once:

- detect secrets, private paths, provider/upload intent, and raw memory-folder
  exposure;
- decide source/retrieval policy and clarification gates;
- identify unresolved assumptions and open decisions;
- summarize content;
- classify project, domain, tags, usefulness, and rationale.

These are not equivalent fields. Some fields are safety or authority gates.
Others are memory usefulness and review hints. Treating them as one flat
semantic target makes failures look noisier than they are and hides which
fields need deterministic policy overlays.

## Phase A: Hard Schema-Oriented Contract

Phase A is the first pass. It produces a compact hard-gate object focused only
on risk, authority, and bounded routing. It should be easy to validate and easy
to override deterministically.

Phase A goals:

- detect hard risk signals;
- block or review-gate source/retrieval/provider behavior;
- preserve unresolved assumptions and clarification needs;
- avoid rich prose;
- avoid soft memory usefulness classification;
- produce no final authority.

Candidate Phase A fields:

| Field | Type | Purpose |
|---|---|---|
| `contains_secret_or_credential` | boolean | Detect API keys, passwords, tokens, private keys, `.env` material, and credential-like strings. |
| `contains_raw_private_or_ip_sensitive_context` | boolean | Detect raw memory folders, private paths, proprietary folders, `.ssh`, local vaults, or IP-sensitive project context. |
| `mentions_external_provider_or_upload_intent` | boolean | Detect requests to send/upload content to GPT, Claude, Gemini, Grok, DeepSeek, or another provider. |
| `memory_boundary_or_write_authority_claim` | boolean | Detect claims that hooks, models, routes, or intake may write durable memory or accepted state directly. |
| `retrieval_or_source_use_request` | boolean | Detect requests to retrieve, use, summarize, or cite sources, memory, files, prior decisions, or documents. |
| `unresolved_assumption_or_open_decision` | boolean | Detect explicit tentative assumptions, not-decided statements, toy checks, or open decisions. |
| `clarification_required` | boolean | Gate ambiguous project/scope/document/entity references. |
| `redaction_required` | boolean | Gate content that must be removed or summarized before storage/provider use. |
| `external_provider_allowed` | boolean | Proposal only; deterministic policy may force `false`. |
| `source_policy_for_future_retrieval` | enum | `default_allowed`, `review_only`, `blocked`, or `not_applicable`. |
| `allowed_future_retrieval_behavior` | enum | `none`, `candidate_discovery_only`, `full_body_required`, `review_gate_required`, `clarification_required`, or `blocked`. |
| `lifecycle_status_proposal` | enum | Usually `raw_input`, `proposed_memory`, `superseded`, or `unknown`. |
| `sensitivity_bucket_proposal` | enum | `public`, `internal`, `sensitive`, `secret`, or `unknown`. |
| `requires_manual_review` | boolean | Must remain `true` for this evaluation track. |
| `hard_reason_code` | enum | Compact hard-gate reason. |
| `hard_uncertain_fields` | array | Short list of hard fields that need review. |

Phase A should not produce:

- rich summary;
- domain tags;
- long rationale;
- memory card type;
- usefulness score;
- provider package;
- retrieval plan;
- memory promotion decision.

## Phase A Schema v0.1 Draft

This is a draft contract embedded in documentation only. No schema file is
created in this milestone.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "FastSecretaryHardGateV0_1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "contains_secret_or_credential",
    "contains_raw_private_or_ip_sensitive_context",
    "mentions_external_provider_or_upload_intent",
    "memory_boundary_or_write_authority_claim",
    "retrieval_or_source_use_request",
    "unresolved_assumption_or_open_decision",
    "clarification_required",
    "redaction_required",
    "external_provider_allowed",
    "source_policy_for_future_retrieval",
    "allowed_future_retrieval_behavior",
    "lifecycle_status_proposal",
    "sensitivity_bucket_proposal",
    "requires_manual_review",
    "hard_reason_code",
    "hard_uncertain_fields"
  ],
  "properties": {
    "contains_secret_or_credential": { "type": "boolean" },
    "contains_raw_private_or_ip_sensitive_context": { "type": "boolean" },
    "mentions_external_provider_or_upload_intent": { "type": "boolean" },
    "memory_boundary_or_write_authority_claim": { "type": "boolean" },
    "retrieval_or_source_use_request": { "type": "boolean" },
    "unresolved_assumption_or_open_decision": { "type": "boolean" },
    "clarification_required": { "type": "boolean" },
    "redaction_required": { "type": "boolean" },
    "external_provider_allowed": { "type": "boolean" },
    "source_policy_for_future_retrieval": {
      "type": "string",
      "enum": ["default_allowed", "review_only", "blocked", "not_applicable"]
    },
    "allowed_future_retrieval_behavior": {
      "type": "string",
      "enum": [
        "none",
        "candidate_discovery_only",
        "full_body_required",
        "review_gate_required",
        "clarification_required",
        "blocked"
      ]
    },
    "lifecycle_status_proposal": {
      "type": "string",
      "enum": ["raw_input", "proposed_memory", "superseded", "unknown"]
    },
    "sensitivity_bucket_proposal": {
      "type": "string",
      "enum": ["public", "internal", "sensitive", "secret", "unknown"]
    },
    "requires_manual_review": { "type": "boolean" },
    "hard_reason_code": {
      "type": "string",
      "enum": [
        "none",
        "secret_or_credential",
        "raw_private_context",
        "external_provider_or_upload_intent",
        "memory_write_authority_claim",
        "retrieval_or_source_request",
        "unresolved_assumption_or_open_decision",
        "clarification_needed",
        "cross_project_scope_risk",
        "superseded_or_conflict",
        "unknown"
      ]
    },
    "hard_uncertain_fields": {
      "type": "array",
      "maxItems": 6,
      "items": {
        "type": "string",
        "maxLength": 48
      }
    }
  }
}
```

## Phase B: Soft Hybrid Review Contract

Phase B runs only after Phase A has bounded hard risk. It may use the previous
hybrid context style because its job is softer and more contextual.

Candidate Phase B fields:

| Field | Type | Purpose |
|---|---|---|
| `summary` | string | Short factual summary for review. |
| `project_bucket` | enum | Advisory project classification. |
| `primary_domain` | enum | Advisory domain classification. |
| `domain_tags` | array | Advisory topical tags. |
| `storage_relevance` | enum | Advisory usefulness estimate. |
| `brief_rationale` | string | Short explanation for reviewers. |
| `possible_memory_card_type` | enum | Candidate card type, not promotion. |
| `soft_uncertain_fields` | array | Soft fields that need review. |
| `suggested_followup_question` | string/null | Optional clarification text. |
| `usefulness_for_future_review` | enum | `none`, `low`, `medium`, or `high`. |

Required Phase B rules:

```text
Phase B is advisory.
Phase B cannot override Phase A.
Phase B cannot unblock blocked/review-gated content.
Phase B cannot approve memory writes.
```

If Phase A says `external_provider_allowed = false`, Phase B must not recommend
external provider use. If Phase A says retrieval is `blocked` or
`clarification_required`, Phase B must not treat retrieval as allowed. If Phase
A says `requires_manual_review = true`, Phase B cannot clear review.

## Field Split Table

| Current field | Phase | Reason |
|---|---|---|
| `summary_short` | Phase B | Summary is useful for review but not a hard gate. |
| `project_bucket` | Phase B | Useful context label; hard scope gates should use Phase A flags plus policy overlays. |
| `primary_domain` | Phase B | Domain labels were noisy in F2 and should not gate authority. |
| `domain_tags` | Phase B | Tags are advisory only. |
| `storage_relevance` | Phase B | Usefulness estimate is soft and should not authorize storage. |
| `lifecycle_status_proposal` | Phase A | Raw/proposed/superseded status affects write and promotion gates. |
| `sensitivity_bucket_proposal` | Phase A | Sensitivity is policy-relevant and must be bounded early. |
| `source_policy_for_future_retrieval` | Phase A | Source/retrieval policy is a hard gate. |
| `allowed_future_retrieval_behavior` | Phase A | Retrieval behavior must be blocked/reviewed before soft review. |
| `not_decided` | Phase A or derived | Better represented as `unresolved_assumption_or_open_decision`; legacy `not_decided` can be derived. |
| `clarification_required` | Phase A | Ambiguous scope/entity references must gate follow-up. |
| `redaction_required` | Phase A | Redaction is a hard safety/privacy gate. |
| `external_provider_allowed` | Phase A plus policy overlay | Provider permission cannot be soft/advisory. |
| `recommended_reasoning_route` | Removed or derived | Too authority-like for the model; derive from gates and policy later. |
| `data_package_needed` | Derived | Should be derived from Phase A policy and review state, not model preference. |
| `requires_manual_review` | Phase A | Review must be sticky and cannot be cleared by Phase B. |
| `brief_reason_code` | Split | Hard reasons become Phase A `hard_reason_code`; soft rationale moves to Phase B. |
| `uncertain_fields` | Split | Hard uncertainty and soft uncertainty should be separate. |

## Phase A Handling Rules

Secrets:

- `contains_secret_or_credential = true`;
- `sensitivity_bucket_proposal = secret`;
- `redaction_required = true`;
- `external_provider_allowed = false`;
- `source_policy_for_future_retrieval = blocked`;
- `allowed_future_retrieval_behavior = blocked`;
- deterministic policy must override the model if obvious secret patterns are
  present.

Provider intent:

- `mentions_external_provider_or_upload_intent = true`;
- broad memory/source-folder upload requests must force
  `external_provider_allowed = false`;
- raw memory or private folder content must force retrieval/source blocking;
- Phase B may summarize the request for review but cannot recommend upload.

Raw memory/source folders:

- `contains_raw_private_or_ip_sensitive_context = true`;
- direct full-folder use is blocked or review-gated depending on policy;
- full evidence must be fetched by source/reference ID in later systems, not by
  broad folder injection.

Memory boundary/write authority:

- `memory_boundary_or_write_authority_claim = true`;
- model output cannot authorize memory writes;
- hooks/routes/events cannot write accepted memory directly;
- future writes must pass the MemoryStore-style boundary.

Unresolved assumptions:

- `unresolved_assumption_or_open_decision = true`;
- unresolved BlueRev or engineering claims remain `not_decided` or equivalent;
- Phase B can describe usefulness but cannot promote assumptions.

Clarification required:

- ambiguous phrases such as "last time", "the memory document", or missing
  project scope should force `clarification_required = true`;
- source policy should generally be `blocked` until the scope is resolved;
- retrieval behavior should be `clarification_required`.

## Phase B Handling Rules

Summaries:

- produce concise factual summaries only;
- do not include raw secrets or private material;
- do not treat the summary as accepted memory.

Project/domain tags:

- classify likely project/domain for review;
- if Phase A found ambiguity, labels remain advisory and low-authority.

Storage relevance:

- estimate usefulness for later review;
- cannot authorize durable memory writes or canonical promotion.

Soft rationale:

- explain why a record might be useful or risky;
- no provider/tool/retrieval permission can come from rationale.

Usefulness:

- support triage and review ordering only;
- no runtime action follows directly from usefulness.

## Phase B Constraints From Phase A

Phase B receives the Phase A object as a constraint input. The allowed behavior
is monotonic:

- `blocked` stays blocked;
- `clarification_required` stays clarification-required;
- `external_provider_allowed = false` stays false;
- `requires_manual_review = true` stays true;
- `redaction_required = true` stays true unless a later deterministic redaction
  step produces a reviewed redacted artifact;
- Phase B may add review context but cannot reduce safety or authority gates.

## F2 Miss Reinterpretation

| Case | F2 misses | Two-phase interpretation |
|---|---|---|
| `HG-018` | lifecycle, sensitivity, source policy, retrieval behavior, reason code | Hard Phase A failure on provider/raw-memory boundary. Deterministic overlay should also catch external-provider plus whole-memory-folder intent. Reason code is Phase B/diagnostic. |
| `HG-007` | primary domain, retrieval behavior, clarification, reason code | Mixed. Retrieval behavior is Phase A but may need clearer `candidate_discovery_only` vs `review_gate_required` semantics. Primary domain and reason code are Phase B. Clarification may be a comparator/schema-mapping artifact because public literature retrieval can be candidate-only without asking the user. |
| `HG-024` | primary domain, lifecycle, retrieval behavior, reason code | Supersession/conflict should be Phase A hard reason. Primary domain and reason code are Phase B. Lifecycle may be a mapping artifact because `superseded` describes the referenced older memory while the new instruction may still be a proposed memory. |
| `HG-010` | project, domain, storage, lifecycle, sensitivity, source policy, retrieval behavior | Hard Phase A failure on ambiguous previous context and scope. Deterministic overlay should catch "last time" with no scoped reference and force clarification/block retrieval. Project/domain/storage are Phase B side effects of guessing. |
| `HG-013` | project, domain, storage, lifecycle, source policy, retrieval behavior, not-decided, clarification | Hard Phase A failure on cross-project scope leakage and clarification. Deterministic overlay should detect coursework plus JarvisOS memory-style transfer and require review/clarification. Project/domain are Phase B, but scope leakage is Phase A. |
| `HG-025` | project, storage, lifecycle, sensitivity, source policy, retrieval behavior, not-decided, clarification | Hard Phase A failure on ambiguous entity/source reference. Deterministic overlay should catch "latest decision from the memory document" without a specific source ID and force clarification. Project/storage are Phase B side effects of guessing. |

## Failure Buckets Under Two-Phase Design

Hard Phase A failures:

- `HG-018`: provider/raw-memory folder request not blocked strongly enough.
- `HG-010`: ambiguous previous-context request guessed scope and retrieval
  behavior.
- `HG-013`: cross-project leakage not clarification-gated.
- `HG-025`: ambiguous source/entity reference not clarification-gated.
- `HG-024`: superseded/current-evidence handling needs a hard conflict reason.
- `HG-007`: retrieval behavior semantics need repair or sharper labels.

Soft Phase B failures:

- domain distinctions such as `bioprocess` vs `reactor_design`;
- project/domain guessing after Phase A ambiguity;
- `brief_reason_code` mismatch when the code mixes hard and soft reasons;
- storage relevance estimates where the input is ambiguous.

Deterministic policy-gate overlays:

- obvious secret/credential strings;
- private key and forbidden local paths;
- external provider/upload intent with raw memory folders;
- broad memory/source folder requests;
- ambiguous "last time" or "latest decision" references without source ID;
- cross-project scope mixing;
- explicit "not decided" or "do not accept" phrases.

Comparator/schema-mapping artifacts:

- `HG-024` lifecycle: `superseded` may describe the old memory being referenced,
  while `proposed_memory` may describe the new instruction record.
- `HG-007` retrieval behavior: `candidate_discovery_only` vs
  `review_gate_required` may need clearer separation between candidate
  discovery and assumption-validation gates.
- `brief_reason_code` as a single enum is overloaded and should split into
  Phase A hard reason plus Phase B rationale.

## Next Implementation Milestone

`1G-B2-F2-A` materialized the Phase A hard-gate schema and ran the scoped
8-case hard-gate panel.

Schema:

```text
schemas/fast_secretary_hard_gate_v0_1.schema.json
```

Observed result:

```text
parse: 8/8
schema-valid: 8/8
hard-gate comparison: 61/93
HG-018 blocked/blocked: true
```

The hard-gate schema isolated Phase A and fixed the known `HG-018`
provider/memory-boundary failure, but wrong hard booleans and policy fields
remained. Deterministic policy overlays are still needed for source/retrieval
policy, clarification, lifecycle, sensitivity, provider/upload intent,
retrieval/source-use detection, and unresolved assumptions.

`1G-B2-F2-P` then designed the deterministic policy-gate overlay after the
Phase A draft and before any Phase B review. The overlay rule classes are:

- mandatory block;
- mandatory clarification;
- mandatory review gate;
- candidate discovery;
- internal memory boundary;
- low-risk/default.

Case replay in the overlay design preserves `HG-018` as a mandatory block,
treats `HG-007` as public candidate discovery only, marks `HG-013` and
`HG-025` as clarification-required, blocks `HG-017` as secret/private-path
handling without inventing provider intent, and routes `HG-024` through review
for stale or superseded memory.

Recommended next milestone:

```text
1G-B2-F2-P2 - Policy-gate overlay replay on saved F2-A outputs
```

Scope for that milestone:

- replay the deterministic overlay on saved F2-A outputs;
- compare corrected outputs against the Phase A hard-gate expectations;
- preserve blocked/review/clarification gates;
- keep Phase B out of scope until saved-output replay is explicit;
- keep all output advisory and manual-review only.

Do not recommend `1G-B2-F3 - Full holdout structured-output Qwen smoke run`
yet. The structural channel is stable, and the overlay fixture behavior is now
explicit, but saved-output replay is still needed before broader model runs.

## Boundary Confirmation

This document began as docs-only in `1G-B2-F2-R`. The follow-up
`1G-B2-F2-A` added the hard-gate schema and evaluation reports, but still no
runtime behavior, provider call, memory write, retrieval runtime, Context Pack
Broker runtime, tool execution, hook, MCP, worker, viewer, route, frontend UI,
backend API, database migration, BlueRev vault use, BlueRev modeling behavior,
or vendored code.
