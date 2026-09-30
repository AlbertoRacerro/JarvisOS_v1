# 158 — Process DWSIM parity beta

State: **ready**. Combined definition, contract and readiness under the maintainer directive of 2026-09-30. Dependency 155 is `merged` at master `d5811792`. This slice extends the 155 registry, compiler and editor; it does not change the 155 architecture.

## Binding architecture (unchanged from 155)

- The Jarvis draft is the instantaneous, authoritative, typed document. Ordinary edits never contact DWSIM.
- DWSIM is the derived runtime for materialization, validation and solving. Validate and Run compile the exact revision into a fresh DWSIM flowsheet, read it back, and refuse the solve on any mismatch.
- Every state Jarvis accepts compiles deterministically into DWSIM and reads back equivalently. The fingerprint stays deterministic.
- The registry stays the single source for the draft schema, inspector forms, compiler mapping and read-back.
- There is no mathematical reimplementation. Every number Jarvis shows as a result comes from DWSIM.

## Fresh runtime evidence (pinned DWSIM 10.2.9 MCP, digest `d20f9742…`, 2026-09-30)

Probe scripts and raw outputs are in `jarvis-control/work/evidence/158/probe/`.

- The MCP exposes 53 tools. `dwsim_unitop_set` matches names against DWSIM's property system. It reports the complete settable-name list for an unknown name, and the complete enum list for an invalid enum.
- `dwsim_flowsheet_degrees_of_freedom` lists the specification slots (property, units, required) that each calculation mode reads.
- `dwsim_scenario_snapshot` / `dwsim_scenario_compare` return every property of every object, each with id, name, DWSIM unit and a `specification` flag. A water/methanol stream has about 120 properties: state, flows, phase splits, per-compound fractions and flows, enthalpy, entropy, Cp, Cp/Cv, Z, the Gibbs/Helmholtz/internal energies, viscosity, thermal conductivity, diffusion coefficients, fugacity and activity coefficients, and bubble/dew points.
- Heater and Cooler modes: `HeatAdded`, `OutletTemperature`, `EnergyStream`, `OutletVaporFraction`, `TemperatureChange`, `HeatAddedRemoved`. The energy stream connects as energy feed on native port 1. `EnergyFlow` (kW) is settable on the energy stream. A heater in `EnergyStream` mode solved from a 50 kW energy stream.
- Splitter:
  - modes are `SplitRatios`, `StreamMassFlowSpec`, `StreamMoleFlowSpec`, `StreamVolumetricFlowSpec`;
  - it has 1 inlet and up to 3 outlets (ports 0–2);
  - it exposes ratio and flow-spec properties;
  - it saves `<Ratios>`.
- HeatExchanger:
  - hot side is feed/product port 0, cold side is port 1;
  - its 11 modes include `CalcTempHotOut`, `CalcTempColdOut`, `CalcBothTemp_UA`, `CalcArea`, `PinchPoint` and `ThermalEfficiency`;
  - `FlowDir` is `CounterCurrent` or `CoCurrent`;
  - U·A mode solved and reported duty, LMTD, efficiency and outlet temperatures.
- Recycle: 1 inlet and 1 outlet, with no required specification. Convergence settings are exposed.
- PFR:
  - modes are `Isothermic`, `Adiabatic`, `OutletTemperature`, `NonIsothermalNonAdiabatic`, `HeatExchange`;
  - `HeatExchange` is DWSIM's native jacketed/coolant model. Its inputs are overall U, heat-exchange area, coolant inlet temperature, coolant mass flow, coolant Cp and coolant flow direction. There are further optional wall and film-coefficient options;
  - geometry is volume and length, plus catalyst loading/void/diameter and pressure drop;
  - it requires a reaction set;
  - it requires an energy stream on energy-feed port 1: without it the solve fails with "No energy stream associated with the reactor";
  - the MCP has **no reaction-definition tool**. A kinetic reaction and reaction set written into the saved native XML and reloaded through `dwsim_flowsheet_load` are recognised: DOF reports 1 active reaction, `ReactionSetID` is settable, and the jacketed PFR solved (outlet 38.5 °C, duty −74.6 kW, residence time 1862 s).
- DistillationColumn:
  - feed connects on port 0, distillate on product port 0, bottoms on product port 1;
  - stages, condenser type and spec values are settable;
  - the MCP **refuses** to connect condenser and reboiler energy streams, and exposes no feed-stage property. The solve then fails with "stream connections to the column are missing";
  - so the column is not materializable through MCP calls alone.

## Accepted capability

### 1. Evidence-derived capability manifest

- A repository probe script (`scripts/qualification/158/`) regenerates a checked-in manifest from the pinned runtime. For each supported native type it records:
  - calculation modes and enum values;
  - settable property names;
  - DOF slots per mode, with property, units and required flag;
  - native ports;
  - the result property catalogue (id, name, unit, specification flag).
- Every Jarvis registry field classifies each property as:
  - `input`: writable, materialized and read back;
  - `result`: calculated and read-only, shown after a solve;
  - `advanced`: system, dynamics or solver metadata, not exposed as writable.
- A deterministic test fails if a Jarvis `input` property, mode, enum value or port is absent from the manifest. Jarvis never exposes a writable field that the pinned runtime did not accept.

### 2. Richer existing units

- Heater and Cooler: all six native modes where materialization and read-back are proven, with their DOF inputs (outlet T, duty, ΔT, outlet vapor fraction, energy stream), pressure drop and efficiency.
- Pump, Valve, Mixer and Flash: the modes and inputs their manifest proves, for example Mixer pressure calculation and the Flash vessel's flash-condition overrides. A mode that cannot be read back equivalently stays unexposed.

### 3. New beta objects

Each new object gets registry, schema, inspector, compiler, read-back and tests.

- **Energy Stream.** A distinct draft object connected to units' energy ports. It may carry a duty specification only where the connected unit's mode reads it. Its duty is otherwise a DWSIM result.
- **Splitter.** 2–3 outlets, split-ratio mode, and flow-spec modes where proven.
- **Heat Exchanger.** Hot and cold inlet/outlet ports, the proven calculation modes and their inputs, flow direction and side pressure drops.
- **Recycle.** A tear block. Draft connections may form loops only through a Recycle. Jarvis validation reports a loop without a Recycle before any DWSIM call.
- **PFR.** A kinetic reactor with all five native thermal modes and their native inputs. `HeatExchange` exposes DWSIM's own coolant/jacket parameters, making it the non-adiabatic jacketed configuration. The draft requires the energy stream DWSIM requires.
- **Reactions.** The draft document gains typed kinetic reactions:
  - stoichiometry, orders and base reactant over declared compounds;
  - phase, basis, and Arrhenius A and E, each with its DWSIM unit;
  - reaction sets that reactors reference.
  - They are materialized as DWSIM-native `Reactions` / `ReactionSets` in the saved case, reloaded, read back and compared like every other field. The injected XML contains only fields proven by the probe; unsupported kinetics types (expression kinetics, heterogeneous/LHHW, equilibrium and conversion reactions) stay visibly unsupported.
  - CSTR may reuse the same mechanism when it is proven by the same tests; otherwise it stays unsupported.
- **Distillation Column.**
  - It is supported only if the implementation proves a deterministic materialization and a real solve for feed stage, condenser/reboiler energy streams and the two column specifications. The route may use the same native-XML-plus-reload mechanism, verified by read-back.
  - Otherwise it remains visibly unsupported with the recorded probe reason. It is never offered with guessed fields.

### 4. Rich inspectors and results

- Before a run, inspectors show only valid writable inputs, grouped by mode, with the display units the registry offers. Values are converted server-side, as in 155.
- After a run, every stream, energy stream and unit exposes the DWSIM-reported result set captured at solve time from the snapshot/compare catalogue. It is shown read-only with DWSIM's units and grouped for readability:
  - conditions and flows;
  - phases;
  - composition;
  - thermodynamic properties;
  - transport properties;
  - equilibrium.
- Grouping is presentation only. Values are never computed in Jarvis. Specification rows and result rows stay distinguished. Results remain bound to the exact revision and fingerprint, as in 155.

### 5. Orthogonal canvas routing

- Stream rendering uses horizontal and vertical segments only; curves are removed.
- The operator can adjust routes through persisted layout waypoints or segment offsets: drag a segment, add or remove a bend, reset.
- Routes are layout-only state. They are excluded from the expected materialization and the fingerprint, and never sent to DWSIM. A route-only revision does not make current results stale.
- Unit drag and edit stay optimistic and instant.
- The 155 proposal highlight and old→new badges keep working on the new routes and inspectors.

### 6. Proposals and agents

- Hermes `jarvis_process_read` / `jarvis_process_propose` derive their proposable properties from the extended registry automatically. Only `input` properties are proposable.

## Boundaries / non-goals

- No new solver, no frontend engineering math, no DWSIM round-trip on edit.
- No dynamics on drafts. The 149 editor stays the dynamics surface.
- No compressors, expanders, pipes, absorbers, Gibbs/equilibrium/conversion reactors, or property-package parameter editing in 158.
- No global `/runs` integration.
- Synthetic public fixtures only, such as water/methanol and the textbook ethylene-oxide hydration kinetics. `private_domain_data.enabled=false` stays.

## Required evidence

- **Deterministic tests:**
  - the manifest cross-check;
  - operations and validation for every new object, including energy ports, loop-without-recycle, reaction stoichiometry and compounds, and a reactor without a reaction set or energy stream;
  - compiler plan and expected normalization per new type, including reactions;
  - read-back comparison with injected mismatches on a new unit, a reaction field and an energy connection;
  - route ops excluded from the fingerprint and from staleness;
  - proposal filtering to `input` properties.
- **Frontend tests:**
  - an orthogonal path has only axis-parallel segments;
  - a waypoint edit produces a layout op only;
  - inspectors render inputs vs results distinctly;
  - no Validate/Run call happens during edits.
- **Real host acceptance** on the canonical WSL host with the pinned DWSIM and a real browser:
  1. the richer existing-unit inspectors;
  2. each new beta unit materializes, reads back equal, and solves in a synthetic flowsheet: an energy-stream heater, a splitter, a heat exchanger, a recycle loop, and a jacketed `HeatExchange` PFR with a kinetic reaction;
  3. the column is proven solved or shown unsupported;
  4. repeated compile gives the same fingerprint;
  5. an injected mismatch on a new field refuses the solve with its path;
  6. edits make no DWSIM calls;
  7. orthogonal routes are edited, persisted, and leave the fingerprint unchanged;
  8. the grouped result inspector is shown after a run;
  9. no manifest-absent field is writable.
- Exact-head CI green.
