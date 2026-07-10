# 021 — ALPHA-GATE hardening: server-owned external-provider boundary

Status: implementation in review; `docs/specs/STATUS.md` is authoritative.

## Goal

Make the existing AI execution spine enforce one deterministic, server-owned
boundary immediately before every external provider attempt.

A request body, BLUECAD brief, task kind, route label, confirmation-shaped
field, or caller-supplied prose must never authorize an external provider call.
The decision is derived from the concrete provider binding selected by the
server and from server-side policy, credential, usage, and budget state.

This slice hardens the external-provider boundary only. It does not claim that
all local filesystem writes, CAD builds, solver calls, promotions, or other
state changes are governed by one universal alpha switch.

## Runtime boundary

`run_ai_task` is the authoritative provider execution spine. It:

1. resolves a route to a `ProviderBinding`;
2. expands the configured fallback chain;
3. evaluates the provider gate for each concrete binding;
4. calls `adapter.complete(...)` only after that binding is allowed.

The existing execution spine decides whether a binding is external from
`ProviderBinding.requires_network`. The request payload does not provide this
classification.

For a network binding, `evaluate_provider_budget_gate(...)` remains the
compatibility entry point used by the spine. It must delegate to the explicit
server-owned `evaluate_alpha_execution_gate(...)` decision.

For a non-network binding, the execution spine does not consult the external
gate. This is the only fixture escape hatch: tests may inject a scripted
adapter only through an explicit binding with `requires_network=False`.
`force_external_allowed`, `confirmed`, `alpha`, `side_effectful`, or similar
payload fields are not authorization inputs.

## Scope

In scope:

- add an immutable `AlphaGateDecision`;
- add an explicit operation identifier for external provider calls;
- fail closed when server settings or the provider identity are absent;
- reject unsupported operation classes rather than silently treating them as
  read-only;
- preserve the current provider-policy checks:
  - AI policy enabled;
  - paid AI enabled;
  - positive and unexhausted global budget;
  - enabled provider registry entry;
  - required credential present;
  - provider token cap not exhausted;
  - provider cost cap not exhausted;
- retain `ProviderBudgetGate` and `evaluate_provider_budget_gate(...)` as a
  compatibility surface;
- prove that the execution spine evaluates the alpha decision before the
  adapter call;
- prove that every fallback binding is evaluated independently;
- prove that an explicitly non-network fixture binding remains offline and
  does not need external authorization;
- prove that request models reject confirmation-shaped self-authorization
  fields.

Files expected to change:

- `backend/app/modules/ai/budget.py`;
- `backend/tests/test_alpha_gate_enforcement.py`;
- this spec;
- `docs/specs/STATUS.md`.

No BLUECAD loop change is required: provider execution authority belongs in
the shared execution spine, not in one product caller.

## Non-goals

- No universal gate over every database or filesystem write.
- No change to BLUECAD candidate creation, CAD build, mesh, FEM, promotion, or
  simulation semantics.
- No live provider call in tests.
- No new provider, model, route, credential, or environment variable.
- No new confirmation protocol.
- No sensitivity, retrieval, redaction, or IP-egress policy; that is spec 059.
- No executable end-to-end BLUECAD proof or data-root backup/restore; that
  remaining historical scope is tracked as 021b.
- No UI.
- No workflow change.
- No automatic merge.

## Binding invariants

1. **Concrete binding authority.** The external/local classification comes
   from the `ProviderBinding` being attempted.
2. **Per-attempt enforcement.** A retry or fallback cannot inherit approval
   from the previous provider.
3. **Fail closed.** Missing server settings, missing provider identity, or an
   unsupported operation denies execution.
4. **No payload authorization.** User-controlled fields do not enter the gate
   function.
5. **Offline fixture rule.** A fixture bypass is valid only when its injected
   binding declares `requires_network=False`; the adapter must therefore be
   unable to become a network fallback through the supplied binding table.
6. **Ledger preservation.** A denial writes a normal pre-provider
   `config_error` row containing the deterministic blocking reason and no
   prompt/output content or secret.
7. **No semantic duplication at BLUECAD.** Product callers may perform
   earlier UX parking checks, but removal or failure of such checks must not
   permit `adapter.complete(...)` to run.

## Acceptance criteria

1. `evaluate_alpha_execution_gate(...)` returns a structured immutable
   decision.
2. The gate denies:
   - `settings=None`;
   - missing/blank provider identity;
   - any operation other than the explicit external-provider operation.
3. The gate preserves all existing global/provider budget, credential, and
   cap behavior.
4. `evaluate_provider_budget_gate(...)` delegates to the alpha decision and
   preserves its existing return contract.
5. A network binding denied by the alpha decision causes:
   - `run_ai_task(...).status == "config_error"`;
   - zero adapter calls;
   - one ledger row for the denied binding;
   - a deterministic denial reason.
6. A retryable failure on provider A followed by a denied provider B causes:
   - provider A to be called once;
   - provider B not to be called;
   - independent gate evaluations for A and B;
   - ledger rows for both attempts.
7. An injected non-network fixture binding:
   - does not consult the external gate;
   - executes only the injected offline adapter;
   - remains subject to route/binding validation and output validation.
8. Confirmation-shaped fields such as `alpha`, `confirmed`,
   `force_external_allowed`, and `side_effectful` are rejected by the task
   request schema.
9. Existing provider-cap, fallback, local-route, BLUECAD, and full backend
   tests remain green.
10. Ruff remains green.

## Required tests

`backend/tests/test_alpha_gate_enforcement.py` must include:

- missing server context fails closed;
- unsupported operation and missing provider fail closed;
- forced gate denial prevents a network adapter call;
- offline binding does not call the external gate;
- each fallback provider is gated before its adapter;
- request payload fields cannot self-authorize.

The integration tests must be mutation-resistant: deleting the execution
spine's provider-gate call or bypassing the compatibility wrapper must make at
least one test fail.

## Residual risk

This slice governs external provider execution only. Local tools and state
changes still rely on their existing deterministic boundaries. The broader
cross-module sensitivity/retrieval/egress boundary remains mandatory before
real BlueRev IP is sent to cloud providers under spec 059.

## Definition of done

- acceptance criteria are implemented;
- focused tests pass;
- full backend tests pass;
- Ruff passes;
- `STATUS.md` links the active implementation PR;
- the superseded PR is closed with a pointer to the replacement;
- human merge authority is preserved.
