# Hybrid Intake Field Ownership

This document defines field ownership for staged memory intake. It preserves the
1C-Y/1C-Z boundary:

```text
models may propose intake hints;
JarvisOS validates, owns policy, and decides;
no intake field authorizes runtime action.
```

Fast intake remains a cheap signal envelope. It is not memory runtime,
retrieval runtime, Context Pack Broker runtime, route selection, provider
routing, tool execution, final sensitivity policy, or canonical promotion.

## Ownership Classes

| Class | Meaning |
| --- | --- |
| `deterministic_owned` | JarvisOS-owned metadata or authority fields. Model output is ignored. |
| `deterministic_first` | JarvisOS deterministic rules should provide the first answer and override obvious model misses. |
| `hybrid` | Deterministic rules and AI hints can both inform a later reviewed decision. |
| `ai_advisory` | AI may propose a non-authoritative hint, but JarvisOS must validate or review before use. |
| `diagnostic_only` | Useful for probe/report analysis only; not copied into canonical memory. |
| `untrusted_for_runtime` | Model output must never control this field or behavior. |

## Deterministic-Owned Fields

JarvisOS owns provenance and runtime authority:

- `source.input_id`
- `source.conversation_id`
- `source.timestamp`
- `source.raw_text_preserved`
- `schema_version`
- `runtime_approved`
- `canonical_promotion`
- `memory_write_authorization`
- `retrieval_authorization`
- `tool_authorization`
- `provider_authorization`
- `route_selection`
- `final_sensitivity_decision`

Model output cannot create, override, or imply these fields.

## Deterministic-First Fields

JarvisOS deterministic rules should own obvious observable cases first:

- `contains_numbers_or_metrics`
- `mentions_code_or_command`
- `mentions_project_or_artifact`
- `mentions_source_or_literature`
- `project_bucket` for explicit project/artifact names such as JarvisOS,
  BlueRev, coursework, local AI, or staged memory references.
- `sensitivity_bucket` for obvious secrets such as API keys, passwords,
  tokens, `.env` content, private keys, and credential placeholders.
- `status_bucket` for obvious phrases such as accepted, confirmed, not
  decided, tentative, candidate, or draft.

These rules are implemented in
`backend/app/modules/local_ai/intake/deterministic_signals.py` and exposed only
through the CLI/manual report path in
`backend/app/modules/local_ai/intake/probe_fast_intake.py`.

## Hybrid Fields

These fields are useful but not final:

- `storage_relevance`
- `record_bucket`
- `domain_bucket`
- `status_bucket`
- `needs_enrichment`
- `needs_user_confirmation`
- `uncertainty_reason`

Deterministic rules should catch clear cases. AI can remain useful for language
that is semantically subtle, but its answer is advisory until validated,
enriched, reviewed, or promoted by JarvisOS policy.

## AI-Advisory Fields

AI can help propose these signals, but they remain non-authoritative:

- `contains_user_preference`
- `contains_user_decision`
- `contains_assumption`
- `contains_design_constraint`
- `contains_open_question`
- `contains_action_request`
- `contains_test_result`
- `mentions_previous_context`
- `confidence_observable`
- `confidence_bucket_assignment`

JarvisOS should treat model confidence as a diagnostic hint, not permission to
act.

## Diagnostic-Only Fields

These fields help repair prompts and evaluate model behavior:

- `uncertain_fields`
- `advisory_note`

Reports may store presence, length, and bounded field-name metadata. Reports
must not persist raw prompt text, raw case text, raw model output, messages,
secret values, or raw advisory notes.

## Model-Untrusted Fields and Behaviors

Model output must never be trusted for:

- sensitivity downgrades;
- secret-to-public downgrades;
- accepted/canonical promotion;
- BlueRev assumption acceptance;
- provider execution;
- tool execution;
- retrieval execution;
- action execution.

Any future runtime path must keep these decisions in JarvisOS deterministic
policy, explicit review, or audited promotion logic.

## Current Baseline

1C-Z-S adds a deterministic baseline helper and manual report mode:

```powershell
.\.venv\Scripts\python -m app.modules.local_ai.intake.probe_fast_intake --mode deterministic-baseline
```

The mode does not call Ollama. It scores the fixed synthetic case set, writes a
sanitized report under `backend/local_eval_reports/`, and compares aggregate
metrics against the latest existing `smoke-flat` report when available.

The baseline is useful for field ownership, hard overrides, and calibration. It
is not approval for memory runtime, retrieval runtime, Context Pack Broker
runtime, routes, UI, provider routing, tool execution, external APIs, local
gatekeeping, chat, or autonomous action.
