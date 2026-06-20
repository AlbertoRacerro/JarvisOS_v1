# 0E-D6B Local Gatekeeper And Logical Gate Architecture

## D6C Correction Notice

0E-D6B correctly places a local gatekeeper before external provider tiers. 0E-D6C adds one earlier proof step: before implementing local gate contracts, JarvisOS must evaluate whether local Gemma can use context, memory, deterministic tools, and structured outputs reliably.

The D6B recommendation for a local gate and external tier contract skeleton is superseded by:

```text
0E-D7 - Local Gemma Evaluation Harness and Golden Set
```

## 1. Executive Judgement

0E-D6 was directionally right that JarvisOS should avoid provider-specific bots and should use logical routing concepts. It missed one critical ordering rule:

```text
Sensitivity classification must happen locally before any cloud provider is considered.
```

The first decision layer is therefore not `cheap`, `medium`, or `frontier`. The first layer is a **Local Gatekeeper**:

```text
User input
-> Local Gatekeeper
   -> deterministic hard rules
   -> optional local Gemma classifier
-> logical gate decision
-> only if allowed: external tier/provider adapter
-> structured response
-> event/audit
```

Updated recommendation after 0E-D6C:

```text
0E-D7 - Local Gemma Evaluation Harness and Golden Set
```

This supersedes the earlier D6 recommendation to add only `AIProviderTier` and the D6B recommendation to move directly into local gate contracts.

## 2. What D6 Got Right

D6 correctly concluded:

- users should interact with one stable Supervisor interface;
- users should not choose provider-specific bots;
- `provider_mode` is not a good future Supervisor routing abstraction;
- provider/model details should be internal or admin/config-only;
- events should eventually record logical routing decisions and concrete provider/model details;
- JarvisOS is not ready to add a medium provider yet.

Those conclusions still stand.

## 3. What D6 Missed

D6 treated external provider tiers as the next architectural layer after Supervisor request classification. That is incomplete because the classifier deciding whether raw user input is sensitive must inspect the raw input.

If that classifier runs on Scaleway, DeepSeek, Grok, Gemini, GPT, Claude, or any other cloud provider, JarvisOS has already sent the raw text externally before deciding whether external transmission is allowed. That defeats the privacy gate.

D6 also used `local_offline` as an optional tier, but local classification is not merely another tier. It is the required first gate before external tiers.

## 4. Why Local Gatekeeper Comes Before Provider Tiers

The Local Gatekeeper owns the first safety decision.

Responsibilities:

- inspect raw user input locally;
- apply deterministic hard rules;
- optionally ask a local model such as Gemma 12B/31B for classification assistance;
- classify sensitivity, complexity, and task type;
- decide whether external calls are allowed, blocked, local-only, or require confirmation;
- emit an audit event even when no external call happens.

Cloud providers may later answer allowed requests, review outputs, or perform reasoning. They must not be the first privacy classifier.

## 5. Why Scaleway Is Not The Privacy Classifier

Scaleway remains useful, but it should not anchor the architecture.

Scaleway can be:

- an optional external-call simulation provider;
- the legacy smoke provider;
- a possible EU provider or fallback;
- an adapter example.

Scaleway must not be:

- the privacy classifier;
- the local gatekeeper;
- the core router;
- a required future provider;
- the central architecture component just because the code already exists.

Avoid sunk-cost bias. Existing Scaleway code can remain for compatibility and smoke testing, but future architecture should be driven by local gate decisions and logical gates.

## 6. Corrected Architecture

Corrected target flow:

```text
User input
-> LocalGatekeeper
   -> HardRuleMatch[]
   -> optional local Gemma classifier
-> GateDecision
   -> selected_gate
   -> sensitivity
   -> complexity
   -> task_type
   -> confidence
   -> external_call_policy
   -> user_confirmation_requirement
-> if allowed and confirmed:
   -> ExternalTierAssignment
   -> ActualProvider adapter
   -> AIResponse
-> Event/audit
```

External tiers are still useful, but they sit after the local gate:

```text
CHEAP_GATE
CHEAP_PLUS_GATE
SCIENTIFIC_MEDIUM_GATE
FRONTIER_GATE
```

## 7. Logical Gate Model

Required gates:

```text
LOCAL_ONLY
LOCAL_GEMMA
USER_CONFIRM_REQUIRED
CHEAP_GATE
CHEAP_PLUS_GATE
SCIENTIFIC_MEDIUM_GATE
FRONTIER_GATE
BLOCKED
```

Meanings:

- `LOCAL_ONLY`: keep the work in deterministic local logic; do not call local LLM or external provider.
- `LOCAL_GEMMA`: use local Gemma if available; no external call.
- `USER_CONFIRM_REQUIRED`: do not call external providers until the user confirms after a clear warning.
- `CHEAP_GATE`: eligible for the cheap external tier.
- `CHEAP_PLUS_GATE`: eligible for a stronger cheap-plus/medium-light external tier.
- `SCIENTIFIC_MEDIUM_GATE`: eligible for a stronger scientific reasoning tier.
- `FRONTIER_GATE`: eligible for the highest reasoning tier after strict policy and cost gates.
- `BLOCKED`: do not process further except for safe local refusal/audit.

The gate is logical. It is not a provider brand.

## 8. Initial Provider Mapping

Initial conceptual mapping for discussion only:

```text
LOCAL_GEMMA:
  Gemma 12B / Gemma 31B local

CHEAP_GATE:
  DeepSeek

CHEAP_PLUS_GATE:
  Grok or equivalent

SCIENTIFIC_MEDIUM_GATE:
  Gemini Pro / Deep Think tier or equivalent

FRONTIER_GATE:
  GPT-5.5 or equivalent frontier provider
```

Contracts and events should use logical gates first. Provider mappings must remain config/admin/internal.

## 9. Deterministic Hard Rules

Hard rules always run before local model classification.

### Always `LOCAL_ONLY` or `BLOCKED`

Treat these as local-only or blocked depending on task and storage policy:

- API keys;
- passwords;
- tokens;
- private keys;
- `.env` content;
- Authorization headers;
- database credentials;
- SSH keys;
- proprietary experimental data;
- final BlueRev geometry;
- patent drafts before filing;
- trade-secret numbers;
- confidential contracts;
- anything explicitly marked `SECRET`;
- anything explicitly marked `CONFIDENTIAL`;
- anything explicitly marked `IP_SENSITIVE`;
- anything explicitly marked `LOCAL_ONLY`.

### `USER_CONFIRM_REQUIRED`

Require confirmation before any external call:

- preliminary BlueRev concepts;
- non-final geometry discussion;
- private project notes;
- business strategy;
- emails before sending;
- university, legal, or administrative documents;
- personal documents.

### External Allowed Candidates

Candidates for external gates after local review:

- public physics;
- public papers;
- public documentation;
- generic software engineering;
- generic Python, Excel, or LaTeX;
- public benchmark discussion;
- non-sensitive boilerplate;
- open-source code questions.

The hard-rule layer should be conservative. If it cannot decide safely, choose local-only, confirmation-required, or blocked.

## 10. Gemma Local Classifier Role

Gemma local is optional future assistance for classification, not an external provider and not a general chat surface.

Potential roles:

- classify sensitivity and complexity;
- identify task type;
- explain gate reasons in a short structured form;
- reduce false positives from hard rules;
- propose `SelectedGate` for local policy to accept or override.

Constraints:

- runs locally only;
- no external network;
- no hidden background execution;
- no memory or chat transcript;
- output is advisory to deterministic policy;
- hard rules override Gemma;
- low confidence should degrade to local-only, confirmation-required, or blocked.

## 11. Gatekeeper Output Schema

Proposed future schema:

```json
{
  "decision": "LOCAL_ONLY | LOCAL_GEMMA | EXTERNAL_ALLOWED | USER_CONFIRM_REQUIRED | BLOCKED",
  "selected_gate": "LOCAL_ONLY | LOCAL_GEMMA | CHEAP_GATE | CHEAP_PLUS_GATE | SCIENTIFIC_MEDIUM_GATE | FRONTIER_GATE | none",
  "sensitivity": "public | internal | semi_sensitive | ip_sensitive | secret",
  "complexity": "routine | moderate | high | frontier",
  "task_type": "classification | summarization | coding | debugging | scientific_reasoning | document_analysis | prompt_drafting | admin_bureaucracy | other",
  "confidence": 0.0,
  "reasons": [],
  "hard_rule_matches": [],
  "requires_user_confirmation": false,
  "allowed_external": false,
  "external_call_would_be_made": false,
  "external_call_attempted": false
}
```

Refined concept names for D7:

```text
LocalGatekeeper
HardRuleMatch
GateDecision
SelectedGate
SensitivityClass
ComplexityClass
TaskType
GateConfidence
ExternalCallPolicy
UserConfirmationRequirement
GateDryRun
ExternalTierAssignment
ActualProvider
SimulatedProviderCall
```

## 12. Gate Dry-Run Test Strategy

Phase 1 should be a dry-run only:

```text
User input
-> hard rules
-> optional local Gemma classifier
-> gate decision
-> event/audit
-> no external call
```

Testing strategy:

- build a golden local test set;
- include public allowed prompts;
- include internal but safe prompts;
- include secrets and credentials;
- include BlueRev preliminary/private/final examples using synthetic placeholders;
- include patent/legal/business/personal examples;
- include public scientific questions;
- include generic coding/debugging questions;
- assert no external calls are attempted;
- assert event payloads do not store raw sensitive text;
- assert hard-rule matches are recorded safely.

The first useful question is:

```text
Can hard rules plus local classification decide where the request should go?
```

not:

```text
Can Scaleway answer as if it were Gemini/GPT?
```

## 13. Scaleway Simulation Role

Phase 2 may use Scaleway only as external-call simulation after Phase 1 works.

Required event fields:

- `selected_gate`;
- `actual_provider = scaleway_test`;
- `simulated_external_call = true`;
- `provider_under_test = false`;
- `external_call_attempted`;
- `external_call_succeeded`;
- `gate_decision_id`;
- `request_id`;
- `correlation_id`.

Rules:

- do not pretend Scaleway is DeepSeek, Grok, Gemini, or GPT;
- do not use Scaleway as the sensitivity classifier;
- do not use Scaleway as the core router;
- keep simulation diagnostics clearly separate from real provider evaluation.

## 14. Event/Audit Implications

Future gate events should exist before provider events.

Gate event payload should include:

- `gate_decision_id`;
- `request_id`;
- `correlation_id`;
- `workspace_id`;
- `policy_mode`;
- `selected_gate`;
- `sensitivity`;
- `complexity`;
- `task_type`;
- `confidence`;
- `hard_rule_matches`;
- `requires_user_confirmation`;
- `allowed_external`;
- `external_call_would_be_made`;
- `external_call_attempted = false`;
- `timestamp`.

Provider event payload should include:

- `gate_decision_id`;
- `selected_gate`;
- `external_tier_assignment`;
- `actual_provider`;
- `model_id`;
- `simulated_external_call`;
- `provider_under_test`;
- `usage`;
- `external_call_attempted`;
- `external_call_succeeded`;
- `blocked_reason`;
- `timestamp`.

Events must not include:

- raw prompts;
- raw API keys;
- raw provider headers;
- raw sensitive BlueRev content;
- raw file contents;
- raw local classifier transcript when sensitive.

## 15. Contract Implications For D7

D7 should not add runtime routing. It should add minimal contracts and tests.

Recommended D7 contracts:

```text
SelectedGate:
  LOCAL_ONLY
  LOCAL_GEMMA
  USER_CONFIRM_REQUIRED
  CHEAP_GATE
  CHEAP_PLUS_GATE
  SCIENTIFIC_MEDIUM_GATE
  FRONTIER_GATE
  BLOCKED

SensitivityClass:
  public
  internal
  semi_sensitive
  ip_sensitive
  secret
  unknown

ComplexityClass:
  routine
  moderate
  high
  frontier
  unknown

ExternalTier:
  cheap
  cheap_plus
  scientific_medium
  frontier
  none

GateDecision
HardRuleMatch
ExternalTierAssignment
TierAssignment
SimulatedProviderCall
```

Existing `AIPrivacyClass`, `AITaskType`, `AIRequest`, and `AIResponse` can remain. D7 should map carefully rather than replacing them broadly.

## 16. Recommended Next Milestone

Superseded D6 recommendation: an AIProviderTier contract skeleton. Do not treat this as the active next milestone.

Superseded D6B recommendation: a local gate and external tier contract skeleton. Do not treat this as the active next milestone.

Corrected D6C recommendation:

```text
0E-D7 - Local Gemma Evaluation Harness and Golden Set
```

Scope:

- create a local Gemma evaluation harness and golden set;
- define expected structured outputs;
- define failure categories;
- test context/memory/tool grounding before gate contracts;
- add no runtime behavior;
- add no routes;
- add no local Gemma runtime;
- add no external provider calls;
- add no routing.

## 17. Explicit Non-Goals

0E-D6B does not implement:

- runtime gatekeeper behavior;
- local Gemma runtime;
- new providers;
- provider routing;
- frontend;
- chat;
- memory;
- streaming;
- BlueRev modeling;
- source ingestion;
- file upload;
- runner execution;
- CAD, CFD, PFD, or geometry workflows;
- MCP;
- agents;
- sidecars;
- desktop automation;
- multi-agent runtime.

## 18. Final Recommendation

JarvisOS should treat D6 as useful but incomplete.

Corrected principle:

```text
Local gate first. External tiers second.
```

JarvisOS is ready for a local Gemma evaluation harness and golden set. It is not ready for local gate contracts, medium provider, frontier provider, provider router, Supervisor UI, local Gemma runtime, or BlueRev modeling.
