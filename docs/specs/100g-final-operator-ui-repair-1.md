# 100g — FINAL-OPERATOR-UI-REPAIR-1

Definition status: **maintainer-inserted frontend-only repair; implementation requires registry `ready` authority**  
Exact derivation base: `c46b0c85a195c714f966cb44f8c543a12657478d`  
Depends on runtime authority: 100f (`merged` through PR #390)

## 1. Purpose

Repair exactly two systemic presentation defects observed by the maintainer after the merged 100f operator-frontend inspection, without reinterpreting the eleven canonical HTML references or adding product/domain authority.

This slice must execute before runtime implementation of 100b. It is deliberately smaller than a visual-identity pass: it corrects one shared composition failure and one shared peer-navigation styling inconsistency only.

## 2. Finding A — workspace header dead-space regression

Affected route families:

- Memory: `Project Basis | Models | Literature`;
- Development: `Roadmap | Brainstorm` (including Timeline/Calendar content below Roadmap);
- Coding: `Repository | Runtime`.

Current exact-base evidence shows these routes render `FinalWorkspaceHeader` immediately before a final-fusion surface while `.application-shell--final .shell-main` is a flex container and the header owns a fixed `min-height: 104px`. The resulting composition can treat the header as a workspace column rather than a compact top header, consuming workspace geometry and leaving visible dead space.

Required repair:

1. title, description and peer selector form one compact horizontal workspace header above the route work area;
2. the following final-fusion work area begins immediately below it and may consume the full available width/height;
3. no fixed-height spacer may remain whose only purpose is to reserve the previous 104px geometry;
4. the repair is scoped to Memory/Development/Coding workspace-header composition and must not flatten or remove the intentional Process palette or BLUECAD navigator/sidebar structures;
5. routes, data owners, selection semantics, Jarvis sidecar and Properties ownership remain unchanged.

A minimal wrapper/layout correction is preferred over route-specific duplication.

## 3. Finding B — shared peer/subpage selector language

The following peer selectors must use the same navigation language:

- Design: `Process | BLUECAD`;
- Memory: `Project Basis | Models | Literature`;
- Development: `Roadmap | Brainstorm`;
- Coding: `Repository | Runtime`;
- Settings: `Appearance | AI | System`.

Required style contract:

- inactive navigation: neutral/outline surface;
- active navigation: accent emphasis using a soft accent fill and/or accent outline;
- strong solid green fill is reserved for genuine primary actions and must not be the normal active peer-tab treatment;
- active state remains distinguishable without color alone through border/weight/current-page semantics;
- no status/action authority changes are implied by navigation styling.

The implementation should converge existing selectors through shared tokens/selectors where that is the minimum safe change; it must not create a new component framework or redesign unrelated controls.

## 4. Files likely touched

Exact implementation-base verification is required before writing. Expected bounded frontend paths are:

- `frontend/src/App.tsx` only if a common wrapper is the minimum composition fix;
- `frontend/src/components/fusion/FinalWorkspaceHeader.tsx` only if markup needs a bounded layout hook;
- `frontend/src/styles/final-workspace-header.css`;
- the existing Design/Settings/final-fusion style owner required to normalize peer navigation;
- `frontend/tests/100g-final-operator-ui-repair.mjs` and `frontend/package.json` for the deterministic gate;
- browser-proof harness/evidence files already used by 100f only where needed for exact-head proof.

No backend path is authorized.

## 5. Non-goals

- no general redesign or visual-identity pass;
- no change to primary IA, routes, redirects or eleven-surface semantics;
- no Process topology/CAD/solver capability or Design semantic change;
- no backend API/schema/domain/store/provider mutation;
- no React-owned project/runtime truth and no fixture values in production;
- no change to Jarvis context/action authority, Properties ownership or action classes;
- no 100b cleanup work inside this slice;
- no opportunistic refactor of unrelated CSS/components.

## 6. Deterministic regression gate

Add `test:100g` and include it in `npm run build` while retaining 058d/100/100f gates.

The gate must fail if either systemic regression returns. At minimum it must assert:

1. affected Memory/Development/Coding content is structurally stacked as compact header then full work area rather than two unconstrained flex siblings/columns;
2. the previous fixed `104px` spacer/`calc(100% - 104px)` contract is absent from the affected workspace header layout;
3. Design, Memory/Development/Coding and Settings peer selectors share neutral inactive + soft-accent active styling and do not use strong solid green as normal active navigation;
4. canonical routes/labels and 100f truthful-unavailable semantics remain intact;
5. no backend or forbidden browser authority is introduced.

Static assertions are regression guards, not sufficient visual proof.

## 7. Browser proof and visual inspection

Because this slice changes user-visible composition, exact-head browser evidence is mandatory.

Proof surfaces and canonical viewports:

- Memory / Project Basis — 1600×1000;
- Memory / Models — 1600×1000;
- Memory / Literature — 1600×1000;
- Development / Roadmap Timeline — 1600×1000;
- Development / Calendar — 1600×1000;
- Development / Brainstorm — 1600×1000;
- Coding / Repository — 1600×1000;
- Coding / Runtime — 1600×1000;
- Design / Process and Design / BLUECAD — 1365×768, to verify selector normalization without palette/navigator regression;
- Settings — 1365×768.

Each evidence record must bind exact implementation head, route, viewport and the corresponding canonical HTML path/hash from `APPROVED_OPERATOR_UI_MANIFEST_2026-08-27.md`.

Manual visual inspection must verify:

- no large dead-space band/column remains under Memory/Development/Coding peer selectors;
- route work content starts immediately below the compact header and uses available width;
- peer-tab active/inactive treatment is visibly coherent across Design, Memory/Development/Coding and Settings;
- Process palette and BLUECAD navigator remain intentional operational columns;
- no fabricated runtime/project state appears.

## 8. Required implementation gates

Before merge on immutable exact head:

- `cd frontend && npm run test:100g`;
- `cd frontend && npm run build`;
- existing spec-status self-test and repository-required CI;
- exact-head browser proof above;
- no unresolved material review finding;
- diff remains frontend-only except spec/evidence/registry lifecycle files.

Any head mutation invalidates prior browser/gate/review evidence.

## 9. Acceptance criteria

100g is complete only when:

1. both maintainer findings are visibly resolved on exact-head browser proof;
2. Memory/Development/Coding use a compact top workspace header with immediate full-width work content below;
3. Design/BLUECAD structural palette/navigator semantics are unchanged;
4. peer navigation uses one coherent neutral/soft-accent language and strong solid green is not ordinary peer navigation;
5. all canonical routes, data owners, Jarvis/Properties structure and action authorities remain unchanged;
6. deterministic regression coverage is wired into `npm run build`;
7. no backend/API/schema/store/provider or fake frontend truth is introduced;
8. implementation merges with exact-head guard and `STATUS.md` is reconciled to `merged` before 100b starts.

## 10. Minimum-necessary test

The maintainer identified two cross-surface defects caused by shared frontend composition/styling. Correcting them in one small shared frontend slice is independently removable, directly testable, and avoids contaminating the already-frozen 100b cleanup with visual changes. A broader redesign would add risk without improving the stated acceptance target.

`NEXT_EXACT_ACTION=MERGE 100g DEFINITION/READINESS AND PROMOTE REGISTRY TO READY`
