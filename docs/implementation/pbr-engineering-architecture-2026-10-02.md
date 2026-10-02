# Nannochloropsis floating-PBR engineering architecture (2026-10-02)

Status: **design record** under the maintainer directive of 2026-10-02 (Mission B: "PBR engineering architecture, design first"). This record carries no implementation authority. It defines the target architecture, fidelity tiers, capability matrix and the planned specs 167–180 in `STATUS.md`. It was revised after the independent architecture review `out/w166/gBrev.report.md` (findings F01–F12 incorporated), and reconciled with the ranked engineering inventory on 2026-10-02 (§4.4). Each of those specs becomes implementable only after its own accepted contract and readiness.

Provenance labels used below:

- **REPO** — repository fact at master `676423ba`.
- **PROBE** — executed on this host, evidence under `/home/thera/jarvis-control/work/evidence/pbr/`.
- **SOURCE** — primary external documentation or literature, independently re-checked in `gBver`.
- **INFERENCE** — coordinator reasoning.

Literature parameter values appear here only as *candidate defaults pending source verification and expert review*. No biological number in this record is a qualified fact.

## 1. Target problem

The target is a production system for *Nannochloropsis gaditana* (cells about 2–4 µm) grown in transparent floating tubular photobioreactors (PBRs) at sea. Operation is continuous or semi-continuous, under natural, continuously varying sunlight.

The engineering questions span six domains:

- **Biology:** growth under light, temperature, nutrients, CO₂/O₂ and pH; respiration in the dark; harvest.
- **Optics:** sun position, tube and array interception, wall transmission, self-shading.
- **Heat:** solar load against a seawater sink.
- **Hydraulics and gas transfer:** pumps, pressure drop, O₂ accumulation, degassing, CO₂ injection, wave-driven mixing.
- **Downstream:** dilute broth (about 0.5–2 g/L) → flocculation/flotation/membrane → centrifuge paste; medium recycle; wet biomass storage.
- **Dynamics and controls:** daily cycles, schedules, controllers, startup and shutdown, disturbances.

The architecture must let an operator take this path inside the product, without editing files, JSON or endpoints:

> flowsheet → select PBR → choose biological model → configure kinetics → configure geometry, light and environment → run → inspect time-dependent results

## 2. Current capability inventory (condensed)

The full inventory with line evidence is in `out/w166/gBinv.report.md` and the DWSIM probe in `evidence/pbr/pDWSIM/pDWSIM.report.md`.

| Area | What exists | Where the operator reaches it |
|---|---|---|
| Process flowsheet (155/158/162) | Jarvis-owned revisioned draft. 11 unit types (Heater, Cooler, Pump, Valve, Mixer, Flash, Splitter, HeatExchanger, Recycle, PFR, DistillationColumn). Closed list of 21 compounds and 6 property packages. Typed ops with layout-vs-meaning stale semantics. Verified DWSIM 10.2.9 materialization. | Process canvas, inspector, Run |
| Reactions | Arrhenius power-law kinetic reactions only, in the PFR, compiled by native-XML patch | Process inspector (operator editor) |
| DWSIM native dynamics | PID, events, integrators through MCP (`editor.py`). Caps of 1 h simulated and 200 points. | Legacy "Native DWSIM cases" stage; results shown as raw JSON |
| PBR biology (107) | `bluerev.pbr_day_night`: lumped well-mixed culture; half-sine PAR; Beer–Lambert slab with depth average; Monod or Haldane light; Rosso CTMI on a *prescribed* temperature sinusoid; Monod nitrogen; first-order loss; O₂ with kLa; daily semi-continuous harvest; `fluids`/CoolProp loop hydraulics. CVODE is the single state owner. Every coefficient needs a `basis_ref`. Results carry an "unqualified" validity envelope. | Engineering Studies stage (scalar results table) |
| Evidence and qualification (102/106) | Typed evaluator contract, separating availability from qualification, plus validity envelopes and a qualification ledger | Implicit |
| Studies and multi-fidelity (108/110) | DOE/LHS/search over evaluators; escalation to CFD/FEM with discrepancy evidence | Engineering Studies stage |
| Process→CAD (109) | `ProcessDesignEnvelope` (tube ID, loop length) → BLUECAD `tube_run`. CAD never becomes hidden process authority. | Studies "Create envelope" |
| BLUECAD (163) | Multi-part `GeometrySpec` (tube_run, bend, joint, manifold, capped_manifold, float, anchor_mount, harvest_module); build123d/OCC; GLB with fail-closed part identity; STEP/STL | BLUECAD workbench |
| CAE adapters | gmsh, CalculiX, OpenFOAM `icoFoam` 2D laminar channel; all disabled by default | Not reachable from the UI |
| Physical properties and correlations | CoolProp (pure water and gases), `fluids` (Colebrook/Clamond), `ht` (Gnielinski/Dittus–Boelter) | Behind evaluators |
| Time series in the frontend | **None**: no chart library and no profile editor. Dynamics are shown as `<pre>` JSON. | — |
| Backend Python | 3.12.3, numpy 2.3, scipy 1.18, scikit-sundae 1.1.3. pvlib, biosteam, pandas, casadi and fmpy are **not** installed. | — |

## 3. Gap analysis

1. **Two worlds that do not meet (central gap).** The operator's Process flowsheet (DWSIM-backed, steady-state) and the existing N. gaditana PBR model (107, dynamic, Studies stage) share no stream, unit, run or UI.
2. **No biological stream state.** Process streams carry only thermodynamic compounds. There is no suspended biomass, nutrients, DIC/pH or salinity. DWSIM has no Biomass compound, and MCP cannot add one (PROBE P7).
3. **No custom kinetics in DWSIM.** Expression-type kinetic reactions fail to load in 10.2.9 (PROBE P2). CustomUO scripts run IronPython without numpy. MCP cannot create a CustomUO, and dynamic mode re-invokes scripts several times per step (PROBE P1/P4). DWSIM cannot own the biology.
4. **Prescribed environment.** Light is a half-sine and temperature a sinusoid. There is no sun geometry, weather, sea temperature, energy balance, carbonate/pH, CO₂ injection, controllers or 1D O₂ accumulation.
5. **Downstream.** DWSIM's `Filter` fails to solve and its `SolidsSeparator` is an unqualified split (PROBE P7). No harvesting physics or energy correlations exist.
6. **UX.** There is no time-series plotting, no profile or schedule editors, no equation or model cards in the Process UI, and no fidelity labels on Process results.
7. **Geometry.** A one-way 109 envelope (single tube) exists. There is no array geometry and no feedback of realized volume or illuminated area into Process.

## 4. Backend-engine decision

The candidate comparison is in `gBeng.report.md` and the probe evidence in `pDWSIM`/`pPBR`; both were independently re-checked in `gBver`.

### 4.1 Ownership (decision)

| Owner | Owns (authoritative state) | Does not own |
|---|---|---|
| **Jarvis Process draft (155)** | Flowsheet document: units, streams, topology, design and operating parameters, model-card selections, scenario definitions, revisions, provenance | Any computed result |
| **DWSIM 10.2.9 (out-of-process, GPL boundary)** | Steady-state thermodynamics and conventional unit operations for the DWSIM-owned subgraph (pumps, heat exchangers, flash/degasser VLE, valves, mixers, splitters, columns); its own solve diagnostics | Biology, optics, sea and environment, PBR state, time in coupled scenarios |
| **Jarvis bioprocess engine (in-process Python; numpy/scipy/scikit-sundae, all permissive)** | PBR and culture state and time (CVODE single owner, as in 107); biological model evaluation; optics and solar coupling; lumped thermal and gas/carbonate balances; controllers and schedules; Jarvis-native bioprocess units (harvest, storage) | Thermodynamic flash or property packages beyond its declared correlations |
| **pvlib (BSD-3)** | Solar position, clear-sky, decomposition and transposition | Tube/array interception geometry (Jarvis adds it; PROBE Q1) |
| **BLUECAD (163)** | Realized geometry candidates and derived geometric measurements | Process design intent (109 rule) |
| **OpenFOAM via BLUECAD/110 (offline)** | Tier-4 field solutions on BLUECAD geometry, reduced to Tier-3 correlations | Anything in the scenario time loop |
| **BioSTEAM/thermosteam (permissive — MIT per PyPI 2.54.0 metadata, NCSA per repository LICENSE; optional, out-of-process worker)** | Later: equipment sizing and costing (TEA) and downstream design correlations | Process truth, dynamics |

### 4.2 Coupling (decision)

**Loose, Jarvis-mastered coupling.** No tight coupling, no FMI co-simulation in the solve loop (FMU exchange stays a later adapter option, §4.4), and no biology inside DWSIM.

- **Steady state (mixed-owner flowsheet).** The draft compiler partitions the flowsheet into DWSIM-owned segments and Jarvis-native units. Jarvis runs a sequential-modular outer loop:
  1. solve upstream DWSIM segments;
  2. pass boundary stream states into Jarvis units;
  3. set DWSIM boundary feeds from Jarvis unit outlets;
  4. iterate cross-engine recycle tears to tolerance, and report the residual per tear.

  Each stream carries its DWSIM thermodynamic state plus a **Jarvis culture extension** (§5.2) that DWSIM never sees. DWSIM-owned units propagate the extension by declared pass-through rules: mixers flow-weight it, splitters copy it, and heaters, coolers, pumps, valves and heat exchangers pass it through. Any unit without a rule refuses (e.g. Flash and DistillationColumn with a culture inlet), so DWSIM VLE never silently carries biology. Gas–liquid transfer of culture O₂/CO₂ belongs to the Jarvis-native **Degasser** (rate-based kLa). Its liquid outlet carries the updated culture extension, and its gas outlet is an ordinary DWSIM-compatible vapor stream (review F02).
- **Dynamic scenarios.** Jarvis is the only clock. CVODE integrates all culture, thermal and gas state, segmented at schedule and controller events: events are handled between segments, as 107 already does for harvest. Downstream DWSIM-owned units are evaluated **quasi-steadily** at macro steps only where a scenario asks for downstream balances. Failure protocol (F05): each macro-step DWSIM solve is bounded (timeout and iteration cap). On non-convergence Jarvis retries once from a damped tear (the last converged state blended with the attempt). If it still fails, the step is marked `downstream_unconverged` with its residual in the artifact and UI, and the authoritative CVODE integration continues. A downstream failure never aborts or silently corrupts the biological trajectory. The basis is timescale separation: hours for biology against seconds for downstream residence. Measured cost is about 0.65 s per small DWSIM load+solve (PROBE P6), so hourly coupling over a day is about 15 s and over a month about 8 min. A run is therefore an async job with progress. Daily-resolution downstream balance is the default; hourly is opt-in.
- **Why not the alternatives.**
  - *DWSIM CustomUO bridge:* IronPython only, no numpy, cannot be created through MCP, invoked several times per dynamic step, and would place science in GPL-hosted scripts.
  - *DWSIM native dynamics for biology:* no custom kinetics, and the caps are designed for vessel holdups.
  - *Modelica authoring / FMU co-simulation runtime:* no Modelica toolchain or FMU co-simulation is required in this slice; DWSIM has no native FMI support, and Jarvis CVODE remains the only scenario clock. This narrows, and does not reject, the inventory's FMI/FMU + FMPy slot (§4.4): FMU import/export stays a later typed adapter option for 172/179.
  - *Pyomo.DAE:* collocation over months explodes.
  - *CasADi:* LGPL. Keep it as an optional later tool for estimation/NMPC behind a process boundary.
  - *BioSTEAM as the main simulator:* steady-state TEA focus, and no PBR physics.
  - *QSDsan as the dynamic core:* it brings a separate BioSTEAM/ThermoSTEAM dynamic stack (≈950 MB installed with dependencies, 16 s cold import) aimed at sanitation and wastewater systems, and its dynamic units do not accept exogenous time-varying inputs. It does ship phototrophic model forms (PM², PM²-ASM2d, PM²-ABACO2: depth-averaged Beer–Lambert light, irradiance saturation/inhibition, photoadaptation, Monod uptake, Droop quota). Those forms and their cited parameter sources are **reference candidates for 169**; no QSDsan value is adopted without the per-value evidence 169 requires.

### 4.3 Recommended stack and alternatives

- **Chosen:** DWSIM 10.2.9 (conventional process); a Jarvis bioprocess engine on scikit-sundae CVODE, numpy and scipy; pvlib for the sun; CoolProp, `fluids` and `ht` for properties and correlations; BLUECAD/OpenFOAM offline for Tier-3/4 correlations; uPlot (MIT) as the single frontend time-series chart library (INFERENCE: small, fast, time-series native; final choice confirmed in spec 171).
- **Optional later:** a BioSTEAM worker (TEA, downstream sizing and cost), CasADi (parameter estimation, NMPC), pvtrace (offline wall-transmission and shading look-up tables).
- **Rejected for now:** QSDsan as the dynamic core (it stays a 169 model-form reference); a Modelica authoring toolchain and FMU co-simulation as the runtime (FMU exchange stays open, §4.4); SU2; Mitsuba.

### 4.4 Reconciliation with the ranked engineering inventory

The repository's ranked engineering-backend inventory is joint authority for this roadmap: [`ENGINEERING_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-19.md`](../audits/ENGINEERING_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-19.md) (S/S-/A+/A/B grades, executive candidate map), its two continuations, the candidate register in [`IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`](../IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md) (REF-038–048), and [`FUTURE_INTEGRATIONS_SYNTHESIS_2026-09-15.md`](../audits/FUTURE_INTEGRATIONS_SYNTHESIS_2026-09-15.md), which names the PBR/BlueRev stack as the first capability bake-off over the existing S/A families. This record selects from that pool; it does not replace it. The candidate-by-candidate reconciliation (evidence: `out/wpbr/rinv.report.md`, 2026-10-02) is:

| Inventory candidate (grade) | Slot in this roadmap |
|---|---|
| DWSIM (S) | Chosen: conventional steady-state units and quasi-steady downstream (167/168/172). |
| SUNDIALS (S-) | Chosen through scikit-sundae CVODE as the single dynamic state owner (170/172). |
| CoolProp (S), ChEDL `fluids`/`ht` (S) | Chosen for properties and correlations (170/175); `thermo`/`chemicals` stay available for later property needs. |
| OpenFOAM (S ref / A+ integration) | Chosen for offline Tier-3/4 correlations (179). Gmsh (A+), meshio (A+) and VTK (S) are the expected meshing, mesh-interchange and field-artifact candidates when 179 is specified. |
| BioSTEAM (S), ThermoSTEAM (S-) | Deferred to the optional out-of-process TEA/sizing worker (178). |
| QSDsan (S-), Bioindustrial-Park (A+) | Model-form and parameter-source references for 169 (§4.2), not runtime authorities. |
| FMI/FMU + FMPy (S), OpenModelica (A+) | Not in the current runtime; 167–172 keep typed owner, state and unit boundaries format-neutral so an FMU import/export adapter can be added later (172 export of reviewed models, 179 surrogate exchange). |
| IDAES + Pyomo (S) | Not chosen for 168/172: the problem is a small-state, event-segmented, months-long simulation, where collocation scales poorly and an equation-oriented flowsheet would duplicate DWSIM ownership. Remains the candidate for later design optimization over converged steady states. |
| NeqSim (S) | Not chosen: DWSIM already owns the conventional process role and is proven on this host (155/158/162); a second conventional engine would add a second authority with no PBR capability gain. |
| CasADi (A+), do-mpc (A+) | Later estimation, MHE and NMPC behind a process boundary (after 172/175); 172 controllers are on/off, PI and turbidostat only. |
| Reaktoro (A+) | Candidate cross-check for the carbonate/pH algebra of 175 (seawater speciation); 175 keeps an algebraic carbonate system as the in-loop form. |
| Cantera (S-), TESPy (A+) | Outside this slice; 180 compiles typed rate laws to DWSIM and 175 uses a lumped thermal balance. |
| CAPE-OPEN (S), DWSIM Thermodynamics Library (A+), WaterTAP (A+), open62541 (A+), pycalphad (A+), OpenMDAO (A+), SU2 (A+), FEniCSx (A+), PETSc (S-), ParaView (A+), PyVista (S-), LEAP71 PicoGK/ShapeKernel/LatticeLibrary/HelixHeatX, CadQuery (S-), OCCT (S), Sketch2Simulation (A+) | Outside this roadmap. Geometry stays with BLUECAD (163/176); none of these slots is required by 167–180 as specified. |

## 5. Data and authority architecture

### 5.1 Unit ownership in the Process draft

Each unit type in the draft registry declares an `owner`: `dwsim` (the existing 11) or `jarvis_bio` (new). The compiler builds DWSIM materialization only for the `dwsim` subgraph. Jarvis units are evaluated by registered evaluators that implement the 106 contract. Results carry the producing owner, evaluator id and version, model-card ids, parameter-set digests and fidelity tier. Agent actions (166) operate on all units through the same typed ops.

### 5.2 Culture stream extension (Jarvis-owned)

`stream.culture`:

- suspended biomass X [kg/m³];
- intracellular N quota [kg N/kg X] (Tier 2);
- dissolved N and P [kg/m³];
- DIC [mol/m³] and pH;
- dissolved O₂ [kg/m³];
- salinity [g/kg];
- an optional lumped composition marker (lipid fraction, Tier 3).

Carrier liquid thermodynamics stay in DWSIM. Water is the carrier; a seawater property basis is a declared screening approximation until a qualified seawater package exists. Feed specification gains a "Culture medium" section. Validation reports missing or contradictory culture data as blockers or warnings, in the 162 style.

### 5.3 Biological model cards (spec 169)

A **model form** is a reviewed Jarvis implementation of one equation family. Each form has:

- a stable id, version and rendered equation;
- a symbol table: name, meaning, unit, valid range;
- its state and input requirements;
- verification tests: analytic limits and balance closure.

Forms are composable into a **growth model** by factors:

- light: Monod/Tamiya, Haldane/Andrews, Steele, Eilers–Peeters, and later Han PSU;
- temperature: isothermal, Rosso/Bernard–Rémond CTMI;
- nutrient: Monod multiplicative, Liebig minimum, Droop quota;
- O₂ inhibition;
- pH factor;
- losses: respiration/maintenance (light vs dark) and decay;
- stoichiometry and yields: elemental biomass formula → O₂ produced and CO₂, N and P consumed.

A **parameter set** is data, not code. It holds values with units and the following metadata:

- per-value `basis_ref` (DOI or dataset);
- species and strain;
- experimental conditions;
- validity ranges;
- verification state: `candidate` → `source_verified` → `expert_reviewed` → `qualified` (qualification ledger 102).

Operators can duplicate a set and edit values. Every edit is revisioned, and an edited value without a source is labelled "operator assumption".

Arbitrary user equations are **not** Tier 1–2. A later "custom expression" form (dimension-checked, AST-restricted, with sympy rendering) can be added behind the same card UI once the validation burden is accepted.

This answers "add Monod kinetics": Monod is a *nutrient-limitation factor of a bioreactor growth model*. It is not a DWSIM PFR reaction. The agent says so and can offer the correct unit.

### 5.4 Environment, site and schedules (specs 171/172)

- **Site:** latitude, longitude, time zone, sea or water body.
- **Environment profile:** a typed time series at a declared resolution. Channels are GHI/DNI/DHI or PAR, air temperature, sea temperature, wind and cloud, plus optional wave height and period for later mixing surrogates (F09). Each profile records source provenance:
  - imported file: CSV, EPW, PVGIS-TMY file;
  - pvlib clear-sky generator for site and dates, with a clearness factor;
  - synthetic generator, such as the existing half-sine for continuity;
  - a fetched dataset (PVGIS/ERA5/CMEMS): **parked** (F12). No live API fetch is planned until a general external-data-provider setting exists with egress approval and credentials. The operator imports downloaded files instead.
- **Operating schedule:** events (harvest or dilution at a time or on a condition; feed changes; setpoint changes; startup inoculation) and controller definitions (on/off with hysteresis such as pH-stat CO₂ and DO-triggered degassing; PI such as cooling; turbidostat harvest on biomass).
- **Persistence (F06).**
  - Schedules, controllers and scenario definitions live **inside the Process draft document** (`draft.schedules`, `draft.scenarios`). They are therefore revisioned, CAS-checked, stale-tracked and editable through typed DraftOps and 166 actions with the same `base_revision` semantics.
  - Environment profiles are large immutable content-addressed artifacts (`process/profiles/{id}` with a sha256 digest). Scenarios reference them by `(profile_id, digest)`. Editing a profile creates a new artifact, and re-pointing a scenario is a draft revision.
  - Changing any referenced input makes dependent results stale.

### 5.5 Scenarios and results

A **scenario** binds:

- a draft revision;
- profile ids and digests;
- a schedule revision;
- duration, output resolution and fidelity tier;
- the solver tolerances it records.

A run produces a **time-series artifact** (columnar numpy `.npz` plus a JSON manifest: channels, units, owners, fidelity, digests, diagnostics, balance residuals) and **KPIs**: areal and volumetric productivity, harvested biomass, energy per kg, maximum temperature, maximum DO, CO₂ use and controller duty. Results are revision-bound and stale-tracked exactly like 155 Process results. Results have no authority beyond their recorded inputs.

### 5.6 Geometry linkage (spec 176; extends 109 without a second authority)

- **Design intent stays in Process.** The PBR unit's geometry descriptors (tube OD/ID, wall, material, loop length, tube count, pitch, orientation azimuth, submerged fraction, manifold layout class) are Process parameters.
- **Process → BLUECAD.** A 109-style envelope generates a BLUECAD array candidate (tubes, manifolds, floats).
- **BLUECAD → Process.** BLUECAD returns *derived measurements* as verification feedback: liquid volume, illuminated projected area, wetted area, bbox and bend count. Mismatches against the Process descriptors are findings.
- **Adoption (F08).** When the operator designs the geometry first in BLUECAD, an explicit "Use geometry from candidate …" action writes descriptors into the Process draft as a revision with provenance. It is allowed **only** for candidates produced by a recognised parametric PBR template, and only from that template's structured parameters. It never feature-recognises arbitrary B-rep. Other candidates are refused with a plain reason. There is no live binding: one authority at a time, visible in the inspector ("from BLUECAD candidate c… · digest …").
- **Tier 3/4.** CFD runs on the BLUECAD candidate geometry. Their outputs come back only as correlations with validity envelopes (§7).

### 5.7 Agent integration

Each new capability adds typed actions to the 166 vocabulary, for example:

- `set_model_factor(unit, factor, form)`;
- `set_parameter(unit, symbol, value, unit)`;
- `attach_profile(scenario, profile)`;
- `add_harvest_event(...)`.

Value changes are confirm-tier, as in 166. Scenario runs remain operator-started. The 166 surface brief grows with the model card and scenario summary, bounded as before.

## 6. Frontend UX architecture

The principle is progressive disclosure on the existing Process surface, with no new top-level product.

- **Palette.** A "Bioprocess" group holds Photobioreactor, Culture medium feed, Degasser (Jarvis-native, rate-based kLa), Harvest separator and Storage tank. Units show an owner badge (DWSIM / Jarvis) in the inspector header.
- **PBR inspector tabs:**
  - **Overview:** key outputs, readiness chip, fidelity badge.
  - **Geometry:** descriptors; "from BLUECAD" binding state; "Create/Update 3D candidate".
  - **Biology:** a model card with an equation rendered per factor, a factor picker (light / temperature / nutrient / O₂ / pH / losses), and a parameter table showing symbol, value, unit, range bar, source and verification badge. "Duplicate set" and "Edit" are available, with off-range warnings.
  - **Light & environment:** site, profile picker, preview plot.
  - **Operation:** dilution or harvest, velocity, setpoints and controllers summary.
  - **Results:** KPIs plus small multiples.
  - An **Advanced** disclosure holds solver tolerances and model-form versions.
- **Profiles panel.** A list, plus an editor with a uPlot chart, table, import (file picker with column mapping and unit selection), generators (clear-sky / synthetic) and provenance. Profiles live in the workspace and are reachable from the PBR tab and from the Scenario panel.
- **Scenario panel.** Opened from the Process toolbar ("Simulate scenario…", secondary to Run). Choose duration, profiles, schedule, fidelity tier and output resolution, then **Run**. The run is an async job with progress and cancel. Results open in a **time-series view**: synchronized plots for states, inputs and controller outputs; KPI cards; a balance-residual chip; and diagnostics (solver steps, events, validity-envelope violations). Export is CSV. Results show "Fidelity T2 · model cards … · unqualified" in every header.
- **Schedule editor.** A timeline with an event list, add-event form, conditional triggers and a controller list with plain-language descriptions ("Inject CO₂ when pH > 8.1 until pH < 7.9").
- **Diagnostics.** Structured findings (blocker / warning / info) with object links, the same as 162.
- **Surrogate correlation library (T3).** Read-only list of qualified correlation artifacts (kLa, mixing, h_sea, wall transmission) with validity envelopes, selectable in Advanced. Producing them (CFD and optics runs) is an offline engineering escalation under 110, not an interactive Process control (F10).
- **Model-card library.** Reachable from the Biology tab "Browse models…", also usable read-only from the Memory/Models surface.
- **Accessibility.** Plots have a table fallback and keyboard-reachable legends. Unit symbols scale per 162.

### Operator journey check

| Step | Discover | Configure | Run | Inspect | Modify |
|---|---|---|---|---|---|
| Flowsheet → PBR | Palette "Bioprocess" | Drag, connect | — | Inspector header | Canvas, agent actions |
| Biological model | Biology tab | Factor picker, parameter table | — | Model card, sources | Duplicate or edit set (revisioned) |
| Geometry | Geometry tab | Descriptors or "Use BLUECAD candidate" | Create 3D candidate | BLUECAD viewer, feedback findings | Either side through explicit actions |
| Light / environment | Light tab, Profiles panel | Import, generate, edit | — | Preview plot | Edit profile (makes results stale) |
| Run | Toolbar "Simulate scenario…" | Scenario form | Run job | Time-series view, KPIs | Re-run, compare runs |

## 7. Fidelity tiers

| Tier | Name | Biology | Light | Thermal | Gas / hydraulics | Use | Cost target |
|---|---|---|---|---|---|---|---|
| **T1** | Engineering lumped | 107-class: light response × CTMI × nutrient Monod; first-order losses | Beer–Lambert in true cylindrical geometry (the 107 one-side slab is retired: up to +170 % error under diffuse light, PROBE Q2) | Prescribed profile | Lumped O₂ and kLa; `fluids` ΔP (with baffle friction multiplier if declared) | Everyday design, sweeps (108) | < 1 s per simulated day |
| **T2** | Coupled environment | + Droop N quota, dark respiration, O₂ and pH factors, yields → CO₂/O₂ | pvlib sun + tube/array interception + Fresnel wall + shading; Beer–Lambert or two-flux selectable | Lumped energy balance (solar, air, sky, seawater) | Lumped (0D) dynamic O₂/DIC with algebraic carbonate pH; degasser kLa; CO₂ and DO control; **1D loop O₂/DIC/pH profiles as steady snapshots** at macro instants (e.g. noon, midnight), not integrated in time (F04) | Operations, controls, seasonal campaigns | ≤ 30 s per simulated month (PROBE Q3: 72 h of a 7-state carbonate/thermal/controller model took 2.0 s at 60 s supervisory steps), excluding optional DWSIM |
| **T3** | Resolved surrogates | + Han PSU / light–dark cycling from mixing | Ray-traced or spectral look-up tables | CFD-derived h_sea / h_air | CFD-derived kLa, mixing frequency, two-phase ΔP; dynamic 1D loop (method of lines) with a separate budget of minutes per simulated month | Detailed design, wave effects | Runtime as T2 (1D dynamic: minutes per month); offline precomputation |
| **T4** | Field CFD | — | (Monte Carlo) | Conjugate heat transfer | OpenFOAM multiphase on BLUECAD geometry | Specific questions; feeds T3 through 110 escalation | Hours per case, offline |

Results always carry their tier, model-card versions, parameter-set verification states and validity envelope. Escalation follows 110: discrepancy evidence between tiers is recorded, and a lower tier never silently inherits a higher tier's status.

## 8. Capability matrix

Columns:

- **Owner** = computational owner.
- **SS/D** = steady state / dynamic.
- **Now** = current support: ✔ supported, ◐ partial, ✗ missing.
- **Phase** = spec.

For every row, the frontend column answers how the operator discovers, configures, runs, inspects and modifies the capability.

| # | Capability | Operator workflow / frontend | Canonical data | Owner | Inputs → outputs (units) | SS/D | Validation | Now | Ext. dep | Priority / phase |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mixed-owner flowsheet | Owner badge on units; Run solves all; results per unit with owner | `unit.owner`; tear residuals | Jarvis orchestrator + DWSIM | Stream states → solved states | SS | Cross-engine balance closure; tear convergence tests | ✗ | — | P0 / 168 |
| 2 | Culture stream extension | Stream inspector "Culture" section; feed "Culture medium" form | `stream.culture` (§5.2) | Jarvis | X kg/m³, N/P kg/m³, DIC mol/m³, pH, O₂ kg/m³, S g/kg | SS+D | Propagation rules per unit; balance tests | ✗ | — | P0 / 167 |
| 3 | Monod / multi-nutrient limitation | Biology tab → Nutrient factor (Monod, Liebig, Droop) | Model form + parameter set | Bio engine | S, K_S → f_N (–) | D | Analytic limits; balance | ◐ (107 Monod N) | — | P0 / 169 |
| 4 | Light response incl. photoinhibition | Biology tab → Light factor | Form + set | Bio engine | Local PAR µmol m⁻² s⁻¹ → f_I | D | Analytic; literature curves | ◐ (Monod / Haldane) | — | P0 / 169 |
| 5 | Temperature effect | Biology tab → Temperature factor | Form + set | Bio engine | T °C → f_T | D | CTMI shape tests | ◐ (Rosso CTMI) | — | P0 / 169 |
| 6 | Respiration / maintenance / dark / decay | Biology tab → Losses | Form + set | Bio engine | X, light state → loss d⁻¹ | D | Dark-period mass loss tests | ◐ (first-order) | — | P1 / 169 |
| 7 | Yields / stoichiometry | Biology tab → Stoichiometry card | Elemental formula + yields | Bio engine | μX → O₂ out, CO₂ / N / P in (kg) | D | Elemental closure | ◐ (Y_O2, fixed N quota) | — | P1 / 169 |
| 8 | O₂ inhibition | Biology tab → O₂ factor | Form + set | Bio engine | DO → f_O2 | D | Literature; analytic | ✗ | — | P1 / 175 |
| 9 | CO₂ / DIC / pH / salinity effects | Biology tab → pH factor; Culture section | Carbonate model + set | Bio engine | DIC, alkalinity, T, S → pH, CO₂(aq) | D | Equilibrium constants vs reference | ✗ | — | P1 / 175 |
| 10 | Parameter provenance and verification | Parameter table: source and verification badge; duplicate or edit | Parameter set (§5.3) | Jarvis (102 ledger) | — | — | Source verification step | ◐ (`basis_ref` required) | — | P0 / 169 |
| 11 | PBR unit (T1) | Palette → PBR; inspector tabs; Run | Unit params + model-card refs | Bio engine (106 evaluator) | Inlet culture, geometry, light → outlet culture, KPIs | SS (periodic) + D | 107 regression; balance | ◐ (107 in Studies only) | — | P0 / 170 |
| 12 | Solar position / irradiance | Light tab: site + profile; preview plot | Site + profile | pvlib | Lat/lon/time → zenith, azimuth, GHI/DNI/DHI W m⁻² | D | pvlib reference cases | ✗ | pvlib (BSD-3) | P0 / 171 |
| 13 | Weather / sea / wind profiles | Profiles panel: import, generate, edit, plot | Profile artifact | Jarvis | File or generator → channels with units | D | Import round-trip; unit checks | ✗ | Optional data APIs (egress-gated) | P0 / 171 |
| 14 | Tube / array interception, wall optics, shading | Light tab → "Optics" disclosure | Geometry descriptors + optical props | Bio engine (+pvlib) | Sun vector, DNI/DHI, D, pitch, n_wall → absorbed PAR per m | D | Analytic single-tube; energy conservation | ✗ | — | P1 / 174 |
| 15 | Attenuation / self-shading in culture | Biology/Light: model selector (Beer–Lambert / two-flux) | Optics form + set | Bio engine | X, D, E_a, E_s, b → average or local PAR | D | Analytic limits; probe Q2 | ◐ (slab BL) | — | P0 / 170 (cylindrical Beer–Lambert) · P1 / 174 (two-flux) |
| 16 | Spectral dependence | Advanced: spectral toggle (T3) | Spectral LUT | Bio engine | λ-resolved → effective PAR | D | Literature | ✗ | — | P3 / 179 |
| 17 | Dynamic boundary profiles in runs | Scenario form: pick profiles | Scenario | Jarvis | Profiles → forcing | D | Interpolation tests | ✗ | — | P0 / 172 |
| 18 | Operating schedules (feed / harvest / setpoints) | Schedule editor timeline | Schedule artifact | Jarvis | Events → state jumps / setpoints | D | Event-ordering tests | ◐ (daily harvest param) | — | P0 / 172 (engine) · 173 (editor) |
| 19 | Controllers (pH-stat, DO, cooling PI, turbidostat) | Schedule editor → Controllers | Controller defs | Bio engine | Measured state → actuator | D | Closed-loop tests | ✗ (DWSIM PID only, legacy) | — | P1 / 172 · 175 |
| 20 | Continuous / semi-batch / startup / shutdown | Scenario templates; schedule | Scenario + schedule | Bio engine | Initial state, events → trajectories | D | Mass-balance closure over events | ◐ (107 semi-continuous) | — | P0 / 172 |
| 21 | Time-series results, KPIs, diagnostics | Time-series view, KPI cards, residual chip, CSV export | Result artifact (§5.5) | Jarvis | Trajectories → plots, KPIs | D | Artifact digest; stale binding | ✗ | uPlot (MIT) | P0 / 171 (charts) · 173 (results view) |
| 22 | Pumps / pipes / pressure drop | Process units (DWSIM) + PBR hydraulics section | Draft + correlations | DWSIM / `fluids` | Q, D, L, roughness → ΔP Pa, power W | SS | Existing evaluator tests | ◐ | — | P1 / 170 |
| 23 | Residence time / loop O₂ accumulation | PBR Results: loop profile snapshot at selected instants | 1D steady loop snapshot (T2); dynamic 1D (T3) | Bio engine | u, L, production → DO(x) | D | Analytic plug flow | ✗ | — | P1 / 175 (snapshot) · 179 (dynamic 1D) |
| 24 | Degassing / CO₂ injection / kLa | Degasser unit (Jarvis-native, rate-based); controller | kLa correlation set | Bio engine; gas outlet to a DWSIM vapor stream | u_g, geometry → kLa s⁻¹, transfer | D | Correlation envelope | ◐ (lumped kLa) | — | P1 / 175 |
| 25 | Wave-driven / passive mixing | Advanced → mixing model (T3) | Surrogate correlation | Bio engine (from CFD) | Sea state → L/D frequency, kLa factor | D | CFD-derived envelope | ✗ | OpenFOAM (offline) | P3 / 179 |
| 26 | Heat balance (solar, air, sky, seawater; metabolic heat declared negligible, as an explicit assumption with an order-of-magnitude check) | Thermal section in PBR tab; T plot | Thermal params | Bio engine | Irradiance, T_air, T_sea, wind, h → T culture | D | Energy closure; analytic step | ✗ (prescribed T) | — | P1 / 175 |
| 27 | Cooling strategies | Controller (submersion / spray / exchanger) | Controller + unit | Bio engine / DWSIM HX | T setpoint → duty | D | Closed-loop tests | ✗ | — | P2 / 175+ |
| 28 | Geometry linkage to BLUECAD | Geometry tab binding; "Create/Update 3D"; findings | Descriptors + envelope + feedback | Process ↔ BLUECAD (109) | Descriptors → candidate; measurements → findings | SS | Digest-bound round-trip | ◐ (single tube envelope) | — | P1 / 176 |
| 29 | CFD-derived correlations | Advanced: correlation picker with validity envelope | Correlation artifact | OpenFOAM via 110 → Jarvis | Field runs → fitted correlations | — | Grid convergence; envelope | ◐ (laminar channel only) | OpenFOAM (GPL, process boundary) | P3 / 179 |
| 30 | Harvesting (flocculation / DAF / membrane / centrifuge / drum filter) | Palette "Harvest separator" with method picker; warnings for infeasible methods (e.g. drum filter without flocculation for 2–4 µm cells) | Unit params + method set | Jarvis-native (+ optional BioSTEAM later) | Broth → paste + filtrate (X, recovery, energy kWh m⁻³) | SS (+ quasi-steady D) | Mass closure; literature ranges | ✗ | — | P1 / 177 |
| 31 | Wet biomass storage | Storage unit; residence; degradation warning | Unit params | Jarvis-native | Paste, T, time → state | D | Balance | ✗ | — | P2 / 177 |
| 32 | Medium / water recycle and accumulation | Recycle stream with culture extension; blowdown | Draft topology | Orchestrator | Filtrate → recycle; accumulation | SS+D | Tear convergence; accumulation tests | ◐ (DWSIM Recycle only) | — | P1 / 168 · 177 |
| 33 | Downstream conventional units (heaters, pumps, extraction) | Existing Process units | Draft | DWSIM | Thermo streams | SS | Existing 158 proofs | ✔ | DWSIM | — |
| 34 | TEA / costing | Later "Economics" tab | TEA artifact | BioSTEAM worker | Equipment, flows → CAPEX/OPEX | SS | Benchmark cases | ✗ | BioSTEAM (NCSA) | P3 / 178 |
| 35 | Fidelity labelling and escalation | Fidelity badge everywhere; "Compare tiers" | Result metadata (110) | Jarvis | — | — | Discrepancy records | ◐ (110 in Studies) | — | P0 / all |
| 36 | Agent actions on bioprocess objects | Sidecar (166) | Action vocabulary | Jarvis actions | — | — | Per-action tests | ◐ (166) | — | P1 / per spec |
| 37 | Monod/Haldane-type *substrate* rate laws in conventional DWSIM reactors (CSTR/PFR) | Reaction editor: typed rate-law form picker (power law, Monod, Haldane/Andrews, with inhibition terms); parameters with units; preview of the generated rate | Typed rate-law form + params in the draft reaction set (never free text) | DWSIM (IronPython `PythonScript` kinetics, generated by Jarvis via native XML; PROBE pDWSIM2) | Concentrations, T → r (kmol m⁻³ s⁻¹) | SS (+DWSIM dyn) | Hand-calculation CSTR checks; determinism (PFR first-solve drift tracked) | ✗ (Arrhenius only) | — | P1 / 180 |
| 38 | Baffles / static mixers in tubes | PBR Geometry tab: insert type, count, pitch | Geometry descriptor | `fluids` multiplier (T1–T2, unqualified); CFD surrogate (T3) | Insert spec → ΔP multiplier, mixing factor | SS | Literature or CFD envelope | ✗ | — | P2 / 170 · 179 |

## 9. Roadmap and planned specs

The dependency graph, where `→` means "required before". It was revised per review F01, F03, F07 and F11.

```
155/158/162/166 ─→ 167 CULTURE STREAMS ─→ 168 MIXED-ENGINE SOLVE ─┐
102/106/107 ─────→ 169 BIO MODEL CARDS ─────────────────────────────┼─→ 170 PBR UNIT T1 ─┬─→ 172 DYNAMIC ENGINE ─→ 173 DYNAMIC STUDIO
155 ─────────────→ 171 ENVIRONMENT PROFILES + CHARTS ─────────────────────────────────┼─→ 172            │
                                                                                     └─→ 174 SOLAR OPTICS T2 ─┐
                                                              172 + 174 ─→ 175 THERMAL + GAS T2 (Degasser, carbonate, controllers)
109/163/166 + 170 ─→ 176 PROCESS↔BLUECAD PBR GEOMETRY LINK
168 + 170 ─→ 177 DOWNSTREAM HARVEST (+172 for dynamic) ─→ 178 BIOPROCESS TEA (optional BioSTEAM worker)
110 + 175 + 176 ─→ 179 CFD / OPTICS SURROGATES T3 (offline)
158 + 169 ─→ 180 RATE-LAW KINETICS IN DWSIM REACTORS
```

These parallelize: 167 ∥ 169 ∥ 171 ∥ 180, then 168, then 170, then 172 ∥ 174 ∥ 176 ∥ 177, then 173 ∥ 175, then 178/179.

A recommended order of value: 167 → 168 → 169 → 170 delivers the first operator-visible PBR in the flowsheet. 180 can run early because it directly answers the observed "Monod on PFR-1" request for conventional reactors. 171 → 172 → 173 delivers the dynamic product.

| Spec | Name | Bounded outcome | Hard deps | Acceptance (summary) |
|---|---|---|---|---|
| 167 | PROCESS-CULTURE-STREAMS-1 | `unit.owner` field. `stream.culture` schema with units. Pass-through rules for every DWSIM unit, refusing for Flash and DistillationColumn. Culture-medium feed specification. Validation findings. Stream and feed "Culture" inspector sections. Owner badges. | 155, 158, 162, 166 | Unit tests per pass-through rule. Draft revision and stale semantics preserved. Chromium: configure a culture feed and inspect propagated culture state on a DWSIM-only flowsheet after Run. |
| 168 | PROCESS-MIXED-ENGINE-SOLVE-1 | Compiler partitioning into DWSIM segments and Jarvis-native units. Sequential-modular outer loop with cross-engine tear iteration, residuals, bounds and damping. One Jarvis-native "specified separator" (recovery and concentration) proving the boundary. Run integration with per-owner results. | 167 | Real DWSIM: pump → Jarvis separator → DWSIM heater → recycle converges with reported residuals. Culture and mass balance closes. Injected non-convergence reported, not hidden. Chromium Run and results. |
| 169 | BIO-MODEL-CARDS-1 | Model-form library (light, temperature, nutrient incl. Monod/Liebig/Droop, losses, stoichiometry) with rendered equations, symbols, units and ranges. Parameter sets as revisioned data with per-value human-checkable sources and verification states. Model-card browse/select/duplicate/edit UI with off-range warnings. | 102, 106, 107 | Analytic-limit and balance tests per form. No set beyond `candidate` without source evidence. Chromium: pick factors, edit a value (revisioned, source badge), view the equation card. The agent explains where Monod applies. |
| 170 | PBR-UNIT-1 | T1 Photobioreactor unit in the flowsheet: the 107 core refactored behind 106, consuming model cards and culture streams. **True cylindrical Beer–Lambert** under beam plus isotropic diffuse, driven by the existing half-sine day curve and a diffuse-fraction parameter; no pvlib dependency (F07). Geometry and operation descriptors including baffle friction multiplier. Periodic-steady result plus outlet culture stream. PBR inspector tabs. | 168, 169 | 107 regression parity for unchanged physics, plus documented slab→cylinder change. Flowsheet PBR → 168 specified separator → recycle runs end to end (F01). Chromium journey "select PBR → choose model → configure → run → inspect". |
| 171 | ENVIRONMENT-PROFILES-1 | Site model. Immutable content-addressed profile artifacts from offline file import (CSV, EPW, PVGIS export) and generators (pvlib clear-sky, synthetic). Optional wave channels. Profile editor with the single chart library (uPlot proposed) and table fallback. **No live API fetch** (F12). | 155 | pvlib reference values. Import round-trip with units and digest. Chromium: import, plot, edit (new artifact), provenance visible. No network. |
| 172 | PROCESS-DYNAMIC-ENGINE-1 | Scenarios, schedules and controllers in the draft document as DraftOps. Async scenario jobs with progress and cancel. CVODE master with segment events. Controller execution (on/off hysteresis, PI, turbidostat). Optional quasi-steady DWSIM downstream with the F05 failure protocol. Time-series artifact (npz + manifest). Headless API. | 170, 171 | 30-day T1 run within budget. Balance closure across harvest and controller events. Downstream failure marked and integration continues. Cancel and stale semantics. API-level tests. |
| 173 | PROCESS-DYNAMIC-STUDIO-1 | Scenario form. Schedule timeline and controller editor with plain-language descriptions. Synchronized time-series view, KPI cards, residual and convergence chips, diagnostics and CSV export. Fidelity labels. Run comparison. | 172 | Chromium: define a schedule, run, inspect plots and KPIs, edit the schedule → stale → re-run, compare runs. Keyboard and table fallbacks. |
| 174 | PBR-SOLAR-OPTICS-2 | T2 optics: pvlib SPA sun vector, tube and array beam/diffuse/sea-reflected interception, Fresnel wall transmission, inter-tube shading, selectable two-flux scattering. | 170, 171 | Analytic single-tube and conservation tests. Probe Q1/Q2 cases reproduced. Chromium: switch the optics model and see the tier label and absorbed-PAR plot. |
| 175 | PBR-THERMAL-GAS-2 | T2 lumped (0D) energy balance (solar, air, sky, seawater; metabolic heat declared negligible). Jarvis-native **Degasser** (rate-based kLa; gas outlet to a DWSIM vapor stream). Dynamic O₂/DIC with algebraic carbonate pH. CO₂ and DO controllers. O₂ and pH growth factors. 1D loop profiles as steady snapshots. | 172, 174 | Energy, carbon and O₂ closure. Controller closed-loop tests. A month in ≤ 30 s (0D, PROBE Q3 basis). Chromium: temperature, DO and pH plots with controller duty and a loop snapshot. |
| 176 | PROCESS-BLUECAD-PBR-LINK-1 | Parametric PBR array template in BLUECAD (tubes, manifolds, floats). Process descriptors → envelope → candidate. Derived-measurement feedback findings. Adoption only from template candidates (F08). Staleness both ways. | 109, 163, 166, 170 | Real build123d array. Feedback mismatch finding. Adoption refused for non-template candidates. Chromium round-trip. |
| 177 | DOWNSTREAM-HARVEST-1 | Jarvis-native harvest separator methods (flocculation, DAF, membrane, centrifuge, drum filter with precoat) with specified performance, energy correlations and feasibility warnings. Storage tank. Medium recycle with accumulation and blowdown. | 168, 170 (+172 for dynamic) | Mass closure. Infeasibility warnings (e.g. drum filter without flocculation for 2–4 µm cells). Recycle accumulation test. Chromium flowsheet PBR → harvest → recycle. |
| 178 | BIOPROCESS-TEA-1 | Optional long-lived out-of-process BioSTEAM worker for sizing and costing. Economics tab. | 177 | Pinned worker and licence record. Benchmark parity. UI. |
| 179 | PBR-CFD-SURROGATES-3 | Offline 110 escalation (OpenFOAM on BLUECAD geometry, optics look-up tables) producing correlation artifacts with validity envelopes. Read-only surrogate library in the UI (F10). Dynamic 1D loop option. | 110, 175, 176 | Grid-convergence evidence. Envelope enforcement. Discrepancy record. Library visible and selectable. |
| 180 | PROCESS-RATE-LAW-KINETICS-1 | Typed rate-law forms (power law, Monod, Haldane/Andrews, inhibition) for DWSIM CSTR/PFR reactions, compiled to IronPython `PythonScript` kinetics through the existing native-XML path (PROBE pDWSIM2). Adds a CSTR unit. No free-text scripts. | 158, 169 | Hand-calculation CSTR checks. Determinism (PFR first-solve drift characterised). Chromium: choose Monod for a reactor, run, inspect conversion. Agent `set_reaction` action (confirm tier). |

Each spec extends the 166 action vocabulary for its objects, and none adds a second authority.

## 10. Probes and remaining uncertainty

Done:

- **pDWSIM (P1–P7):** results in §2–§4.
- **pDWSIM2:** user-defined kinetics, §10.3.
- **pPBR:**
  - Q1 pvlib for tube arrays;
  - Q2 light-model error;
  - Q3 CVODE stiffness with carbonate and controllers;
  - Q4 BioSTEAM on Python 3.12.

  Results are in §10.1.
- **gBver:** independent literature and licence verification, §10.2.

Still uncertain, and owned by the named spec:

- a qualified seawater property basis in DWSIM (167; screening approximation until then);
- the real DWSIM cost and convergence on the actual PBR + downstream graph (168/172 benchmark gate, F05 protocol);
- *N. gaditana* parameter qualification (169, expert review);
- two-flux radiative properties for the actual strain and culture (174);
- wave-mixing and baffle correlations (179);
- frontend delivery effort for charts and editors (171/173), the largest UI investment; uPlot keeps the dependency small.

### 10.1 pPBR results (executed 2026-10-02, scratch venv, scripts and raw output in `evidence/pbr/probes/`)

- **Q1 pvlib 0.16.1 (BSD-3-Clause)** computed SPA solar position and Ineichen clear-sky irradiance with the packaged Linke-turbidity table (no network) for Cádiz on the solstices. The Jarvis-side interception geometry is what matters. Intercepted daily energy on a horizontal 60 mm tube:
  - summer, N–S axis: 739 Wh/m isolated, 633 Wh/m in a 90 mm pitch array;
  - summer, E–W axis: 582 / 551 Wh/m;
  - winter, N–S axis: 294 / 220 Wh/m;
  - winter, E–W axis: 390 / 256 Wh/m.

  Orientation reverses its advantage between seasons, and array shading costs about 5–35 %. **Verdict:** pvlib is sufficient as the sun/sky engine. Tube/array interception, shading, wall transmission and sea reflection are Jarvis model forms (spec 174).
- **Q2 light-model error** (illustrative optics, not *N. gaditana* facts). The current 107 one-side-lit slab against true cylindrical Beer–Lambert under isotropic light gives +19 % to **+170 %** error (12 of 15 cases above 20 %). Under collimated normal light the error is at most 18 %. Two-flux scattering corrections relative to the slab were 1–16 % for b = 0.002–0.03. **Verdict:** tube geometry dominates and belongs in T1; scattering (two-flux) is a T2 option whose value depends on measured radiative properties.
- **Q3 CVODE (scikit-sundae 1.1.3 through the repo's `integrate_ode`).** The model had 7 states (X, N, O₂, DIC with algebraic carbonate pH closure, T) plus a pH-stat CO₂ on/off controller with hysteresis. 72 h at 60 s supervisory segments took **2.0 s**, 62.7 k RHS evaluations and 202 controller transitions, with carbon and nitrogen balances closed to 1e-13. Explicit fast CO₂ hydration (8 states) gave the same trajectory at 2.5 s. **Verdict:** algebraic carbonate closure plus segment-boundary controllers is the T2 numerical architecture. A second integrator is unnecessary.
- **Q4 BioSTEAM 2.54.0 / thermosteam 0.54.2 / QSDsan 1.5.3.** A custom biomass solid (CH1.8O0.5N0.2) and a centrifuge flowsheet were easy, and the simulation took 0.7 ms. However, the cold import costs **14.6 s** (QSDsan 16 s), numba cannot cache dynamically defined functions ("no locator available"), and design correlations warn below industrial scale (minimum 2 t/h solids). **Verdict:** if adopted (178), BioSTEAM runs as a long-lived out-of-process worker for sizing and TEA, never in the request path or the time loop.

### 10.3 DWSIM user-defined kinetics (pDWSIM2, `evidence/pbr/pDWSIM2/report.md`)

- `ReactionKinFwdType=UserDefined` with an `Expression` loads and solves in CSTR and PFR. The numeric checks agree with hand-calculated first-order CSTR conversion (0.25825 % vs 0.2580 %; 0.51530 % vs 0.5148 %). However, the expression binds **only T**, so concentration-dependent (Monod) laws fail (`no variable named 'R1'`).
- `ReactionKinetics=PythonScript` (IronPython) **works**: the script receives T, P, Amounts and stoichiometry aliases R1/R2/P1/N1 and must set `r`. This makes Monod/Haldane substrate kinetics possible inside DWSIM reactors.
- Authoring requires native-XML patching (`ReactionKinetics`, `ScriptTitle`, a `ScriptItem`), exactly like the current compiler's Arrhenius path. MCP has no reaction-authoring tool.
- CSTR solves are bit-identical. PFR shows a tiny first-solve drift (1.3e-4 relative), then stable.

Consequence: spec 180 offers typed rate-law forms for conventional reactors. The photobioreactor (light, environment, state, harvest) remains outside DWSIM.

### 10.2 Verification of external claims (`out/w166/gBver.report.md`)

The independent verification found the biology literature summary (`gBbio`) **unreliable as a parameter source**. Problems included many wrong or non-resolving DOIs and values attributed to papers that do not contain them. For example, Bernard & Rémond (2012) calibrated *N. oceanica*, not *N. gaditana*, and contains no quota model. The "benchmark acceptance criteria" were fabricated, and the "Beer–Lambert errs 100–300 %" citation does not exist. The equation *forms* (Monod, Haldane, Droop, CTMI, two-flux, Han PSU) are standard and unaffected.

Consequences:

1. This record adopts **no** literature parameter values.
2. Spec 169 must build any *N. gaditana* parameter set with per-value, human-checkable source evidence (resolved DOI, page or table, quoted value, species/strain, conditions) and an expert-review state before any set is labelled beyond `candidate`.
3. Benchmark datasets for validation (e.g. the Solix flat-panel *Nannochloropsis* data of Quinn et al. 2011, which is not tubular) are selected inside 169/172 with the same discipline.

Verified software facts:

- pvlib 0.16.1 BSD-3-Clause; scikit-sundae BSD-3-Clause; FMPy BSD-2-Clause; CasADi LGPL-3.0+; OpenFOAM and DWSIM GPL-3.0; QSDsan NCSA.
- BioSTEAM and thermosteam are permissive (MIT in PyPI metadata; NCSA in the repository LICENSE).
- DWSIM has no native FMI.
- Data terms: PVGIS reuse with attribution under Commission reuse policy; Copernicus Marine free reuse with attribution. **Open-Meteo's free API is non-commercial** (commercial use needs a subscription or a self-hosted AGPL server), so it is not a default source.

DWSIM source defines user-defined reaction kinetics (`ReactionKineticType.UserDefined` with `Expression` or `PythonScript` modes) evaluated in CSTR/PFR. The pDWSIM probe exercised a different field (`ReactionKinFwdType=Expression`), so a targeted follow-up probe (pDWSIM2) decides whether Monod-type *substrate* kinetics can live in DWSIM reactors for simple steady bioreactions (§10.3).

## 11. Maintainer decisions requested

None block the plan. Four choices are recorded as defaults that the maintainer may override:

1. **uPlot (MIT)** as the single chart library (171/173).
2. No live weather or ocean API fetch; offline file import plus pvlib generation only (171). A provider setting with egress approval is a separate future decision.
3. BioSTEAM deferred to an optional out-of-process TEA worker (178) rather than a core dependency.
4. Seawater is treated as water for carrier thermodynamics until a qualified seawater basis exists. O₂ and CO₂ solubility for culture balances use salinity-corrected correlations inside the bio engine (175), and results are labelled accordingly.
