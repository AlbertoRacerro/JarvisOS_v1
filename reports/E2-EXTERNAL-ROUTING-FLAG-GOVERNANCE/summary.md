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

- E2 initially added a rule-8-specific flag gate.
- E2-R1 adds a final `proposed_external_target` chokepoint as the authoritative external-proposal invariant.
- The rule-8 gate remains as defense-in-depth / historical local branch.
- When `external_routing_enabled is not True`, any decision carrying `proposed_external_target` is fully normalized to local/no-external state.
- Normalization clears external-adjacent redaction and confirmation fields instead of only clearing the target.
- Rule 8 with `external_routing_enabled is True` preserves the existing external proposal behavior.

## Files

- [scripts/router_policy_decision_probe.py](C:/Users/thera/Documents/JarvisOS_v1/scripts/router_policy_decision_probe.py)
- [tests/test_router_policy_message_route_smoke.py](C:/Users/thera/Documents/JarvisOS_v1/tests/test_router_policy_message_route_smoke.py)

## Checks

- `python -m pytest tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py -q`
- `git diff --check`
- `git status --short`
