# Form Protocol Catalog

Milestone: 1E - Form protocol catalog design

## Executive Summary

JarvisOS form protocols are bounded proposal contracts for local models and
deterministic helpers.

Core rule:

```text
local models fill bounded forms only; JarvisOS owns validation, retry, policy, persistence, promotion, execution, retrieval gates, provider/tool gates, audit, and final decisions
```

Valid form structure does not prove semantic truth. A form can be schema-valid
and still be wrong, stale, unsafe, overconfident, under-sourced, or out of
scope. Forms separate what a model may propose from what JarvisOS may later
save, review, retrieve, promote, execute, or send to a provider.

This catalog is documentation-only. It defines conceptual form families for
future design and testing. It does not create Pydantic models, JSON schemas,
runtime validators, retry loops, routes, APIs, scorer code, harnesses, model
calls, memory runtime, retrieval runtime, Context Pack Broker runtime, provider
calls, tool execution, or BlueRev modeling.

## Scope And Non-Goals

This catalog defines:

- shared form principles;
- a shared metadata envelope concept;
- conceptual form families;
- authority boundaries for each form;
- failure categories for future validators and smoke tests;
- relationships to the holdout intake generalization set and future milestones.

This catalog does not define implementation files, database tables, routes,
runtime schemas, runtime models, harnesses, scorers, prompts, generators, or
model adapters.

Non-goals:

- no backend code;
- no frontend code;
- no routes or APIs;
- no database migration;
- no SQLAlchemy or Pydantic runtime models;
- no repository or storage classes;
- no runtime validator;
- no retry-loop implementation;
- no model calls;
- no Gemma, Ollama, Qwen, or external provider calls;
- no retrieval runtime;
- no memory runtime;
- no Context Pack Broker runtime;
- no compression runtime;
- no provider/tool execution;
- no hooks;
- no MCP;
- no worker or viewer;
- no BlueRev modeling;
- no external reference audit;
- no vendored code;
- no start of `1F - Structural validator + retry loop design`.

## Shared Form Principles

### Bounded Fields

Forms should use bounded fields with explicit shapes. Long free prose should be
limited to rationale, short summaries, or clarification text. Fields that
affect policy, scope, storage, retrieval, provider use, tool use, sensitivity,
or promotion must be closed enums, booleans, stable IDs, bounded lists, or
source references where possible.

### Enums Over Free Prose

Closed enums are preferred for:

- project bucket;
- domain bucket;
- lifecycle status;
- source-class policy;
- retrieval behavior;
- sensitivity;
- allowed effect;
- review reason;
- tool intent;
- provider intent;
- confidence band;
- uncertainty reason.

Enums make structural validation possible. They do not make semantic output
correct.

### `not_decided` When Evidence Is Insufficient

Models must use `not_decided` when source evidence, scope, or user choice is
insufficient. This is especially important for BlueRev assumptions, material
choices, geometry, process parameters, provider/tool permissions, memory
promotion, and final sensitivity.

`not_decided` is not a failure when evidence is genuinely insufficient. It is a
required safe output.

### Source IDs And Provenance

When a claim matters, the form should carry source IDs, source references, or
provenance. Missing source references should limit the form to advisory or
proposed status.

Claims that can affect decisions, accepted memory, canonical state, provider
use, tool use, final sensitivity, retrieval gates, or BlueRev assumptions
require source-grounded review before later use.

### Model Output Is Advisory Only

Models may propose:

- labels;
- context requests;
- retrieval intents;
- memory-card candidates;
- source-card candidates;
- decision-card candidates;
- assumption-card candidates;
- evidence-card candidates;
- clarification questions;
- sensitivity assessments;
- provider/tool intents;
- review requests.

Models may not authorize:

- memory writes;
- memory promotion;
- canonical state changes;
- retrieval access;
- full-body evidence retrieval;
- provider calls;
- tool calls;
- route selection;
- final sensitivity;
- safety decisions;
- execution;
- BlueRev assumptions.

### Structural Validation Is Not Semantic Truth

JarvisOS validates structure:

- schema version;
- required fields;
- enum values;
- booleans;
- field lengths;
- max counts;
- source ID shape;
- scope shape;
- allowed effects;
- confidence bounds;
- obvious secret/path hard overrides.

JarvisOS does not prove semantic truth through validation. It does not prove
source interpretation, summary quality, memory completeness, strategic
correctness, final sensitivity, or BlueRev technical validity.

## Shared Metadata Envelope Concept

Every future form should be wrapped in a small metadata envelope. This is a
conceptual contract only, not a runtime schema.

Required conceptual fields:

- `schema_version`: names the conceptual form version.
- `form_id`: stable ID for the form instance.
- `filled_by`: `deterministic_rule|local_model|jarvisos|user|system|unknown`.
- `model_proposed`: boolean that stays true when a model supplied semantic
  content.
- `source_refs`: bounded list of source IDs or source references.
- `scope`: workspace, project, and milestone scope.
- `confidence`: numeric or bounded confidence band when useful.
- `uncertain_fields`: bounded list of field names.
- `allowed_effect`: the only effect the form may request.
- `requires_review`: boolean review gate.

Conceptual envelope:

```json
{
  "schema_version": "form_protocol_v0",
  "form_id": "string",
  "filled_by": "deterministic_rule|local_model|jarvisos|user|system|unknown",
  "model_proposed": true,
  "source_refs": [],
  "scope": {
    "workspace_id": "string|null",
    "project_id": "jarvisos|bluerev|coursework|personal|general|unknown",
    "milestone_id": "string|null"
  },
  "confidence": {
    "value": 0.0,
    "meaning": "diagnostic_only"
  },
  "uncertain_fields": [],
  "allowed_effect": "proposal_only",
  "requires_review": true
}
```

Rules:

- `allowed_effect` must be narrow.
- `confidence` is diagnostic, not authority.
- `uncertain_fields` must not be copied into canonical memory as raw model
  prose.
- Missing scope blocks authority and may require clarification.
- Source references are required before a form can support decisions.

## Catalog Of Conceptual Forms

### `ClassificationForm`

Purpose:

- Produce non-critical semantic hints such as task, project, topic, context
  need, and confidence.

Filled by:

- deterministic fallback;
- local model in future bounded diagnostics;
- JarvisOS-owned routing helper after policy allows.

Required fields:

- `task_hint`;
- `project_hint`;
- `topic_hint`;
- `context_need_hint`;
- `confidence`;
- `uncertain_fields`;
- metadata envelope.

Allowed effect:

- advisory hint only.

JarvisOS-owned decisions:

- final task routing;
- final project scope;
- retrieval authorization;
- provider/tool authorization;
- safety and sensitivity policy.

Forbidden effects:

- route selection;
- provider/tool execution;
- memory write;
- retrieval access;
- safety decision;
- final sensitivity;
- BlueRev modeling.

Validation notes:

- closed enums;
- confidence bounds;
- max uncertain fields;
- hard overrides for obvious secrets and disallowed actions;
- no raw prompts or model output in reports unless separately approved.

Future test coverage:

- holdout cases with JarvisOS, BlueRev, coursework, personal, and unknown
  project buckets;
- failure classes: `wrong_project_bucket`, `wrong_domain_bucket`,
  `missed_not_decided`, `cross_project_leakage`.

### `FastIntakeSignalForm`

Purpose:

- Preserve cheap write-time signals for possible memory without creating
  canonical truth.

Filled by:

- deterministic extraction;
- local model as advisory helper;
- hybrid deterministic-first process.

Required fields:

- source/input ID;
- raw-text-preserved indicator;
- observable flags;
- broad storage buckets;
- explicit mentions;
- surface summary;
- uncertainty;
- confidence;
- lifecycle status from canonical terms.

Allowed effect:

- staged `raw_input` or `fast_intake` signal proposal only.

JarvisOS-owned decisions:

- source metadata;
- raw/original retention;
- persistence;
- sensitivity hard overrides;
- lifecycle transition;
- memory promotion.

Forbidden effects:

- accepted memory;
- canonical state;
- retrieval authorization;
- provider/tool authorization;
- BlueRev assumption acceptance.

Validation notes:

- use canonical lifecycle values:
  `raw_input`, `fast_intake`, `proposed_memory`, `enriched_memory`,
  `accepted_memory`, `canonical_state`, `superseded`, `unknown`;
- validate booleans and enums;
- enforce max field lengths;
- reject obvious secrets or forbidden paths from normal memory flow.

Future test coverage:

- holdout cases HG-001 through HG-032 cover staged intake, low-value messages,
  secrets, forbidden paths, user preferences, and BlueRev `not_decided`
  behavior;
- failure classes: `wrong_lifecycle_status`, `wrong_storage_relevance`,
  `secret_not_blocked`, `unauthorized_memory_promotion`.

### `ContextAccessRequest`

Purpose:

- Ask for bounded context packages, source files, or source IDs when current
  orientation is insufficient.

Filled by:

- local model;
- JarvisOS;
- user or system request translation.

Required fields:

- requested context type;
- source IDs or allowed package IDs when known;
- reason;
- scope;
- max source count;
- whether full evidence is required;
- `not_decided` fallback.

Allowed effect:

- request bounded context assembly or candidate discovery after JarvisOS policy
  checks.

JarvisOS-owned decisions:

- whether context is allowed;
- source selection;
- redaction;
- full-body retrieval;
- context package assembly;
- audit.

Forbidden effects:

- arbitrary file/database browsing;
- global recent context injection;
- direct retrieval by model;
- provider/tool calls.

Validation notes:

- scope is required;
- unknown scope triggers clarification;
- source IDs must be from an allowed vocabulary or known source catalog later;
- max counts prevent unbounded context.

Future test coverage:

- HG-010, HG-012, HG-013, HG-025 test ambiguous scope and previous-context
  references;
- failure classes: `retrieval_bypass_attempt`, `cross_project_leakage`,
  `missed_clarification`.

### `RetrievalIntentForm`

Purpose:

- Propose a progressive retrieval request without querying storage directly.

Filled by:

- local model;
- JarvisOS;
- user request interpreter.

Required fields:

- retrieval purpose;
- requester actor type;
- downstream consumer;
- scope;
- allowed source classes;
- review-only source classes;
- max candidates;
- whether full body may be requested by ID later.

Allowed effect:

- candidate discovery proposal only.

JarvisOS-owned decisions:

- scope and sensitivity gate;
- candidate discovery;
- full-body-by-ID approval;
- source-class policy;
- downstream provider/tool redaction gates;
- audit.

Forbidden effects:

- direct storage query;
- full-body retrieval without ID and policy;
- model-controlled browsing;
- memory promotion;
- provider/tool authorization.

Validation notes:

- align with `retrieval_request_v0` in
  `docs/PROGRESSIVE_RETRIEVAL_CONTRACT_DESIGN.md`;
- `external_provider` and `tool` are not direct requester actor types;
- review-only source classes require purpose, scope, sensitivity, and audit.

Future test coverage:

- HG-004, HG-011, HG-012, HG-021, HG-023 cover full-body and review gates;
- HG-018 and HG-019 cover provider/tool direct-query blocks;
- failure classes: `missed_full_body_requirement`,
  `provider_tool_direct_request_allowed`, `raw_or_proposed_as_normal_context`.

### `MemoryCardProposal`

Purpose:

- Propose a durable memory candidate for later review, enrichment, or
  promotion.

Filled by:

- local model during future enrichment;
- deterministic helper for simple mechanical candidates;
- user explicit memory request translator.

Required fields:

- memory kind;
- short statement;
- source refs;
- scope;
- lifecycle status;
- sensitivity;
- confidence;
- review requirement;
- `not_decided` where applicable.

Allowed effect:

- `proposed_memory` only.

JarvisOS-owned decisions:

- persistence through MemoryStore;
- deduplication;
- sensitivity hard overrides;
- enrichment;
- acceptance;
- canonical promotion.

Forbidden effects:

- direct durable write bypassing MemoryStore;
- accepted memory;
- canonical state;
- BlueRev assumption acceptance.

Validation notes:

- source refs required for important claims;
- user "remember this" requests still start as proposed unless policy says
  otherwise later;
- model confidence cannot promote memory.

Future test coverage:

- HG-003, HG-015, HG-020, HG-027, HG-030 cover preferences and explicit memory
  requests;
- failure class: `memory_promotion_attempt`.

### `SourceCardProposal`

Purpose:

- Propose metadata for a source, artifact, paper, commit, report, or document.

Filled by:

- local model;
- JarvisOS source importer later;
- deterministic source scanner later.

Required fields:

- source ref;
- source type;
- title or short label;
- provenance;
- scope;
- freshness;
- sensitivity;
- interpretation status.

Allowed effect:

- source metadata proposal only.

JarvisOS-owned decisions:

- source validity;
- source fetch;
- full-body access;
- sensitivity;
- whether source supports a decision.

Forbidden effects:

- invented citation;
- accepted source interpretation;
- provider/tool call;
- canonical decision.

Validation notes:

- URLs, DOIs, file paths, commit hashes, and artifact IDs must preserve exact
  spelling;
- source-card proposal does not prove paper contents or file contents.

Future test coverage:

- HG-021 and HG-023 cover DOI/source-card and canonical document reference
  behavior;
- failure class: `invented_source_or_fact`.

### `DecisionCardProposal`

Purpose:

- Propose, summarize, or classify a decision without making it accepted.

Filled by:

- local model;
- user request translator;
- future review workflow.

Required fields:

- decision statement;
- decision status;
- source refs;
- scope;
- affected milestones or docs;
- rationale;
- review requirement.

Allowed effect:

- proposed decision record only.

JarvisOS-owned decisions:

- accepted decision status;
- ADR creation;
- canonical doc changes;
- promotion to canonical state;
- supersession.

Forbidden effects:

- creating accepted ADRs automatically;
- changing roadmap state;
- changing runtime policy;
- BlueRev decision acceptance.

Validation notes:

- status must distinguish proposed, accepted, superseded, and `not_decided`
  where applicable;
- decision summaries need full source evidence for important changes.

Future test coverage:

- HG-001, HG-002, HG-004, HG-024, HG-029 cover JarvisOS decision boundaries;
- failure classes: `unauthorized_memory_promotion`,
  `semantically_wrong_but_structurally_valid`.

### `AssumptionCardProposal`

Purpose:

- Propose a tentative assumption for later source-grounded review.

Filled by:

- local model;
- user input translator;
- future modeling/workbench flow.

Required fields:

- assumption statement;
- project scope;
- domain;
- source refs;
- status;
- `not_decided` flag;
- sensitivity;
- review reason.

Allowed effect:

- proposed assumption only.

JarvisOS-owned decisions:

- assumption acceptance;
- source-grounded review;
- conflict handling;
- BlueRev model use;
- canonical promotion.

Forbidden effects:

- accepted BlueRev material, geometry, process, or parameter decision;
- model-driven design choice;
- canonical state.

Validation notes:

- BlueRev assumptions default to review-required;
- missing source refs force `not_decided`;
- numbers, units, materials, and process terms must be preserved exactly.

Future test coverage:

- HG-006, HG-009, HG-022, HG-028, HG-031, HG-032 cover tentative BlueRev
  assumptions and contradictions;
- failure class: `unauthorized_bluerev_assumption`.

### `EvidenceCardProposal`

Purpose:

- Propose evidence relevant to a claim, decision, conflict, or review.

Filled by:

- local model;
- JarvisOS retrieval or source-grounding workflow later;
- user request translator.

Required fields:

- evidence statement;
- source refs;
- source class;
- full-body requirement;
- scope;
- freshness;
- contradiction/gap markers;
- sensitivity.

Allowed effect:

- evidence candidate only.

JarvisOS-owned decisions:

- whether evidence is valid;
- whether full body is fetched;
- whether evidence supports a decision;
- conflict resolution.

Forbidden effects:

- treating snippets as truth;
- treating FTS as full evidence;
- provider/tool authorization;
- memory promotion.

Validation notes:

- full body is required when evidence affects decisions;
- stale/superseded markers must be preserved;
- source metadata must travel with evidence.

Future test coverage:

- HG-004, HG-011, HG-021, HG-023, HG-024 cover full-body evidence,
  source-grounding, and stale/superseded behavior;
- failure classes: `missed_full_body_requirement`,
  `invented_source_or_fact`.

### `ClarificationRequest`

Purpose:

- Ask a bounded, high-value question when scope, source, user intent, or
  decision state is insufficient.

Filled by:

- local model;
- JarvisOS;
- future review workflow.

Required fields:

- question;
- reason enum;
- affected fields;
- scope;
- blocking status;
- suggested choices when safe;
- source refs if available.

Allowed effect:

- ask user or reviewer a bounded clarification.

JarvisOS-owned decisions:

- whether to ask;
- whether to proceed with `not_decided`;
- whether clarification result becomes memory or canonical state later.

Forbidden effects:

- filling missing choices with guesses;
- asking broad unnecessary questions;
- selecting BlueRev assumptions.

Validation notes:

- question length bounded;
- reason enum required;
- missing scope or ambiguous previous context should trigger clarification.

Future test coverage:

- HG-009, HG-010, HG-013, HG-025, HG-028 cover clarification behavior;
- failure class: `missed_clarification`.

### `SensitivityAssessment`

Purpose:

- Propose semantic sensitivity classification for later policy handling.

Filled by:

- local model;
- deterministic rules for obvious hard overrides;
- future stronger reviewer.

Required fields:

- sensitivity bucket;
- rationale;
- hard-override indicators;
- source refs;
- scope;
- uncertainty;
- recommended handling.

Allowed effect:

- advisory sensitivity proposal only.

JarvisOS-owned decisions:

- final sensitivity;
- secret refusal;
- redaction;
- provider eligibility;
- tool eligibility;
- storage eligibility.

Forbidden effects:

- sensitivity downgrade;
- external provider permission;
- raw secret storage;
- public treatment of private BlueRev data.

Validation notes:

- obvious API keys, passwords, tokens, `.env` content, private keys, and
  forbidden paths are deterministic hard blocks;
- semantic sensitivity is not proven by model output.

Future test coverage:

- HG-008, HG-016, HG-017, HG-018, HG-031 cover sensitive and secret cases;
- failure classes: `secret_not_blocked`, `wrong_sensitivity_bucket`.

### `ToolIntentProposal`

Purpose:

- Propose a tool action intent without executing anything.

Filled by:

- local model;
- user action parser later.

Required fields:

- tool intent type;
- target ID or source ref;
- risk;
- scope;
- confirmation requirement;
- rationale.

Allowed effect:

- proposal for JarvisOS policy review only.

JarvisOS-owned decisions:

- allowed tool catalog;
- target validation;
- risk handling;
- confirmation;
- execution construction;
- audit.

Forbidden effects:

- arbitrary command generation;
- direct shell execution;
- direct filesystem or database access;
- memory promotion.

Validation notes:

- tool names must come from a future allowed catalog;
- model text must never become a shell command;
- provider/tool forms are separate from execution.

Future test coverage:

- HG-019 covers model tool execution and raw memory querying blocks;
- failure class: `unsafe_provider/tool_intent`.

### `ProviderIntentProposal`

Purpose:

- Propose a need for external or stronger model review without calling a
  provider.

Filled by:

- local model;
- JarvisOS policy planner later;
- user request parser.

Required fields:

- provider intent type;
- proposed tier;
- sensitivity bucket;
- redaction requirement;
- budget requirement;
- scope;
- source refs;
- rationale.

Allowed effect:

- provider review proposal only.

JarvisOS-owned decisions:

- provider eligibility;
- credentials;
- budget;
- redaction;
- prompt packaging;
- routing;
- final call decision;
- audit.

Forbidden effects:

- direct provider call;
- memory dump;
- provider as retrieval requester;
- final routing decision.

Validation notes:

- external providers cannot query memory or retrieval directly;
- downstream provider use requires separate gates;
- sensitive or unknown scope fails closed.

Future test coverage:

- HG-018 covers broad memory-folder-to-provider blocking;
- failure class: `provider_tool_direct_request_allowed`.

### `ReviewRequest`

Purpose:

- Request stronger review when a form is uncertain, high-impact, sensitive,
  contradictory, or under-sourced.

Filled by:

- local model;
- JarvisOS;
- user or reviewer.

Required fields:

- review type;
- target form/source/ref;
- reason enum;
- scope;
- sensitivity;
- urgency;
- allowed reviewer class.

Allowed effect:

- queue or request review later, after a review system exists.

JarvisOS-owned decisions:

- whether review is required;
- who or what reviews;
- whether review output can affect memory, retrieval, provider use, tool use,
  or canonical state;
- audit.

Forbidden effects:

- treating review request as review result;
- calling 31B/API reviewer automatically;
- accepting BlueRev assumptions.

Validation notes:

- review request is a control signal, not evidence;
- high-impact and sensitive requests remain blocked until review completes.

Future test coverage:

- HG-005, HG-012, HG-022, HG-028, HG-031 cover failure reports, review-only
  retrieval, toy modeling, contradiction, and private data;
- failure classes: `missed_review_gate`,
  `semantically_wrong_but_structurally_valid`.

## Authority Matrix

| Area | Model may propose | JarvisOS owns | Requires review | Forbidden |
| --- | --- | --- | --- | --- |
| Classification | Low-stakes labels and confidence. | Final policy, routing, safety. | Low confidence or high impact. | Safety-critical action from label. |
| Intake | Observable hints and broad buckets. | Source metadata, persistence, lifecycle. | Important or sensitive memory. | Accepted/canonical memory. |
| Context access | Bounded request and rationale. | Source selection, redaction, package assembly. | Ambiguous scope or sensitive source. | Arbitrary browsing. |
| Retrieval | Intent and source-class request. | Candidate discovery, full-body gate, audit. | Raw/proposed/superseded classes. | Direct storage query. |
| Memory cards | Proposed memory. | MemoryStore write boundary, promotion. | Durable or high-impact memory. | Direct durable write. |
| Source/evidence | Candidate source/evidence. | Full-body fetch, provenance, source validity. | Decisions or conflicts. | Snippet as truth. |
| Decisions | Proposed decision summary. | ADR/canonical decision status. | Any durable decision. | Auto-accepted decision. |
| Assumptions | Tentative assumption. | Acceptance and BlueRev use. | BlueRev and engineering assumptions. | Model-accepted assumption. |
| Clarification | Bounded question. | Whether to ask or stop. | Blocking ambiguity. | Guessing missing choice. |
| Sensitivity | Advisory assessment. | Final sensitivity and redaction. | Unknown/subtle sensitivity. | Downgrade or external permission. |
| Tool intent | Intent only. | Tool catalog, execution construction, audit. | Risky or mutating action. | Arbitrary command execution. |
| Provider intent | Need for stronger provider. | Budget, redaction, routing, call. | External/sensitive use. | Direct provider call. |
| Review | Review request. | Review routing and result handling. | High-impact uncertainty. | Review request as approval. |

## Failure Taxonomy

`schema_invalid`:

- Output cannot be parsed or violates required structure.

`semantically_wrong_but_structurally_valid`:

- Form validates structurally but assigns the wrong project, domain, source,
  action, or meaning.

`invented_source`:

- Source ID, DOI, file, commit, or evidence is fabricated or not grounded.

`missing_not_decided`:

- Model selects a value when evidence, user choice, or scope is insufficient.

`unsafe_provider_tool_intent`:

- Model proposes provider/tool use that bypasses policy, redaction, budget,
  confirmation, or target validation.

`memory_promotion_attempt`:

- Model attempts accepted memory, canonical state, or MemoryStore bypass.

`retrieval_bypass_attempt`:

- Model tries to query storage, fetch raw/proposed records, or browse full
  bodies without scoped gates.

`bluerev_assumption_acceptance_attempt`:

- Model accepts BlueRev material, geometry, process, metric, or modeling
  assumption without source-grounded review and explicit policy.

These failures map to the 1D-G holdout taxonomy, including
`wrong_project_bucket`, `wrong_domain_bucket`, `wrong_storage_relevance`,
`wrong_lifecycle_status`, `wrong_sensitivity_bucket`, `missed_review_gate`,
`missed_full_body_requirement`, `unsafe_default_source_class`,
`raw_or_proposed_as_normal_context`, `secret_not_blocked`,
`provider_tool_direct_request_allowed`, `cross_project_leakage`,
`missed_not_decided`, `missed_clarification`, `invented_source_or_fact`,
`unauthorized_memory_promotion`, `unauthorized_bluerev_assumption`, and
`runtime_action_proposed`.

## Relationship To Future Milestones

### `1F - Structural validator + retry loop design`

1F should design how JarvisOS validates form structure, reports machine-readable
errors, and decides when retry is safe.

1F should not treat structural validity as semantic truth. It should keep
model output advisory and preserve JarvisOS authority over policy, persistence,
promotion, retrieval, providers, tools, audit, and final decisions.

This 1E catalog gives 1F the conceptual form families and common envelope. It
does not implement validators or retry logic.

### `1G - Gemma form-fill smoke test harness`

1G may later design a smoke harness that asks a local model to fill bounded
forms and compares selected fields against the holdout set.

1G must remain separate from this milestone. The 1D-G holdout set exists as
stable input data, but this catalog does not call Gemma, Ollama, Qwen, or any
model and does not create a scorer or harness.

## Milestone Boundary Confirmation

1E is a docs-only design milestone.

It adds no:

- backend code;
- frontend code;
- routes or APIs;
- database migration;
- SQLAlchemy or Pydantic runtime models;
- repository or storage classes;
- runtime schemas;
- validators;
- retry loops;
- scorer;
- harness;
- tests;
- JSON data files;
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

This milestone does not start `1F - Structural validator + retry loop design`.
