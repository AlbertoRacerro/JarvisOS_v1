# E4-A7-PRE Economic Execution Policy Boundary

## Verdict

GREEN

## Baseline

- current HEAD: `4e6c41511f7543d412fd679919dbdef47ffb995e`
- baseline status: clean before A7-PRE
- A6 zip cleanup required: no

## Changed Files

- production:
  - `scripts/router_policy_semantic_validator.py`
- tests:
  - `tests/test_router_policy_economic_execution_policy_boundary.py`
- reports:
  - `reports/E4-A7-PRE-ECONOMIC-EXECUTION-POLICY-BOUNDARY/summary.md`
  - `reports/E4-A7-PRE-ECONOMIC-EXECUTION-POLICY-BOUNDARY/summary.json`
- schemas:
  - none

## Integration Points

- `scripts/router_policy_semantic_validator.py::evaluate_economic_execution_policy_boundary`
- `scripts/router_policy_semantic_validator.py::evaluate_confirmed_execution_consumption_boundary`
- `scripts/router_policy_semantic_validator.py::evaluate_confirmed_execution_activation_boundary`

## Economic Execution Policy Boundary

- A7-PRE adds a pure helper that evaluates a supplied consumed A6 ticket against a requested execution plan.
- The helper returns status and violations only.
- The helper does not mutate the consumed ticket.
- The helper does not mutate the requested execution plan.
- The helper does not read or write the A6 JSONL ledger.
- The helper does not set `provider_call_allowed_now`, `external_network_allowed_now`, or `tool_execution_allowed_now`.
- `policy_scope` is `economic_execution_precheck_only`.

## Consumed Ticket Requirements

- `schema_version` must be `v1`
- `economic_envelope_complete` must be `true`
- `automatic_execution_eligible` must be `true`
- `economic_envelope.provider_candidate` must be present and known
- `economic_envelope.budget_class` must be present and known
- `economic_envelope.max_tokens_allowed` must be a positive int
- `economic_envelope.dry_run_required` must be a bool
- `economic_envelope.allowed_execution_mode` must be present

## Requested Execution Plan Requirements

- `provider_candidate` must be present and known
- `budget_class` must be present and known
- `max_tokens_requested` must be a positive int
- `execution_mode` must be present
- `dry_run` must be a bool
- real automatic execution requires:
  - history off policy
  - explicit non-negative retry cap
  - explicit non-negative tool-call cap
  - fallback provider explicitly disabled

## Ordering

- provider class ordering: `local < external:cheap < external:scientific_medium < external:frontier`
- provider aliases supported:
  - `local:qwen -> local`
  - `local:gemma -> local`
  - `external:cheap -> external:cheap`
  - `external:scientific_medium -> external:scientific_medium`
  - `external:frontier -> external:frontier`
- budget class ordering: `local < cheap < medium < frontier`
- budget aliases supported:
  - `low -> cheap`
  - `high -> frontier`
  - `expensive -> frontier`
- unknown provider and budget classes fail closed
- no new provider/provider-family names were introduced by A7-PRE; pre-existing schema enum values `local:qwen`/`local:gemma` are normalized to the abstract local class.

## Enforcement

- requested provider class cannot exceed consumed provider class
- requested budget class cannot exceed consumed budget class
- requested max tokens cannot exceed consumed `max_tokens_allowed`
- `execution_mode=dry_run` requires `dry_run=true`
- `execution_mode=dry_run` with `dry_run=false` fails closed
- `execution_mode=execute_after_confirm` with `dry_run=true` is diagnostic dry-run only
- diagnostic dry-run pass does not imply provider or network permission
- `execution_policy_allowed` is not provider permission
- `dry_run_required=true` blocks requested `dry_run=false`
- consumed `allowed_execution_mode=execute_after_confirm` is required for real automatic execution
- consumed `allowed_execution_mode=dry_run` may satisfy dry-run-only requests
- `answer_only`, `propose_only`, `dry_run`, and `blocked` fail real automatic execution
- history must be off for real automatic execution
- retry cap must be explicit for real automatic execution
- tool-call cap must be explicit for real automatic execution
- fallback provider must be explicitly disabled for real automatic execution
- `route_tier` remains audit-only and is not authority

## Authority Chain Expectation

- `A5 activation_safe == true`
- `A6 consumption_allowed == true`
- `A6 automatic_execution_eligible == true`
- `A7-PRE execution_policy_allowed == true`

## No Execution / No Registry

- provider execution added: no
- network execution added: no
- SDK/API imports added: no
- `.env` reads added: no
- provider registry added: no
- API keys added: no
- E3 activated: no
- DB/server/workflow added: no
- token benchmark added: no
- A8/A9 work added: no
- schema changes: none

## Tests

- `python -m pytest tests/test_router_policy_economic_execution_policy_boundary.py -q` -> `25 passed in 0.13s`
- `python -m pytest tests/test_router_policy_confirmed_execution_consumption_boundary.py -q` -> `23 passed in 0.27s`
- `python -m pytest tests/test_router_policy_confirmed_execution_activation_boundary.py -q` -> `17 passed in 0.10s`
- `python -m pytest tests/test_router_policy_confirmation_revalidation_boundary.py -q` -> `15 passed in 0.08s`
- `python -m pytest tests/test_router_policy_semantic_validator.py -q` -> `40 passed in 0.12s`
- `python -m pytest tests/test_router_policy_canonical_digest.py -q` -> `14 passed in 0.07s`
- `python -m pytest tests/test_router_policy_confirmation_digest_binding.py -q` -> `5 passed in 0.13s`
- `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_external_egress_scope.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `324 passed in 1.04s`
- `python -m json.tool reports/E4-A7-PRE-ECONOMIC-EXECUTION-POLICY-BOUNDARY/summary.json` -> pass
- `git diff --check` -> CRLF warning only, no whitespace/content failure
- `rg -n "evaluate_external_budget_gate\(" scripts backend --glob '!scripts/router_policy_external_budget_gate.py'` -> no matches
- `rg -n "^import requests|^from requests|^import httpx|^from httpx|openai|anthropic|gemini" scripts` -> existing pre-E4 regex/text references only
- `rg -n "\.env|os\.environ|dotenv|API_KEY|SECRET|TOKEN" scripts tests reports/E4-A7-PRE-ECONOMIC-EXECUTION-POLICY-BOUNDARY` -> report assertions plus existing probe/test/reference matches only
- `rg -n "datetime\.now|time\.time|utcnow\(" scripts tests` -> existing pre-E4 probe timestamp generation plus A4/A5/A6/A7 negative test assertions only

## Known Limitations

- A7-PRE does not call providers
- A7-PRE does not read real secrets
- A7-PRE does not implement provider registry
- A7-PRE does not implement token benchmark
- A7-PRE does not wire runtime automatic call path
- A7-PRE uses abstract provider and budget classes only
- A7-PRE remains helper-only and adds no provider permission surface

## Final Git Status

```text
 M scripts/router_policy_semantic_validator.py
?? reports/E4-A7-PRE-ECONOMIC-EXECUTION-POLICY-BOUNDARY/changed_files.zip
?? reports/E4-A7-PRE-ECONOMIC-EXECUTION-POLICY-BOUNDARY/
?? tests/test_router_policy_economic_execution_policy_boundary.py
```

## Next Recommended Slice

`E4-A8-RUNTIME-AUTHORITY-CHAIN-INTEGRATION`
