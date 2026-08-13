# Spec 085 — BLUECAD-WORKBENCH-2

**Definition status:** complete specification; implementation remains unauthorized until a separate readiness decision promotes registry row 085.

**Registry status at definition:** `planned`

**Depends on:** 006, 006c, 083, 084

**Exact derivation baseline:** `master` at `019be37ea52b61205d4fb015e9ab16f4c5cc7312`.

**Authority:** `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/specs/STATUS.md`, `docs/specs/081-frontend-beta-authority-0.md`, merged specs 006/006c/070/083/084, and this document.

**Visual boundary:** the maintainer-approved BLUECAD reference is authoritative for layout direction and information hierarchy, not for engineering data. Global font, palette, iconography, token-value replacement, component grammar, borders/radii/shadows and global motion remain the independently removable visual-identity lane and are not absorbed by 085.

---

## 1. Purpose

Replace the compatibility-mounted legacy BLUECAD page inside `ModelStage` with the first native BLUECAD operator workbench built on the 083 shell and 084 candidate aggregate.

The result must preserve the complete working BLUECAD lifecycle while changing composition into a desktop-first engineering workstation:

- candidate/workspace navigation in the contextual navigator;
- one dominant real GLB viewport in Model stage;
- lifecycle, freshness, validation and promotion shown as distinct concepts;
- validation, evidence, artifacts, diagnostics and attempt history in bounded contextual/dock regions;
- create, duplicate-brief, archive and promote actions preserved through existing backend authority;
- honest loading, empty, partial-data and unavailable states;
- no fake CAD editing, FEM, Jarvis chat, analytics, telemetry, confidence or system-health data.

085 changes operator composition only. It does not alter BLUECAD generation, validation, artifacts, evidence, dependency/freshness, AI routing, promotion, run execution or scene-binding authority.

## 2. Verified baseline

At the derivation baseline:

1. `frontend/src/stages/ModelStage.tsx` compatibility-mounts `pages/BlueCAD.tsx`.
2. `BlueCAD.tsx` currently loads workspaces/candidates, keeps candidate selection, filters archived candidates, creates candidates, archives, promotes valid candidates, copies a brief for duplicate/retry flow, fetches validation-report JSON, renders real GLB content and ordered attempts, and tolerates malformed error-detail JSON.
3. `BluecadGlbViewer` is the real Three.js GLB renderer. Geometry inspection belongs to 086 and verified scene-component identity to 092.
4. 083 already owns the shell, router, rail, navigator, sidecar, dock, stage registry, focus behavior and appearance contracts.
5. 084 supplies `getBluecadCandidateAggregate(workspaceId, candidateId)` with canonical candidate, artifact, evidence, run, freshness and diagnostic projections. 085 is the first visible consumer.
6. Existing candidate mutations remain canonical backend routes. No second mutation path is authorized.
7. There is no editable Aspen-like flowsheet, no general CAD authoring kernel, no AI thread domain and no Jarvis conversational sidecar at this baseline.

Readiness must re-audit these statements if `master` moves materially.

## 3. Native workbench layout

Target hierarchy:

```text
application shell
├─ top bar / compact stage chrome
├─ rail
└─ model workspace
   ├─ contextual navigator
   │  ├─ workspace selector
   │  ├─ archived/filter controls
   │  └─ candidate list
   ├─ primary stage
   │  ├─ compact BLUECAD status/action strip
   │  ├─ dominant real GLB viewport
   │  └─ bounded candidate summary/actions
   ├─ contextual sidecar
   │  ├─ properties/lifecycle/freshness
   │  ├─ validation/evidence
   │  └─ artifacts/diagnostics
   └─ analysis dock
      └─ attempt history plus explicit candidate-linked references
```

The viewport must remain the dominant Model-stage region. At compact desktop widths and 200% zoom, navigator/sidecar/dock may collapse via existing shell controls; internal panes may scroll locally; page-level horizontal overflow is forbidden.

The maintainer reference contributes workstation density, slim navigation, compact chrome, right context, lower dock, light/off-white surfaces, restrained depth and selective natural chlorophyll/leaf-green accents. 085 must express this only through existing 070 semantic tokens/primitives and local BLUECAD layout styling; it may not redefine the global design system.

## 4. State and selection ownership

Server authority remains: workspaces, candidate lifecycle, aggregate detail, artifacts, evidence, freshness, attempts, promotion linkage and mutation outcomes.

Local frontend state may include archived visibility, local text filtering over already-loaded candidates, disclosure/tab state, creation-form text, transient request state and viewer camera/session state. No global state library is authorized.

Selecting a candidate should publish the existing 083 `StageSelection` record branch using the accepted `RecordRef` shape. 085 must not invent scene-component identity and must not persist a geometry hit as engineering truth.

Workspace change, archived filtering, archive mutation or missing aggregate must revalidate selection deterministically.

Candidate identity may be added to URL state only if readiness proves the existing 083 router has an accepted typed subject seam. Otherwise selection stays stage-local; no second router is created.

## 5. Data-loading contract

The navigator uses existing workspace and candidate-list APIs for discovery.

Selecting a candidate loads exactly one 084 aggregate. Visible candidate detail must consume:

- `aggregate.candidate` for canonical detail and ordered attempts;
- `aggregate.artifacts` for safe metadata/content links;
- `aggregate.evidence` for canonical evidence references;
- `aggregate.runs` for explicit run/model references;
- `aggregate.freshness` for four-state freshness;
- `aggregate.diagnostics` for bounded partial-data warnings.

085 must not recreate provenance, evidence, run or freshness joins in TypeScript.

Detailed validation checks may still be read from the canonical report artifact because 084 intentionally does not reinterpret report JSON as canonical evidence. Missing/malformed report content must not hide the rest of the candidate.

The GLB viewer receives only the existing secure backend artifact-content URL. `stored_path`, direct data-root paths and frontend filesystem access are forbidden.

Out-of-order requests must not allow an older workspace/candidate aggregate to overwrite newer selection. Readiness must freeze the minimum request-generation/cancellation guard.

## 6. Lifecycle actions

085 preserves current 006/006c semantics:

- **Create:** submit non-empty brief through existing route, refresh canonical list and select returned visible candidate.
- **Duplicate brief:** copy selected brief into the creation form for editing/resubmission. Do not label this as a backend retry if it is not one.
- **Archive:** use existing archive route, refresh list, and if archived rows are hidden select the first remaining visible candidate or honest empty state.
- **Promote:** show only when canonical state permits; call only existing promotion route; render returned decision linkage; never auto-promote after validation.

Conflicting actions for one candidate must be disabled while a mutation is pending. Success is claimed only after backend confirmation and canonical reload. A response from a previous workspace/selection must not mutate the current view.

## 7. Region contracts

### Contextual navigator

Minimum contents: workspace selector, archived toggle, refresh control if still necessary, candidate rows with lifecycle state and brief summary, selected state, loading/error/empty states. No scores or invented health metrics.

### Primary viewport

Minimum contents: compact candidate context, real `BluecadGlbViewer` when GLB exists, honest no-GLB state, bounded create/duplicate/archive/promote actions. Do not add fake Sketch/Extrude/Fillet/etc. commands. New inspection tools belong to 086.

### Contextual sidecar

May show read-only candidate properties, lifecycle, freshness, promotion linkage, validation summary, evidence references, artifact metadata and 084 diagnostics. No Jarvis input, AI confidence, personas or proposal-generation controls; those belong to 090/091.

### Analysis dock

May show ordered attempt history, structured error detail, validation table and explicit 084 run/evidence references. It must not become the generic Runs workbench from 088 or Analytics dock from 089.

## 8. Semantic-state rules

The following are distinct and must never be collapsed into one traffic-light state:

```text
candidate lifecycle  = canonical BLUECAD status
freshness            = 084 dependency summary
validation           = report/check verdicts
promotion            = decision linkage / eligibility
```

Use existing 070 primitives such as `StatusBadge`, `InlineNotice`, `Surface`, `Button` and `Field` where semantically appropriate. Communicate state with text/structure as well as color.

084 diagnostics are bounded notices, not reasons to hide valid GLB/lifecycle data. Missing evidence/run/artifact references are never silently converted to stale.

## 9. Viewer boundary

085 preserves `BluecadGlbViewer` and may only harden embedding where necessary: resize containment, loading/error state and cleanup on artifact/unmount.

Forbidden until 086/092: geometry-hit semantics, persistent Three.js identity, component naming authority, isolate/hide, measurements, clipping/sections, semantic evidence highlighting, scene-component IDs and binding manifests.

If a concrete viewer lifecycle defect blocks native embedding, readiness may authorize only the smallest viewer fix with an exact regression test.

## 10. Required empty/error states

The native workbench must cover without mock engineering content:

1. no workspaces;
2. workspace-list failure;
3. workspace with no candidates;
4. candidate-list loading/failure;
5. aggregate loading and aggregate 404 after list selection;
6. aggregate partial diagnostics;
7. no GLB and GLB load failure;
8. no validation report and malformed/unavailable report;
9. zero attempts;
10. mutation failure;
11. archived-only workspace while archived rows are hidden.

## 11. Accessibility and responsive requirements

Prove at minimum:

- candidate list keyboard reachability and programmatic selected state;
- non-color lifecycle/freshness/validation communication;
- accessible busy/disabled mutation controls;
- correct disclosure/tab semantics where used;
- labeled GLB canvas plus adjacent textual fallback/summary;
- viewer does not trap focus;
- actions, sidecar and dock reachable without pointer-only interaction;
- deterministic focus after archive hides the selected candidate;
- reduced-motion behavior;
- compact desktop and 200% zoom with no page-level horizontal scroll and a still-usable viewport.

## 12. Blocking failure modes

085 is not complete if any of these occur:

1. working legacy BLUECAD behavior is removed without native parity;
2. frontend infers evidence/run/freshness instead of consuming 084;
3. lifecycle, freshness and validation are conflated;
4. stale async responses display another workspace/candidate;
5. archive/promotion claims success before backend confirmation;
6. duplicate-brief is misrepresented as backend retry;
7. real GLB rendering regresses or viewer resources leak on candidate changes;
8. fake CAD/FEM/AI/system-health/analysis values are introduced;
9. filesystem paths or direct data-root access reach frontend state;
10. compact/zoom behavior creates global overflow or unusable viewport;
11. keyboard/focus regressions make critical controls unreachable;
12. 085 changes backend engineering authority, schema, provider, credentials, budget, egress or global visual identity;
13. 085 implements 086, 088, 089, 090/091 or 092 early.

## 13. Likely implementation file boundary

Readiness must freeze an exact allow-list, expected to be a subset of:

```text
frontend/src/App.tsx
frontend/src/app/selection.ts
frontend/src/stages/ModelStage.tsx
frontend/src/pages/BlueCAD.tsx
frontend/src/components/BluecadGlbViewer.tsx
frontend/src/components/shell/ContextualNavigator.tsx
frontend/src/components/shell/ContextualSidecar.tsx
frontend/src/components/shell/AnalysisDock.tsx
frontend/src/components/bluecad/*
frontend/src/api/client.ts
frontend/src/styles/app.css
scripts/check_bluecad_workbench.py
```

Backend files, schema/migrations, package manifests, lockfiles, workflows, provider/credential/budget/egress code and Penpot/global-identity assets are not expected and require formal amendment.

Prefer bounded BLUECAD components rather than making `ModelStage.tsx`, `Layout.tsx` or one global shell component own the entire workbench.

## 14. Acceptance criteria

1. `ModelStage` no longer compatibility-mounts the legacy stacked BLUECAD page as its primary composition.
2. Native BLUECAD preserves create, selection, archived filtering, archive, duplicate-brief, promotion, validation detail, attempts and real GLB rendering.
3. Visible detail consumes 084 aggregate data for artifacts, evidence, runs, freshness and diagnostics with no client-side authority reconstruction.
4. Lifecycle, freshness, validation and promotion are distinct.
5. Real GLB is the dominant Model-stage surface and still uses the secure backend content route.
6. No-GLB, no-validation, zero-attempt and partial-data candidates remain usable without fabricated output.
7. Candidate selection uses the accepted typed record-selection seam without scene identity.
8. Workspace/candidate request races cannot cross-contaminate visible state.
9. Navigator, sidecar and dock contain only real data and controls belonging to 085.
10. No 086 inspection, 088 generic runs, 089 analytics, 090/091 Jarvis/thread behavior, 092 scene binding, grade surface or editable flowsheet is implemented.
11. 070/083 theme, keyboard, focus, reduced-motion, compact-width and no-global-overflow contracts remain intact.
12. Existing BLUECAD backend authority and routes remain unchanged.
13. Frontend production build and all exact-head conformance gates pass.

## 15. Tests and proof

Readiness should add a dependency-free `scripts/check_bluecad_workbench.py` if existing test infrastructure cannot prove boundaries. If added, it must self-test and verify that the native workbench consumes 084, preserves mutation clients, introduces no direct provider/filesystem access, ships no fake engineering labels/values from the reference, touches no dependency/schema/workflow/global-identity files and removes the 083 compatibility-mount state.

Deterministic tests/harnesses must cover workspace change, candidate selection/aggregate matching, out-of-order responses, archived-filter selection, partial diagnostics, duplicate-brief semantics, promotion eligibility/busy state, no-GLB/failed-GLB, malformed validation report and zero attempts.

Required exact-head gates include at least:

```bash
python scripts/check_spec_status.py --self-test
python scripts/check_ui_foundation.py
python scripts/check_app_shell.py
python scripts/check_bluecad_read_model.py
python scripts/check_bluecad_workbench.py   # if readiness adds it
cd frontend
npm ci
npm run build
```

Repository CI and BLUECAD Real Tool Proof remain mandatory if triggered by the implementation PR.

085 contributes to, but does not complete, Phase-2 evidence. The later checkpoint after 086 must still prove real GLB, distinct lifecycle/freshness, validation/evidence, attempt history, A0 inspection tools, honest no-FEM state and compact-width behavior.

## 16. Non-goals

No global visual-identity replacement, CAD authoring, geometry inspection, measurement, clipping, semantic scene identity, scene binding, FEM execution/browser, generic Runs UI, analytics, editable Engineering Data, AI threads, Jarvis chat/personas, grading, editable flowsheet, provider/credential/budget/egress change, new backend endpoint or schema migration.

## 17. Rollback and continuity

085 must remain independently removable from later 086–092 work. During implementation, legacy BLUECAD may remain only as internal migration reference until parity is proven; the merged product must not expose two competing primary workbenches.

If native migration cannot preserve an existing lifecycle action or real GLB rendering within this boundary, stop before removing the compatibility path and either amend 085 minimally or invoke the 081 controlled queue re-derivation path for a material architecture prerequisite.

Reverting the 085 merge must not require reverting 083 or 084.

## 18. Readiness requirements

A separate readiness PR must, against exact current `master`:

1. re-read 006/006c behavior, 083 shell, 084 aggregate and current frontend runtime;
2. prove 006, 006c, 083 and 084 are merged and no other implementation front is active;
3. map every working legacy BLUECAD operator function to its native replacement or accepted non-goal;
4. freeze exact component composition and allowed file set;
5. decide whether `BlueCAD.tsx` is decomposed, migrated or removed only after parity proof;
6. freeze use of the existing candidate `RecordRef` selection seam;
7. decide URL-owned versus stage-local candidate identity without adding a second router;
8. inspect `BluecadGlbViewer` lifecycle and authorize only minimum embedding fixes;
9. freeze race-handling strategy, deterministic tests and checker necessity;
10. prove no backend/schema/dependency/workflow/global-identity change is needed;
11. define compact-width, 200%-zoom and keyboard evidence;
12. promote registry row 085 to `ready` only when no unresolved authority decision remains.

Until readiness merges, row 085 remains `planned`, Implementation PR remains `—`, and runtime implementation is unauthorized.
