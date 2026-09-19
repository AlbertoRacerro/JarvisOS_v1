# Area B explicit file coverage increment — 2026-09-17T0730Z

MAPPING_STATUS: IN_PROGRESS

Area B only. This increment contains direct-read evidence for B-owned frontend/operator UX files and is intended for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It contains no Area-A ownership rows.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/components/fusion/FinalOperatorReadSurface.tsx` | READ | Backend-owned Project Basis/model-spec/system-info READ projection; keeps unavailable exact-version, Git SHA, terminal/update and Jarvis commit authority explicitly Unknown/unavailable rather than inferred. |
| `frontend/src/components/fusion/FinalOperatorUnavailableSurface.tsx` | READ | Truthful unavailable-state compositions for memory/development/coding surfaces; unsupported actions are disabled/labeled while only local presentation toggles/navigation remain active. |
| `frontend/src/components/fusion/FinalWorkspaceHeader.tsx` | READ | Canonical Memory/Development/Coding peer-header/tab presentation using `AppLink` and explicit `aria-current` active destination. |
| `frontend/src/components/fusion/FinalSettingsSurface.tsx` | READ | Settings workspace wrapper exposing Appearance/AI/System route tabs and delegating actual settings behavior to the existing `Settings` page. |
| `frontend/src/components/fusion/ProjectSearchPanel.tsx` | READ | Workspace-scoped literal project search with minimum query bound, stale-response generation guard, fail-closed error state, provenance/source cues and canonical result navigation without implicit Jarvis context insertion. |
| `frontend/src/components/fusion/ProjectKnowledgePanel.tsx` | READ | Server-owned Project Knowledge revision lifecycle UI; draft approval/reconciliation are bound to exact revision tokens/digests, known FAIL requires explicit acknowledgement, and Process recomputation handoff carries revision/basis/validation identities. |

## Capability facts

- `FinalOperatorReadSurface` deliberately distinguishes workspace/model-spec/system observations from stronger identities it cannot prove: exact model versions, executed/remote Git SHA and browser-side process authority remain explicit Unknown/unavailable.
- `FinalOperatorUnavailableSurface` is not fake product functionality: unsupported backend-owned actions are disabled with reasons; presentation-only disclosure/view controls may remain interactive.
- `ProjectSearchPanel` invalidates prior request generations when workspace/query changes, so stale asynchronous results are not promoted into the current workspace view.
- `ProjectKnowledgePanel` treats frontend state as non-canonical and binds approval/reconciliation to server identities and digests; historical/discarded/superseded revisions remain inspectable without silently becoming writable parents.

## Remaining coverage

Literal completion is not yet proven. Continue direct inspection of remaining `frontend/` files and canonical behavior/appearance assets under `docs/design-references/`, then re-scan against fresh tracked-tree truth and consolidate all rows into the canonical ledger before declaring completion.

UNACCOUNTED_FILES: NOT_YET_ZERO
