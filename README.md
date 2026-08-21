# JarvisOS

**An experimental local-first AI co-engineering workspace.**

I am building JarvisOS as a chemical engineering student, not as a software engineer trying to launch a finished CAD/CAE product. I did not start this project with a software-engineering background. Part of the experiment is exactly that: **how far can an engineer with domain knowledge, AI-assisted software development, local models, and existing scientific tools go in building a useful personal engineering environment?**

The answer is not assumed in advance. The repository contains real implemented paths, tests, architecture, and a substantial roadmap, but usefulness has to be earned through real engineering cases and independent validation.

> **JarvisOS is not a claim that an AI can replace engineering expertise, Fusion, Aspen HYSYS, ANSYS, or other mature industrial software.** The goal is to build a controlled environment that can combine the best available tools — open, local, custom, or commercial when necessary — without making one AI model or one vendor the owner of the engineering workflow.

> **License note:** this repository is publicly source-available for inspection and evaluation, but it is **not currently distributed under an open-source software license**. See [Source availability and licensing](#source-availability-and-licensing).

This README is the public front door to the project. It is intentionally more stable and explanatory than the internal implementation registry. For exact current work state and implementation authority, see [`docs/specs/STATUS.md`](docs/specs/STATUS.md).

---

## Why I am building it

Modern engineering work can depend on excellent but expensive proprietary software, cloud services, and increasingly on AI systems that process project context outside the engineer's machine. I am interested in a different operating model:

- **local-first where practical** — private or sensitive engineering context should not need to leave the machine merely because an AI feature is useful;
- **tool independence** — the workspace should survive changing AI providers, model runtimes, numerical solvers, and software vendors;
- **reuse before reinvention** — JarvisOS should connect mature scientific and open-source tools rather than rebuild them for ego or architectural purity;
- **deterministic engineering evidence** — an LLM may propose, explain, or help write software, but engineering results should come from inspectable models, solvers, calculations, and explicit evidence;
- **lower barriers to engineering software** — AI-assisted coding may let domain engineers build integrations and workflows that previously required much deeper software specialization;
- **selective openness** — I want to learn from, depend on, and where appropriate contribute back to open-source projects, while keeping the option to protect parts of JarvisOS and future commercial work.

The project is therefore both a tool and an experiment in **human + AI leverage**. AI systems have helped substantially with coding, review, research, and architecture. That does not make generated code or AI reasoning correct by default; JarvisOS is deliberately designed around that limitation.

---

## The core idea

![JarvisOS architecture overview](docs/assets/readme/architecture-overview.svg)

The architectural rule is simple:

> **AI models propose. JarvisOS validates, gates, records, executes, and audits.**

JarvisOS owns canonical project state, policy, provenance, permissions, external-data egress, execution boundaries, engineering acceptance, and evidence. AI runtimes and scientific tools are replaceable components around that core.

This is important because a fluent answer from an AI model is not the same thing as an accepted engineering result.

---

# BlueRev: the first intended real engineering use case

The first domain in which I want JarvisOS to become genuinely useful is **photobioreactor/process engineering for BlueRev**.

A previous version of the roadmap made CAD unusually visible because the CAD → mesh → FEM path is already much more mature in the repository than the biological/process side. That implementation asymmetry is not the intended engineering priority.

> **Implementation maturity must never be used as a proxy for BlueRev product priority.**

For BlueRev, the priority is **process first, physical CAD second**.

![BlueRev process-first engineering flow](docs/assets/readme/bluerev-process-first.svg)

## P1 — Integrated photobioreactor process simulation

The first major BlueRev engineering capability is intended to model enough of the process to predict and compare real operating/design choices. Depending on the case and required fidelity, that can include:

- microalgal growth kinetics, productivity, concentration, limitation, and inhibition;
- incident light, attenuation/self-shading, light limitation, and photoinhibition;
- circulation, mixing, recirculation time, dead zones, and light/dark exposure;
- shear stress and biological shear limits;
- baffles or static mixers when they materially affect mixing or viability;
- gas-liquid mass transfer, CO2 delivery, O2 generation/removal, stripping, and `kLa`-type metrics;
- aeration and gas-flow requirements;
- nutrient dosing and consumption;
- pH, temperature, and control demand where relevant;
- pressure drop, hydraulics, pump/compressor demand, and energy consumption;
- volumetric/areal productivity and trade-offs between productivity, viability, transfer, and energy.

**This integrated BlueRev process model is a priority target, not a claim that all of these capabilities already exist today.** The repository currently contains bounded process/hydraulic foundations, but the BlueRev-specific end-to-end model is still a major gap.

## P1b — Process design and optimization

Once a process model can evaluate a configuration, JarvisOS should be able to vary quantities such as:

- tube diameter and total length;
- number of loops and reactor topology;
- circulation flow rate and velocity;
- biomass concentration;
- aeration / CO2 flow and injection strategy;
- baffles/static-mixer parameters;
- nutrient and operating conditions.

A central design rule is:

> **Tube diameter, length, flow rate, and reactor topology are first process-design variables and only secondarily CAD parameters.**

The process layer should eventually produce a feasible/design envelope — pressure drop, shear, gas transfer, energy, productivity, operating constraints, dimensions — rather than simply asking CAD to invent a shape.

## P2 — Physical design / BLUECAD

Only after the process requirements are sufficiently constrained does BLUECAD become the main problem: **how do we turn the selected process into a physical object that can actually be built, operated, inspected, cleaned, supported, and verified?**

That includes geometry, loop/serpentine arrangement, manifolds, bend radii, supports, interfaces, footprint, accessibility, materials, manufacturability, and structural verification.

The existing BLUECAD work is therefore not less important; it is downstream of the process question.

---

# What works today?

The table below is an orientation snapshot, not the live spec registry. Exact current implementation state belongs in [`docs/specs/STATUS.md`](docs/specs/STATUS.md).

| Capability | BlueRev priority | Current maturity | Notes |
| --- | --- | --- | --- |
| Jarvis canonical engineering state, provenance and evidence | Foundation | **Working** | Backend-owned durable records and evidence relationships are already part of the product spine. |
| Local/external AI routing, policy, budget and egress controls | Foundation | **Working** | Local-first routes exist; external AI is explicit and policy-gated rather than an automatic authority path. |
| Frontend/backend engineering workbench surfaces | Foundation | **Working / evolving** | React frontend and FastAPI backend are connected; the functional beta is still being completed. |
| Bounded deterministic runner | Foundation | **Working** | Reviewed deterministic models can run through bounded runner contracts with persisted results/evidence. |
| **Integrated BlueRev photobioreactor process model** | **P1 — highest** | **Planned / partial foundations only** | This is the most important major engineering gap after a usable beta. |
| **BlueRev process design / optimization** | **P1b** | **Planned** | Will vary process/design variables using deterministic evaluators before physical CAD. |
| BLUECAD semantic parametric geometry | **P2** | **Working** | `GeometrySpec` + deterministic build123d/OCP construction and stable engineering artifacts. |
| STEP / STL / GLB export and manifests | P2 support | **Working** | Used by the current BLUECAD pipeline and frontend inspection. |
| Gmsh meshing adapter | P2 support | **Implemented and tested** | Real executable use remains safe-default disabled until exact target-host qualification. |
| CalculiX static FEM adapter | P2 support | **Implemented and tested** | Includes deterministic deck/result handling and a verification foundation; target-host qualification remains separate. |
| CAD → mesh → FEM → evidence → UI chain | P2 support | **Implemented, opt-in** | Existing path should be kept, qualified and extended rather than rebuilt. |
| Engineering Qualification Suite | Validation | **Planned** | Begins after a usable beta and first real BlueRev cases; domain-specific rather than a generic imitation of commercial suites. |
| Hermes / broader AgentRuntime + MCP capability integration | Platform | **Planned / qualification required** | Candidate runtime/tool layer; Jarvis must retain authority. |
| Design Explorer / DOE / Pareto studies | Later engineering | **Planned** | Intended to reuse qualified process and physical evaluators, not replace them with AI guesses. |
| Generative geometry, surrogates, active learning, specialist training | Research | **Requires further research** | Only after deterministic evaluators and real demand justify them. |

### Status vocabulary

- **Working** — production-reachable code/path exists and is exercised by the current application/test system.
- **Work in progress** — currently being completed or integrated in the live functional queue.
- **Planned** — architecture or roadmap exists, but implementation is not authorized merely because it appears here.
- **Requires further research** — the direction may be useful, but technical value, fidelity, or integration economics are not yet proven.

---

# Roadmap

The public roadmap is intentionally coarse. It describes direction without duplicating the live internal spec sequence.

```text
CURRENT FUNCTIONAL BETA WORK
        |
        v
GLOBAL VISUAL IDENTITY
        |
        v
USABLE END-TO-END JARVISOS BETA
        |
        v
FRESH CORE / RUNTIME REVALIDATION
Hermes · MCP · sandbox · model-runtime boundaries only where justified
        |
        v
P1 — INTEGRATED PHOTOBIOREACTOR PROCESS MODEL
biology · light · mixing/shear · gas transfer · nutrients/control · energy
        |
        v
P1b — PROCESS DESIGN / OPTIMIZATION
D · L · topology · flow · aeration · operating constraints
        |
        v
P2 — BLUECAD PHYSICAL REALIZATION
reuse and extend the existing CAD path
        |
        v
MESH / CFD / FEM / MANUFACTURABILITY
only where the engineering decision requires them
        |
        v
FIRST REAL BLUEREV ENGINEERING CASES
        |
        v
DOMAIN-SPECIFIC ENGINEERING QUALIFICATION
        |
        v
DESIGN EXPLORER
DOE · optimization · feasibility · Pareto · evidence-grounded explanation
        |
        v
ADVANCED GENERATIVE ENGINEERING
surrogates · active learning · generative geometry · specialist training
```

The key sequencing distinction is:

**build something usable first → use it on real BlueRev problems → discover what must be trusted → qualify those models → automate broader design exploration.**

The Engineering Qualification Suite is deliberately **not** a prerequisite for ever reaching beta. It exists to determine, after real use begins, whether the selected open/custom/commercial backends are accurate, robust, reproducible, and traceable enough for the actual BlueRev decisions being made.

JarvisOS does not need to reproduce every refinery, combustion, distillation, or petrochemical capability of a general industrial process simulator if those problems are irrelevant to BlueRev. If a future problem genuinely requires Aspen HYSYS, ANSYS, Fusion, STAR-CCM+, or another commercial tool, JarvisOS should be able to treat that tool as a specialist backend rather than pretending an inferior substitute is automatically good enough.

**Local-first is a control strategy, not an anti-commercial ideology.**

---

# How AI is allowed to participate

![JarvisOS AI authority model](docs/assets/readme/ai-authority.svg)

JarvisOS deliberately separates several things that are often collapsed in AI demos:

1. a model being capable of proposing an action;
2. a tool being visible to that model;
3. the user/Jarvis policy granting permission;
4. execution actually occurring;
5. the resulting evidence being accepted into canonical engineering state.

The AI can help formulate a model, explain results, propose a geometry, choose tools, draft code, search the repository, or suggest the next experiment. It does **not** become engineering truth merely by sounding confident.

For the same reason, external AI egress and canonical state mutation are separate authority boundaries. A future agent runtime such as Hermes may execute useful mechanics, but it is intended to remain replaceable and subordinate to JarvisOS policy/state/evidence rules.

---

# For technical readers

## Current application stack

### Backend

- **Python**
- **FastAPI**
- **Pydantic**
- **Pint** for units
- **SQLite**-backed durable application state
- **httpx** and explicit provider/runtime adapters
- **PyYAML** for bounded configuration surfaces

Pinned backend dependencies are in [`backend/requirements.txt`](backend/requirements.txt).

### Frontend

- **React 18**
- **TypeScript**
- **Vite**
- **Three.js** for 3D engineering inspection

Pinned frontend dependencies are in [`frontend/package.json`](frontend/package.json).

### Current engineering stack

- **build123d / OCP / OpenCascade** for deterministic B-Rep geometry;
- **Gmsh** through a registry-bound external-tool adapter for meshing;
- **CalculiX** through a registry-bound adapter for static FEM;
- bounded process/hydraulic calculation and runner foundations;
- typed simulation runs, artifacts, manifests, digests, evidence and acceptance criteria.

![Current BLUECAD engineering chain](docs/assets/readme/current-engineering-chain.svg)

The current Gmsh and CalculiX integration is intentionally safe-default disabled until an operator provides an exact executable/version/provenance/hash-qualified registry entry. **An adapter being implemented is not the same as a solver being qualified for every engineering use case.**

## Architectural ownership

JarvisOS is intended to own:

- canonical project and engineering state;
- engineering identity, units, provenance, freshness, and acceptance;
- AI route/budget/egress policy;
- capability grants and commit/promotion authority;
- run/artifact/evidence identity;
- the semantic engineering contracts that connect replaceable tools.

External systems may own replaceable mechanics:

- agent loops and session runtimes;
- model inference;
- semantic code intelligence;
- derived retrieval indexes;
- sandbox execution mechanisms;
- CAD/mesh/CFD/FEM/property/process numerical kernels;
- telemetry transport.

A repeated design principle is:

> **BLUECAD/JarvisOS owns semantic engineering intent and evidence; numerical kernels remain replaceable.**

## Current repository engineering chain

The production-shaped path already present is approximately:

```text
operator / Jarvis proposal
        |
        v
BLUECAD candidate + GeometrySpec
        |
        v
build123d / OCP
        |
        +--> STEP / STL / GLB + manifests / digests
        |
        v
registry-bound Gmsh
        |
        +--> mesh + physical groups + quality evidence
        |
        v
registry-bound CalculiX
        |
        +--> solver outputs + parsed result summary
        |
        v
SimulationRun + artifacts + typed evidence + acceptance criteria
        |
        v
FastAPI read models -> BLUECAD / Runs / Analytics frontend
```

For BlueRev, that physical chain is intended to sit **after** the process-design layer described earlier, except where geometry and process physics must iterate explicitly.

---

# Selected upstreams and reference projects

JarvisOS is intentionally not designed in isolation. I have been auditing upstream projects to decide whether JarvisOS should **keep**, **wrap**, **replace**, **extend**, or simply **learn from** existing software.

The complete candidate register is in [`docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`](docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md). A project appearing below does **not** mean it is bundled, integrated, endorsed, or part of the JarvisOS license.

| Project | Why it matters here | Relationship |
| --- | --- | --- |
| [build123d](https://github.com/gumyr/build123d) | Pythonic parametric B-Rep CAD | Current dependency / BLUECAD geometry foundation |
| [Open CASCADE / OCCT](https://github.com/Open-Cascade-SAS/OCCT) | Mature geometric modeling kernel | Underlying geometry technology / reference |
| [Gmsh](https://gitlab.onelab.info/gmsh/gmsh) | Mesh generation and physical groups | Current external solver/mesher adapter |
| [CalculiX](https://www.calculix.de/) | Open finite-element solver | Current external static-FEM adapter |
| [NousResearch Hermes Agent](https://github.com/NousResearch/hermes-agent) | Agent runtime, progressive tool disclosure, MCP/tool execution patterns | Future runtime candidate; not canonical authority |
| [Serena](https://github.com/oraios/serena) | Semantic code intelligence via language servers | Future code-intelligence candidate |
| [OpenAI Codex](https://github.com/openai/codex) | Agent runtime/state/process architecture patterns | Architectural reference / runtime bake-off candidate |
| [Model Context Protocol](https://github.com/modelcontextprotocol/specification) | Standardized tool/context interoperability | Future capability/tool boundary candidate |
| [CoolProp](https://github.com/CoolProp/CoolProp) | Thermophysical properties | Future process/property backend candidate |
| [IDAES](https://github.com/IDAES/idaes-pse) | Equation-oriented process modeling and optimization | High-value future process-engineering candidate |
| [BioSTEAM](https://github.com/BioSTEAMDevelopmentGroup/biosteam) | Bioprocess simulation / TEA ecosystem | Future bio/process candidate |
| [DWSIM](https://github.com/DanWBR/dwsim) | Open process simulator and interoperability reference | Possible external process backend |
| [OpenFOAM](https://github.com/OpenFOAM/OpenFOAM-dev) | High-fidelity CFD | Conditional backend when lower-cost models cannot answer a named decision |
| [LEAP71 ShapeKernel](https://github.com/leap71/LEAP71_ShapeKernel) | Computational/generative engineering geometry | Research candidate after deterministic design infrastructure |

Before any substantial reuse, vendoring, or dependency adoption, the exact upstream version, license, transitive boundary, maintenance cost, and measurable benefit are intended to be re-checked. JarvisOS does not need to adopt every interesting repository it studies.

---

# Engineering qualification philosophy

A numerical tool is not accepted because it is open source, popular, or produces a plausible plot.

For a real BlueRev decision, qualification may compare JarvisOS-selected evaluators against:

- analytical solutions;
- trusted engineering correlations;
- literature data;
- experimental data when available;
- independent numerical implementations;
- commercial engineering software when a meaningful comparison is available.

The useful question is not:

> Is JarvisOS equivalent to every feature of Fusion, Aspen HYSYS, ANSYS, or STAR-CCM+?

It is:

> **For the engineering decisions BlueRev actually needs to make, are JarvisOS and its selected backends accurate, robust, reproducible, and traceable enough to be useful?**

If the answer for a subsystem is no, the architecture should make it possible to replace that evaluator or call a stronger specialist tool instead of hiding the limitation.

---

# Repository map

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
- [`docs/README.md`](docs/README.md) — documentation authority map;
- [`docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`](docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md) — audited candidate/upstream register;
- [`docs/strategy/JARVISOS_BACKEND_PUZZLE_STRATEGY_2026-08-21.md`](docs/strategy/JARVISOS_BACKEND_PUZZLE_STRATEGY_2026-08-21.md) — future backend strategy;
- [`docs/strategy/JARVISOS_BACKEND_PUZZLE_QUEUE_BLUEPRINT_2026-08-21.md`](docs/strategy/JARVISOS_BACKEND_PUZZLE_QUEUE_BLUEPRINT_2026-08-21.md) — non-authoritative future queue blueprint;
- [`docs/strategy/BLUEREV_ENGINEERING_PRIORITY_AMENDMENT_2026-08-21.md`](docs/strategy/BLUEREV_ENGINEERING_PRIORITY_AMENDMENT_2026-08-21.md) — process-first BlueRev priority correction.

Older planning documents can be valuable historical evidence without being current implementation authority.

---

# Running the current development build

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

Recreate backend dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
```

Frontend dependencies:

```powershell
cd frontend
npm install
```

Representative local checks:

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check app tests

cd ..\frontend
npm run build
```

The repository also uses CI and exact-head gates; see the internal execution documentation for the authoritative development workflow.

---

# Collaboration

I am interested in technical criticism and collaboration around areas such as:

- photobioreactors, microalgae, biochemical/process systems engineering;
- process modeling, transport phenomena, hydrodynamics and mass transfer;
- scientific Python and numerical methods;
- CAD/CAE, meshing, CFD/FEM and engineering interoperability;
- local AI runtimes, agent infrastructure, sandboxing and tool protocols;
- engineering validation, provenance and reproducible computational workflows.

A particularly useful contribution is often **not more code**, but evidence that an existing project already solves a problem better than something JarvisOS was about to build.

Please use GitHub discussions/issues where appropriate or contact the repository owner before proposing substantial code, research, integration, or commercial collaboration.

---

# Source availability and licensing

Copyright © 2026 Alberto Racerro. All rights reserved.

This repository is publicly available for inspection and evaluation, but **no software license is currently granted for JarvisOS itself**.

Except for the limited rights provided by GitHub's Terms of Service for use through GitHub's functionality, no permission is granted to use, copy, modify, distribute, sublicense, sell, commercialize, or create derivative products from this codebase unless separately agreed in writing.

Public source availability must therefore **not** be interpreted as an open-source license or a waiver of copyright.

Third-party packages, tools, reference projects, and external software retain their own licenses and copyright. Their presence in documentation does not place them under the JarvisOS copyright posture.

If you are interested in using JarvisOS, building on it, integrating a component, contributing substantially, conducting research together, or discussing commercial licensing, contact the repository owner first. Terms can be considered case by case.

The long-term boundary between protected JarvisOS core components and potentially open/reusable interfaces, adapters, schemas, or examples is still under evaluation.

---

## A note on expectations

This repository is intentionally public enough to be inspectable. That means the useful standard is not whether the project sounds ambitious; it is whether individual claims survive inspection by people who know more than I do.

Where the code works, the README should say that it works. Where a path is merely implemented but not yet scientifically qualified, it should say so. Where something is planned, it should not be presented as a feature. Where an existing project is better than a custom implementation, JarvisOS should prefer reuse or integration.

That distinction is part of the project.
