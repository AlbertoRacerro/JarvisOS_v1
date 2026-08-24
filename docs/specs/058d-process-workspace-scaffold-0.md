# 058d — PROCESS-WORKSPACE-SCAFFOLD-0

Status: **definition-only; implementation not authorized**  
Date: 2026-08-24  
Depends on: 058b, 071b, 083, 089, 091, 096

## 1. Purpose

Create the minimum frontend-only workstation seam required before VISUAL-IDENTITY-1 so JarvisOS no longer presents its existing dependency/provenance browser as a process flowsheet.

The current `/design/flowsheet` stage is runtime lineage: it reads lineage graph/freshness authority, presents upstream/downstream record relationships and diagnostics, and explicitly says provenance does not imply recomputation. It is not process topology and must not become process topology by relabelling its existing graph data.

058d therefore separates two operator concepts:

1. **Lineage** — the existing read-only dependency/provenance surface over current lineage authority;
2. **Process** — a distinct canvas-first workstation scaffold that communicates where a future Aspen/HYSYS-like process workbench will live, while remaining explicitly inert until server-owned process/evaluator contracts exist.

The implementation remains unauthorized until a separate exact-master readiness record proves the minimum route/stage migration, shell-region reuse, inert-state behavior and browser acceptance without adding backend semantics or a second engineering state owner.

## 2. Preserved authority

058d must reuse, not duplicate:

- **083 App Shell** for routing, Design stages, workspace ownership and shell regions;
- **096** for the canonical Jarvis-over-Properties sidecar geometry and overflow behavior;
- **071b** for the single mutable engineering working configuration and Properties owner;
- **091/097** for Jarvis interaction/action authority; the Process scaffold grants no additional AI mutation authority;
- **089** for the existing Analysis Dock region and read-only analytics authority;
- **087 lineage runtime** for dependency/provenance reads, freshness and selection semantics;
- existing semantic tokens/shared primitives from 070.

No new process-domain truth is introduced by this slice.

## 3. Runtime fact being corrected

Exact master after the 058d queue insertion exposes:

- `StageKind = "model" | "results" | "review" | "flowsheet"`;
- `/design/flowsheet` titled `Flowsheet`;
- `FlowsheetStage` that imports lineage APIs and renders `Lineage / Dependency & provenance`;
- the Design-stage selector labels that route `Flowsheet`.

This naming can make a read-only provenance graph appear to be the future process flowsheet. 058d corrects that semantic collision before visual identity makes it look intentional.

## 4. Route and compatibility decision

The minimum compatible target is:

- canonical lineage route: **`/design/lineage`**;
- canonical process scaffold route: **`/design/process`**;
- historical **`/design/flowsheet`** remains a compatibility alias that resolves to `/design/lineage` and replaces the URL rather than rendering a third semantic stage.

This avoids breaking old links while making the product vocabulary unambiguous. `/design/flowsheet` must never silently become the new Process route because existing links historically refer to the lineage surface.

Readiness must verify that the current router can implement this alias without a second routing subsystem and must freeze the exact history/replace behavior.

## 5. Stage vocabulary

The normal Design stage sequence after implementation should distinguish:

- Model;
- Process;
- Results;
- Lineage.

Review remains outside the Design stage sequence under its existing primary route/authority.

The existing `flowsheet` stage kind should be retired or renamed in the smallest type-safe migration proved by readiness. It must not survive as a third ambiguous semantic stage beside Process and Lineage.

## 6. Lineage surface requirements

Current lineage behavior is preserved functionally.

058d may rename/move presentation ownership, but must not alter the underlying lineage contract:

- same workspace reads;
- same lineage graph/node/freshness APIs;
- same stale-generation guards;
- same dependency/provenance semantics;
- same node selection integration;
- same diagnostic/read-only behavior;
- no recomputation or process simulation claim.

Operator-facing naming should consistently say **Lineage**, **Dependency & provenance**, or equivalent semantic language. It must not call lineage nodes process equipment, streams, unit operations or process-flowsheet elements.

## 7. Process scaffold

The Process stage is intentionally not an editable process model.

The central region is a **canvas-first workstation scaffold** with a clear inert/empty state. It may contain structural zones such as:

- compact process-toolbar slot;
- equipment/palette slot;
- large central process-canvas slot;
- bounded stage-local status/empty-state message;
- existing shared sidecar and Analysis Dock regions.

All process-specific controls must be visibly inert or empty-state-only in V0. Disabled controls may describe future capability, but cannot imply that a topology, equipment library, stream graph or solver exists.

The central message must state truthfully that process topology editing becomes available only when server-owned process/evaluator contracts are integrated.

## 8. Shell composition

The Process scaffold must reuse current shell composition rather than creating a parallel application frame.

Required:

- same primary App shell/header/navigation;
- same workspace ownership;
- same Jarvis/Properties sidecar composition;
- same shell-region mechanism;
- same Analysis Dock component/region where readiness proves it belongs;
- same responsive/effective-200% behavior.

The scaffold may contribute a bounded navigator/palette placeholder or dock request through existing stage-region seams only if readiness proves this is simpler than a local inert slot. It must not create another global sidecar, another Properties owner or another analytics dock.

## 9. Properties and Jarvis behavior

Process V0 has no authoritative process-object selection.

Therefore:

- entering Process must not fabricate a selected pump/tube/stream/node;
- Properties remains the existing 071b owner and shows its existing neutral/no-target state unless another already-authoritative selection legitimately survives under shell rules;
- Jarvis may converse normally under existing thread/context authority but receives no invented process graph or equipment context;
- Jarvis engineering actions cannot mutate nonexistent process topology;
- no prompt claims that inert palette/canvas slots are real engineering objects.

Current App route changes clear `selection` and shell contributions. Readiness should preserve that fail-closed behavior unless exact runtime proves a safer existing transition contract.

## 10. Analysis Dock behavior

058d may expose the existing Analysis Dock affordance on Process only as a reused shell surface. It must not invent process KPIs or process-run data to populate it.

Acceptable V0 outcomes include:

- existing dock available but empty/neutral under current workspace evidence;
- dock affordance present only when current shell contract already supports it;
- stage-local explanation that analysis requires authoritative runs/results.

Readiness must choose the minimum behavior from current runtime. No second analytics state model is authorized.

## 11. No hidden process model

058d performs zero creation, mutation or persistence of:

- process nodes;
- material streams;
- energy streams;
- tubes, joints, pumps, valves, reactors, columns or unit-operation instances;
- connectivity/ports;
- topology graph;
- process parameters/specifications owned by a new frontend model;
- drag/drop layout state;
- solver state;
- process calculation/evaluator state.

React component state may own only ephemeral presentation state required for the inert scaffold itself, such as a local open/closed placeholder palette. It must not become an engineering/process-record store.

## 12. No backend expansion

058d authorizes no:

- FastAPI route;
- SQLite table/column/migration;
- backend process graph/service;
- process schema;
- model/evaluator contract;
- provider/tool call;
- runner/solver call;
- durable workspace state;
- new package/framework.

If implementation discovers that a credible Process scaffold requires backend process topology, implementation must stop at the inert scaffold and record the missing backend authority for the later process/evaluator queue. It must not guess a schema in 058d.

## 13. Toolbar and palette constraints

Toolbar/palette controls may only be structural placeholders.

Permitted examples:

- disabled `Add equipment` / `Connect` slots;
- empty palette region labelled `Process equipment` with `Not available yet`;
- non-interactive canvas help text;
- inert viewport/navigation affordances that do not persist engineering layout.

Forbidden:

- draggable pseudo-equipment whose state appears editable;
- fake stream lines;
- hardcoded pumps/reactors/tubes presented as supported domain vocabulary;
- mock pressure/temperature values;
- fake solver/run buttons;
- localStorage/sessionStorage topology persistence;
- pretend validation/blocker states.

## 14. Visual boundary

058d owns information architecture and semantic separation only.

It may add the minimum classes/layout needed for:

- canvas dominance;
- inert toolbar/palette/canvas regions;
- reuse of sidecar/dock geometry;
- responsive no-overflow behavior.

It must reuse current semantic tokens/primitives. No global palette, typography, icon set, radius/shadow system, motion language or final workstation styling belongs here. Spec 100 remains the sole global visual-identity slice.

## 15. Accessibility and responsive behavior

Required V0 behavior:

- Process and Lineage stage links are keyboard reachable and have unambiguous accessible names;
- `/design/flowsheet` compatibility navigation lands on canonical Lineage without duplicate focus/history loops;
- inert toolbar/palette controls are semantically disabled, not fake clickable controls;
- central empty state remains readable at effective 200%;
- no document-level horizontal overflow;
- Jarvis/Properties remains usable at desktop and compact widths;
- any local canvas/palette overflow is bounded locally;
- visible focus, reduced motion, light/dark/system semantics remain intact;
- stage changes do not preserve stale selection/context accidentally.

## 16. Stale/race behavior

Because Process V0 performs no process-data reads, it should introduce no new data-fetch race class.

Readiness must still verify:

- Lineage workspace A → B late responses remain rejected after route rename;
- Lineage → Process clears stale lineage selection/shell contributions according to existing App route-change behavior;
- Process → Lineage reinitializes lineage reads normally;
- `/design/flowsheet` alias does not mount Lineage twice or create duplicate history entries;
- Process route changes do not trigger runner/provider/canonical mutation.

## 17. Explicit non-goals

058d does not implement:

- Aspen/HYSYS-like editable flowsheet;
- process-topology backend;
- unit-operation library;
- stream/equipment semantics;
- persistent drag/drop;
- process solver or evaluator;
- CAD/process coupling;
- PBR process model;
- design-study controller;
- multifidelity orchestration;
- optimization/DOE;
- new engineering-record lifecycle;
- new Jarvis action type;
- global visual identity;
- Notes/scratchpad;
- routine 062 grading UI.

Future editable process capability must be derived from server-owned process/evaluator contracts after the relevant post-100 architecture/evaluator slices.

## 18. Readiness questions

A separate exact-master readiness record must answer:

1. What exact router/type changes are minimum to add canonical `/design/lineage` + `/design/process` while keeping `/design/flowsheet` as a replace-style compatibility alias?
2. Can `FlowsheetStage.tsx` be renamed to `LineageStage.tsx` without broad file churn, or is retaining the filename while changing exported stage identity lower risk?
3. What exact `StageKind`, `RouteId`, `PRODUCTION_ROUTES`, `DESIGN_STAGE_ITEMS` and `PRIMARY_STAGES` changes are required?
4. How will Process expose/reuse Jarvis/Properties and Analysis Dock without a second shell owner?
5. What should the existing Properties panel show when Process has no selected authoritative engineering object?
6. Which inert toolbar/palette/canvas elements are necessary to communicate workstation structure without implying backend capability?
7. What exact CSS/layout changes are minimum for a canvas-first central region and effective-200% behavior?
8. Which existing route/navigation tests or browser harness can prove canonical alias replacement and stage focus/history behavior?
9. What exact files form the minimum implementation allow-list?
10. Can implementation remain frontend-only with zero API/schema/store/provider/runner changes? If not, narrow implementation rather than invent backend authority.
11. Does reusing the Analysis Dock on Process require App-level route composition, a stage contribution, or no change at all?
12. What exact wording makes the Process empty state truthful and clearly inert?

## 19. Deterministic acceptance requirements

Readiness must turn current runtime into tests for at least:

1. `/design/lineage` resolves to the preserved lineage stage;
2. historical `/design/flowsheet` resolves/replaces to canonical `/design/lineage`;
3. `/design/process` resolves to a distinct Process stage;
4. Design navigation exposes separate Process and Lineage entries with no ambiguous `Flowsheet` label;
5. current lineage graph/freshness behavior is unchanged apart from route/stage naming;
6. Process mounts no lineage/process API calls merely to draw the scaffold;
7. Process creates zero canonical, runner, solver, provider or thread side effects solely by entering/interacting with inert regions;
8. no fake process object becomes current `StageSelection`;
9. shell Jarvis/Properties composition remains single-owner;
10. Analysis Dock behavior, if exposed, reuses the existing owner and does not fabricate observations;
11. route transitions clear stale stage contributions/selection;
12. disabled toolbar/palette controls cannot mutate state into an apparent process topology;
13. no new persistent browser storage is introduced;
14. no 100 visual-identity behavior appears.

## 20. Browser acceptance matrix

The eventual implementation requires real browser evidence for:

- navigate Model → Process → Results → Lineage;
- direct-load `/design/process`;
- direct-load `/design/lineage`;
- direct-load historical `/design/flowsheet` and observe canonical replace to `/design/lineage`;
- Process canvas-first scaffold visible with truthful inert empty state;
- toolbar/palette slots visibly disabled/inert;
- no fake equipment/streams/values appear;
- Jarvis/Properties sidecar remains present and usable;
- Analysis Dock behavior matches readiness and contains no fabricated process data;
- Lineage retains real workspace graph, selection and freshness behavior;
- Lineage → Process with a selected lineage node cannot leave stale lineage context presented as process context;
- keyboard-only stage navigation and visible focus;
- effective 200% with no page-level horizontal overflow;
- compact sidecar behavior remains valid;
- light/dark/system and reduced-motion behavior remain semantic;
- browser/network assertions prove no process/canonical/run/provider mutation occurs from scaffold interaction.

Screenshot-only evidence is insufficient without route/state/effect assertions.

## 21. Migration and rollback

No backend/data migration exists.

Frontend route migration is additive and compatibility-preserving:

- add canonical Lineage and Process routes;
- retain `/design/flowsheet` only as a compatibility alias to Lineage;
- do not rewrite stored project data because no route is project authority.

Rollback removes Process and restores the prior stage registry while leaving lineage/backend data untouched. Historical `/design/flowsheet` links remain supported until a future explicit compatibility decision removes the alias.

## 22. Downstream seam

After 058d implementation merges and is registry-reconciled, 100 VISUAL-IDENTITY-1 may begin its own lifecycle.

100 may style the Process scaffold but must not convert inert slots into pseudo-process semantics. Real editable process work remains post-backend and must be derived from future process/evaluator contracts, including the later architecture/evaluator queue rather than being smuggled into visual identity.