<h1 align="center">JarvisOS</h1>

<h3 align="center">A personal, local-first AI engineering workspace</h3>

<p align="center"><strong>Can a chemical engineering student with almost no traditional software background use AI to build a genuinely useful engineering environment?</strong></p>

<p align="center">That is the experiment.</p>

<p align="center"><code>local-first</code> · <code>evidence-first</code> · <code>tool-independent</code> · <code>source-available</code></p>

<p align="center"><a href="#what-is-jarvisos">What it is</a> · <a href="#why-im-building-it">Why</a> · <a href="#how-jarvisos-is-supposed-to-work">How it works</a> · <a href="#what-works-today">What works</a> · <a href="#building-blocks-i-plan-to-use">Building blocks</a> · <a href="#microalgae-photobioreactor-project">Photobioreactor project</a> · <a href="#roadmap">Roadmap</a> · <a href="#technical-details">Technical details</a> · <a href="#licensing-and-collaboration">License & collaboration</a></p>

> **Short version:** JarvisOS is my attempt to connect AI, engineering models, numerical tools, CAD, project memory and evidence in one controlled workspace. I am not trying to rebuild Fusion, Aspen HYSYS, ANSYS or every professional tool from scratch. I want JarvisOS to help me use the strongest tool available for each problem while keeping control of the workflow, the data and what gets accepted as engineering truth.

> **License note:** the repository is publicly source-available for inspection and evaluation, but JarvisOS is **not currently distributed under an open-source software license**. See [Licensing and collaboration](#licensing-and-collaboration).

This README is the public front door to the project. The exact live implementation queue remains [`docs/specs/STATUS.md`](docs/specs/STATUS.md).

---

# What is JarvisOS?

JarvisOS is a personal engineering workspace built around one idea: **AI should help me reason, connect tools and move work forward, but it should not silently become the source of truth.**

I want to be able to describe an engineering goal in natural language, let Jarvis assemble the right context and tools, run deterministic calculations or external solvers, inspect what happened, and keep a traceable record of the result.

That can mean very different things depending on the problem: calling a process model, generating parametric geometry, running a mesh or FEM solver, searching project knowledge, comparing alternatives, or eventually coordinating a larger design study.

The long-term goal is not one giant model that "does engineering". It is a **controlled layer that can orchestrate many models and tools without giving any one of them ownership of the project.**

---

# Why I'm building it

I started from a fairly simple frustration.

Engineering software is powerful, but it is often expensive, fragmented across many tools and increasingly tied to cloud services. At the same time, AI is getting good enough to help people cross software boundaries that would previously have required much deeper programming experience.

So I wanted to test a question:

> **What happens if the engineer keeps the domain knowledge and final responsibility, while AI helps connect the software?**

I am a chemical engineering student. I did not start JarvisOS with a software-engineering background, and I do not know in advance how valuable the result will be. That uncertainty is part of the experiment.

If it becomes genuinely useful, that says something interesting about the leverage AI can give to people with domain expertise but limited coding experience. If it does not, the code, tests and engineering comparisons should make that visible rather than hiding it behind a polished demo.

### The idea in three lines

| Keep control | Reuse good tools | Verify the result |
| --- | --- | --- |
| Prefer local execution when practical and gate what is allowed to leave the machine. | Do not rebuild a solver just because it is interesting. Wrap or call the strongest suitable tool instead. | An AI answer is not engineering evidence. Calculations, runs, artifacts and acceptance criteria should be inspectable. |

I also do **not** want “local-first” to become an anti-commercial ideology. If a real problem needs HYSYS, ANSYS, Fusion, STAR-CCM+ or another specialist package, JarvisOS should eventually be able to use that package as a backend without making the whole workflow depend on it.

---

# How JarvisOS is supposed to work

At the center is a small authority layer owned by JarvisOS. Around it sit replaceable AI runtimes, memory systems, code-intelligence tools and engineering backends.

![JarvisOS high-level architecture](docs/assets/readme/architecture-overview.svg)

**Status colors used in the diagrams:** green = implemented · yellow = implemented but partial / qualification still needed · blue = planned target · red = research / demand-gated · gray = optional or replaceable external component.

The core rule is simple:

> **AI proposes. Deterministic policy authorizes. Tools execute. Evidence comes back. Jarvis decides what becomes canonical state.**

That means a model can be useful without becoming the authority. An agent runtime can coordinate work without owning project truth. A solver can produce evidence without being allowed to rewrite the project by itself.

### Control and memory

I do not want JarvisOS to have one vague “AI memory”. Different kinds of information need different authority.

![JarvisOS control and memory layers](docs/assets/readme/memory-control.svg)

The intended split is:

- **canonical project/engineering state** — accepted facts, parameters, decisions and typed engineering records;
- **runs, artifacts and evidence** — exact inputs, outputs, provenance, diagnostics and acceptance criteria;
- **derived retrieval memory** — a rebuildable semantic/temporal layer for finding useful context;
- **external notes and documents** — useful source material that does not silently become canonical truth.

Hermes fits **below** Jarvis authority as a candidate AgentRuntime/tool-orchestration layer. MCP is a candidate capability boundary between runtimes and tools. Semantic code-intelligence systems such as Serena can sit alongside that runtime layer. None of them need to own canonical engineering state.

### Engineering backends

The same idea applies to engineering software: JarvisOS should own the semantic intent, the run/evidence identity and the acceptance boundary, while the numerical kernels remain replaceable.

![JarvisOS engineering backends](docs/assets/readme/engineering-backends.svg)

For one task the best backend may be open and local. For another it may be a custom Python model. For another it may eventually be a commercial specialist tool. The architecture should make that a backend choice rather than a rewrite of the whole workspace.

---

# What works today?

The current repository already contains more than a UI mockup, but it is still a beta under construction.

| Capability | Current maturity | What that means |
| --- | --- | --- |
| Jarvis canonical state, provenance and evidence | **Working** | Durable backend-owned project/engineering records and evidence relationships exist. |
| AI routing, budget, egress and policy controls | **Working** | Local-first routes exist; external AI is explicit and gated. |
| Frontend + backend workbench surfaces | **Working / evolving** | The application is connected end to end, but the functional beta is still being completed. |
| Bounded deterministic runner | **Working** | Reviewed deterministic models can execute with persisted runs and evidence. |
| Semantic parametric CAD layer | **Working** | `GeometrySpec` + deterministic build123d/OCP construction and stable geometry artifacts exist. |
| STEP / STL / GLB export | **Working** | Current geometry artifacts and manifests are produced. |
| Gmsh meshing adapter | **Implemented; qualification separate** | Integration exists; exact executable/host qualification is a separate gate. |
| CalculiX static FEM adapter | **Implemented; qualification separate** | Deterministic deck/result handling and verification foundations exist. |
| CAD → mesh → FEM → evidence → UI chain | **Implemented, opt-in** | The current physical-design chain exists and should be qualified and extended rather than rebuilt. |
| Integrated microalgae photobioreactor process model | **Planned / partial foundations** | Bounded process/hydraulic foundations exist, but the real integrated process model is still a major gap. |
| Process design / optimization loop | **Planned** | Iterative search/DOE/optimization over deterministic process evaluations. |
| Hermes AgentRuntime / MCP capability layer | **Planned / qualify first** | Candidate runtime/tool layer under Jarvis authority. |
| Engineering Qualification Suite | **Planned** | Starts after a usable beta and real engineering cases. |
| Design Explorer / DOE / Pareto studies | **Planned** | Intended to reuse qualified evaluators, not replace them with AI guesses. |
| Generative geometry, surrogates, active learning, specialist training | **Research** | Later work only if deterministic evaluators and real demand justify it. |

The exact implementation state is governed by [`docs/specs/STATUS.md`](docs/specs/STATUS.md), not by this summary.

### A physical-design path that already exists

![Current CAD-to-FEM engineering chain](docs/assets/readme/current-engineering-chain.svg)

This is one real path in the repository today. It is **not** the whole architecture, and it is not meant to imply that every future engineering workflow starts from CAD.

---

# Building blocks I plan to use

JarvisOS is intentionally not being designed in isolation. A large part of the project is finding strong existing projects, understanding what they already solve, and deciding where JarvisOS should integrate instead of reinventing.

The list below is my current shortlist, not a fixed dependency promise. I still need to validate fit, licensing boundaries, maintenance cost and engineering quality as each piece approaches real use. The roadmap is expected to change when better evidence or better upstreams appear.

## Orchestration, tools and memory

| Project / ecosystem | How I currently expect it to help |
| --- | --- |
| [NousResearch Hermes Agent](https://github.com/NousResearch/hermes-agent) | My leading candidate for a replaceable agent runtime: sessions, tool orchestration, progressive tool disclosure and MCP-style mechanics, while JarvisOS keeps policy and canonical state. |
| [Model Context Protocol](https://github.com/modelcontextprotocol/specification) | A standard boundary for exposing tools/resources/context without hard-wiring every runtime directly into Jarvis services. |
| [Serena](https://github.com/oraios/serena) | Semantic code intelligence through language servers, so coding agents can work with symbols and project structure instead of treating the repo as raw text. |
| [OpenAI Codex](https://github.com/openai/codex) | A strong architectural reference for agent runtime/state/process patterns and one candidate in the broader runtime bake-off. |
| [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) | Another reference/candidate for permissioned agent mechanics and tool use; useful for comparing runtime boundaries rather than locking JarvisOS to one vendor. |
| [Graphiti](https://github.com/getzep/graphiti), [Mem0](https://github.com/mem0ai/mem0), [Cognee](https://github.com/topoteretes/cognee) | Candidate ideas/backends for **derived** semantic or temporal memory. The important boundary is that retrieval memory remains rebuildable and non-authoritative. |
| [OpenTelemetry](https://github.com/open-telemetry/opentelemetry-specification) | A likely foundation for observing AI/tool runs consistently without confusing telemetry with engineering authority. |

## Engineering and scientific tools

| Project / ecosystem | How I currently expect it to help |
| --- | --- |
| [build123d](https://github.com/gumyr/build123d) + [Open CASCADE / OCCT](https://github.com/Open-Cascade-SAS/OCCT) | Already form the core of the parametric CAD layer: semantic Python geometry on top of a mature B-Rep kernel. |
| [Gmsh](https://gitlab.onelab.info/gmsh/gmsh) | Current meshing backend for turning geometry into solver-ready meshes with physical groups and quality evidence. |
| [CalculiX](https://www.calculix.de/) | Current open static-FEM backend; useful for structural verification when the scope fits. |
| [CoolProp](https://github.com/CoolProp/CoolProp) + [thermo](https://github.com/CalebBell/thermo) / [chemicals](https://github.com/CalebBell/chemicals) / [fluids](https://github.com/CalebBell/fluids) | Candidate property, transport, hydraulic and thermodynamic building blocks for process models instead of recreating basic correlations and property packages. |
| [BioSTEAM](https://github.com/BioSTEAMDevelopmentGroup/biosteam) + [QSDsan](https://github.com/QSD-Group/QSDsan) | Particularly relevant references for bio/process simulation, dynamic biological models, uncertainty and techno-economic workflows. |
| [IDAES](https://github.com/IDAES/idaes-pse) + [Pyomo](https://github.com/Pyomo/pyomo) + [WaterTAP](https://github.com/watertap-org/watertap) | Strong candidates for equation-oriented process modeling, optimization and reusable property/unit-model contracts. |
| [DWSIM](https://github.com/DanWBR/dwsim) + [CAPE-OPEN](https://www.cape-open.com/) | A possible open process-simulation backend and an interoperability route toward specialist process components. |
| [OpenMDAO](https://github.com/OpenMDAO/OpenMDAO) + [CasADi](https://github.com/casadi/casadi) | Candidate infrastructure for design studies, multidisciplinary coupling, optimization and eventually the Design Explorer loop. |
| [OpenFOAM](https://github.com/OpenFOAM/OpenFOAM-dev) | High-fidelity CFD when lower-cost correlations or reduced models cannot answer a specific mixing, shear, gas-transfer or flow question. |
| [LEAP71 ShapeKernel](https://github.com/leap71/LEAP71_ShapeKernel) | A later computational/generative geometry reference if the project reaches the point where deterministic design infrastructure justifies that extra complexity. |

The fuller audit trail is in [`docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`](docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md).

---

# Microalgae photobioreactor project

One of the first real engineering problems I want to use JarvisOS on is a personal **microalgae photobioreactor project**.

The important question is not “how do I draw the reactor?”. It is:

> **Given the biology, light, mixing, gas transfer, shear, pressure drop and energy demand, which operating conditions and reactor dimensions actually make sense?**

That makes **process simulation** the first major engineering capability I need from JarvisOS for this project.

![Microalgae photobioreactor design loop](docs/assets/readme/photobioreactor-process-loop.svg)

### Understand the process first

The model can progressively bring together the phenomena that actually matter:

- microalgal growth, productivity, limitation and inhibition;
- light availability, attenuation, self-shading, photolimitation and photoinhibition;
- circulation, mixing, recirculation time, dead zones and light/dark exposure;
- shear stress and biological shear limits;
- baffles or static mixers when they matter;
- CO2 delivery, O2 removal, gas-liquid transfer and `kLa`-type behaviour;
- aeration and gas-flow demand;
- nutrient dosing, pH and temperature control when relevant;
- pressure drop, pump/compressor demand and energy consumption;
- the trade-off between productivity, viability, transfer limits, footprint and energy.

The integrated model does **not** exist end to end yet. That is one of the main engineering gaps I want to close after the usable beta exists.

### Iterate before committing to geometry

The process model should not run once and immediately send an answer to CAD.

Jarvis should see each evaluation, compare it with constraints and evidence, change the next candidate and run the model again. At first that loop can be mostly human-guided; later it can use DOE, search and optimization.

Variables can include tube diameter and length, loop topology, circulation flow, biomass concentration, aeration/CO2 strategy, baffles, nutrient dosing and operating conditions.

The useful output is a **feasible or promising process-design envelope**: dimensions, flows, pressure drop, shear limits, gas-transfer requirements, energy constraints and productivity targets.

Only then does the CAD layer take over the next question:

> **How do I turn that process design into something that can actually be built, operated, cleaned, supported, inspected and verified?**

If geometry, CFD, FEM or manufacturability later invalidates a process assumption, the result goes back through Jarvis and reopens the process loop. It is not a one-way pipeline.

---

# Roadmap

The public roadmap is intentionally coarse. The live implementation sequence remains in [`docs/specs/STATUS.md`](docs/specs/STATUS.md).

```text
FINISH CURRENT FUNCTIONAL BETA
        ↓
GLOBAL VISUAL IDENTITY
        ↓
USABLE END-TO-END JARVISOS BETA
        ↓
FRESH CORE / RUNTIME REVALIDATION
Hermes · MCP · sandbox · model runtimes where justified
        ↓
INTEGRATED PHOTOBIOREACTOR PROCESS MODEL
biology · light · mixing/shear · gas transfer · control · hydraulics · energy
        ↓
PROCESS DESIGN / OPTIMIZATION LOOP
geometry-driving dimensions · flow · aeration · operating constraints
        ↓
CAD / PHYSICAL REALIZATION
reuse and extend the existing parametric geometry path
        ↓
MESH / CFD / FEM / MANUFACTURABILITY
when the engineering decision needs them
        ↓
FIRST REAL MICROALGAE PROJECT CASES
        ↓
DOMAIN-SPECIFIC ENGINEERING QUALIFICATION
        ↓
DESIGN EXPLORER
DOE · optimization · feasibility · Pareto · evidence-grounded explanation
        ↓
ADVANCED GENERATIVE ENGINEERING
surrogates · active learning · generative geometry · specialist training
```

The sequence I care about is simpler than the diagram:

> **Build something usable → use it on a real engineering problem → discover what has to be trusted → qualify those models → automate broader design exploration.**

The Engineering Qualification Suite is deliberately not a prerequisite for reaching beta. It starts once there is something real to use and real decisions to compare.

---

# Technical details

Everything below this point is intentionally more technical.

## Current application stack

### Backend

- **Python**
- **FastAPI**
- **Pydantic**
- **Pint** for units
- **SQLite**-backed durable application state
- **httpx** and explicit provider/runtime adapters
- **PyYAML** for bounded configuration surfaces

Pinned backend dependencies: [`backend/requirements.txt`](backend/requirements.txt).

### Frontend

- **React 18**
- **TypeScript**
- **Vite**
- **Three.js** for 3D engineering inspection

Pinned frontend dependencies: [`frontend/package.json`](frontend/package.json).

### Current engineering stack

- **build123d / OCP / OpenCascade** for deterministic B-Rep geometry;
- **Gmsh** through a registry-bound external-tool adapter for meshing;
- **CalculiX** through a registry-bound adapter for static FEM;
- bounded process/hydraulic calculation and runner foundations;
- typed simulation runs, artifacts, manifests, digests, evidence and acceptance criteria.

The current Gmsh and CalculiX integrations are intentionally safe-default disabled until an operator provides an exact executable/version/provenance/hash-qualified registry entry. An adapter being implemented is not the same as a solver being scientifically qualified for every use case.

## Architectural ownership

JarvisOS is intended to own:

- canonical project and engineering state;
- engineering identity, units, provenance, freshness and acceptance;
- AI route/budget/egress policy;
- capability grants and commit/promotion authority;
- run/artifact/evidence identity;
- semantic engineering contracts that connect replaceable tools.

External systems may own replaceable mechanics:

- agent loops and session runtimes;
- model inference;
- semantic code intelligence;
- derived retrieval indexes;
- sandbox/isolation mechanisms;
- CAD/mesh/CFD/FEM/property/process numerical kernels;
- telemetry transport.

> **JarvisOS owns semantic engineering intent and evidence; numerical kernels remain replaceable.**

## Memory and evidence model

| Layer | Authority | Current direction |
| --- | --- | --- |
| Canonical structured state | **Authoritative** | Jarvis-owned durable accepted/proposed/rejected/superseded records and engineering state. |
| Runs / artifacts / evidence | **Authoritative evidence** | Exact run identity, inputs, outputs, manifests, digests, provenance and criteria. |
| Derived semantic/temporal retrieval | **Non-authoritative** | Future rebuildable index; candidate backends/patterns are still being qualified. |
| External notes / documents | **Source material** | Optional bounded context sources; promotion to canonical state must be explicit. |

## Agent/runtime model

The future runtime direction is adapter-based:

```text
Jarvis authority
      ↓ bounded task + context + capability grant
AgentRuntime adapter
      ↓
Hermes / another qualified runtime
      ↓
MCP / capability gateway
      ↓
Jarvis services + engineering-tool adapters
      ↓
evidence returned to Jarvis authority
```

Hermes is currently a candidate, not an integrated dependency and not canonical authority.

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
FastAPI read models → CAD / Runs / Analytics frontend
```

## Engineering qualification philosophy

A numerical tool is not accepted because it is open source, popular or produces a plausible plot.

For a real engineering decision, qualification can compare selected evaluators against analytical solutions, trusted correlations, literature or experimental data, independent numerical implementations and commercial engineering software where a meaningful comparison is available.

The useful question is not:

> *Is JarvisOS equivalent to every feature of Fusion, Aspen HYSYS, ANSYS or STAR-CCM+?*

It is:

> **For the engineering decisions I actually need to make, are JarvisOS and its selected backends accurate, robust, reproducible and traceable enough to be useful?**

If the answer for a subsystem is no, I would rather replace that evaluator or call a stronger specialist tool than hide the limitation.

## Repository map

```text
backend/    FastAPI application, domain services, AI/runtime logic, engineering adapters and tests
frontend/   React + Vite + TypeScript operator application
scripts/    Windows startup, local probes, smoke/evaluation helpers
schemas/    design-time schemas
reports/    generated bounded evaluation/smoke reports
docs/       architecture, specs, strategy, audits, evidence and historical design records
```

Important documentation entry points:

- [`docs/specs/STATUS.md`](docs/specs/STATUS.md) — **sole live implementation/queue authority**;
- [`AGENTS.md`](AGENTS.md) — hard repository invariants for coding agents;
- [`docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`](docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md) — exact-head delivery and automation rules;
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — architecture;
- [`docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`](docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md) — audited candidate/upstream register;
- [process-first engineering priority amendment](docs/strategy/BLUEREV_ENGINEERING_PRIORITY_AMENDMENT_2026-08-21.md) — internal strategy correction for the photobioreactor work.

## Running the current development build

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

Default local development endpoints:

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

Third-party packages, tools, reference projects and external software retain their own licenses and copyright. Their presence in this README does not place them under the JarvisOS copyright posture.

## Collaboration

I am especially interested in criticism or collaboration around:

- photobioreactors, microalgae and biochemical/process systems engineering;
- process modeling, transport phenomena, hydrodynamics and mass transfer;
- scientific Python and numerical methods;
- CAD/CAE, meshing, CFD/FEM and engineering interoperability;
- local AI runtimes, agent infrastructure, sandboxing and tool protocols;
- engineering validation, provenance and reproducible computational workflows.

A useful contribution is often **not more code**. Sometimes the best contribution is simply pointing me to an existing project that already solves a problem better than something I was about to build.

If you want to discuss the project, suggest an upstream, contribute substantially, explore a research collaboration or talk about licensing, **contact me** through GitHub.

The long-term boundary between protected JarvisOS core components and potentially open/reusable interfaces, adapters, schemas or examples is still under evaluation.

---

## A final note

I do not expect this README to prove that JarvisOS is useful. The interesting part starts when I can use it on real engineering problems and compare the results with methods and software I already trust.
