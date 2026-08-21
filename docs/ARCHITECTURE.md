# Architecture

This is the canonical current architecture source for JarvisOS.

`docs/specs/STATUS.md` remains the sole live implementation and queue authority. Historical milestone and strategy documents are evidence of prior decisions; they do not override this file when they describe runtime state that no longer exists.

Last architecture reconciliation: **2026-08-21**.

---

## 1. Product principle

JarvisOS is a local-first engineering workspace. It is not a general numerical solver, not a model provider, and not an autonomous engineering authority.

The intended separation is:

```text
Engineer = final engineering responsibility
JarvisOS = software authority boundary, state, policy, provenance, execution identity
AI / agents = proposals, reasoning, tool intents, explanations
Engineering tools = replaceable numerical/mechanical backends
Evidence = results + provenance + fidelity/qualification context
```

The core invariants are:

1. `AI/agent proposal != canonical state mutation`.
2. `tool output != accepted engineering truth`.
3. capability authority, information-flow/egress authority, and state-commit authority are separate concerns.
4. canonical state changes only through JarvisOS-controlled transitions.
5. the engineer remains responsible for the engineering decision even when a software transition is automated.
6. **sunk cost is zero**: current JarvisOS code receives no architectural preference merely because it already exists.

If a qualified upstream project already solves a generic numerical/runtime problem better than an in-house subsystem, the default disposition is `WRAP_UPSTREAM`, `REPLACE_WITH_UPSTREAM`, or `DELETE`, not indefinite parallel maintenance.

---

## 2. High-level data flow

The intended high-level flow is explicitly bidirectional where information returns:

```text
                         response / proposal
              ┌────────────────────────────────┐
              │                                ↓
Engineer ⇄ JarvisOS authority boundary ⇄ AI / AgentRuntime
              │
              │ authorized execution request
              ↓
      Engineering / software capability
              │
              ↓
     result + artifacts + diagnostics
              │
              ↓
        evidence / run records
              │
              ├────────────→ JarvisOS / Engineer inspection
              │
              └────────────→ explicit commit/promotion decision when applicable
```

A diagram arrow is a data/request flow, not a vague association. JarvisOS policy governs transitions; policy is not itself a data store and does not “produce” canonical state.

---

## 3. Authority boundary

JarvisOS currently distributes authority responsibilities across backend modules rather than implementing one monolithic `AuthorityCore` class. The architectural boundary is still real, but the implementation is composed from services.

JarvisOS owns or is intended to own:

- canonical project and engineering state;
- record lifecycle and promotion semantics;
- workspace and engineering identity;
- units, provenance and freshness;
- AI route, budget and egress policy;
- capability permission and confirmation boundaries;
- run/artifact/evidence identity;
- sensitivity and external-packet lineage;
- evaluator contracts and qualification metadata;
- deterministic state-transition and audit records.

External systems may own replaceable mechanics:

- LLM inference;
- agent/session loops;
- semantic code intelligence;
- derived semantic/temporal retrieval;
- sandbox/isolation implementation;
- property packages;
- process solvers;
- CAD kernels;
- meshers;
- CFD/FEM solvers;
- optimization algorithms;
- telemetry transport.

No external backend should need direct authority over canonical JarvisOS state.

---

## 4. Current write-path debt

The repository has a real proposal/promotion lifecycle through `app/modules/memory`, including AI- and calculation-originated proposals, explicit promote/reject transitions, replacement semantics and freshness invalidation.

However, older `app/modules/modeling` CRUD endpoints still create assumptions, parameters and decisions directly. This means the implementation does **not yet have one fully unified canonical-state write path**.

That is known architecture debt, not an intentional permanent dual authority model.

Target:

```text
user / AI / calculation / import
             ↓
       typed write intent
             ↓
 canonical-state service
 validation · provenance · lifecycle · audit
             ↓
        canonical store
```

Direct user creation may still be allowed to create an accepted record where policy permits. The requirement is one transition service and one set of semantics, not forcing every human entry through an artificial “AI proposal” state.

### Parameter lifecycle versus value quality

Parameters currently contain both lifecycle and value-quality concepts. Those concepts must remain distinct:

```text
record lifecycle:
proposed → accepted / rejected → superseded

value/evidence quality:
candidate / literature / measured / validated / ...
```

The same word `accepted` should not ambiguously mean both “this record is canonical” and “this value has a certain quality classification”. Authoritative AI context must require an accepted lifecycle state plus an explicitly permitted value-quality state.

The post-visual-identity queue contains the correction.

---

## 5. Context, retrieval and memory

Canonical state and retrieval memory are different systems.

```text
Canonical state ─────┐
Runs / evidence ─────┤
External documents ──┤
Derived retrieval ───┤
Code intelligence ───┤
                     ↓
               Context Broker
                     ↓
          bounded ContextPack + manifest
                     ↓
             AI / AgentRuntime
                     ↓
        response / proposal / ToolIntent
```

Current implementation includes deterministic context-pack assembly, source manifests, digests, bounded selection and FTS/LIKE-based record search. The current implementation is not yet a semantic/temporal retrieval system.

Future semantic/temporal indexes are rebuildable and non-authoritative. If an index disagrees with canonical state, canonical state wins.

External notes and documents are sources. MCP may expose resources/capabilities but is not itself the conceptual owner of those documents.

Code intelligence such as Serena and retrieval memory are parallel context/capability sources; one is not inherently downstream of the other.

---

## 6. AI and AgentRuntime model

All provider execution must continue through JarvisOS-owned routing, egress, budget and ledger boundaries.

The future agent/runtime shape is:

```text
JarvisOS policy + context + capability grant
                 ⇅
          AgentRuntime adapter
                 ⇅
       Hermes / another runtime
                 ⇅
        capability interface
          e.g. MCP where useful
                 ⇅
          JarvisOS services
```

The return path is mandatory. Agent output returns to JarvisOS as a response, proposal or tool intent.

There is no valid architecture in which:

```text
Hermes → canonical state
```

without a JarvisOS transition boundary in between.

Hermes, MCP and related slices remain frozen under the current live registry until explicitly re-derived after the current queue and post-visual-identity architecture correction/revalidation.

---

## 7. Engineering evaluator model

The desired engineering architecture is evaluator-based, not “JarvisOS contains all solvers”.

Target contract concept:

```text
EvaluationRequest
  evaluator identity/version
  typed inputs + units
  model/fidelity selection
  validity assumptions
  execution policy
        ↓
EngineeringEvaluator adapter
        ↓
upstream/custom specialist backend
        ↓
EvaluationResult
  outputs
  diagnostics / failure taxonomy
  artifacts
  provenance
  fidelity
  validity domain
  qualification state
  uncertainty where available
```

Current code does not yet implement one universal `EngineeringEvaluator` interface. Several mature bounded paths have typed contracts that should inform the future common boundary.

A common abstraction must not erase solver-specific semantics or pretend incompatible analyses are interchangeable.

---

## 8. Evidence model

Current typed `evidence_records` are strongest for BLUECAD validation, mesh quality and static FEM.

That is a real evidence foundation but not yet a universal engineering evidence layer.

The target common evidence envelope should be able to represent, where relevant:

- exact producer/evaluator and version;
- exact run and input digest;
- result/artifact digest;
- engineering quantity and units;
- model fidelity;
- qualification state;
- validity domain;
- known exclusions;
- uncertainty/sensitivity information;
- provenance/source references;
- pass/fail/indeterminate or richer typed outcome;
- freshness/staleness.

**Provenance is necessary but not sufficient for scientific validity.** A deterministic, fully traceable result can still be wrong or be used outside its validity domain.

---

## 9. Current physical-design path

A real production-shaped path already exists:

```text
operator / Jarvis proposal
        ↓
BLUECAD candidate + GeometrySpec
        ↓
build123d / OCP
        ↓
STEP / STL / GLB + manifest / digests
        ↓
registry-bound Gmsh
        ↓
mesh + groups + quality outcome
        ↓
registry-bound CalculiX
        ↓
static FEM result + verification report
        ↓
SimulationRun + artifacts + typed evidence
        ↓
FastAPI aggregate/read APIs
        ↓
BLUECAD / Runs / Analytics UI
```

When the bounded structural-repair mode is enabled, there is also a real feedback path:

```text
criteria failure
      ↓
selected evidence
      ↓
AI repair proposal
      ↓
new GeometrySpec
      ↓
rebuild → remesh → resolve → compare
```

The AI repair proposal still does not own final project truth.

### Current CAD scope

`GeometrySpec` is a bounded semantic CAD vocabulary, not a generic CAD replacement. Current part kinds include tube runs, bends, joints, manifolds/capped manifolds, floats, anchor mounts and harvest modules.

The implemented green capability is deterministic parametric CAD construction/export and current semantic scene binding. Broader physical synthesis such as maintainability, access, cleanability and manufacturability is future engineering logic unless a specific implemented check proves otherwise.

### Gmsh and CalculiX

The adapters are implemented. Exact executable/host provenance and scientific qualification are separate gates.

The current Gmsh path includes bounded physical-group construction and retry behavior; it is not a claim of robust arbitrary industrial meshing.

The current CalculiX path is static FEM, not a general multiphysics suite.

---

## 10. Current process-engineering reality

The repository currently contains several useful deterministic BlueRev experiments:

- geometry/hydraulics/pumping screening;
- biomass/nutrient/harvest bookkeeping and bounded economic proxies;
- buoyancy and optical-transmission proxies;
- explicit topology experiments;
- a typed acyclic process kernel.

These results should remain inspectable historical/verification assets until the upstream replacement decision is complete.

They do **not** collectively form an integrated predictive photobioreactor simulator.

### Specific limits that must remain public

The current biomass/nutrient/harvest model takes volumetric productivity as an input. It therefore does not yet predict productivity from coupled light, biology, gas transfer, nutrients, temperature and hydrodynamics.

The current optical model is a Beer-Lambert-like screening proxy. It does not implement a full radiation field, spectral PAR, scattering or light-growth coupling.

The example batch-growth model is a simple deterministic runner demonstration, not a qualified PBR biology model.

### Custom `process_kernel`

The current process kernel validates a directed acyclic graph and executes blocks in topological order. That makes it useful as a bounded feed-forward calculation experiment.

It is **not** the target general PBR solver because real process models may require:

- recycle/algebraic loops;
- nonlinear simultaneous equations;
- ODE integration;
- DAE integration;
- controller/state coupling;
- dynamic gas/liquid/biological inventories;
- nonlinear optimization.

No new generic solver functionality should be added to `app/modules/process_kernel` before the zero-sunk-cost upstream bake-off.

The target is to evaluate IDAES/Pyomo, BioSTEAM/QSDsan, CasADi/OpenMDAO, DWSIM/CAPE-OPEN, CoolProp/thermo/chemicals/fluids and other relevant upstreams against the actual PBR requirements. Generic JarvisOS code duplicated by a stronger selected upstream should then be retired/deleted. Domain-specific equations, fixtures or adapters are retained only when they remain the stronger boundary.

---

## 11. Lineage graph is not a process flowsheet

`app/modules/flowsheet` currently models dependency/provenance/freshness relationships between records such as model specs, runs, artifacts, assumptions, parameters, decisions, AI jobs, BLUECAD attempts and evidence.

That is useful, but the name collides with the engineering meaning of “process flowsheet”.

Future cleanup should rename that boundary toward `lineage`, `dependency_graph` or `provenance_graph` while preserving compatibility as needed.

`app/modules/process_kernel/flowsheet.py` is the separate process-topology concept.

---

## 12. Obsolete engineering placeholder module

`app/modules/engineering` predates much of the current domain implementation and still contains placeholder-era concepts while real engineering behavior now lives in modeling, memory, runner, process, BLUECAD and lineage modules.

It should not be preserved for historical reasons. Post-visual-identity cleanup will either:

- delete it if it has no current consumers; or
- replace it with a deliberately designed common engineering contract only if that abstraction is required by the evaluator architecture.

A directory name is not a reason to keep an abstraction.

---

## 13. Photobioreactor architecture

The PBR workflow is an iterative design study, not a one-way process-to-CAD pipeline.

### Outer loop: engineer and Jarvis

Jarvis belongs in the outer decision/interpretation loop:

```text
Engineer ⇄ Jarvis
 goals · constraints · model choice · interpretation · intervention
```

### Inner loop: reproducible study controller

The numerical inner loop should be deterministic/reproducible:

```text
DesignStudy
  variables + bounds
  objectives
  constraints
  evaluator/fidelity policy
        ↓
StudyController
        ⇅
DOE / optimizer / search
        ⇅
EngineeringEvaluator(s)
        ⇅
EvaluationResult + failure/evidence
        ↓
Study store / Pareto / feasibility state
```

The optimizer receives evaluation results directly. An LLM should not need to choose the next point for every candidate evaluation.

### Failure taxonomy

At minimum the study layer must distinguish:

- invalid design / constraint violation;
- invalid geometry;
- solver/numerical failure;
- execution/infrastructure failure;
- successful but infeasible result;
- feasible result;
- dominated design;
- qualified/verified result where an explicit qualification rule applies.

A failed solver is not equivalent to an infeasible physical design.

### Multi-fidelity evaluation

The cheapest adequate evaluator should be used first.

```text
analytical / correlation / reduced-order
              ↓ when unresolved
higher-fidelity deterministic model
              ↓ when unresolved
CFD / specialist high-fidelity backend
```

CFD is therefore not inherently “after CAD”. It can enter the study as a selected high-fidelity evaluator when mixing, shear, gas transfer, baffle behavior or another field quantity changes the process-design decision.

---

## 14. Process geometry versus detailed CAD

Process design can contain geometric variables before a detailed CAD object exists.

Examples:

- tube diameter;
- total active length;
- loop/path count;
- topology choice;
- target flow and velocity;
- gas-injection arrangement at an abstract level;
- footprint/envelope constraints.

Target handoff:

```text
ProcessDesignEnvelope
  process-driving dimensions
  flows / operating ranges
  pressure/shear/transfer constraints
  energy constraints
  qualification/uncertainty
        ↓
DetailedGeometrySpec / physical synthesis
        ↓
CAD artifacts
        ↓
structural / CFD / manufacturing checks as required
        ↓
feedback to DesignStudy when physical checks invalidate assumptions
```

The CAD layer should realize a process design, not silently become the authority that chooses process physics.

---

## 15. Storage and persistence

The FastAPI backend is the durable application boundary.

Current durable state is SQLite-backed. The frontend must use backend APIs and must not directly call providers, local model runtimes, filesystem paths or engineering executables.

Runtime data and repository source remain separate. Current deployment remains Windows-first and local-first.

Events are audit/history records. JarvisOS does not currently claim to be fully event-sourced.

---

## 16. Runner and execution safety

The bounded Python runner is suitable for reviewed deterministic scripts under its current policy. It is not a hostile-code sandbox.

Host-process restrictions, AST checks, bounded working directories, output limits and secret stripping do not create a strong OS isolation boundary.

If future Hermes/MCP/remote-agent behavior can reach executable tools, a fresh sandbox/isolation design and qualification is mandatory before general untrusted code execution is exposed.

---

## 17. Documentation authority

Documentation precedence:

1. current source code + deterministic tests for what is actually implemented;
2. `docs/specs/STATUS.md` for live queue/state authority;
3. this file for canonical architecture and known debt;
4. current full specs/readiness decisions for authorized slice boundaries;
5. strategy/audit documents for planning evidence;
6. historical milestone documents for history only.

A README or old strategy statement must not override current source/tests when claiming implementation status.

---

## 18. Post-visual-identity architecture correction

The current functional beta queue remains ahead of the architecture-remediation implementation work. The architecture reconciliation itself is documentation-only and can be merged without opening a second runtime front.

After the current functional queue and global visual identity, the intended correction sequence is:

```text
1. unify canonical-state write semantics and Parameter lifecycle/value-quality semantics
2. generalize engineering evaluator/evidence contracts
3. perform zero-sunk-cost process upstream bake-off
4. replace/delete duplicated custom generic process-solver infrastructure
5. remove dead placeholder engineering code and resolve flowsheet/lineage naming
6. implement the selected PBR evaluator architecture
7. add deterministic StudyController / DOE / optimization inner loop
8. add explicit ProcessDesignEnvelope → detailed CAD handoff
9. add multi-fidelity escalation/qualification driven by real PBR decisions
```

The exact rows and authorization state live only in `docs/specs/STATUS.md`.

See `docs/strategy/JARVISOS_ARCHITECTURE_RECONCILIATION_2026-08-21.md` for the audit rationale and zero-sunk-cost disposition rules.
