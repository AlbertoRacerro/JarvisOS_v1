# Engineering Knowledge Unit Guide

## Unit of storage

The stored object is an **Engineering Knowledge Unit**, not a page fragment, exercise, solution step or spreadsheet cell.

A unit must answer:

1. What general engineering problem does this knowledge solve?
2. What is the canonical reusable statement?
3. Which equations, variables, parameters or ordered steps are required?
4. Under which assumptions and validity limits may it be used?
5. How can an engineer verify that it was applied correctly?
6. Which general failure modes must be guarded against?
7. Which BlueRev subsystem and decision can use it?
8. What business effect can follow from using it correctly?

## Allowed knowledge types

- `concept`
- `physical_law`
- `equation`
- `mechanistic_model`
- `empirical_correlation`
- `algorithm`
- `engineering_procedure`
- `control_strategy`
- `architecture_pattern`
- `verification_method`
- `economic_method`
- `business_strategy`
- `parameter_set`

## Knowledge strength

- `fundamental`: conservation law or mathematical identity.
- `mechanistic`: derived model tied to physical assumptions.
- `empirical`: correlation or fitted relation with a validity domain.
- `procedural`: ordered engineering workflow.
- `architectural`: allocation of responsibilities and interfaces.
- `decision_method`: strategy for selecting actions under objectives and constraints.
- `frontier_hypothesis`: promising direction not yet mature enough for automatic retrieval.

## Granularity

Create a separate unit when at least one of these changes independently: governing model, assumptions or validity range, algorithm and convergence rule, engineering decision supported, verification method, control authority, or business decision logic.

Do not create separate units merely because a different exercise, document or notation uses the same general method.

## Example transformation

Source-specific material: a spreadsheet computes a tube-side Reynolds number for one exchanger.

Canonical stored knowledge: internal-flow Reynolds number requires density, viscosity, velocity and characteristic diameter defined for the same fluid and compatible thermodynamic state. Its value determines the applicable flow-regime correlations.

The spreadsheet values remain only in temporary QA if needed to verify the extraction.

## Parameters and constants

A reusable parameter set may be stored only when it includes substance/material/organism scope, equation convention, numerical value and uncertainty where available, units and basis, validity range, provenance and verification status. A one-off value chosen for an exercise is not reusable knowledge.

---

# Source and Evidence Policy

Sources provide evidence and provenance. Authority labels do not automatically make a statement true.

Preferred source order:

1. international standards and regulator documents;
2. primary peer-reviewed research;
3. reproducible benchmarks and mature open-source implementations;
4. patents and official technical reports;
5. vendor documentation for implementation details;
6. course material and textbooks for foundations;
7. internal BlueRev working hypotheses.

Evidence levels:

- `normative`: standard or regulatory requirement;
- `primary_validated`: primary work with relevant experimental or field validation;
- `primary_preprint`: recent primary research not treated as settled;
- `course_foundation`: educational source requiring independent checks for important claims;
- `working_hypothesis`: provisional BlueRev method, never sufficient by itself for promotion.

A unit may enter retrieval only when canonical knowledge is generic and source-agnostic, assumptions/applicability/invalidity/failure modes are explicit, verification status meets the threshold, confidence is at least 0.8, unresolved questions are empty, and frontier/internal hypotheses are not presented as established knowledge.

Licensed standard text is not copied. Standard identifiers define research directions; conformance requires checking the applicable official edition and implementation.

Recent papers may identify valuable directions such as EMPC, proactive digital twins or equation-free structural twins. They are candidate evidence, not automatic proof of maturity, transferability or economic value for BlueRev.

---

# QA Fixture and Benchmark Policy

The canonical store contains generic reusable knowledge only.

A temporary QA workspace may contain original exercise data, spreadsheet formulas and cell lineage, reproduced calculations, rejected interpretations, source defects and runtime logs. These exist only to decide whether a generic unit is correct and complete.

A benchmark store contains prompts, fixtures, solutions and grading evidence and remains isolated from reference retrieval.

Non-cheating rules:

- never derive the expected answer from the model output being tested;
- never enlarge tolerance after observing a failure without independent physical justification;
- never delete a failed assertion merely to obtain a green report;
- never copy a source result into canonical knowledge without reproducing or independently supporting it;
- keep `not_run`, `withheld`, `failed` and `passed` distinct;
- a structurally valid record is not automatically technically verified.

---

# BlueRev Engineering Research Radar v1

## P0 — foundation required now

| Track | Knowledge objective | BlueRev decision unlocked | Current state |
|---|---|---|---|
| Dynamic process model | Coupled mass, energy, growth, gas-transfer and harvest dynamics | Define the first process twin and experimental states | Foundations partly verified; BlueRev model not calibrated |
| Measurement and identifiability | Sensor selection, soft sensors, excitation and parameter identifiability | Decide which sensors and experiments are worth buying | Candidate |
| Layered DCS-like automation | Field protection, regulatory control, supervision and optimization boundaries | Define prototype-to-fleet control architecture | Architecture retrieval-ready; BlueRev hazard logic missing |
| Interlocks and alarms | Cause-effect logic, permissives, degraded modes | Prevent biomass and equipment-loss events | Candidate |
| Contextualized time series | Signal identity, unit, quality, configuration and lineage | Make prototype data reusable for digital twins and fleet learning | Retrieval-ready |
| Smart Joint semantic interface | Capabilities, commands, states, diagnostics and energy data | Standardize replaceable modules | Retrieval-ready |
| Offshore design basis | Environmental load envelope, operating/survival states, fatigue cases | Avoid optimizing against one nominal sea state | Candidate |
| Design-to-cost modularity | Allocate cost, lifetime and serviceability across tubes and Smart Joints | Shape product architecture and supplier strategy | Candidate |
| Value of information | Rank experiments by decision impact | Spend prototype budget on the uncertainties that matter | Candidate |
| Real-options stage gates | Reversible learning before irreversible capital | Sequence prototype, pilot and commercial commitments | Candidate |

## P1 — pilot and scale-up advantage

| Track | Direction | BlueRev use | Maturity treatment |
|---|---|---|---|
| MPC and EMPC | Constraint-aware coordinated control under weather disturbances | CO2, DO, harvest/dilution and thermal optimization | Selection logic ready; BlueRev EMPC candidate |
| Lifecycle digital twins | Separate design, commissioning, operational, maintenance, economic and fleet twins | Avoid a monolithic dashboard called a twin | Architecture retrieval-ready |
| Online state/parameter estimation | Fuse models and measurements with uncertainty | Biomass, fouling and transfer-state estimation | Candidate |
| Reduced-order structural twins | High-fidelity FEM to online surrogate and virtual sensing | Fatigue and inspection planning | Frontier hypothesis, withheld |
| Dynamic economic potential | Dynamic TEA plus uncertainty, degradation and option value | Value cleaning, harvest timing, sensing and design changes | BlueRev working hypothesis, withheld |
| Fault-tolerant automation | Detection, isolation and bounded degraded operation | Offshore autonomy with imperfect sensors | Candidate |
| Fleet learning | Versioned configuration plus cross-module validation | Compounding operational IP | Frontier hypothesis, withheld |

P2 includes downstream product switching, automated quality-by-design, certification evidence, lifecycle assessment, manufacturing automation and commercial optimization across products/sites/contracts.

Each track must produce generic units, assumptions and invalidity, a BlueRev decision map, required experiments/models, an economic consequence, maturity label and evidence class. The radar is not a feature wishlist: a direction advances only when it changes a concrete engineering or investment decision.

---

# Research Source Notes

Microalgae control directions use arXiv:2512.15668 for EMPC, arXiv:2512.15916 for a coupled outdoor control benchmark and arXiv:2410.08575 for dynamic optimization evidence. None is treated as BlueRev field validation.

Modular automation uses ISA-95/IEC 62264 for functional boundaries, IEC 62541/OPC UA for interoperability direction, IEC 63278/AAS for standardized asset representation and MTP capability/energy semantics papers for Smart Joint contracts.

Digital-twin directions use arXiv:2310.03761 for contextualized process time series and ISO 23247 as a reference-architecture direction, not as a complete marine-bioprocess solution.

Structural twin and offshore papers identify reduced-order, sparse virtual-sensing and load-modeling directions only. No source validates a BlueRev structure.

Value of information, real-options gates, design-to-cost and dynamic economic potential connect engineering evidence to investment. `Dynamic economic potential` is explicitly a provisional BlueRev framework, not a recognized standard term, and remains withheld.

---

# Roadmap

## Phase 1 — ontology foundation

Define generic units, exclude case-specific results, seed foundations and state-of-the-art directions, and withhold frontier/internal hypotheses. Status: draft foundation, not production-approved.

## Phase 2 — adversarial source pilot

Use 40–60 representative sections across bioprocess, controls, transport, hydraulics, FEM/offshore mechanics and techno-economics. Extract generic units only and measure duplicate consolidation, unsupported claims, assumption/validity completeness and independent-review disagreement.

## Phase 3 — BlueRev decision map

Link each unit to subsystem, design variable, pending decision, uncertainty, experiment, model/tool, CAPEX/OPEX/reliability effect and project stage gate. Priority follows decision leverage, not document order.

## Phase 4 — state-of-the-art research program

For every P0/P1 track, identify standards, primary papers, benchmarks and mature open-source implementations; distinguish industrial patterns from hypotheses; reproduce relevant methods where possible; define BlueRev adaptation and validation.

## Phase 5 — storage and retrieval

Only after the unit model survives the pilot: build the canonical store, provenance/versioning, semantic deduplication and relation graph; expose only eligible units; keep QA and benchmark stores separate.

## Phase 6 — benchmark factory

Generate tests for formula/unit application, model selection, assumptions, algorithm design, control/architecture choices, diagnosis and economic reasoning. Specific numerical cases belong here, not in memory.

Do not map the full corpus or wire normal JarvisOS retrieval until independent review, a representative generic-extraction pilot, ontology stability, strict promotion and a working BlueRev decision map exist.

---

# Supersedes the Microtopic/Exercise-Centric Approach

The previous pilot treated page fragments, worked calculations and spreadsheet details as candidate microtopics. That approach is superseded.

The new object is a reusable Engineering Knowledge Unit: a formula with assumptions/validity; a model with states/boundaries/verification; an algorithm with initialization/convergence; a procedure or strategy with decision logic; an architecture pattern with authority/interface boundaries; or an economic method connected to enterprise decisions.

Course files remain evidence and QA fixtures. They no longer determine database granularity. Many exercises may support one canonical unit and one exercise may support several units. No unit exists merely because a source contains another numerical example.

Previous records migrate only when generic content can be extracted without retaining case-specific inputs or outputs; otherwise they remain QA or benchmark material.
