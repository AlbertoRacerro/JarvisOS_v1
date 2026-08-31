# 129 EGRESS-SIDE-CHANNEL-CLOSURE-1

Status: definition / planning authority only

## Purpose

Close the two exact legacy product external-dispatch side channels retained by 128 without broadening provider, egress, budget, privacy, credential, or routing authority. All externally dispatched AI work must flow through the already accepted canonical AI execution/provider/egress spine rather than constructing/selecting a concrete provider adapter and calling it directly from diagnostic product surfaces.

This definition is derived from exact master `c92ba543c9f56d4dcd1d4cbfe5d7192eb3f69cdd`. It creates no implementation authority. `docs/specs/STATUS.md=planned` remains authoritative until a separate full specification and fresh readiness decision are accepted and the registry becomes `ready`.

## Exact confirmed debt

128 readiness binds exactly two AE002 legacy-product-dispatch exceptions to 129:

1. `backend/app/modules/ai/deepseek_provider_smoke.py::run_provider_smoke`
   - constructs `DeepSeekProviderAdapter()` directly;
   - applies local settings/privacy checks;
   - calls `adapter.complete(AIRequest(...))` directly;
   - therefore external dispatch can bypass the canonical execution-side egress/budget/ledger/fallback authority even when the local smoke checks are individually sensible.

2. `backend/app/modules/ai/supervisor_public_test.py::run_supervisor_public_test`
   - performs its own concrete provider selection through `_select_provider`;
   - carries the selected adapter in `ProviderSelection`;
   - calls `selection.adapter.complete(AIRequest(...))` directly;
   - therefore provider choice and external dispatch are locally reimplemented outside the canonical execution boundary.

These are the only exact 129 debt entries frozen by accepted 128 authority. This definition does not infer that every HTTP client, provider adapter implementation, local Ollama call, test fixture, or repository-development network operation is product egress debt.

## Required direction for the full specification

The later full spec must re-inventory fresh exact master and freeze the minimum compatibility-preserving closure for both public diagnostic surfaces. It must require:

- no direct concrete-provider adapter construction or `.complete(...)` dispatch in either debt owner;
- no local provider-selection algorithm that can become a second routing/fallback authority;
- delegation through the existing canonical AI execution/provider/egress spine, preserving its current credential, egress-decision, budget/usage, provider-routing, request/correlation, and safe-ledger authority rather than recreating those checks beside it;
- existing smoke/public-test request limits and safety intent to remain bounded product behavior unless fresh evidence proves a contract change is necessary;
- provider-specific diagnostic intent, if still required, to be expressed as canonical request policy/metadata only where the existing execution authority explicitly supports it; a diagnostic route must not regain concrete-adapter authority through a renamed helper;
- failure closed when canonical execution rejects privacy/egress/budget/provider availability; no fallback to direct adapter dispatch;
- removal of the two exact 129 exceptions from architecture-enforcement configuration only after runtime code and deterministic tests prove the bypasses are gone.

## Failure modes to resolve before readiness

The full-spec/readiness inventory must explicitly test for:

1. **policy duplication drift** — a smoke route locally checks a subset of privacy/budget rules but misses a canonical egress/ticket/ledger requirement added later;
2. **provider-selection drift** — Supervisor chooses DeepSeek/Scaleway independently of the accepted router, producing inconsistent fallback, model, pricing, or availability behavior;
3. **secret/credential authority leakage** — a diagnostic path directly instantiates an adapter/provider and thereby gains credential-bearing dispatch capability;
4. **budget/accounting split brain** — adapter call succeeds while canonical usage/budget/ledger accounting is skipped or recorded differently;
5. **metadata/request identity loss** — migration to the canonical path drops request/correlation/workspace/task metadata needed for safe auditability;
6. **semantic downgrade during migration** — `public/internal` diagnostic restrictions accidentally become broader merely because the canonical gateway supports more sensitivity classes;
7. **hidden fallback bypass** — canonical rejection is followed by a direct adapter retry or alternate concrete-provider call;
8. **test-only escape becoming runtime authority** — fixtures/helpers may stub the canonical execution boundary but must not introduce a production flag or import path that restores direct dispatch;
9. **architecture allowlist staleness** — 129 debt exceptions remain after the bypass disappears, permitting future reintroduction under an obsolete exemption;
10. **scope explosion** — implementation rewrites the provider/router/egress architecture instead of removing the two already-known side channels.

## Scope

Planning scope is limited to the two exact 128-owned debt surfaces, the canonical execution seam they must delegate to, their registered API contracts/callers, focused deterministic tests, and the exact 128 architecture-enforcement debt entries that must be retired after closure.

The full spec must identify the exact implementation paths from fresh master before readiness. Expected candidate paths may include the two debt modules, their focused tests, the minimum canonical execution/request contract needed for delegation if a missing bounded seam is proven, architecture-enforcement config/tests for debt removal, and `docs/specs/STATUS.md` for lifecycle bookkeeping. This list is not implementation authority.

## Non-goals

- no new provider or provider SDK;
- no new credential store or secret transport;
- no new egress policy/confirmation system;
- no new durable ledger/store/schema/migration;
- no broad AI router rewrite;
- no change to local Ollama ownership merely because it uses HTTP;
- no removal of diagnostic endpoints unless fresh full-spec evidence proves compatibility-preserving delegation is impossible or the endpoint is unused and canonical product authority permits retirement;
- no 130–134 or 113–126 implementation;
- no broad cleanup of repository-development network calls or unrelated provider adapters;
- no implementation while 129 remains `planned`.

## Definition acceptance criteria

1. The problem is bound to the two exact AE002 debts already assigned to 129 by accepted 128 readiness.
2. The security boundary is explicit: product diagnostic code must not own concrete external dispatch, provider selection, or credential-bearing adapter construction outside the canonical execution spine.
3. The later full spec is required to preserve bounded diagnostic safety semantics while eliminating duplicate dispatch authority.
4. Debt-exception removal is part of closure, preventing the static architecture gate from silently retaining a stale bypass allowance.
5. Failure modes cover policy, provider selection, credentials, accounting, metadata, fallback, tests, stale allowlists, and scope control.
6. No implementation, lifecycle promotion, schema, provider, credential, or product behavior change is authorized by this definition.

## Evidence inspected

- `docs/specs/128-readiness-2026-08-30.md` — exact AE002 debt ownership and 129 disposition;
- `backend/app/modules/ai/deepseek_provider_smoke.py` — direct `DeepSeekProviderAdapter()` construction and `adapter.complete(...)`;
- `backend/app/modules/ai/supervisor_public_test.py` — local concrete provider selection and `selection.adapter.complete(...)`;
- current post-112 hardening-first scheduling authority and `STATUS.md` at exact derivation master.

## Next lifecycle step

After this definition is accepted and merged, derive a separate full specification from then-current exact master. Because this is an egress/security boundary, definition, full-spec, and readiness remain distinct lifecycle stages; no planning compression grants implementation authority.
