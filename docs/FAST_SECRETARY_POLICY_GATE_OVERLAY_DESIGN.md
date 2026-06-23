# Fast Secretary Policy-Gate Overlay Design

Milestone: `1G-B2-F2-P - Fast secretary policy-gate overlay design`

This document designs the deterministic policy-gate overlay that sits after the
Phase A hard-gate LLM draft. It is design-only. It adds no runtime memory,
retrieval runtime, provider routing runtime, queue behavior, backend route,
frontend UI, database schema, Context Pack Broker runtime, worker, hook, MCP,
tool execution, model call, BlueRev vault use, BlueRev modeling behavior, or
vendored code.

## Purpose And Boundary

The overlay corrects or constrains the Phase A hard-gate draft before any Phase
B soft review can run.

It exists because `1G-B2-F2-A` showed:

```text
parse: 8/8
schema-valid: 8/8
hard-gate comparison: 61/93
HG-018 blocked/blocked: true
```

The Phase A schema fixed the output channel and repaired the severe
provider/raw-memory failure on `HG-018`, but remaining hard booleans and policy
fields still missed:

```text
wrong hard booleans:
- memory_boundary_or_write_authority_claim: 1
- mentions_external_provider_or_upload_intent: 1
- retrieval_or_source_use_request: 4
- unresolved_assumption_or_open_decision: 5

wrong policy fields:
- allowed_future_retrieval_behavior: 4
- clarification_required: 4
- lifecycle_status_proposal: 8
- sensitivity_bucket_proposal: 3
- source_policy_for_future_retrieval: 2
```

The correction is not to make Qwen block more aggressively. The overlay must
separate:

- mandatory hard blocks;
- mandatory review gates;
- clarification gates;
- public candidate discovery;
- internal memory-boundary handling;
- low-risk/default handling.

The overlay output is still not runtime authority. It is a corrected hard-gate
decision for manual review and later evaluation.

## Pipeline Position

Target pipeline:

```text
input/event
-> Phase A hard-gate LLM draft
-> deterministic policy-gate overlay
-> corrected hard-gate decision
-> Phase B soft hybrid review
-> manual review / memory proposal / no-write
```

Phase B cannot override the overlay. If the overlay blocks retrieval, provider
use, or memory write authority, Phase B can only add review context.

## Inputs

The overlay input is:

- raw input text or event text;
- optional case/project/source metadata when available;
- Phase A hard-gate draft matching
  `schemas/fast_secretary_hard_gate_v0_1.schema.json`;
- optional deterministic source facts such as file path, source ID, project
  scope, and sensitivity hints.

The overlay must not depend on:

- model rationale;
- Phase B output;
- global recent context;
- broad memory folder access;
- external provider judgement.

## Outputs

The overlay returns a corrected hard-gate decision using the Phase A field set:

- hard booleans;
- `clarification_required`;
- `redaction_required`;
- `external_provider_allowed`;
- `source_policy_for_future_retrieval`;
- `allowed_future_retrieval_behavior`;
- `lifecycle_status_proposal`;
- `sensitivity_bucket_proposal`;
- `requires_manual_review`;
- `hard_reason_code`;
- `hard_uncertain_fields`.

Additional audit metadata should be conceptual for now:

```json
{
  "overlay_applied": true,
  "overlay_rule_ids": ["string"],
  "overlay_changed_fields": ["string"],
  "overlay_precedence_winner": "mandatory_block|clarification|review_gate|candidate_discovery|memory_boundary|default",
  "manual_review_required": true
}
```

Do not create runtime schema or storage for this metadata in this milestone.

## Rule Classes

### 1. Mandatory Block Rules

Mandatory block rules force:

```text
external_provider_allowed = false
requires_manual_review = true
source_policy_for_future_retrieval = blocked
allowed_future_retrieval_behavior = blocked
```

They also force:

```text
redaction_required = true
sensitivity_bucket_proposal = secret
```

when secret-like content is present.

Triggers:

- API keys, tokens, passwords, private keys, `.env` material;
- `.ssh`, `id_rsa`, credential paths;
- request to upload/send a raw memory folder to an external provider;
- whole memory folder or raw private context to GPT, Claude, Gemini, Grok,
  DeepSeek, or another provider;
- explicit provider upload intent involving private or IP-sensitive content.

Mandatory block rules are narrow. They should not catch public literature
candidate discovery.

### 2. Mandatory Review-Gate Rules

Mandatory review-gate rules force:

```text
external_provider_allowed = false
requires_manual_review = true
source_policy_for_future_retrieval = review_only
allowed_future_retrieval_behavior = review_gate_required
```

Triggers:

- superseded or stale memory references;
- source exists but may be outdated;
- identifiable cross-project source use with internal context risk;
- internal project data that is not secret but is not public;
- current-evidence or conflict handling.

Review-gate rules preserve evidence for a human or later policy layer. They do
not authorize retrieval or memory promotion.

### 3. Mandatory Clarification Rules

Mandatory clarification rules force:

```text
clarification_required = true
requires_manual_review = true
source_policy_for_future_retrieval = blocked
allowed_future_retrieval_behavior = clarification_required
```

Triggers:

- "the thing we decided last time";
- "latest decision from memory document" without a file/source ID;
- ambiguous entity, source, project, or target policy;
- cross-project leakage where source and target project are unclear;
- previous-context references with no scope.

Clarification rules are different from mandatory blocks. They preserve the
possibility that the user can provide a specific source or scope later.

### 4. Candidate Discovery Rules

Candidate discovery rules allow:

```text
source_policy_for_future_retrieval = review_only
allowed_future_retrieval_behavior = candidate_discovery_only
external_provider_allowed = false
requires_manual_review = true
```

Triggers:

- requests to retrieve public literature or candidate sources;
- public DOI, paper, web, or literature discovery;
- source discovery with no raw private context and no provider upload request.

Candidate discovery does not allow full-body retrieval, source acceptance, or
assumption validation. It permits only candidate discovery for later review.

### 5. Internal Memory-Boundary Rules

Internal memory-boundary rules force:

```text
requires_manual_review = true
external_provider_allowed = false
```

They also prevent:

```text
lifecycle_status_proposal = accepted_memory
lifecycle_status_proposal = canonical_state
```

unless a later explicit promotion workflow exists.

Triggers:

- durable memory write authority;
- "put this in memory";
- MemoryStore/canonical-state claims;
- claims that hooks, models, routes, or intake can write accepted memory
  directly;
- "treat old memory as superseded".

These rules do not automatically block useful memory drafts. They keep write
authority outside the model.

### 6. Low-Risk Default Rules

Low-risk/default rules apply only if no higher-precedence rule fires.

Possible outputs:

```text
requires_manual_review = true
source_policy_for_future_retrieval = review_only|not_applicable
allowed_future_retrieval_behavior = none|review_gate_required
external_provider_allowed = false
```

Even low-risk records remain manual-review evidence in this evaluation track.

## Precedence Order

The overlay applies rules in this order:

1. Mandatory block.
2. Mandatory clarification.
3. Mandatory review gate.
4. Candidate discovery.
5. Internal memory boundary.
6. Low-risk/default.

If two rules conflict, the higher-precedence rule wins. However, mandatory
block rules must be precise: public literature candidate discovery must not be
blocked just because it mentions BlueRev or future modeling.

## Field-Level Override Table

| Field | Overlay authority | Notes |
|---|---|---|
| `contains_secret_or_credential` | Override true on secret patterns | API keys, passwords, tokens, private keys, `.env`, `.ssh/id_rsa`. |
| `contains_raw_private_or_ip_sensitive_context` | Override true on raw memory/private paths/IP-sensitive folders | Whole memory folder, local private path, vault, proprietary project folder. |
| `mentions_external_provider_or_upload_intent` | Override true only when provider/upload intent is explicit | Do not set true for a local secret path unless a provider is named. |
| `memory_boundary_or_write_authority_claim` | Override true for MemoryStore/write/canonical/hook authority claims | Does not approve writes. |
| `retrieval_or_source_use_request` | Override true for source, memory, previous-context, literature, file-use requests | Must not imply retrieval is allowed. |
| `unresolved_assumption_or_open_decision` | Override true for tentative or not-decided language | Includes "toy", "not a design decision", "not accepted", "might". |
| `clarification_required` | Override true for ambiguous scope/source/entity | Higher precedence than review/candidate discovery when source is unclear. |
| `redaction_required` | Override true for secrets/private key material | May remain false for review-only internal memory without raw secret. |
| `external_provider_allowed` | Usually force false | Future provider approval requires separate policy, redaction, and review. |
| `source_policy_for_future_retrieval` | Override by rule class | `blocked`, `review_only`, or `not_applicable`. |
| `allowed_future_retrieval_behavior` | Override by rule class | `blocked`, `clarification_required`, `review_gate_required`, `candidate_discovery_only`, or `none`. |
| `lifecycle_status_proposal` | Clamp unsafe values | Never accepted/canonical from model; use `raw_input`, `fast_intake`, `proposed_memory`, `superseded`, or `unknown`. |
| `sensitivity_bucket_proposal` | Override up on secret/private/internal signals | Do not downgrade internal/sensitive/secret based on model output. |
| `requires_manual_review` | Force true | Sticky in this track. |
| `hard_reason_code` | Override to highest-precedence rule reason | Records the dominant overlay reason. |
| `hard_uncertain_fields` | Append changed/ambiguous fields | Useful for later review and tests. |

## Case-Level Replay

### HG-018

Input type:

```text
provider intent + whole JarvisOS memory folder
```

F2-A result:

```text
blocked/blocked = true
```

Overlay behavior:

- preserve mandatory block;
- `contains_raw_private_or_ip_sensitive_context = true`;
- `mentions_external_provider_or_upload_intent = true`;
- `external_provider_allowed = false`;
- `source_policy_for_future_retrieval = blocked`;
- `allowed_future_retrieval_behavior = blocked`;
- `requires_manual_review = true`;
- `redaction_required` depends on whether raw secret/private content is present
  in the input payload; broad memory-folder upload remains blocked either way.

### HG-007

Input type:

```text
BlueRev public literature retrieval / candidate source discovery
```

F2-A problem:

```text
over-blocked public literature candidate discovery
```

Overlay behavior:

- not a mandatory block;
- `source_policy_for_future_retrieval = review_only`;
- `allowed_future_retrieval_behavior = candidate_discovery_only`;
- `sensitivity_bucket_proposal = internal`;
- `external_provider_allowed = false` by default;
- `requires_manual_review = true`;
- no full-body retrieval or assumption validation without review.

### HG-013

Input type:

```text
CPPOM handout asks to use latest JarvisOS memory decision style
```

F2-A problem:

```text
cross-project/ambiguous source request was blocked but not clarified correctly
```

Overlay behavior:

- mandatory clarification;
- `clarification_required = true`;
- `source_policy_for_future_retrieval = blocked`;
- `allowed_future_retrieval_behavior = clarification_required`;
- `sensitivity_bucket_proposal = internal`;
- `requires_manual_review = true`;
- user must identify the source decision and approve cross-project use.

### HG-017

Input type:

```text
.ssh/id_rsa local secret path
```

F2-A problem:

```text
correctly hard-blocked, but falsely marked provider/upload intent
```

Overlay behavior:

- mandatory block;
- `contains_secret_or_credential = true`;
- `contains_raw_private_or_ip_sensitive_context = true`;
- `mentions_external_provider_or_upload_intent = false` unless a provider is
  explicitly named;
- `redaction_required = true`;
- `external_provider_allowed = false`;
- `source_policy_for_future_retrieval = blocked`;
- `allowed_future_retrieval_behavior = blocked`;
- `requires_manual_review = true`.

### HG-024

Input type:

```text
stale/superseded memory about Gemma routing
```

F2-A problem:

```text
over-blocked a stale-memory review case
```

Overlay behavior:

- mandatory review gate;
- not a mandatory block;
- `source_policy_for_future_retrieval = review_only`;
- `allowed_future_retrieval_behavior = review_gate_required`;
- `sensitivity_bucket_proposal = internal`;
- `lifecycle_status_proposal = proposed_memory` or a superseded-related
  internal status, but not accepted/canonical;
- `requires_manual_review = true`.

### HG-025

Input type:

```text
"latest decision from memory document" ambiguous source
```

F2-A problem:

```text
source was blocked, but retrieval behavior should be clarification_required
```

Overlay behavior:

- mandatory clarification;
- `clarification_required = true`;
- `source_policy_for_future_retrieval = blocked`;
- `allowed_future_retrieval_behavior = clarification_required`;
- `requires_manual_review = true`;
- no broad memory retrieval until a source ID or document reference is supplied.

## What Remains Advisory From Qwen

The Phase A LLM draft remains useful as an advisory signal for:

- ambiguous cases not caught by deterministic rules;
- tentative classification of unresolved assumptions;
- preliminary sensitivity suggestion;
- suggested hard uncertainty fields;
- candidate hard reason when no overlay rule fires.

The draft cannot:

- unblock a mandatory block;
- clear `requires_manual_review`;
- permit external provider use;
- permit retrieval;
- approve memory writes;
- promote lifecycle to accepted/canonical;
- override deterministic sensitivity or source policy.

## What Remains Manual-Review

Manual review remains required for:

- all Phase A corrected decisions in this evaluation track;
- every source/retrieval candidate;
- every provider-related or upload-related request;
- every cross-project source-use request;
- every unresolved assumption;
- every superseded/conflict case;
- any policy overlay conflict or changed field.

## What Should Be Tested Next

Recommended next milestone:

```text
1G-B2-F2-P1 - Policy-gate overlay fixture prototype
```

Scope:

- implement a tiny pure-Python fixture prototype only;
- make zero model calls;
- run against fixed examples for `HG-018`, `HG-007`, `HG-013`, `HG-017`,
  `HG-024`, and `HG-025`;
- test precedence order;
- test block vs review vs clarification vs candidate discovery;
- prove the overlay does not over-block public literature discovery;
- prove private key paths do not create false provider intent.

Do not start Phase B soft hybrid review until overlay fixture behavior is
explicit and tested.

## Milestone Boundary Confirmation

This milestone is docs-only. It does not add overlay code, runtime memory,
retrieval runtime, provider routing runtime, queue behavior, backend route,
frontend UI, database schema, Context Pack Broker runtime, worker, hook, MCP,
tool execution, model call, BlueRev vault use, BlueRev modeling behavior, or
vendored code.
