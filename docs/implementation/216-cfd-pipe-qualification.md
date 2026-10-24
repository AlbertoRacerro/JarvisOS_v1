# Spec 216 CFD pipe qualification — in progress

This is a measured checkpoint for the first typed smooth-tube cases. It is **not**
the spec 216 acceptance run or a qualified reduced model. All solver outputs
below were generated outside the repository by pinned OpenFOAM v2412 tools.

## Reproduction

The case is the BlueCad tube template with outer diameter 14 mm, wall 2 mm,
length 200 mm, so its bore is 10 mm. Water-like properties are 998.2 kg/m³ and
1.002 mPa·s. Mean inlet speed is 0.01 m/s (Re 99.6208). The steady laminar
`simpleFoam` case runs 300 iterations with residual target 1e-6. The generated
quarter-pipe O-grid has two symmetry planes. Pressure is sampled at 0.65 L and
0.85 L at the same radius, and velocity at three radii at 0.85 L. `p` is
kinematic pressure; the comparison multiplies by density. The analytic
Hagen–Poiseuille gradient is 3.2064 Pa/m. The source fixture files in
`backend/tests/fixtures/cfd_pipe/laminar_probe_{p,U}.txt` preserve the values
from the level 0 real run; trailing spaces were removed for repository checks.

Use the operator registry built by `scripts/qualification/216/operator_registry.py`
and `scripts/qualification/216/run_case.py --contract <JSON> --registry <YAML>
--out <external directory>` to repeat one typed case. The command writes a
manifest, registry and tool-binary SHA-256 values, mesh check, full logs,
residual verdict and analytic error to that external directory. It reports
measurement without claiming numerical qualification or publication.

### Current result: casegen v2 with the pinned-build workaround (2026-10-24)

The defect identified in the last section below is now worked around in the
adapter, as spec 216 requirement 1 allows. Case generator
`cfd_pipe_casegen_v2` writes `cache { grad(U) yes; }` into `fvSolution`.
With a cached gradient, `fvc::grad(U)` returns a reference instead of a
reusable temporary. `T()` then allocates its result and transposes correctly.
That covers every `simpleFoam` stress path that calls `fvc::grad(U)`: laminar
`Stokes` and the RAS `linearViscousStress` family. This is a dictionary
entry, not compiled code. conda-forge has no other OpenFOAM release to move
the pin to (only two `openfoam-2412` builds). Probes now use `cellPoint`
interpolation. The default cell-centre value biased the radial profile
comparison by up to half a cell's velocity change: 2.1% at level 0 and 5.1%
at level 1 on the same fields.

Regression controls: `scripts/qualification/216/solver_controls.py` generates
two `blockMesh` cases from typed values. Both reuse the generated pipe
case's `fvSchemes`, `fvSolution` and transport dictionaries. It runs them with
the pinned tools. The tool-dependent test
`test_solver_controls_with_real_openfoam_detect_the_transpose_defect` runs
both controls. It also checks that the square duct **fails** when the cache
entry is removed.

| Control (pinned v2412) | Mesh | Measured | Analytic | Error | Tolerance |
| --- | --- | ---: | ---: | ---: | ---: |
| Square duct, four walls | 40×16×16 | 2.810362 Pa/m | 2.851091 Pa/m (f·Re 56.908) | −1.43% | 2% |
| Same settings without the cache entry (hand-written control above) | 40×16×16 | 3.483047 Pa/m | 2.851091 Pa/m | +22.2% | fails |
| Half channel, one wall | 80×16×16 | 1.200088 Pa/m | 1.2024 Pa/m | −0.19% | 2% |

The −1.4% duct residual equals the `icoFoam` control on the same mesh. It is
discretisation error at 16 cells per side, not the defect.

Typed laminar reruns, from `run_case.py`, with the same contract as below
(Re 99.62, 300 iterations):

| Mesh level | Cells | Measured ΔP/L (Pa/m) | Error vs HP 3.2064 | Profile max error / mean speed | Case manifest digest |
| --- | ---: | ---: | ---: | ---: | --- |
| 0 | 15,360 | 3.220777 | +0.448% | 0.797% | `sha256:39629a90b242538e72abe886e46d36db242b73ed5c46475643aedabdff3fa577` |
| 1 | 51,840 | 3.215386 | +0.280% | 0.400% | `sha256:aa3b56243979ef3c18b736e1185cfcc52b2fe13d2e12997788984849e52b3ad2` |
| 2 | 174,960 | 3.218273 | +0.370% | 0.552% | `sha256:d3977c14b5470e7c3f93407f6b78272fae7f33d8468a279987f303fee35c7eeb` |

Levels 0 and 1 met the 1e-6 residual target. Level 2 did **not**: its final
initial residuals were Ux 9.4e-6 and p 4.0e-7 after 300 iterations
(1230 s). Its value is shown for completeness only. It must not be used for
an observed order or GCI until it is rerun with a larger iteration budget.
All three meshes pass `checkMesh` with zero failed checks. The pressure error
is now within 0.5% on every mesh, against +25% before. No mesh-sensitivity
uncertainty is claimed yet.

The level 0 probe output is preserved in
`backend/tests/fixtures/cfd_pipe/laminar_cached_grad_probe_{p,U}.txt`.

One typed turbulent case ran at level 0: the C1 condition (D = 46 mm,
L = 2 m, v = 0.45 m/s, Re 20,621). It used k-ω SST, low-Re resolved walls,
estimated y⁺ 0.50 and 121,800 cells, with `checkMesh` accepted. It ran 1500
iterations with every residual below the 1e-5 target. Manifest:
`sha256:c4609aeeb56ee558fff1dbf586e9fd9a7ac5aa3be2826d7f94aad88b05960d85`.
The probe gradient between 0.65 L and 0.85 L, density-scaled, is
54.454 Pa/m. That is −3.53% against smooth-pipe Colebrook (56.444 Pa/m) and
−6.01% against Blasius (57.938 Pa/m). This is a single mesh. Its first
pressure station, at 1.3 m, lies before the contract's 1.59 m development
allowance, so it is a measurement and not yet the turbulent qualification.
`run_case.py` does not yet compute a turbulent comparison; the numbers above
were computed by hand from the probe file. The external run directories are
`~/jarvis-control/work/evidence/216-solver-controls/c81-typed/v2/` and
`c81-controls-v2/`.

**Still open before publication:** a turbulent comparison computed by the
runner itself, with stations inside the developed section; a turbulent mesh
study; an observed order or GCI on the three laminar meshes; and the rest of
spec 216 (live residual console, viewport, publication, Process pinning). No
reduced model is published.

### Superseded first runs: casegen v1, defective stress path

| Mesh level | Cells | Final residual target | Measured ΔP/L (Pa/m) | Error vs HP | Profile max error / mean speed |
| --- | ---: | --- | ---: | ---: | ---: |
| 0 | 15,360 | met | 4.016805 | 25.275% | 1.434% |
| 1 | 51,840 | met | 4.013776 | 25.180% | 4.699% |

Both `checkMesh` reports have zero failed checks (non-orthogonality maxima
24.69° and 27.83°). Input geometry digest for both is
`sha256:e2d7f53b600c50f9fea73d81398453f9dfe0c7e509711a25fb8f2c01e3ded988`.
The level 0 and 1 case manifest digests are respectively
`sha256:96c183cf2949609579555404b60f457239c0b01c9d792da11eca6a6d5f8c322d`
and `sha256:0f7670d87fc5f42256f886c42ab482a2d758e6555054f99dff7051ace69782f8`.
The level 2 mesh passed `checkMesh` at 174,960 cells, but its diagnostic
solver run was stopped after about ten minutes while the earlier two levels
already showed the material pressure discrepancy. It has no final fields or
numerical comparison and is excluded from the table.

The pressure error persists after the first refinement, so a small mesh
spread would not establish physical accuracy. No pressure-drop model should
be published from these runs. The next numerical repair must trace the
pressure equation, boundary conditions, sampling and mesh family, then rerun
the three-mesh laminar and turbulent qualification before publication.

### Controlled solver diagnostics (2026-10-24)

The level 0 generated case was copied into separate external `/tmp` directories;
each diagnostic copy changed only the stated solver input. All variants ran
`blockMesh` and `simpleFoam` with the same pinned v2412 installation and used
the same two pressure probe locations. These hand-edited copies are diagnostics,
not typed cases or qualification evidence.

| Variant | Solver input change | Final pressure gradient | Solver verdict |
| --- | --- | ---: | --- |
| Generated baseline | none | 4.016805 Pa/m | residual-converged at 300 iterations |
| Linear convection | `div(phi,U)` from bounded linear-upwind to `Gauss linear` | 4.015921 Pa/m | completed 300 iterations |
| Fixed-speed inlet | `flowRateInletVelocity` to `fixedValue` at 0.01 m/s | 4.010354 Pa/m | residual-converged at 300 iterations |
| Standard SIMPLE trial | `consistent no`, velocity relaxation 0.5 | 3.080548 Pa/m at iteration 300; −25539.4 Pa/m at iteration 1500 | **failed**: continuity and momentum residuals did not converge |
| Relaxed standard SIMPLE | `consistent no`, velocity relaxation 0.7, pressure-field relaxation 0.3 | 4.016811 Pa/m | completed 500 iterations; final Ux and p residuals below 1e-8 |

The inlet, convection and relaxed standard SIMPLE changes do not explain the
25% pressure excess. The first standard SIMPLE trial must not be cited as
agreement with Hagen–Poiseuille:
its iteration-300 pressure was transient and the run subsequently diverged.
The relaxed trial copied the generated level 0 case into an external diagnostic
directory, removed its saved fields, and changed only `fvSolution` and the
iteration/write limit in `controlDict`. Its final probe values were
`p(0.13 m) = 0.000286128986166` and `p(0.17 m) = 0.000125166824916` m²/s²;
at 998.2 kg/m³ they yield 4.016811 Pa/m, within 0.0002% of the baseline.
This is a solver-setting diagnostic, not a typed qualification run. The
saved-field checks below narrow the discrepancy but do not resolve the
discrete axial momentum balance. Only a converged physical balance can
justify changing the case generator or the reported pressure result.

### Developed-section pressure check (2026-10-24)

The saved level 0 `300/` field was copied to a separate external diagnostic
case and resampled with pinned v2412 `postProcess` at ten axial stations, all
at `(y, z) = (0.5, 0.5) mm`. No solver input or field was changed. The outputs
are preserved in `backend/tests/fixtures/cfd_pipe/laminar_axial_probe_{p,U}.txt`.
The sampled axial velocity approaches 0.01952 m/s by x = 0.10 m and stays within 0.02% of
that value through x = 0.18 m. Density-scaled pressure gradients are:

| Axial interval | Measured gradient |
| --- | ---: |
| 0.02–0.06 m | 4.189823 Pa/m |
| 0.06–0.10 m | 4.024052 Pa/m |
| 0.10–0.14 m | 4.017085 Pa/m |
| 0.14–0.18 m | 4.016832 Pa/m |

The 25% excess is already present in the nearly developed interior and is
not explained by the choice of the original 0.13–0.17 m probe interval. This
diagnostic still leaves the discrete wall-stress/pressure balance and mesh
geometry unresolved. The resampled field is not a qualification run.

### Saved-field wall-stress check (2026-10-24)

Pinned v2412 `simpleFoam -postProcess -func wallShearStress -time 300` was
applied to the saved level 0 and 1 fields. For wall faces whose axial centres
lie in the original 0.13–0.17 m pressure interval, the axial kinematic wall
stress was averaged by each face's area from `constant/polyMesh`. For a
developed quarter-pipe, the wall-implied pressure gradient is
`rho * 2 * |mean wallShearStress_x| / R` (R = 5 mm). This is a diagnostic force
balance from the saved fields, not a new solver run or qualification result.

| Mesh level | Wall faces in interval | Mean axial kinematic wall stress (m²/s²) | Wall-implied gradient (Pa/m) | Sampled pressure gradient (Pa/m) |
| --- | ---: | ---: | ---: | ---: |
| 0 | 256 | 8.426385e-6 | 3.364487 | 4.016805 |
| 1 | 576 | 8.418050e-6 | 3.361159 | 4.013776 |

The wall-implied gradient is about 5% above Hagen–Poiseuille, while the
sampled pressure gradient is about 25% above it. Their roughly 19% mismatch
persists across refinement. The profile and near-constant axial velocity in
the developed interval make entrance loss an inadequate explanation. The
discrete pressure/momentum balance remains unresolved; neither gradient is
accepted as a publishable pipe correlation. A separate level 0 trial changing
only `consistent yes` to `consistent no` with the existing U relaxation 0.9
failed with a floating-point exception and supplied no usable result.

### Radial pressure and axial-development check (2026-10-24)

The unchanged saved level 0 `300/` field was resampled with pinned v2412
`simpleFoam -postProcess` at x = 0.13 and 0.17 m. At each station, five points
had z = 0.5 mm and y = 0.5, 1.5, 2.5, 3.5, or 4.0 mm. The temporary case was
outside the repository; only its `controlDict` probe locations changed.
The raw output is preserved in
`backend/tests/fixtures/cfd_pipe/laminar_radial_probe_{p,U}.txt`.

| y (mm) | Density-scaled pressure gradient (Pa/m) | Ux at 0.13 m (m/s) | Ux change to 0.17 m (m/s) |
| ---: | ---: | ---: | ---: |
| 0.5 | 4.016805 | 0.019521201 | +2.418e-7 |
| 1.5 | 4.016805 | 0.018275295 | +1.335e-7 |
| 2.5 | 4.016805 | 0.014518725 | −4.235e-8 |
| 3.5 | 4.016805 | 0.009856709 | −9.448e-8 |
| 4.0 | 4.016805 | 0.007924333 | −8.997e-8 |

The pressure gradient is independent of these radial sample points to the
reported precision. The sampled axial velocities change by at most 0.0025%
of the 0.01 m/s mean speed between stations. This excludes radial probe
placement and a still-developing axial profile in that interval as explanations
for the 25% pressure excess. It does not identify the discrete balance error;
the case remains unqualified and publication remains refused.

The maintainer-owned [cloud prototype PR #916](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/916)
was read as input. It reports laminar agreement within 0.037% using ESI
OpenFOAM v1912, a wedge mesh and a longer entrance allowance. Those are
prototype claims from a different tool release and mesh; they do not validate
this v2412 case. The next repair can use its field and mesh analysis as a
comparison without modifying or merging that lane.

### Saved-field flow balance (2026-10-24)

The unchanged level 0 and 1 `300/phi` surface-scalar fields were read from the
external pinned-v2412 cases. Summing each inlet and outlet patch's face fluxes
gives the following volumetric rates. The prescribed quarter-pipe rate is
`π(0.005 m)²(0.01 m/s)/4 = 1.96349540849e-7 m³/s`.

| Mesh level | Inlet flux (m³/s) | Outlet flux (m³/s) | Absolute imbalance / prescribed rate |
| --- | ---: | ---: | ---: |
| 0 | −1.96349540849e-7 | 1.96349534126e-7 | 3.42e-8 |
| 1 | −1.96349540849e-7 | 1.96349543474e-7 | 1.34e-8 |

This excludes an incorrect imposed quarter-flow or gross mass imbalance as the
source of the 25% pressure excess. It is a saved-field diagnostic, not an
independent solver run or numerical qualification. The discrete axial momentum
balance remains unresolved, so publication is still refused.

### Solver-path controls outside the case generator (2026-10-24)

Hand-written `blockMesh` cases, independent of the spec 216 generator, were run
with the same pinned v2412 installation, the generated level 0 `fvSchemes`,
`fvSolution` (SIMPLEC), transport properties and probe method. Each control has
an exact analytic laminar answer. These are external diagnostics, not typed
cases or qualification evidence. Inputs, logs, probe output and the two duct
fields are preserved outside the repository in
`~/jarvis-control/work/evidence/216-solver-controls/`.

| Control | Mesh | Solver | Measured gradient | Analytic | Error |
| --- | --- | --- | ---: | ---: | ---: |
| Plane half-channel, one wall, z one cell | 200×20×1 | `simpleFoam` | 1.200936 Pa/m | 1.2024 Pa/m | −0.12% |
| Plane half-channel, one wall, z resolved | 80×16×16 | `simpleFoam` | 1.200091 Pa/m | 1.2024 Pa/m | −0.19% |
| Square-duct quarter, two walls, two `symmetryPlane` | 80×16×16 | `simpleFoam` | 3.533717 Pa/m | 2.851106 Pa/m | +23.94% |
| Same quarter, `symmetry` patch type | 80×16×16 | `simpleFoam` | 3.533717 Pa/m | 2.851106 Pa/m | +23.94% |
| Full square duct, four walls | 80×32×32 | `simpleFoam` | 3.530449 Pa/m | 2.851106 Pa/m | +23.83% |
| Full square duct, four walls | 40×16×16 | `simpleFoam` | 3.483047 Pa/m | 2.851106 Pa/m | +22.16% |
| Same, `grad(U) leastSquares` | 40×16×16 | `simpleFoam` | 3.495584 Pa/m | 2.851106 Pa/m | +22.60% |
| Same, `div(phi,U)` bounded upwind | 40×16×16 | `simpleFoam` | 3.484025 Pa/m | 2.851106 Pa/m | +22.20% |
| Same, transient to steady | 40×16×16 | `pimpleFoam` | 3.483039 Pa/m | 2.851106 Pa/m | +22.16% |
| Same, transient to steady | 40×16×16 | `icoFoam` | 2.810508 Pa/m | 2.851106 Pa/m | −1.42% |

The square-duct analytic value is the series solution (Poiseuille number
f·Re = 56.908). The generated level 0 quarter pipe with
`nNonOrthogonalCorrectors 2` gave 4.016806 Pa/m, unchanged from the baseline.
The generated mesh's outlet area is 1.960343e-5 m², 0.16% below the exact
quarter circle; the wall vector area matches the arc geometry.

The excess therefore occurs on a plain orthogonal duct and does not depend on
the generator, O-grid, symmetry patch type, non-orthogonal correction, gradient
or convection scheme, or SIMPLEC. It appears with walls in two transverse
directions but not with one wall direction. `icoFoam` gives the expected
result on the same mesh, flow rate and schemes. `simpleFoam` and `pimpleFoam`
share the laminar `Stokes` momentum-transport term
`-fvc::div(nuEff*dev2(T(grad(U)))) - fvm::laplacian(nuEff, U)`; `icoFoam` uses
`-fvm::laplacian(nu, U)` only. The installed `linearViscousStress.C` source
has the standard form, and `turbulenceFields` reports uniform `nuEff`
1.00380685233e-6 m²/s.

The converged 40×16×16 `simpleFoam` field is also internally inconsistent.
An independent NumPy evaluation of the saved field gives an axial `ν∇²u` of
2.8757 Pa/m equivalent, while its pressure gradient is 3.4828 Pa/m. That
evaluation finds the explicit `dev2(T(grad U))` term negligible in the
developed section. Wall-adjacent cells have an odd–even zig-zag and are not
mirror-symmetric (for example 1.894, 1.985, 3.043, 2.626, 3.619… mm/s
along one wall). The `icoFoam` field is smooth and symmetric, and its own
`ν∇²u` (2.8097 Pa/m) matches its pressure gradient (2.8102 Pa/m). The saved
4-wall square-duct wall-shear balance gives 2.915 Pa/m, while the pressure
gives 3.530 Pa/m. This is the same pattern as the quarter-pipe wall-stress
check above.

**Conclusion at that checkpoint:** the 25% excess comes from the pinned
`simpleFoam`/`pimpleFoam` laminar momentum-transport path of this v2412
build when walls lie in two transverse directions. It is not a spec 216 case
generator defect. The section below identifies the defective operator.

### Defective tensor transpose in the pinned build (2026-10-24)

Rerunning the 40×16×16 `simpleFoam` duct for 2000 iterations with `p` and `U`
tolerance 1e-15, relative tolerance 0.01 and up to 200 sweeps gives
3.483047 Pa/m (+22.17%), the same value as before. Solver-tolerance
stagnation is therefore not the cause.

A diagnostic copy of the same duct then added a run-time-compiled
`vectorCodedSource` fvOption. It adds `+fvc::div(ν dev2(T(fvc::grad(U))))`,
which cancels the explicit `Stokes` term. Nothing else changed. The pressure
gradient became 2.810508 Pa/m (−1.42%), which matches the `icoFoam` control
to all printed digits. The same cancellation on the generated level 0
quarter pipe (300 iterations, final initial residuals ≤ 5.6e-9) gave
3.220790 Pa/m against Hagen–Poiseuille 3.2064 Pa/m (+0.45%), instead of
4.016805 Pa/m (+25.3%). Its centreline speed moved from 0.019521 to
0.019656 m/s (analytic 0.02).

The same fvOption wrote OpenFOAM's own `grad(U)`, `T(grad(U))`,
`dev2(T(grad(U)))` and the divergence term. Their y and z divergence
components match a NumPy replication to seven digits. The axial component
does not: it is −1.415 Pa/m equivalent at the duct centre, where the
continuum and replicated values are about 4e-9. At every cell checked, the
axial value equals `ν ∂_z(∂_z u_x)`, not `ν ∂_z(∂_x u_z)`. The written fields
show why. On a temporary field, `T(fvc::grad(U))` puts (∇U)_zx in both the
XZ and ZX entries. XY/YX and YZ/ZY transpose correctly. For a stored field,
`T(g)` and `g.T()` are exact (zero difference). The installed
`Tensor<Cmpt>::T()` header is correct, so the fault is in the compiled
in-place field transpose of this conda-forge build. `linearViscousStress`
applies `T()` to the temporary returned by `fvc::grad(U)`.

This explains every control. A one-wall channel has no `∂_z u_x`, so the
spurious term is zero and it passes. A duct or pipe has walls in both
transverse directions, so the solver adds about half a transverse Laplacian
as a body force. The error does not shrink with refinement.

**Conclusion for the next repair:** the pinned build's transpose of a
temporary tensor field is wrong. Every pinned `simpleFoam`/`pimpleFoam`
momentum-transport model that calls `dev2(T(fvc::grad(U)))` is affected:
laminar `Stokes` and the RAS/LES `linearViscousStress` family. The turbulent
qualification is affected too. Spec 216 requirement 1 allows working around a
known release defect in the adapter, with documentation, or moving the pin.
The repair should do one of these and add a regression control: the
40×16×16 square duct within about 2% of f·Re = 56.908 and the one-wall
channel. The typed laminar and turbulent qualification must then be rerun.
The coded-source run above is diagnostic only and is not a typed case.
Pressure output stays unpublishable until that rerun passes. Inputs, logs,
written fields and analysis scripts are in
`~/jarvis-control/work/evidence/216-solver-controls/c80-*`.
