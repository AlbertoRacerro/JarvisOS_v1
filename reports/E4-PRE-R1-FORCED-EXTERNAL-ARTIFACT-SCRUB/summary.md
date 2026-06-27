# E4-PRE-R1 - Forced External Artifact Scrub Coverage

## Scope

- milestone: `E4-PRE-R1 - Forced External Artifact Scrub Coverage`
- starting_head: `a852c5916026556aa641b1e9f14f32483103633b`
- production_patch_required: false
- production_patch_reason: none
- router_module_path: [router_policy_decision_probe.py](C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_decision_probe.py)
- schema_path: [router_policy_decision_v0_3_1_1.schema.json](C:/Users/thera/Documents/JarvisOS_v1/schemas/router_policy_decision_v0_3_1_1.schema.json)
- valid_test_external_target_value: `external:scientific_medium`

## Forced Bundle

- forced_external_artifact_bundle_fields:
  - `proposed_external_target`
  - `external_allowed`
  - `external_network_allowed_now`
  - `provider_call_allowed_now`
  - `confirmation_required`
  - `confirmation_payload_required`
  - `confirmation_payload`
  - `confirmation_digest`
  - `confirmation_options`
- bundle source:
  - runtime-valid sample derived from current valid external proposal path through `_external_candidate_proposal`
- redaction_field_classification:
  - `redaction_required`: dual-use local safety, excluded from global forced bundle
  - `redaction_status`: dual-use local safety, excluded from global forced bundle
  - focused external-artifact assertion retained on `_private_provider_boundary` forced scrub path
- external_artifact_candidate_field_audit:
  - `manual_review_required`: dual-use local safety, excluded
  - `manual_review_reason`: absent
  - `external_provider`: absent
  - `external_model`: absent
  - `provider_target`: absent
  - `routing_target`: absent
  - `network_allowed`: absent
  - `egress_*`: absent
  - `budget_class`, `max_tokens_allowed`: present but unrelated to external proposal artifact scrub

## Finalizer

- finalizer_returns_complete_decision: true
- direct_finalizer_schema_validation_applied: true
- schema_validation_reason: `_enforce_external_proposal_flag_invariant` returns complete router decision dicts
- direct_finalizer_adversarial_tests:
  - `test_forced_bundle_finalizer_scrubs_not_exactly_true_flags`
  - `test_forced_bundle_finalizer_preserves_valid_target_when_flag_true`
- direct_finalizer_not_exactly_true_cases:
  - `False`
  - `None`
  - `"true"`
  - `1`
- direct_finalizer_positive_preserve_result:
  - valid target preserved under exact `True`

## Integration

- integration_forced_scrub_producers:
  - `_budget_or_policy_fallback`
  - `_private_provider_boundary`
- integration_forced_scrub_not_exactly_true_cases:
  - `False`
  - `None`
  - `"true"`
  - `1`
- integration_forced_scrub_results:
  - `_budget_or_policy_fallback`:
    - status: covered
    - outcome: accepted + reached, forced bundle observed before return, final output fully scrubbed, schema-valid
    - enforced_by:
      - `test_forced_budget_or_policy_fallback_bundle_scrubbed_when_external_flag_not_true`
  - `_private_provider_boundary`:
    - status: covered
    - outcome: accepted + reached, forced bundle observed before return, final output fully scrubbed, schema-valid, redaction cleared
    - enforced_by:
      - `test_forced_private_provider_boundary_bundle_scrubbed_when_external_flag_not_true`
- integration_positive_preserve_producers:
  - `_budget_or_policy_fallback`
  - `_private_provider_boundary`
  - `_unknown_external_pressure`
  - `_external_candidate_proposal`
- integration_positive_preserve_results:
  - `_budget_or_policy_fallback`:
    - status: covered
    - enforced_by:
      - `test_forced_budget_or_policy_fallback_bundle_preserved_when_external_flag_true`
  - `_private_provider_boundary`:
    - status: covered
    - enforced_by:
      - `test_forced_private_provider_boundary_bundle_preserved_when_external_flag_true`
  - `_unknown_external_pressure`:
    - status: covered
    - enforced_by:
      - `test_forced_unknown_external_pressure_bundle_preserved_when_external_flag_true`
  - `_external_candidate_proposal`:
    - status: covered
    - enforced_by:
      - `test_forced_external_candidate_bundle_preserved_when_external_flag_true`

## Validation

- schema_validation_result:
  - direct finalizer outputs validated by:
    - `test_forced_bundle_finalizer_scrubs_not_exactly_true_flags`
    - `test_forced_bundle_finalizer_preserves_valid_target_when_flag_true`
  - public integration outputs validated by:
    - `test_forced_budget_or_policy_fallback_bundle_scrubbed_when_external_flag_not_true`
    - `test_forced_private_provider_boundary_bundle_scrubbed_when_external_flag_not_true`
    - `test_forced_budget_or_policy_fallback_bundle_preserved_when_external_flag_true`
    - `test_forced_private_provider_boundary_bundle_preserved_when_external_flag_true`
    - `test_forced_unknown_external_pressure_bundle_preserved_when_external_flag_true`
    - `test_forced_external_candidate_bundle_preserved_when_external_flag_true`
- no_provider_e3_e4_wiring_check:
  - pre-commit diff-scoped inspection limited to R1 changed files found no production `evaluate_external_budget_gate` call, no provider client code, and no external/network execution wiring

## Checks

- tests/checks run:
  - `python -m pytest tests/test_router_policy_external_proposal_invariant.py -q` -> `67 passed in 0.37s`
  - `python -m pytest tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `236 passed in 0.75s`
  - `git diff --check` -> warnings only, LF/CRLF normalization notices for `tests/test_router_policy_external_proposal_invariant.py`, `reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/summary.md`, and `reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/summary.json`
  - `git status --short` -> ` M reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/summary.json`, ` M reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/summary.md`, ` M tests/test_router_policy_external_proposal_invariant.py`, `?? reports/E2-EXTERNAL-ROUTING-FLAG-GOVERNANCE/changed_files.zip`, `?? reports/E3-EXTERNAL-BUDGET-SESSION-GATE/changed_files.zip`, `?? reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/changed_files.zip`, `?? reports/E4-PRE-ROUTER-EXTERNAL-PROPOSAL-INVARIANT/changed_files.zip`

## Known Limitations

- R1 validates forced artifacts for current discovered producer paths, not undiscovered future producer construction patterns.
- R1 depends on representative trigger inputs reaching the intended producers.
- R1 does not implement E4.
- E4 still requires cumulative egress scope, digest/confirmation, provider policy, and E3 re-validation.

## E4-PRE-R1.1 - Forced Return Consumption Proof

- r1_1_status: `GREEN`
- starting_head: `872077e6077bc32c49b4c85756776d0faf2a8576`
- final_head: recorded in post-commit handoff
- production_patch_required: false
- production_patch_reason: none
- files_changed:
  - [tests/test_router_policy_external_proposal_invariant.py](C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_external_proposal_invariant.py)
  - [summary.md](C:/Users/thera/Documents/JarvisOS_v1/reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/summary.md)
  - [summary.json](C:/Users/thera/Documents/JarvisOS_v1/reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/summary.json)

## Forced Return Consumption

- scrub_after_producers_covered:
  - `_budget_or_policy_fallback`: returned-object path covered directly by `test_budget_or_policy_fallback_flag_off_sentinel_baseline_survives_public_output` and `test_forced_budget_or_policy_fallback_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed`
  - `_private_provider_boundary`: returned-object path covered directly by `test_private_provider_boundary_flag_off_sentinel_baseline_survives_public_output` and `test_forced_private_provider_boundary_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed`
- not_exactly_true_cases_attempted:
  - `False`
  - `None`
  - `"true"`
  - `1`
- integration_outcome_classification_by_case:
  - `_budget_or_policy_fallback`:
    - `False`: accepted + reached
    - `None`: accepted + reached
    - `"true"`: accepted + reached
    - `1`: accepted + reached
  - `_private_provider_boundary`:
    - `False`: accepted + reached
    - `None`: accepted + reached
    - `"true"`: accepted + reached
    - `1`: accepted + reached

## Sentinel

- sentinel_field: `max_tokens_allowed`
- sentinel_value: `1337`
- sentinel_selection_reason:
  - field exists in real producer outputs for both scrub-after paths
  - field is required by the public decision schema
  - field is not an external-artifact safety-control field
  - `_external_disabled_local_fallback` does not recompute or overwrite it
  - changing it inside the wrapper does not change the producer-selection or finalizer-scrub logic under test
- sentinel_baseline_tests:
  - `test_budget_or_policy_fallback_flag_off_sentinel_baseline_survives_public_output`
  - `test_private_provider_boundary_flag_off_sentinel_baseline_survives_public_output`
- sentinel_baseline_result: sentinel preserved in final public output on the same flag-off path for both scrub-after producers
- fallback_boundary_used: none
- fallback_boundary_reason: not needed because the public-output sentinel survived current output normalization

## Enforcing Tests

- forced_return_consumption_enforced_by:
  - `test_budget_or_policy_fallback_flag_off_sentinel_baseline_survives_public_output`
  - `test_private_provider_boundary_flag_off_sentinel_baseline_survives_public_output`
  - `test_forced_budget_or_policy_fallback_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed`
  - `test_forced_private_provider_boundary_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed`
- full_bundle_scrub_enforced_by:
  - `test_forced_bundle_finalizer_scrubs_not_exactly_true_flags`
  - `test_forced_budget_or_policy_fallback_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed`
  - `test_forced_private_provider_boundary_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed`
- sentinel_baseline_enforced_by:
  - `test_budget_or_policy_fallback_flag_off_sentinel_baseline_survives_public_output`
  - `test_private_provider_boundary_flag_off_sentinel_baseline_survives_public_output`
- schema_validation_enforced_by:
  - `test_forced_bundle_finalizer_scrubs_not_exactly_true_flags`
  - `test_forced_bundle_finalizer_preserves_valid_target_when_flag_true`
  - `test_budget_or_policy_fallback_flag_off_sentinel_baseline_survives_public_output`
  - `test_private_provider_boundary_flag_off_sentinel_baseline_survives_public_output`
  - `test_forced_budget_or_policy_fallback_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed`
  - `test_forced_private_provider_boundary_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed`
  - `test_forced_budget_or_policy_fallback_bundle_preserved_when_external_flag_true`
  - `test_forced_private_provider_boundary_bundle_preserved_when_external_flag_true`
  - `test_forced_unknown_external_pressure_bundle_preserved_when_external_flag_true`
  - `test_forced_external_candidate_bundle_preserved_when_external_flag_true`

## Schema Validation

- schema_validation_method: local validator in `tests/test_router_policy_external_proposal_invariant.py`
- schema_constructs_used:
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
- schema_constructs_covered:
  - all constructs currently used by `schemas/router_policy_decision_v0_3_1_1.schema.json`
- unsupported_schema_constructs: none for the current router decision schema usage
- schema_validation_coverage: complete for the currently used router decision schema constructs

## Status Accuracy

- pre_commit_status:
  - tracked modifications:
    - `tests/test_router_policy_external_proposal_invariant.py`
    - `reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/summary.md`
    - `reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/summary.json`
  - expected unrelated untracked artifacts:
    - `reports/E2-EXTERNAL-ROUTING-FLAG-GOVERNANCE/changed_files.zip`
    - `reports/E3-EXTERNAL-BUDGET-SESSION-GATE/changed_files.zip`
    - `reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/changed_files.zip`
    - `reports/E4-PRE-ROUTER-EXTERNAL-PROPOSAL-INVARIANT/changed_files.zip`
- final_post_commit_status: clean except expected untracked `changed_files.zip` artifacts
- status_drift_fixed: true

## No-Wiring

- no_provider_e3_e4_wiring_check: clean
- method:
  - diff-scoped inspection of R1.1 changed files
  - grep for `evaluate_external_budget_gate`, provider/network client code, `requests`, `httpx`, `urllib`, confirmation/session/digest implementation, and external execution wiring
- result:
  - no production `evaluate_external_budget_gate` call added
  - no provider/network client code added
  - no E3/E4 runtime wiring added
  - no external execution path added

## Known Limitations

- R1.1 proves forced return consumption for the current discovered scrub-after producer paths only.
- R1.1 does not implement E4.
- R1.1 does not activate E3.
- E4 still requires cumulative egress scope, digest/confirmation binding, provider policy, and E3 re-validation.
