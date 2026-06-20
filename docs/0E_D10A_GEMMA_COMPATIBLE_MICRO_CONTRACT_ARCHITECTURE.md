# 0E-D10A Gemma-Compatible Micro-Contract Architecture

## 1. Executive Judgement

JarvisOS should stop treating the full D7 `GemmaEvalOutput` as the first local Gemma contract.

D9R showed that the full output is too monolithic for the first local orchestration path. The corrected architecture is a staged pipeline of small, independently validated micro-contracts.

Decision:

```text
Gemma proposes small structured objects.
JarvisOS validates them.
JarvisOS executes or blocks.
JarvisOS records the result.
```

Gemma remains a local orchestrator candidate, not an executor, not a memory system, not a tool runtime, not a database reader, and not an external API client.

## 2. Why Full D7 Failed As A First Contract

The D7 schema was useful as a harness because it described the long-term operating-brain shape in one place.

It failed as a first local Gemma runtime contract because it combined too many decisions into one output:

- task classification;
- sensitivity classification;
- context sufficiency;
- context package request;
- tool request allow/deny structure;
- local action selection;
- external escalation drafting;
- TODO extraction;
- decision extraction;
- hallucination detection;
- final response planning.

D9R showed that `gemma4:31b-it-qat` can satisfy a compact schema with Ollama native structured output, but the full D7 one-case probe timed out. That points to contract shape and runtime cost, not simply model incapability.

## 3. What D9R Proves And Does Not Prove

D9R proves:

- both 12B and 31B can emit tiny direct JSON;
- 31B can satisfy a compact schema through native structured output;
- OpenAI-compatible JSON hints are weaker than native structured output in this local setup;
- the full D7 schema is too heavy for a first one-pass contract.

D9R does not prove:

- Gemma is ready for local chat;
- Gemma is ready for gatekeeping;
- Gemma is ready for memory, retrieval, file/database access, or tool execution;
- Gemma 31B is weak;
- Gemma 31B is strong enough for production orchestration;
- 12B can handle anything beyond narrow local utility probes.

## 4. Local Gemma Role

Gemma's role is advisory and bounded.

Allowed:

- classify a request;
- propose bounded context packages;
- classify sensitivity as an advisory signal;
- propose a tool call for JarvisOS validation;
- draft a redacted external prompt if policy later allows;
- extract TODOs and decisions from provided text;
- select relevant evidence from provided snippets.

Forbidden:

- executing tools;
- reading arbitrary files;
- querying databases;
- mutating project state;
- calling external APIs;
- bypassing JarvisOS policy;
- treating stale context as canonical;
- inventing retrieved evidence or tool results.

## 5. JarvisOS Role

JarvisOS is authoritative.

JarvisOS owns:

- memory;
- retrieval;
- context packaging;
- policy;
- privacy classification;
- token/cost gates;
- tool validation;
- execution;
- persistence;
- audit logging;
- schema validation;
- retries and repair decisions.

Gemma output is input to JarvisOS validation, not permission to act.

## 6. External API Role

External APIs may eventually serve as stronger reasoning specialists.

They are never called by Gemma.

Correct path:

```text
Gemma drafts an ExternalPromptDraftOutput
-> JarvisOS validates sensitivity/policy/cost/user confirmation
-> JarvisOS sends or blocks
-> JarvisOS records the decision
```

No external escalation exists in D10A.

## 7. Micro-Contract Pipeline

Proposed staged pipeline:

```text
User input
-> TaskClassificationOutput
-> SensitivityCheckOutput
-> ContextRequestOutput, if context is needed
-> EvidenceSelectionOutput, if context snippets are provided
-> ToolCallProposalOutput, if an action is proposed
-> ExternalPromptDraftOutput, only if local policy later permits escalation
-> TodoExtractionOutput or DecisionExtractionOutput, when extraction is requested
-> Final response drafting in a later, separate contract
```

The pipeline can stop after any stage.

Each stage is:

- small;
- schema-validatable;
- independently testable;
- retryable;
- compatible with native structured output;
- non-executing.

## 8. Contract Definitions

The initial code-level contract sketches live in:

```text
backend/app/modules/local_ai/contracts.py
```

They are isolated Pydantic models. They do not call a model, register routes, persist data, or replace the D7 harness.

### TaskClassificationOutput

Purpose:

Classify the user's request.

Fields:

- `task_type`
- `project_area`
- `requires_context`
- `requires_tool`
- `requires_external_reasoning`
- `confidence`
- `reasons`
- `schema_version`

### ContextRequestOutput

Purpose:

Ask JarvisOS for bounded context packages.

Fields:

- `requested_context_packages`
- `context_request_reason`
- `minimum_needed_context`
- `forbidden_context`
- `confidence`
- `schema_version`

Gemma may request packages. It may not read files directly.

### SensitivityCheckOutput

Purpose:

Provide an advisory sensitivity classification.

Fields:

- `sensitivity`
- `externalization_allowed`
- `redaction_required`
- `user_confirmation_required`
- `reasons`
- `confidence`
- `schema_version`

JarvisOS policy remains authoritative.

### ToolCallProposalOutput

Purpose:

Propose an action for validation.

Fields:

- `tool_name`
- `arguments`
- `purpose`
- `risk_level`
- `requires_user_confirmation`
- `allowed_by_model`
- `confidence`
- `schema_version`

This does not execute the tool.

### ExternalPromptDraftOutput

Purpose:

Prepare a redacted prompt for a future external model only if JarvisOS policy allows.

Fields:

- `target_capability`
- `redacted_prompt`
- `included_context_refs`
- `excluded_sensitive_refs`
- `reason_for_escalation`
- `expected_output_contract`
- `confidence`
- `schema_version`

Gemma must not send the prompt externally.

### TodoExtractionOutput

Purpose:

Extract TODOs from supplied logs or notes.

Fields:

- `todos`
- `owner_guess`
- `priority_guess`
- `source_refs`
- `confidence`
- `schema_version`

### DecisionExtractionOutput

Purpose:

Extract accepted, proposed, superseded, or rejected decisions from supplied context.

Fields:

- `decisions`
- `decision_status`
- `source_refs`
- `supersedes`
- `confidence`
- `schema_version`

### EvidenceSelectionOutput

Purpose:

Select relevant snippets from already retrieved evidence.

Fields:

- `selected_evidence_refs`
- `rejected_evidence_refs`
- `reasoning_summary`
- `missing_evidence`
- `confidence`
- `schema_version`

This does not implement retrieval.

## 9. Validation Rules

All micro-contracts should follow these rules:

- `extra="forbid"`;
- strict schema version;
- confidence between 0 and 1;
- controlled enum vocabulary where possible;
- bounded list fields;
- context references by ID, not raw file paths;
- no execution claims;
- no external-call claims;
- no invented tool results;
- no arbitrary filesystem or database requests.

JarvisOS must validate every output before using it.

## 10. Retry/Repair Strategy

Retries should remain local and bounded.

Recommended strategy:

1. Validate the first structured output.
2. If JSON-invalid, retry once with a shorter direct prompt.
3. If schema-invalid, retry once with the validation error and the same contract schema.
4. If still invalid, mark the contract failed.
5. Do not silently repair sensitive or tool-related decisions.
6. Do not convert an invalid proposal into an executed action.

Repair is a validation aid, not a policy bypass.

## 11. Failure Handling

Failure classes:

- runtime unavailable;
- timeout;
- invalid JSON;
- schema invalid;
- unsupported enum;
- low confidence;
- missing required context;
- unsafe tool proposal;
- externalization not allowed;
- stale or conflicting evidence;
- policy disagreement.

Safe handling:

- stop the pipeline;
- request bounded context;
- ask the user for clarification;
- fall back to deterministic JarvisOS logic;
- log the failed contract without raw secrets.

## 12. Ollama Native Structured Output

D9R showed that native structured output can matter.

Future probes should use:

```json
{
  "stream": false,
  "format": {
    "type": "object",
    "properties": {}
  },
  "options": {
    "temperature": 0
  }
}
```

Only local endpoints are allowed.

Allowed:

```text
http://localhost:11434/api/chat
http://127.0.0.1:11434/api/chat
```

Forbidden:

- HTTPS;
- external domains;
- cloud provider URLs;
- credentials in URLs;
- API keys.

D10A does not add a persistent native adapter. D10B should test these schemas through a narrow probe harness.

## 13. Future Context Pack Broker Relationship

The Context Pack Broker should not be Gemma-controlled.

Gemma may emit:

```text
ContextRequestOutput
```

JarvisOS should then decide:

- whether the requested packages exist;
- whether policy allows them;
- whether the user/workspace permits them;
- whether they should be summarized or redacted;
- whether the request should be denied.

Gemma receives only the bounded package contents JarvisOS provides.

## 14. Future External API Escalation Relationship

Gemma may eventually draft:

```text
ExternalPromptDraftOutput
```

JarvisOS must then validate:

- sensitivity;
- redaction;
- user confirmation;
- provider policy;
- budget;
- token cap;
- audit logging;
- expected output contract.

Gemma never sends the request.

## 15. Anti-Patterns To Avoid

Avoid:

- one huge "brain output" schema as the first runtime contract;
- Gemma reading files directly;
- Gemma calling tools directly;
- Gemma deciding externalization authoritatively;
- Gemma returning prose for machine decisions;
- hidden automatic retries that mutate meaning;
- treating low-confidence proposals as actions;
- building a benchmark platform before micro-contracts work;
- adding UI, routes, persistence, registry, scheduler, or provider routing in D10A.

## 16. Recommended Next Milestone

Recommended next:

```text
0E-D10B - Micro-Contract Probe Harness
```

D10B should test `gemma4:31b-it-qat` on each micro-contract individually using native structured output before any runtime integration.

D10B should remain evaluation-only and should not add chat, memory runtime, retrieval runtime, local gatekeeper enforcement, provider routing, frontend UI, or BlueRev modeling.
