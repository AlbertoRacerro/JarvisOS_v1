# Area B direct-read ledger increment — 2026-09-17T0132Z

MAPPING_STATUS: IN_PROGRESS

This increment is Area B only. It preserves direct content inspection completed against PR #660 head `d6cbc9faeb1c80b63b4839957297e18ab8221630` while the canonical large-document replacement blocker recorded in `B-frontend-operator-ux-ledger-progress.md` remains unresolved. These rows MUST be folded into the canonical `## EXPLICIT FILE COVERAGE LEDGER`; they are not a completion claim.

| path | status | one-line role/reason |
|---|---|---|
| `frontend/src/components/Layout.tsx` | READ | Application shell coordinator: owns navigator/context/analysis panel visibility and focus restoration, applies appearance preference, opens route-specific shell regions, provides skip-link/main focus behavior, and composes Rail plus contextual regions around stage content. |
| `frontend/src/components/PageErrorBoundary.tsx` | READ | Page-level React error boundary that converts render exceptions into an explicit danger notice while logging error/detail to the browser console instead of leaving a blank operator surface. |
| `frontend/src/components/BluecadGlbViewer.tsx` | READ | Three.js GLB viewer with orbit/pan/zoom and click inspection; publishes session-bound mesh facts/selection, accepts only unique semantic BLUECAD SHA keys from object ancestry, handles WebGL/load failure explicitly, and disposes renderer/scene/material/texture/listener resources on replacement/unmount. |

## Capability facts

- `Layout.tsx` makes shell-panel state route-sensitive rather than globally persistent: BLUECAD opens navigator+sidecar, Process opens its sidecar, Memory knowledge routes keep Jarvis context reachable, and route changes close the analysis dock and move focus to main content.
- Final operator routes suppress the historical top bar while retaining Rail and shell regions; knowledge routes expose an explicit `Show Jarvis knowledge` recovery control when the sidecar is closed.
- `PageErrorBoundary.tsx` is a render-failure containment boundary only: it surfaces the thrown message and directs the operator to console evidence; it does not retry, infer recovery, or mask the exception as successful content.
- `BluecadGlbViewer.tsx` deliberately separates ephemeral viewer identity (`viewer-session-*`, `mesh-*`) from canonical semantic identity. A semantic key is accepted only when exactly one ancestor/name candidate matches `bluecad-part-sha256-<64 hex>`; ambiguous/missing candidates remain `null`.
- Viewer selection commands are session-bound, preventing stale commands from selecting meshes after artifact replacement. Pointer drags above 4 px are not treated as click selections. Resource cleanup covers loaded geometry/material textures, grid resources, controls, renderer, observers and event listeners.

## Remaining coverage

Area B remains incomplete. Fresh head/tree truth was inspected before this increment. Remaining work includes `frontend/package-lock.json`, public/static assets, unledgered API/components/pages/stages/styles/helpers/tests, canonical `docs/design-references/` behavior/appearance assets, and safe consolidation of all verified rows into `B-frontend-operator-ux.md`.

UNACCOUNTED_FILES: NOT_YET_ZERO
