# Spec 029 — SETTINGS-1

**Definition status:** complete definition contract; registry remains `planned` until a separate readiness decision.

**Freshly re-derived from:** `master` at `e6b27b005b5ce3600dedde8d55769a889c7a6251` after merged/reconciled 091 JARVIS-SIDECAR-1.

**Queue position:** after 091 JARVIS-SIDECAR-1 and before 092 SCENE-BINDING-0.

---

## 1. Purpose

Replace the current `/settings` migration placeholder with one truthful operator Settings surface over already-existing JarvisOS configuration, credential and local-system authorities.

029 is primarily a frontend composition slice. It must not invent a second settings store, credential mechanism, provider registry, budget ledger, route policy, data-root selector or diagnostic authority. Where the backend already exposes mutable configuration, Settings may operate that exact contract. Where the backend exposes status only, Settings remains read-only.

The intended operator outcome is: from one shell-native page, understand whether external AI can execute, why it may be blocked, what effective credential/storage mode is active, what budget/token limits are configured, and safely change only the already-authorized mutable controls without exposing secrets or bypassing canonical execution policy.

## 2. Current runtime facts

This definition is derived from runtime/code on the exact master above, not from legacy Settings prose.

1. `frontend/src/App.tsx` routes `/settings` to `MigrationPendingSurface`; legacy diagnostics remain available at `/legacy/system-status` and `/legacy/ai-draft`.
2. `frontend/src/api/client.ts` already exposes `GET /ai/settings`, `PUT /ai/settings`, `GET /ai/status`, `GET /secrets/scaleway/status`, `POST /secrets/scaleway/api-key`, `DELETE /secrets/scaleway/api-key`, and `GET /system/info`.
3. `SystemStatus.tsx` currently renders backend/storage/provider/budget diagnostics, but it is a legacy diagnostic route rather than the product Settings surface.
4. 082 already owns secure persisted Scaleway credential storage and explicitly forbids plaintext persistence, secret previews derived from the key, weak non-Windows persistence fallbacks, and backup/recovery claims for credentials.
5. 094 and the canonical execution spine own the normal provider path and provider enablement semantics. 029 does not alter provider execution.
6. 061/059b own budget, permission, confirmation, egress and provider-call authority. Frontend Settings must never infer or override permission locally.
7. 070 and 083 own shell/accessibility/layout contracts; 091 owns the global Jarvis sidecar composition. Settings must fit those existing regions rather than create a new application shell.
8. Safe defaults remain authoritative: paid AI disabled, budget zero, fake provider mode unless explicitly configured by existing backend contracts.

## 3. Scope

### 3.1 Settings information architecture

The `/settings` page exposes compact, desktop-first sections using the existing shell and UI primitives:

- **AI execution** — effective provider/mode, paid-AI state, external-call allowed/blocked state and canonical blocking reason;
- **Budget and limits** — monthly API budget, month-to-date spend, Scaleway monthly/hard-stop token caps, current token usage and direct-continuation limit when already writable through `/ai/settings`;
- **Credential** — effective Scaleway credential presence/source/storage health, with explicit set/replace/delete actions using the existing secret endpoints;
- **System/storage diagnostics** — backend/environment/data-root/database readiness from `/system/info`, read-only;
- **Advanced diagnostics links** — bounded links to legacy diagnostic surfaces where details remain intentionally outside 029.

Sections may be collapsed/expanded locally for usability, but this local UI state is not product configuration and need not persist.

### 3.2 Existing mutable AI settings only

Settings may edit only fields that the current backend `/ai/settings` contract already accepts and validates. The implementation must inspect exact request-model authority during readiness and freeze an allow-list before coding.

The frontend must not send opaque whole-object round trips. Each save action builds an explicit allow-listed payload from current operator inputs so server-added/read-only fields cannot be accidentally written back.

After every mutation, the page must reread canonical `/ai/settings` and `/ai/status` instead of assuming the submitted values became effective.

### 3.3 Credential handling

Credential UX uses only the existing secret service.

Requirements:

- password-type entry or equivalent non-revealing input;
- entered plaintext exists only transiently in component memory until submission completes or is cancelled;
- never place the key in URL, browser storage, console/log messages, analytics, DOM attributes intended for persistence, errors or screenshots/evidence;
- never prefill an existing key;
- status is based only on server-returned non-secret metadata;
- replacement requires an explicit operator action; delete requires explicit confirmation in the UI;
- if an environment override is effective, Settings must truthfully show that browser replacement cannot become effective and follow the existing backend conflict semantics;
- corrupted/unavailable persisted credential states remain distinct from absent;
- failed set/replace/delete does not optimistically change displayed canonical state.

029 must not change 082 storage, DPAPI, recovery or secret-response contracts merely to simplify frontend UX.

## 4. State ownership and concurrency

Settings is a long-lived shell route and must handle stale asynchronous work explicitly.

1. Every initial load/reload owns a request generation. Late results from an older generation cannot overwrite a newer reload.
2. A mutation snapshots the section/value set it owns. Late completion may trigger a canonical reread, but may not overwrite newer unsaved operator edits.
3. One mutation per authority domain at a time: AI-settings mutation and credential mutation each have their own busy lock. Unrelated read-only diagnostics may still reload.
4. Repeated click/Enter while a mutation is in flight must not emit duplicate PUT/POST/DELETE requests.
5. Route departure invalidates UI ownership of responses. The backend request may finish, but stale completion must not repaint another route or throw an uncaught error.
6. A failed canonical reread after a successful mutation must be shown as an uncertainty/reload failure, not as proof that the mutation failed or succeeded differently.

No client-side retry may automatically repeat a credential write/delete or settings mutation after an uncertain network outcome. The operator can explicitly reload canonical state first.

## 5. Validation and safe presentation

Frontend validation is ergonomic only; backend validation remains authoritative.

- numeric fields reject empty/non-finite/malformed values before request;
- do not silently coerce negative budget/cap values or values outside backend-defined bounds;
- do not invent units or convert budget/token values;
- unknown provider/status values are rendered as bounded text, not mapped to fake success;
- backend `blocking_reason` and safe validation messages are rendered inertly as text;
- raw response objects, exception stacks, secrets, provider payloads and absolute sensitive filesystem details are never dumped into the page;
- system data-root/database paths may be displayed only to the extent already returned by the current trusted local `/system/info` contract; 029 adds no new path exposure.

## 6. Shell, accessibility and visual constraints

029 is a normal product page inside 083.

- preserve global rail, navigator, Jarvis sidecar and dock behavior;
- Settings does not replace or disable the 091 sidecar;
- semantic headings and field labels are required;
- every control is keyboard operable;
- busy/disabled state is perceivable without relying on color alone;
- mutation errors and success/uncertainty notices are associated with the relevant section and do not steal focus unexpectedly;
- destructive credential delete has an explicit confirmation affordance and predictable focus return/cancel behavior;
- effective 200% zoom must remain usable with no global horizontal page overflow; dense settings groups may wrap or internally scroll only where an existing component contract allows it;
- reduced-motion and 070 theme/token contracts remain unchanged;
- local styling follows the maintainer-approved engineering-workstation hierarchy, but global visual identity remains a separate independently removable lane.

## 7. Non-goals

029 does **not** add or redesign:

- provider adapters, routing, model selection authority or external-call permission;
- a generic credential vault, new provider credentials or secret schema;
- backend settings storage, migrations or a new preferences database;
- data-root relocation/editing;
- recovery/backup behavior;
- telemetry, analytics or account sync;
- theme editor, accent-color system or global visual-identity implementation;
- keyboard shortcut editor;
- agent/persona configuration;
- 062 grading or operator-design surface;
- 092 scene binding, 058c scene semantics, 006b variants or 058b comparison;
- live smoke-test execution as part of ordinary Settings save;
- direct provider calls from the frontend;
- automatic enablement of paid AI after a credential is entered.

Legacy diagnostic routes may remain reachable until a later cleanup spec proves they are redundant. 029 should not delete them merely because it surfaces overlapping status.

## 8. Minimum-necessary implementation boundary

Expected implementation scope, subject to readiness verification:

- one product Settings page/component and bounded local styles;
- a narrow Settings API client module or additive typed helpers around the existing endpoints;
- `frontend/src/App.tsx` replacement of the `/settings` placeholder;
- deterministic state helper/harness only if needed to prove stale-response/mutation ownership without duplicating React logic;
- focused frontend conformance checker and browser evidence;
- focused backend tests only if readiness discovers an existing endpoint contract is insufficient or undocumented; no backend product change is presumed;
- `docs/specs/STATUS.md` only for implementation lifecycle.

Readiness must prove whether current `/ai/settings` request fields and secret status response are sufficient before any backend mutation is authorized.

### Test del minimo necessario

Criterio di accettazione della spec: provide one safe, truthful product Settings surface over the existing canonical settings, credential and system-status authorities.
Questo lavoro serve a soddisfarlo?           sì
Il criterio è raggiungibile senza di esso?   no — `/settings` is currently an explicit migration placeholder and the usable controls/status are fragmented across legacy diagnostics and API-only contracts.
Se sì: perché lo aggiungo comunque
Not applicable. The definition rejects new settings infrastructure and composes existing authorities only.

## 9. Acceptance criteria

1. `/settings` is no longer a migration placeholder and is reachable through the existing application shell.
2. Initial load shows bounded canonical AI settings/status, credential status and system/storage diagnostics without making any provider/execution call.
3. A settings save sends only readiness-approved mutable fields to the existing backend contract and then reloads canonical state.
4. Invalid numeric/operator input is rejected without request and without silent coercion.
5. Backend validation/conflict failure leaves canonical displayed state truthful and preserves editable input for correction when safe.
6. Credential set/replace/delete uses only existing secret endpoints; no existing secret is ever returned or prefetched into the input.
7. Test/evidence scans prove the submitted secret does not appear in browser storage, URL, console output, rendered status text, fixtures, screenshots or repository artifacts.
8. Environment, secure-persisted, absent, corrupted and unavailable credential semantics that exist in the backend are not collapsed into a false single “configured” state.
9. Credential deletion is explicit and guarded; duplicate in-flight set/delete actions are suppressed.
10. Entering a credential never automatically enables paid AI or changes provider/budget settings.
11. Settings displays canonical blocking reason/external-call state rather than inferring permission client-side.
12. Late load/mutation responses after a newer reload or route departure cannot overwrite current state or produce uncaught errors.
13. An uncertain post-mutation reload is represented as uncertainty requiring reload, never retried automatically as a second mutation.
14. 091 Jarvis sidecar remains present and functional on Settings; no second sidecar/shell region is created.
15. Legacy diagnostic routes required for information not migrated by 029 remain reachable.
16. Keyboard navigation, destructive-action focus behavior, Escape/cancel where applicable, reduced motion and effective-200%-zoom/no-global-overflow contracts pass browser evidence.
17. Browser evidence records zero unexpected provider/external-network calls while loading and editing Settings with mocked backend boundaries.
18. Implementation is independently removable: reverting 029 returns `/settings` to its placeholder without requiring rollback of 082/094/059b/061/070/083/091.
19. Repository CI, frontend production build, 029 conformance checker/self-test, relevant inherited 070/083/091 preservation gates and exact-head browser matrix are green.
20. Exact-head independent review returns PASS before merge.

## 10. Required readiness questions

A separate readiness record must answer from fresh master/runtime evidence:

1. What exact request model and mutable field allow-list does `PUT /ai/settings` accept today?
2. Which of those fields should be exposed in beta Settings versus left diagnostic/read-only?
3. Does the current secret status response on master already expose the 082 effective-source/persisted-state semantics expected here, and are frontend types stale?
4. What safe public error body is currently available for AI-settings and secret mutation failures, versus the generic `Request failed with <status>` client behavior?
5. Can 029 be frontend-only, or is one narrow additive error/status projection required for truthful UX?
6. Which current legacy System Status fields are appropriate to duplicate read-only in Settings and which should remain legacy-only?
7. What exact browser matrix proves no duplicate mutation, stale response rejection, secret non-disclosure, environment override, corrupted/unavailable status, keyboard/focus and effective-200%-width behavior?
8. What exact implementation allow-list is sufficient without touching provider, secret-storage, schema, workflow, package or global visual-identity scope?

Registry row 029 remains `planned`; this definition alone grants no implementation authority.
