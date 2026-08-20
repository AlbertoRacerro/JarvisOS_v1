# BLUECAD model IR and interchange audit — 2026-08-20

Status: discovery/reference only; **not implementation authority**.

## Question

If BLUECAD were built from zero today, should its executable engineering-model layer be:

1. a new proprietary equation/model language;
2. based on a lightweight existing declarative ODE format;
3. based on an existing symbolic multiphysics framework;
4. Modelica-compatible;
5. or a small BLUECAD semantic/provenance IR that compiles to multiple backends?

JarvisOS's current `ModelSpec` is useful engineering governance state but is not yet an executable scientific-model IR. This audit therefore treats existing Jarvis work as one candidate among others and applies zero sunk-cost preference.

---

## IR-REF-01 — GreenLight

Source: `davkat1/GreenLight`  
Origin: Wageningen Research  
License: BSD-3-Clause-Clear  
Evidence: CODE-FIRST  
Reference value: **A+/S for model-definition ergonomics**

### Strong mechanisms

GreenLight represents dynamic ODE models using definitions that carry:

- mathematical expression;
- type/state role;
- unit;
- description;
- literature/reference metadata;
- initial values;
- inputs;
- options.

Its parser extracts variables plus `unit`, `description`, and `reference`, maps dependencies, checks cycles, and computes a solving order.

A particularly strong mechanism for BLUECAD is **ordered composition/override**. Model definitions can be loaded from multiple JSON/dict/file sources; later definitions override earlier ones, while duplicate definitions inside one source are rejected. This naturally supports the desired fidelity workflow:

```text
M0 base model
 + temperature-limitation overlay
 + carbonate-chemistry overlay
 + improved-light overlay
```

where one physical law can replace a simplified assumption without rewriting the rest of the model.

### Important negative evidence

Do not reuse the GreenLight execution mechanism blindly inside an AI-facing engineering platform.

The current default `solving_method` is `solve_ivp_from_str`. It builds Python source code from model-expression strings and executes it with `exec()`. The default runtime options also include `nans_to_zeros=True` and `clip_large_nums=True`, which can keep a simulation running by silently replacing NaNs and clipping extreme values. Those are pragmatic research-simulation choices but conflict with JarvisOS's fail-explicitly/evidence-first philosophy.

For BLUECAD:

- borrow declarative metadata and layered override semantics;
- never execute user/model-generated strings through unrestricted `exec`;
- parse expressions into a typed AST/symbolic graph;
- reject unit errors, unsupported functions, cycles, NaNs and invalid domains deterministically;
- record equation-level provenance.

### Disposition

**Architecture reference, not direct runtime adoption.**

---

## IR-REF-02 — PyBaMM

Source: `pybamm-team/PyBaMM`  
License: BSD-3-Clause  
Evidence: CODE-FIRST  
Reference value: **S for symbolic equation/submodel backend architecture**

### Strong mechanisms

Despite its battery focus, `pybamm.BaseModel` is genuinely generic. Official examples construct arbitrary ODE/PDE models from `Variable`, `Parameter`, `SpatialVariable`, symbolic operators such as `grad` and `div`, then provide:

- differential equations (`rhs`);
- algebraic equations;
- boundary conditions;
- initial conditions;
- output variables;
- geometry;
- parameter processing;
- mesh/discretisation;
- solver selection.

The model can then be converted/discretised and solved using IDAKLU or other backends.

The `BaseModel` implementation also owns:

- submodel dictionaries;
- coupled-variable construction;
- ODE/DAE equations;
- BC/IC/event composition;
- variables grouped by submodel;
- geometry;
- parameterisation/discretisation state;
- serialization;
- conversion to other computational representations.

The build pipeline is deliberate: first collect each submodel's fundamental variables, then iterate coupled variables until dependencies resolve, then ask each submodel to set RHS, algebraic equations, BCs, ICs and events. This is very close to the kind of deterministic composition BLUECAD will eventually need.

PyBaMM also has an unusually useful scientific-provenance mechanism: modules register citations and the runtime can print only the citations implicated by code paths/models actually used.

### Important negative evidence

`BaseSubModel` itself is not cross-domain generic. Its domain validation is battery-specific (`negative`, `separator`, `positive`, etc.). BLUECAD should therefore not inherit the PyBaMM submodel ontology wholesale.

The package is also substantially heavier than current JarvisOS: NumPy, SciPy, xarray, SymPy, pandas, anytree, pybammsolvers and other dependencies are core. It includes optional telemetry through PostHog; users are prompted to opt in and timeout defaults to disabled, and `PYBAMM_DISABLE_TELEMETRY` can force opt-out. Any JarvisOS integration would need telemetry deterministically disabled by policy, not left to an interactive prompt.

### Disposition

Two realistic future routes:

**Route A — PyBaMM as numerical/symbolic backend**

BLUECAD keeps its own domain-neutral semantic model/submodel contracts and compiles suitable ODE/PDE/DAE systems into `pybamm.BaseModel`.

**Route B — architectural adaptation only**

Reuse the build concepts (fundamental variables -> coupled variables -> equations/IC/BC/events) while using another symbolic backend such as CasADi/SymPy.

Do not make battery-specific PyBaMM classes the canonical BLUECAD IR.

---

## IR-REF-03 — Modelica Standard Library

Source: `modelica/ModelicaStandardLibrary`  
License: BSD-3-Clause  
Evidence: CODE/DISTRIBUTION-FIRST  
Reference value: **S as mature multidomain component/equation reference**

### Why it matters

The Modelica Standard Library already spans many domains BLUECAD intends to touch:

- Fluid;
- Media;
- Mechanics;
- Thermal;
- Electrical;
- Magnetic;
- Blocks/control;
- units/constants;
- state graphs.

This is strong evidence that BLUECAD should not casually reinvent acausal connection semantics, replaceable physical components, unit conventions, or generic physical connectors.

The library itself is permissively licensed. The separate question is which compiler/runtime is used to flatten/execute Modelica.

### Disposition

Treat Modelica syntax/semantics and MSL as an interoperability/reference target. Do not assume the full OpenModelica compiler must be embedded.

---

## IR-REF-04 — OpenModelica

Source: `OpenModelica/OpenModelica`  
Evidence: CODE/LICENSE-FIRST  
Reference value: **S as external industrial/academic Modelica compiler**  
Integration disposition: **EXTERNAL / LICENSE-BOUNDARY**

OpenModelica is a mature Modelica compiler/simulation environment, but its OSMC Public License requires a deliberate licensing choice. Non-member redistribution can use AGPL; proprietary source integration under the alternative EPL-derived modes is tied to OSMC membership/conditions. The license explicitly notes that an external party wishing to use OpenModelica source together with proprietary software must be an OSMC member.

Therefore:

- do not copy compiler code into proprietary BLUECAD casually;
- OpenModelica remains useful as an external compiler/oracle/tool;
- Modelica compatibility does **not** require making OpenModelica a linked internal dependency.

---

## IR-REF-05 — PyMoCa

Source: `pymoca/pymoca`  
License: BSD-3-Clause  
Evidence: CODE-FIRST  
Reference value: **A+/S candidate for Modelica-to-symbolic translation**

### Strong mechanisms

PyMoCa is a Python Modelica translator with a real parser/AST/instantiation/flattening architecture. Current core dependencies are only NumPy and ANTLR runtime; CasADi, SymPy and ModelicaXML are optional backends.

Its current pipeline is explicitly separated:

```text
Modelica source
 -> parser AST
 -> instance tree
 -> flattening
 -> flat equations/variables/parameters/constants
 -> CasADi or SymPy backend
```

The new flattening implementation is designed against the Modelica Language Specification and is tested against parts of the Modelica Compliance Suite and Modelica Standard Library. The repository has substantial parser, instantiation, redeclaration, CasADi, SymPy and MSL test suites.

This is potentially a much cleaner proprietary-product boundary than embedding OpenModelica: BLUECAD could parse/flatten a useful Modelica subset with permissively licensed PyMoCa and send the equations to a symbolic/numerical backend.

### Important negative evidence

PyMoCa still declares itself Alpha and its own architecture document records incomplete language features/TODOs, including conditional declarations, some reference validation, transitions and portions of record handling. Its PyPI documentation explicitly warns that error checking is incomplete and breaking API changes are expected; 0.12 release candidates appeared in July 2026.

Therefore it is not yet safe to declare “full Modelica support”.

### Disposition

**Very strong future spike candidate.** Test the exact Modelica subset BLUECAD would need rather than promising language-wide compatibility.

---

## IR-REF-06 — CasADi

Source: `casadi/casadi`  
License: LGPL-3.0  
Evidence: established code/documentation; detailed code audit deferred  
Reference value: **S symbolic/optimization backend**  
Disposition: **BOUNDARY**

CasADi supplies sparse symbolic graphs, automatic differentiation, ODE/DAE integration interfaces, nonlinear optimization and code generation, with Python/C++/MATLAB frontends. It is an obvious candidate downstream of either a BLUECAD-native AST or PyMoCa.

LGPL is commercially usable through a normal library boundary, but changes to CasADi itself remain LGPL.

This is especially attractive because later calibration/optimal-control/MBDoE work benefits from differentiable equations instead of an opaque numerical function.

---

## IR-REF-07 — FMI / FMPy

Source: `CATIA-Systems/FMPy`  
Origin: Dassault Systèmes  
License: BSD-2-Clause for FMPy, with separately identified bundled component licenses  
Evidence: CODE-FIRST  
Reference value: **S for solver/component interoperability**

### Code evidence

FMPy has real implementations for FMI 1, 2 and 3 plus:

- model-description parsing;
- simulation;
- typed continuous/discrete inputs and event handling;
- FMU build utilities;
- remoting;
- container FMUs;
- cross-check infrastructure;
- examples, CLI, GUI and test suites.

The simulation code handles FMI-version-specific types, value references, continuous/discrete inputs, event times, interpolation and output recording rather than acting as a thin file reader.

### BLUECAD value

FMI gives BLUECAD a powerful adapter boundary:

```text
BLUECAD canonical component
    inputs / outputs / parameters / units / events
                  |
                  +--> native Python/C++ adapter
                  +--> FMU via FMPy
                  +--> external CLI/service
                  +--> Modelica/PyMoCa/CasADi backend
```

A solver that already exports an FMU should not necessarily receive a bespoke deep Jarvis integration.

FMU metadata also creates a useful artifact boundary: exact FMU hash/version, model-description manifest, parameters, input schedule and outputs can be recorded in a `SimulationRun` for reproducibility.

### Safety caveat

An FMU contains native executable code. Treating it as a standard format does not make it safe. Third-party FMUs must be handled as untrusted executable artifacts with sandbox/resource/network/filesystem policy just like other external binaries.

---

# Current comparison

| Concern | Current strongest reference | Notes |
| --- | --- | --- |
| Human-readable layered model definitions | GreenLight | excellent override/provenance ergonomics; do not copy `exec` runtime |
| Generic symbolic ODE/PDE/DAE model object | PyBaMM `BaseModel` | mature and tested, but full submodel ontology is battery-specific |
| Mature multidomain component semantics | Modelica / MSL | decades of work; avoid reinventing acausal connectors casually |
| Permissive Modelica parser/flattening path | PyMoCa | promising and active; incomplete language coverage must be tested |
| Sparse differentiation/optimization backend | CasADi | strong boundary candidate, LGPL |
| External simulator/component interchange | FMI + FMPy | BSD FMPy, strong standard boundary |
| Jarvis canonical engineering truth | Jarvis ModelSpec/Assumption/Parameter/Evidence | keep above numerical backends |

# Emerging recommendation

Do **not** choose one of these projects as the entire BLUECAD architecture.

The strongest current direction is a thin proprietary **BLUECAD Semantic Model IR** that owns what none of the numerical packages should own:

```text
ModelDefinition
  identity / domain / maturity
  variables + semantic type + unit
  parameters + bounds + provenance + uncertainty
  equations + assumption IDs + source references
  states / algebraics / inputs / outputs
  events / constraints
  component ports / topology bindings
  submodel slots + replacement compatibility
  validation requirements
  backend capabilities required
```

Then compile/adapt:

```text
BLUECAD Semantic IR
        |
        +--> simple native SciPy/NumPy M0 evaluator
        +--> PyBaMM BaseModel for symbolic ODE/PDE/DAE cases
        +--> PyMoCa/Modelica interoperability
        +--> CasADi for AD/optimization/control
        +--> FMU/FMPy for external components
        +--> domain-specific solvers through adapters
```

This makes the proprietary layer small but strategically valuable: it owns engineering meaning, provenance and fidelity replacement, while existing software owns numerical methods and domain kernels.

# Consequence for BlueRev M0

Do not delay M0 to build this full IR.

For M0, implement the equations in a very small transparent native model behind interfaces that already expose:

- named variables;
- Pint units;
- parameters/source/confidence;
- assumption IDs;
- deterministic input/output schema;
- one model/version identifier.

The M0 contract should be deliberately easy to migrate later into the Semantic IR. The first Model-IR spike should happen only once a second model/fidelity variant proves the abstraction is needed.
