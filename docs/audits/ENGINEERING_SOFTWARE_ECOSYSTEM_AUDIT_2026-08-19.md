# Engineering software ecosystem audit — 2026-08-19

Status: code-first candidate-integration audit; **not implementation authority**  
Scope: BLUECAD / JarvisOS engineering backends, process simulation, thermodynamics, digital twins, computational geometry, optimization, CFD/FEM and domain libraries.  
Canonical implementation authority remains `docs/specs/STATUS.md`.

## Why this audit exists

This audit started from a maintainer request to inspect BioSTEAM, DWSIM, a remembered thermodynamic-property project, Aspen/Dynsim-like open engineering software, and LEAP 71 repositories.

The remembered thermodynamic project was initially misidentified as `arkharin/OpenCool`. The intended category is instead represented much more closely by **CoolProp**, together with the ChEDL `thermo/chemicals/fluids/ht` ecosystem, ThermoSTEAM and materials-equilibrium libraries. `arkharin/OpenCool` is therefore excluded from the primary candidate set.

The central conclusion is that BLUECAD should not attempt to recreate an Aspen-like monolith. There is already enough maintained permissive or linkable software to justify a **canonical BLUECAD engineering IR plus typed backend adapters**.

---

# Integration-mode legend

- `DIRECT_DEPENDENCY`: commercially compatible permissive component worth evaluating as a maintained upstream dependency.
- `VENDORED_COMPONENT`: permissive source may be vendored when offline deployment, reproducibility or controlled patching materially justify it.
- `LINKED_OR_EXTERNAL`: reciprocal library is potentially usable behind a dynamic-library/process/service boundary after exact legal/compliance review.
- `EXTERNAL_ENGINE`: copyleft or otherwise unsuitable for proprietary embedding; drive it as a separate executable/application/service and exchange explicit artifacts/protocols.
- `REFERENCE_ONLY`: useful architecture/prior art, but current licensing, maturity or fit does not justify integration.

Licensing statements in this audit describe the inspected repository/version only. Dataset, model-weight, plugin and transitive-component licenses require separate release-time review.

---

# Executive candidate map

| Family | Primary role | License posture | Mode | Grade | Main BLUECAD value |
| --- | --- | --- | --- | --- | --- |
| CoolProp | high-accuracy fluid properties | MIT | DIRECT_DEPENDENCY | S | thermophysical backend / REFPROP-like capability |
| ChEDL `thermo` + `chemicals` + `fluids` + `ht` | chemical/property/flash/hydraulics/heat transfer | MIT-family | DIRECT_DEPENDENCY | S | broad chemical and engineering property layer |
| ThermoSTEAM | process-oriented chemical/thermo objects | UIUC/NCSA-style | DIRECT_DEPENDENCY | S- | combines ChEDL and optional CoolProp for process streams |
| BioSTEAM | process flowsheet + convergence + TEA/UQ | UIUC/NCSA-style | DIRECT_DEPENDENCY | S | sequential-modular process and economics backend |
| Bioindustrial-Park | validated biorefinery model corpus | MIT | DIRECT_DEPENDENCY / DATASET-LIKE | A+ | benchmark/reference flowsheets and published cases |
| QSDsan | dynamic bio/wastewater + LCA/TEA | UIUC/NCSA-style | DIRECT_DEPENDENCY | S- | BlueRev-relevant dynamic bioprocess/domain library |
| IDAES + Pyomo | equation-oriented process/dynamics/optimization | BSD-style permissive | DIRECT_DEPENDENCY | S | Aspen-like equation-oriented process backend |
| WaterTAP | water-treatment domain models on IDAES | BSD-style permissive | DIRECT_DEPENDENCY | A+ | proof of domain-pack architecture; usable water models |
| DWSIM full application | Aspen-like steady/dynamic simulator | GPL-3 | EXTERNAL_ENGINE | S reference/integration | automation, CAPE-OPEN, dynamic-simulation interoperability |
| DWSIM Thermodynamics Library | thermo/property packages | LGPL-3 | LINKED_OR_EXTERNAL | A+ | optional mature property-package backend |
| CAPE-OPEN | process-simulation interoperability standard | standard/type-library terms require exact review | ADAPTER TARGET | S | UnitOperation/PropertyPackage/MaterialObject interop |
| FMI/FMU + FMPy | dynamic-model exchange/co-simulation | FMPy BSD-2 | DIRECT_DEPENDENCY | S | neutral digital-twin/model-exchange contract |
| OpenModelica / OMSimulator | Modelica/FMI authoring and co-simulation | OSMC/GPL/proprietary membership paths | EXTERNAL_ENGINE | A+ | external model generation/compilation/simulation |
| do-mpc | MPC + MHE/state estimation | LGPL-3 | LINKED_OR_EXTERNAL | A+ | digital-twin estimation/control layer |
| open62541 | OPC UA client/server/pubsub | MPL-2 | LINKED_OR_EXTERNAL | A+ | plant telemetry/control connector |
| Cantera | kinetics/reactors/combustion/electrochemistry | BSD-like | DIRECT_DEPENDENCY | S- | specialized reaction engineering backend |
| TESPy | thermal-energy networks | MIT | DIRECT_DEPENDENCY | A+ | heat-pump/refrigeration/power-cycle backend |
| pycalphad | CALPHAD/material phase equilibria | MIT | DIRECT_DEPENDENCY | A+ | materials/element phase-equilibrium backend |
| Reaktoro | reactive chemistry/geochemistry | LGPL-2.1 | LINKED_OR_EXTERNAL | A+ | aqueous/electrolyte/reactive systems |
| OpenCalphad | CALPHAD reference | unclear in inspected GitHub metadata | REFERENCE_ONLY | B | compare algorithms/data models; prefer pycalphad for integration |
| LEAP71 PicoGK | implicit/voxel/OpenVDB geometry | Apache-2.0 | DIRECT_DEPENDENCY | S | implicit computational-engineering geometry kernel |
| LEAP71 ShapeKernel | semantic computational geometry | Apache-2.0 | DIRECT_DEPENDENCY | S- | engineering shape construction above PicoGK |
| LEAP71 LatticeLibrary | lattice generation | Apache-2.0 | DIRECT_DEPENDENCY | A+ | manufacturable lattice/domain library |
| LEAP71 HelixHeatX | computational heat-exchanger geometry | Apache-2.0 | DIRECT_DEPENDENCY | A+ | example of engineering semantics generating manufacturable geometry |
| CadQuery | Python parametric B-Rep CAD | Apache-2.0 | DIRECT_DEPENDENCY | S- | traditional equipment geometry, STEP/assemblies/constraints |
| OCCT | industrial B-Rep CAD/CAM/CAE kernel | LGPL-2.1 | LINKED_OR_EXTERNAL | S | underlying precise geometry kernel |
| OpenMDAO | multidisciplinary coupling/optimization | Apache-2.0 | DIRECT_DEPENDENCY | A+ | couple process, geometry, CFD, FEM and economics with derivatives |
| CasADi | symbolic AD / optimal control / DAE | LGPL-3 | LINKED_OR_EXTERNAL | A+ | optimal control, parameter estimation, code generation |
| SUNDIALS | ODE/DAE/nonlinear/time integration | BSD-3 | DIRECT_DEPENDENCY | S- | numerical foundation for dynamic models |
| SU2 | CFD + adjoint/design | LGPL-2.1 | LINKED_OR_EXTERNAL | A+ | CFD/design backend |
| FEniCSx/DOLFINx | general FEM/PDE | LGPL-3 | LINKED_OR_EXTERNAL | A+ | programmable multiphysics FEM backend |
| Gmsh | geometry/mesh/pre-post | GPL-2+ / commercial integration option | EXTERNAL_ENGINE | A+ | meshing backend via files/process; commercial license if embedded |
| CalculiX / Code_Aster | structural/thermal FEA | GPL | EXTERNAL_ENGINE | A | mature external structural solvers |

---

# 1. Thermodynamic and chemical property layer

## 1.1 CoolProp

Upstream: `CoolProp/CoolProp`  
License: MIT  
Recommended mode: `DIRECT_DEPENDENCY`

The inspected `AbstractState` layer is already the abstraction BLUECAD would otherwise need to create internally. It exposes a backend-neutral thermodynamic state and caches/accesses thermodynamic and transport properties including enthalpy, entropy, internal/Gibbs/Helmholtz energy, heat capacities, speed of sound, compressibility, viscosity, thermal conductivity, surface tension, fugacity/chemical potential and fluid constants.

Candidate use:

```text
BLUECAD PropertyProvider
        |
        +-- CoolPropBackend
              +-- HEOS/high-accuracy fluids
              +-- cubic EOS / supported alternative backends
              +-- transport properties
```

Do not duplicate CoolProp tables/correlations inside BLUECAD unless a specific gap is demonstrated.

## 1.2 ChEDL / Caleb Bell ecosystem

Primary projects:

- `CalebBell/thermo`
- `CalebBell/chemicals`
- `CalebBell/fluids`
- `CalebBell/ht`

Recommended mode: `DIRECT_DEPENDENCY`, with **data provenance audited separately from code**.

This ecosystem is broader than CoolProp for general chemical/process work:

- identifiers and constants;
- pure-component correlations;
- mixture/equilibrium models;
- activity coefficients;
- cubic EOS;
- flash (`FlashVL`, `FlashVLN` and related machinery);
- pressure drop/piping/fittings;
- heat-transfer correlations.

This is the strongest current candidate for the maintainer's remembered “software with all thermodynamic properties” category.

## 1.3 ThermoSTEAM

ThermoSTEAM demonstrates that ChEDL + optional CoolProp already work together in a process-oriented chemical/stream abstraction. Its `Chemical` model includes identifiers and extensive property handles: critical constants, boiling/melting points, formation properties, heat capacities, phase volumes/densities, viscosity, thermal conductivity, surface tension, permittivity, EOS and group-contribution/activity-coefficient metadata.

Rather than choosing one universal property database, BLUECAD should define a provider contract and allow high-confidence backends to overlap.

### Proposed `PropertyPackage` boundary

```text
PropertyPackage
  identify_components()
  create_state(specification)
  flash(inputs)
  get_property(name, phase/component scope)
  get_transport_property(name)
  get_phase_equilibrium_state()
  provenance()
  validity_range()
  uncertainty_or_quality_metadata()
```

Candidate backends:

```text
ChEDL/Thermo
CoolProp
ThermoSTEAM
pycalphad
DWSIM DTL
Reaktoro
CAPE-OPEN PropertyPackage
future proprietary/experimental packages
```

The BLUECAD canonical model should not expose one backend's private object model as the domain IR.

---

# 2. Process-simulation engines

## 2.1 BioSTEAM

Upstream: `BioSTEAMDevelopmentGroup/biosteam`  
License: University of Illinois/NCSA-style permissive; explicitly permits use, modification, merge, publication, distribution, sublicensing and sale subject to attribution/no-endorsement conditions.  
Recommended mode: `DIRECT_DEPENDENCY`

### Code-first findings

`System` is a real process execution graph, not a diagram helper. The inspected implementation contains:

- units/streams and process digraphs;
- sequential-modular recycle state;
- material-balance and energy-balance solving;
- composition-sensitive inner fixed-point solving;
- relaxation of recycle/material states;
- root/fixed-point numerical methods;
- dynamic integration support;
- utilities/facilities.

Its evaluation `Model` adds:

- typed parameters/indicators;
- baseline and distribution metadata;
- Monte Carlo / sampling support;
- sensitivity-analysis integration;
- constrained/numerical optimization;
- convergence prediction/modeling.

### TEA is a standalone asset

The inspected `TEA` implementation contains real project economics:

- multiple depreciation schedules;
- working capital;
- construction schedules;
- startup fractions;
- loans and financing;
- replacement cost;
- taxes/incentives;
- inflation;
- NPV/IRR;
- bare-module/Lang-factor extension points.

Therefore BLUECAD should consider BioSTEAM's economics layer independently of whether BioSTEAM is the active physical flowsheet solver.

Candidate mapping:

```text
BLUECAD equipment/streams/cost basis
           |
           v
BioSTEAM-compatible economic adapter
           |
           v
TEA / sensitivity / uncertainty LiveArtifacts
```

## 2.2 Bioindustrial-Park

Upstream: `BioSTEAMDevelopmentGroup/Bioindustrial-Park`  
License: MIT

Treat this primarily as a **reference-model and benchmark corpus**: published biorefinery models, uncertainty/sensitivity cases and TEA results are valuable for validating adapters and later engineering-agent benchmarks.

Do not silently transform published cases into BLUECAD canonical truth; retain source/version and assumptions.

## 2.3 IDAES + Pyomo

Upstream: `IDAES/idaes-pse`, `Pyomo/pyomo`  
License: permissive BSD-style project terms in inspected license files.  
Recommended mode: `DIRECT_DEPENDENCY`

IDAES is the strongest inspected equation-oriented Aspen-like backend.

### Flowsheet contract

The inspected `FlowsheetBlock` supports:

- steady or dynamic configuration;
- a real time domain (`ContinuousSet`) for dynamic models;
- time units;
- nested/shared time domains;
- default property-package configuration separate from the flowsheet.

### Property-package contract

The inspected `PhysicalParameterBlock` / `StateBlock` code has explicit:

- property-package parameters;
- phase/component sets;
- associated state-block classes;
- state variables and display variables;
- initialization;
- scaling;
- inherent reactions;
- ports constructed from thermodynamic state.

This is a highly relevant implementation reference for BLUECAD's canonical `PropertyPackage` / `MaterialState` / `Port` interfaces.

### Strategic use

BioSTEAM and IDAES should not be framed as a winner-take-all choice.

```text
BioSTEAM -> sequential modular + TEA/UQ + strong bio/process workflow
IDAES    -> equation-oriented + optimization + rigorous dynamic algebraic model
```

BLUECAD should own a neutral `ProcessModelIR`, then allow backend eligibility based on model capability.

## 2.4 WaterTAP

Upstream: `watertap-org/watertap`  
License: permissive BSD-like terms  
Recommended mode: direct domain library where relevant.

WaterTAP proves an important architecture pattern: a general equation-oriented core can support **vertical domain packs** rather than accumulating all equipment in one monolith.

Possible BLUECAD domain packs:

```text
core-process
chemical
thermal
water
bio
materials
BlueRev
```

## 2.5 QSDsan

Upstream: `QSD-Group/QSDsan`  
License: University of Illinois/NCSA-style permissive.  
Recommended mode: `DIRECT_DEPENDENCY` / domain backend.

The repository contains dynamic unit implementations including influent, CSTR, anaerobic reactor, generic bioreactor, clarifier, membrane bioreactor, electrochemical cell, pumping, sludge treatment and membrane gas extraction, in addition to sustainability/LCA/TEA concepts.

This is unusually relevant to BlueRev because it provides ready-made dynamic biological/resource-recovery abstractions that can be mapped into future photobioreactor and water/biological digital twins.

## 2.6 DWSIM

Upstream: `DanWBR/dwsim` / official DWSIM ecosystem.

### License boundary

- full application/dynamics code inspected: GPL-3-or-later -> `EXTERNAL_ENGINE` for a proprietary BLUECAD distribution;
- DWSIM Thermodynamics Library: LGPL family -> evaluate `LINKED_OR_EXTERNAL` separately.

### Automation API

The inspected automation layer provides flowsheet creation/loading/saving/calculation and a registry of property packages including CoolProp, PR/SRK/PRSV variants, activity-coefficient methods, GERG, PC-SAFT, steam tables, seawater and CAPE-OPEN-related paths. It also loads external chemical datasets including ChEDL integration.

DWSIM is therefore a strong **interoperability target and regression reference**, even when its GPL application code is not embedded.

### Dynamics data model

`DWSIM.DynamicsManager` separates:

- schedules;
- event sets;
- cause-and-effect matrices;
- integrators;
- monitored variables;
- historian state.

The `Integrator` carries separate switches/rates for equilibrium, pressure-flow and control calculation plus integration step, duration and real-time mode.

Event transitions can refer to initial state / previous event / explicit event and may be step, linear, logarithmic, inverse-logarithmic or random. The manager restores historical snapshots to evaluate transition state.

This is a strong reference for a future Dynsim-like BLUECAD contract even if the execution backend is different.

---

# 3. Process interoperability standards

## 3.1 CAPE-OPEN

CAPE-OPEN should become a first-class interoperability target rather than merely a file-import feature.

The standard already separates concepts BLUECAD needs:

- Process Modelling Environment (PME);
- Unit Operation;
- Property Package;
- Material Object;
- ports;
- parameters;
- thermodynamic interfaces;
- persistence/error/numerical-service contracts.

Candidate strategy:

1. make BLUECAD's native IR semantically compatible where practical;
2. create explicit CAPE-OPEN adapters on Windows;
3. do not let COM/.NET CAPE-OPEN object identity become the canonical BLUECAD object model;
4. preserve provider/version/provenance for every imported property/unit package.

## 3.2 FMI / FMU / FMPy

Upstream: `CATIA-Systems/FMPy`  
License: BSD-2-Clause  
Recommended mode: `DIRECT_DEPENDENCY`

FMI provides a mature vendor-neutral contract for dynamic model exchange/co-simulation. FMPy gives a permissive Python implementation for inspecting and simulating FMI 1/2/3 FMUs.

Candidate BLUECAD object:

```text
FMUAsset
  file_digest
  fmi_version
  mode: model_exchange | co_simulation | scheduled_execution
  typed_inputs
  typed_outputs
  parameters
  states
  units
  source_model/provenance
  simulation_history
```

This enables Modelica/open tools and future proprietary tools to feed the same digital-twin layer without forcing BLUECAD to own their equation compiler.

## 3.3 OpenModelica / OMSimulator

OpenModelica is valuable as an **external authoring/compiler/simulation engine**, but its current OSMC/GPL/proprietary-membership licensing is not the same as a permissive library.

OMSimulator is similarly useful for SSP/FMI co-simulation but carries the OSMC license file.

Prefer:

```text
OpenModelica -> build/export FMU
FMPy/BLUECAD -> own FMU asset and runtime integration
```

rather than making the OpenModelica runtime part of BLUECAD's proprietary core.

---

# 4. Digital-twin state estimation, control and telemetry

A digital twin should not be one opaque object.

Recommended canonical separation:

```text
ModelAsset
TelemetryBinding
Estimator
CalibrationRun
Controller
Scenario/EventSchedule
Historian / EvidenceSeries
```

## 4.1 do-mpc

License: LGPL-3  
Mode: `LINKED_OR_EXTERNAL`

The inspected tree contains both MPC and Moving Horizon Estimation (MHE) plus an OPC-UA-related module. It is therefore a practical reference/backend for:

`plant telemetry -> estimated state/parameters -> calibrated model -> predictive control`.

## 4.2 open62541

License: MPL-2.0  
Mode: isolated `LINKED_OR_EXTERNAL` component with file-level compliance.

Candidate role: OPC UA client/server/pubsub connector for industrial plant telemetry and commands. JarvisOS authority/policy must remain above it; OPC UA connectivity is not execution authorization.

## 4.3 SUNDIALS

License: BSD-3-Clause  
Mode: `DIRECT_DEPENDENCY`

SUNDIALS is a strong general numerical foundation for ODE/DAE, nonlinear solves, sensitivity analysis and time integration. It becomes relevant if BLUECAD owns dynamic models directly instead of delegating every time integration to IDAES/Cantera/FMU/CasADi.

---

# 5. Specialized engineering backends

## 5.1 Cantera

License: permissive BSD-style  
Mode: `DIRECT_DEPENDENCY`

The inspected `ReactorNet` code supports time-dependent reactor networks, flow controllers/valves/walls, time/spatial integration, steady-state solving, DAE-related operation, Jacobians, solver tolerances/preconditioners and sensitivities.

Candidate domain: detailed kinetics, combustion, reacting systems and electrochemistry.

## 5.2 TESPy

License: MIT  
Mode: `DIRECT_DEPENDENCY`

TESPy's `Network` builds a system of equations from component topology/specifications and supports design/offdesign workflows plus serialized network state. It is a strong ready-made backend for heat pumps, refrigeration, power cycles and thermal networks.

## 5.3 Materials/reactive thermodynamics

### pycalphad

MIT. Strong candidate for CALPHAD phase equilibria and material thermodynamic calculations.

### Reaktoro

LGPL-2.1. Strong specialized backend for aqueous/reactive/geochemical/electrolyte systems; isolate behind a link/process boundary.

### OpenCalphad

Code exists and remains active, but no sufficiently clear license was established in this audit. Keep `REFERENCE_ONLY` until exact reuse rights are proven. Prefer pycalphad for direct proprietary integration today.

---

# 6. Computational geometry — LEAP 71 and B-Rep

## 6.1 PicoGK

Upstream: `leap71/PicoGK`  
License: Apache-2.0  
Mode: `DIRECT_DEPENDENCY`

PicoGK is a compact implicit/voxel computational-engineering geometry kernel. The inspected `Voxels` layer can create geometry from implicit functions, meshes, lattices and scalar fields and supports boolean union/subtract/intersect.

This is highly suitable for generated/additive/manifold-like engineering geometry that is awkward in traditional feature-history CAD.

## 6.2 LEAP71 ShapeKernel

License: Apache-2.0  
Mode: `DIRECT_DEPENDENCY`

ShapeKernel provides semantic construction layers over PicoGK: base shapes, frames, functions, modulations, splines, utilities and visualization.

Important pattern: code describes engineering intent and generates geometry deterministically; the UI is not the source of geometric truth.

## 6.3 LEAP71 LatticeLibrary

License: Apache-2.0.

A maintained lattice library above PicoGK/ShapeKernel. Candidate for direct reuse in heat exchangers, structured internals, porous/support structures and additive-manufactured BlueRev components.

## 6.4 HelixHeatX

License: Apache-2.0.

This is a particularly useful architecture reference because the model generates semantically meaningful manufacturable heat-exchanger geometry (fluid volumes, fins, walls, flanges/support features) rather than merely scripting generic CAD commands.

Candidate BLUECAD pattern:

```text
EngineeringObject
  governing parameters
  constraints
  semantic regions
  geometry generator
  simulation domains
  manufacturing metadata
```

## 6.5 PicoGK simulation-artifact concept

The simulation example demonstrates a valuable data-model idea: geometry, physical domains, boundary-condition patches and scalar/vector fields can coexist in one semantic artifact. Even where the example repository's exact license needs separate confirmation, the concept is worth retaining.

Candidate BLUECAD `SimulationArtifact`:

```text
artifact_id
geometry_version
material/domain labels
boundary-condition regions
scalar/vector/tensor fields
mesh or discretization reference
solver configuration
result fields
units
provenance
source model digest
verification state
```

Results should return attached to the same engineering domains instead of becoming anonymous screenshots/CSV files.

## 6.6 CadQuery + OCCT

CadQuery license: Apache-2.0  
OCCT license: LGPL-2.1

The inspected CadQuery `Assembly` contains hierarchical named objects, material and arbitrary metadata, geometric selectors, constraints and a constraint solver; assembly import/export includes STEP and visualization formats.

Therefore BLUECAD should not force all geometry into PicoGK.

### Dual-kernel proposal

```text
Canonical BLUECAD GeometryAsset
        |
        +-- BRepBackend
        |     CadQuery -> OCCT
        |     STEP / precise faces / assemblies / conventional equipment
        |
        +-- ImplicitBackend
              PicoGK -> OpenVDB-like fields
              lattices / generative forms / additive geometry
```

Conversion is an explicit operation with quality/provenance metadata, not a hidden coercion.

---

# 7. Multidisciplinary optimization and coupling

## 7.1 OpenMDAO

License: Apache-2.0  
Mode: `DIRECT_DEPENDENCY`

The inspected `Group` layer maintains a real dependency graph, explicit and implicit systems, continuous/discrete connections, units conversion, dynamic shape dependencies, nonlinear and linear solvers, MPI process allocation, Jacobian infrastructure and derivative scopes.

This makes OpenMDAO attractive as a **coupling/MDO layer above heterogeneous engineering backends**:

```text
process model ---------
geometry --------------|
CFD -------------------|--> OpenMDAO problem/derivatives --> optimizer
FEA -------------------|
TEA/LCA ----------------
```

Do not use OpenMDAO objects as BLUECAD's permanent domain representation. Generate/wrap them from the canonical IR.

## 7.2 CasADi

License: LGPL-3.

Useful specialized layer for automatic differentiation, sparse symbolic graphs, nonlinear optimization, optimal control, ODE/DAE and code generation. Strong fit for advanced MPC/calibration, but not necessary as the single optimization representation for all BLUECAD tasks.

---

# 8. Mesh, CFD and FEM

## 8.1 Gmsh

License posture: GPL-2-or-later for the open distribution, with an explicit commercial-license path for closed-source integration.

Recommended mode today: `EXTERNAL_ENGINE` via command/process/files unless a commercial embedding license is deliberately acquired.

It remains an excellent mesher/backend because it exposes geometry/mesh/postprocessing APIs and supports the OpenCASCADE kernel.

## 8.2 SU2

License: LGPL-2.1.

Strong CFD/design backend, especially for adjoint/design-optimization use. Isolate behind an adapter and preserve solver/version/configuration provenance.

## 8.3 FEniCSx / DOLFINx

License: LGPL-3.

General programmable FEM/PDE backend suitable for custom multiphysics. It is complementary to turnkey structural solvers: use when BLUECAD needs explicit weak-form/model ownership rather than a fixed solver menu.

## 8.4 CalculiX / Code_Aster

GPL external solvers. Treat them as `EXTERNAL_ENGINE` processes, with BLUECAD owning input generation, execution manifest, artifact collection and deterministic post-run verification.

A proprietary orchestration layer does not need to copy solver source to gain value from these engines.

---

# 9. Proposed BLUECAD engineering architecture

The audited projects converge on a modular architecture:

```text
BLUECAD CANONICAL ENGINEERING IR
|
+-- Component / Chemical Registry
|   +-- identifiers
|   +-- units / provenance / validity
|
+-- Process Model
|   +-- Streams
|   +-- Ports
|   +-- Equipment
|   +-- Connections
|   +-- Specifications
|   +-- Events / schedules
|
+-- PropertyPackage interface
|   +-- ChEDL / thermo / chemicals / fluids / ht
|   +-- CoolProp
|   +-- ThermoSTEAM
|   +-- DWSIM DTL
|   +-- Reaktoro
|   +-- pycalphad
|   +-- CAPE-OPEN packages
|
+-- ProcessExecution adapter
|   +-- BioSTEAM
|   +-- IDAES / Pyomo
|   +-- DWSIM external
|   +-- TESPy
|   +-- domain packs: WaterTAP / QSDsan
|
+-- DynamicModel / Twin
|   +-- FMU / FMPy
|   +-- OpenModelica external
|   +-- Estimator / MHE
|   +-- Controller / MPC
|   +-- OPC UA telemetry
|   +-- historian + calibration runs
|
+-- GeometryAsset
|   +-- B-Rep: CadQuery / OCCT
|   +-- implicit: PicoGK / ShapeKernel
|
+-- SimulationArtifact
|   +-- domains
|   +-- BCs
|   +-- fields
|   +-- mesh
|   +-- solver run
|   +-- results + provenance
|
+-- Solver adapters
|   +-- Cantera
|   +-- SU2
|   +-- FEniCSx
|   +-- Gmsh external
|   +-- CalculiX / Code_Aster external
|
+-- Coupling / optimization
|   +-- OpenMDAO
|   +-- Pyomo / IDAES
|   +-- CasADi
|   +-- SUNDIALS numerics
|
+-- Economics / sustainability
    +-- BioSTEAM TEA
    +-- QSDsan LCA/TEA
    +-- domain-specific cost models
```

## Core rule

**BLUECAD owns identity, IR, typed adapters, provenance, versioning, execution manifests, verification and UX. It does not need to own every numerical kernel.**

This preserves commercial differentiation while using mature permissively licensed engineering science rather than recreating it.

---

# 10. Interop with commercial engineering tools

The same IR should support external proprietary tools:

```text
Aspen HYSYS adapter
AVEVA/Dynsim adapter
CAPE-OPEN adapter
FMU adapter
DWSIM adapter
```

Commercial engines remain external authorities for their own calculations. Jarvis/BLUECAD should capture:

- exact model/file/version;
- input mapping;
- property package;
- solver configuration;
- run ID;
- stdout/log/evidence where available;
- exported result fields;
- deterministic postconditions.

This prevents a commercial-tool integration from becoming a special UI automation hack.

---

# 11. Engineering benchmark opportunity

The existing Harbor / Verifiers engineering-agent work should later include real tasks built around these open backends:

- create/repair a BioSTEAM recycle flowsheet;
- choose and configure a CoolProp/ChEDL property package;
- reproduce an IDAES state/flash result;
- generate a CadQuery equipment geometry with invariant dimensions;
- generate a PicoGK semantic domain artifact;
- run Cantera reactor/kinetics cases;
- calibrate an FMU using measured traces;
- optimize coupled geometry/process/economics through OpenMDAO;
- verify solver artifacts rather than score prose.

Permissive open engineering software is therefore useful twice: **product backend and deterministic benchmark oracle**.

---

# 12. Next audit queue

High-value next code audits, in order:

1. CAPE-OPEN current reference implementations/type libraries and redistribution terms.
2. permissive meshing candidates or wrappers that reduce reliance on GPL Gmsh for embedded use.
3. VTK / ParaView and scientific-result visualization/data-model layers.
4. OpenFOAM plus OpenFOAM Python/control adapters as an external CFD engine comparison to SU2.
5. PETSc / petsc4py as a scalable linear/nonlinear numerical backend.
6. OpenFAST / Modelica domain libraries if mechanical/energy digital twins become relevant.
7. python-control / estimation libraries as narrower alternatives to do-mpc where only state-space/control primitives are needed.
8. inspect current process-simulation AI/agent projects only when they expose executable engineering contracts, not README-only wrappers.
9. search for the exact repository behind the newly published PyOMES dynamic-process framework and audit code/license if available.
10. investigate diagram/PFD-to-simulation pipelines such as Sketch2Simulation only after source code is located; paper claims are not implementation evidence.

---

# Promotion rule for engineering dependencies

Before any candidate becomes an implementation spec:

1. define the exact BLUECAD problem it replaces or enables;
2. select the narrowest upstream component that solves it;
3. pin exact version/commit and inspect transitive licenses/data/model terms;
4. build a tiny adapter prototype against the canonical IR;
5. compare numerical behavior to a trusted engineering reference;
6. define deterministic verifier/tolerances and units;
7. record attribution/SBOM obligations;
8. only then create the governing spec/ADR.

This audit itself grants no implementation authority.
