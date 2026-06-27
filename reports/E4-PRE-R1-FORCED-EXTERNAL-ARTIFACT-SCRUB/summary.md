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
  - `python -m pytest tests/test_router_policy_external_proposal_invariant.py -q` -> `65 passed in 0.31s`
  - `python -m pytest tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `236 passed in 0.79s`
  - `git diff --check` -> passed, LF/CRLF warning only for `tests/test_router_policy_external_proposal_invariant.py`
  - `git status --short` -> ` M tests/test_router_policy_external_proposal_invariant.py`, `?? reports/E2-EXTERNAL-ROUTING-FLAG-GOVERNANCE/changed_files.zip`, `?? reports/E3-EXTERNAL-BUDGET-SESSION-GATE/changed_files.zip`, `?? reports/E4-PRE-R1-FORCED-EXTERNAL-ARTIFACT-SCRUB/`, `?? reports/E4-PRE-ROUTER-EXTERNAL-PROPOSAL-INVARIANT/changed_files.zip`

## Known Limitations

- R1 validates forced artifacts for current discovered producer paths, not undiscovered future producer construction patterns.
- R1 depends on representative trigger inputs reaching the intended producers.
- R1 does not implement E4.
- E4 still requires cumulative egress scope, digest/confirmation, provider policy, and E3 re-validation.
