# Historical A+B ledger progress

HISTORICAL_A_SOURCE_NOT_UNION_OWNERSHIP

MAPPING_STATUS: IN_PROGRESS

This sidecar preserves direct-read evidence accumulated while issue #656 temporarily combined Areas A+B. Backend rows below are historical source evidence for Area A only. They MUST NOT count as Area B ownership or global-union coverage, and no new backend-A rows may be added here. Preserve until Area A/D confirms absorption.

## Historical Area-A direct-read evidence

The prior revisions of this file directly inspected and recorded backend AI contracts, costs, sensitivity, thread, egress persistence/runtime, execution, budget and context-builder material. That evidence remains available in Git history for Area A to absorb; this file is no longer an Area-A working ledger.

## Area B explicit file coverage increment

The canonical destination remains `docs/agent-manual/parts/B-frontend-operator-ux.md` under its required `## EXPLICIT FILE COVERAGE LEDGER`. These rows are durable direct-read evidence to be folded into that canonical table without weakening the `READ` standard.

| path | status | one-line role/reason |
|---|---|---|
| `frontend/index.html` | READ | Vite HTML entry document: declares responsive viewport, JarvisOS title, root mount node, and `/src/main.tsx` module bootstrap. |
| `frontend/package.json` | READ | Frontend package/build contract: React/Vite/Three dependencies, loopback dev/preview scripts, and production build gate chaining operator source-contract tests, TypeScript, and Vite build. |
| `frontend/tsconfig.json` | READ | Strict no-emit ES2020/DOM TypeScript configuration scoped to `src`, with isolated modules and React JSX transform. |
| `frontend/vite.config.ts` | READ | React Vite configuration: frontend binds `127.0.0.1:5173` and proxies `/api` to loopback backend `127.0.0.1:8000`. |
| `frontend/src/App.tsx` | READ | Root operator composition: resolves routes, owns workspace/selection/shell state, mounts primary stages and routed surfaces, derives stable Jarvis context refs, suppresses Jarvis in Settings, and composes Properties/Analytics shell regions. |
| `frontend/src/app/AppLink.tsx` | READ | Same-origin SPA anchor adapter preserving native modified-click, target, download and external-navigation behavior while routing ordinary internal clicks through app navigation. |
| `frontend/src/app/routes.ts` | READ | Canonical frontend route/nav registry, redirects, normalization and DEV-only local-chat route; unknown paths resolve to explicit not-found rather than guessed product content. |
| `frontend/src/app/selection.ts` | READ | Typed transient stage-selection union covering canonical records, ephemeral geometry hits, BLUECAD binding states and resolved semantic BLUECAD parts. |
| `frontend/src/app/useAppRouter.ts` | READ | Browser History router hook: canonicalizes routes, tracks popstate, preserves query/hash on navigation, and delegates cross-origin destinations to full browser navigation. |
| `frontend/src/api/coding.ts` | READ | Typed Coding client for repository/ref/tree/file/search/PR/check/review/runtime/pipeline truth plus bounded inspect/context-preview/suggest-modification actions; errors preserve deterministic status/code. |
| `frontend/src/api/projectSearch.ts` | READ | Workspace project-search client and result contract carrying stable refs, provenance/source refs, lifecycle/version metadata, match tier, and canonical Memory destination route/params. |
| `frontend/src/api/runs.ts` | READ | Read-only simulation-run client exposing run summaries/details, logs and artifact evidence including truncation, provenance/hash/status and data-root containment metadata. |
| `frontend/src/api/settings.ts` | READ | Security-sensitive Settings client: reads canonical AI/provider/secret/system state, bounds public error projection, mutates AI settings, and replaces/deletes Scaleway credentials without any read-back API for raw secret material. |
| `frontend/src/api/threads.ts` | READ | Typed AI-thread client for list/detail/create, context-pack preview, and interaction submission with explicit request IDs plus optional expected context digest binding. |
| `frontend/src/api/generated/modeling.ts` | GENERATED/ASSET | Verified generated TypeScript contract for backend `ParameterRead`; file declares its backend source and regeneration command and models value/lifecycle states explicitly. |
| `frontend/src/api/client.ts` | READ | Broad legacy/core frontend API seam: loopback/configurable base URL, typed system/workspace/modeling/AI/secret/BLUECAD contracts and basic JSON helpers; exposes explicit attempted/succeeded, blocking, usage and escalation metadata instead of deriving provider success from text. |
| `frontend/src/api/development.ts` | READ | Development API client for roadmap/calendar CRUD and brainstorm lineage/discussion/reconciliation/promotion; optimistic revision tokens and idempotency keys are carried on mutating operations, with promotions explicitly proposal-only. |
| `frontend/src/api/knowledgeActions.ts` | READ | Jarvis knowledge-action client requiring server context preview with exact refs/digest before proposal; refused states are rejected rather than silently treated as current/proposed context. |
| `frontend/src/api/literature.ts` | READ | Literature read client modeling source/entry review states, provenance locators, used-by references and backing availability; content URLs are exposed only when backing is explicitly available and content-enabled. |
| `frontend/src/api/memory.ts` | READ | Memory proposal client for assumption/parameter/decision promotion/rejection and parameter replacement; preserves structured status errors and replacement invalidation evidence. |
| `frontend/src/api/modelDossier.ts` | READ | Read-only model-dossier client exposing version identity plus run/artifact/evidence availability, keeping operator dossier inspection bound to explicit model-version IDs. |
| `frontend/src/api/parameterLifecycle.ts` | READ | Canonical parameter edit/lifecycle client with expected timestamp/state concurrency guards and structured error code/status propagation for activate/deactivate/archive/delete transitions. |
| `frontend/src/api/projectKnowledge.ts` | READ | Project-knowledge draft/impact/approval/revalidation/reconcile client; carries revision tokens, preview/validation digests, expected target identity and idempotency keys so operator approval is bound to reviewed server state. |

## Capability facts from B increments

- `App.tsx` confirms there is one operator composition boundary rather than independent page shells: route changes clear selection/shell/model-version state; stage routes contribute shell regions; Settings deliberately removes the Jarvis sidecar; Runs/Engineering Data/Process receive the Analytics dock.
- Project Basis deep-link refs are bounded to 200 characters and allowlisted to requirement/parameter/assumption/decision before becoming stable Jarvis context. Model and Literature stable refs likewise derive from explicit current selections/query identifiers rather than ambient page text.
- The production navigation taxonomy is Design, Memory, Development, Coding and Settings. Historical `/design/model`, `/design/results`, `/design/lineage` and `/design/flowsheet` paths canonicalize to `/memory/models`; `/` and `/home` canonicalize to `/design/process`.
- Internal links retain native browser semantics for modified clicks/new targets/downloads. Same-origin ordinary clicks use History API routing; cross-origin navigation is not intercepted.
- The frontend development surface is loopback-bound and `/api` is proxied to the loopback backend. The package build is not merely `vite build`: it first runs the enumerated operator contracts plus TypeScript checking.
- Coding UI authority is explicitly narrower than arbitrary Git/GitHub control: the client exposes repository/runtime truth and bounded backend inspect/context-preview/suggest-modification actions, with exact workspace/repository/base SHA/target paths supplied by the caller.
- Project search results carry server-provided stable refs and canonical destination routes; the frontend does not synthesize domain identity from display text.
- Runs API is an evidence/inspection seam only in this file: it lists existing runs/logs/artifacts and exposes truncation/hash/source metadata, but contains no run-launch mutation.
- Settings error handling intentionally refuses to project arbitrary unparseable response text. Credential status/capability is structured metadata; raw submitted Scaleway API keys are only sent on replacement and are never returned by this client.
- Thread interaction submission can bind to a previewed context digest, preserving the distinction between ambient UI state and explicit server-validated context selection.
- `api/generated/modeling.ts` is genuinely generated rather than merely living in a `generated/` directory: its header identifies `backend/app/modules/modeling/models.py::ParameterRead` and `python scripts/generate_frontend_contracts.py` as provenance/regeneration path.
- `api/client.ts` exposes provider execution truth as separate status/blocking/attempted/succeeded/usage fields. Operator surfaces must preserve those distinctions and must not interpret non-empty `response_text` as proof that the intended external provider call succeeded.
- Development mutations carry revision/idempotency authority; brainstorm promotion payloads are explicitly `proposal_only`, so UI language must not imply that promotion directly mutates downstream roadmap/design/coding truth.
- Knowledge actions bind proposals to a prior server-produced exact-ref context digest. A refused preview/proposal is a terminal UI-visible refusal for that request, not context that the browser may reconstruct locally.
- Literature backing availability is explicit and multi-state (`available`, `missing`, `ineligible`, `unsupported`, `unsafe`); only an available/content-enabled backing gets a content URL, preventing UI from equating a citation record with readable source bytes.
- Memory replacement returns invalidation evidence (`affected_count`, graph digest, replacement ref); parameter lifecycle edits separately use expected timestamp/current-state guards. Operator UX should surface stale/conflict outcomes rather than overwrite optimistically without reconciliation.
- Project-knowledge approval/reconcile is review-state-bound: revision tokens and preview/validation/target digests are part of the mutation contract, so stale previews cannot be represented as unconditional approval authority.

## Canonical-ledger integration blocker

The connected GitHub file reader returns the large canonical `B-frontend-operator-ux.md` only in bounded/truncated ranges, while the available contents write operation replaces the complete file atomically and has no patch/append primitive. Replacing the canonical file from an incomplete fetch would destroy existing capability material. Therefore this run preserves verified B rows durably here rather than performing a destructive canonical rewrite. Next action: reconstruct/materialize the complete canonical file safely, change its stale `MAPPING_STATUS: COMPLETE` to `IN_PROGRESS`, add `## EXPLICIT FILE COVERAGE LEDGER`, fold these verified rows into that table, then continue direct reads. This is a tooling/write-shape blocker to canonical consolidation, not a coverage exemption.

## Remaining coverage

Area B only. Literal completion is not yet proven. Fresh master and PR-head tree truth were inspected before this update. The remaining scope includes `frontend/package-lock.json`, `frontend/public/`, all still-unledgered `frontend/src/` components/pages/styles/helpers and tests, plus canonical behavior/appearance assets under `docs/design-references/`. The canonical `B-frontend-operator-ux.md` still requires safe reconstruction and exhaustive one-row-per-file consolidation before its historical COMPLETE claim can be accepted.

UNACCOUNTED_FILES: NOT_YET_ZERO
