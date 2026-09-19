# Area B explicit file coverage ledger increment 18

MAPPING_STATUS: IN_PROGRESS

This is a durable Area-B-only increment for PR #660. It extends the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`; it does not claim completion or global-union ownership. Backend Area-A rows are intentionally excluded.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/components/BluecadGlbViewer.tsx` | READ | Directly inspected. React/Three.js GLB viewer boundary: loads object URLs from `blob`, renders scene/camera/lights/grid, derives stable mesh selections from `userData`/names, applies selection highlighting, disposes geometries/materials and revokes object URLs on teardown. Viewer selection is presentation/inspection state only; no CAD mutation authority is present. Loading errors are surfaced to the operator; stale async load completion is guarded by an `active` flag. |

## Inspection notes

### `frontend/src/components/BluecadGlbViewer.tsx`
- Uses `GLTFLoader` against a browser object URL created from the supplied GLB `Blob`.
- Selection identity prefers `mesh.userData.part_id`, then `mesh.name`, then generated `mesh-N`; click raycasting returns `part_id`, `object_name`, and a viewer object key.
- Highlighting mutates emissive presentation on selected meshes and restores prior emissive state before applying a new selection.
- Cleanup marks the load inactive, disposes controls/renderer/scene geometry and materials, removes canvas/resize listener, and revokes the object URL.
- Failure mode recorded: the file reports loader failures but does not expose retry/cancellation UI itself; ownership of retry/reload remains with the caller/workbench. The `active` guard prevents a completed stale load from replacing a torn-down viewer, but it does not cancel network/parse work already in flight.
- Authority boundary: this component is an inspect/select renderer. No geometry authoring, persistence, backend commit, filesystem, or GitHub authority is implemented here.

## Reconciliation state

The canonical B document still contains a stale historical `MAPPING_STATUS: COMPLETE` marker while literal file-by-file reconciliation is unfinished. This increment is authoritative for the newly inspected row and keeps Area B `IN_PROGRESS`. `UNACCOUNTED_FILES: 0` is NOT asserted.

Next work: continue direct inspection of remaining tracked `frontend/` files and canonical operator design-reference assets, then merge all durable increments into the canonical ledger and prove exact set equality against a fresh tracked-tree scan before changing status to COMPLETE.
