# E4-A4 - Confirmation Decision Revalidation Boundary

## Verdict

- verdict: `GREEN`
- current HEAD: `e7c53e4ab2236362dfb0287fd6a539b1846143d9`

## Changed Files

- production:
  - [router_policy_semantic_validator.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_semantic_validator.py)
- tests:
  - [test_router_policy_confirmation_revalidation_boundary.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_confirmation_revalidation_boundary.py)
- reports:
  - [summary.md](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A4-CONFIRMATION-DECISION-REVALIDATION-BOUNDARY/summary.md)
  - [summary.json](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A4-CONFIRMATION-DECISION-REVALIDATION-BOUNDARY/summary.json)
- schemas:
  - none

## Integration Points

- semantic-validator helper:
  - `validate_confirmation_revalidation_boundary(...)`
- semantic-validator caller:
  - `_check_expiry(...)`
- reused A3 digest helper:
  - `validate_confirmation_digest_integrity(...)`

## Revalidation Boundary Implemented

- implemented: yes
- coverage level: `mixed`
- no public confirmation workflow added: yes
- boundary validates only provided `previous_decision` and `consent_context`
- A4-R1 fixes applied:
  - missing/invalid `now` fail closed
  - previous external target + missing/non-external current target fail closed
  - current `confirmed_execution.confirmation_digest` non-null rejected

## Previous Confirmation Requirements

- `confirmed_execution` requires:
  - `previous_decision` provided
  - `previous_decision.lifecycle_stage == "awaiting_confirmation"`
  - `previous_decision.confirmation_required == True`
  - non-empty `previous_decision.confirmation_digest`
- enforced_by:
  - `test_valid_confirmed_execution_passes_revalidation_boundary`
  - `test_missing_previous_decision_rejected`

## Consent Context Requirements

- required and checked:
  - `confirmed_previous_decision_id`
  - `confirmed_confirmation_digest`
  - `confirmation_action == "allow_once"`
  - valid `confirmed_at`
- enforced_by:
  - `test_valid_confirmed_execution_passes_revalidation_boundary`
  - `test_consent_digest_mismatch_rejected`
  - `test_missing_confirmed_at_rejected`

## Digest Continuity Behavior

- `consent_context.confirmed_confirmation_digest` must equal `previous_decision.confirmation_digest`
- current revalidation does not trust stored previous digest blindly
- enforced_by:
  - `test_consent_digest_mismatch_rejected`

## Previous Digest Integrity Recheck

- uses A3 helper/envelope:
  - `validate_confirmation_digest_integrity(previous_decision)`
- rejects tampered previous decision payload/target/options after original confirmation creation
- enforced_by:
  - `test_previous_digest_tampering_rejected_by_recomputed_a3_digest`

## Input Revalidation Behavior

- missing or invalid `now` fails closed for `confirmed_execution` revalidation
- missing current `input_digest` fails closed
- missing previous `input_digest` fails closed
- input drift is rejected at A4 boundary
- no schema change was made for `input_revalidated`
- current schema lacks `input_revalidated`, so A4 cannot represent explicit revalidation state and therefore rejects drift deterministically
- enforced_by:
  - `test_missing_now_fails_closed_for_confirmed_execution_revalidation`
  - `test_missing_or_drifted_input_digest_fails_closed`

## Target Continuity Behavior

- target continuity is representable and tested through existing fields:
  - `current.proposed_external_target`
  - fallback to external `current.provider_candidate`
  - compared against `previous_decision.proposed_external_target`
- previous external target + missing/non-external current target fail closed
- target drift rejected
- no `TARGET_CONTINUITY_LIMITATION`
- enforced_by:
  - `test_missing_current_target_rejected_when_previous_target_exists`
  - `test_target_drift_rejected_where_representable`

## Actionability Drift Behavior

- digest match does not grant provider/network permission
- helper does not mutate `provider_call_allowed_now`
- helper does not mutate `external_network_allowed_now`
- `confirmed_execution` must not retain live confirmation artifacts:
  - `confirmation_required`
  - `confirmation_payload_required`
  - `confirmation_payload`
  - `confirmation_digest`
  - `confirmation_options`
- enforced_by:
  - `test_digest_match_does_not_mutate_or_grant_provider_network_permission`
  - `test_confirmed_execution_cannot_retain_live_confirmation_artifacts`
  - `test_confirmed_execution_cannot_retain_confirmation_digest`

## Expiry Behavior

- previous confirmation requires valid `expires_at`
- missing or invalid previous expiry fails closed
- expired previous confirmation rejected
- uses caller-supplied `now` only
- enforced_by:
  - `test_missing_or_expired_previous_confirmation_rejected`
  - `test_revalidation_helper_uses_caller_supplied_now_only`

## Purity / No-Mutation Proof

- helper returns violations only
- helper does not mutate current decision or previous decision
- helper does not set provider/network permissions
- no wall-clock calls inside the helper
- enforced_by:
  - `test_digest_match_does_not_mutate_or_grant_provider_network_permission`
  - `test_revalidation_helper_uses_caller_supplied_now_only`

## route_action / route_tier Non-Authority Proof

- changing route labels alone does not rescue an invalid revalidation state
- input drift remains rejected even if route labels are changed
- enforced_by:
  - `test_route_labels_remain_non_authority_for_revalidation`

## Tests Added / Updated

- added:
  - `tests/test_router_policy_confirmation_revalidation_boundary.py`
    - `test_valid_confirmed_execution_passes_revalidation_boundary`
    - `test_missing_now_fails_closed_for_confirmed_execution_revalidation`
    - `test_missing_previous_decision_rejected`
    - `test_consent_digest_mismatch_rejected`
    - `test_missing_confirmed_at_rejected`
    - `test_missing_or_expired_previous_confirmation_rejected`
    - `test_previous_digest_tampering_rejected_by_recomputed_a3_digest`
    - `test_missing_or_drifted_input_digest_fails_closed`
    - `test_missing_current_target_rejected_when_previous_target_exists`
    - `test_target_drift_rejected_where_representable`
    - `test_digest_match_does_not_mutate_or_grant_provider_network_permission`
    - `test_confirmed_execution_cannot_retain_live_confirmation_artifacts`
    - `test_confirmed_execution_cannot_retain_confirmation_digest`
    - `test_route_labels_remain_non_authority_for_revalidation`
    - `test_revalidation_helper_uses_caller_supplied_now_only`
- unchanged but re-run:
  - [test_router_policy_semantic_validator.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_semantic_validator.py)
  - [test_router_policy_confirmation_digest_binding.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_confirmation_digest_binding.py)
  - [test_router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_canonical_digest.py)

## Checks Run

- `python -m pytest tests/test_router_policy_canonical_digest.py -q` -> `14 passed in 0.04s`
- `python -m pytest tests/test_router_policy_confirmation_digest_binding.py -q` -> `5 passed in 0.08s`
- `python -m pytest tests/test_router_policy_confirmation_revalidation_boundary.py -q` -> `15 passed`
- `python -m pytest tests/test_router_policy_semantic_validator.py -q` -> `40 passed in 0.09s`
- `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_external_egress_scope.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `324 passed in 0.90s`
- `git diff --check` -> CRLF warning only, no whitespace/content failure
- `git status --short` -> expected A4 files only
- `rg -n "evaluate_external_budget_gate\(" scripts backend --glob '!scripts/router_policy_external_budget_gate.py'` -> no matches
- `rg -n "^import requests|^from requests|^import httpx|^from httpx|openai|anthropic|gemini" scripts` -> existing pre-E4 regex/text references only
- `rg -n "\.env|os\.environ|dotenv|API_KEY|SECRET|TOKEN" scripts tests reports/E4-A4-CONFIRMATION-DECISION-REVALIDATION-BOUNDARY` -> existing test/probe/reference matches only

## Provider / Env / E3 / Schema

- provider/network absence:
  - no provider execution added
  - no network execution added
  - no SDK/API imports added
- `.env` / secrets absence:
  - no `.env` reads added
  - no `os.environ` runtime reads added
  - grep matches are existing probes/tests/patterns, not new secrets handling
- E3 inertness:
  - no production caller for `evaluate_external_budget_gate`
- schema change status:
  - none

## Known Limitations

- A4 validates provided `previous_decision` / `consent_context` state only
- no persistence, retrieval, single-use confirmation ticket storage, or durable confirmation record validation
- schema lacks `input_revalidated`, so A4 rejects input drift rather than modeling explicit revalidation state
- no public confirmation acceptance or execution workflow was added

## Next Recommended Slice

- next recommended slice: `E4-A5 - Confirmed Execution Activation Boundary`

## Final Git Status

- expected A4 dirty files only
