# A4-R2-R1 - Fix local responder timing metadata compatibility

## Summary

- fix-forward patch after `c7c334856e2a53d866baa3f76d21a8e460fb7e76`
- shared adapter now omits `local_responder_timing` when raw Ollama timing keys are entirely absent
- shared adapter still includes `local_responder_timing` when any timing key is present, including zero values
- backend dev test updated to match the compatibility rule

## Scope

- files changed: `scripts/router_policy_local_responder.py`, `tests/test_router_policy_local_responder.py`, `backend/tests/test_dev_local_chat.py`, `reports/router_policy/1G-B2-F3-A4-R2-R1/summary.json`, `reports/router_policy/1G-B2-F3-A4-R2-R1/summary.md`
- root local responder tests fixed: `true`
- backend tests still pass: `true`
- keep_alive behavior changed: `false`
- num_predict behavior changed: `false`
- backend_timing preserved: `true`

## Residual risks

- A4-R2 timing metadata is diagnostic only.
- A4-R2-R1 does not change live latency behavior.
- A4-R1a prompt wording remains separate and must not be fixed in this milestone.
- A5-R2 Italian detector hardening remains separate and must not be fixed in this milestone.
