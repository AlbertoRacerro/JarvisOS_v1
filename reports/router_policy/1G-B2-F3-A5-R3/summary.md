# 1G-B2-F3-A5-R3 Summary

## Implementation

- Floor: `scripts/router_policy_message_route_smoke.py::_apply_bluerev_ip_sensitivity_floor`.
- Exact insertion point: `scripts/router_policy_message_route_smoke.py:631`, immediately after the `assume_public_simple`/else normalization block sets `assume_public_simple_safe_path`, immediately before `return input_obj`.
- Confirmation: floor runs after the `assume_public_simple` safe-path normalization.
- Confirmation: floor mutates only `phase_a_signals["sensitivity_bucket_proposal"]`.
- Confirmation: floor is monotonic: `public`, `internal`, or `unknown` -> `sensitive`; `sensitive` stays `sensitive`; `secret` stays `secret`.
- Confirmation: floor does not downgrade `secret` to `sensitive`.
- Explicit markers include `parametri proprietari BlueRev`, `correlazioni riservate BlueRev`, `proprietà intellettuale BlueRev`, `dati proprietari BlueRev`, `assunzioni proprietarie BlueRev`, `design riservato BlueRev`, `brevetto BlueRev non pubblicato`, `segreto industriale BlueRev`, `IP sensibile BlueRev`.

## Compatibility

- Phase-B bridge compatibility: `scripts/router_policy_hint_bridge_probe.py` no longer treats bucket-only `sensitive` + `low_risk` as a hard gate; `secret`, `unknown`, raw-private, manual-review, and operational hard gates still dominate.
- `contains_raw_private_or_ip_sensitive_context` is not used for BlueRev/IP external-deny.
- `external_allowed=true` is not set for future external eligibility.
- No unconsumed diagnostic field is used as the only external-deny mechanism.
- No hard reason is added merely because an explicit BlueRev/IP marker is present.
- No live-Ollama-dependent tests were added.
- Generated answer content is not tested.

## Test Coverage

- Override public/internal -> sensitive: `tests/test_router_policy_message_route_smoke.py::test_a5_r3_002_bluerev_ip_floor_overrides_public_and_internal_external_candidates`.
- `assume_public_simple` public -> sensitive: `tests/test_router_policy_message_route_smoke.py::test_a5_r3_001_bluerev_ip_floor_runs_after_assume_public_simple`.
- Secret monotonicity: `tests/test_router_policy_message_route_smoke.py::test_a5_r3_003_bluerev_ip_floor_does_not_downgrade_secret`.
- False positives: `tests/test_router_policy_message_route_smoke.py::test_a5_r3_004_bluerev_and_naked_nouns_do_not_trigger_ip_floor`.
- Backend mocked responder: `backend/tests/test_dev_local_chat.py::test_a5r3_bluerev_ip_sensitive_answer_only_executes_with_mocked_responder`.
- Phase-B compatibility: `tests/test_router_policy_hint_bridge_probe.py::test_a5_r3_bucket_only_sensitive_low_risk_does_not_block_phase_b_answer_hint`.
- Backend test harness: `backend/tests/conftest.py` adds `backend` and `scripts` to `sys.path` for backend pytest invocations from repo root.

## Commands

- `python -m unittest tests.test_router_policy_message_route_smoke` -> pass, 93 tests.
- `python -m pytest backend/tests/test_dev_local_chat.py backend/tests/test_dev_message_route_smoke.py -q` -> pass, 120 tests.
- `python -m unittest tests.test_router_policy_hint_bridge_probe` -> pass, 16 tests.

## Residual Risks

- Active Python initially lacked `pytest`; `backend/requirements-dev.txt` was installed before backend verification.
- The floor is intentionally phrase-based; bare `BlueRev` and naked nouns do not trigger it.
