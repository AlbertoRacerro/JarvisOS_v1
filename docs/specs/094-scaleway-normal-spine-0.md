# Spec 094 — SCALEWAY-NORMAL-SPINE-0

**Definition status:** complete implementation contract; implementation authority depends on the registry readiness decision in `094-readiness-2026-08-04.md`.

**Depends on:** 015, 018, 021, 059b, 061a, 061b, 082

**Authority:** spec 081 re-derivation rule for an active slice that proved non-implementable within its accepted boundary

**Target path:** `docs/specs/094-scaleway-normal-spine-0.md`

---

## 1. Purpose

Authorize the smallest normal-execution-spine Scaleway path required to finish the blocked Windows operator checkpoint for spec 082 without pretending that provider-routing work belonged to 082.

Spec 082 successfully added secure current-user Windows persistence for the already existing `SCALEWAY_API_KEY` secret reference. Its final checkpoint also requires one bounded external AI call after backend restart. Current `master` cannot perform that call through `run_ai_task` because no normal provider-registry route is bound to Scaleway. Adding such a route is explicitly outside 082: 082 requires no provider-registry configuration change and forbids route-authority changes.

094 resolves that contradiction as a separate authority slice. It does not reopen or revise the credential-persistence implementation. It authorizes one bounded Scaleway route and makes the pre-existing live smoke endpoints use the same normal execution, egress, reservation and ledger spine instead of retaining a second provider-dispatch path.

## 2. Queue re-derivation

094 is inserted immediately after blocked 082 and before freshly re-derived 070.

This changes one product decision from spec 081: the queue previously assumed 082 could finish its operator checkpoint before any additional backend authority slice. Repository evidence now proves that assumption false because 082 forbids the route change needed by its checkpoint.

All other 081 decisions remain unchanged:

- 070 remains unauthorized until 082 and 094 are complete;
- 066–068 and 080 remain frozen;
- one implementation front remains active at a time;
- 083–093 retain their existing order and scope;
- no frontend work is authorized by 094.

## 3. Current runtime facts

This definition is derived from `master` at `ec1353b7ffb0b63d669fb0254d31d0a879b977cf` and from the closed technical exploration PR #219.

1. `resolve_secret_ref("env:SCALEWAY_API_KEY")` already resolves the effective environment-or-secure-persisted Scaleway credential boundary implemented by 082.
2. `run_ai_task` resolves a concrete provider/model binding from the validated registry, applies the server-owned provider gate, creates the exact 059b egress packet/decision, reserves projected budget atomically, invokes the adapter, and records `ai_jobs`, attempts, usage and cost.
3. `configs/ai_providers.yaml` on `master` has no Scaleway binding; `external:cheap` is DeepSeek and must remain DeepSeek.
4. Existing live Scaleway smoke endpoints call the Scaleway adapter through a separate path and maintain legacy month-to-date counters in `ai_settings`.
5. Two paid Scaleway dispatch paths would create split reservation and accounting authority unless they are unified.
6. PR #219 demonstrated that adding a route while preserving two dispatch paths causes repeated gate, reservation, status and model-authority conflicts.
7. The Windows operator has already proven secure save, backend restart without `SCALEWAY_API_KEY`, and post-restart `secure_persisted / usable` status. Only the bounded normal-spine call and leak inspection remain.

## 4. Chosen architecture

### 4.1 One external dispatch spine

Every live Scaleway provider call after 094 uses the existing normal execution spine owned by `run_ai_task` and 059b.

- Add one dedicated route class: `external:scaleway`.
- Bind it to provider ID `scaleway` and one explicitly registered model.
- Do not add a fallback chain.
- Preserve `external:cheap` and `external:reasoning` unchanged.
- Synthetic smoke tests remain local and make no provider call.
- Existing live smoke and smoke-console endpoints become compatibility wrappers over the normal execution service. They must not invoke the Scaleway transport or adapter directly.

The wrappers may retain their existing request/response shapes, privacy checks and bounded case lists, but provider admission, egress, reservation, dispatch, usage and cost authority comes only from the normal spine.

### 4.2 Provider-specific adapter

Scaleway remains a provider-specific adapter because the existing provider owns:

- the effective 082 credential boundary;
- `SCALEWAY_BASE_URL` compatibility;
- provider-specific sanitized metadata;
- legacy smoke-facing status.

The registry must not overwrite it with the generic OpenAI-compatible adapter. The adapter still satisfies the provider-neutral request/response contract used by `run_ai_task`.

### 4.3 Model authority

The initial registered normal-route model is:

`gemma-4-26b-a4b-it`

The model ID must be represented once in the validated registry and passed as the concrete binding model to the adapter.

Legacy `SCALEWAY_MODEL` is not a global route override. It may be interpreted only inside a smoke compatibility wrapper and only when it resolves to a model already registered for provider `scaleway`. An unknown legacy value blocks that smoke request without breaking `registry_bindings()` or unrelated routes.

A route-specific environment override, if retained, must use a separate name such as `AI_ROUTE_SCALEWAY_MODEL`, must resolve uniquely to a registered Scaleway model assigned to `external:scaleway`, and must fail closed before provider dispatch.

### 4.4 Endpoint authority

`SCALEWAY_BASE_URL` remains the provider-specific endpoint override. It must be normalized and validated before transport. It does not change provider identity, route identity, model registration, pricing or egress policy.

### 4.5 Single accounting authority

Because all live Scaleway calls use the normal spine:

- projected tokens and cost are reserved through existing 059b reservations;
- completed usage is recorded in `ai_jobs` and `egress_attempts`;
- stale in-flight attempts use existing conservative reconciliation;
- there is no new aggregate-only smoke reservation and no second paid-call ledger;
- the legacy Scaleway counters remain historical compatibility data and are not incremented by new live calls after 094;
- status reports legacy historical counters separately where the current response contract requires them, but `usage_total_tokens`, cap decisions and `external_calls_allowed` use the authoritative normal-spine usage plus active/in-flight reservations.

No completed call may be counted twice.

## 5. Provider and route registry contract

The registry adds provider `scaleway` with:

- execution class `external_provider`;
- network required;
- base URL `https://api.scaleway.ai/v1`;
- secret reference `env:SCALEWAY_API_KEY`;
- bounded timeout;
- explicit provider token and cost caps;
- concrete model pricing metadata;
- route class `external:scaleway`.

The provider kind may be `scaleway` so the adapter factory retains the provider-specific adapter. Registry validation must continue to reject contradictory execution metadata, missing pricing, malformed secret references, unknown model overrides and duplicate route bindings.

## 6. Admission and execution gates

A concrete `external:scaleway` attempt is allowed only when all existing normal-spine gates pass:

1. AI policy is not disabled;
2. paid AI is enabled;
3. global monthly budget is positive and not exhausted;
4. the registry provider is enabled;
5. the effective 082 credential is present and usable;
6. provider token and cost caps remain available;
7. 059b sensitivity, sanitization and exact-packet policy allows the request;
8. projected global/provider budget can be reserved atomically;
9. any required first-use or policy confirmation ticket is valid and consumed through the existing ticket path;
10. the exact provider/model binding remains unchanged between decision, reservation and invocation.

Legacy smoke-only booleans may continue to disable the smoke compatibility endpoints, but they must not create a second budget or dispatch authority. The normal route itself is controlled by the existing server-owned provider, budget and 059b gates.

## 7. Compatibility wrappers

### 7.1 Live smoke matrix

`POST /ai/smoke-tests/run` in live mode:

- keeps the existing bounded harmless cases and privacy filtering;
- submits each externally allowed case through the shared execution service with `external:scaleway`;
- uses the existing 059b confirmation semantics rather than bypassing first-use authority;
- maps the task result back to the current smoke response shape;
- never calls the adapter directly.

### 7.2 Smoke console

`POST /ai/smoke-console/run`:

- retains prompt length, privacy and output-token bounds;
- submits the allowed prompt through the shared execution service with `external:scaleway`;
- maps the task result back to the current console response shape;
- never creates an independent reservation or updates counters before transport.

### 7.3 Failure semantics

HTTP 200 with no choice or empty completion text is a provider response error, not success. It must preserve dispatch evidence, reconcile the reservation conservatively, record a provider error and permit only the fallback behavior explicitly configured for the route. Since `external:scaleway` has no fallback chain, no alternate provider is attempted.

## 8. Status contract

`GET /ai/status` preserves all existing fields.

For active provider mode `scaleway`:

- `credential_status` reflects the effective 082 secret boundary;
- `external_calls_allowed` is computed from the same server-owned gate used by execution;
- `usage_total_tokens` reflects finalized normal-spine Scaleway usage plus budget-relevant active/in-flight reservations;
- legacy direct-smoke input/output fields remain visible as historical compatibility fields and must be labelled or documented as such;
- cap exhaustion and blocking reason must agree with the next normal-spine admission decision.

Status is informational and never creates permission.

## 9. Data and migration boundary

094 should not add a new state store. Existing `ai_jobs`, 059b packets/decisions/tickets/reservations/attempts and event records are the authority.

No migration is expected. If implementation proves that the current schema cannot represent a required normal-spine attempt, work stops and the spec returns to definition review; a migration must not be introduced silently.

## 10. Security and secret boundary

094 does not change 082 persistence, envelope, DPAPI, deletion, recovery or environment-precedence behavior.

Requirements:

- never serialize the key into a packet, job, reservation, event or error;
- never include key-derived previews;
- resolve the credential only at the provider boundary after all pre-dispatch gates that do not require plaintext;
- redact authorization headers and transport exceptions;
- leak tests scan responses, events, logs, SQLite and repository files using exact-key and unique-substring probes without printing the secret.

## 11. Out of scope

- frontend or Settings UI;
- new credential types or general vault work;
- automatic provider fallback;
- changing `external:cheap` or `external:reasoning`;
- model benchmarking or promotion;
- dynamic model discovery;
- remote access, multiuser permissions or cloud secret synchronization;
- spec 070 implementation;
- Hermes, MCP or frozen specs 066–068/080;
- changes to recovery snapshots;
- a second provider-call ledger or new schema.

## 12. Acceptance criteria

### 12.1 Registry and adapter

1. `external:scaleway` resolves uniquely to provider `scaleway` and the registered model.
2. `external:cheap` and `external:reasoning` remain byte-for-byte equivalent in resolved provider/model identity.
3. The Scaleway provider-specific adapter is retained; generic OpenAI-compatible providers remain generic.
4. The adapter uses the registry-selected model for normal routed work.
5. `SCALEWAY_BASE_URL` remains effective without changing route/model identity.
6. Legacy `SCALEWAY_MODEL` cannot break global or unrelated route resolution.
7. Any route-specific model override is distinct, registered and fail-closed.

### 12.2 Single execution spine

8. No live Scaleway endpoint invokes the adapter or transport outside the normal execution service.
9. Every live Scaleway call produces the normal flow/job, 059b packet/decision, reservation and attempt evidence.
10. First-use and other 059b confirmation requirements remain effective.
11. No fallback provider is attempted for `external:scaleway`.
12. Empty or malformed provider content is recorded as provider error, not success.

### 12.3 Accounting and status

13. Concurrent routed and smoke-wrapper calls cannot reserve beyond global, provider or Scaleway caps.
14. Active and in-flight reservations count before another call is admitted.
15. Final usage is reconciled exactly once from actual usage when available and conservatively otherwise.
16. Legacy counters are not incremented by new live calls and cannot double-count normal-spine jobs.
17. `/ai/status` agrees with the next execution gate for route-only, wrapper-only and mixed historical usage.
18. Counter reset or settings update cannot erase an identifiable in-flight reservation.

### 12.4 Credential and checkpoint

19. The route resolves `env:SCALEWAY_API_KEY` through the effective 082 secret boundary.
20. A real Windows current-user DPAPI credential remains usable after backend restart without environment or re-entry.
21. One bounded post-restart `run_ai_task` call through `external:scaleway` succeeds or yields a provider-auth/transport error with proof that the persisted credential reached the provider boundary; a configuration or route mismatch is not acceptance.
22. No secret material appears in responses, logs, events, SQLite or repository files.
23. All temporarily changed operator settings are restored after the checkpoint.

### 12.5 Authority and regression

24. No frontend, recovery, promotion, sensitivity, fallback or unrelated route authority changes.
25. Existing synthetic/local/provider registry, egress and token-flow suites remain green.
26. CI performs no live provider call and requires no real Windows account or key.
27. The implementation PR identifies the exact 082 checkpoint evidence it enables but does not claim 082 complete before the Windows operator proof.

## 13. Required automated tests

- default registry loads with the Scaleway route and unchanged existing routes;
- provider-specific adapter factory selection;
- normal route passes the concrete registered model and endpoint;
- legacy smoke-model override isolation;
- route-specific override positive and negative validation;
- missing/corrupt credential blocks before transport;
- live smoke and console wrappers cannot call transport directly;
- first-use confirmation and ticket resume through 059b;
- projected-budget concurrency and reservation exhaustion;
- actual, estimated and stale in-flight reconciliation;
- route-only and wrapper-originated job accounting;
- status/execution agreement;
- empty/malformed completion rejection;
- exact packet/model identity through fallback index zero;
- no fallback for `external:scaleway`;
- secret leak scans using test-only sentinels;
- full backend suite and Ruff;
- Windows-only live checkpoint remains manual and is never run in CI.

## 14. Manual Windows checkpoint

After the 094 implementation is merged:

1. update only the clean checkpoint worktree to exact `master`;
2. verify `SCALEWAY_API_KEY` is absent from the process environment;
3. start the backend under the same Windows user that persisted the credential;
4. confirm `/secrets/scaleway/status` reports `secure_persisted / usable` without re-entry;
5. save the current AI settings for restoration;
6. enable only the minimum policy/budget values needed for one bounded call;
7. submit `run_ai_task` with route `external:scaleway`, harmless prompt `Reply with the word OK.`, and maximum output eight tokens;
8. complete any normal 059b confirmation ticket through the existing endpoint;
9. capture job, flow, packet, decision, reservation, attempt, provider/model, usage and cost evidence;
10. perform exact-key and unique-substring leak scans without printing the key;
11. restore all changed settings;
12. record the checkpoint in a documentation-only reconciliation PR that marks both 094 and 082 complete and then unlocks fresh 070 derivation.

## 15. Minimum-necessary test

**Required outcome:** complete the already mandated 082 Windows checkpoint through the existing normal execution and egress authorities.

**Can the outcome be reached on current master?** No. No normal route is bound to Scaleway.

**Can 082 authorize the missing route?** No. 082 explicitly forbids route-authority and registry-configuration changes.

**Smallest authorized change:** one dedicated no-fallback Scaleway route plus conversion of existing live smoke entry points into wrappers over the same normal spine, so there is only one paid-call reservation and ledger authority.

**Why not keep the #219 architecture?** It retained two paid dispatch paths and therefore required parallel gate, reservation, accounting and status logic. Review repeatedly demonstrated that this was not independently safe or minimal.
