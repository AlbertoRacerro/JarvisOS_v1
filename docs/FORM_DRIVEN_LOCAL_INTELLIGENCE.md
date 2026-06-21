# Form-Driven Local Intelligence

This document defines the corrected local AI architecture for JarvisOS.

Core rule:

```text
Gemma is the local semantic brain.
JarvisOS is the deterministic structure around it.
```

JarvisOS does not semantically understand Gemma outputs. JarvisOS provides
forms, schemas, allowed options, path rules, permissions, retries, logging,
persistence, promotion policy, and audit. Gemma performs semantic reasoning
locally inside those bounded forms and protocols.

## Structural Validation Is Not Semantic Validation

Structural validation may include:

- schema validity;
- required fields;
- allowed enum values;
- boolean fields;
- field length;
- status values;
- source IDs;
- path existence;
- allowed path roots;
- permitted save locations;
- valid transition states;
- no obvious secrets such as API keys, passwords, tokens, or `.env` content.

Structural validation must not claim to validate:

- semantic fidelity;
- strategic correctness;
- summary quality;
- whether a design assumption is technically true;
- whether a memory card is semantically complete;
- whether sensitivity is semantically correct beyond obvious hard overrides.

When a valid form is semantically wrong, the failure belongs to Gemma reliability,
source quality, or review policy. JarvisOS can reject invalid structure, request
a retry with machine-readable errors, save a proposed object, or require review.
It must not pretend that schema validity proves semantic truth.

## Gemma-Facing Showcase Files

Future JarvisOS should maintain a small set of always-readable showcase files for
Gemma. These files are synthetic system maps and indexes, not a replacement for
source files.

Example showcase files:

```text
GEMMA_START_HERE.md
CURRENT_STATE.md
SYSTEM_MAP.md
MEMORY_INDEX.md
PROJECT_INDEX.md
FILE_CATALOG.md
DECISION_INDEX.md
OPEN_CLARIFICATIONS.md
TOOL_AND_PROVIDER_CATALOG.md
SAFETY_POLICY.md
```

Intent:

- Gemma reads these small files first.
- Showcase files summarize what important sources contain.
- Gemma uses them to request the right files or context packages.
- Moderate over-fetch is acceptable.
- Under-fetch on important tasks is a serious failure mode.

Simple indexes, backlinks, tags, and source IDs come before any graph or
Obsidian-like implementation. A graph view may become useful later only after
the simpler showcase/index pattern proves useful.

## Responsibilities

For current `gemma4:12b-it-qat` classification work, the only accepted runtime
role is non-critical advisory semantic hints. The broader capabilities below
describe future form-driven architecture and require reliability gates before
they can affect policy, persistence, routing, tools, memory, retrieval, or
provider behavior.

Gemma should be able to:

- read showcase files;
- inspect system maps;
- request additional context;
- fill memory cards;
- fill decision, source, and file cards;
- propose provider intent;
- propose tool intent;
- assess sensitivity according to stable policy;
- ask clarification when a substantial choice is missing;
- leave fields as `not_decided` or `to_be_defined` when context is insufficient.

JarvisOS should:

- generate and update showcase files;
- provide stable schemas and forms;
- validate structure only;
- reject invalid forms;
- request retries with machine-readable errors;
- save proposed outputs;
- promote outputs only according to explicit policy;
- log everything;
- prevent arbitrary commands and arbitrary file writes.

## Form Protocol Catalog

Future Gemma work should use explicit forms. Each form separates what Gemma
proposes from what JarvisOS is allowed to save, promote, or execute.

| Form | Purpose | Filled By | JarvisOS Structural Checks | Semantic Limit | Effect |
| --- | --- | --- | --- | --- | --- |
| `ClassificationForm` | Produce non-critical semantic hints for a prompt or task. | Gemma or deterministic fallback. | Schema, enums, confidence bounds, hard overrides. | Does not prove the label is semantically correct and does not own safety-critical fields. | Can provide task, project, topic, context-need, and confidence hints only. |
| `ContextAccessRequest` | Ask for bounded context. | Gemma. | Allowed package/source IDs, reason length, max count. | Does not prove the requested context is sufficient. | Can trigger bounded context assembly. |
| `MemoryCard` | Propose a memory item. | Gemma. | Required fields, source IDs, tags, status. | Does not prove the memory is complete or true. | Can save as proposed memory. |
| `FileCard` | Summarize a file or file role. | Gemma. | Existing path/source ID, allowed root, summary length. | Does not prove summary quality. | Can update an index after policy allows. |
| `SourceCard` | Describe an evidence source. | Gemma. | Source ID, citation fields, freshness fields. | Does not prove source interpretation is correct. | Can save source metadata. |
| `DecisionCard` | Propose or summarize a decision. | Gemma. | Status enum, linked sources, owner fields. | Does not prove strategic correctness. | Can save as proposed decision. |
| `RoadmapCard` | Propose roadmap state. | Gemma. | Milestone ID, status enum, dependencies. | Does not prove priority is correct. | Can save as proposed roadmap update. |
| `ClarificationRequest` | Ask for high-value missing information. | Gemma. | Question length, allowed reason enum, target entity/source. | Does not prove the question is necessary. | Can ask the user or reviewer. |
| `SensitivityAssessment` | Assess sensitivity. | Gemma. | Enum, rationale length, hard deterministic overrides. | Does not prove semantic sensitivity in subtle cases. | Can trigger local-only, review, or redaction policy. |
| `ToolIntentProposal` | Propose a tool action. | Gemma. | Allowed tool intent, target ID, risk, confirmation flag. | Does not authorize a concrete command. | Can be blocked, reviewed, or transformed by JarvisOS. |
| `ProviderIntentProposal` | Propose external model use. | Gemma. | Allowed provider intent, provider enum, sensitivity, budget fields. | Does not authorize provider access. | Can be blocked, reviewed, or routed by JarvisOS policy. |
| `ReviewRequest` | Ask for stronger review. | Gemma or JarvisOS. | Review type, target ID, reason enum. | Does not prove review result. | Can queue human, 31B, or API sampling review later. |

Provider enum examples for future design language only:

```text
deepseek
grok
gemini
gpt_5_5
local_gemma_12b
local_gemma_31b
```

These names do not create provider integrations by themselves.

## Clarification Philosophy

Gemma must not hallucinate missing substantial choices. If multiple BlueRev
materials were discussed but none was explicitly selected, Gemma must not assume
a material. It should set `material = "not_decided"` or create a
`ClarificationRequest` asking for a short confirmation.

Clarifications are for high-value uncertainty:

- missing user choice;
- conflicting sources;
- outdated evidence;
- ambiguous reference;
- multiple candidate entities;
- unsafe or sensitive ambiguity;
- insufficient source detail.

Clarifications are not for mechanical uncertainty such as field names, ordinary
formatting, or routine schema choices that JarvisOS can define.

## Sensitivity Philosophy

Gemma performs semantic sensitivity assessment using stable fiscal and safety
policy. JarvisOS applies deterministic hard overrides only for obvious cases
such as API keys, passwords, tokens, `.env` files, forbidden paths, disallowed
providers, invalid enum values, or explicit user confirmation requirements.

Deterministic checks cannot reliably distinguish public literature data from
proprietary prototype experimental data. That distinction is semantic and
belongs to Gemma or to a stronger reviewer when needed.

The current `gemma4:12b-it-qat` classification evidence is not strong enough for
runtime safety decisions. 12B may provide advisory semantic hints, but final
sensitivity, risk, next action, provider selection, tool execution, memory
write, retrieval, route selection, external-call, and safety decisions remain
JarvisOS policy or review-gate responsibilities.

## Tool And Provider Intent

Gemma should never generate arbitrary executable commands. It fills
`ToolIntentProposal` or `ProviderIntentProposal` forms.

JarvisOS validates allowed intent, provider, target, risk, confirmation, path,
and budget fields. JarvisOS constructs the concrete execution, blocks it, or
asks for review. A valid intent form is not permission to run arbitrary code,
write arbitrary files, or call an external provider.

## Memory Staging

Memory should move through explicit stages:

```text
raw_source
proposed_memory
accepted_memory
canonical_state
```

Gemma may produce proposed memory cards through valid forms. Promotion to
accepted or canonical memory is controlled by policy, such as:

- high smoke-test reliability;
- sampling review;
- stronger local 31B or API review;
- direct user decision;
- repeated use without contradiction;
- source-grounded verification.

Routine mechanical memory cards should not require personal user review forever.
The system should earn autonomy through evidence.

## Smoke-Test Philosophy

Do not assume Gemma is reliable. Do not assume Gemma is unreliable. Measure.

Future smoke tests should measure:

- schema validity;
- source fidelity;
- invented references;
- correct `not_decided` behavior;
- clarification quality;
- tag usefulness;
- context request completeness;
- over-fetch versus under-fetch;
- sensitivity assessment quality;
- provider/tool intent validity;
- rerun stability.

JarvisOS should prefer empirical reliability data over manual human review as
the main safety mechanism, while still preserving explicit policy gates for
promotion and execution.

## Rebased Roadmap

Near-term sequence after the existing manual live probe:

```text
1B-R-LIVE  Manual Gemma 12B classification probe
1C         Classification live probe analysis and roadmap rebase
1D         Gemma-facing showcase files design
1E         Form protocol catalog design
1F         Structural validator + retry loop design
1G         Gemma form-fill smoke test harness
1H         Showcase files generator design
1I         Context access from showcase files
1J         Provider/tool intent form design
```

Later local memory and context foundation:

```text
2A         Source-grounded review protocol
2B         Optional 31B/API sampling review
2C         Memory promotion policy
2D         Memory index generation
2E         Context package assembly
```

External provider sequence:

```text
3A         External prompt package format
3B         Redaction/sensitivity policy
3C         Provider abstraction hardening
3D         DeepSeek
3E         Grok
3F         Gemini
3G         GPT-5.5
3H         Provider selection policy
```

Workbench, Foundry, and Debate Mode remain downstream layers. They depend on the
form/protocol/memory foundation proving reliable first.
