# E3 - External Budget/Session Gate

## Scope

- One pure deterministic budget/session gate.
- Provider-agnostic.
- No external execution.
- No pricing/currency.
- No provider tokenizers.
- No DB/session persistence.
- No rendered payload digest or E4 work-session logic.

## Behavior

Adds `evaluate_external_budget_gate(request, session_usage, budget_policy, now_epoch)`.

The gate validates:

- server-derived `request_text_bytes`
- conservative input token estimate via `bytes_per_token` default 3
- requested output token cap, with deny-not-clamp behavior
- cumulative session estimated token budget
- calls-per-session budget
- session TTL with injected `now_epoch`
- strict integer validation that rejects bools
- deterministic return-all reason codes with dependency-aware skip behavior

`allowed=true` does not enable external execution. E4 must still require E1, E2, user confirmation, and provider configuration.

## Trust boundary

`request_text_bytes` must be computed server-side by E4 from the exact text-bearing bytes that will be sent externally. E3 cannot verify the measurement by itself.

## Known limitations

- Generic token estimate is conservative but not provider-accurate.
- E3 does not perform billing.
- E3 does not persist session usage.
- E3 over-counts output using `requested_max_output_tokens` because real output is unknown at gate time.
- E4 must feed server-derived `request_text_bytes` from the exact provider-bound text-bearing payload.
- E4 must persist `next_session_usage` after a successful external call.

## Checks

- `python -m pytest tests/test_router_policy_external_budget_gate.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py -q`
  - `236 passed in 0.46s`
- `git diff --check`
  - passed
- `git status --short`
  - before commit: `?? E3_APPLY_INSTRUCTIONS.txt`, `?? reports/E2-EXTERNAL-ROUTING-FLAG-GOVERNANCE/changed_files.zip`, `?? reports/E3-EXTERNAL-BUDGET-SESSION-GATE/`, `?? scripts/router_policy_external_budget_gate.py`, `?? tests/test_router_policy_external_budget_gate.py`
