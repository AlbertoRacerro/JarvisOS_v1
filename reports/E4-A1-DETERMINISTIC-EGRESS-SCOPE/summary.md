# E4-A1 - Deterministic Egress Scope

## Verdict

- verdict: `GREEN`
- scope: deterministic egress scope only
- digest/confirmation binding: out of scope
- provider execution: not added
- E3 production activation: not added
- schema changes: none

## Phase 0 Inspection

- router decision module/function:
  - [router_policy_decision_probe.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_decision_probe.py)
  - `decide_router_policy`
- current finalizer/output normalizer:
  - `_enforce_external_proposal_flag_invariant`
- current router decision schema:
  - [router_policy_decision_v0_3_1_1.schema.json](/C:/Users/thera/Documents/JarvisOS_v1/schemas/router_policy_decision_v0_3_1_1.schema.json)
- current external target enum values:
  - `external:cheap`
  - `external:scientific_medium`
  - `external:frontier`
- current external proposal fields:
  - `proposed_external_target`
  - `external_allowed`
  - `external_network_allowed_now`
  - `provider_call_allowed_now`
  - `confirmation_required`
  - `confirmation_payload_required`
  - `confirmation_payload`
  - `confirmation_digest`
  - `confirmation_options`
- current egress/scope/provider policy fields:
  - input `provider_policy.allowed_provider_tiers`
  - input `provider_policy.blocked_provider_tiers`
  - input `budget_policy.max_tier`
  - no existing allowed-target field in input schema
- existing schema validation helper:
  - local validator pattern reused in test file
- existing tests extended, not replaced:
  - [tests/test_router_policy_external_proposal_invariant.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_external_proposal_invariant.py)
  - [tests/test_router_policy_message_route_smoke.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_message_route_smoke.py)
  - [tests/test_router_policy_semantic_validator.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_semantic_validator.py)
  - [tests/test_router_policy_external_egress_gate.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_external_egress_gate.py)
  - [tests/test_router_policy_external_budget_gate.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_external_budget_gate.py)
- schema changes avoidable: yes
- E3 remains inert: yes

## Changed Files

- production files changed:
  - [router_policy_external_egress_scope.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_external_egress_scope.py)
  - [router_policy_decision_probe.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_decision_probe.py)
- test files changed:
  - [test_router_policy_external_egress_scope.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_external_egress_scope.py)
- schema files changed:
  - none
- report files changed:
  - [summary.md](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A1-DETERMINISTIC-EGRESS-SCOPE/summary.md)
  - [summary.json](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A1-DETERMINISTIC-EGRESS-SCOPE/summary.json)

## E4-A1 State Table

- state 1: `external_routing_enabled is not exactly True`
  - `proposed_external_target = None`
  - `external_allowed = False`
  - `external_network_allowed_now = False`
  - `provider_call_allowed_now = False`
  - `confirmation_required = False`
  - `confirmation_payload_required = False`
  - `confirmation_payload = None`
  - `confirmation_digest = None`
  - `confirmation_options = []`
  - public-path enforced_by:
    - `test_e4_a1_public_flag_not_exactly_true_still_scrubs_all_external_artifacts`
    - locked regression:
      - `test_forced_bundle_finalizer_scrubs_not_exactly_true_flags`
      - `test_forced_budget_or_policy_fallback_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed`
      - `test_forced_private_provider_boundary_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed`
- state 2: `external_routing_enabled is exactly True + egress denied`
  - current repo-compatible behavior:
    - `proposed_external_target` remains visible as non-actionable proposal
    - `external_allowed = False`
    - `external_network_allowed_now = False`
    - `provider_call_allowed_now = False`
    - `confirmation_required = False`
    - `confirmation_payload_required = False`
    - `confirmation_payload = None`
    - `confirmation_digest = None`
    - `confirmation_options = []`
  - public-path enforced_by:
    - `test_e4_a1_public_flag_true_egress_denied_keeps_visible_proposal_but_clears_confirmation`
- state 3: `external_routing_enabled is exactly True + egress allowed + no explicit confirmation mechanism`
  - current repo-compatible narrower variant:
    - `proposed_external_target = valid target`
    - `external_allowed = False`
    - `external_network_allowed_now = False`
    - `provider_call_allowed_now = False`
    - `confirmation_required = False`
    - `confirmation_payload_required = False`
    - `confirmation_payload = None`
    - `confirmation_digest = None`
    - `confirmation_options = []`
  - reason for narrower variant:
    - current semantic validator treats `external_allowed=True` as an executable external-candidate state, so E4-A1 keeps public outputs proposal-only
  - public-path enforced_by:
    - `test_e4_a1_public_flag_true_egress_allowed_remains_proposal_only_without_new_confirmation`

## Helper Behavior

- helper:
  - [router_policy_external_egress_scope.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_external_egress_scope.py)
  - `evaluate_external_egress_scope(proposed_external_target, allowed_targets)`
- helper properties:
  - deterministic
  - side-effect-free
  - no env vars
  - no remote config
  - no provider registry
  - no API keys
  - no network resources
  - no model output consumed directly
- helper behavior:
  - `None target -> denied`
  - `invalid target -> denied`
  - `valid target not in allowed_targets -> denied`
  - `valid target in allowed_targets -> allowed`
  - `empty allowed_targets -> denied`
  - `allowed_targets` order changes -> same result
- helper-only enforced_by:
  - `test_e4_a1_helper_none_target_denied`
  - `test_e4_a1_helper_invalid_target_denied`
  - `test_e4_a1_helper_valid_target_not_in_allowed_targets_denied`
  - `test_e4_a1_helper_valid_target_in_allowed_targets_allowed`
  - `test_e4_a1_helper_empty_allowed_targets_denied`
  - `test_e4_a1_helper_allowed_targets_order_does_not_change_result`

## Public Behavior

- public denied-target behavior:
  - deterministic egress denial does not make the target actionable
  - existing visible proposal may remain visible under flag `True`
  - stale confirmation metadata is cleared on deny
  - public-path enforced_by:
    - `test_e4_a1_public_flag_true_egress_denied_keeps_visible_proposal_but_clears_confirmation`
- public allowed-target behavior:
  - deterministic egress allow preserves proposal visibility only
  - no provider execution permission is introduced
  - no external network permission is introduced
  - no new confirmation metadata is introduced by E4-A1
  - public-path enforced_by:
    - `test_e4_a1_public_flag_true_egress_allowed_remains_proposal_only_without_new_confirmation`

## Locked Invariants Preserved

- locked invariant tests preserved:
  - `tests/test_router_policy_external_proposal_invariant.py`
  - `tests/test_router_policy_message_route_smoke.py`
  - `tests/test_router_policy_semantic_validator.py`
  - `tests/test_router_policy_external_egress_gate.py`
  - `tests/test_router_policy_external_budget_gate.py`
- enforced_by checks:
  - `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q`

## Provider Execution Absence

- no provider execution path added
- no external network execution path added
- `provider_call_allowed_now` remains `False` in all E4-A1 public outputs covered here
- `external_network_allowed_now` remains `False` in all E4-A1 public outputs covered here
- public-path enforced_by:
  - `test_e4_a1_public_flag_not_exactly_true_still_scrubs_all_external_artifacts`
  - `test_e4_a1_public_flag_true_egress_denied_keeps_visible_proposal_but_clears_confirmation`
  - `test_e4_a1_public_flag_true_egress_allowed_remains_proposal_only_without_new_confirmation`

## E3 Inertness

- `evaluate_external_budget_gate` still has no production caller
- E3 remains inert
- checked by:
  - diff-scoped grep in production/test/report changed files
  - repo grep for `evaluate_external_budget_gate` production usage

## Schema Validation

- schema validation method:
  - local validator in [test_router_policy_external_egress_scope.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_external_egress_scope.py)
- schema constructs used:
  - `type`
  - `const`
  - `enum`
  - `minLength`
  - `maxLength`
  - `pattern`
  - `minimum`
  - `minItems`
  - `uniqueItems`
  - `items`
  - `properties`
  - `required`
  - `additionalProperties`
- coverage:
  - complete for the currently used router decision schema constructs
- enforced_by:
  - `test_e4_a1_public_flag_not_exactly_true_still_scrubs_all_external_artifacts`
  - `test_e4_a1_public_flag_true_egress_denied_keeps_visible_proposal_but_clears_confirmation`
  - `test_e4_a1_public_flag_true_egress_allowed_remains_proposal_only_without_new_confirmation`

## Checks Run

- `python -m pytest tests/test_router_policy_external_egress_scope.py -q`
- `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q`
- `git diff --check`
- `git status --short`

## Test Names Added

- `test_e4_a1_helper_none_target_denied`
- `test_e4_a1_helper_invalid_target_denied`
- `test_e4_a1_helper_valid_target_not_in_allowed_targets_denied`
- `test_e4_a1_helper_valid_target_in_allowed_targets_allowed`
- `test_e4_a1_helper_empty_allowed_targets_denied`
- `test_e4_a1_helper_allowed_targets_order_does_not_change_result`
- `test_e4_a1_public_flag_not_exactly_true_still_scrubs_all_external_artifacts`
- `test_e4_a1_public_flag_true_egress_denied_keeps_visible_proposal_but_clears_confirmation`
- `test_e4_a1_public_flag_true_egress_allowed_remains_proposal_only_without_new_confirmation`

## Known Limitations

- E4-A1 does not make any external target executable.
- E4-A1 keeps current public router behavior proposal-only because `external_allowed=True` is still bound to executable-route semantics in the current validator.
- E4-A1 does not implement digest binding.
- E4-A1 does not implement confirmation payload binding validation.
- E4-A1 does not activate E3 production budget/session enforcement.
- E4-A1 does not add schema fields for explicit scope-allowed-but-not-executable state.

## Out Of Scope

- why digest/confirmation binding is out of scope:
  - reserved for later slices
  - not needed to prove deterministic target-scope evaluation
- not implemented:
  - canonical digest helper
  - confirmation payload binding
  - provider execution
  - external network calls
  - E3 production activation

## Next Slice

- next recommended slice: `E4-A2 - Canonical Digest Helper`

## E4-A1-R1 - Natural Provider+Budget Egress Deny Coverage

- verdict: `GREEN`
- changed files:
  - [router_policy_decision_probe.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_decision_probe.py)
  - [test_router_policy_external_egress_scope.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_external_egress_scope.py)
  - [summary.md](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A1-DETERMINISTIC-EGRESS-SCOPE/summary.md)
  - [summary.json](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A1-DETERMINISTIC-EGRESS-SCOPE/summary.json)
- production patch:
  - `_allowed_external_targets(input_obj)` now excludes tiers that fail `_budget_allows(input_obj, tier)`
  - no schema change
  - no `evaluate_external_budget_gate` production call
- tests added:
  - `test_e4_a1_public_flag_true_natural_egress_denied_by_provider_policy`
  - `test_e4_a1_public_flag_true_natural_egress_denied_by_budget_policy`
- forced/helper-deny secondary coverage:
  - `test_e4_a1_forced_helper_deny_keeps_visible_proposal_but_clears_confirmation`

## Natural Deny Coverage

- natural provider-policy deny coverage:
  - provider policy excludes `SCIENTIFIC_MEDIUM`
  - budget still allows `SCIENTIFIC_MEDIUM`
  - helper spy calls real `evaluate_external_egress_scope`
  - `allowed_targets` excludes `external:scientific_medium`
  - real helper returns `allowed=False`
  - final output remains non-actionable and schema-valid
  - enforced_by:
    - `test_e4_a1_public_flag_true_natural_egress_denied_by_provider_policy`
- natural budget-policy deny coverage:
  - provider policy allows `SCIENTIFIC_MEDIUM`
  - budget `max_tier = LOCAL_FAST` denies `SCIENTIFIC_MEDIUM`
  - helper spy calls real `evaluate_external_egress_scope`
  - `allowed_targets` excludes `external:scientific_medium`
  - real helper returns `allowed=False`
  - final output remains non-actionable and schema-valid
  - enforced_by:
    - `test_e4_a1_public_flag_true_natural_egress_denied_by_budget_policy`
- helper-deny monkeypatch test classification:
  - secondary finalizer-reaction coverage only
  - not counted as natural provider/budget deny proof
  - enforced_by:
    - `test_e4_a1_forced_helper_deny_keeps_visible_proposal_but_clears_confirmation`

## Budget-Tier Semantics / Parity

- `_allowed_external_targets` now reuses existing `_budget_allows(input_obj, tier)` semantics directly
- no second tier-ordering implementation added
- parity evidence:
  - provider-allow + budget-deny case excludes denied target from `allowed_targets`
  - enforced_by:
    - `test_e4_a1_public_flag_true_natural_egress_denied_by_budget_policy`

## E3 / Provider / Schema

- E3 inertness status:
  - `evaluate_external_budget_gate` still has no production caller
- provider/network execution absence:
  - no provider execution added
  - no network execution added
  - no provider/network SDK imports added in router path
- schema change status:
  - none

## Backlog Before E4-A2

- targetless companion artifact backlog:
  - before or during E4-A2, harden/test:
    - `proposed_external_target = None`
    - `provider_call_allowed_now = True`
    - `external_network_allowed_now = True`
    - `confirmation_payload_required = True`
    - `confirmation_payload != None`
    - `confirmation_digest != None`
    - `confirmation_options` non-empty
- route_action ambiguity note:
  - denied path can still emit `route_action = ask_user_confirm` / `route_tier = USER_CONFIRM` while all actionability flags are false
  - downstream must not use `route_action` alone as actionability source of truth

## E4-A1-R1 Checks

- `python -m pytest tests/test_router_policy_external_egress_scope.py -q` -> `14 passed in 0.19s`
- `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `303 passed in 0.97s`

## E4-A1-R2 - Targetless Companion Artifact Scrub

- verdict: `GREEN`
- changed files:
  - [router_policy_decision_probe.py](/C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_decision_probe.py)
  - [test_router_policy_external_proposal_invariant.py](/C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_external_proposal_invariant.py)
  - [summary.md](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A1-DETERMINISTIC-EGRESS-SCOPE/summary.md)
  - [summary.json](/C:/Users/thera/Documents/JarvisOS_v1/reports/E4-A1-DETERMINISTIC-EGRESS-SCOPE/summary.json)
- production patch:
  - added `_has_live_external_companion_artifacts(decision)`
  - `_enforce_external_proposal_flag_invariant(...)` now scrubs live targetless companion artifacts for both flag-not-exactly-True and flag-exactly-True paths
- production patch reason:
  - `proposed_external_target is None` previously bypassed scrub even when companion artifacts were live
- schema changes:
  - none
- tests added:
  - `test_targetless_companion_finalizer_scrubs_not_exactly_true_flags`
  - `test_targetless_companion_finalizer_scrubs_even_when_flag_true`
  - `test_clean_targetless_finalizer_no_op_preserves_local_internal_fields`
  - `test_targetless_companion_budget_fallback_public_output_scrubbed_when_external_flag_not_true_and_forced_return_consumed`

## Direct Finalizer Targetless Companion Scrub

- flag_not_exactly_true_cases:
  - `False`
  - `None`
  - `"true"`
  - `1`
- targetless_dirty_input_classification:
  - adversarial_pre_finalizer: true
  - final_input_schema_valid_required: false
  - final_output_schema_valid_required: true
- enforced_by:
  - `test_targetless_companion_finalizer_scrubs_not_exactly_true_flags`

## Flag True Targetless Behavior

- expected behavior:
  - `external_routing_enabled=True` alone is not sufficient
  - valid target + deterministic allowed scope required before external confirmation/provider artifacts may survive
- enforced_by:
  - `test_targetless_companion_finalizer_scrubs_even_when_flag_true`

## Public/Integration Targetless Companion Scrub

- status:
  - covered
- boundary tested:
  - `_budget_or_policy_fallback`
- forced return consumption proof:
  - yes
- safe sentinel used:
  - `max_tokens_allowed = 1337`
- limitation if no public sentinel:
  - none on current path
- enforced_by:
  - `test_targetless_companion_budget_fallback_public_output_scrubbed_when_external_flag_not_true_and_forced_return_consumed`

## Clean Targetless No-Op / Preserve

- status:
  - covered
- preserved local/internal fields:
  - `manual_review_required = True`
  - `route_action = route_local`
  - `route_tier = LOCAL_ONLY`
  - `reason_codes = ["local_only_sensitive_context"]`
  - `redaction_required = False`
  - `redaction_status = "not_required"`
- no external artifact introduced:
  - yes
- schema-valid final output:
  - yes
- enforced_by:
  - `test_clean_targetless_finalizer_no_op_preserves_local_internal_fields`

## Redaction/Local Field Classification

- redaction_required:
  - classification: dual-use local safety
  - included_in_bundle: false
  - reason: used by local secret/provider-boundary safety, not targetless external companion-only artifact
- redaction_status:
  - classification: dual-use local safety
  - included_in_bundle: false
  - reason: used by local secret/provider-boundary safety, not targetless external companion-only artifact

## E3 / Provider / Schema

- E3 inertness status:
  - `evaluate_external_budget_gate` still has no production caller
- provider/network absence:
  - no provider execution added
  - no network execution added
  - no provider/network SDK imports added in router path
- schema change status:
  - none
- digest helper added:
  - no
- confirmation binding added:
  - no

## R2 Checks Run

- `python -m pytest tests/test_router_policy_external_proposal_invariant.py -q` -> `74 passed in 0.15s`
- `python -m pytest tests/test_router_policy_external_egress_scope.py -q` -> `14 passed in 0.04s`
- `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_external_egress_scope.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `324 passed in 0.30s`
- `git diff --check` -> warnings only, LF/CRLF normalization notices for touched files
- `git status --short` -> dirty worktree remains, including pre-existing `docs/DECISIONS.md`

## R2 Known Limitations

- R2 does not implement digest helper.
- R2 does not implement confirmation payload binding.
- R2 does not activate E3.
- R2 does not add provider execution.
- Route action/tier alone remain non-authoritative for actionability.

## R2 Next Step

Next step:
  E4-A2 - Canonical Digest Helper

Precondition satisfied:
  targetless companion artifact scrub
