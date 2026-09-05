# 124 PROVIDER-SETTINGS-GENERIC-1

Status: full specification / planning authority. Implementation remains unauthorized until a separate readiness decision moves the canonical `STATUS.md` row to `ready`.

Definition authority merged through PR #553. Full-spec derivation basis: exact `master` `794b305eab35fcafeded773de2bccbbd9700e515`.

## Purpose

Provide one bounded Settings-facing provider/integration surface over the already accepted provider registry, secure-secret, external-egress/policy, usage/budget/accounting, system/status, and explicit context/action owners. 124 is a projection and operator-interaction seam only. It does not become a second provider registry, credential store, health authority, routing engine, budget ledger, usage ledger, egress path, provider-test authority, or Jarvis context authority.

The accepted upstream owners remain `015`, `018`, `021`, `059b`, `061a`, `082`, `094`, and `111`.

## Fresh runtime evidence and V0 boundary

Fresh master shows that provider identity/configuration is canonically loaded from `configs/ai_providers.yaml` through `backend/app/modules/ai/provider_registry.py`. The registry owns provider IDs, provider kind/execution class, enabled/network requirements, base URL, `api_key_ref`, timeout, provider token/cost caps, registered models, route classes, pricing metadata, and fallback chains.

Secure persisted credential mutation is not generic. `backend/app/modules/secrets/storage.py` and `backend/app/modules/secrets/service.py` own a hardened `ScalewaySecretStore` and Scaleway-specific save/delete/status operations. `resolve_secret_ref()` can resolve generic `env:*` references for server-side use, but persisted write/delete authority is implemented only for `SCALEWAY_API_KEY`. Therefore 124 MUST NOT generalize that store or claim persisted mutation support for DeepSeek, GLM, Kimi, or future providers.

The current registry contains local/synthetic providers with no credential reference; `scaleway` with `env:SCALEWAY_API_KEY`, for which 082 supports environment or secure-persisted effective state plus persisted save/delete; and `deepseek`, `glm`, and `kimi` with environment-backed credential references only.

The existing `frontend/src/pages/Settings.tsx` and `frontend/src/api/settings.ts` already own Settings presentation, canonical reload-after-mutation semantics, an explicit `uncertain` state after ambiguous mutation failure, and Scaleway credential save/delete without browser persistence or secret readback. 124 reuses that surface.

Fresh master ALSO contains `POST /ai/provider-smoke/run`. That action delegates through `AIGateway.run_provider_smoke()` to `deepseek_provider_smoke.run_provider_smoke()`, whose route is fixed to `external:deepseek` and whose contract is explicitly a DeepSeek-only diagnostic smoke path with bounded prompt/output, privacy/policy gates, canonical execution, events, and usage/accounting behavior. It is not a generic provider-settings test contract.

Therefore V0 does not add a generic `Test connection`, `Ping provider`, or sample-generation control. It MUST NOT relabel, widen, parameterize, or repurpose the existing DeepSeek smoke endpoint as a provider-agnostic test authority. The existing DeepSeek smoke remains unchanged and outside 124.

## Accepted V0 product behavior

### Provider catalogue projection

Settings may show a bounded catalogue projected from the canonical provider registry. The server, not the browser, resolves provider identity and source configuration.

The projection may expose only non-secret operator-relevant facts already owned upstream, including provider ID, kind/execution class, enabled state, network requirement, whether credentials are required, bounded model/capability identifiers, configured timeout/caps where useful, and canonical status/blocking facts exposed by accepted owners.

The frontend MUST NOT copy provider lists, model catalogues, fallback chains, prices, budget limits, or health state into a second static registry. Display labels may be presentation-only formatting of server-returned identifiers; they are not persisted provider truth.

The browser MUST NOT receive credential values, masked previews derived from credential values, provider request headers, arbitrary secret references, or provider URLs for direct invocation.

### Credential status

Credential status is provider-scoped and secret-free. The server resolves `provider_id` through the canonical provider registry and resolves its existing credential reference through the accepted secret boundary.

The projection must distinguish at least:

- `not_required` for providers without an API-key reference;
- `configured_environment` when the effective secret comes from environment;
- `configured_secure_persisted` only where the existing secure-persistence owner actually supports the credential;
- `absent` when no credential is available;
- `corrupted` / `unavailable` where the secure-storage owner exposes those states;
- `unknown` when truthful state cannot be determined.

No response, event, log, analytics payload, browser state, error body, or Jarvis context may contain the credential value or a preview derived from it.

### Credential mutation capability

Credential mutation is capability-based and fail-closed.

On this derivation head, only `scaleway` may expose Settings credential replace/delete because only Scaleway has accepted secure-persisted mutation support in 082. The server derives that capability from the accepted credential owner and canonical provider identity; the browser must not infer editability from `api_key_ref` or provider name.

For `deepseek`, `glm`, and `kimi` on this head, Settings may show credential presence/status and environment-managed state, but no persisted save/replace/delete control is usable. 124 MUST NOT create generic file/key storage, mutate process environment, edit `.env`, or broaden `ScalewaySecretStore` into a multi-provider secret database.

If later master adds an accepted persisted-secret owner for another provider, readiness must explicitly revalidate and include it. This full spec does not automatically grant that capability.

### Mutation identity and completion semantics

V0 retains the existing Scaleway-specific mutation endpoint family rather than inventing a generic mutation facade. The browser MUST NOT submit a filesystem path, environment-variable name, `secret_id`, or arbitrary secret reference.

Unknown providers, credential-not-required providers, and providers without accepted persisted-mutation capability fail closed before any write/delete.

The existing completion contract remains:

1. submit exactly one explicit operator mutation;
2. never automatically retry an ambiguous save/delete request;
3. re-read canonical state after a definitive response when possible;
4. if mutation outcome or canonical reload is ambiguous, enter explicit `uncertain` state and block further credential mutation until canonical state is reloaded;
5. never infer success from submitted or optimistic frontend state.

Delete of an already-absent persisted Scaleway credential remains idempotent under 082. Environment override remains authoritative: when `SCALEWAY_API_KEY` is supplied by environment, persisted replacement/deletion cannot be presented as changing the effective credential.

### Provider status, usage, and budget projection

124 may compose availability/status, usage, and budget information only from existing accepted owners. Any browser-facing projection delegates rather than recomputes.

Provider config facts come from the canonical registry; credential presence from the accepted secret resolver/status owner; external policy/budget gates from existing AI policy/budget owners; usage totals from canonical accounting/job data; budget values from canonical settings/registry/accounting owners; system information from the existing system owner.

The frontend must not derive a new usability/health truth from partial inputs. Disabled, credential-missing, policy-blocked, budget-blocked, unavailable, or unknown providers must not be rendered healthy because one subprojection is green. Partial/unknown/unavailable source states remain explicit.

## HTTP/API boundary

Read-side V0 is frozen to one bounded projection on the existing AI router: `GET /ai/provider-settings` (consumed by the existing frontend API client as `/ai/provider-settings`). It returns provider catalogue plus secret-free credential/status/capability facts sourced from existing owners. It MUST NOT persist a provider snapshot as truth.

The response model must be typed in the existing AI model boundary and include, per provider, enough information to render canonical provider identity, enabled/network state, credential requirement/state, credential mutation capability, and accepted status/blocking facts without exposing raw `api_key_ref` or secret material.

Credential mutation remains on the existing 082 Scaleway endpoints. No generic credential mutation endpoint is added by V0.

The existing `POST /ai/provider-smoke/run` remains DeepSeek-only and unchanged. `GET /ai/provider-settings` MUST NOT call it, probe providers, perform provider egress, or convert diagnostic smoke output into health truth.

API errors exposed to the browser use bounded typed details and never serialize raw exception bodies that could contain request headers, credentials, provider response payloads, filesystem paths, or secret values.

## Frontend boundary

Reuse the existing Settings page and API client. Expected implementation touch points are a bounded subset of:

- `frontend/src/pages/Settings.tsx`;
- `frontend/src/api/settings.ts`;
- existing Settings styles/components only as required;
- the minimum existing AI route/model/service code needed for `GET /ai/provider-settings`;
- focused backend/frontend tests.

Do not create a second router, global settings store, provider registry, provider SDK, credential cache, context basket, design system, or top-level provider-management application.

Credential input remains transient component state only for an accepted mutable provider. It is cleared after submission/unmount and never written to local/session storage, URL/query state, analytics, logs, or Jarvis context.

Async provider selection, catalogue/status refresh, and credential mutation/reload are generation/identity guarded so a response for provider A cannot overwrite provider B or a newer canonical snapshot.

## Deterministic acceptance matrix

| Case | Required result |
| --- | --- |
| provider catalogue loads | identities/capabilities come from canonical server registry; no frontend provider-truth copy |
| local/synthetic provider | credential `not_required`; no credential mutation affordance |
| Scaleway environment key present | environment-managed status; persisted mutation cannot be shown as changing effective key |
| Scaleway secure-persisted key present | presence shown without value/preview; replace/delete through 082 only |
| Scaleway persisted store corrupted/unavailable | explicit corrupted/unavailable state; no false configured/healthy state |
| DeepSeek/GLM/Kimi env key present | configured/environment-managed; no persisted save/delete affordance |
| DeepSeek/GLM/Kimi env key absent | absent; no generic secret store or `.env` mutation offered |
| unknown provider ID | fail closed; no status/mutation cross-binding |
| provider selection changes during async read | stale response ignored; new provider remains authoritative |
| mutation response/reload ambiguous | explicit `uncertain`; no auto-retry or optimistic configured state |
| duplicate delete of absent Scaleway persisted key | existing idempotent absent result retained |
| provider disabled/policy/budget blocked | truthful blocked state; no client-derived healthy state |
| partial/unavailable status source | partial/unknown/unavailable visible; stale green state not retained |
| usage/budget display | canonical server-owned values only; no client shadow ledger |
| browser network behavior | JarvisOS backend only; no direct provider request |
| secret handling | no readback/preview/log/URL/browser persistence/Jarvis-context secret material |
| generic live provider test | no V0 affordance or generic endpoint; existing DeepSeek smoke remains unchanged |

## Required deterministic tests

Readiness must freeze exact test paths. Implementation evidence must prove at least:

1. provider catalogue delegates to the canonical provider registry and does not invent unknown providers;
2. credential status for no-key, environment-backed, Scaleway persisted, corrupted, unavailable, and absent states is secret-free;
3. API serialization contains neither credential values nor masked previews derived from them;
4. only accepted persisted-mutation capability is exposed; on this head only Scaleway qualifies;
5. provider-scoped UI cannot redirect mutation to arbitrary env vars, secret IDs, providers, or paths;
6. environment override remains authoritative and visible;
7. ambiguous mutation is not automatically retried and results in canonical reload/`uncertain` behavior;
8. async provider/catalogue/status/mutation responses cannot cross-bind or overwrite newer provider identity/state;
9. policy/budget/usage/status projections consume canonical owners without second calculations or health truth;
10. browser/API tests prove no direct provider URL, provider SDK, browser secret persistence, or new generic live-test egress;
11. regression proof confirms existing DeepSeek `/ai/provider-smoke/run` remains DeepSeek-only and is not called/generalized by 124;
12. existing Scaleway secure-storage hardening/redaction tests plus normal repository CI and focused frontend tests/build remain green.

Because this changes credential/provider operator behavior, final implementation acceptance requires independent exact-head semantic review. Readiness must explicitly decide the exact-head real-browser proof requirement; if implementation materially changes provider selection, credential mutation, or uncertain/error rendering, browser proof is expected unless deterministic lower-layer evidence proves the full operator interaction.

## Security and failure modes

Implementation must fail closed against secret disclosure; accidental genericization of Scaleway persistence; browser-to-provider egress; provider A responses/mutations binding to provider B; arbitrary env/path/secret-ID injection; retry/optimism after ambiguous mutation; environment override mislabeled as persisted state; partial status rendered healthy; frontend provider/model/price/budget drift; duplicated usage/budget calculations; stale green status; accidental generalization or silent invocation of the DeepSeek smoke path; unmetered probes; and credentials entering Jarvis context/model evidence.

## Non-goals

- no new credential store or generic persisted-secret database;
- no plaintext/masked secret read API;
- no `.env` or process-environment mutation;
- no provider adapter or provider SDK work;
- no provider/model registry redesign;
- no routing/fallback/provider-selection redesign;
- no usage/budget/accounting or health authority;
- no generic provider test and no modification/generalization of the existing DeepSeek smoke;
- no automatic discovery, rotation, validation, or background provider action;
- no browser direct provider/GitHub/network authority;
- no model-scoped key/Hermes claim;
- no secret/context integration;
- no unrelated repository/execute/merge authority;
- no general Settings redesign.

## Readiness gate

124 remains `planned` after this full spec. A separate readiness decision must re-read then-current master and freeze exact implementation files/routes/tests plus browser-proof requirements. It must verify that no intervening change altered provider credential persistence, DeepSeek smoke/provider-test authority, provider registry semantics, Settings ownership, or policy/budget/accounting contracts.

Readiness may move 124 to `ready` only if implementation remains a bounded projection over existing authorities and deterministic evidence can prove secret redaction, provider identity binding, stale/ambiguous mutation behavior, canonical delegation, absence of direct browser/provider egress, and non-generalization of the existing DeepSeek smoke.

If readiness discovers that generic persisted credentials, generic live provider tests, new adapters/storage, or new policy/accounting authority are required, it must stop and derive separate prerequisite authority rather than widen 124.

No product-code implementation, provider call, credential migration, provider-config mutation, or registry-state promotion is authorized by this full specification alone.
