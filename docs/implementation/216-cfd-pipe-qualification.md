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

The maintainer-owned [cloud prototype PR #916](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/916)
was read as input. It reports laminar agreement within 0.037% using ESI
OpenFOAM v1912, a wedge mesh and a longer entrance allowance. Those are
prototype claims from a different tool release and mesh; they do not validate
this v2412 case. The next repair can use its field and mesh analysis as a
comparison without modifying or merging that lane.
