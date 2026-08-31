<h1 align="center">JarvisOS</h1>

<h3 align="center">A personal, local-first AI engineering workspace</h3>

<p align="center"><strong>Can AI help assemble a serious engineering workspace without becoming the source of engineering truth?</strong></p>

<p align="center"><code>local-first</code> · <code>evidence-first</code> · <code>upstream-first</code> · <code>source-available</code></p>

<p align="center"><a href="#what-is-jarvisos">What it is</a> · <a href="#how-it-works">How it works</a> · <a href="#what-works-today">What works</a> · <a href="#engineering-backends">Engineering backends</a> · <a href="#microalgae-photobioreactor-project">PBR project</a> · <a href="#roadmap">Roadmap</a> · <a href="#technical-details">Technical details</a> · <a href="#licensing-and-collaboration">License</a></p>

> **Short version:** JarvisOS connects AI, project knowledge, engineering records, numerical tools, CAD/CAE, runs and evidence in one controlled workspace. AI can reason, propose and use authorized capabilities; canonical engineering state changes only through explicit JarvisOS-owned transitions.

> **License note:** this repository is publicly source-available for inspection and evaluation, but JarvisOS is **not currently distributed under an open-source software license**. See [Licensing and collaboration](#licensing-and-collaboration).

This README is the public front door. The exact live implementation queue is [`docs/specs/STATUS.md`](docs/specs/STATUS.md); the canonical architecture is [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

# What is JarvisOS?

JarvisOS is a personal engineering workspace built around a strict separation of responsibilities:

```text
Engineer      = final engineering responsibility
JarvisOS      = software authority boundary, state, policy, provenance and execution identity
AI / agents   = reasoning, proposals, explanations and tool intents
Tools         = replaceable engineering or software backends
Evidence      = results + provenance + fidelity / qualification context
```

The core rule is simple:

> **AI output is not canonical state, and tool output is not automatically accepted engineering truth.**

The goal is not to build one giant model that “does engineering”. The goal is a controlled workstation where an engineer can describe a task, assemble bounded context, ask AI for help, execute deterministic or specialist tools, inspect exact outputs and evidence, and deliberately promote only the information that should become authoritative.

JarvisOS is deliberately **upstream-first**. If a qualified external project already solves a generic numerical or infrastructure problem better, the default is to integrate, wrap or replace rather than preserve weaker in-house code because it already exists.

---

# Why build it?

Engineering work is often fragmented across modeling software, numerical tools, CAD/CAE, spreadsheets, documents, project notes and increasingly cloud AI systems. JarvisOS is an experiment in making those boundaries easier to cross without hiding them.

| Keep control | Reuse strong tools | Verify results |
| --- | --- | --- |
| Prefer local execution when practical and explicitly control external egress. | Give existing code zero sunk-cost privilege when a stronger upstream exists. | Keep runs, inputs, artifacts, provenance, model limits and acceptance criteria inspectable. |

“Local-first” is not an anti-commercial rule. If a real engineering problem needs Aspen HYSYS, ANSYS, Fusion, STAR-CCM+ or another specialist package, the long-term architecture should allow that package to sit behind a controlled adapter without becoming the owner of JarvisOS state.

---

# How it works

![JarvisOS high-level architecture](docs/assets/readme/architecture-overview.svg)

The governing boundary is:

> **The engineer owns the engineering decision. JarvisOS owns software-side commit authority. AI and agents propose. Policy authorizes capabilities and egress. Tools execute. Results and evidence return.**

## AI, policy and state

![JarvisOS AI authority flow](docs/assets/readme/ai-authority.svg)

Provider calls, local runtimes and future agent runtimes remain below JarvisOS-owned routing, policy, credential, budget and egress controls. A response can become a proposal or tool intent; it cannot silently become project truth.

## Project knowledge, context and memory

![JarvisOS control and memory layers](docs/assets/readme/memory-control.svg)

JarvisOS deliberately separates:

- **canonical project and engineering state** — accepted Project Basis facts, requirements, parameters, assumptions, decisions and typed records;
- **working revisions / change sets** — explicit bounded edits before reconciliation into canonical owners;
- **runs, artifacts and evidence** — exact execution identity, inputs, outputs, manifests, diagnostics, provenance and qualification context;
- **derived retrieval** — rebuildable search/index layers that never outrank canonical state;
- **external documents and notes** — source material, not automatic truth;
- **context assembly** — bounded, inspectable context passed to AI or agent runtimes.

The repository already has deterministic context assembly, exact references, provenance manifests and Project Knowledge foundations. Future retrieval layers remain derived and non-authoritative.

## Canonical write authority

Project Basis changes now have an explicit backend-owned change-set / working-revision / reconciliation path over existing engineering-record ownership.

One architecture debt remains intentionally visible: some legacy modeling mutation surfaces still predate that canonical owner boundary. Those paths must either delegate to accepted owner/CAS/reconciliation semantics or explicitly reject caller-supplied authority. JarvisOS is not intended to keep a permanent second write authority for compatibility.

---

# What works today?

JarvisOS is still under active development, but the repository is well beyond a UI mockup.

| Capability | Current maturity | Meaning |
| --- | --- | --- |
| Operator workstation + shared visual identity | **Working / evolving** | The main application shell, operator surfaces, contextual sidecars and current visual system are integrated; product behavior still evolves behind explicit authority boundaries. |
| Project Knowledge / Project Basis | **Working foundation** | Canonical Project Basis change sets, working revisions, impact/revalidation and reconciliation exist over current engineering-record owners. |
| Engineering records, lifecycle, provenance and freshness | **Working** | Backend-owned durable records, lifecycle/CAS behavior, lineage and stale propagation exist. Some legacy modeling mutation entry points still require canonical-path closure. |
| Jarvis context and action contracts | **Working foundation** | Stable exact context references and generic capability/action contracts exist without giving Jarvis domain commit authority. |
| AI routing, budget, egress and provider policy | **Working** | Local-first routing and explicit external-provider controls share server-owned policy and accounting boundaries. |
| Architecture-enforcement CI | **Working** | Deterministic checks guard against new raw-SQLite, provider and domain side-channel ownership and track accepted architectural debt explicitly. |
| Bounded deterministic runner | **Working** | Reviewed deterministic models can execute with persisted runs and artifacts. It is **not** a hostile-code sandbox. |
| Semantic parametric CAD | **Working** | `GeometrySpec` plus deterministic build123d/OCP construction and stable artifacts exist for the bounded vocabulary. |
| STEP / STL / GLB export | **Working** | Geometry artifacts, manifests and digests are generated within the supported path. |
| Gmsh meshing | **Implemented; qualification separate** | Registry-bound adapter and evidence path exist; host/executable/scientific qualification remains use-case-specific. |
| CalculiX static FEM | **Implemented; qualification separate** | Deterministic deck/result handling and verification foundations exist; this is not a claim of general multiphysics coverage. |
| CAD → mesh → FEM → evidence → UI | **Implemented, opt-in** | A real physical-design path exists, including bounded evidence-guided repair. |
| Process / PBR screening experiments | **Working experiments** | Hydraulics, biomass/nutrient bookkeeping, harvesting, buoyancy, optical proxies and an acyclic process-kernel experiment exist. They are not an integrated predictive PBR simulator. |
| Common engineering-evaluator / evidence architecture | **Partial foundation** | Existing typed CAD/mesh/FEM/run evidence informs the future common evaluator and qualification boundary. |
| Hermes / MCP-style AgentRuntime layer | **Not a current runtime dependency** | Any future integration must be freshly qualified below JarvisOS-owned context, policy, credentials, egress, budget and commit authority. |

The exact implementation state is intentionally **not duplicated here**. See [`docs/specs/STATUS.md`](docs/specs/STATUS.md).

### One implemented physical-design path

![Current CAD-to-FEM engineering chain](docs/assets/readme/current-engineering-chain.svg)

This is one production-shaped path in the repository, not a claim that every engineering workflow starts from CAD.

---

# Engineering backends

JarvisOS should own evaluator identity, typed inputs, units, run/evidence identity and acceptance boundaries while numerical kernels remain replaceable.

![JarvisOS engineering backends](docs/assets/readme/engineering-backends.svg)

The target pattern is:

```text
EvaluationRequest
      ↓
EngineeringEvaluator adapter
      ↓
upstream / custom specialist backend
      ↓
EvaluationResult
outputs · failure state · artifacts · provenance · fidelity · qualification
```

There is intentionally no claim that every current backend implements one universal interface yet. A common contract must preserve solver-specific semantics rather than flatten incompatible analyses.

## Current and candidate ecosystems

| Area | Current relationship / candidates |
| --- | --- |
| Parametric CAD | **build123d + OCP / OpenCascade** are current dependencies. |
| Meshing | **Gmsh** has a current registry-bound adapter. |
| Static FEM | **CalculiX** has a current registry-bound adapter. |
| Properties / transport | CoolProp, thermo, chemicals and fluids are upstream candidates/building blocks. |
| Bio/process simulation | BioSTEAM, QSDsan, IDAES, Pyomo, WaterTAP and DWSIM/CAPE-OPEN are important upstream candidates/references. |
| Optimization / multidisciplinary studies | CasADi and OpenMDAO are candidates for later deterministic study-control work. |
| Higher-fidelity CFD | OpenFOAM is a candidate evaluator when a real decision cannot be resolved by cheaper models. |
| Agent runtime / capability interfaces | Hermes and MCP-style interfaces are candidates only; neither owns JarvisOS state. |
| Derived retrieval / code intelligence | Graph/semantic memory systems and language-server/code-intelligence tools may become rebuildable context sources, never canonical owners. |

The fuller candidate audit is in [`docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`](docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md).

---

# Microalgae photobioreactor project

One of the first real engineering problems targeted by JarvisOS is a **microalgae photobioreactor design study**.

The important question is not simply “how do I draw the reactor?”. It is:

> **Given the biology, light, mixing, gas transfer, shear, pressure drop and energy demand, which operating conditions and reactor dimensions actually make sense?**

![Microalgae photobioreactor design loop](docs/assets/readme/photobioreactor-process-loop.svg)

The integrated predictive model does **not** exist end to end yet. Current process code is a set of bounded screening experiments and an acyclic custom kernel, not a general recycle/dynamic PBR simulator.

## Jarvis belongs in the outer loop

A numerical optimizer should not require an LLM decision between every candidate.

```text
Engineer ⇄ Jarvis
 goals · constraints · interpretation · intervention
                    ⇅
             typed DesignStudy
                    ⇅
             StudyController
                    ⇅
          DOE / optimizer / search
                    ⇅
       EngineeringEvaluator(s)
                    ⇅
 EvaluationResult + evidence + failure state
```

The optimizer receives deterministic evaluation results directly. Jarvis helps define goals, interpret evidence and intervene at explicit boundaries rather than spending model calls inside the tight numerical loop.

## Process design before detailed CAD

Tube diameter, length, loop count and similar quantities may be geometric variables before a detailed CAD object exists.

```text
process variables + operating variables
        ↓
ProcessDesignEnvelope
        ↓
selected feasible design
        ↓
DetailedGeometrySpec / CAD realization
        ↓
mesh / CFD / FEM / manufacturability when required
        ↓
feedback to the study if physical verification invalidates an assumption
```

CFD is a fidelity choice, not merely the “last step after CAD”. It may become an evaluator inside the study when a lower-cost model cannot resolve the decision.

---

# Roadmap

The public roadmap is intentionally architectural rather than a duplicate of the live spec queue.

```text
CURRENT OPERATOR + PROJECT-KNOWLEDGE FOUNDATION
        ↓
CANONICAL AUTHORITY CONVERGENCE
close legacy write/side-channel debt · preserve one owner per state transition
        ↓
KNOWLEDGE / DEVELOPMENT / CODING TRUTH SURFACES
exact project knowledge · repository/runtime truth · explicit proposal/review state
        ↓
ENGINEERING EVIDENCE CONTRACT
common fidelity · validity · qualification · uncertainty semantics where justified
        ↓
PROCESS UPSTREAM REVALIDATION
zero-sunk-cost bake-off · keep / wrap / replace / delete
        ↓
COMMON ENGINEERING EVALUATOR BOUNDARY
replaceable process / CAD / CAE / CFD / commercial adapters
        ↓
INTEGRATED PBR EVALUATOR
biology · light · mixing/shear · gas transfer · control · hydraulics · energy
        ↓
DESIGN STUDY CONTROLLER
DOE · optimization · feasibility · failure taxonomy · Pareto / uncertainty
        ↓
PROCESS-DESIGN → CAD HANDOFF
        ↓
MULTI-FIDELITY PHYSICAL VERIFICATION
mesh · CFD · FEM · manufacturability when the decision requires them
        ↓
REAL MICROALGAE CASES + DOMAIN QUALIFICATION
```

The principle remains:

> **Use what already works, make authority explicit, remove duplicated infrastructure, qualify the engineering boundary, and solve a real problem.**

For exact dependencies, readiness and implementation state, use [`docs/specs/STATUS.md`](docs/specs/STATUS.md).

---

# Technical details

## Current application stack

### Backend

- **Python**
- **FastAPI**
- **Pydantic**
- **Pint** for units
- **SQLite**-backed durable application state
- **httpx** and explicit provider/runtime adapters
- **PyYAML** for bounded configuration surfaces

Pinned dependencies: [`backend/requirements.txt`](backend/requirements.txt).

### Frontend

- **React 18**
- **TypeScript**
- **Vite**
- **Three.js** for 3D engineering inspection

Pinned dependencies: [`frontend/package.json`](frontend/package.json).

### Current engineering stack

- **build123d / OCP / OpenCascade** for deterministic B-Rep geometry;
- **Gmsh** through a registry-bound external-tool adapter;
- **CalculiX** through a registry-bound static-FEM adapter;
- bounded process/PBR screening calculations and runner experiments;
- typed simulation runs, artifacts, manifests, digests and engineering evidence.

An adapter being implemented is not the same as a solver being scientifically qualified for every use case.

## Architectural ownership

JarvisOS owns or is intended to own:

- canonical project and engineering state;
- lifecycle, change-set and reconciliation semantics;
- engineering identity, units, provenance and freshness;
- AI route, budget, credential and egress policy;
- capability grants and software-side commit boundaries;
- run/artifact/evidence identity;
- evaluator contracts that keep numerical backends replaceable.

External systems may own replaceable mechanics such as inference, agent loops, retrieval indexes, CAD/mesh/CFD/FEM kernels, process solvers, optimizers, sandbox implementations and telemetry transport.

> **JarvisOS should own engineering intent, controlled state transitions and evidence identity; numerical kernels receive no sunk-cost privilege.**

## Memory, context and evidence

| Layer | Authority |
| --- | --- |
| Canonical Project Basis / engineering records | **Authoritative after accepted JarvisOS-owned transition** |
| Working revisions / change sets | **Non-canonical until reconciled** |
| Runs / artifacts | **Execution record** |
| Typed engineering evidence | **Evidence scoped by fidelity, validity and qualification** |
| Derived search / semantic retrieval | **Non-authoritative and rebuildable** |
| External notes / documents | **Source material** |

## Current physical-design chain

```text
operator / Jarvis proposal
        ↓
CAD candidate + GeometrySpec
        ↓
build123d / OCP
        ├── STEP / STL / GLB + manifests / digests
        ↓
registry-bound Gmsh
        ├── mesh + physical groups + quality evidence
        ↓
registry-bound CalculiX
        ├── solver outputs + parsed result summary
        ↓
SimulationRun + artifacts + typed evidence + acceptance criteria
        ↓
FastAPI read models → operator UI
```

When bounded repair is enabled, failed criteria may produce an evidence-grounded repair proposal and a new candidate. The proposal still does not own final engineering truth.

## Current process-model reality

The current process stack should be read as a set of useful experiments, not as a finished simulator:

- productivity is still an input in the biomass/nutrient/harvest screening path rather than an emergent result of coupled biology/light/transport;
- the optical path is a bounded transmission proxy, not a complete radiation/photosynthesis model;
- the custom `process_kernel` executes acyclic typed block graphs and is not a general recycle, nonlinear-equation, ODE or DAE solver;
- the historical dependency/provenance module named `flowsheet` is conceptually lineage, not a process flowsheet.

Generic process-solver expansion should follow a fresh upstream comparison, not extend the current kernel by inertia.

## Engineering qualification philosophy

A numerical tool is not accepted because it is popular, open source or produces a plausible plot.

For a real engineering decision, qualification may compare selected evaluators against analytical solutions, trusted correlations, literature or experimental data, independent numerical implementations and commercial engineering software when that comparison is meaningful.

> **For the decisions I need to make, are the selected evaluators accurate, robust, reproducible, appropriately qualified and traceable enough to be useful?**

Provenance is necessary, but provenance alone does not make a model scientifically valid.

## Repository map

```text
backend/    FastAPI application, state/policy services, AI/runtime logic, engineering adapters and tests
frontend/   React + Vite + TypeScript operator application
scripts/    startup, local probes, CI/evaluation helpers
schemas/    design-time schemas
reports/    bounded generated evaluation/smoke reports
docs/       architecture, specs, strategy, audits, evidence and historical design records
```

Important documentation entry points:

- [`docs/specs/STATUS.md`](docs/specs/STATUS.md) — **sole live implementation/queue authority**;
- [`AGENTS.md`](AGENTS.md) — hard repository invariants for coding agents;
- [`docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`](docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md) — exact-head delivery and automation rules;
- [`docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`](docs/POST_112_PARALLEL_DELIVERY_PROFILE.md) — controlled parallel delivery after the Project Knowledge Core milestone;
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — canonical architecture and known debt;
- [`docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`](docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md) — candidate/upstream audit register.

## Running the development build

JarvisOS is currently Windows-first.

One-click local start:

```text
Start-JarvisOS.cmd
```

Separate launchers:

```text
Start-JarvisOS-Backend.cmd
Start-JarvisOS-Frontend.cmd
```

PowerShell launchers:

```powershell
.\scripts\init-database.ps1
.\scripts\start-backend.ps1
.\scripts\start-frontend.ps1
```

Default local endpoints:

```text
frontend: http://localhost:5173
backend:  http://localhost:8000
```

Representative local checks:

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check app tests

cd ..\frontend
npm run build
```

---

# Licensing and collaboration

Copyright © 2026 Alberto Racerro. All rights reserved.

This repository is publicly available for inspection and evaluation, but **no software license is currently granted for JarvisOS itself**.

Except for the limited rights provided by GitHub's Terms of Service for use through GitHub's functionality, no permission is granted to use, copy, modify, distribute, sublicense, sell, commercialize or create derivative products from this codebase unless separately agreed in writing.

Public source availability must therefore **not** be interpreted as an open-source license or a waiver of copyright.

Third-party packages, tools, reference projects and external software retain their own licenses and copyright.

## Collaboration

I am especially interested in criticism or collaboration around:

- photobioreactors, microalgae and biochemical/process systems engineering;
- process modeling, transport phenomena, hydrodynamics and mass transfer;
- scientific Python and numerical methods;
- CAD/CAE, meshing, CFD/FEM and engineering interoperability;
- local AI runtimes, agent infrastructure, sandboxing and tool protocols;
- engineering validation, provenance and reproducible computational workflows.

A useful contribution is often **not more code**. Sometimes the best contribution is pointing to an existing project that already solves a problem better than something JarvisOS was about to build.

If you want to discuss the project, suggest an upstream, contribute substantially, explore research collaboration or talk about licensing, contact me through GitHub.

---

## Final note

This README is intentionally descriptive rather than authoritative about the live queue. The project should be judged by the code, tests, exact evidence and real engineering decisions it can support — not by how polished the README sounds.
