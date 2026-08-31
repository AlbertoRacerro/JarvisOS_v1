<h1 align="center">JarvisOS</h1>

<h3 align="center">A personal AI-assisted engineering & R&D workspace</h3>

<p align="center"><strong>One project, one engineering workspace, many AI and simulation tools — with the engineer still in charge.</strong></p>

<p align="center"><code>engineering R&D</code> · <code>AI cowork</code> · <code>local-first</code> · <code>evidence-first</code></p>

---

## What is JarvisOS?

JarvisOS is my attempt to build the engineering workspace I would like to use for real R&D: one place where **project knowledge, calculations, simulations, CAD/CAE, evidence and AI assistants can work around the same project state**.

I come from **chemical engineering, not software development**. The project is also an experiment in a question I find genuinely exciting:

> How far can an engineer with no formal software-development background go today by combining strong AI tools, existing engineering software, careful testing and ordinary engineering common sense?

I am building JarvisOS alone. A lot of the code has been produced with substantial AI assistance. I do not want to disguise that, and I do not want to pretend I have somehow recreated Aspen HYSYS, ANSYS, Claude Code, Hermes Agent or a frontier model by myself.

The interesting part is the **integration**: making good existing tools cooperate inside a traceable engineering workflow instead of living in separate programs, spreadsheets and AI chats.

![JarvisOS high-level architecture](docs/assets/readme/architecture-overview.svg)

---

## Why I started it

The first serious use case is a **microalgae photobioreactor R&D project**. It naturally mixes biology, hydraulics, gas transfer, light, energy, process design, optimization, CAD and eventually higher-fidelity physical verification.

That exposed three practical problems I want JarvisOS to attack:

- **Engineering software is fragmented.** Useful work quickly spreads across spreadsheets, scripts, process simulators, CAD/CAE tools, papers and separate AI conversations.
- **University licenses do not last forever.** I want to keep doing engineering R&D outside the university environment without making the whole workflow depend on software that may become prohibitively expensive. Where open/local tools are good enough, I want to use them; where a commercial specialist tool is genuinely better, JarvisOS should be able to integrate it rather than imitate it badly.
- **Real R&D data can be sensitive.** Company data, unpublished research, designs and IP should not automatically leave the machine just because an AI assistant is useful. JarvisOS is therefore local-first and treats external AI use as a deliberate, policy-controlled data-egress decision.

The goal is not “cloud bad” or “commercial software bad”. The goal is **choice, interoperability and control**.

![Microalgae photobioreactor design loop](docs/assets/readme/photobioreactor-process-loop.svg)

---

## What the application looks like today

JarvisOS already has a working **React/TypeScript operator workstation** rather than only backend experiments.

The current frontend brings the main project surfaces into one application: Design/Process work, Results and Lineage, Engineering Data, Runs, Review, Memory, Development, Coding and Settings. A persistent **Jarvis sidecar** provides contextual AI interaction next to the engineering work instead of in a disconnected chatbot tab.

Some surfaces are already backed by real domain authority; others are deliberately present as honest scaffolds while their backend capabilities are still being built. Missing functionality is meant to stay visibly unavailable rather than be faked in the UI.

BLUECAD already provides a real 3D engineering path with parametric geometry and inspection, while the Process workspace is intentionally earlier in its evolution.

---

## AI: routing, egress and orchestration

JarvisOS is **not tied to one model or one AI provider**.

Today, product AI requests already pass through a JarvisOS-owned execution layer that handles provider routing, local/external execution boundaries, fallback rules, usage and budget accounting, context selection and external-data policy.

For an external call, the system can build an explicit bounded context packet, apply sensitivity and sanitization rules, account for projected spend and preserve provenance of what was actually disclosed. Provider credentials stay outside normal frontend state. `route_class="auto"` remains local-only; external execution requires the accepted server-side path and policy.

In short:

```text
project context
      ↓
JarvisOS policy · sensitivity · budget · routing
      ↓
local model
   or
approved external provider
```

### Where Hermes fits

I am particularly interested in **Hermes Agent** because it already tackles things I do not want to rebuild unnecessarily: agent loops, delegation, sub-agents, tool use and MCP integration.

The future idea is not:

```text
JarvisOS → rebuild Hermes
```

but closer to:

```text
JarvisOS
  owns project state · context · policy · credentials · egress · budget
        ↓
Hermes / another qualified orchestrator
  reasons · delegates · coordinates approved tools
        ↓
engineering and software capabilities
```

Hermes is **not integrated as a production runtime today**. The older Hermes designs are intentionally frozen. After the Coding/Development foundations and Jarvis coding actions are in place, I want to re-evaluate Hermes from the then-current architecture, together with MCP and any other strong orchestration approaches that are worth testing.

If Hermes proves to be the right runtime, I would rather integrate it behind JarvisOS-owned boundaries than maintain a weaker home-made agent framework. The same rule applies to future model routers, agent runtimes and tool protocols: **evaluate strong upstream projects first; integrate what survives testing.**

---

## One roadmap: from today to the full R&D loop

This is the development direction at a glance. The exact live spec state changes frequently; [`docs/specs/STATUS.md`](docs/specs/STATUS.md) is the canonical queue.

| Stage | Direction |
| --- | --- |
| ✅ **Working foundation** | Operator workstation, Jarvis sidecar, Project Basis/change sets, typed engineering records and provenance, runs/evidence, AI provider gateway and egress controls, BLUECAD parametric CAD, Gmsh meshing, CalculiX static FEM, CAD → mesh → FEM evidence path. |
| 🔧 **Architecture hardening — current focus (127–134)** | Close legacy write and egress side-channels, harden runner determinism, unify first error contracts, ratchet typing, generate selected frontend contracts and make merge governance mechanically verifiable. |
| ⏳ **Project knowledge & R&D workspace (113–126)** | Model dossiers, literature/provenance, project search, roadmap/calendar, brainstorm capture, repository/runtime truth, inspectable development pipeline, Jarvis knowledge/development/coding actions, generic provider settings and separately gated safe update/terminal capabilities. |
| ⏳ **Agent-runtime evaluation** | After the Coding foundations: fresh Hermes V1 evaluation/re-derivation, bounded MCP/tool access, model passthrough and comparison with other useful orchestration approaches while JarvisOS retains authority over project state, policy, credentials, egress and budget. |
| ⏳ **Common engineering evidence (102)** | Generalize the evidence contract only as much as replaceable engineering evaluators actually need. |
| ⏳ **Process-software bakeoff (103)** | Re-evaluate the current custom process stack from zero against projects such as **IDAES/Pyomo/WaterTAP, BioSTEAM/QSDsan, DWSIM/CAPE-OPEN, CasADi/OpenMDAO** and property libraries. Keep, wrap, replace or delete based on evidence rather than sunk cost. |
| ⏳ **Selected process stack + common evaluator (104–106)** | Remove duplicated generic solver infrastructure, clean the engineering boundary and define a common typed interface for process/CAD/CAE/CFD/commercial backends without pretending all solvers are the same. |
| ⏳ **Integrated photobioreactor evaluator (107)** | Combine the selected upstream stack with the BlueRev-specific biology, light, mixing/shear, gas transfer, hydraulics, controls and energy equations that are actually needed. |
| ⏳ **Design studies & optimization (108)** | DOE/optimization/search over reproducible evaluator results, feasibility and Pareto state; Jarvis stays in the outer interpretation and engineering-decision loop. |
| ⏳ **Process → CAD handoff (109)** | Turn process-driving geometry, flows and constraints into an explicit typed handoff to detailed CAD instead of letting CAD silently become process-design authority. |
| ⏳ **Multi-fidelity engineering (093/110)** | Escalate from analytical/reduced-order models to CFD, FEM and specialist/commercial software only when higher fidelity can materially change the decision. |
| 🎯 **Target** | A complete microalgae R&D loop where the engineer and AI assistants can explore a design, run the right level of simulation, compare alternatives, inspect evidence, update the project basis and move from process decisions toward physical design inside one coherent workspace. |

The exact tools in the future stack are intentionally **not predetermined**. If an established upstream project solves a generic problem better, I want JarvisOS to use it. If a commercial package such as Aspen HYSYS or another specialist environment is the right tool and licensing permits it, the long-term architecture should be able to connect it too.

---

## The vision

The end goal is a kind of **engineering coworking desk**.

I want to be able to work on a real R&D question and have several useful forms of intelligence around it: an AI that can challenge an assumption, another that can inspect code or literature, numerical tools that can calculate or simulate, CAD/CAE tools that can verify the physical design, and one project memory that keeps the assumptions and evidence connected.

I sometimes describe the AI side as having colleagues, friends or specialists available to discuss the project with. That is a workflow metaphor, not a claim that an LLM is a qualified engineer or that its answer carries authority.

The engineer remains responsible for the engineering decision. JarvisOS should make that decision **better informed, easier to reproduce and less fragmented**.

---

## Interested in collaborating?

Yes — very much.

This is still a personal experimental project, and that is exactly why outside expertise is valuable. I would be interested in hearing from:

- software developers and AI/agent engineers;
- chemical, process, mechanical, control and other engineers;
- researchers and professors working on simulation, optimization, bioprocesses or engineering software;
- people interested in open/local scientific-computing ecosystems;
- companies or engineers with real R&D workflow problems worth testing against;
- investors or builders interested in where AI-assisted engineering tools could realistically go.

If the idea is interesting, if you see a technical mistake, or if there is a tool/project I should evaluate instead of rebuilding something myself, **open an issue or contact me through GitHub**.

I am not looking to pretend the project is more mature than it is. I am interested in making it genuinely better.

---

## For technical readers

Start here instead of using this README as technical authority:

- [Live implementation/spec queue](docs/specs/STATUS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Agent execution and repository-development protocol](docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md)
- [Candidate integrations / upstream projects](docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md)
- [Work-item specifications](docs/specs/README.md)

Current core stack: **Python + FastAPI + SQLite** on the backend; **React + TypeScript + Vite + Three.js** on the frontend; **build123d/OCP/OpenCascade**, **Gmsh** and **CalculiX** in the current physical-design chain.

---

## License

This repository is publicly **source-available for inspection and evaluation**, but JarvisOS is **not currently distributed under an open-source software license**. Unless written permission says otherwise, the code remains all-rights-reserved.

Discussion, critique and collaboration are welcome; public availability should not be interpreted as permission to redistribute the code, create derivative products or reuse it in another product without permission.
