<h1 align="center">JarvisOS</h1>

<h3 align="center">An experimental AI-assisted engineering workspace</h3>

<p align="center"><strong>What can one chemical-engineering-minded person build with strong AI tools, careful verification and ordinary engineering common sense?</strong></p>

<p align="center"><code>personal R&D</code> · <code>local-first</code> · <code>evidence-first</code> · <code>source-available</code></p>

<p align="center"><a href="#the-short-version">Short version</a> · <a href="#why-i-am-building-this">Why</a> · <a href="#the-microalgae-project">Microalgae project</a> · <a href="#what-i-want-the-workspace-to-feel-like">AI cowork</a> · <a href="#what-jarvisos-is-not">What it is not</a> · <a href="#what-exists-today">Current state</a> · <a href="#technical-details">Technical details</a> · <a href="#licensing-and-collaboration">License</a></p>

> **Important:** JarvisOS is a personal experiment, not a commercial engineering suite and not a claim of software-development expertise. I come from chemical engineering, not software development. I am using modern AI tools to see how far a serious engineering project can be pushed by one person who is willing to study, test, compare results, accept mistakes and keep the system honest about what it can and cannot do.

> **License note:** this repository is publicly source-available for inspection and evaluation, but JarvisOS is **not currently distributed under an open-source software license**. See [Licensing and collaboration](#licensing-and-collaboration).

The exact live implementation queue is [`docs/specs/STATUS.md`](docs/specs/STATUS.md). The canonical architecture is [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

# The short version

JarvisOS is an attempt to build one personal R&D workspace where an engineer can:

- keep project knowledge, assumptions, requirements, models, runs and evidence together;
- work with AI assistants that can discuss a problem, challenge assumptions, explain results, suggest changes and help write or inspect code;
- connect different calculation tools, numerical models, CAD/CAE tools and eventually commercial engineering software through controlled interfaces;
- run as much as practical locally;
- decide explicitly when information may leave the machine and reach an external AI provider;
- preserve traceability between a design decision and the calculations, files and assumptions behind it.

The long-term idea is less “build a new super-software that replaces everything” and more:

> **build a useful engineering desk where different specialist tools and AI assistants can work together around one project without silently taking ownership of the engineering decision.**

The human engineer remains responsible for the engineering. JarvisOS is supposed to help organize the work, connect tools, preserve evidence and make AI collaboration more useful and less opaque.

---

# Why I am building this

I started JarvisOS from the point of view of someone interested in engineering R&D, not from the point of view of an experienced software architect.

That is part of the experiment.

The question is not whether I can personally reinvent the software industry. I cannot, and that is not the objective. The question is whether current AI systems can reduce the software barrier enough that an engineer with no formal software-development background can still assemble a useful, technically disciplined tool for a real project.

My approach is roughly:

1. define the engineering problem;
2. ask AI for help designing or implementing a bounded solution;
3. inspect what was produced;
4. test it aggressively;
5. compare it against known equations, independent implementations, documentation or trusted software when possible;
6. remove or replace custom code when a stronger existing project already solves the problem better;
7. keep going only when the result survives those checks.

This repository therefore contains both useful working software and the evidence of a learning process. Some designs have already been replaced. Some experiments are intentionally retained only as references. Some future ideas may never be worth implementing.

That is preferable to pretending every early decision was correct.

## A practical motivation: engineering outside the university environment

Engineering students and researchers often have access to excellent commercial software through university licenses. That access may disappear, become expensive or become impractical outside the university environment.

For the kind of R&D work I want to continue, I would like a platform that can use strong open, local or low-cost tools where they are good enough, while still leaving room to connect commercial tools when they are genuinely necessary.

This does **not** mean pretending that an open-source library is automatically equivalent to Aspen HYSYS, ANSYS, Fusion, STAR-CCM+ or another mature industrial package. If a commercial tool is the right tool for a decision, the architecture should be able to use it.

The goal is to avoid making the whole project dependent on one expensive license before that dependency is actually justified.

## A second motivation: control over sensitive R&D data

The other concern is AI.

Cloud AI systems are extremely useful, but real engineering projects can contain confidential company information, unpublished research, design details, experimental data, intellectual property and other material that should not be sent casually to third-party services.

JarvisOS is therefore designed **local-first**, not because cloud AI is inherently unacceptable, but because data egress should be a deliberate engineering and security decision.

The intended pattern is:

```text
local project state
      ↓
select only the required context
      ↓
apply policy / sensitivity / budget checks
      ↓
use a local model when adequate
      OR
explicitly authorize an external provider when useful
```

Local-first is a design preference, not a claim that the current system is a formally certified secure environment. Security, isolation and provider policy are still engineering problems that must be tested like everything else.

---

# The microalgae project

The first serious engineering use case behind JarvisOS is a **microalgae photobioreactor R&D project**.

The problem is naturally multidisciplinary. A useful design can involve:

- biology and productivity;
- light availability and optical attenuation;
- gas transfer and CO₂ supply;
- mixing and shear;
- hydraulics and pressure drop;
- pumps and energy demand;
- reactor geometry;
- buoyancy and structural considerations;
- process economics;
- CAD, meshing, CFD or FEM when higher fidelity is actually needed.

In a conventional workflow these questions can end up spread across spreadsheets, Python or MATLAB scripts, process simulators, CAD packages, reports, papers and many separate AI chats.

The JarvisOS idea is to make them parts of one traceable project.

![Microalgae photobioreactor design loop](docs/assets/readme/photobioreactor-process-loop.svg)

The intended workflow is roughly:

```text
Engineer + AI assistants
        ↓
goals · assumptions · questions · alternatives
        ↓
project knowledge + typed engineering data
        ↓
calculation / process / CAD / CAE evaluators
        ↓
results + evidence + limitations
        ↓
comparison / optimization / discussion
        ↓
engineering decision
```

The integrated predictive PBR model does **not** exist end to end today. Current process work consists of bounded screening models and experiments. That distinction matters.

---

# What I want the workspace to feel like

The interaction goal is closer to having a small group of useful collaborators around the same engineering desk than to using a chatbot in a separate browser tab.

Different AI systems may be useful for different jobs: discussing an idea, criticizing assumptions, reading documentation, inspecting code, planning an experiment, explaining a solver failure or drafting a change.

I sometimes think of that experience as having colleagues, friends or specialists available to discuss the work with. That is a **workflow metaphor**, not a claim that AI systems are people or that their answers carry professional authority.

A good AI assistant in JarvisOS should be able to say things such as:

- “this assumption is inconsistent with the accepted project basis”;
- “this result depends on a stale parameter”;
- “these two models disagree here”;
- “this calculation is outside its validity range”;
- “I can suggest this change, but I cannot commit it without the proper owner transition”;
- “there is already an upstream library that probably solves this better than our custom code.”

That is more useful to me than an assistant that confidently produces an answer without exposing how it relates to the rest of the project.

---

# What JarvisOS is not

JarvisOS is **not**:

- a replacement for Aspen HYSYS, ANSYS, Fusion, OpenFOAM, MATLAB or every other engineering package;
- a new frontier AI model;
- a replacement for Claude Code, Codex, Hermes or other software/agent systems;
- evidence that one person with AI has suddenly become an expert software-development team;
- a certified engineering platform;
- a guarantee that every model in the repository is scientifically valid for every use case;
- an attempt to hide the fact that much of the software was built with substantial AI assistance.

Where those tools are strong, I would rather integrate or learn from them than imitate them badly.

The interesting experiment is the **integration layer and engineering workflow**: can different tools and AI systems cooperate around one controlled project state, while keeping assumptions, evidence, authority and data handling explicit?

---

# What exists today

JarvisOS is still under active development, but it is no longer only a mock-up.

| Area | Current reality |
| --- | --- |
| Operator application | A React/TypeScript engineering workstation exists with shared navigation, project surfaces, Jarvis sidecar, runs, engineering data, lineage, analysis and BLUECAD views. |
| Project knowledge | Backend-owned Project Basis change sets, working revisions, impact/revalidation and reconciliation foundations exist. |
| Engineering records | Typed records, lifecycle state, provenance, freshness and CAS-style guarded updates exist for supported paths. Some legacy write surfaces are still being consolidated. |
| AI execution | Local/external routing, provider configuration, budget/accounting and controlled egress foundations exist. |
| Context for AI | Exact project/context references and deterministic bounded context assembly exist. |
| CAD | Parametric B-Rep geometry uses build123d/OCP/OpenCascade for the supported vocabulary. |
| Meshing | Gmsh is connected through a controlled external-tool adapter. |
| Static FEM | CalculiX is connected through a controlled adapter with verification foundations. |
| CAD → mesh → FEM | A bounded end-to-end physical-design path exists with artifacts and evidence. |
| Process/PBR calculations | Several useful screening models and process-kernel experiments exist, but not a complete predictive PBR simulator. |
| CI / architecture checks | Automated tests and architecture guards try to stop accidental new state, provider or database side channels from appearing. |
| Hermes / MCP-style runtime | Possible future integration area, not a current claim or required runtime. |

For exact spec state and implementation status, use [`docs/specs/STATUS.md`](docs/specs/STATUS.md). This README intentionally stays higher level.

---

# The design principles in plain language

## 1. The AI is allowed to be useful, not magical

AI can reason, propose, explain and call authorized capabilities. Its text is not automatically engineering truth.

## 2. One important fact should have one real owner

Project parameters, requirements, runs, evidence and other durable state should not be silently editable through multiple unrelated paths.

## 3. Results should come with receipts

Important calculations should retain inputs, units, model identity, artifacts, provenance and enough context to understand where the result came from.

## 4. Use existing software when it is better

Custom code gets no special protection just because time was spent writing it. If BioSTEAM, IDAES, Pyomo, OpenMDAO, Gmsh, CalculiX, OpenFOAM or another project is better for a generic problem, JarvisOS should wrap or reuse it where practical.

## 5. Use expensive fidelity only when the decision needs it

Not every question needs CFD. Not every geometry needs FEM. Cheap analytical or reduced-order models should solve the easy part first; higher-fidelity tools should be used when they can actually change a decision.

## 6. Local-first, not local-only

Keep sensitive context and ordinary work local when practical. External AI or commercial software can still be used deliberately when their value justifies it.

---

# Technical details

The rest of this README is for readers who want a more software-oriented description.

## High-level architecture

![JarvisOS high-level architecture](docs/assets/readme/architecture-overview.svg)

A simplified ownership model is:

```text
Engineer
  owns the engineering decision

JarvisOS
  owns application state, identity, policy, provenance and controlled transitions

AI / agent runtimes
  reason, propose, explain and request capabilities

Engineering tools
  calculate, simulate, build or inspect

Evidence
  records what ran, with what inputs, assumptions and limitations
```

The central rule is:

> **AI output is not canonical state, and numerical output is not automatically accepted engineering truth.**

## AI and authority

![JarvisOS AI authority flow](docs/assets/readme/ai-authority.svg)

Provider calls, local models and future agent runtimes remain below JarvisOS-owned routing, policy, credential, budget and egress controls.

A model response can create a proposal or request a capability. Durable domain state is intended to change only through the accepted domain owner and its validation/reconciliation path.

## Project knowledge, context and evidence

![JarvisOS control and memory layers](docs/assets/readme/memory-control.svg)

JarvisOS separates several things that are easy to blur together:

| Layer | Meaning |
| --- | --- |
| Canonical Project Basis / engineering records | Accepted project state after an authorized transition. |
| Working revisions / change sets | Proposed or staged edits that are not yet canonical. |
| Runs / artifacts | What actually executed and what files/results it produced. |
| Engineering evidence | Results plus provenance, fidelity, validity and qualification context. |
| Derived search / retrieval | Rebuildable indexes used to find context; not the source of truth. |
| External documents / notes | Sources and working material; not automatically accepted facts. |

The current architecture still contains some legacy mutation debt. Those paths are being forced either through accepted canonical owners/CAS/reconciliation semantics or toward explicit rejection rather than permanent parallel write authority.

## Engineering backends

JarvisOS is intended to make numerical backends replaceable instead of burying engineering logic inside one monolith.

![JarvisOS engineering backends](docs/assets/readme/engineering-backends.svg)

Target pattern:

```text
EvaluationRequest
      ↓
EngineeringEvaluator adapter
      ↓
open-source / custom / commercial specialist backend
      ↓
EvaluationResult
outputs · failures · artifacts · provenance · fidelity · qualification
```

Current and candidate ecosystems include:

| Area | Relationship |
| --- | --- |
| Parametric CAD | **build123d + OCP / OpenCascade** are current dependencies. |
| Meshing | **Gmsh** has a current registry-bound adapter. |
| Static FEM | **CalculiX** has a current registry-bound adapter. |
| Properties / transport | CoolProp, thermo, chemicals and fluids are useful upstream building blocks/candidates. |
| Bio/process simulation | BioSTEAM, QSDsan, IDAES, Pyomo, WaterTAP and DWSIM/CAPE-OPEN are important candidates/references. |
| Optimization | CasADi and OpenMDAO are candidates for study-control work. |
| Higher-fidelity CFD | OpenFOAM is a candidate when cheaper models cannot resolve the engineering decision. |
| Commercial engineering software | Future adapters may connect packages such as Aspen HYSYS or other specialist tools when access and licensing permit. |
| Agent runtimes / tool protocols | Hermes and MCP-style systems are candidates below JarvisOS-owned state/policy boundaries, not replacements for them. |

More candidate/upstream notes live in [`docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`](docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md).

## Current physical-design chain

```text
operator / Jarvis proposal
        ↓
CAD candidate + GeometrySpec
        ↓
build123d / OCP
        ├── STEP / STL / GLB + manifests / digests
        ↓
Gmsh
        ├── mesh + physical groups + quality evidence
        ↓
CalculiX
        ├── solver outputs + parsed result summary
        ↓
SimulationRun + artifacts + typed evidence
        ↓
FastAPI read models → operator UI
```

This is one implemented engineering path, not a claim that every problem should begin with CAD or end with FEM.

## Current process-model reality

The present process/PBR stack should be read as a set of useful experiments rather than a finished simulator:

- productivity is still an input in parts of the biomass/nutrient/harvest path rather than an emergent result of a complete biology/light/transport model;
- the optical path is a bounded transmission proxy, not a full radiation/photosynthesis model;
- the custom process kernel handles bounded acyclic typed calculations and is not a general recycle/nonlinear/ODE/DAE simulator;
- future process work is explicitly being compared against stronger upstream ecosystems before more generic custom solver infrastructure is added.

## Engineering qualification philosophy

A numerical tool is not accepted merely because it is popular, open source or produces a plausible plot.

For real decisions, useful checks may include comparison against:

- analytical solutions;
- trusted engineering correlations;
- literature or experimental data;
- independent numerical implementations;
- established commercial software when a comparison is available and meaningful.

The useful question is:

> **For the decision I need to make, is this model accurate, robust, reproducible, appropriately qualified and traceable enough?**

Provenance is necessary. It is not the same thing as scientific validity.

## Application stack

### Backend

- Python
- FastAPI
- Pydantic
- Pint
- SQLite-backed durable application state
- httpx and explicit provider/runtime adapters
- PyYAML for bounded configuration surfaces

Pinned dependencies: [`backend/requirements.txt`](backend/requirements.txt).

### Frontend

- React 18
- TypeScript
- Vite
- Three.js for 3D engineering inspection

Pinned dependencies: [`frontend/package.json`](frontend/package.json).

### Engineering stack already used in the repository

- build123d / OCP / OpenCascade;
- Gmsh;
- CalculiX;
- bounded process/PBR calculations;
- typed runs, artifacts, manifests, digests and evidence.

An adapter existing in the repository is **not** a claim that its solver has been qualified for every engineering use case.

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
- [`docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`](docs/POST_112_PARALLEL_DELIVERY_PROFILE.md) — current controlled-parallel delivery profile;
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — canonical architecture and known debt;
- [`docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`](docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md) — upstream/candidate audit register.

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

Useful criticism is welcome, especially around:

- photobioreactors, microalgae and biochemical/process systems engineering;
- process modeling, transport phenomena, hydrodynamics and mass transfer;
- scientific Python and numerical methods;
- CAD/CAE, meshing, CFD/FEM and engineering interoperability;
- local AI runtimes, agent infrastructure, sandboxing and tool protocols;
- engineering validation, provenance, cybersecurity and reproducible computational workflows.

A useful contribution is often **not more code**. Pointing out that an existing project already solves a problem better, identifying a bad assumption, finding a validation gap or explaining why an architecture is unnecessarily complicated can be more valuable.

If you want to discuss the project, suggest an upstream, contribute substantially, explore research collaboration or talk about licensing, contact me through GitHub.

---

## Final note

JarvisOS should be judged by what it can actually demonstrate: code that runs, tests that pass for the right reasons, engineering models with known limits, traceable evidence and eventually useful decisions on a real microalgae project.

A polished README is not evidence that those goals have been achieved.
