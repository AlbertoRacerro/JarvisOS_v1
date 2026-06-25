# A5-R2 - Italian operational write detector hardening

## Summary

- smoke-only detector extension for Italian memory-write, document/project-write, and credential-like save intents
- end-to-end blocking achieved through existing hard-gate-relevant fields, not detector flag alone
- safe-local predicate behavior preserved; no predicate change
- BlueRev/IP-sensitive marker detection explicitly deferred to `A5-R3`

## Scope

- base commit: `bbe9f7a7d143c1fbc5d994975601447a855ba71f`
- files changed:
  - `scripts/router_policy_message_route_smoke.py`
  - `tests/test_router_policy_message_route_smoke.py`
  - `backend/tests/test_dev_local_chat.py`
  - `reports/router_policy/1G-B2-F3-A5-R2/summary.json`
  - `reports/router_policy/1G-B2-F3-A5-R2/summary.md`
- local responder modified: `false`
- frontend modified: `false`
- prompt contract modified: `false`
- external routing added: `false`

## Behavior

- Italian memory-write examples now set existing memory-write hard-gate fields and block local execution
- Italian document/project-write examples now set existing file-write/codebase hard-gate fields and block local execution
- Italian credential-like save examples now set existing secret/credential plus memory-write hard-gate fields and block local execution
- harmless history still executes, while blocked Italian history turns are excluded from local prompt context
- safe non-persistent persona/session requests remain unblocked

## Residual risks

- A5-R2 hardens Italian operational write detection but does not enable external routing.
- External API routing remains blocked until future detector/IP work is audited and accepted.
- BlueRev/IP-sensitive marker detection is deferred to A5-R3 because it requires clean_for_local vs clean_for_external separation.
- Pattern-based detection can still miss paraphrases; future iterations may expand coverage.
- False positives must be monitored around ordinary words like memoria, codice, brevetto, documento.
- A4-R1a prompt wording remains separate.
- Streaming UI remains separate.
