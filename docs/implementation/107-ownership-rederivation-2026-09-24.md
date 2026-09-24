# 107–110 ownership re-derivation after DWSIM whole-engine evidence — 2026-09-24

Status: Frontier Coordinator implementation decision under the 2026-09-24 maintainer scheduling/architecture directive. Evidence base: [103 DWSIM whole-engine qualification](../specs/103-dwsim-whole-engine-qualification-2026-09-24.md), 103/104 bakeoff and strangler evidence, merged 014/102/106 contracts. This does not change STATUS dependencies or accepted spec outcomes; it fixes *where* each capability lives so 107 does not grow generic process infrastructure.

## Governing rule

DWSIM 10.2.9 is the preferred complete generic process-engine hypothesis: flowsheet, streams/connectivity, thermodynamics/flash, unit operations, recycle, pumps/valves/tanks/HX/reactors/controllers, steady state, dynamics where qualified, persistence, native desktop editing and headless execution. It stays intact behind a narrow replaceable adapter; Jarvis does not re-implement or cherry-pick its internals. Jarvis owns project/evidence/qualification/study authority, policy, provenance and promotion. Native DWSIM IDs, session IDs and case files are case-local references, never canonical Jarvis identity. Every adapter write is followed by authoritative read-back; an MCP `ok: true` is never convergence authority while `findings`/blockers, uncalculated objects or balance residuals remain.

107 is the **scientifically tracked BlueRev/PBR delta**: organism, light, gas transfer, nutrients, floating-PBR environment coupling, harvest/storage behaviour. It must not add custom stream, flowsheet, recycle, generic thermodynamics, generic equipment or a generic dynamic integrator.

## BlueRev delta placement

| Capability | Placement now | Evidence / reason | Later path |
| --- | --- | --- | --- |
| *N. gaditana* growth (light, temperature, nutrient, loss) | 107 external `EngineeringEvaluator` (`bluerev.pbr_day_night`), CVODE via SUNDIALS as sole time/state owner | Biology needs versioned, qualification-tracked equations and a stiff integrator; DWSIM CustomUO runs IronPython `ScriptText` (no NumPy/SUNDIALS), custom-unit dynamic integration and blank-case MCP creation are unproven | DWSIM CustomUO wrapper for **steady** flowsheet coupling only after blank-case creation and energy closure are proven; same model version, no second copy of the equations |
| Nutrient uptake, O2 production/degassing | 107 evaluator (coupled to the biology state) | Source terms share the biomass state; splitting them would create two time owners | CO2/pH/carbonate — DEFERRED to 107 follow-up with sourced chemistry (NeqSim/`thermo` reference), recorded as model gap |
| Irradiance, optical attenuation | 107 evaluator (Beer–Lambert depth-averaged) | BlueRev-specific; no upstream process engine owns it | Circular/multi-side/diffuse geometry — DEFERRED to 107 follow-up; optical CFD/ray methods — 110 |
| Solar angle, weather | `EnvironmentalScenario` input to 107 (prescribed diel PAR/temperature) | Scenario data, not process state; no qualified weather source yet | Weather/solar data backend (e.g. pvlib + dataset) — DEFERRED to 108 study inputs with source provenance |
| Seawater heat exchange, floating-hull heat balance | Generic HX/seawater properties → DWSIM (Seawater IAPWS-08, HeatExchanger); BlueRev boundary terms (sea-contact, solar absorption) → 107 | Generic equipment/properties belong to the engine; BlueRev boundary conditions are the delta. Currently a recorded model gap (prescribed temperature) | Heat balance in 107 evaluator with CoolProp/DWSIM seawater reference checks; qualify against measured data |
| Loop hydraulics, pumps, valves | 104 `fluids`/CoolProp screening evaluators consumed by 107 (reuse, no new code); plant hydraulics → DWSIM flowsheet | 107 reuses existing evaluators; generic network hydraulics is engine work | DWSIM pump/pipe/valve case with read-back in the 107 DWSIM adapter |
| Harvest / replenishment | Schedule semantics in the time owner of the run: 107 evaluator (reduced model) or DWSIM events/schedules (plant model) | DWSIM event/schedule/state restore proven on one sample; never both engines in one run | Plant-level harvest splitter/tank in DWSIM; biology exchanged by co-simulation with explicit state handoff (108/110) |
| Wet biomass storage | Tank/holdup → DWSIM; degradation kinetics → 107 | No sourced degradation data | DEFERRED (model gap `storage`); no invented parameters |
| Controls | Plant PID → DWSIM (actuation proven, effectiveness **not** proven); advanced/MPC → do-mpc/CasADi | One time owner per run | Pressure-flow-qualified BlueRev control case — DWSIM adapter follow-up; MPC — 108 |
| Studies, DOE, optimization, Pareto | 108 study controller over evaluator results | Outer loop, not a process engine | OpenMDAO/Pyomo where justified |
| Mixing, wave/passive mixing, CFD | 110 via 014 OpenFOAM adapter | Native CFD semantics must be preserved | Qualified PBR domain case — 110 |
| Structural/geometry | 109 handoff to BLUECAD, Gmsh/CalculiX owners | CAD never becomes process authority | — |
| Reference/validation backends | BioSTEAM/ThermoSTEAM, CoolProp, ChEDL, NeqSim, QSDsan/WaterTAP | Independent checks keep value even when DWSIM owns the generic graph | 107/110 comparison fixtures |

## Time/state ownership

Exactly one owner per dynamic run: the 107 CVODE evaluator for the reduced PBR model; DWSIM dynamics for a plant flowsheet run. Coupling the two is co-simulation with an explicit state handoff (FMI/FMPy candidate, 110), never a shared mutable state.

## Consequences for 108–110 and 149

- 108 treats DWSIM cases and 107 evaluators as peers behind the 106 evaluator boundary; it owns study reproducibility, not process semantics.
- 109 emits a `ProcessDesignEnvelope` from study evidence; DWSIM case hash + native IDs are provenance, not design authority.
- 110 escalates fidelity (107 reduced → DWSIM plant → OpenFOAM/CalculiX) carrying validity/qualification envelopes.
- 149 renders a read-only, revisioned projection of the DWSIM case (native ID/tag/type, ports and connector records, geometry, editable property IDs/units, solved values, findings, dynamic schedules/states/controllers, custom-unit identity, case hash/version) and edits only through typed adapter commands with expected-revision CAS and read-back. The frontend never owns a second flowsheet graph.

## Upstream capability completeness

| Capability | Disposition |
| --- | --- |
| DWSIM flowsheet, streams, thermo/flash, units, recycle, steady solve, persistence | INTEGRATED as target owner via the 107 DWSIM adapter boundary (hash-pinned stdio MCP, read-back, findings/balance checks); production case coverage grows per BlueRev case |
| DWSIM dynamics, events, named states | INTEGRATED for adapter read/run with time-series-derived timing; pressure-flow-qualified initialization DEFERRED to 107 DWSIM follow-up |
| DWSIM PID/controllers | DEFERRED — actuation proven, process-level effectiveness unproven; qualified control case owed by 107 DWSIM follow-up |
| DWSIM CustomUO / Python Script | DEFERRED — load/edit/persist proven; blank-case creation (MCP refuses) and dynamic support unproven; Automation API / upstream MCP addition probe owed |
| DWSIM CAPE-OPEN | DEFERRED to adapter follow-up; compatibility unproven |
| DWSIM desktop editor | INTEGRATED as expert/debug interface on the same case file (round trip proven); not required for ordinary Jarvis operation |
| DWSIM MCP complete connector graph / property-package identity / full property schema | DEFERRED to Automation/XML-backed adapter or upstream repair before 149 projection |
| DWSIM TEA/LCA, Plus-only features | DEFERRED to 108 comparison; GPL core only assumed |
| BioSTEAM/ThermoSTEAM | DEFERRED to 107/108 as alternative bioprocess/TEA evaluator and reference; never co-owning DWSIM state |
| SUNDIALS CVODE (sksundae) | INTEGRATED — 107 evaluator time/state owner |
| CoolProp, fluids | INTEGRATED — 104 evaluators consumed by 107 |
| ChEDL thermo/chemicals/ht, NeqSim | DEFERRED to 107 follow-up/110 as independent property/saline/carbonate references |
| CasADi, do-mpc, Pyomo/IDAES | DEFERRED to 108/110 optimization/control |
| QSDsan/WaterTAP, FMPy/FMI, OpenMDAO | DEFERRED to 108/110 |
| OpenFOAM, Gmsh, CalculiX | INTEGRATED through 014 / mesh / FEM owners; PBR domain cases DEFERRED to 110 |
| pvlib / weather datasets | DEFERRED to 108 study inputs (not yet qualified) |
