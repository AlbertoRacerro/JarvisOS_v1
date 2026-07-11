# 024-C1 — verification kernel and fixture contract

Base: `1c5d94fba4dc61567f631b48447b020cf5294bf9`  
Spec: `docs/specs/024-fem-verification-battery.md`  
Preflight: `reports/024-C-PREFLIGHT/summary.md`

## Scope

This slice implements only the verification-owned foundation required before the
three analytic CalculiX acceptance solves. It does not change production
`ResultSummary` semantics, schemas, solver defaults, routing, promotion, UI, or
provider behavior.

Delivered:

- closed-form cantilever, open-end Lamé, and finite-width-hole reference functions;
- explicit net-section stress convention for the Pilkey/Peterson polynomial;
- component-aware native FRD parsing with reordered-header support and exact
  component validation;
- INP coordinate, connectivity, NSET, and ELSET parsing;
- Cartesian-to-cylindrical/tangential tensor transformation;
- deterministic coordinate/radius filtering with location residuals;
- deterministic aggregation, comparison, and segmented-pressure audit records;
- path-confined SHA-256 verification for checked-in FEM fixtures;
- explicit fixture generator plus checked-in cantilever, segmented-cylinder, and
  plate-with-hole STEP/manifest pairs;
- a strict real-Gmsh audit for the eight segmented bore groups, loaded area,
  uniqueness, fixed-end isolation, and self-equilibrated pressure resultant.

## Fixture design

The cylinder is one annular solid with its inner cylindrical face split at
`z = 20, 40, ..., 140 mm` using OpenCascade `BRepFeat_SplitShape`. It therefore
retains eight distinct 20 mm bore faces without introducing eight disconnected
volumes.

Each bore port uses a selection half-side of `20.5 mm`, matching the current mesh
adapter relation `half = 0.75 * outer_d`. The fixed-end selection cube is centered
at `z = -40 mm` with half-side `40.5 mm`: this contains the complete annular end
face at `z = 0` but cannot contain the first bore band or the full outer cylinder.
The real-tool test verifies the selected fixed nodes remain on `z = 0`.

Fixture exports use build123d `0.11.1` and a fixed STEP timestamp. Regeneration is
an explicit maintainer operation. Normal CI verifies the checked-in SHA-256 index
rather than regenerating CAD.

## Analytic references

- Cantilever: `F L^3 / (3 E I) = 1.6 mm`.
- Lamé bore: hoop `16.6666667 MPa`, radial `-10 MPa`, axial `0 MPa`.
- Finite-width hole: `Kt = 2.506464`, net nominal stress `12.5 MPa`, peak
  tangential stress `31.3308 MPa`.

The finite-width polynomial is bound to the net-section convention from Walter D.
Pilkey and Deborah F. Pilkey, *Peterson's Stress Concentration Factors*, third
edition, Wiley, 2008, ISBN `978-0-470-04824-5` / `0470048247`, corroborated by the
official Ansys PyMAPDL plate-with-hole example.

## Deterministic verification

Local focused verification before PR creation:

- verification-kernel tests: `12 passed`;
- Ruff `E/F/I/B/UP`: passed;
- Ruff format check: passed;
- Python compile check: passed;
- fixture regeneration: byte-stable STEP digests and unchanged fixture index.

The implementation PR must additionally pass:

- complete backend suite and repository Ruff gate;
- existing real Gmsh/CalculiX alpha proof;
- new strict segmented-bore Gmsh audit;
- uploaded bounded proof diagnostics including `segmented_bore_audit.json`.

## Binding stop condition

024-C2 must not begin unless the strict real-tool audit proves all eight bore
groups non-empty and unique, mapped area within 1% of `2*pi*a*L`, fixed-end
selection isolated to `z = 0`, and resultant norm below 0.5% of the scalar pressure
force scale. Failure requires a fixture/spec correction; no bounding-box expansion,
tolerance widening, manual mesh edit, or replacement by a global maximum is
permitted.
