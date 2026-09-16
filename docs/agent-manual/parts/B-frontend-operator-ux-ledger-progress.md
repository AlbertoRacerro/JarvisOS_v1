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

## Capability facts from this B increment

- `App.tsx` confirms there is one operator composition boundary rather than independent page shells: route changes clear selection/shell/model-version state; stage routes contribute shell regions; Settings deliberately removes the Jarvis sidecar; Runs/Engineering Data/Process receive the Analytics dock.
- Project Basis deep-link refs are bounded to 200 characters and allowlisted to requirement/parameter/assumption/decision before becoming stable Jarvis context. Model and Literature stable refs likewise derive from explicit current selections/query identifiers rather than ambient page text.
- The production navigation taxonomy is Design, Memory, Development, Coding and Settings. Historical `/design/model`, `/design/results`, `/design/lineage` and `/design/flowsheet` paths canonicalize to `/memory/models`; `/` and `/home` canonicalize to `/design/process`.
- Internal links retain native browser semantics for modified clicks/new targets/downloads. Same-origin ordinary clicks use History API routing; cross-origin navigation is not intercepted.
- The frontend development surface is loopback-bound and `/api` is proxied to the loopback backend. The package build is not merely `vite build`: it first runs the enumerated operator contracts plus TypeScript checking.

## Remaining coverage

Area B only. Literal completion is not yet proven. A fresh PR-head tree scan was performed before this update. The remaining scope includes all other tracked files under `frontend/` (including `package-lock.json`, `public/`, remaining `src/`, generated TS, CSS and every test/helper) plus canonical behavior/appearance assets under `docs/design-references/`. The canonical `B-frontend-operator-ux.md` currently contains capability-level coverage but still lacks the required exhaustive one-row-per-file ledger, so its historical `MAPPING_STATUS: COMPLETE` claim is not valid under the maintainer's literal-coverage acceptance rule and must be corrected during safe canonical consolidation.

UNACCOUNTED_FILES: NOT_YET_ZERO
