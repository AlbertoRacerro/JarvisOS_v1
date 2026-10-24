# Spec 216 CFD pipe qualification — in progress

This is a measured checkpoint for the first typed smooth-tube case. It is **not**
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

The first two input changes do not explain the 25% pressure excess. The
standard SIMPLE trial must not be cited as agreement with Hagen–Poiseuille:
its iteration-300 pressure was transient and the run subsequently diverged.
The next bounded check is the discrete wall-stress/pressure balance and the
mesh's wall-face geometry; only a converged physical balance can justify
changing the case generator or the reported pressure result. The saved-field
check below narrows this discrepancy but does not resolve it.

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

The maintainer-owned [cloud prototype PR #916](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/916)
was read as input. It reports laminar agreement within 0.037% using ESI
OpenFOAM v1912, a wedge mesh and a longer entrance allowance. Those are
prototype claims from a different tool release and mesh; they do not validate
this v2412 case. The next repair can use its field and mesh analysis as a
comparison without modifying or merging that lane.
