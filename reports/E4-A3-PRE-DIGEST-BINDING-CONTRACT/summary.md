# E4-A3-PRE - Digest Binding Contract

## Verdict

- verdict: `GREEN`
- milestone: `E4-A3-PRE-DIGEST-BINDING-CONTRACT`
- scope: `digest_binding_contract_report_only_by_default`
- E4-A2 commit hash: `691878209c792ee715d9893db10aac0734aa1dee`
- current HEAD: `691878209c792ee715d9893db10aac0734aa1dee`

## Changed Files

- reports:
  - [summary.md](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A3-PRE-DIGEST-BINDING-CONTRACT/summary.md)
  - [summary.json](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A3-PRE-DIGEST-BINDING-CONTRACT/summary.json)
- production:
  - none
- tests:
  - none
- schemas:
  - none
- docs:
  - none

## Digest Purpose / Version

- decision:
  - `digest_purpose = "router_confirmation_intent"`
  - `digest_version = "v1"`
  - explicit before runtime binding
- rationale:
  - future semantic changes must not silently reuse an old digest contract
- evidence:
  - [router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_canonical_digest.py)
  - report-only A3-PRE contract decision

## Bound Payload

- exact digest-bound payload for future binding:
  - `proposed_external_target`
  - `provider_call_allowed_now`
  - `external_network_allowed_now`
  - `confirmation_required`
  - `confirmation_payload_required`
  - `confirmation_payload`
  - `confirmation_options`
- rationale:
  - these are the E4-A2 helper whitelist fields and the only fields that express confirmation intent/actionability
- evidence:
  - [router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_canonical_digest.py)

## Excluded Fields

- explicitly excluded:
  - `confirmation_digest`
  - `digest`
  - `route_action`
  - `route_tier`
  - `reason_codes`
  - `audit_notes`
  - `requires_new_decision_after_confirmation`
- rationale:
  - digest fields must not hash themselves
  - route labels are not authority
  - explanatory fields are not bound intent
  - `requires_new_decision_after_confirmation` is lifecycle state, not bound actionability in PRE
- evidence:
  - [router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_canonical_digest.py)
  - [test_router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_canonical_digest.py)
    - `test_digest_excludes_itself`
    - `test_route_action_and_route_tier_are_not_actionability_authority_for_digest`
    - `test_requires_new_decision_after_confirmation_is_reserved_for_later_binding`
    - `test_non_safety_explanatory_text_outside_confirmation_payload_does_not_change_digest`

## Actionability Authority

- authority fields only:
  - `provider_call_allowed_now`
  - `external_network_allowed_now`
  - `confirmation_required`
  - `confirmation_payload_required`
  - `confirmation_payload`
  - `confirmation_digest`
  - `confirmation_options`
- non-authority labels:
  - `route_action`
  - `route_tier`
- hard rule:
  - digest integrity does not grant provider execution
  - digest integrity does not grant network execution
  - digest integrity does not activate E3

## requires_new_decision_after_confirmation

- classification:
  - `confirmation_lifecycle_field`
- digest relevance:
  - `controlled_separately_as_lifecycle_state`
- rationale:
  - PRE contract keeps bound intent separate from post-confirmation decision lifecycle
  - blind preservation would conflate integrity with workflow state
- evidence:
  - [test_router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_canonical_digest.py)
    - `test_requires_new_decision_after_confirmation_is_reserved_for_later_binding`

## Invalidation Rules

- recompute digest if any bound field changes:
  - `proposed_external_target`
  - `provider_call_allowed_now`
  - `external_network_allowed_now`
  - `confirmation_required`
  - `confirmation_payload_required`
  - `confirmation_payload`
  - `confirmation_options`
- clear digest instead of recomputing when:
  - `proposed_external_target` becomes `None` or empty
  - confirmation is no longer required
  - finalizer or scrubber removes external companion artifacts
  - decision normalizes to local/no-external fallback
- future version rule:
  - if `digest_purpose` or `digest_version` changes, old digest must not be trusted and must be recomputed under the new contract

## Writer / Reader Boundary

- writer boundary:
  - future external-confirmation finalizer/helper may compute digest when a decision is in a confirmation-bearing external-proposal state
  - future scrubber/fallback normalizer must clear digest when the decision is targetless or local/no-external
- reader boundary:
  - future confirmation validator may compare stored digest against recomputed digest before accepting a confirmation payload
- non-reader boundary:
  - router selection
  - provider execution path
  - network execution path
  - E3 budget gate
- hard rule:
  - digest proves payload integrity only
  - digest is not execution permission

## Checks Run

- E4-A2 closure:
  - `git status --short` before commit -> only `scripts/router_policy_canonical_digest.py`, `tests/test_router_policy_canonical_digest.py`, `reports/E4-A2-CANONICAL-DIGEST-HELPER/`
  - `python -m pytest tests/test_router_policy_canonical_digest.py -q` -> `11 passed in 0.06s`
  - `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_external_egress_scope.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `324 passed in 0.99s`
  - `git diff --check` -> clean
  - `git commit -m "Add canonical confirmation digest helper"` -> `691878209c792ee715d9893db10aac0734aa1dee`
- A3-PRE verification:
  - `python -m pytest tests/test_router_policy_canonical_digest.py -q`
  - `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_external_egress_scope.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q`
  - `git diff --check`
  - `git status --short`
  - `rg -n "evaluate_external_budget_gate\(" scripts backend --glob '!scripts/router_policy_external_budget_gate.py'`
  - `rg -n "^import requests|^from requests|^import httpx|^from httpx|openai|anthropic|gemini" scripts`

## Grep Matches Classified

- `rg -n "evaluate_external_budget_gate\(" scripts backend --glob '!scripts/router_policy_external_budget_gate.py'`
  - no matches
  - classification: `no production E3 caller`
- `rg -n "^import requests|^from requests|^import httpx|^from httpx|openai|anthropic|gemini" scripts`
  - `scripts/local_policy_gate_overlay_probe.py`
    - classification: `existing pre-E4 reference`
    - reason: regex vocabulary only, not provider/network import or execution
  - `scripts/router_policy_message_route_smoke.py`
    - classification: `existing pre-E4 reference`
    - reason: regex vocabulary only, not provider/network import or execution

## Provider / E3 / Schema

- provider/network absence:
  - no provider execution added
  - no network execution added
  - no SDK/API imports added
- E3 inertness:
  - no production caller for `evaluate_external_budget_gate`
- schema changes:
  - none

## Known Limitations

- report-only PRE contract; no runtime writer/reader integration
- no digest purpose/version constants added to production code yet
- no runtime validator/finalizer exists yet to enforce the contract
- `requires_new_decision_after_confirmation` remains intentionally outside digest-bound authority

## Next Recommended Slice

- next recommended slice: `E4-A3 - Confirmation Digest Binding Integration`
