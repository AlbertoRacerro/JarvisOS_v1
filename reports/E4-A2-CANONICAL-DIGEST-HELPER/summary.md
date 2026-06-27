# E4-A2 - Canonical Digest Helper

## Verdict

- verdict: `GREEN`
- current HEAD: `162d182356a0440217aff0dfd794e442a078b287`
- docs/DECISIONS.md stash:
  - reference: `stash@{0}: On audit/safe-fixes-2026-06-23: baseline-cleanup docs/DECISIONS.md`
  - hash: `7518aae68a76612c524b13f0f462c58268687cc6`

## Changed Files

- production:
  - [router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_canonical_digest.py)
- tests:
  - [test_router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_canonical_digest.py)
- reports:
  - [summary.md](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A2-CANONICAL-DIGEST-HELPER/summary.md)
  - [summary.json](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A2-CANONICAL-DIGEST-HELPER/summary.json)
- schemas:
  - none

## Helper

- helper file/function:
  - [router_policy_canonical_digest.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_canonical_digest.py)
  - `canonicalize_confirmation_intent`
  - `compute_confirmation_digest`
- properties:
  - pure
  - deterministic
  - side-effect-free
  - standard library only
  - no env
  - no network
  - no filesystem writes
  - no model calls
- enforced_by:
  - `test_helper_uses_no_runtime_entropy_or_external_state`

## Canonicalization Rules

- `json.dumps(..., sort_keys=True, separators=(",", ":"))`
- digest excludes existing digest fields:
  - `confirmation_digest`
  - `digest`
- nested dict keys sorted deterministically
- list order preserved
- no timestamps
- no randomness
- no UUIDs
- no object IDs
- no environment dependence
- enforced_by:
  - `test_same_canonical_safety_intent_gives_same_digest_despite_key_order`
  - `test_stable_nested_ordering_inside_digest_relevant_payload`
  - `test_digest_excludes_itself`
  - `test_helper_uses_no_runtime_entropy_or_external_state`

## Included Digest Fields

- `proposed_external_target`
- `provider_call_allowed_now`
- `external_network_allowed_now`
- `confirmation_required`
- `confirmation_payload_required`
- `confirmation_payload`
- `confirmation_options`
- rationale:
  - these fields directly express confirmation/actionability intent without binding workflow execution
- enforced_by:
  - `test_canonical_payload_contains_only_digest_relevant_fields`
  - `test_different_safety_relevant_target_changes_digest`
  - `test_different_confirmation_payload_changes_digest`
  - `test_confirmation_options_list_order_is_semantically_meaningful`

## Excluded Digest Fields

- `confirmation_digest`
- `digest`
- `route_action`
- `route_tier`
- `requires_new_decision_after_confirmation`
- `reason_codes`
- `audit_notes`
- rationale:
  - existing digest fields must not feed themselves
  - `route_action` / `route_tier` are labels, not actionability authority
  - `requires_new_decision_after_confirmation` is a confirmation lifecycle field and is reserved for later binding
  - `reason_codes` / `audit_notes` are explanatory, not digest-critical here
- enforced_by:
  - `test_digest_excludes_itself`
  - `test_non_safety_explanatory_text_outside_confirmation_payload_does_not_change_digest`
  - `test_route_action_and_route_tier_are_not_actionability_authority_for_digest`
  - `test_requires_new_decision_after_confirmation_is_reserved_for_later_binding`

## route_action / route_tier Classification

- `route_action`: label, not actionability authority
- `route_tier`: label, not actionability authority
- digest relevance:
  - excluded unless intentionally added later as display-only payload content
- enforced_by:
  - `test_route_action_and_route_tier_are_not_actionability_authority_for_digest`

## requires_new_decision_after_confirmation Classification

- classification:
  - confirmation lifecycle field
- digest relevance:
  - reserved for later confirmation binding
- rationale:
  - E4-A2 is helper-only and does not implement confirmation workflow/binding
- enforced_by:
  - `test_requires_new_decision_after_confirmation_is_reserved_for_later_binding`

## List Ordering Semantics

- `confirmation_options` treated as semantically ordered
- order changes digest
- rationale:
  - current runtime does not prove unordered semantics; preserving order is the safer default
- enforced_by:
  - `test_confirmation_options_list_order_is_semantically_meaningful`

## Tests Added

- `test_same_canonical_safety_intent_gives_same_digest_despite_key_order`
- `test_different_safety_relevant_target_changes_digest`
- `test_different_confirmation_payload_changes_digest`
- `test_non_safety_explanatory_text_outside_confirmation_payload_does_not_change_digest`
- `test_digest_excludes_itself`
- `test_stable_nested_ordering_inside_digest_relevant_payload`
- `test_confirmation_options_list_order_is_semantically_meaningful`
- `test_helper_uses_no_runtime_entropy_or_external_state`
- `test_route_action_and_route_tier_are_not_actionability_authority_for_digest`
- `test_requires_new_decision_after_confirmation_is_reserved_for_later_binding`
- `test_canonical_payload_contains_only_digest_relevant_fields`

## Checks Run

- `git rev-parse stash@{0}` -> `7518aae68a76612c524b13f0f462c58268687cc6`
- `git status --short` before work -> clean
- `git rev-parse HEAD` -> `162d182356a0440217aff0dfd794e442a078b287`
- `python -m pytest tests/test_router_policy_canonical_digest.py -q` -> `11 passed in 0.08s`
- `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_external_egress_scope.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `324 passed in 1.07s`
- `git diff --check` -> clean
- `git status --short` -> `?? scripts/router_policy_canonical_digest.py`, `?? tests/test_router_policy_canonical_digest.py`, `?? reports/E4-A2-CANONICAL-DIGEST-HELPER/`
- `rg -n "evaluate_external_budget_gate\(" scripts backend --glob '!scripts/router_policy_external_budget_gate.py'` -> no matches
- `rg -n "^import requests|^from requests|^import httpx|^from httpx|openai|anthropic|gemini" scripts/router_policy_decision_probe.py scripts/router_policy_external_egress_scope.py scripts/router_policy_canonical_digest.py` -> no matches

## Locked Suite Status

- locked suite status: `GREEN`
- result:
  - `324 passed in 1.07s`

## E3 / Provider / Schema

- provider/network absence:
  - no provider execution added
  - no network execution added
  - no SDK/API imports added
- E3 inertness:
  - no production caller for `evaluate_external_budget_gate`
- schema change status:
  - none

## Known Limitations

- helper-only milestone; no confirmation binding integration
- helper excludes lifecycle labels and explanatory fields by design
- helper preserves list order rather than imposing set semantics

## Next Recommended Slice

- next recommended slice: `E4-A3 - Confirmation Payload Binding Integration`
