# 024-C2 — analytic FEM battery and deterministic report

## Status

Implementation PR: #85. Normal CI and the strict registry-bound Gmsh/CalculiX
workflow are authoritative. Runtime-generated numerical reports are uploaded as
Actions artifacts and are not committed.

A complete strict run passed on the implementation head after the fixes described
below. The final workflow binds the generated report to the pull-request head SHA
rather than GitHub's synthetic merge ref.

## Implemented scope

024-C2 consumes the hash-bound fixtures and verification kernel merged in #84 and
adds:

- prescribed C3D10 AnalysisSpec builders for the cantilever, segmented open-end
  Lamé cylinder, and finite-width plate with a central hole;
- a coarse and fine cantilever run using target sizes `20/3 mm` and `10/3 mm`;
- a Lamé target size of `4 mm`, within the spec requirement `<= 5 mm` and reused
  from the successful C1 segmented-bore proof; an initial `5 mm` C2 run was
  rejected because both bounded attempts reported one inverted C3D10;
- real execution exclusively through `mesh_analysis_spec` and
  `solve_static_analysis` with the operator registry;
- location-specific displacement/stress sampling from retained INP and FRD
  artifacts;
- nonzero-resultant and self-equilibrated reaction-balance checks;
- deterministic JSON and Markdown report rendering with normalized-input tests;
- relative artifact paths, fixture digests, mesh counts, tool pins/hashes,
  sampling coordinates, analytic inputs, errors, tolerances, and limitations;
- strict workflow upload of the battery report and complete bounded diagnostics,
  including partial proof roots when execution fails before report generation.

## Real-proof corrections found during implementation

The strict workflow found two integration defects before numerical acceptance:

1. The verification INP parser attempted to parse Gmsh's free-text `*Heading`
   payload as integers. It now ignores payload lines outside NODE, ELEMENT, NSET,
   and ELSET sections, with a regression using the real Gmsh heading form.
2. The 024-B solid-only solver-mesh serializer emitted coordinates with 17
   significant digits. A near-zero coordinate exceeded the bounded CalculiX node
   field and stopped the Lamé solve before analysis. Solver coordinates now use a
   finite, maximum-20-character, 12-significant-digit representation with
   round-trip and non-finite regressions. Topology, node identities, source mesh,
   pressure mapping, solver options, and acceptance tolerances are unchanged.

## Prescribed acceptance values

- Cantilever: `1.6 mm`, relative error `<= 2%`, and fine error no greater than
  coarse error.
- Lamé cylinder: bore hoop stress `16.6666667 MPa` within `5%`; radial stress
  `-10 MPa` with negative sign and error within `10%`; at least eight angular
  samples in the axial layer nearest `z = 80 mm`; bore area within `1%`; applied
  and fixed-face resultant norms below `0.5%` of `p 2 pi a L`.
- Plate with hole: net-section nominal stress `12.5 MPa`,
  `Kt = 2.506464`, peak tangential stress `31.3308 MPa`, relative error `<= 7%`,
  sampled at symmetric transverse-diameter points near the mid-thickness layer.

The plate polynomial is bound to *Peterson's Stress Concentration Factors*, third
edition, Walter D. Pilkey and Deborah F. Pilkey, Wiley, ISBN 9780470048245, using
the net-section nominal-stress convention frozen by the spec and C1 regression.

## Observed strict real-tool evidence

Using Gmsh `4.12.1+ds1-1.1build2` and CalculiX `2.21-1`:

- cantilever fine tip magnitude: `1.59746153 mm`, error `0.1587%`; coarse result
  `1.59531093 mm`, error `0.2931%`; refinement and both reaction balances pass;
- Lamé mean bore hoop stress: `16.810872 MPa`, error `0.8652%`; radial stress
  `-9.689835 MPa`, error `3.1017%`, correct sign; `64` angular samples at mean
  radius `20.0 mm` and mean `z = 80.0 mm`; mapped area error `0.1186%`;
- plate symmetric mean tangential stress: `32.279150 MPa`, error `3.0269%`;
  both selected nodes lie on radius `10 mm` near `z = 0`, and reaction balance
  passes;
- meshes contain only C3D10 volume elements: cantilever coarse `587`, fine
  `3719`, Lamé `45744`, plate `114514`;
- full offline suite: `1036 passed, 11 skipped`; strict real-tool selection:
  `10 passed`.

All battery artifact paths are relative to the isolated proof root. The report
contains no runner-temporary absolute path.

## Verification ownership

The evaluator and runner remain separate from the production
`bluecad_result_summary_v0_1` parser. The only production integration change is
the bounded numeric serialization needed for CalculiX to read the already
validated solid-only solver mesh. No ResultSummary field, AnalysisSpec schema,
normal BLUECAD mesh default, solver option, candidate promotion rule, provider,
routing path, UI, or corpus behavior changes.

Global displacement and von Mises maxima are retained only as diagnostics. They
are not substituted for the prescribed sampling locations.

## Failure-mode controls

The battery fails closed for:

- missing/corrupt INP, FRD, pressure mapping, or report artifacts;
- non-C3D10 volume output;
- missing required node/surface sets;
- under-resolved cantilever tip or Lamé angular layer;
- wrong Lamé radial-stress sign;
- plate samples outside the bounded radius, mid-thickness, or target-point
  residuals;
- reaction imbalance or unintended transverse resultant above the frozen limits;
- fixture digest/path escape;
- any case exceeding its frozen tolerance;
- any artifact path escaping the isolated proof root;
- non-finite or over-width solver coordinate serialization.

No fallback to a global maximum, automatic tolerance widening, manual mesh edit,
undocumented boundary-condition substitution, fake local refinement, or direct
binary invocation is permitted.

## PR surface

- `backend/app/modules/bluecad/fem_verification_battery.py`
- `backend/app/modules/bluecad/fem_verification_runner.py`
- `backend/app/modules/bluecad/fem_verification_parsers.py`
- `backend/app/modules/bluecad/fem_pressure_integration.py`
- public verification exports
- focused offline and strict real-tool tests
- existing BLUECAD real-tool workflow and runbook
- canonical spec registry and this implementation report

PRs #80 and #81 remain outside this runtime boundary and are not modified.
