# 024-C analytic FEM battery — implementation preflight

Base commit: `4b83f7e65c26bd29bf0879e0a3f09d237a7858b9`  
Date: 2026-07-11  
Scope: definition and code-path audit only; no runtime, solver, workflow, provider, routing, UI, corpus, or production-default change.

## Decision

**GO, but do not hand the whole current 024-C body to a coding agent as one undifferentiated patch.**

The contract is implementable on the post-024-B tree. The safest review boundary is two ordered implementation PRs under the existing spec row:

1. **024-C1 — verification kernel and fixture contract**
2. **024-C2 — real analytic battery, report, and workflow gate**

No acceptance criterion or tolerance is removed. 024-C2 remains blocked until 024-C1 is merged and its real segmented-bore selection audit is green.

## Repository-state finding

PR #79 is merged, but `docs/specs/STATUS.md` still describes 024-B as under review. The next status-only or 024-C planning change must correct the row to record 024-A and 024-B as merged and 024-C as the remaining work. A planning PR does not occupy the `Implementation PR` column.

## Existing evidence and parser boundary

### Available retained artifacts

The post-024-B path retains and hashes the inputs needed by a verification-owned parser:

- original Gmsh `mesh.inp` with boundary groups;
- pressure-only `solver_mesh.inp` with BODY tetrahedra and required NSETs;
- CalculiX `analysis.inp`, `analysis.frd`, `analysis.dat`, solver log and status files;
- `pressure_face_mapping.json` with mapped area, normals, explicit BODY face identifiers, applied resultant evidence and load provenance.

`fem_pressure_integration._parse_mesh` already parses node coordinates, element connectivity, node sets, element sets and node-to-volume adjacency. These pure capabilities may be extracted or reused without changing `ResultSummary` semantics.

### Required new verification parser

`fem_adapter_base._parse_native_frd` reads the `-5` component-name records but currently discards the names after using their count to truncate each result vector. It therefore cannot prove that a six-value vector means `SXX, SYY, SZZ, SXY, SYZ, SZX`, and it cannot safely support reordered FRD headers.

024-C1 must add a separate verification-owned parser that:

- retains block name, component names and per-node values;
- rejects missing, duplicate or unsupported components;
- maps values by component name rather than position;
- proves reordered-header handling in offline tests;
- exposes coordinates, selected node IDs, raw tensors and location residuals;
- does not alter the existing production summary parser or silently substitute a global maximum.

The DAT reaction parser and the post-024-B `reaction_resultant` are sufficient inputs for case-aware load-balance checks.

## Segmented Lamé bore feasibility

The existing mesh adapter creates physical surfaces with:

```text
Surface In BoundingBox {origin - half, origin + half}
half = 0.75 * (outer_d or pad_d)
```

The Gmsh reference manual uses `Surface In BoundingBox` to retrieve whole CAD surface entities by their bounding boxes. It does not create a partial surface selection. Therefore the bore must be partitioned in the STEP fixture into eight distinct 20 mm axial surface entities before meshing.

For the specified inner radius 20 mm, outer radius 40 mm and band centres `z = 10, 30, ..., 150 mm`, a half-side of 20.5 mm is analytically consistent **if the STEP really contains eight distinct bore surfaces**:

- each radius-20, length-20 bore band has a bounding box fully inside its own selection cube;
- the previous and next bands extend beyond the cube in z and should not be selected;
- the radius-40 outer cylinder and annular end faces extend beyond the cube in x/y and should not be selected.

This is not sufficient acceptance evidence. 024-C1 must generate the checked-in fixture, run real Gmsh through `mesh_analysis_spec`, and fail closed unless the eight groups prove all of the following:

- every group is non-empty;
- no group contains an outer-cylinder or end-face entity;
- no surface element appears in two bands;
- the union maps to the bore exactly once;
- summed mapped area agrees with `2*pi*a*L` within 1%;
- the integrated applied-force vector is self-equilibrated within the existing 0.5% scale limit.

Failure of that audit is a binding STOP requiring a fixture-definition amendment, not a larger bounding box or a weakened check.

## Finite-width plate source check

The prescribed polynomial is independently corroborated by the official Ansys PyMAPDL example `2d_plate_with_a_hole.py`:

```text
Kt = 3 - 3.14(d/W) + 3.667(d/W)^2 - 1.527(d/W)^3
```

That example cites *Peterson's Stress Concentration Factors*, ISBN `0470048247`. The ISBN identifies Walter D. Pilkey and Deborah F. Pilkey, third edition, Wiley, 2008. The example explicitly adjusts the far-field stress by `W/(W-d)` before forming `Kt`; this confirms the **net-section nominal-stress convention** required by the current spec.

Implementation evidence must cite the edition and ISBN above. It must also retain the regression that rejects use of gross-section stress. The Ansys example is corroborating implementation evidence, not a replacement for the cited handbook.

Source references:

- Ansys PyMAPDL official repository, `examples/00-mapdl-examples/2d_plate_with_a_hole.py`, commit `c4ad9ed4d7f8bc5f1b1ba0dbb8c62d305a426641`.
- W. D. Pilkey and D. F. Pilkey, *Peterson's Stress Concentration Factors*, 3rd ed., Wiley, 2008, ISBN `978-0-470-04824-5` / `0470048247`.
- Gmsh Reference Manual 4.15.2, `Surface In BoundingBox` examples and scripting command reference.

## Proposed ordered implementation boundary

### 024-C1 — verification kernel and fixture contract

Expected scope:

- new bounded module under `backend/app/modules/bluecad/` for analytic formulae, component-aware FRD parsing, INP/group parsing, coordinate filtering, tensor transformations, deterministic aggregation and comparison records;
- deterministic fixture-builder script plus checked-in STEP/manifest/digest files for beam, segmented cylinder and plate;
- offline tests for formula reference values, net-vs-gross convention, reordered FRD headers, corrupt/missing records, tensor transformations, location rejection and deterministic fixture manifests;
- one focused real Gmsh audit proving the segmented bore groups, uniqueness and mapped area before any Lamé stress acceptance claim;
- no production `ResultSummary`, route, schema, UI or promotion change.

C1 exit gate:

- normal CI green;
- strict real-tool group audit green;
- checked-in fixture digests stable;
- no binding stop condition triggered.

### 024-C2 — analytic solves and report

Expected scope:

- real C3D10 cantilever fine/coarse solves;
- real C3D10 open-end Lamé pressure solve;
- real C3D10 finite-width plate solve;
- location-specific sampling and case-aware reaction/resultant checks;
- deterministic Markdown and JSON report rendering;
- extension of the existing hash-pinned BLUECAD proof workflow;
- bounded artifact upload containing fixtures, mesh, decks, FRD/DAT/logs, mappings, comparisons and environment/tool hashes.

C2 exit gate:

- cantilever displacement error <= 2% and fine not worse than coarse;
- Lamé hoop error <= 5%, radial error <= 10% with correct sign, bore area/resultant checks green;
- plate peak tangential stress error <= 7% using net-section nominal stress;
- full backend suite, Ruff and strict real-tool workflow green;
- no tolerance widening, skipped strict test, manual mesh edit, fictitious refinement or global-maximum substitution.

## File-overlap audit

Open PR #80 changes only the isolated `engineering_corpus` runtime/tests/report surface. Open PR #81 changes only engineering-corpus research documentation. Neither overlaps the expected BLUECAD/FEM files for 024-C. Both remain outside this work and must not be modified.

## Recommended next action

Merge the planning/status correction, then start 024-C1 from the resulting `master`. Do not start 056 and do not fold #80 or #81 into the 024-C branch.
