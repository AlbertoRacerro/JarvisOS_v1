# 129 EGRESS-SIDE-CHANNEL-CLOSURE-1 — Full Specification

Status: full specification / planning authority only
Derived from exact master: `13dba2866a5501f7935a60f9797fd571e9d63c6b`

This document does not authorize implementation. `docs/specs/STATUS.md=planned` remains authoritative until a separate readiness decision is accepted and the registry becomes `ready`.

## 1. Objective

Close the two exact external-dispatch side channels assigned to 129 by accepted 128 authority without creating a second routing, privacy, credential, budget, ledger, fallback, or egress authority.

The two debt owners are:

1. `backend/app/modules/ai/deepseek_provider_smoke.py::run_provider_smoke`;
2. `backend/app/modules/ai/supervisor_public_test.py::run_supervisor_public_test`.

Both must delegate externally dispatched work through the existing canonical AI execution spine in `backend/app/modules/ai/execution.py`, whose `run_ai_task` path already owns route binding, provider-neutral adapter invocation, network-egress enforcement, budget/usage handling, fallback behavior, request evidence, and AI-job ledger recording.

## 2. Frozen authority boundary

After 129 implementation:

- diagnostic product modules do not construct concrete external provider adapters;
- diagnostic product modules do not call provider `.complete(...)` directly;
- diagnostic product modules do not implement their own provider-selection/fallback algorithm;
- credential-bearing adapter construction remains in the canonical provider registry/execution infrastructure;
- external dispatch reaches a provider only after the canonical execution path accepts the request;
- canonical privacy/egress/budget/provider rejection is terminal for that diagnostic request; there is no direct-provider retry escape;
- canonical request, correlation, workspace/task and ledger identity remains observable through the existing execution evidence rather than a parallel diagnostic ledger.

No new authority surface is introduced merely to make the diagnostic code look indirect. A helper that still owns a concrete adapter or invokes `.complete(...)` outside the execution boundary is non-compliant.

## 3. Current-master inventory

Fresh exact-master inspection confirms:

### 3.1 `deepseek_provider_smoke.py`

Current debt:

- constructs `DeepSeekProviderAdapter` directly;
- performs local settings/privacy eligibility checks;
- constructs `AIRequest` locally;
- invokes `adapter.complete(...)` directly.

Required closure:

- retain the endpoint's bounded smoke/diagnostic purpose and public-safety intent;
- express any supported route/provider intent through canonical route/request inputs only;
- dispatch through the canonical execution seam;
- translate the canonical `AiTaskOutcome` into the existing smoke response contract with the smallest compatibility-preserving mapping;
- remove concrete adapter construction and direct completion from the module;
- do not add a fallback that reinstantiates DeepSeek when canonical execution rejects or cannot route the request.

### 3.2 `supervisor_public_test.py`

Current debt:

- locally selects between concrete providers/adapters;
- carries the selected adapter as local provider-selection state;
- directly invokes `selection.adapter.complete(...)`;
- duplicates provider/budget/availability behavior that can drift from canonical routing.

Required closure:

- remove local concrete-provider selection and adapter-bearing selection state from the dispatch path;
- preserve the existing public/internal restrictions and bounded request limits;
- request execution through the canonical route mechanism;
- rely on canonical routing/fallback/budget/egress behavior rather than reproducing it locally;
- map the canonical outcome to the existing public-test response shape with no widening of sensitivity or request authority.

### 3.3 Canonical execution/provider spine

`backend/app/modules/ai/execution.py` already provides the accepted positive execution spine. Relevant current properties include:

- route-class resolution through canonical provider bindings;
- provider-neutral `AIProviderAdapter` execution;
- external-network egress enforcement before provider invocation;
- budget/provider gates for network routes;
- canonical fallback-chain metadata and attempt accounting;
- success and pre-provider-failure AI-job ledger evidence;
- canonical context/request evidence and outcome typing through `AiTaskOutcome`.

`backend/app/modules/ai/provider_registry.py` and `configs/ai_providers.yaml` remain the provider/route configuration owners. 129 must consume those owners, not clone them.

## 4. Exact implementation scope

Expected implementation paths are limited to the minimum set proven necessary from fresh implementation-base master:

- `backend/app/modules/ai/deepseek_provider_smoke.py`;
- `backend/app/modules/ai/supervisor_public_test.py`;
- their focused backend tests;
- `backend/app/modules/ai/execution.py` only if fresh implementation evidence proves that a small provider-neutral diagnostic invocation seam or bounded metadata input is genuinely missing;
- `backend/app/modules/ai/provider_registry.py` / `configs/ai_providers.yaml` only if an already-supported canonical route cannot express the existing bounded diagnostic intent and a minimal declarative route addition is required;
- `configs/architecture_enforcement.json` and architecture-enforcement tests only to remove/prove removal of the two exact 129 debt exceptions after runtime closure is evidenced;
- `docs/specs/STATUS.md` only for lifecycle bookkeeping.

A runtime patch that can close both debts without changing the shared execution API is preferred. Any shared-spine change must be demonstrably necessary, provider-neutral, additive/minimal, and separately covered by focused tests.

## 5. Behavioral contract

### 5.1 DeepSeek smoke

The smoke path remains a diagnostic path, not an alternate provider API. It must:

- preserve existing input validation and bounded-output intent unless current canonical execution already enforces a stricter equivalent;
- never bypass sensitivity/privacy restrictions when using the shared executor;
- produce a deterministic failure response when canonical execution returns validation/config/route/provider/egress/budget failure;
- never retry through a directly constructed adapter;
- preserve enough canonical ledger/request evidence to identify the attempted route/provider/model and failure reason without emitting secrets.

If the existing canonical router cannot guarantee an exact DeepSeek provider pin, the implementation must not silently recreate local provider-selection authority. Readiness must choose between: (a) an already-supported canonical DeepSeek route, or (b) a minimal declarative canonical route/policy addition. Direct provider pinning inside the diagnostic module is forbidden.

### 5.2 Supervisor public test

The public-test path must:

- preserve its current public/internal sensitivity boundary;
- preserve bounded request/token behavior;
- invoke canonical execution exactly once per logical request, aside from canonical executor-owned retry/fallback behavior;
- not independently decide DeepSeek vs Scaleway availability, pricing, budget, credential readiness, or fallback;
- expose only sanitized canonical outcome metadata required by the existing response contract;
- fail closed if canonical execution rejects the request.

## 6. Failure-mode requirements

Implementation and tests must explicitly cover:

1. **Direct-dispatch regression** — neither debt module constructs a concrete external adapter or calls `.complete(...)` directly.
2. **Policy duplication drift** — local diagnostic code cannot become the deciding privacy/egress/budget authority.
3. **Provider-selection drift** — Supervisor does not maintain a second DeepSeek/Scaleway selection/fallback implementation.
4. **Credential leakage** — diagnostic responses/errors/logging contain no API key or credential value and diagnostic modules do not acquire credential-bearing adapters directly.
5. **Budget/ledger split brain** — one logical external execution produces canonical attempt/usage/ledger evidence only; no parallel manual accounting path remains.
6. **Metadata identity loss** — request/correlation/workspace/task identity used by the existing route remains present where the current contracts provide it.
7. **Semantic widening** — moving to the shared executor does not broaden public/internal diagnostic sensitivity or uncap output.
8. **Hidden fallback bypass** — canonical rejection never triggers a direct adapter call or alternate concrete-provider helper.
9. **Test escape** — tests may inject/stub the canonical execution seam but no production flag/helper restores direct dispatch.
10. **Allowlist staleness** — the exact 129 AE002 exceptions are removed once runtime tests prove closure, and the architecture gate fails if either direct-dispatch pattern is reintroduced.
11. **Scope explosion** — no unrelated provider/router/credential/store/schema/UI refactor is included.

## 7. Required deterministic evidence

Before implementation may be accepted, the candidate exact head must provide focused evidence for both debt owners.

Minimum proof set:

- existing focused tests updated to assert preserved public behavior through the canonical execution boundary;
- canonical success mapping for each diagnostic surface;
- canonical validation/config/route/provider rejection mapping;
- a test proving a rejection cannot fall through to direct provider dispatch;
- a test proving the diagnostic module does not own concrete provider selection/adapter completion after migration;
- budget/usage/ledger behavior asserted at the canonical seam where current test infrastructure exposes it, avoiding duplicate manual accounting assertions that would themselves encode a second authority;
- request/correlation/task metadata continuity where those fields are part of the current surface contract;
- architecture-enforcement self-test and repository gate green after deleting only the exact 129 debt exceptions;
- focused Ruff/Pytest for affected backend files/tests, followed by the repository-required frozen-head terminal gates.

Static grep alone is insufficient runtime proof, and green runtime tests alone are insufficient if the architecture debt exceptions remain stale.

## 8. Acceptance criteria

129 implementation is acceptable only when all are true on the exact candidate head:

1. Both exact 128-owned side channels dispatch through the canonical execution/provider/egress spine.
2. Neither debt module constructs a concrete external provider adapter or directly calls `.complete(...)`.
3. Supervisor no longer owns a parallel provider-selection/fallback algorithm for external dispatch.
4. Existing diagnostic safety boundaries and bounded-request semantics are preserved or made strictly safer with documented compatibility evidence.
5. Canonical egress, budget/usage, provider routing/fallback and AI-job ledger authority is not duplicated locally.
6. Canonical rejection fails closed with no direct-provider escape.
7. No credential or secret authority is moved into a diagnostic product surface.
8. Focused deterministic tests cover success, rejection, no-bypass and compatibility behavior for both surfaces.
9. The two exact 129 architecture-enforcement exceptions are removed only after the runtime proof is green, and architecture enforcement remains green without them.
10. No unrelated provider/router/schema/store/UI or 130–134/113–126 implementation is bundled.
11. All repository-required terminal gates are green on the exact merge head with no unresolved material review finding.

## 9. Non-goals

- no new provider SDK or provider family;
- no credential-store or secret-transport redesign;
- no new egress confirmation/policy system;
- no durable store/schema/migration;
- no AI router rewrite;
- no broad budget/ledger refactor;
- no change to local Ollama ownership merely because it uses HTTP;
- no removal of diagnostic endpoints unless a separate fresh authority permits it;
- no broad cleanup of unrelated network calls or provider adapters;
- no implementation of 130–134 or 113–126.

## 10. Readiness gate

A separate readiness decision is mandatory because 129 closes a security/egress boundary. Readiness must re-read fresh master and confirm, before changing `STATUS.md` to `ready`:

- the two debt owners still match this inventory or any drift is explicitly reconciled;
- the canonical execution route(s) required by both diagnostics are concretely identified from current provider configuration;
- any proposed shared execution/provider-registry change is proven necessary and bounded;
- exact focused test paths and architecture-exception entries are identified;
- no dependency or overlapping active PR invalidates the implementation boundary;
- implementation can satisfy the acceptance criteria without inventing new credential/egress/routing authority.

Until that readiness decision is accepted and `STATUS.md` is `ready`, implementation remains forbidden.

## Evidence inspected

- `docs/specs/129-egress-side-channel-closure-1.md` at exact master;
- `backend/app/modules/ai/deepseek_provider_smoke.py`;
- `backend/app/modules/ai/supervisor_public_test.py`;
- `backend/app/modules/ai/execution.py`;
- `backend/app/modules/ai/provider_registry.py`;
- `configs/ai_providers.yaml`;
- `configs/architecture_enforcement.json`;
- focused DeepSeek smoke tests and current architecture-enforcement checker;
- canonical post-112 hardening/lifecycle authority.
