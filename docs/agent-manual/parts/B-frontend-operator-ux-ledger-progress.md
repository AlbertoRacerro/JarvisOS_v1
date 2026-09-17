# Historical A+B ledger progress

HISTORICAL_A_SOURCE_NOT_UNION_OWNERSHIP

MAPPING_STATUS: IN_PROGRESS

This sidecar preserves direct-read evidence accumulated while issue #656 temporarily combined Areas A+B. Backend rows are historical source evidence for Area A only. They MUST NOT count as Area B ownership or global-union coverage, and no new backend-A rows may be added here. Preserve until Area A/D confirms absorption.

## Historical Area-A direct-read evidence

Prior revisions directly inspected backend Area-A material. That evidence remains in Git history for Area A to absorb; this file is no longer an Area-A working ledger.

## Area B explicit file coverage increment

The canonical destination remains `docs/agent-manual/parts/B-frontend-operator-ux.md` under its required `## EXPLICIT FILE COVERAGE LEDGER`. Rows below are durable direct-read evidence to fold into that canonical table without weakening the `READ` standard.

| path | status | one-line role/reason |
|---|---|---|
| `frontend/index.html` | READ | Vite HTML entry document: responsive viewport, JarvisOS title, root mount, `/src/main.tsx` bootstrap. |
| `frontend/package.json` | READ | React/Vite/Three package/build contract and production operator-contract/TypeScript/Vite build gate. |
| `frontend/tsconfig.json` | READ | Strict no-emit ES2020/DOM TypeScript configuration scoped to `src`. |
| `frontend/vite.config.ts` | READ | Loopback Vite server and `/api` proxy to loopback backend. |
| `frontend/src/App.tsx` | READ | Root operator composition, route/workspace/selection/shell state, primary stages and shell regions. |
| `frontend/src/app/AppLink.tsx` | READ | SPA anchor adapter preserving native modified/external/download navigation semantics. |
| `frontend/src/app/routes.ts` | READ | Canonical route/nav registry, redirects, normalization and explicit not-found handling. |
| `frontend/src/app/selection.ts` | READ | Typed transient stage-selection union including BLUECAD semantic/binding states. |
| `frontend/src/app/useAppRouter.ts` | READ | History router preserving query/hash and delegating cross-origin navigation. |
| `frontend/src/api/coding.ts` | READ | Typed Coding client for repository/ref/tree/file/search/PR/check/review/runtime/pipeline truth and bounded actions. |
| `frontend/src/api/projectSearch.ts` | READ | Project-search client carrying stable refs, provenance/lifecycle metadata and canonical destination. |
| `frontend/src/api/runs.ts` | READ | Read-only simulation-run/log/artifact evidence client with provenance/hash/truncation metadata. |
| `frontend/src/api/settings.ts` | READ | AI/provider/secret/system settings client with bounded errors and no raw-secret readback. |
| `frontend/src/api/threads.ts` | READ | AI-thread client with context preview and request/context-digest-bound interaction submission. |
| `frontend/src/api/generated/modeling.ts` | GENERATED/ASSET | Verified generated ParameterRead TypeScript contract with declared backend source/regeneration command. |
| `frontend/src/api/client.ts` | READ | Core frontend API seam exposing explicit provider attempted/succeeded/blocking/usage evidence. |
| `frontend/src/api/development.ts` | READ | Roadmap/calendar/brainstorm client with revision/idempotency guards and proposal-only promotion. |
| `frontend/src/api/knowledgeActions.ts` | READ | Knowledge-action client requiring exact-ref server context digest before proposal. |
| `frontend/src/api/literature.ts` | READ | Literature client with provenance and explicit backing availability/content eligibility. |
| `frontend/src/api/memory.ts` | READ | Memory proposal/replacement client preserving structured errors and invalidation evidence. |
| `frontend/src/api/modelDossier.ts` | READ | Read-only model-version dossier evidence client. |
| `frontend/src/api/parameterLifecycle.ts` | READ | Parameter edit/lifecycle client with optimistic expected-state/timestamp guards. |
| `frontend/src/api/projectKnowledge.ts` | READ | Project-knowledge review/approval/reconciliation client bound to revisions and digests. |
| `frontend/src/main.tsx` | READ | React bootstrap, visual preference initialization and ordered global CSS cascade. |
| `frontend/src/operatorSemantics.ts` | READ | Defensive presentation semantics preserving unknown/stale/failure evidence. |
| `frontend/src/theme.ts` | READ | Appearance/accent persistence, validation, fallback and contrast-aware CSS variables. |
| `frontend/src/vite-env.d.ts` | READ | Tiny Vite ambient client-type declaration; no hidden runtime registration. |
| `frontend/src/components/Layout.tsx` | READ | Route-sensitive operator shell with accessible panel controls and focus restoration. |
| `frontend/src/components/PageErrorBoundary.tsx` | READ | Converts page render exceptions into explicit recoverable failure UI. |
| `frontend/src/components/BluecadGlbViewer.tsx` | READ | Three.js BLUECAD viewer preserving canonical semantic identity separately from ephemeral mesh/view identity and cleaning resources/listeners. |
| `frontend/src/components/ai/JarvisKnowledgeActions.tsx` | READ | Knowledge-action basket UI checks exact version/revision/digest identity before advisory proposals. |
| `frontend/src/components/ai/JarvisSidecar.css` | READ | Jarvis sidecar presentation/layout rules for thread, context, failure and action states. |
| `frontend/src/components/ai/useJarvisSidecar.tsx` | READ | Sidecar controller binds provider context to inspected digest, generation-guards async results, and preserves idempotent retry evidence. |
| `frontend/src/components/analytics/AnalyticsDockContent.tsx` | READ | Persisted-run comparison UI with six-run cap, explicit baseline, workspace-generation guard, separate model-contract failure, source-run links and visible rejection states. |
| `frontend/src/components/analytics/analyticsState.ts` | READ | Fail-closed analytics projection/comparison: bounded schema-v1 outputs, finite scalars, exact model versions/units, deterministic baseline, and authoritative engineering-input reconstruction. |
| `frontend/src/components/analytics/analyticsStateHarness.ts` | READ | Executable source-contract harness covering malformed/oversized payloads, unit/model mismatch, stale workspace responses, selection/baseline rules, configuration drift and deep-link ambiguity. |
| `frontend/src/components/analytics/variantComparisonNavigation.ts` | READ | Builds encoded source-run deep links and rejects missing, duplicate, blank or overlong workspace/run identities. |
| `frontend/src/components/ui/Button.tsx` | READ | Shared native-button primitive; defaults to `type=button`, forwards refs/HTML semantics, and exposes bounded visual variants without inventing action authority. |
| `frontend/src/components/ui/Field.tsx` | READ | Accessible form-field compositor linking label, generated/control id, hint/error descriptions, required state and `aria-invalid` onto the supplied control. |
| `frontend/src/components/ui/InlineNotice.tsx` | READ | Shared inline status notice with explicit tone labels; danger state receives alert semantics rather than relying on color alone. |
| `frontend/src/components/ui/StatusBadge.tsx` | READ | Presentation-only status badge with explicit domain tones including proposed/stale/unavailable/synthetic/archived; does not infer status. |
| `frontend/src/components/ui/Surface.tsx` | READ | Minimal semantic surface wrapper selecting section/article/div while preserving native HTML attributes. |
| `frontend/src/components/shell/AnalysisDock.tsx` | READ | Accessible analysis panel focuses its heading on open, closes on Escape, and explicitly states analytics unavailability when no real content is supplied. |
| `frontend/src/components/shell/ContextualNavigator.tsx` | READ | Accessible route-sensitive navigator derives peer/roadmap links from canonical registries, marks current pages, focuses on open, and closes on Escape. |
| `frontend/src/components/shell/LegacyDiagnosticSurface.tsx` | READ | Transition wrapper visibly labels legacy diagnostic content as stale rather than presenting it as canonical operator truth. |
| `frontend/src/components/shell/MigrationPendingSurface.tsx` | READ | Explicit migration-pending/unavailable placeholder with semantic notice and optional native-safe related-route navigation. |
| `frontend/src/components/shell/Rail.tsx` | READ | Primary JarvisOS navigation rail sourced from the canonical primary-nav registry with `aria-current` state. |
| `frontend/src/components/shell/TopBar.tsx` | READ | Thin current-route header that composes externally owned panel and appearance controls without inventing state. |
| `frontend/src/components/shell/ContextualSidecar.tsx` | READ | Accessible Jarvis/Properties sidecar: focus-on-open/Escape/arrow-key tabs; explicitly distinguishes ephemeral geometry, unresolved/ambiguous bindings and canonical BLUECAD/engineering selections without granting edit authority. |
| `frontend/src/pages/Dashboard.tsx` | READ | Legacy/foundation health dashboard; fetches backend health but uses local fallback strings for environment/version, so those fallbacks must not be treated as authoritative runtime evidence. |
| `frontend/src/pages/DevLocalChat.tsx` | READ | Explicit DEV-only local-chat diagnostic UI: no persistent memory/retrieval/external providers/tools; surfaces route gates, network/HTTP failures, deterministic history filtering, prompt-char budget and adapter truncation semantics. |

## Capability facts from latest B increment

- `Dashboard` is a small foundation/diagnostic surface, not an authority projection: backend status comes from `getHealth`, while absent environment/version render `local` and `0.1.0` fallbacks. Consumers must not interpret those fallback labels as verified runtime identity.
- `DevLocalChat` explicitly labels itself non-production and local-only, builds history solely from prior successful user/assistant turns, and keeps blocked/error entries out of subsequent history.
- Local-chat failure modes are operator-visible: 404 explains the dev-route gate, 422 reports validation failure, 5xx includes bounded `error_type`, invalid JSON becomes a blocked reason, and network failure points to backend/proxy availability.
- Prompt-budget UI distinguishes the adapter's character budget from the model context window, reports deterministic safety/history omissions, and explicitly states that `response_truncated=false` is not a completion guarantee.

## Canonical-ledger integration blocker

The connected GitHub file reader returns the large canonical `B-frontend-operator-ux.md` only in bounded/truncated form, while the available contents write operation replaces the complete file atomically and has no patch/append primitive. Replacing it from an incomplete fetch would destroy existing capability material. Verified B rows are therefore preserved durably here pending safe complete-file reconstruction. This is a tooling/write-shape blocker to canonical consolidation, not a coverage exemption.

The canonical file currently contains a stale `MAPPING_STATUS: COMPLETE` header inherited from the earlier capability-level map. That status is NOT defensible under the later literal file-by-file requirement and MUST be treated as superseded by this progress ledger's `MAPPING_STATUS: IN_PROGRESS` until canonical reconstruction can safely replace it and a fresh-tree comparison proves zero unaccounted B files.

## Remaining coverage

Area B only. Literal completion is not yet proven. Fresh PR-head tree truth was inspected before this update. Remaining scope includes `frontend/package-lock.json`, `frontend/public/`, still-unledgered `frontend/src/` API/components/pages/stages/styles/helpers/tests, and canonical behavior/appearance assets under `docs/design-references/`. `Dashboard.tsx` and `DevLocalChat.tsx` are now directly read and ledgered. The canonical `B-frontend-operator-ux.md` still requires safe reconstruction and exhaustive one-row-per-file consolidation before completion.

UNACCOUNTED_FILES: NOT_YET_ZERO
