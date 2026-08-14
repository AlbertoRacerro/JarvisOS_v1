# 086 — MODEL-INSPECTION-A0

Status note: `docs/specs/STATUS.md` is authoritative. This document defines scope only and does not authorize implementation until a separate readiness decision promotes 086 from `planned` to `ready`.

## 1. Purpose

Add bounded geometry-only inspection to the existing BLUECAD GLB viewer after 085, without inventing semantic model identity, persistent scene state, editable CAD behavior, engineering authority, or a second selection system.

The user must be able to inspect what is visibly present in the loaded GLB and obtain clearly labeled, client-derived geometry facts. Every inspection hit is ephemeral and valid only for the currently loaded viewer session.

This slice also hardens viewer lifecycle behavior required by inspection so stale hits cannot survive artifact replacement, failed loads, unmounts, or disposed Three.js objects.

## 2. Authority and dependencies

Hard dependencies:

- 006 BLUECAD workbench + 3D viewer — merged;
- 085 BLUECAD-WORKBENCH-2 — merged and reconciled before this definition branch.

Current runtime authority remains:

- FastAPI + SQLite own engineering and lifecycle records;
- 084/085 own canonical BLUECAD candidate aggregate and workbench selection;
- the GLB artifact is a display artifact, not a semantic scene graph;
- frontend inspection derives only transient facts from the currently loaded Three.js scene.

Future 092 SCENE-BINDING-0 and 058c scene-semantics work remain separate. 086 must not create identifiers, persistence, APIs, schemas, or contracts that pretend a rendered mesh is already bound to an engineering record or scene component.

## 3. User-visible capability

For a successfully loaded GLB, the operator can:

1. activate geometry inspection without leaving the selected BLUECAD candidate;
2. select a visible mesh by pointer hit-testing in the viewport;
3. inspect the same loaded mesh through a keyboard-operable mesh list or equivalent accessible control, so pointer interaction is not the sole route;
4. see a compact readout of facts derived from that loaded mesh and scene;
5. clear the inspection explicitly;
6. continue orbit/pan/zoom without turning inspection into an edit mode.

The inspection readout must state that the information is geometry-only/session-scoped and carries no semantic record identity.

## 4. Session-scoped inspection contract

The implementation may define a small frontend-only type equivalent to:

```ts
type GeometryInspectionHit = Readonly<{
  sessionKey: string;
  meshKey: string;
  displayName: string | null;
  materialNames: readonly string[];
  triangleCount: number | null;
  worldBounds: Readonly<{
    min: readonly [number, number, number];
    max: readonly [number, number, number];
  }> | null;
}>;
```

Names are illustrative, not readiness-frozen API names.

Requirements:

- `sessionKey` is generated in the viewer for one successfully loaded artifact instance and is discarded on replacement/unmount; it is not persisted or sent to the backend;
- `meshKey` is only unique inside that loaded session. A Three.js UUID, traversal index, or equivalent may be used internally, but it must never be exposed as a durable domain identifier;
- `displayName` may use the GLTF/Three.js object name when present, otherwise a neutral label such as `Mesh 3`; no semantic name may be inferred;
- material names are copied only when present in the artifact and are labeled as artifact metadata, not material-property authority;
- triangle count, if shown, is calculated from the loaded geometry/index and is labeled as rendered geometry complexity, not FEM/mesh-quality evidence;
- bounds are computed from the loaded mesh in world space. Units must not be claimed unless an already-authoritative artifact contract supplies them; otherwise render numeric coordinates without inventing a unit.

No inspection field may be written to SQLite, candidate state, evidence, lineage, scene binding, requirements, decisions, artifacts, or logs as a new authoritative record.

## 5. Interaction and ownership

### 5.1 One BLUECAD selection owner

085 remains the owner of workspace/candidate selection. Geometry inspection is subordinate viewer state and must not publish a new `StageSelection`, change the selected candidate, or alter candidate lifecycle state.

### 5.2 Pointer inspection

Pointer selection uses Three.js raycasting against meshes belonging to the current successfully loaded GLB only.

- Ignore the grid, lights, helper objects, disposed objects, and anything outside the loaded artifact subtree.
- Convert pointer coordinates from the renderer canvas bounding rectangle, not page coordinates.
- If no mesh is hit, clear the current hit or leave it unchanged according to the readiness-frozen UX; the behavior must be deterministic and testable.
- Inspection must not disable normal OrbitControls behavior. Readiness must choose a minimal gesture rule that avoids accidental selection while orbiting, for example click-without-material-drag rather than pointer-down.

### 5.3 Keyboard-equivalent route

The loaded artifact must expose an accessible mesh-selection route outside raw canvas raycasting. The minimum sufficient implementation is a compact list/select control derived from the same loaded mesh inventory and feeding the same inspection state.

Do not implement keyboard emulation of 3D cursor movement, spatial traversal, or a custom accessibility framework in this slice.

### 5.4 Presentation

Use existing 085 shell composition. Geometry inspection should appear as a compact subordinate section in the BLUECAD contextual sidecar or an equivalently existing 085-owned region. It must not replace canonical candidate lifecycle/validation/artifact detail and must not add a new global panel system.

## 6. Lifecycle and stale-state rules

Inspection correctness is defined by loaded-scene ownership, not merely React component presence.

A current hit and mesh inventory must be cleared when any of these occurs:

- `artifactUrl` changes;
- a new GLB load begins;
- the GLB load fails;
- the viewer cannot create WebGL;
- the loaded artifact is replaced;
- the component unmounts;
- the owned scene is disposed.

Callbacks from a stale loader/session must not repopulate mesh inventory, hit state, status text, or inspection detail after a newer artifact has become current.

If a selected mesh is disposed or absent from the current loaded subtree, the UI must fail closed to no inspection rather than retain a stale reference.

The viewer must continue the 085 resource rules: owned geometries/materials/textures, controls, renderer, observers, listeners, and animation frames are disposed exactly once by the session that owns them.

## 7. Geometry fact derivation

Allowed derived facts are deliberately narrow:

- artifact object/mesh name when actually present;
- material names when actually present;
- triangle count from the current BufferGeometry when calculable;
- world-space axis-aligned bounds from the current mesh;
- neutral mesh ordinal/session identifier for inspectability.

Explicitly forbidden in 086:

- part type, component identity, equipment tag, semantic entity type, engineering-record ID, requirement linkage, decision linkage, lineage ownership, or scene-component binding inferred from mesh names or hierarchy;
- physical material properties inferred from material names;
- dimensions with invented units;
- volume, mass, stress, CFD/FEM result, tolerances, manufacturability, confidence, validity, health, or other engineering claims not already provided by a canonical backend contract;
- writing GLTF extras or node names into authoritative JarvisOS records;
- heuristic joins from mesh names to backend entities.

If a future semantic mapping is needed, 092/058c must define it explicitly.

## 8. Failure modes that block acceptance

1. **Stale hit after artifact replacement** — inspection shows mesh data belonging to an earlier GLB.
2. **Disposed-object retention** — state holds Three.js objects or callbacks after disposal, causing leaks/errors.
3. **False semantic authority** — UI labels a mesh as a domain component/record without an accepted binding contract.
4. **Pointer-only capability** — geometry inspection cannot be reached through keyboard-operable UI.
5. **Orbit/inspection conflict** — normal camera interaction causes uncontrolled selection or becomes unusable.
6. **Wrong ray coordinates** — hit testing ignores canvas bounds/resize and selects the wrong object.
7. **Helper-object hits** — grid/helper/light objects are exposed as model geometry.
8. **Unit fabrication** — coordinates/dimensions display units not established by authority.
9. **Page-level overflow/regression** — the added inspection surface breaks 070/083/085 compact desktop or effective 200% zoom behavior.
10. **Selection authority collision** — mesh inspection mutates candidate `StageSelection` or lifecycle state.

## 9. Accessibility and responsive requirements

- The inspection control/readout must be keyboard reachable with visible focus under the existing foundation contracts.
- Pointer inspection has an equivalent keyboard-operable mesh list/select route.
- Status changes that matter to the user are announced through the existing viewer/status pattern without noisy repeated announcements during orbiting.
- The canvas retains an accurate accessible label; if inspection mode materially changes its purpose, the label/instructions must reflect that without implying semantic editing.
- At effective 200% zoom and compact desktop widths, inspection content wraps/scrolls within its owning region and creates no page-level horizontal overflow.
- Reduced-motion and theme behavior continue unchanged; no new animation is required.

## 10. Likely implementation boundary

Readiness must re-check exact current code before freezing an allow-list. The expected minimum boundary is frontend-only and likely limited to:

- `frontend/src/components/BluecadGlbViewer.tsx`;
- `frontend/src/components/bluecad/BluecadWorkbench.tsx`;
- at most one small frontend-only inspection state/helper or harness file if it materially improves deterministic lifecycle testing;
- one bounded conformance checker and/or focused frontend harness if required to freeze the session/stale-state contract;
- `docs/specs/STATUS.md` only for normal lifecycle state/PR-number transitions during implementation.

No backend route/service/schema change, package or lockfile change, workflow change, provider/credential/budget/egress change, global shell redesign, or visual-identity lane change is expected or authorized by this definition.

If readiness discovers that a backend or dependency change is actually required, it must stop and re-derive the minimum boundary instead of silently expanding implementation scope.

## 11. Acceptance criteria

086 is implementation-ready only when readiness can freeze tests proving all of the following:

1. A loaded GLB yields a deterministic inventory of inspectable artifact meshes and excludes viewer helpers.
2. Pointer hit-testing selects only a mesh in the current loaded artifact subtree using canvas-relative coordinates.
3. A keyboard-operable control selects the same inventory and feeds the same session-scoped inspection state.
4. The readout exposes only allowed geometry facts and clearly labels them geometry-only/session-scoped with no semantic identity.
5. Artifact replacement/load failure/unmount clears the current hit and mesh inventory; stale loader callbacks cannot restore them.
6. Orbit/pan/zoom remains functional and inspection selection uses a readiness-frozen gesture rule that avoids material drag conflicts.
7. No backend write/request beyond the existing GLB artifact fetch is introduced by inspection.
8. Candidate/workspace selection and lifecycle behavior from 085 remain unchanged.
9. Existing GLB success, error, resize and owned-resource disposal behavior remains correct.
10. Keyboard focus, compact desktop, effective 200% zoom, theme and no-page-horizontal-overflow contracts remain intact.
11. Existing 070/083/084/085 preservation/conformance gates remain green on the exact implementation head.

## 12. Deterministic evidence strategy

Readiness should prefer the smallest evidence set that proves the real failure modes:

- a pure/helper harness for mesh-inventory filtering and session/stale acceptance if those rules are extracted into pure logic;
- source/conformance checks that prohibit backend/schema/package/workflow scope drift and semantic-identity claims;
- locked frontend `npm ci` + production `npm run build` on the exact head;
- browser proof using a real small GLB fixture to exercise pointer selection, keyboard-equivalent selection, artifact replacement, load failure, resize, orbit continuity, focus, compact desktop and effective 200% zoom;
- existing BLUECAD real-tool proof and inherited frontend gates where required by the final touched-file set.

Do not substitute JSON/source presence for rendered pointer coordinates, keyboard operation, or stale-session behavior.

## 13. Rollback

086 must remain independently removable. Rollback means removing the geometry-inspection state/controls/callbacks and returning `BluecadGlbViewer`/BLUECAD sidecar to the merged 085 behavior without changing candidate data, backend schema, artifact format, or scene semantics.

No migration or data cleanup should be required.

## 14. Non-goals

086 does not implement:

- semantic scene/component identity or persistent selection;
- scene binding to JarvisOS engineering records;
- CAD face/edge/topology editing or B-rep inspection;
- measurement tools, snapping, section cuts, clipping planes, exploded views, annotations, gizmos, transforms, or model edits;
- FEM/CFD field/result probing;
- lineage, run, analytics, Jarvis/AI or proposal-review functionality;
- global visual identity;
- new 3D libraries or dependencies unless a later readiness re-derivation proves the existing Three.js stack insufficient.

Those capabilities belong to their own queued slices or future independently removable specifications.
