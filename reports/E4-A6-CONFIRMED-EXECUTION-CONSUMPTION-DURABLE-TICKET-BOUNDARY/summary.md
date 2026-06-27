# E4-A6 Confirmed Execution Consumption Boundary

## Verdict

GREEN

## Baseline

- milestone: `E4-A6-CONFIRMED-EXECUTION-CONSUMPTION-DURABLE-TICKET-BOUNDARY`
- current HEAD: `2e5b0b667919fe0bc83c3f0fb55e1008ee74b7f2`
- baseline status: clean before A6

## Changed Files

- production:
  - `scripts/router_policy_semantic_validator.py`
- tests:
  - `tests/test_router_policy_confirmed_execution_consumption_boundary.py`
- reports:
  - `reports/E4-A6-CONFIRMED-EXECUTION-CONSUMPTION-DURABLE-TICKET-BOUNDARY/summary.md`
  - `reports/E4-A6-CONFIRMED-EXECUTION-CONSUMPTION-DURABLE-TICKET-BOUNDARY/summary.json`
- gitignore:
  - `.gitignore`
- schemas:
  - none

## Implementation

- A6 is a local alpha `allow_once` consumption boundary.
- A6 adds `evaluate_confirmed_execution_consumption_boundary(...)`.
- A6 reuses `evaluate_confirmed_execution_activation_boundary(...)` before any consumption write.
- A6 uses `consent_context.consent_id` as the consumption key.
- A6 rejects missing, non-string, empty, too-short, and placeholder `consent_id` values.
- A6 does not require UUID-only consent ids.
- A6 binds consent to previous decision id and confirmation digest through A4/A5.
- A6 writes an append-only JSONL ledger with `schema_version="v1"`.
- A6 writes one complete JSON object plus newline, flushes, and fsyncs.
- A6 fails closed on replay, corrupt lines, partial final line, duplicate keys, read failure, write failure, and failed A5 activation.
- A6 does not skip corrupt ledger entries.

## Economic Envelope

- source: `previous_decision`
- current `confirmed_execution` decision is diagnostic/comparison only, not authoritative for the consumed envelope.
- captured fields when present:
  - `route_tier`
  - `budget_class`
  - `provider_candidate`
  - `max_tokens_allowed`
  - `dry_run_required`
  - `allowed_execution_mode`
- completeness requires:
  - `provider_candidate`
  - `budget_class`
  - `max_tokens_allowed`
  - `dry_run_required`
  - `allowed_execution_mode`
- `route_tier` is audit/label only and cannot make the envelope complete by itself.
- `max_tokens_allowed` must be a positive int; bool, string, zero, negative, and missing values make the envelope incomplete.
- A6 computes:
  - `economic_envelope_complete`
  - `economic_envelope_limitations`
  - `automatic_execution_eligible`
- `automatic_execution_eligible=false` whenever `economic_envelope_complete=false`.
- `consumption_allowed=true` does not imply provider/network execution.

## No Permission Grant

- provider execution added: no
- network execution added: no
- SDK/API imports added: no
- `.env` reads added: no
- provider registry added: no
- E3 activated: no
- DB/server/workflow added: no
- ticket retrieval service added: no
- token benchmark added: no
- A7/A8/A9 work added: no
- schema changes: none

## Ledger Privacy

Ledger records include only:

- `schema_version`
- `consumption_key`
- `consumed_at`
- `previous_decision_id`
- `confirmation_digest`
- `confirmed_at`
- `target`
- `input_digest`
- `economic_envelope`
- `economic_envelope_complete`
- `economic_envelope_limitations`
- `automatic_execution_eligible`

Ledger records do not include prompt text, raw user input, raw private payloads, provider responses, model outputs, API keys, secrets, or `.env` values.

## Tests

- `python -m pytest tests/test_router_policy_confirmed_execution_consumption_boundary.py -q` -> `23 passed in 0.14s`
- `python -m pytest tests/test_router_policy_confirmed_execution_activation_boundary.py -q` -> `17 passed in 0.03s`
- `python -m pytest tests/test_router_policy_confirmation_revalidation_boundary.py -q` -> `15 passed in 0.03s`
- `python -m pytest tests/test_router_policy_semantic_validator.py -q` -> `40 passed in 0.06s`
- `python -m pytest tests/test_router_policy_canonical_digest.py -q` -> `14 passed in 0.04s`
- `python -m pytest tests/test_router_policy_confirmation_digest_binding.py -q` -> `5 passed in 0.04s`
- `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_external_egress_scope.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `324 passed in 0.45s`
- `python -m json.tool reports/E4-A6-CONFIRMED-EXECUTION-CONSUMPTION-DURABLE-TICKET-BOUNDARY/summary.json` -> pass
- `git diff --check` -> CRLF warnings only, no whitespace/content failure
- `rg -n "evaluate_external_budget_gate\(" scripts backend --glob '!scripts/router_policy_external_budget_gate.py'` -> no matches
- `rg -n "^import requests|^from requests|^import httpx|^from httpx|openai|anthropic|gemini" scripts` -> existing pre-E4 regex/text references only
- `rg -n "\.env|os\.environ|dotenv|API_KEY|SECRET|TOKEN" scripts tests reports/E4-A6-CONFIRMED-EXECUTION-CONSUMPTION-DURABLE-TICKET-BOUNDARY` -> report assertions plus existing probe/test/reference matches only
- `rg -n "datetime\.now|time\.time|utcnow\(" scripts tests` -> existing pre-E4 probe timestamp generation plus A4/A5/A6 negative test assertions only

## Final Git Status

```text
 M .gitignore
 M scripts/router_policy_semantic_validator.py
?? reports/E4-A6-CONFIRMED-EXECUTION-CONSUMPTION-DURABLE-TICKET-BOUNDARY/
?? tests/test_router_policy_confirmed_execution_consumption_boundary.py
```

## Known Limitations

- A6 is local alpha only.
- A6 uses a local JSONL ledger and is single-process alpha only; no DB, server, or transaction architecture was added.
- A6 does not implement provider/budget ordering; that remains future A7/A9 work.
- A6 does not implement retry, tool-call, history, or provider execution policy; that remains future A7/A9 work.
- A6 does not implement token benchmark or prompt compression harness.
- A6 does not claim provider readiness.

## Next Recommended Slice

`E4-A7-PROVIDER-BUDGET-ORDERING-AND-EXECUTION-POLICY-PRE`
