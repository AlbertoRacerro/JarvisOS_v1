# OpenFOAM smooth-pipe prototype (cloud lane, issue #913)

Self-contained prototype for the CFD vertical slice of #901 Phase 2: a typed contract is
turned into a complete OpenFOAM case, run, and checked against the analytic solution
and smooth-pipe correlations. It is **not** wired into the backend and has no spec number.
Evidence: `docs/implementation/openfoam-pipe-prototype-2026-10-23.md`.

## Layout

| File | Role |
|---|---|
| `contract.py` | pydantic `PipeCase` (D, L, fluid, inlet velocity *or* flow rate, outlet pressure, mesh, model, solver tolerance) with regime/geometry validation |
| `foam_dict.py` | typed Python → OpenFOAM dictionary serializer (no free-form text path) |
| `casegen.py` | contract → `system/`, `constant/`, `0/` (blockMesh 2D-axisymmetric wedge) + SHA-256 manifest |
| `foam_io.py` | runs utilities, parses solver logs and ASCII fields |
| `polymesh.py` | polyMesh reader; cell/face geometry with OpenFOAM's decomposition |
| `analysis.py` | Hagen–Poiseuille, Blasius, Colebrook, GCI, developed-flow post-processing |
| `study.py` | the whole validation study + reduced model + VTK export |
| `plots.py` | evidence figures (matplotlib, optional) |
| `evidence/` | committed output of the last full run |

## Reproduce

Ubuntu 24.04: `sudo apt-get install openfoam gmsh python3-gmsh` (OpenFOAM v1912 ESI,
Gmsh 4.12.1), then `pip install pydantic numpy matplotlib pyvista pytest`.

```bash
# full study (20 cases, ~41 min wall on 4 cores; the finest SST mesh alone takes ~40 min); writes evidence/results.json, reduced_model.json, plots, VTK
python3 -m prototypes.openfoam_pipe --work /tmp/pipe_cases --out prototypes/openfoam_pipe/evidence
# smoke run (~5 s)
python3 -m prototypes.openfoam_pipe --work /tmp/pipe_quick --out /tmp/pipe_quick_out --quick
# tests (the OpenFOAM run test skips when simpleFoam/blockMesh are absent)
python3 -m pytest prototypes/openfoam_pipe/tests -q
```

The binaries need `WM_PROJECT_DIR`; `foam_io.foam_env()` sets it to `/usr/share/openfoam`
when the Ubuntu package is detected.

## Known environment defect

In the Ubuntu 24.04 `openfoam` 1912 package every function object aborts in
`dictionary::digest()` (`error in IOstream "sha1"`), including `postProcess -func`.
The prototype therefore uses no function objects: cell centres/volumes come from
`polymesh.py` (cell volumes match `checkMesh -writeAllFields` to 5e-12), and wall shear
stress / y+ are computed from the wall-adjacent cell exactly as `wallShearStress`
does on an orthogonal mesh.
