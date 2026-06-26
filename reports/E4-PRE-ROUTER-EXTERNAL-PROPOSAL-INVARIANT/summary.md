# E4-PRE - Router External Proposal Invariant Guard

## Start

- starting HEAD: `799e48aef0ced2d717bd761cda960492f047cd7e`
- tracked worktree clean status: clean
- ignored untracked changed_files_zip artifacts:
  - `reports/E2-EXTERNAL-ROUTING-FLAG-GOVERNANCE/changed_files.zip`
  - `reports/E3-EXTERNAL-BUDGET-SESSION-GATE/changed_files.zip`

## Phase 0

- router module path: [router_policy_decision_probe.py](C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_decision_probe.py)
- decision representation: `dict`
- external artifact field inventory:
  - `proposed_external_target`
  - `external_allowed`
  - `external_network_allowed_now`
  - `provider_call_allowed_now`
  - `confirmation_required`
  - `confirmation_payload_required`
  - `confirmation_payload`
  - `confirmation_digest`
  - `confirmation_options`
  - `redaction_required`
  - `redaction_status`
- always-present external artifact fields:
  - all fields above are required by [router_policy_decision_v0_3_1_1.schema.json](C:/Users/thera/Documents/JarvisOS_v1/schemas/router_policy_decision_v0_3_1_1.schema.json)
- optional external artifact fields: none among the tracked invariant fields above
- how `proposed_external_target` is written today:
  - `decision.update({... "proposed_external_target": "external:scientific_medium" ...})`
  - `decision.update({... "proposed_external_target": target ...})`
- valid_proposed_external_target_shape:
  - enum in decision schema: `external:cheap | external:scientific_medium | external:frontier | null`
- valid_test_external_target_value: `external:scientific_medium`
- downstream_target_validation_present: true
- target_validation_location_if_present: [router_policy_decision_v0_3_1_1.schema.json](C:/Users/thera/Documents/JarvisOS_v1/schemas/router_policy_decision_v0_3_1_1.schema.json)
- current producer helpers discovered by inspection:
  - `_private_provider_boundary`
  - `_unknown_external_pressure`
  - `_external_candidate_proposal`
  - `_budget_or_policy_fallback`
- finalizers_or_output_normalizers_discovered:
  - `_enforce_external_proposal_flag_invariant`

## Producer Classification

- producer helpers expected:
  - `_private_provider_boundary`
  - `_unknown_external_pressure`
  - `_external_candidate_proposal`
  - `_budget_or_policy_fallback`
- AST producer discovery result:
  - discovered set matched expected set
- producer classification summary:
  - `_private_provider_boundary` -> `scrub-after`
  - `_budget_or_policy_fallback` -> `scrub-after`
  - `_unknown_external_pressure` -> `suppress-before`
  - `_external_candidate_proposal` -> `suppress-before`
- producer classification evidence:
  - `_private_provider_boundary`: reachable before finalizer on raw-private + provider-boundary input; finalizer scrubs with flag off
  - `_budget_or_policy_fallback`: reachable before finalizer on high-complexity public/internal fallback; finalizer scrubs with flag off
  - `_unknown_external_pressure`: current rule-8 gate calls `_external_disabled_local_fallback` when flag is not exactly `True`, so producer is not reached with flag off
  - `_external_candidate_proposal`: `_qualifies_for_external_candidate(...)` requires `external_routing_enabled is True`, so producer is not reached with flag off
- producer patch namespace summary:
  - all producers are defined locally in [router_policy_decision_probe.py](C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_decision_probe.py)
  - monkeypatch target namespace: `router_policy_decision_probe.<helper_name>`
- producer reachability summary:
  - `_private_provider_boundary`:
    - representative trigger input: raw-private/IP-sensitive + provider/upload intent
    - flag off expected call_count: `> 0`
    - flag on expected call_count: `> 0`
  - `_budget_or_policy_fallback`:
    - representative trigger input: public/internal + high complexity scientific request + no candidate tier available
    - flag off expected call_count: `> 0`
    - flag on expected call_count: `> 0`
  - `_unknown_external_pressure`:
    - representative trigger input: unknown sensitivity + external pressure via `needs_current_info`
    - flag off expected call_count: `0`
    - flag on expected call_count: `> 0`
  - `_external_candidate_proposal`:
    - representative trigger input: public/internal + high complexity + scientific depth + provider/budget allow
    - flag off expected call_count: `0`
    - flag on expected call_count: `> 0`
- actual call_count by flag per producer:
  - `_private_provider_boundary`: flag off `1`, flag true `1`
  - `_budget_or_policy_fallback`: flag off `1`, flag true `1`
  - `_unknown_external_pressure`: flag off `0`, flag true `1`
  - `_external_candidate_proposal`: flag off `0`, flag true `1`
- monkeypatch enforcement coverage:
  - scrub-after producers proved `call_count > 0` with flag off and final output scrubbed
  - suppress-before producers proved `call_count == 0` with flag off and final output safe
  - positive preserve tests proved valid external target preservation with flag true for all four current producers
- flag_off_output_scrubbed_or_suppressed per producer:
  - `_private_provider_boundary`: scrubbed
  - `_budget_or_policy_fallback`: scrubbed
  - `_unknown_external_pressure`: suppressed-before
  - `_external_candidate_proposal`: suppressed-before
- flag_true_positive_tested per producer:
  - `_private_provider_boundary`: yes
  - `_budget_or_policy_fallback`: yes
  - `_unknown_external_pressure`: yes
  - `_external_candidate_proposal`: yes
- flag_true_external_artifact_preserved_or_skip_reason per producer:
  - `_private_provider_boundary`: preserved valid target
  - `_budget_or_policy_fallback`: preserved valid target
  - `_unknown_external_pressure`: preserved valid target
  - `_external_candidate_proposal`: preserved valid target
- positive_preserve_coverage_by_finalizer:
  - single finalizer `_enforce_external_proposal_flag_invariant`
  - positive preserve covered through all current producer paths

## Interpretation

- redaction field interpretation:
  - `redaction_required` / `redaction_status` are broader than external proposals because `_block_secret` uses them for local blocked secret handling
  - invariant assertions therefore focus globally on proposal/provider/network/confirmation artifacts
  - dedicated provider-boundary downgrade test additionally proves external redaction artifacts are cleared for a scrubbed external proposal path
- behavioral matrix cases:
  - unknown external pressure
  - high-complexity public/internal budget fallback
  - raw-private/provider boundary
  - normal external candidate
- external_routing_enabled non-identity truthy cases checked:
  - `1`
  - `"true"`
  - `"True"`
  - `[]`
  - `{}`
- branch activation limitations if any:
  - final normalized outputs for flag-off cases intentionally collapse to the same local/no-external shape
  - producer-specific branch activation for flag-off cases is therefore proven primarily by monkeypatch call counts, not by final route markers alone
- unknown producer handling result:
  - none discovered

## Checks

- tests/checks run:
  - `python -m pytest tests/test_router_policy_external_proposal_invariant.py -q` -> `48 passed in 0.09s`
  - `python -m pytest tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `236 passed in 0.26s`
  - `git diff --check` -> passed
  - `git status --short` -> `?? reports/E2-EXTERNAL-ROUTING-FLAG-GOVERNANCE/changed_files.zip`, `?? reports/E3-EXTERNAL-BUDGET-SESSION-GATE/changed_files.zip`, `?? reports/E4-PRE-ROUTER-EXTERNAL-PROPOSAL-INVARIANT/`, `?? tests/test_router_policy_external_proposal_invariant.py`
- files changed:
  - [test_router_policy_external_proposal_invariant.py](C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_external_proposal_invariant.py)
  - [summary.md](C:/Users/thera/Documents/JarvisOS_v1/reports/E4-PRE-ROUTER-EXTERNAL-PROPOSAL-INVARIANT/summary.md)
  - [summary.json](C:/Users/thera/Documents/JarvisOS_v1/reports/E4-PRE-ROUTER-EXTERNAL-PROPOSAL-INVARIANT/summary.json)
- production_patch_required: false
- post-commit diff-scoped no-wiring check: pre-commit explicit-path inspection found no production call to `evaluate_external_budget_gate`, no provider client code, and no external execution wiring in the E4-PRE files
- confirmation that no provider/E3/E4 wiring was added: true by explicit-path inspection of the E4-PRE files

## Known Limitations

- AST is used for producer discovery, not full dataflow proof.
- E4-PRE protection is only as complete as producer discovery.
- A future producer using a mutation/construction pattern not detected by AST/repo discovery may evade both the expected producer set and monkeypatch enforcement.
- Behavioral matrix is example-based and may not exercise such a producer.
- Monkeypatch enforcement depends on correct producer classification and representative trigger inputs.
- A producer with incorrect or incomplete representative trigger input may appear unreachable even if it is reachable in production.
- Positive preserve tests must use a valid proposed_external_target; otherwise downstream target validation can create false failures unrelated to over-scrubbing.
- Expected producer set is a tripwire, not the main guarantee.
- E4 still requires cumulative egress scope, digest/confirmation, provider policy, and E3 re-validation.
