# Engineering software ecosystem audit — continuation — 2026-08-19

Status: code-first continuation; **not implementation authority**.

This file extends `ENGINEERING_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-19.md` with result-data, scalable numerics, CFD and mesh-interchange findings.

## VTK / ParaView / PyVista

### VTK

Upstream: `Kitware/VTK`  
License: BSD-like terms in `Copyright.txt`  
Mode: `DIRECT_DEPENDENCY`  
Grade: S for scientific result representation/filters.

VTK should be evaluated as a **result-data and scientific-pipeline layer**, not merely as a renderer. It already provides mature representations and processing for meshes, grids, scalar/vector/tensor fields and derived visualization/analysis pipelines.

Candidate BLUECAD use:

```text
SimulationArtifact
   |
   +-- canonical engineering provenance/semantic regions
   |
   +-- VTK-compatible numerical dataset
          +-- points/cells
          +-- scalar fields
          +-- vector fields
          +-- tensor fields
          +-- time series
```

BLUECAD remains the owner of engineering identity/provenance; VTK handles numerical geometry/field representation and filters.

### ParaView

Upstream: `Kitware/ParaView`  
License: BSD-3-Clause  
Mode: `DIRECT_DEPENDENCY` for reusable libraries where appropriate and/or `EXTERNAL_TOOL` for inspection/debugging.  
Grade: A+.

ParaView is a strong external validation/debug surface for solver artifacts. A BLUECAD solver adapter should ideally be able to emit an artifact that can be opened independently in ParaView, reducing dependence on BLUECAD's own visualization code when debugging numerical correctness.

### PyVista

Upstream: `pyvista/pyvista`  
License: MIT  
Mode: `DIRECT_DEPENDENCY`  
Grade: S- for Python-side engineering visualization/mesh analysis.

PyVista provides a much narrower Python integration surface over VTK than adopting ParaView internals. It is a strong candidate for backend-side derived plots, mesh analysis, field extraction and test utilities.

## meshio

Upstream: `nschloe/meshio`  
License: MIT  
Mode: `DIRECT_DEPENDENCY`  
Grade: A+.

`meshio` solves a different problem from a mesher: it normalizes **mesh file interchange**. This is valuable because BLUECAD can use GPL/LGPL/commercial mesh generators and solvers as separate engines while keeping a permissive internal import/export layer.

Candidate use:

```text
Gmsh / Netgen / SU2 / FEniCS / CalculiX / Code_Aster / third-party solver
                          |
                          v
                       meshio
                          |
                          v
                 BLUECAD MeshArtifact
```

Do not assume format conversion preserves all solver-specific boundary groups or semantic metadata. BLUECAD must verify named regions, physical groups, units and cell/field semantics explicitly.

## Netgen

Upstream: `NGSolve/netgen`  
License: LGPL-2.1  
Mode: `LINKED_OR_EXTERNAL`  
Grade: A.

Netgen is a viable alternative mesher to Gmsh with a less restrictive library-style license, but it is still reciprocal rather than permissive. It should be evaluated when embedded meshing is required and LGPL compliance is acceptable.

It does not eliminate the value of Gmsh as an external meshing engine.

## PETSc

Upstream: `petsc/petsc`  
License: BSD-like redistribution terms  
Mode: `DIRECT_DEPENDENCY`  
Grade: S- for scalable numerical infrastructure.

PETSc is a strong future foundation for distributed linear/nonlinear solves, time integration and scalable PDE systems.

Important license boundary: PETSc's root license explicitly states that software fetched through its `--download-package` mechanism remains under each package's own license. A JarvisOS/BLUECAD distribution must therefore audit optional PETSc solver packages independently rather than treating the PETSc license as transitive coverage.

Recommended role:

- do not expose PETSc objects as the BLUECAD engineering IR;
- use PETSc beneath solver adapters or custom numerical backends;
- record exact PETSc build and optional solver packages in the execution manifest/SBOM.

## OpenFOAM

Upstream: `OpenFOAM/OpenFOAM-dev`  
License: GPL-3-or-later  
Mode: `EXTERNAL_ENGINE`  
Grade: S reference / A+ integration target.

OpenFOAM remains one of the most important CFD engines to support despite being unsuitable for proprietary in-process embedding.

Candidate adapter boundary:

```text
BLUECAD Geometry/Domain/BC IR
           |
           v
OpenFOAM case generator
           |
           v
OpenFOAM external executable
           |
           v
logs + mesh + field files
           |
           v
meshio / VTK / PyVista ingest
           |
           v
BLUECAD SimulationArtifact + deterministic verifier
```

The commercial differentiation is the semantic model, orchestration, provenance, validation and UX rather than ownership of Navier-Stokes kernels.

## Updated CAE artifact stack

```text
GeometryAsset
  B-Rep: CadQuery/OCCT
  implicit: PicoGK/ShapeKernel
        |
        v
Meshing
  Gmsh external
  Netgen linked/external
  other future backend
        |
        v
MeshArtifact
  canonical named regions / units / provenance
  meshio import/export
        |
        v
Solver
  OpenFOAM external
  SU2 linked/external
  FEniCSx linked/external
  CalculiX/Code_Aster external
        |
        v
FieldArtifact
  VTK-compatible numerical data
  verification/provenance owned by BLUECAD
        |
        +-- PyVista backend analysis
        +-- ParaView independent inspection
        +-- BLUECAD frontend rendering
```

This separation is preferred over binding a solver directly to a frontend scene object.

## Updated next queue

1. CAPE-OPEN concrete type libraries/reference packages and redistribution boundary.
2. OpenFOAM case structure/function-object/runtime-selection code to design the narrow adapter.
3. VTK/PyVista time-series and multiblock data structures for the canonical `FieldArtifact` prototype.
4. PETSc/petsc4py only if a custom BLUECAD solver layer becomes an authorized need.
5. state-estimation/control alternatives (`python-control`, filter/estimator libraries) for lightweight digital twins.
6. locate/audit PyOMES source if the new dynamic-process project publishes it.
7. locate code for PFD/diagram-to-simulation systems before treating paper claims as implementation evidence.
