# 124 PROVIDER-SETTINGS-GENERIC-1

## Definition kernel

**Lifecycle:** definition only. This artifact does not make 124 implementation-ready; `docs/specs/STATUS.md` remains the live work-state authority and 124 remains `planned` until a separate full spec and readiness decision are merged.

**Fresh derivation basis:** exact `master` `97dfeeb45bb897414ad186994aeff8725ed7103b` and the existing merged owners listed by the 124 registry row: `015`, `018`, `021`, `059b`, `061a`, `082`, `094`, and `111`.

## Problem

JarvisOS already has separate authority for provider registration/routing, external-provider gating, secure credential storage, usage/budget/accounting, provider/system projections, and explicit context/action governance. The remaining product gap is a bounded Settings-facing provider/integration surface that lets an operator configure and inspect those existing owners without creating a second credential store, provider registry, egress path, usage ledger, policy engine, or context authority.

## Bounded owner to derive

124 will own only the provider/integration Settings projection and operator interaction contract over existing authorities. The later full spec must freeze the exact existing server contracts and current frontend surface before implementation.

The intended product boundary is:

- provider/integration configuration projected from the existing provider/config owners;
- secure credential submission, replacement, deletion, and presence/status projection through the existing secure-storage owner, with secret values never returned to ordinary read surfaces;
- provider availability/status and bounded connection/test feedback through existing provider/egress/policy authority;
- provider catalogue/capability information projected from existing authoritative registries rather than copied into frontend-owned truth;
- usage, budget, and system/provider health projections from existing accounting/system owners;
- an existing Settings/operator surface only, unless fresh full-spec inspection proves a minimal extension is necessary.

## Authority boundaries

124 MUST NOT create or acquire any of the following authority:

1. A second credential store or plaintext-secret read API.
2. A second provider/model registry, routing policy, fallback policy, budget ledger, usage ledger, or health source of truth.
3. Browser-to-provider network access, provider credentials in browser-owned persistence, or a client-side bypass around server egress/policy gates.
4. New provider adapters, provider-selection semantics, model-scoped key ownership, or Hermes/provider-routing claims.
5. Automatic provider discovery, autonomous credential rotation, or background provider actions.
6. Jarvis context authority for credentials or provider secrets. `111` remains the context/action boundary; secret material is not context evidence.
7. Any commit/apply/execute/merge/repository mutation authority unrelated to the bounded Settings surface.

A live provider test, if retained after full-spec inspection, must be an explicitly requested bounded server-side action routed through the existing provider, egress, policy, usage, and budget authorities. 124 may render its result; it may not invent an unmetered or policy-bypassing probe.

## Failure modes that the full spec must close

The next lifecycle artifacts must make the following failures mechanically testable rather than relying on UI convention:

- **Secret disclosure:** credential values leak through GET/list/status responses, logs, errors, analytics, browser persistence, or Jarvis context.
- **Authority bypass:** a provider test or status refresh performs direct browser egress or bypasses the existing external-provider/policy/budget spine.
- **Duplicate truth:** frontend or 124 introduces a parallel provider catalogue, configuration registry, health truth, usage total, or budget calculation that can drift from its owner.
- **Cross-provider confusion:** a save/delete/test action targets a different provider/integration identity than the one the operator saw.
- **Stale mutation:** an async completion or delayed confirmation applies against a replaced provider/config/credential state.
- **Ambiguous retry:** save/delete/test retries can accidentally create duplicate effects or misreport success after a timeout/partial failure.
- **False health:** unavailable, unknown, partial, stale, or policy-blocked provider state is rendered as healthy/usable.
- **Unbounded test cost/egress:** repeated provider tests can create uncontrolled requests, spend, or side effects.
- **Secret-presence ambiguity:** the UI cannot distinguish absent/configured/invalid/unknown without exposing the credential itself.

## Required full-spec derivation

A separate full-spec PR must inspect then-current runtime and freeze, at minimum:

- the exact Settings frontend owner(s), routes/components, and server API surfaces to reuse;
- the exact provider/integration identifiers and canonical sources for configuration, catalogue/capability, status/health, usage, budget, and system projection;
- the exact secure-credential write/delete/presence contract and all redaction guarantees inherited from `082`;
- any provider-test operation that already exists, including egress/policy/budget/accounting behavior, or explicitly exclude live testing if no governed contract exists;
- stale-write/idempotency semantics for credential/config mutations and bounded test actions;
- response/error states for absent, unknown, unavailable, policy-blocked, partial, stale, and failed providers;
- the minimum frontend changes necessary without redesigning Settings or duplicating backend authority.

If fresh inspection shows that a required product behavior needs a new credential, provider, egress, policy, accounting, or store authority, the full spec must stop and re-derive that prerequisite separately rather than smuggling it into 124.

## Readiness requirements

A separate readiness decision must freeze deterministic evidence for the accepted full spec. At minimum it must require:

- server/API contract tests for credential redaction and no-secret readback;
- negative tests proving browser-facing paths cannot bypass provider/egress/policy owners;
- deterministic provider identity, stale-action, retry/idempotency, partial/unknown-state, and duplicate-truth tests for whichever write/test operations are accepted;
- usage/budget/status projections proven to consume their canonical owners rather than recompute shadow truth;
- frontend/API tests for the bounded Settings flows;
- exact-head real-browser proof for material operator flows when the readiness inspection determines browser behavior cannot be established deterministically below that layer.

## Definition exit criteria

This definition is complete when it establishes one independently removable Settings/provider integration owner, preserves all existing credential/provider/egress/policy/accounting/context authorities, records the material failure modes above, and leaves exact API/UI/test contracts to the required full-spec and readiness stages.

No implementation, registry status promotion, credential migration, provider call, or runtime behavior change is authorized by this definition.
