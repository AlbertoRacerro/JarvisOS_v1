# BlueRev Engineering Priority Amendment — Process First

Status: **PLANNING AMENDMENT ONLY — NOT `STATUS.md`, NOT IMPLEMENTATION AUTHORITY**

Prepared: 2026-08-21

Repository base observed for this amendment: exact `master` `2b4d1ce347561ac38970f07d7ef2407ad185dddc`.

Active runtime front observed separately at authoring time: PR #319, `Implement SCENE-SEMANTICS-A1`; this amendment does not modify that PR, its branch, runtime code, specs, or `docs/specs/STATUS.md`.

Related planning documents:

- `JARVISOS_BACKEND_PUZZLE_STRATEGY_2026-08-21.md`
- `JARVISOS_BACKEND_PUZZLE_QUEUE_BLUEPRINT_2026-08-21.md`

## 0. Purpose and precedence

The existing backend-puzzle queue blueprint correctly identified that JarvisOS already has a much more mature CAD/mesh/FEM path than its broader process-engineering stack. That implementation asymmetry can create the wrong product interpretation: a reader or future agent may infer that BLUECAD/CAD is the primary BlueRev engineering objective simply because it is currently the most developed engineering path.

That inference is wrong.

**Implementation maturity must never be used as a proxy for BlueRev product priority.**

This amendment therefore changes the **engineering-priority interpretation and future planning order** of the backend-puzzle blueprint wherever the older document implies that CAD/Gmsh/CalculiX qualification is the highest-priority BlueRev engineering outcome.

Where this document conflicts specifically with the engineering-priority ordering in sections 0, 4, 7, 8, 10, 12, or 13 of `JARVISOS_BACKEND_PUZZLE_QUEUE_BLUEPRINT_2026-08-21.md`, this amendment is the newer planning interpretation.

It does **not** supersede:

- `docs/specs/STATUS.md` as the sole live queue authority;
- the current functional queue;
- the global visual-identity ordering;
- Jarvis authority/egress/state/provenance rules;
- the evidence that BLUECAD, Gmsh, CalculiX, the deterministic runner, and the CAD-to-FEM path already exist and should be reused rather than rebuilt.

No runtime work is authorized by this file.

---

# 1. Correct BlueRev engineering priority

The intended BlueRev engineering hierarchy is:

1. **P1 — integrated photobioreactor process simulation**;
2. **P1b — process design and optimization**;
3. **P2 — physical design / CAD realization**;
4. **P2b — mesh, CFD/FEM, structural/manufacturing verification where required**;
5. **domain-specific Engineering Qualification Suite on real BlueRev cases**;
6. **Design Explorer over qualified BlueRev-relevant evaluators**;
7. advanced generative engineering, surrogates, active learning, and training only after measured demand.

The CAD path is currently more mature in JarvisOS. That is an implementation fact, not the BlueRev priority order.

The primary engineering question is not initially:

> What geometry should BLUECAD draw?

It is:

> What photobioreactor process and operating/design envelope gives the best biologically viable, hydraulically feasible, energy-aware BlueRev outcome?

Only after that process question is sufficiently constrained should BLUECAD turn the selected process design into a physical object.

---

# 2. P1 — Integrated photobioreactor process simulation

Primary future disposition: existing process/hydraulic foundations **KEEP / HARDEN / EXTEND**; missing BlueRev-specific biological/process capabilities **BUILD / QUALIFY** only through the existing Jarvis run/evidence authority.

P1 is the first major BlueRev-specific engineering capability to establish once a usable JarvisOS beta exists and the repository's current authorized product work has completed.

The target is an integrated, inspectable process model that can progressively combine the phenomena that actually determine photobioreactor performance. The model need not begin with maximum fidelity in every subsystem; lower-cost deterministic models are preferred until a named decision requires a higher-fidelity backend.

P1 scope can include, as required by real BlueRev cases:

### Biology and productivity

- microalgal growth kinetics;
- biomass productivity and concentration;
- substrate/nutrient limitation where relevant;
- biological inhibition mechanisms;
- coupling between biological state and operating conditions;
- explicit validity domain, assumptions, parameters, provenance, uncertainty, and model version.

### Light and photosynthetic response

- incident irradiance and light availability;
- spatial or reduced-order light distribution;
- attenuation/absorption through the culture;
- self-shading effects when relevant;
- light limitation;
- photoinhibition;
- light/dark cycling produced by circulation and mixing when the selected model requires it;
- coupling between optical conditions and biological productivity.

### Hydrodynamics and mixing

- circulation and mixing behavior at the fidelity needed for the decision;
- characteristic mixing/recirculation times;
- residence-time or exposure-time metrics when useful;
- dead/stagnant regions where a model can resolve them;
- velocity-related biological constraints;
- shear stress and shear exposure relative to algal tolerance;
- effects of baffles, static mixers, loop topology, or similar design features when they materially change the process.

### Gas-liquid transfer and aeration

- CO2 delivery and utilization;
- oxygen generation and removal/stripping;
- gas-liquid mass transfer;
- `kLa` or equivalent mass-transfer metrics when appropriate;
- air/CO2 flow requirements;
- gas composition and injection strategy where relevant;
- process limitations caused by dissolved gases.

### Nutrients and operating control

- nutrient dosing and consumption where required;
- pH and pH-control demand where required;
- temperature and thermal-control demand where required;
- other operating constraints that materially affect productivity or viability.

### Hydraulics and energy

- pressure drop through the selected process topology;
- pump head and pumping power;
- compressor/blower demand where gas delivery requires it;
- energy consumption associated with circulation, aeration, temperature control, or other required auxiliaries;
- specific energy consumption and relevant energy/productivity trade-offs.

### Integrated outputs

The process layer should eventually be able to produce bounded, evidenced quantities such as:

- volumetric and/or areal productivity;
- biomass production rate;
- viable operating envelope;
- limiting mechanism(s);
- light-use metrics;
- shear constraint margin;
- gas-transfer constraint margin;
- pressure drop;
- pump/compressor power;
- nutrient and gas demand;
- specific energy consumption;
- efficiency/yield metrics relevant to BlueRev;
- confidence/qualification/validity status for every reported result.

This is a roadmap target, **not a claim that these capabilities are already implemented**.

---

# 3. Fidelity ladder: do not jump directly to CFD

P1 is process-first, not CFD-first.

Use the cheapest model that can resolve the current engineering decision while preserving its validity boundary and evidence. A possible escalation pattern is:

```text
analytical/correlation model
        |
        v
0D / 1D / compartment / reduced-order process model
        |
        v
validated coupled deterministic model
        |
        v
CFD or other high-fidelity field solver only if the decision remains unresolved
```

CFD is therefore neither an automatic early prerequisite nor an intrinsically late capability. It is activated when mixing, shear, mass transfer, light exposure, baffle behavior, or another named BlueRev question cannot be answered adequately by the cheaper model.

OpenFOAM/SU2 or other external solvers remain replaceable numerical backends under Jarvis evidence and qualification boundaries; they never become canonical engineering truth by themselves.

---

# 4. P1b — Process design and optimization

Primary future disposition: **BUILD / EXTEND** above the P1 evaluator and the existing deterministic runner.

After P1 can evaluate a bounded configuration, the next BlueRev capability is to vary the quantities that define the process and determine a feasible/valuable operating and design envelope.

Candidate variables may include:

- tube internal/outer diameter where physically relevant;
- total tube/reactor length;
- number of loops or parallel paths;
- reactor topology;
- recirculation flow rate;
- local or bulk velocity targets;
- biomass/cell concentration;
- air and CO2 flow;
- gas composition;
- injection location and strategy;
- baffle/static-mixer presence, spacing, or geometry parameters;
- nutrient dosing policy;
- temperature or pH operating targets;
- other real BlueRev operating/design variables exposed by the P1 model.

The governing rule is explicit:

> **Tube diameter, length, flow rate, and reactor topology are first process-design variables and only secondarily CAD parameters.**

The process layer should be able to return a design envelope rather than merely one drawing. Conceptually:

```text
required / feasible tube-diameter range
required total length / active volume
nominal and allowable recirculation flow
maximum allowable shear / shear exposure
maximum allowable pressure drop
pumping/compression power constraint
CO2-transfer requirement
O2-removal constraint
gas-flow range
nutrient/thermal/control requirements
productivity target and trade-offs
qualification / uncertainty / validity information
```

These outputs become requirements and constraints for the physical-design layer.

---

# 5. P2 — Physical design / BLUECAD

Primary disposition: current BLUECAD semantic CAD **KEEP / HARDEN / EXTEND**.

BLUECAD is priority #2 for BlueRev, not because it is unimportant, but because it should realize a process design rather than silently choose the process physics by itself.

Once P1/P1b provide a process envelope, BLUECAD can determine how to make it physically real:

- spatial arrangement and packaging;
- number and routing of serpentine/loop elements;
- bend radii;
- manifolds and collectors;
- injection and sampling interfaces;
- baffle/static-mixer physical realization when selected by process design;
- supports and mounts;
- materials;
- envelope/footprint;
- accessibility;
- maintenance and cleaning constraints;
- manufacturability;
- interfaces with pumps, gas delivery, sensors, harvesting, and other equipment;
- geometry necessary for later structural/field verification.

The handoff is therefore:

```text
P1 integrated process evaluator
        |
        v
P1b process design / feasible envelope
        |
        v
engineering requirements + constraints
        |
        v
P2 BLUECAD physical realization
```

BLUECAD may expose geometry variables back to P1/P1b when geometry changes process behavior, but the coupling must remain explicit and typed rather than turning CAD geometry into hidden process authority.

---

# 6. P2b — Mesh, CFD/FEM, and manufacturability

The existing JarvisOS path:

```text
GeometrySpec
   -> build123d / OCP
   -> STEP / STL / GLB + manifests
   -> registry-bound Gmsh
   -> mesh / groups / quality evidence
   -> registry-bound CalculiX
   -> FRD / DAT / parsed results
   -> simulation runs / typed evidence
   -> frontend inspection
```

is an incumbent to **KEEP / QUALIFY / HARDEN / EXTEND**, not rebuild.

Target-host Gmsh/CalculiX qualification remains useful operational work, but it must not be mistaken for the primary BlueRev engineering objective merely because that pipeline already exists.

Structural FEM, CFD, thermal, or other field analyses enter when the physical or process decision requires them. Their results remain evidence attached to an explicit evaluator and exact tool/version/platform identity.

---

# 7. Correct future sequence

The current functional queue and global visual-identity phase remain ahead of this engineering expansion. The planning order becomes:

```text
CURRENT AUTHORIZED FUNCTIONAL QUEUE
        |
        v
GLOBAL VISUAL IDENTITY
        |
        v
USABLE JARVISOS BETA CHECKPOINT
        |
        v
FRESH EXACT-MASTER / UPSTREAM REVALIDATION
        |
        v
MINIMUM JARVIS / HERMES / RUNTIME FOUNDATIONS
only where re-derived and authorized
        |
        v
P1 INTEGRATED PHOTOBIOREACTOR PROCESS MODEL
biology + light + mixing/shear + gas transfer
+ nutrients/control + hydraulics/energy
        |
        v
P1b PROCESS DESIGN / OPTIMIZATION
D, L, topology, flow, aeration, operating variables
        |
        v
P2 BLUECAD PHYSICAL REALIZATION
        |
        v
P2b MESH / CFD / FEM / MANUFACTURABILITY
only where required
        |
        v
FIRST REAL BLUEREV ENGINEERING CASES
        |
        v
DOMAIN-SPECIFIC ENGINEERING QUALIFICATION SUITE
        |
        v
DESIGN EXPLORER OVER QUALIFIED BLUEREV EVALUATORS
        |
        v
ADVANCED GENERATIVE ENGINEERING
surrogates / active learning / generative geometry / training
```

The exact runtime sequence is still subject to future re-derivation through `STATUS.md`. This diagram establishes product/engineering priority, not implementation authorization.

---

# 8. Usable beta comes before the scientific qualification program

The Engineering Qualification Suite must **not** become another prerequisite that indefinitely delays a usable JarvisOS beta.

The beta checkpoint means the product can be used end to end: project state, Jarvis interaction, deterministic execution, results/evidence, frontend inspection, and the already implemented engineering paths are sufficiently connected to begin real BlueRev work.

Only after that usable base exists should real BlueRev cases determine which engineering models deserve qualification effort.

The sequence is:

```text
build usable end-to-end beta
        -> use it on a real BlueRev problem
        -> discover the decisions and required evaluators
        -> build/extend the necessary process capability
        -> compare against independent references
        -> qualify the capability for that decision class
        -> widen scope only when another real decision requires it
```

This avoids spending months proving irrelevant chemistry or solver breadth merely because commercial engineering suites support it.

---

# 9. Domain-specific Engineering Qualification Suite

The qualification question is not:

> Is JarvisOS equivalent to every capability of Aspen HYSYS, Fusion, ANSYS, STAR-CCM+, or another industrial suite?

The useful question is:

> **For the engineering decisions BlueRev actually needs to make, are JarvisOS and its selected backends accurate, robust, reproducible, and traceable enough to be useful?**

Qualification therefore follows real BlueRev cases and expands incrementally.

Relevant evidence can include, depending on the model:

- analytical solutions;
- trusted correlations;
- literature data;
- experimental data;
- independent numerical implementations;
- commercial-software comparison when available and meaningful;
- sensitivity/uncertainty studies;
- convergence and failure behavior;
- exact tool/model/version/platform provenance.

Measure more than numerical closeness. Where appropriate also record:

- accuracy/error;
- convergence and stability;
- domain of validity;
- failure detectability;
- reproducibility;
- computational cost;
- operator effort;
- sensitivity to uncertain inputs;
- agreement/disagreement between independent methods.

Do not prioritize validation of benzene systems, refinery flowsheets, combustion, distillation, or any other domain merely to imitate a general commercial simulator when it is unrelated to an actual BlueRev decision.

If a BlueRev problem later needs such capability, qualify it then.

---

# 10. Commercial and open backends are tools, not ideology

JarvisOS remains local-first and seeks to reduce structural dependence on expensive licenses and mandatory external-cloud processing. This must not become an anti-commercial rule.

For a specific engineering decision:

- use a local/open backend when it is sufficiently capable and qualified;
- use a custom deterministic model when it is simpler and more auditable;
- use a commercial solver or simulator when the open/local stack does not meet the required fidelity, robustness, validation, or regulatory/industrial expectation;
- preserve JarvisOS state, provenance, evidence, and workflow around whichever backend is selected.

A future commercial adapter is therefore not an architectural failure. Vendor independence means the Jarvis environment is not owned by one solver vendor; it does not mean every solver must be free or local in every case.

---

# 11. Design Explorer must begin with process design, not shape generation

The first high-value BlueRev Design Explorer use case should not be:

> generate hundreds of CAD shapes

It should be closer to:

> maximize useful biomass/productivity while respecting biological shear, dissolved-gas, pressure-drop, energy, operating, and other BlueRev constraints by exploring process variables such as diameter, length, topology, recirculation, aeration, and operating conditions.

The first process-centric flow is:

```text
biological + light + transport + hydraulic/energy model
        |
        v
DesignStudy
variables + bounds + objectives + constraints
        |
        v
DOE / optimizer
        |
        v
bounded deterministic process candidates
        |
        v
productivity / shear / gas transfer / dP / energy / feasibility
        |
        v
reproducible feasible / Pareto process designs
        |
        v
selected process design envelope
        |
        v
BLUECAD physical realization
        |
        v
higher-fidelity CFD/FEM/manufacturing checks where required
```

An AI model may propose the study and explain results. Deterministic code owns units, candidate generation, evaluation, constraints, failure classification, Pareto logic, and evidence.

A surrogate may later screen/propose candidates, but an authoritative qualified evaluator verifies engineering acceptance.

---

# 12. Design Explorer entry gate correction

The older blueprint says Design Explorer may begin once at least one deterministic evaluator is qualified. For BlueRev product priority this is too weak: a qualified FEM fixture alone must not make CAD-centric Design Explorer the next engineering milestone.

The BlueRev-specific entry gate is:

- a usable JarvisOS beta exists;
- at least one **BlueRev-relevant process evaluator** is end-to-end reachable;
- its variables, units, outputs, failure modes, provenance, and validity boundary are explicit;
- the evaluator has enough independent qualification evidence for the class of decisions the first study will make;
- the existing runner/evidence/result infrastructure can execute and preserve its candidate evaluations;
- the first study corresponds to a real BlueRev decision.

CAD/FEM may be part of that evaluator when the decision requires them. They are not required merely because those adapters already exist.

---

# 13. Current maturity versus product priority

| Capability | BlueRev product priority | Current repository maturity interpretation | Planning consequence |
| --- | ---: | --- | --- |
| Integrated photobioreactor process simulation | **P1** | Important gap above bounded process/hydraulic foundations | First BlueRev-specific engineering expansion |
| Process design / optimization | **P1b** | Study/DOE/Pareto orchestration is a real gap | Build after a useful P1 evaluator exists |
| BLUECAD semantic/parametric geometry | **P2** | Real incumbent | **KEEP / HARDEN / EXTEND**, do not rebuild |
| Gmsh meshing | P2 support | Implemented/tested adapter; target-host qualification required | **KEEP / QUALIFY / HARDEN** |
| CalculiX FEM | P2 support | Implemented/tested static-FEM path; target-host/workload qualification required | **KEEP / QUALIFY / EXTEND** |
| CFD | P1/P2 support depending on decision | No production CFD path verified | Demand-gated **BUILD / QUALIFY**, not a generic platform milestone |
| Engineering Qualification Suite | after first real BlueRev cases | Partial verification assets exist by subsystem | Grow domain-by-domain from real decisions |
| Design Explorer | after relevant evaluator qualification | Canonical study/batch/Pareto domain absent | Process-first initial use case |
| Surrogates / active learning / generative geometry | later | Research/advanced gaps | Require measured demand and qualified evaluators |

---

# 14. What must not happen

Do not:

- infer BlueRev priority from the amount of code already written in a subsystem;
- make CAD the default first engineering answer merely because BLUECAD is mature;
- rebuild the existing BLUECAD/Gmsh/CalculiX/runner/evidence chain;
- build a generic Aspen replacement before a BlueRev use case requires a missing process capability;
- install a solver portfolio merely to maximize backend count;
- require CFD when a simpler qualified model resolves the decision;
- reject CFD when a real mixing/shear/light/gas-transfer decision demonstrably needs field resolution;
- optimize unqualified outputs at large scale;
- let an LLM's narrative become engineering acceptance;
- validate broad petrochemical/refinery/combustion domains by default when they are unrelated to BlueRev;
- treat local-first as a prohibition on commercial tools when a specific job genuinely needs them.

---

# 15. Implication for the future public README

When the repository README is rewritten as a public front door, it should not introduce JarvisOS engineering through CAD first.

The public explanation should make the process hierarchy visible:

```text
BlueRev process question
    -> biological / light / transport / energy model
    -> process design and constraints
    -> physical CAD realization
    -> mesh / CFD / FEM / verification when required
    -> evidence and iteration
```

It should distinguish clearly between:

- **Working now**;
- **Work in progress**;
- **Planned**;
- **Requires further research/qualification**.

In particular, the integrated photobioreactor capability must not be presented as already working merely because it is product priority #1.

---

# 16. Activation and handoff rule

At any future engineering handoff, the coordinating agent must:

1. fetch fresh exact `master`, `docs/specs/STATUS.md`, active PRs, and checks;
2. respect the current functional/visual-identity/runtime authority before starting engineering expansion;
3. read this amendment together with the backend-puzzle strategy and queue blueprint;
4. distinguish **product priority** from **implementation maturity**;
5. treat integrated photobioreactor process simulation as BlueRev P1 and physical CAD as P2;
6. identify the first real BlueRev decision before selecting process libraries, CFD, optimization, or new solver backends;
7. reuse existing Jarvis state, runner, evidence, BLUECAD, mesh, FEM, frontend, and authority seams;
8. derive exactly one canonical definition/readiness slice through normal `STATUS.md` governance before runtime implementation.

No planning handle or priority label in this document is implementation authority.