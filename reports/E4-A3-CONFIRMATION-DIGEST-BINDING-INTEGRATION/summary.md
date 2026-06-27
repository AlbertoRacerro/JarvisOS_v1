# E4-A3 - Confirmation Digest Binding Integration

## Verdict

- verdict: `GREEN`
- current HEAD: `a2625cd887236b75134c3babf5f4ec50c4699ff5`

## Changed Files

- production:
  - [router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_canonical_digest.py)
  - [router_policy_decision_probe.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_decision_probe.py)
  - [router_policy_semantic_validator.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_semantic_validator.py)
- tests:
  - [test_router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_canonical_digest.py)
  - [test_router_policy_confirmation_digest_binding.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_confirmation_digest_binding.py)
  - [test_router_policy_semantic_validator.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_semantic_validator.py)
- reports:
  - [summary.md](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A3-CONFIRMATION-DIGEST-BINDING-INTEGRATION/summary.md)
  - [summary.json](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A3-CONFIRMATION-DIGEST-BINDING-INTEGRATION/summary.json)
- schemas:
  - none

## Integration Points

- helper:
  - `canonicalize_confirmation_digest_envelope(...)`
  - `compute_confirmation_digest(...)`
  - `validate_confirmation_digest_integrity(...)`
- public-router path:
  - `_external_candidate_proposal(...)` computes `confirmation_digest` from the bound decision envelope after `confirmation_options` are populated
- validator path:
  - `_check_confirmation_payload(...)` validates digest integrity with the helper and reports violation only
- scrub/finalizer path:
  - reused existing `_external_scope_denied_proposal_only(...)`
  - reused existing `_external_disabled_local_fallback(...)`

## Digest Purpose / Version Binding

- cryptographically bound in digest input:
  - `digest_purpose = "router_confirmation_intent"`
  - `digest_version = "v1"`
- envelope:
  - `{"digest_purpose": "...", "digest_version": "...", "confirmation_intent": <bound payload>}`
- enforced_by:
  - `test_digest_purpose_and_version_are_cryptographically_bound`
  - `test_confirmation_bearing_public_router_proposal_gets_bound_digest`

## Bound Payload

- digest-bound fields:
  - `proposed_external_target`
  - `provider_call_allowed_now`
  - `external_network_allowed_now`
  - `confirmation_required`
  - `confirmation_payload_required`
  - `confirmation_payload`
  - `confirmation_options`
- `confirmation_options` order preserved as semantically meaningful
- enforced_by:
  - `test_canonical_payload_contains_only_digest_relevant_fields`
  - `test_confirmation_options_list_order_is_semantically_meaningful`
  - `test_confirmation_bearing_public_router_proposal_gets_bound_digest`

## Excluded Fields

- excluded:
  - `confirmation_digest`
  - `digest`
  - `route_action`
  - `route_tier`
  - `reason_codes`
  - `audit_notes`
  - `requires_new_decision_after_confirmation`
- enforced_by:
  - `test_digest_excludes_itself`
  - `test_route_action_and_route_tier_are_not_actionability_authority_for_digest`
  - `test_non_safety_explanatory_text_outside_confirmation_payload_does_not_change_digest`
  - `test_requires_new_decision_after_confirmation_is_reserved_for_later_binding`
  - `test_requires_new_decision_after_confirmation_is_lifecycle_only_in_bound_digest`

## Digest Compute Behavior

- confirmation-bearing external proposal gets `confirmation_digest`
- digest recomputes from the bound envelope, not raw `confirmation_payload` alone
- compute happens after `confirmation_options` are set, so option order remains digest-relevant
- digest compute does not set `provider_call_allowed_now=True`
- digest compute does not set `external_network_allowed_now=True`
- enforced_by:
  - `test_confirmation_bearing_public_router_proposal_gets_bound_digest`

## Digest Clear Behavior

- digest clears when target becomes `None`
- digest clears when local/no-external fallback normalizes the decision
- digest clears when existing scrub/finalizer companion-removal logic runs
- no duplicate scrubber was added
- enforced_by:
  - `test_targetless_finalizer_scrubs_digest_and_confirmation_artifacts`
  - `test_local_fallback_clears_digest_without_public_confirmation_flow`
  - existing invariant coverage in [test_router_policy_external_proposal_invariant.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_external_proposal_invariant.py)

## Digest Validation Behavior

- validation is pure integrity check only
- validator returns status only and does not mutate the decision
- digest mismatch fails integrity validation
- digest match validates payload integrity only
- digest match does not grant provider execution
- digest match does not grant network execution
- enforced_by:
  - `test_validate_confirmation_digest_integrity_returns_status_only_and_does_not_mutate`
  - `test_validate_confirmation_digest_integrity_rejects_mismatch_without_granting_permissions`
  - `test_digest_validation_mismatch_blocks_integrity_only_without_mutation`
  - semantic validator reuse in [router_policy_semantic_validator.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_semantic_validator.py)

## Coverage Levels

- compute coverage level: `public-router path`
- clear coverage level: `finalizer-level`
- validate coverage level: `helper-only`
- note:
  - clear also has public-router fallback coverage
  - validate also has contract-layer validator reuse, but no public confirmation acceptance workflow was added

## Lifecycle / Authority

- `requires_new_decision_after_confirmation`:
  - classification: `confirmation_lifecycle_field`
  - handling: lifecycle-only, not digest-bound actionability
- `route_action` / `route_tier`:
  - labels only, not actionability authority
- enforced_by:
  - `test_route_action_and_route_tier_are_not_actionability_authority_for_digest`
  - `test_requires_new_decision_after_confirmation_is_lifecycle_only_in_bound_digest`

## Tests Added

- `tests/test_router_policy_confirmation_digest_binding.py`
  - `test_confirmation_bearing_public_router_proposal_gets_bound_digest`
  - `test_digest_validation_mismatch_blocks_integrity_only_without_mutation`
  - `test_targetless_finalizer_scrubs_digest_and_confirmation_artifacts`
  - `test_local_fallback_clears_digest_without_public_confirmation_flow`
  - `test_requires_new_decision_after_confirmation_is_lifecycle_only_in_bound_digest`
- added helper tests:
  - `test_digest_purpose_and_version_are_cryptographically_bound`
  - `test_validate_confirmation_digest_integrity_returns_status_only_and_does_not_mutate`
  - `test_validate_confirmation_digest_integrity_rejects_mismatch_without_granting_permissions`

## Checks Run

- `python -m pytest tests/test_router_policy_canonical_digest.py -q` -> `14 passed in 0.06s`
- `python -m pytest tests/test_router_policy_confirmation_digest_binding.py -q` -> `5 passed in 0.12s`
- `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_external_egress_scope.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `324 passed in 0.92s`
- `git diff --check` -> CRLF warnings only, no whitespace/content failure
- `git status --short` -> expected A3 touched files plus report
- `rg -n "evaluate_external_budget_gate\(" scripts backend --glob '!scripts/router_policy_external_budget_gate.py'` -> no matches
- `rg -n "^import requests|^from requests|^import httpx|^from httpx|openai|anthropic|gemini" scripts` -> existing pre-E4 regex/text references only

## Provider / E3 / Schema

- provider/network absence:
  - no provider execution added
  - no network execution added
  - no SDK/API imports added
  - no `.env` reads added
- E3 inertness:
  - no production caller for `evaluate_external_budget_gate`
- schema change status:
  - none

## Known Limitations

- no public confirmation acceptance workflow was added
- validation is integrity-only and does not execute or authorize anything
- digest compute coverage is limited to the existing confirmation-bearing external proposal path

## Next Recommended Slice

- next recommended slice: `E4-A4 - Confirmation Decision Revalidation Boundary`
