# Engineering software ecosystem audit — continuation 2 — 2026-08-19

Status: code-first continuation; **not implementation authority**.

This file extends the engineering-software audit with process/digital-twin interoperability, P&ID/flowsheet intelligence, industrial plant ingestion, calibration/data reconciliation and model diagnostics.

---

# 1. NeqSim — process + thermodynamics + digital-twin backend

Upstream: `equinor/neqsim`  
License: Apache-2.0  
Mode: `DIRECT_DEPENDENCY`  
Grade: **S**

NeqSim is one of the strongest engineering candidates found in the entire audit because the current repository spans thermodynamics, process modeling, structured interchange, dynamic simulation, calibration, data reconciliation and tooling for migration from proprietary process simulators.

## 1.1 Declarative process JSON

The current `neqsim.process.processmodel` package contains:

- `JsonProcessBuilder`;
- `JsonProcessExporter`;
- `ProcessJsonValidator`;
- explicit process connections;
- PFD export;
- DEXPI reader/writer and round-trip metadata.

`ProcessJsonValidator` exposes different validation profiles and checks canonical keys, equipment names/types/properties and, in full mode, process connectivity. This is a strong reference for BLUECAD's own validation layer.

`JsonProcessBuilder` compiles declarative JSON into a process model in multiple passes. It supports several thermodynamic model families and deliberately separates object creation from connection/wiring so forward references and recycle topology can be handled.

Candidate BLUECAD pattern:

```text
BLUECAD ProcessModelIR
   |
   +-- deterministic validation
   |
   +-- backend compiler
          +-- NeqSim
          +-- BioSTEAM
          +-- IDAES
          +-- DWSIM external
```

The backend JSON must remain a projection/compile target rather than BLUECAD's sole source of truth.

## 1.2 DEXPI semantic round-trip

NeqSim's DEXPI work is notable because the round-trip profile checks engineering semantics rather than only XML parse success. Inspected checks include retention of equipment/stream identity, line/fluid data, operating conditions and source metadata.

This suggests a BLUECAD rule:

> an interchange round-trip is successful only if required engineering semantics and runnable model state survive, not merely if the resulting document is syntactically valid.

## 1.3 Steady design -> dynamic candidate

`DynamicProcessHelper` scans a steady process, creates measurement devices such as pressure/level/temperature/flow transmitters, finds relevant control valves, creates PID controllers, seeds setpoints from the steady solution, changes the process to transient calculation and applies a time step.

This is a strong product concept for BLUECAD:

`PromoteSteadyDesignToDynamicCandidate`

The operation should generate **proposals** for instrumentation/control topology and tuning. It should not silently turn design heuristics into production control authority.

## 1.4 Batch calibration

`BatchParameterEstimator` provides offline parameter estimation using historical runs, Levenberg-Marquardt-style optimization, parameter bounds, standard deviations, operating-condition data and covariance/correlation information.

Candidate BLUECAD object:

```text
CalibrationRun
  model_version
  dataset/evidence refs
  estimated_parameters
  parameter_bounds
  covariance/correlation
  residual statistics
  solver/options
  verifier outcome
```

## 1.5 Online EnKF parameter estimation

`EnKFParameterEstimator` adds sequential ensemble-Kalman updates with parameter uncertainty, confidence and history. This is more suitable for live digital twins than treating one fitted parameter vector as permanent truth.

Canonical separation should remain:

```text
raw telemetry
   -> data reconciliation
   -> estimator
       +-- batch historical calibration
       +-- online ensemble state/parameter estimate
   -> controller / prediction
```

## 1.6 Data reconciliation

`DataReconciliationEngine` implements weighted least-squares adjustment under equality constraints. It carries measurement uncertainties/covariance, returns raw vs adjusted values/residuals and includes chi-square / normalized residual support for gross-error detection.

This is a direct fit for the future engineering-data layer and should be compared against Pyomo/IDAES alternatives before any custom reconciliation code is written.

## 1.7 Gym/RL interface caveat

NeqSim includes a `GymEnvironment` / episode-runner abstraction suitable for converting process behavior into learning environments.

Do **not** treat all bundled examples as physics oracles. The inspected separator example uses deliberately simplified level dynamics and randomness rather than a high-fidelity dynamic model.

Useful reuse:

- environment contract;
- observation/action/reward/termination structure;
- episode/result capture.

Required Jarvis improvement:

- engineering training environments must be backed by validated physics or deterministic domain verifiers.

## 1.8 UniSim migration / regression

`devtools/unisim_reader.py` is unusually valuable. It uses COM to inspect UniSim and extracts substantially more than drawing topology, including property-package and component information, hypothetical-component data, critical properties, binary interaction parameters, volume shifts and enthalpy coefficients. It also contains comparison tooling for running UniSim and NeqSim against each other.

This suggests a powerful commercial-to-open migration path:

```text
UniSim/HYSYS-like source model
      |
      +-- topology
      +-- thermo basis
      +-- component metadata/BIPs
      +-- operating cases
      v
BLUECAD migration package
      |
      +-- NeqSim/open backend model
      +-- side-by-side regression suite
```

A migration is not complete until numerical regression demonstrates acceptable agreement under stated tolerances.

---

# 2. Sketch2Simulation — structured process-diagram ingestion

Upstream: `OptiMaL-PSE-Lab/Sketch2Simulation`  
License: MIT  
Mode: selective `DIRECT_DEPENDENCY` / reference  
Grade: A+

The important value is not “LLM writes HYSYS Python”. It is the **structured normalization layer between probabilistic diagram understanding and simulator execution**.

## 2.1 Strong path

The inspected coupling normalizer:

- creates typed graph edges;
- removes orphan/inconsistent edges;
- recognizes integrated column / reboiler / condenser / reflux patterns;
- retains evidence stream IDs;
- rewrites topology for downstream HYSYS compilation;
- removes resulting self-loops.

Candidate BLUECAD ingestion:

```text
image / sketch / PDF
   -> multimodal extraction
   -> candidate graph with provenance/confidence
   -> deterministic topology normalizer
   -> canonical BLUECAD ProcessModelIR
   -> solver-specific compiler
   -> engineering verifier
```

## 2.2 Weak path

The inspected execution agent writes generated Python to a temporary file and runs it through `subprocess.run` with timeout. Successful exit code is a major success signal. The fixer agent then feeds code/log/issue report to a local Qwen/Ollama model.

Do not copy this as the BLUECAD verifier/sandbox model.

JarvisOS improvements required:

- hard execution sandbox;
- exact authority scope;
- typed compiler inputs rather than arbitrary generated Python where possible;
- solver-state and engineering postcondition verification;
- exact model/artifact provenance.

---

# 3. DEXPI, pyDEXPI and process-document interchange

## DEXPI 2.0

DEXPI is a high-priority interoperability standard for PFD/P&ID/plant data. Current DEXPI 2.0 separates/relates plant and process models and no longer requires Proteus as the only conceptual serialization path.

BLUECAD should aim to support DEXPI as an interchange surface while keeping a canonical internal IR that can evolve independently.

## pyDEXPI

Upstream: `process-intelligence-research/pyDEXPI`  
License: AGPL-3.0  
Mode: `REFERENCE_ONLY` or separately licensed service/component.

pyDEXPI provides a strong Python implementation reference: Pydantic domain model, Proteus loading, JSON/pickle serialization, graph abstraction, SVG rendering and synthetic P&ID generation.

Because the upstream explicitly states AGPL copyleft and offers separate commercial licensing, do not incorporate it into the proprietary BLUECAD core under the public license.

Prefer:

- DEXPI standard itself;
- permissive NeqSim DEXPI components where sufficient;
- independently implemented adapter code derived from the published standard rather than copied AGPL source;
- or negotiate a commercial pyDEXPI license if the implementation becomes strategically superior.

---

# 4. SFILES2 — compact process-graph projection

Upstream: `process-intelligence-research/SFILES2`  
License: MIT  
Mode: `DIRECT_DEPENDENCY`  
Grade: A+

The inspected implementation maintains a `networkx.MultiDiGraph`, treating unit operations as nodes and process/control streams as typed multi-edges. It encodes branch/recycle/cycle structure and converts bidirectionally between graph and SFILES strings.

Recommended role:

**SFILES is a projection, not the source of truth.**

Use it for:

- compact LLM context;
- retrieval/indexing;
- training data;
- topology comparison/deduplication;
- text-friendly process search.

Canonical engineering metadata, parameters, provenance and detailed P&ID semantics remain in BLUECAD IR / DEXPI-compatible structures.

---

# 5. ENFORCE — physically constrained surrogate models

Upstream: `process-intelligence-research/ENFORCE`  
License: MIT  
Mode: `DIRECT_DEPENDENCY` / R&D component  
Grade: A

The core neural model does not merely add constraint residuals to a training loss. After the network predicts an output, an adaptive Newton-style projection enforces nonlinear equality and inequality constraints. Inequalities can be reformulated with Fischer-Burmeister, and the backward path uses an implicit-function formulation rather than retaining all projection iterations.

Candidate use:

```text
validated high-fidelity solver
       -> generated dataset
       -> ENFORCE surrogate
       -> independent physical residual verifier
       -> fast optimization / online twin prediction
```

Never allow the surrogate to become the canonical truth solely because constraints are projected to zero; approximation error against the underlying physical model must remain measured.

---

# 6. Generalized Graph Line Entry System

Upstream: `process-intelligence-research/Generalized-graph-line-entry-system`  
License: MIT  
Mode: optional direct utility  
Grade: B+

GGILES generalizes depth-first graph serialization to sequential strings and reconstructs NetworkX graphs. It is potentially useful for graph-based language-model representations, but SFILES2 is more semantically valuable for process engineering.

---

# 7. Chemical Engineering Knowledge Graph client

Upstream: `process-intelligence-research/ChemEngKG_kgtool`  
License: MIT for the client package  
Mode: `DIRECT_DEPENDENCY` for interface code, **data license/provenance separate**  
Grade: A-

The package exposes a GraphQL/SPARQL-oriented `ChemKG` interface with graph listing/export, SPARQL execution and file-to-resource linking using URIs/hashes.

Important boundary:

- MIT license of the client does not establish redistribution rights for every knowledge-graph dataset or backend source;
- the README references a separate backend repository which was not publicly resolvable during this audit;
- use the interface/client pattern, but audit graph content provenance before importing a corpus into JarvisOS.

Potential Jarvis role:

`EngineeringKnowledgeSource` queried from structured evidence rather than using an LLM's parametric memory as the source of chemical-engineering facts.

---

# 8. KG4DT — knowledge-graph digital twin reference

Upstream: `sustainable-processes/KG4DT`  
License: Creative Commons Attribution-NonCommercial 4.0  
Mode: `REFERENCE_ONLY`  
Grade: B+

The project combines ontologies/knowledge graph with process/model knowledge and functional agents for model assembly/calibration/database/model operations.

Because the repository is explicitly non-commercial, no source should enter BlueRev/JarvisOS under the current license.

The useful architectural question is retained:

> Should a digital-twin knowledge graph be a separate source of truth or a derived semantic view?

Recommended BLUECAD answer: **derived semantic projection**.

```text
Canonical BLUECAD engineering IR
        |
        +-- deterministic semantic projection
                 -> RDF/knowledge graph
                 -> GraphRAG / reasoning / discovery
```

A KG should not silently diverge from the actual model/telemetry/configuration objects that control simulations.

---

# 9. OpenFMSL — structural solver diagnostics reference

Upstream: `Nukleon84/OpenFMSL`  
License: MIT  
Mode: `REFERENCE_ONLY` / selective algorithm reuse  
Grade: B+

Although old, the compact C# equation-oriented solver exposes useful transparent numerical behavior:

- build a global equation system;
- generate Jacobian;
- Dulmage-Mendelsohn decomposition;
- identify over-constrained / under-specified systems;
- blockwise Newton + line search;
- on failure, list the constraints with the largest residuals.

This produces two strong BLUECAD UX primitives:

1. structural DOF diagnosis;
2. top failing constraints/residuals after numerical failure.

IDAES currently provides a more mature implementation of the same philosophy and should be preferred for direct integration.

---

# 10. IDAES DiagnosticsToolbox — first-class engineering explainability

Upstream: `IDAES/idaes-pse`  
License: permissive IDAES terms already recorded in the main audit  
Mode: `DIRECT_DEPENDENCY`  
Grade: S

The current diagnostics system has grown into a dedicated subpackage rather than a helper function. The inspected `DiagnosticsToolbox` separates structural checks (which can be run before initialization) from numerical checks after a partial/complete solution.

It covers, among other things:

- degrees of freedom;
- inconsistent units;
- external/unused/uninitialized variables;
- bounds and near-bound values;
- large constraint residuals;
- extreme/canceling constraint terms;
- Jacobian magnitude and parallel row/column behavior;
- conditioning certificates / SVD;
- degeneracy;
- convergence analysis.

Most importantly, output semantics are organized as:

`Warnings -> Cautions -> Next Steps`.

Candidate BLUECAD capability:

```text
DiagnoseModel(model_version, optional run)
  structural_status
  numerical_status
  findings[]
     severity
     model_component_refs
     evidence
     explanation
     suggested_next_diagnostic
  recommended_next_steps[]
```

This is much better than allowing an LLM to infer the reason for non-convergence solely from a solver log.

---

# 11. Pyomo parmest — offline parameter estimation

Upstream: `Pyomo/pyomo` (`pyomo.contrib.parmest`)  
License: BSD-3-Clause  
Mode: `DIRECT_DEPENDENCY`  
Grade: A+

The inspected parameter-estimation module supports:

- SSE and measurement-error-weighted SSE;
- explicit experiment outputs / unknown parameters;
- prior Fisher Information Matrix validation;
- regularization against prior parameter estimates;
- sensitivities;
- multi-experiment/scenario machinery;
- covariance-related analysis.

This should be compared directly with NeqSim's batch estimator rather than building an independent BLUECAD parameter optimizer.

---

# 12. GEKKO / APMonitor — dynamic optimization reference and candidate

Upstream: `BYU-PRISM/GEKKO`  
Python repository license: MIT  
Mode: `CANDIDATE`, exact bundled solver/APMonitor binary terms must be audited before redistribution  
Grade: A+

GEKKO is technically highly relevant. The current README documents nine APMonitor modes spanning:

- steady-state simulation;
- parameter update;
- real-time optimization;
- dynamic simulation;
- moving-horizon estimation;
- nonlinear predictive control/dynamic optimization;
- sequential variants of dynamic simulation/estimation/optimization.

The backend compiles equations to a sparse representation, performs structural/model reduction and uses orthogonal collocation for DAE transcription. It also emits `infeasibilities.txt`, exposes multiple diagnostic levels and can decompose problematic models during cold-start initialization.

However, the pip package bundles platform-specific APMonitor executables and can invoke several solver backends. The MIT root license of the Python repository is not sufficient evidence in this audit to assert uniform commercial redistribution terms for all bundled binaries/solvers.

Therefore:

- keep as strong technical/reference and possible runtime candidate;
- verify exact redistribution/license of APMonitor executable and chosen solvers before product bundling;
- do not assume `pip install` implies all embedded artifacts share the root MIT terms.

---

# 13. Lightweight control / estimation candidates

## python-control

Upstream: `python-control/python-control`  
License: BSD-3-Clause  
Grade: A

Use as a narrow control-system analysis/design layer when a full nonlinear MPC/MHE stack would be excessive. It is suitable for state-space/control primitives and should remain separate from plant/model identity.

## Stone Soup

Upstream: `dstl/Stone-Soup`  
License: MIT  
Grade: B+ for process digital twins, A in its native tracking domain.

Stone Soup is a mature state-estimation/tracking framework but is optimized for target-tracking rather than chemical-process models. It may still provide reusable Kalman/particle/data-association primitives, but NeqSim/Pyomo/do-mpc are closer to process-engineering needs.

---

# 14. Equinor industrial integration ecosystem

## tagreader-python

License: MIT  
Mode: `DIRECT_DEPENDENCY`  
Grade: S-

The inspected client layer abstracts plant historian/data-source access and supports PI Web API and AspenOne/IP.21-oriented data sources. It handles time zones, current snapshots, raw/interpolated series and caching that fetches missing ranges rather than refetching the complete history.

Candidate canonical boundary:

```text
TelemetryBinding
  source_kind: opcua | pi | aspen_ip21 | csv | mqtt | ...
  tag/path
  engineering_units
  timestamp/timezone policy
  quality metadata
  resampling/interpolation policy
  credentials_ref
```

## rvmsharp

Upstream: `equinor/rvmsharp`  
License: MIT  
Mode: `DIRECT_DEPENDENCY`  
Grade: S for AVEVA plant-model import.

RvmSharp is an actively maintained C# library/utility for AVEVA PDMS/E3D `.RVM` files. It can attach sidecar attributes, align/connect RVM stores, tessellate geometry and export/convert models, including OBJ and a CAD Reveal pipeline.

This is the strongest direct path found so far for importing real AVEVA plant geometry into BLUECAD.

Candidate adapter:

```text
AVEVA PDMS/E3D RVM + attribute sidecars
        -> RvmSharp
        -> hierarchical plant geometry + metadata
        -> BLUECAD PlantGeometryAsset
        -> optional mesh/Reveal/VTK projection
```

Do not immediately flatten imported RVM hierarchy to triangles; preserve source node IDs/attributes/transforms for equipment reconciliation with process/P&ID objects.

The repository includes Huldra sample-data references. Sample-dataset licenses must remain separate from code license.

## neqsimExcelCapeOpen

This C# repository is a concrete CAPE-OPEN/Excel interface around NeqSim, containing CAPE-OPEN unit-operation and NeqSim interface projects. No root license was visible in the inspected repository metadata/tree, so use as `REFERENCE_ONLY` until exact rights are resolved.

The permissive NeqSim core plus published CAPE-OPEN specifications remain the preferred implementation basis.

## engineering-symbols

License: MIT in repository metadata.  
Candidate value: ready-made SVG industrial engineering symbols for PFD/P&ID UI. Audit symbol provenance/semantic mapping before promotion.

## NOAKADEXPI

No explicit license was established from GitHub metadata. Treat as `REFERENCE_ONLY` for DEXPI mapping/requirements.

## ERT / iterative_ensemble_smoother

GPL-licensed ensemble assimilation/history-matching software. Retain as external/reference for ensemble methods; prefer permissive components where comparable process-estimation functionality exists.

## ecalc

Root license: LGPL-3.0. The domain tree separates process energy, energy usage, fuel, emissions, installation/asset concepts, regularity/time-series and a wrapper toward NeqSim.

Candidate role: `LINKED_OR_EXTERNAL` energy/emissions backend complementary to process simulation and BioSTEAM/QSDsan economics/sustainability. Further model-level audit is still required before promotion.

---

# 15. Updated digital-twin architecture

The audit now strongly supports this separation:

```text
Engineering Model Asset
   |
   +-- physical/process model
   +-- property-package basis
   +-- geometry/P&ID identity
   |
TelemetryBinding[]
   +-- OPC UA
   +-- PI
   +-- Aspen IP.21
   +-- other source
   |
   v
Raw Observation / Historian
   |
   v
Data Reconciliation
   |
   +-- adjusted values
   +-- covariance
   +-- gross-error findings
   |
   v
Estimator / Calibration
   +-- batch parameter fit
   +-- online EnKF/MHE
   |
   v
Twin State
   |
   +-- uncertainty/confidence
   +-- model/version provenance
   |
   +-- Prediction
   +-- Optimization
   +-- Controller proposal/execution
```

The knowledge graph, LLM view and SFILES projection are **derived views** of this state, not competing authorities.

---

# 16. Immediate next queue

1. audit `equinor/ecalc` calculation contracts and emissions/energy profiles;
2. inspect RvmSharp semantic node/attribute/transform classes and available target formats;
3. audit current process-intelligence public repo set for any additional executable graph/P&ID tool; do not invent code repositories for paper-only work;
4. inspect IDAES/Pyomo diagnostics/parameter-estimation capabilities before writing custom BLUECAD diagnostics;
5. search process-oriented system-identification/state-estimation libraries only where they add capabilities absent from NeqSim/Pyomo/do-mpc;
6. inspect engineering-symbols / DEXPI symbol mapping and P&ID rendering assets;
7. audit industrial/plant-model ecosystems beyond Equinor only when they provide actual import/interop code (AVEVA, DEXPI, FMI, OPC UA, historians);
8. update the canonical intake register with NeqSim, process-document intelligence and industrial-integration families after this continuation is complete.
