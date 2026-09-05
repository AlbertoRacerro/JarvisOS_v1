# 124 PROVIDER-SETTINGS-GENERIC-1

Status: full specification / planning authority. Implementation remains unauthorized until a separate readiness decision moves the canonical `STATUS.md` row to `ready`.

Definition authority merged through PR #553. Full-spec derivation basis: exact `master` `794b305eab35fcafeded773de2bccbbd9700e515`.

## Purpose

Provide one bounded Settings-facing provider/integration surface over the already accepted provider registry, secure-secret, external-egress/policy, usage/budget/accounting, system/status, and explicit context/action owners. 124 is a projection and operator-interaction seam only. It does not become a second provider registry, credential store, health authority, routing engine, budget ledger, usage ledger, egress path, or Jarvis context authority.

The accepted upstream owners remain `015`, `018`, `021`, `059b`, `061a`, `082`, `094`, and `111`.

## Fresh runtime evidence and resulting V0 boundary

Fresh master shows that provider identity/configuration is canonically loaded from `configs/ai_providers.yaml` through `backend/app/modules/ai/provider_registry.py`. The registry already owns provider IDs, provider kind/execution class, enabled/network requirements, base URL, `api_key_ref`, timeout, provider token/cost caps, registered models, route classes, pricing metadata, and fallback chains.

Fresh master also shows that secure persisted credential mutation is currently not generic. `backend/app/modules/secrets/storage.py` and `backend/app/modules/secrets/service.py` own a hardened `ScalewaySecretStore` and Scaleway-specific save/delete/status operations. `resolve_secret_ref()` can read generic `env:*` references for server-side provider use, but persisted write/delete authority is only implemented for `SCALEWAY_API_KEY`. Therefore this full spec MUST NOT silently generalize the secure store or claim persisted mutation support for DeepSeek, GLM, Kimi, or future providers.

The current provider registry contains:

- local/synthetic providers with no credential reference;
- `scaleway` with `env:SCALEWAY_API_KEY`, for which 082 already supports environment or secure-persisted effective state plus persisted save/delete;
- `deepseek`, `glm`, and `kimi` with environment-backed credential references only on fresh master.

The existing `frontend/src/pages/Settings.tsx` and `frontend/src/api/settings.ts` already provide the Settings owner, canonical reload-after-mutation semantics, an `uncertain` state after ambiguous mutation failure, and Scaleway credential save/delete without browser persistence or secret readback. 124 reuses that surface rather than creating a new Settings application or store.

No already-governed provider connection-test action exists in the inspected runtime. V0 therefore explicitly EXCLUDES live provider testing. Adding a test button that performs provider egress would require a separately derived server action with explicit policy, budget, accounting, timeout, retry, and side-effect semantics.

## Accepted V0 product behavior

### Provider catalogue projection

The Settings surface may show a bounded provider catalogue projected directly from the canonical provider registry. The server, not the browser, resolves the provider identity and source configuration.

For each provider, the projection may include only non-secret operator-relevant facts already owned by the registry or canonical status owners, such as:

- `provider_id`;
- provider kind / execution class;
- enabled state;
- whether network access is required;
- whether a credential reference is required;
- bounded model/capability identifiers already present in the provider registry;
- configured timeout and provider budget caps when useful to the Settings presentation;
- canonical provider availability/policy/budget status already exposed by accepted owners.

The frontend MUST NOT copy the provider list, model catalogue, fallback chains, prices, budget limits, or health state into a second static registry. Display labels may be derived presentation-only formatting from server-returned identifiers; they are not persisted provider truth.

The browser MUST NOT receive credential values, provider request headers, secret-reference internals that would create a new mutation authority, or arbitrary provider URLs intended for direct invocation. A server-returned non-secret base URL may be omitted unless it is materially useful to the accepted Settings surface.

### Credential status

Credential status is provider-scoped but secret-free. The server resolves the selected `provider_id` through the canonical provider registry and then resolves its existing `api_key_ref` through the accepted secret boundary.

The Settings projection must distinguish at least:

- `not_required` for providers without an API-key reference;
- `configured_environment` when the accepted effective secret comes from an environment variable;
- `configured_secure_persisted` only where the existing secure-persistence owner actually supports that credential;
- `absent` when no credential is available;
- `corrupted` / `unavailable` where the existing secure-storage owner exposes those states;
- `unknown` when a bounded server-side projection cannot determine a truthful state.

No response, event, log, analytics payload, browser state, error body, or Jarvis context may contain the credential value or a masked preview derived from it. Presence/status is sufficient.

### Credential mutation capability

Credential mutation is capability-based and fail-closed.

On this full-spec derivation head, only `scaleway` is allowed to expose Settings credential `replace` / `delete`, because only Scaleway has accepted secure-persisted mutation support in 082. The server MUST derive this capability from its accepted credential owner and canonical provider identity; the browser must not infer editability merely from `api_key_ref` or provider name.

For environment-backed providers without an accepted persisted-secret mutation owner (`deepseek`, `glm`, `kimi` on fresh master):

- Settings may show credential presence/status;
- Settings must show that the effective credential is environment-managed when present;
- no save/replace/delete control is rendered as usable;
- 124 MUST NOT add generic file/key storage, mutate process environment, edit `.env`, or broaden `ScalewaySecretStore` into a multi-provider secret database.

If future canonical master adds an accepted persisted-secret owner for another provider, readiness/implementation must revalidate and explicitly include that capability; this full spec alone does not automatically authorize it.

### Credential mutation identity and completion semantics

Every accepted mutation is bound to the provider identity visible to the operator. For V0, the implementation may retain the existing Scaleway-specific endpoint family or add a thin provider-scoped Settings facade only if the server resolves `provider_id=scaleway` to the existing 082 operation. The browser MUST NOT submit a filesystem path, environment variable name, `secret_id`, or arbitrary secret reference.

Unknown provider IDs, credential-not-required providers, and providers without accepted persisted mutation capability fail closed before any secret write/delete.

The existing reload-after-mutation contract is retained:

1. submit exactly one explicit operator mutation;
2. do not automatically retry an ambiguous save/delete request;
3. re-read canonical status after a definitive response when possible;
4. if the mutation outcome or canonical re-read is ambiguous, enter an explicit `uncertain` state and block further credential mutation until canonical state is reloaded;
5. never infer success from the submitted value or optimistic frontend state.

Delete of an already-absent persisted Scaleway credential remains idempotent according to the existing 082 owner. Save/replace remains one bounded operation; no client retry loop is authorized.

Environment override remains authoritative: if `SCALEWAY_API_KEY` is supplied by the environment, persisted replacement/deletion cannot be presented as changing the effective credential. Existing 082 environment-override failure semantics must remain explicit.

### Provider status, usage, and budget projection

124 may compose provider availability/status, usage, and budget information only from existing accepted owners. It may add a thin browser-facing projection if an existing endpoint is insufficient, but the projection must delegate rather than recompute.

In particular:

- provider enabled/network/execution-class/config facts come from the canonical provider registry;
- credential presence comes from the accepted secret resolver/status owner;
- external-provider policy permission and budget gate come from existing AI/provider policy owners;
- usage totals come from canonical accounting/job data;
- provider/global budget values come from canonical settings/registry/accounting owners;
- system information comes from the existing system owner.

The frontend must not calculate provider usability from partial inputs. A provider that is disabled, credential-missing, policy-blocked, budget-blocked, unavailable, or unknown must not be rendered as healthy/usable because another subprojection is green.

The server response should preserve typed source-state fields where practical so the UI can render `available`, `blocked`, `unavailable`, `unknown`, or `partial` truthfully without creating a client-side health algorithm.

## Explicit exclusion: live provider test

V0 has no `Test connection` / `Ping provider` / sample-generation action.

Fresh inspection found no accepted server-side test operation with explicit egress, policy, budget, accounting, timeout, retry/idempotency, and response-redaction semantics. A generic HTTP probe, model-completion probe, browser fetch, SDK call, or unmetered provider request is outside 124.

If a later slice needs live testing, it must first derive or reuse a governed server action and prove:

- existing egress allowlist/policy enforcement;
- provider credential resolution server-side only;
- bounded timeout and request size;
- explicit spend/token accounting when a billable model call is used;
- no automatic retry after ambiguous completion;
- redacted errors and no secret/header echo;
- typed unavailable/policy-blocked/budget-blocked/partial outcomes.

## HTTP/API boundary

Implementation may add the minimum typed read projection needed by the existing Settings page. Prefer a bounded Settings/provider route family over a generic RPC endpoint.

An accepted read response may compose registry, credential-status, policy/budget/status, usage, and system facts, but each field must be sourced from its existing owner. The route must not persist its own provider snapshot as truth.

Any credential mutation route must delegate to 082 and expose only accepted mutation capabilities. On the derivation head this means Scaleway secure-persisted replace/delete only. A provider-scoped facade is acceptable only if its allowlist/capability mapping is server-owned and closed; it must not turn arbitrary `api_key_ref` strings into persisted storage keys.

API errors exposed to the browser must use bounded typed codes/details and must never serialize raw exception bodies that could contain request headers, credentials, provider response payloads, filesystem paths, or secret values.

## Frontend boundary

Reuse the current Settings page and its API client. Expected implementation touch points are a bounded subset of:

- `frontend/src/pages/Settings.tsx`;
- `frontend/src/api/settings.ts`;
- existing Settings styles/components only when required for the bounded provider list/status controls;
- the minimum backend projection/routes/service code required to delegate to accepted owners;
- focused backend/frontend tests.

Do not create a second router, global settings store, provider registry, provider SDK, credential cache, context basket, design system, or new top-level provider-management application.

Credential input remains transient component state only for a provider with accepted mutation capability. It must be cleared after submission/unmount and never written to local/session storage, URL/query state, analytics, logs, or Jarvis context.

Async provider selection, catalogue refresh, status refresh, usage/budget refresh, and credential mutation/reload must be generation/identity guarded so a response for provider A cannot overwrite provider B or a newer canonical snapshot.

## Deterministic acceptance matrix

| Case | Required result |
| --- | --- |
| provider catalogue loads | identities/capabilities come from canonical server registry; no frontend provider truth copy |
| local/synthetic provider | rendered as credential `not_required`; no credential mutation affordance |
| Scaleway environment key present | status says environment-managed; persisted mutation cannot be shown as changing effective key |
| Scaleway secure-persisted key present | presence shown without value/preview; replace/delete capability available through 082 only |
| Scaleway persisted store corrupted/unavailable | explicit corrupted/unavailable state; no false configured/healthy status |
| DeepSeek/GLM/Kimi env key present | configured/environment-managed status; no persisted save/delete affordance |
| DeepSeek/GLM/Kimi env key absent | absent status; no generic secret store or `.env` mutation offered |
| unknown provider ID | fail closed; no credential/status/mutation cross-binding |
| provider selection changes during async read | old response discarded/ignored; new provider remains authoritative |
| mutation response/reload ambiguous | explicit `uncertain`; no auto-retry or optimistic configured state |
| duplicate delete of absent persisted Scaleway key | existing idempotent absent result retained |
| provider disabled/policy blocked/budget blocked | truthful blocked state; no client-derived healthy state |
| partial/unavailable status source | partial/unknown/unavailable visible; previous green state not retained as current |
| usage/budget display | canonical server-owned values only; no client recomputation/shadow ledger |
| browser network behavior | JarvisOS backend only; no direct provider request |
| secret handling | no GET/readback, masked preview, logs, URL/browser persistence, or Jarvis context secret material |
| live provider test | no V0 affordance or endpoint added |

## Required deterministic tests

Readiness must freeze exact test paths, but implementation evidence must materially prove at least:

1. provider catalogue projection delegates to the canonical provider registry and rejects/does not invent unknown providers;
2. credential status for no-key, environment-backed, Scaleway persisted, corrupted, unavailable, and absent states is secret-free;
3. API serialization contains neither credential values nor masked previews derived from them;
4. only providers with accepted persisted-mutation capability expose mutation; on the derivation head only Scaleway qualifies;
5. provider-scoped mutation cannot redirect to an arbitrary env var, secret ID, provider, or filesystem path;
6. environment override remains authoritative and visible;
7. ambiguous mutation failure is not automatically retried and results in canonical reload/`uncertain` behavior;
8. async provider/catalogue/status/mutation responses cannot cross-bind or overwrite newer provider identity/state;
9. policy/budget/usage/status projections consume canonical owners and do not introduce a second calculation or health truth;
10. browser/API tests prove no direct provider URL, provider SDK, browser secret persistence, or live-test egress is introduced;
11. existing Scaleway secure-storage hardening and redaction tests remain green;
12. normal repository CI and focused frontend build/tests pass on the exact implementation head.

Because this changes credential/provider operator behavior, final implementation acceptance requires independent exact-head semantic review. Readiness must also decide whether exact-head real-browser proof is required; if the accepted implementation materially changes provider selection, credential mutation, or uncertain/error rendering, browser proof is expected unless deterministic lower-layer evidence can prove the complete operator interaction.

## Security and failure modes

Implementation must fail closed against:

- secret disclosure through API/readback/log/error/analytics/browser persistence/context;
- accidental genericization of Scaleway persisted storage into an unreviewed multi-provider secret store;
- browser-to-provider egress or browser-owned provider credentials;
- provider A mutation/status completing against provider B after selection changes;
- arbitrary `api_key_ref`, environment-variable, path, or secret-ID injection;
- optimistic or retried credential mutation after timeout/partial failure;
- environment override being mislabeled as persisted/configurable state;
- disabled/policy-blocked/budget-blocked/unknown provider rendered healthy from partial evidence;
- frontend provider/model/catalogue/price/budget copies drifting from server owners;
- duplicated usage or budget calculations;
- stale green status surviving refresh failure;
- unmetered live provider tests, background probes, or side-effecting health checks;
- credentials entering Jarvis context or ordinary model evidence.

## Non-goals

- no new credential store or generic persisted-secret database;
- no plaintext/masked secret read API;
- no `.env` or process-environment mutation;
- no provider adapter or provider SDK work;
- no provider/model registry redesign;
- no routing/fallback/provider-selection policy redesign;
- no usage/budget/accounting authority;
- no health source of truth;
- no live provider test in V0;
- no automatic discovery, rotation, validation, or background provider action;
- no browser direct provider/GitHub/network authority;
- no model-scoped key/Hermes claim;
- no secret/context integration;
- no unrelated repository/execute/merge authority;
- no general Settings redesign.

## Readiness gate

124 remains `planned` after this full spec. A separate readiness decision must re-read then-current master and freeze exact implementation files/routes/tests plus the browser-proof requirement. It must verify that no intervening change has introduced or changed provider credential persistence, provider-test authority, provider registry semantics, Settings ownership, or policy/budget/accounting contracts.

Readiness may move 124 to `ready` only if the accepted implementation remains a bounded projection over existing authorities and the deterministic evidence above can prove secret redaction, provider identity binding, stale/ambiguous mutation behavior, canonical source delegation, and absence of direct browser/provider egress.

If readiness discovers that generic persisted credentials, live provider tests, new provider adapters, new storage, or new policy/accounting authority are required, it must stop and derive separate prerequisite authority rather than widening 124.

No product-code implementation, provider call, credential migration, provider-config mutation, or registry-state promotion is authorized by this full specification alone.
