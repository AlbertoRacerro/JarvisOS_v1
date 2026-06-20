# 0E-B2 Foundation Refactor Readiness Review

## 1. Executive Judgement

JarvisOS is ready for **0E-C AI Provider Abstraction Design**, but not for multi-provider implementation, Supervisor AI UI, BlueRev modeling, runner UI, or broader workbench features.

The foundation has crossed from prototype into infrastructure. The current codebase has enough real behavior to expose structural pressure:

- AI safety is strong for smoke-test scope, but the code is still Scaleway-shaped.
- Data infrastructure is better after 0E-B, but schema migration is still lightweight and should not be stressed too hard before formal migration tooling.
- Python Runner V0 is useful and controlled, but `runner/service.py` is already too dense for another model kind.
- Frontend operator pages work, but `AIDraft.tsx` and `api/client.ts` are at the edge of temporary maintainability.
- Error and event conventions are inconsistent enough that provider abstraction should define shared primitives rather than add another branch.

Main judgement:

```text
Proceed to design-only 0E-C.
Do not implement new providers yet.
Keep BlueRev modeling paused.
```

## 2. Current Foundation Maturity Score

Overall maturity: **7 / 10 for a local-first foundation**.

| Area | Score | Severity | Action | Judgement |
| --- | ---: | --- | --- | --- |
| Backend module boundaries | 7 | medium | harden now | Boundaries are understandable, but AI and runner services are growing dense. |
| AI safety posture | 8 | high | keep | Defaults, gates, and tests are strong for smoke paths. |
| AI provider abstraction readiness | 5 | high | refactor during 0E-C | Current provider interface is too modeling-draft and Scaleway specific. |
| Secrets | 7 | medium | keep | Runtime-memory key path is safe for V0 and isolated enough. |
| Data infrastructure | 7 | medium | harden now | Migration ledger, indexes, and artifact readback exist; still lightweight. |
| Runner V0 | 7 | high | refactor later | Safe enough for one reviewed script, not for expansion without splitting service responsibilities. |
| API/error conventions | 5 | medium | refactor during 0E-C | Error shapes differ by module. |
| Frontend structure | 5 | medium | refactor during 0E-C | Operator UI works, but AI page/client should split before more AI surface. |
| Tests | 7 | medium | harden now | Good coverage, but fixtures/mocks duplicate heavily. |
| Documentation | 7 | low | document only | Honest and useful, but README is becoming milestone-accumulative. |

## 3. Immediate Blockers Before 0E-C

No blockers for **0E-C as a design milestone**.

Blockers before **0E-D multi-provider implementation**:

| Severity | Action | Blocker |
| --- | --- | --- |
| blocker | refactor during 0E-C | No provider-neutral adapter contract. |
| blocker | refactor during 0E-C | No provider/model registry or capability model. |
| blocker | refactor during 0E-C | Token/cost accounting is Scaleway-specific. |
| blocker | refactor during 0E-C | No shared gate pipeline object for budget -> privacy -> token -> provider. |
| high | refactor during 0E-C | API/error shapes are inconsistent across modules. |
| high | refactor during 0E-C | AI tests lack provider contract fixtures. |

## 4. Structural Risks Before Provider Abstraction

| Severity | Action | Risk | Why It Matters |
| --- | --- | --- | --- |
| high | refactor during 0E-C | Scaleway names are embedded in status, settings, token guard, UI, and tests. | A second provider would create copy/paste branching unless provider-neutral concepts are introduced first. |
| high | refactor during 0E-C | AI provider base interface only models `ModelingDraftRequest`. | Future Supervisor AI tasks need structured, provider-neutral request/response types. |
| high | refactor during 0E-C | Smoke tests and smoke console duplicate gates, usage accounting, and event payload assembly. | More provider paths will multiply this duplication. |
| high | refactor during 0E-C | Token metadata is named as smoke-test metadata. | Usage accounting must become provider-neutral before multi-provider work. |
| medium | refactor during 0E-C | `AIDraft.tsx` combines settings, secrets, smoke tests, smoke console, token meter, and draft request. | Future AI settings or Supervisor UI would turn it into a frontend monolith. |
| medium | refactor during 0E-C | `api/client.ts` mixes all domain types and calls. | Provider and workbench expansion need domain-specific API clients. |
| medium | harden now | Event payloads are free-form JSON. | Audit trail will need typed conventions before real AI analysis workflows. |
| medium | refactor later | Runner service handles too many responsibilities. | Fine for one script, risky for a second script or UI workflow. |
| low | document only | Docs still refer to historical milestones in the main README. | Usable now, but current-state orientation will get harder. |

## 5. Backend Module Assessment

### `backend/app/core`

Status: **keep / harden now**

Good:

- `config.py`, `paths.py`, and `database.py` keep the repo path and data root separate.
- `schema.py` centralizes schema and indexes.
- `database.py` now exposes schema migration status for `/system/info`.

Risks:

- `schema.py` is 292 lines and will grow quickly with another migration.
- `database.py` handles connection, initialization, migration recording, and info reporting.
- `core/errors.py` defines `AppError` but most modules still use local `ValueError`, `RunnerSafetyError`, or raw `HTTPException`.

Recommendation:

- During 0E-C, define a shared `AppError`/HTTP mapping convention before adding provider adapter endpoints.
- Later, split migration definitions from base schema if another two migrations land.

### `backend/app/modules/modeling`

Status: **keep / refactor later**

Good:

- Routes are thin.
- Service functions are direct and readable.
- Domain records are still intentionally minimal.

Risks:

- `service.py` repeats create/list patterns and local workspace checks.
- Errors are plain `ValueError`, mapped to string `detail`, unlike runner/secrets structured details.
- Event payloads include short record data; acceptable now, but later modeling data may become sensitive.

Recommendation:

- Do not refactor before 0E-C.
- Before ModelWorkbench work, add repository helpers and structured domain errors.

### `backend/app/modules/ai`

Status: **refactor during 0E-C**

Good:

- Routes are thin.
- Gateway remains the public AI boundary.
- Provider HTTP logic is isolated in `providers/scaleway.py`.
- Fake provider remains safe and deterministic.
- Smoke console does not become chat.

Risks:

- `budget.py` is Scaleway-specific.
- `token_guard.py` is Scaleway-specific and returns `SmokeTestTokenMetadata`.
- `models.py` mixes settings, draft, smoke-test, and console schemas.
- `smoke_tests.py` and `smoke_console.py` both implement gate/evaluate/log/account patterns.
- `providers/base.py` is too narrow for provider routing.

Recommendation:

- 0E-C should design provider-neutral primitives and only then move code.

### `backend/app/modules/secrets`

Status: **keep / refactor during 0E-C**

Good:

- Runtime-memory key storage avoids false secure persistence.
- Environment key priority is clean.
- Secret status returns metadata only.
- The module is isolated enough for V0.

Risks:

- The current names are Scaleway-specific, which is fine for V0 but will duplicate for OpenAI/Anthropic/DeepSeek.
- There is no generic `ProviderCredential` concept yet.
- No OS-backed storage interface exists.

Recommendation:

- During 0E-C, design generic credential concepts, but do not implement DPAPI yet.

### `backend/app/modules/runner`

Status: **keep for now / refactor later**

Good:

- Routes are thin.
- `local_python.py` is the only subprocess boundary.
- `safety.py` is separate and focused.
- Explicit job creation and explicit run remain clean.
- Artifacts and logs integrate with `SimulationRun`.

Risks:

- `service.py` is 691 lines and handles implementation registration, job creation, execution, metadata, logs, output parsing, artifact registration, readback, status transitions, and events.
- Error handling is internally consistent but module-local.
- Adding another script kind directly here would make the file too broad.

Recommendation:

- Do not split before 0E-C.
- Split before adding a second runner model kind or runner UI.

### `backend/app/modules/events`

Status: **harden now / refactor during 0E-C**

Good:

- Redaction is centralized in event persistence.
- Tests cover obvious secret redaction.
- Events are already valuable audit breadcrumbs.

Risks:

- Event payloads are not typed.
- Redaction lives in events, but secrets/API response redaction may need a broader security utility later.
- Event naming and payload shapes vary by module.

Recommendation:

- During 0E-C, define `AIEvent` conventions for provider attempts, blocks, usage, and routing decisions.

### `backend/app/modules/files`

Status: **keep / refactor later**

Good:

- Artifact record service is small.
- Runner artifact readback now exists through runner service.

Risks:

- Artifact creation/list helpers are minimal and not yet a repository.
- Runner service bypasses files service for generated artifact registration.
- Absolute path handling is still local-first and acceptable, but future remote modes would need a different exposure policy.

Recommendation:

- For workbench/artifact viewer milestones, create a dedicated artifact repository/service.

### `backend/app/main.py`

Status: **keep**

Good:

- Router registration is still clear.
- CORS methods now cover current UI calls.

Risk:

- None immediate.

## 6. AI Module Assessment

Readiness for target concepts:

| Concept | Current Readiness | Severity | Action |
| --- | --- | --- | --- |
| `AIProviderAdapter` | partial | high | refactor during 0E-C |
| `ProviderRegistry` | missing | blocker | refactor during 0E-C |
| `ModelRegistry` | missing | blocker | refactor during 0E-C |
| `ModelCapability` | missing | high | refactor during 0E-C |
| `AITaskType` | informal strings only | high | refactor during 0E-C |
| `RoutingPolicy` | missing | blocker | refactor during 0E-C |
| `BudgetPolicy` | Scaleway smoke-specific | high | refactor during 0E-C |
| `PrivacyPolicy` | local engine exists | medium | harden now |
| `AIRequest` | draft-specific class | high | refactor during 0E-C |
| `AIResponse` | draft-specific class | high | refactor during 0E-C |
| `AIUsage` | smoke token metadata only | high | refactor during 0E-C |
| `AIEvent` | free-form event payloads | medium | refactor during 0E-C |

Hardcoded Scaleway assumptions:

- `AISettingsRead` contains Scaleway flags and token counters.
- `AIStatusRead` exposes Scaleway fields.
- `budget.py` has `evaluate_live_scaleway_smoke_gate`.
- `token_guard.py` uses Scaleway counters and cap fields.
- UI labels expose Scaleway directly in AI settings.
- Smoke test/console implementations directly instantiate `ScalewayProvider`.
- Secret status endpoints are Scaleway-only.
- Docs and tests use Scaleway as the only live-provider path.

Duplicated logic to extract:

- Gate result shape.
- Provider attempt metadata.
- Token usage estimation and actual/fallback update.
- Event payload assembly.
- Blocked response construction.
- Provider mode resolution.

0E-C should not simply rename Scaleway fields. It should design the neutral layer and then decide which existing smoke code remains Scaleway-specific compatibility.

## 7. Secrets Module Assessment

Status: **safe V0, not final architecture**.

What is good:

- Raw keys are not returned.
- Runtime-memory storage is honest and avoids plaintext persistence.
- Environment variable priority is explicit.
- Secret event payloads contain metadata only.
- Invalid-key responses avoid echoing raw input after 0E-B1 hardening.

What will not scale:

- Endpoint paths and models are Scaleway-specific.
- No `ProviderCredential` or `CredentialStatus` abstraction.
- No store interface such as `RuntimeSecretStore`, `EnvSecretStore`, `WindowsCredentialStore`.
- No credential scope concept.

Recommended 0E-C design concepts:

```text
ProviderCredential
CredentialStatus
CredentialSource
CredentialScope
CredentialStore
RuntimeCredentialStore
EnvironmentCredentialSource
```

Do not implement persistent DPAPI/Windows Credential Manager in 0E-C unless a separate design explicitly approves it.

## 8. Data Infrastructure Assessment

Status: **strong enough for design, not for heavy expansion**.

Good:

- `schema_migrations` records current schema state.
- `/system/info` exposes bootstrap and schema state.
- Useful indexes exist for events, artifacts, runs, jobs, and model versions.
- Runner artifact metadata readback exists.
- Event redaction is centralized.

Risks:

- Migration mechanism is still in-code and lightweight.
- `schema.py` will become unwieldy with multiple future migrations.
- No upgrade tests from realistic old DB files.
- `system/info` is broad and may become a dumping ground.
- Artifact reads are split between files and runner modules without a shared artifact repository.

Recommended during/after 0E-C:

- Keep 0E-C mostly design-only; do not rework migrations there.
- Before a larger data milestone, split migration records/statements into dedicated files.
- Add old-schema migration tests before another schema-heavy milestone.
- Define artifact read conventions before building artifact viewer UI.

## 9. Runner Assessment

Status: **keep frozen while AI provider design happens**.

The runner is appropriately scoped:

- local only;
- no shell;
- controlled work/output paths;
- bounded logs;
- script hash;
- reviewed deterministic script only;
- no AI-generated code execution.

Structural warning:

`runner/service.py` should not receive another model type. The next runner expansion should first split:

- `implementation_service.py`;
- `job_service.py`;
- `execution_service.py`;
- `artifact_service.py`;
- possibly `repository.py`.

Action:

- No runner refactor before 0E-C.
- Refactor before runner UI or second model kind.

## 10. API/Error Convention Assessment

Status: **inconsistent but tolerable for design phase**.

Current shapes:

- Modeling: `HTTPException(detail="Model spec not found.")`
- Runner: `HTTPException(detail={"code": "...", "message": "..."})`
- Secrets: `HTTPException(detail={"code": "scaleway_api_key_invalid", "message": "..."})`
- AI smoke: returns `200` with blocked result objects.

Risk:

Provider abstraction will need clean blocked/error semantics. Without a convention, each provider route or adapter will invent its own response.

Recommended staged convention:

1. During 0E-C, document a shared error envelope:

```json
{
  "code": "machine_readable_code",
  "message": "human readable safe message",
  "details": {}
}
```

2. Keep smoke blocked responses as normal data, not HTTP errors.
3. Use HTTP errors for invalid API usage, missing records, and conflicts.
4. Move module-local error mapping toward `core/errors.py` after 0E-C.

Do not rewrite all current endpoints now.

## 11. Frontend Structure Assessment

Status: **works as operator UI, must split before AI UI grows**.

Observed file pressure:

- `frontend/src/pages/AIDraft.tsx`: 520 lines.
- `frontend/src/styles/global.css`: 502 lines.
- `frontend/src/api/client.ts`: 339 lines.

Good:

- UI remains local operator surface, not polished product workbench.
- No general chat was introduced.
- Secret input is localized and not persisted in browser storage.

Risks:

- `AIDraft.tsx` mixes AI cost guard, secret entry, AI settings, synthetic smoke tests, smoke console, token meter, and modeling draft request.
- `api/client.ts` mixes all backend domains and type definitions.
- Future Supervisor AI UI cannot be safely added to this file as-is.
- `SystemStatus.tsx` may need schema fields in the frontend type later.

Recommended split during 0E-C:

```text
frontend/src/api/
  http.ts
  ai.ts
  secrets.ts
  system.ts
  domain.ts

frontend/src/pages/ai/
  AIDraft.tsx
  AICostGuardPanel.tsx
  ScalewayKeyPanel.tsx
  SmokeTestsPanel.tsx
  SmokeConsolePanel.tsx
  DraftRequestPanel.tsx
```

Do not redesign UI. Split only to keep future AI controls maintainable.

## 12. Testing Assessment

Status: **good coverage, duplicated fixtures**.

Good:

- AI smoke paths are heavily tested with mocked providers.
- Secrets tests assert raw key absence.
- Runner tests cover success, failures, paths, logs, artifacts, and no secret environment.
- Data infrastructure tests cover schema migrations, indexes, redaction, and artifact readback.

Risks:

- Each test file defines similar `client` fixtures.
- Provider mocking is repeated inline.
- No provider adapter contract tests exist.
- No shared assertion helper for "no raw secret in response/event."
- No frontend tests, only build verification.

Recommended before or during 0E-C:

- Add `backend/tests/conftest.py` with:
  - isolated data root fixture;
  - initialized TestClient fixture;
  - no-network guard fixture for AI tests;
  - event payload helpers.
- Add provider contract tests in 0E-C design/implementation.
- Keep frontend testing postponed unless UI behavior starts getting complex.

## 13. Documentation Assessment

Status: **useful but milestone-heavy**.

Good:

- README documents data root, startup, AI gates, key entry, and runner limitations.
- Architecture doc captures current boundaries.
- RUNBOOKS now has useful manual validation and key-entry flows.
- 0E-A review is still directionally accurate.

Stale or missing:

- ADRs stop at Python Runner V0 and should add decisions for runtime-memory secret entry and future Supervisor AI/provider routing.
- README still reads partly like a chronological milestone log.
- There is no single "current operating model" page.
- The strategic `vierisid/jarvis` translation exists in the prompt but not yet in repo docs, except through this 0E-B2 review.

Recommended tiny doc fixes before 0E-C:

- Add ADRs for:
  - runtime-memory Scaleway key as temporary operator convenience;
  - one future Supervisor AI interface, not provider-specific bot buttons.
- Keep them short. Do not write a large strategy document before 0E-C.

## 14. Recommended Tiny Fixes Before 0E-C

No runtime code fixes are required before 0E-C design.

Allowed tiny fixes:

| Severity | Action | Fix |
| --- | --- | --- |
| low | document only | Add ADR for runtime-memory secret entry if desired. |
| low | document only | Add ADR for future single Supervisor AI interface if desired. |
| low | harden now | Add one shared test fixture file only if tests are edited during 0E-C. |

Do not split modules before 0E-C. The design should decide the target seams first.

## 15. Recommended Refactors During 0E-C

0E-C should be design-first, but it should specify exact future refactors:

1. `AIProviderAdapter`
   - Provider-neutral call interface.
   - No route/frontend direct provider calls.

2. `ProviderRegistry`
   - Lists configured/available providers.
   - Keeps Scaleway as current live smoke provider.

3. `ModelRegistry`
   - Model IDs, provider, capability metadata, context limits, cost hints.

4. `AITaskType`
   - `modeling_draft`;
   - `smoke_test`;
   - `smoke_console`;
   - future `model_review`;
   - future `source_grounded_query`.

5. `RoutingPolicy`
   - Chooses provider/model by task, sensitivity, budget, capability, and allowed egress.

6. `AIUsage`
   - Provider-neutral input/output tokens, usage source, cost estimate, model, provider, timestamp.

7. `AIGateResult`
   - Shared result for settings/budget/privacy/token/provider availability.

8. `AIEvent`
   - Typed event payload conventions for routed, blocked, attempted, succeeded, failed.

9. Secrets design
   - Generic credential concepts.
   - Runtime store remains V0.
   - DPAPI/Windows Credential Manager postponed.

10. Frontend split
   - Split AI page panels and API client before adding any Supervisor UI controls.

## 16. Recommended Refactors Later

| Severity | Action | Refactor |
| --- | --- | --- |
| high | refactor later | Split `runner/service.py` before second runner model kind. |
| medium | refactor later | Create artifact repository/service before artifact viewer. |
| medium | refactor later | Split schema/migrations before another schema-heavy milestone. |
| medium | refactor later | Move redaction/security helpers out of events if API responses need shared redaction. |
| medium | refactor later | Add migration tests from old SQLite snapshots. |
| low | refactor later | Convert README into current quickstart plus milestone archive. |
| later | postpone | Add authentication only if JarvisOS becomes accessible beyond localhost. |

## 17. Explicit Non-goals

Do not implement in 0E-C:

- OpenAI, Claude, DeepSeek, Mistral, or any new provider;
- AI Supervisor UI;
- provider-specific bot buttons;
- BlueRev scientific models;
- runner UI;
- file upload or parsing;
- Scientific Data Connectors;
- CAD, Geometry, CFD, FEM;
- agents or MCP;
- sidecars;
- desktop daemon behavior;
- voice;
- browser/clipboard/screen automation;
- multi-agent debate;
- generic workflow builder;
- arbitrary Python execution;
- AI-generated code execution.

## 18. Revised Roadmap

### 0E-C AI Provider Abstraction Design

Goal: design the provider-neutral AI layer.

Acceptance criteria:

- Provider and model registry design exists.
- Provider adapter contract exists.
- Provider-neutral request/response/usage shapes exist.
- Routing policy is defined.
- Gate pipeline is defined.
- Credential model is designed but not made persistent.
- Tests required for provider contracts are specified.
- No new provider is implemented.

### 0E-D First Provider Adapter Implementation

Goal: implement provider abstraction for the existing Scaleway path or one carefully selected provider after 0E-C.

Acceptance criteria:

- Mocked tests first.
- No direct provider calls from routes/frontend.
- No network by default in tests.
- Usage accounting goes through `AIUsage`.
- Secrets go through credential boundary.

### 0E-E AI Task Types And Structured Responses

Goal: define task-specific structured outputs without building general chat.

Acceptance criteria:

- Task types are explicit.
- Output schemas are typed.
- Supervisor-facing UX remains one stable interface.
- Outputs are draft suggestions, not automatic truth.

### 0E-F Supervisor AI Interface Gate

Goal: decide what one stable Supervisor AI surface should look like.

Acceptance criteria:

- No provider-specific bot buttons.
- Internal routing remains hidden except diagnostics/settings.
- Sensitive content rules are visible.
- Audit events are clear.

### 0F Modeling Workbench Foundation

Start only after 0E provider/routing foundations are accepted.

Scope:

- model tree;
- assumptions;
- parameters;
- formulas/equations;
- SimulationRun history;
- artifact viewer;
- reviewed runner UI.

### Later Phases

Postpone:

- engineering workflow graph;
- source-grounded literature workflow;
- R&D Debate Mode;
- CAD/PFD/geometry;
- sidecar integrations.

Final judgement:

```text
JarvisOS should keep becoming a local-first engineering workbench.
The next move is provider abstraction design, not more capability.
BlueRev modeling should remain paused.
```
