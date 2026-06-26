# E2 - External Routing Flag Governance

## Scope

- Surgical fix only.
- No sensitivity redesign.
- No E1 changes.
- No E3/E4 concepts.

## Already Existing Behavior

- Rule 6 external candidacy was already gated by `user_policy.external_routing_enabled is True` in `_qualifies_for_external_candidate(...)`.
- Missing, `None`, or `False` already prevented rule-6 external candidacy.
- `DevLocalChatRequest` still has no client `user_policy` channel in [backend/app/api/dev_message_route.py](C:/Users/thera/Documents/JarvisOS_v1/backend/app/api/dev_message_route.py).
- A5-R3 and E1 already cover sensitivity, BlueRev/IP, and deterministic egress safety.

## New Fix

- Rule 8 now checks the external-routing flag before proposing external review.
- `unknown/ambiguous sensitivity + external pressure + flag missing/None/False` now falls back to coherent local/no-external behavior.
- Rule 8 with `external_routing_enabled is True` preserves the existing external proposal behavior.

## Files

- [scripts/router_policy_decision_probe.py](C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_decision_probe.py)
- [tests/test_router_policy_message_route_smoke.py](C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_message_route_smoke.py)

## Checks

- `python -m pytest tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py -q`
- `git diff --check`
- `git status --short`
