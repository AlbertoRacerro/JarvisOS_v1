# 184 — Culture loops: internal circulation separated from net throughput

State: **accepted and ready**. Written under the maintainer directive of 2026-10-07 ("Lane C — fix the biological / hydraulic semantics"). Reviewed against the PBR unit and the dynamic engine at master `9fecfe1b`, with an independent current-code review.

- **Hard dependencies:** 170 and 172 (merged), and 183. 183 must be merged before implementation starts.
- **Place in the roadmap:** BlueRev circulates a finite culture through short tubes and dark nodes for days. Its biology depends on net feed and harvest, not on how fast the culture circulates. Jarvis must represent that directly. Semi-batch campaign events are 185; state-triggered actions are 186.

## Fresh evidence (master `9fecfe1b`)

### Steady T1 PBR (`process_stack/pbr_unit.py`)

- The unit is a 0-D well-mixed loop. V is the tube volume n·π·d²·L/4.
- D is the process inlet flow over V (`:813-817`).
- `liquid_velocity` is the unit's *internal* circulation. It feeds only:
  - the hydraulics (Re, ΔP and pumping power, `:707-730`);
  - the `PBR_FEED_EXCEEDS_CIRCULATION` comparison (`:890-895`).

So within one PBR, circulation and throughput are already separate: the process inlet *is* the net throughput.

The conflation appears only when internal circulation is drawn as process streams. A PBR fed through a recycle loop then reports these on the gross, recycle-inclusive inlet:
- `dilution_h` and `hrt_d`;
- `PBR_HRT_OUT_OF_RANGE`;
- the washout rule.

The finding's "Fresh feed" wording is wrong in that case too.

### Steady circulation loops are ill-posed for biology

- With zero net throughput, the carrier inventory of a closed loop is a neutral tear mode (q = 1).
- With net throughput, the productive state satisfies μ − k_d ≈ D_net. The first-order terms of the culture tear map cancel there, leaving |1 − q| = O(X·|∂μ/∂X| / D_pass), where D_pass is the per-pass rate Q/V_unit. For BlueRev (μ_max ≈ 7e-6 s⁻¹, D_pass ≈ 0.13 s⁻¹) that is 1e-4 or less.
- Each steady PBR also passes its 24 h-mean outlet downstream. In a loop that circulates in minutes, every segment therefore sees a constant inlet, and the diurnal state (including the O₂ peak) is erased.
- 183 makes such loops truthfully unconverged. It cannot make them physically meaningful.

### Dynamic engine (`process_stack/dynamic_engine.py`)

- Each participating PBR is a CSTR on its summed inlet flow (`:954-973`). Recycled culture carries its own state, so a tanks-in-series loop integrates correctly in time.
- Mixer, Splitter, Pump, Recycle and SpecifiedSeparator are algebraic. There are no holdup vessels.
- Stream flows are solved by `np.linalg.lstsq` without a rank check, in two places:
  - `_topology`, `:326`;
  - `_rebalance_flows`, `:1401-1457`, which runs after every feed, dilution, controller and splitter action.
- A loop's circulating flow lies in the null space of the balance equations. It is silently set to the minimum-norm value, which is often 0 and is then reported as `ZERO_THROUGHFLOW`. Nothing can specify it.
- The engine reports no hydraulics.
- `manifest.productivity` uses the PBR volumes only (`:1103`).

## Decision

### 1. Two named quantities, never aliased

| Quantity | Definition | Drives |
|---|---|---|
| **Circulation** | The flow that moves culture around a loop. Within one PBR it is n·u·A from `liquid_velocity`. Around a culture loop it is a scenario specification (§3). | Velocity, Re, ΔP, pumping power, pass transit time, per-pass rate D_pass. |
| **Net throughput** | Flows that cross the culture inventory boundary: fresh feed or makeup in; harvest, concentrate or purge out. | Net dilution D_net, culture residence time V_loop/Q_net,out, washout. |

### 2. Steady T1 PBR (170): additive only

The equations and every existing output key and value are unchanged.

New outputs:
- `circulation_flow_m3_h` = n·u·π·d²/4;
- `pass_transit_time_s` = L/u;
- `circulation_to_throughflow_ratio`.

Wording changes:
- The display labels of `dilution_h`, `hrt_d` and `volumetric_flow_m3_h` say "process-inlet basis".
- `PBR_FEED_EXCEEDS_CIRCULATION` reads "Process throughflow exceeds internal circulation". No test or frontend file pins this text.

**New warning `PBR_LOOP_AS_PROCESS_RECYCLE`.**
- `mixed_runtime` emits it, using `partition["consumed"]`, when a PBR lies on a Jarvis-converged tear cycle and its process-inlet dilution exceeds 10 × μ_max of its card.
- It states that the loop behaves as internal circulation, and recommends a dynamic culture loop.

### 3. Dynamic engine

**`HoldupTank`** is a new registry unit: a dark, well-mixed culture vessel. It is **dynamic-only** in this slice.
- Steady Run and materialize refuse a draft containing one, with `HOLDUP_TANK_DYNAMIC_ONLY`. The draft itself stays valid.
- Parameters:
  - `liquid_volume` (m³, > 0): the initial and nominal working volume;
  - `min_volume` and `max_volume`, used by 185, with 0 ≤ min ≤ liquid ≤ max;
  - `temperature` (K);
  - optional `oxygen_kla` (1/s, ≥ 0) and `oxygen_saturation` (kg/m³, > 0), set together.
- The tank has no own model pin. Its loss term and N quota come from the participating network's single model card, which 172 already requires to be shared by coupled units.
- Its biology is dark: μ = 0, plus the card's loss at the tank temperature. This uses a dark-only growth constructor.
- Tanks are listed in `scenario.units` alongside PBRs. The participating-unit limit is raised from 8 to 12 (at most 8 PBRs).
- `scenario.initial` accepts tanks, with `{X, N, O2}` required as for PBRs.
- `TOPOLOGY_CARD_MISMATCH` and the supported-type whitelists include the tank.
- The state layout uses one slot-offset helper in place of the hard-coded `i*7` arithmetic.

**Specified circulation.**
- `scenario.circulation` maps a Pump tag to a volumetric flow (m³/s, > 0). The equation Q_pump_outlet = value joins the flow balance.
- The steady path ignores scenario data, as now.

**One flow solver.** `_solve_flows(topology, overrides)` replaces both `lstsq` call sites and carries the circulation equations.
- If `matrix_rank` is below the number of unknown streams, the system is refused with `FLOW_UNDERDETERMINED`, naming the units of each unspecified cycle. There is no minimum-norm fallback.
- An inconsistent system keeps `FLOW_BALANCE_UNSOLVED`. Full rank only makes the least-squares solution unique, so after the solve the relative volumetric conservation residual max|A·Q − b| / max(|b|, |Q|) must be ≤ 1e-9; otherwise the run is refused with `reason: conservation_residual`, the residual and the streams of the worst equation. A solution that needs a negative flow is refused with `reason: negative_flow`. The least-squares fit of an inconsistent system is never accepted.
- **Circulation-implied splitters.** A Splitter inside a loop whose Pump circulation is specified takes its split from continuity (net boundary inflow leaves through it); its declared ratios are not equations. Dilution events and controllers acting on it are refused with `SPLIT_IMPLIED_BY_CIRCULATION`; the operator changes the boundary feed instead. This is a **steady pumped-loop bleed only**: it is not the harvesting mechanism for semi-batch operation.
- A closed loop with no boundary streams is valid when its circulation is specified.
- `ZERO_THROUGHFLOW` remains for a PBR whose solved inlet is zero.
- Feed, dilution, controller and splitter actions re-solve with the circulation equations kept.

**Hydraulics in dynamic runs.** These are reported per flow interval in the manifest and series:
- For a PBR **inside a culture loop with specified circulation**, the solved inlet flow is the circulation. u = Q_in/(n·A), and Re, ΔP and power are computed from it with the 170/104 hydraulics. If u differs from the declared `liquid_velocity` by more than 1 %, the engine raises `PBR_CIRCULATION_VELOCITY_MISMATCH` (warning). The solved flow is authoritative.
- For **any other PBR**, the inlet is net throughput. Hydraulics come from the declared `liquid_velocity`, as in 170, and no mismatch check applies.

### 4. Culture loops and KPIs

A **culture loop** is a strongly connected component of the participating network that is non-trivial (contains a cycle) and contains a PBR. Pump and Recycle are ordinary nodes; the existing Tarjan in `mixed.components` serves. A loop's id is the tag of its lexicographically first PBR.

For each loop the manifest reports these, constant between events:
- V_loop = ΣV_PBR + ΣV_tank;
- illuminated fraction ΣV_PBR/V_loop;
- Q_circ: the maximum flow over streams internal to the component;
- pass transit time V_loop/Q_circ;
- net boundary inflow and outflow;
- D_net = Q_net,out/V_loop;
- culture residence time 1/D_net (or "∞, batch").

New series channels:
- `{tag}_pass_rate_1_s` per PBR;
- `{loop}_X_mean` and `{loop}_N_mean` (inventory means);
- `{loop}_biomass_kg`.

Existing keys are not renamed. `manifest.productivity` is unchanged, and `productivity_loop` adds the net basis: harvested kg per V_loop per day.

### 5. Transport scope in T1 (recorded, not hidden)

- In T1, "transport" means velocity, Re, pass transit time and the per-pass rate. These follow the circulation.
- `oxygen_kla` remains a declared unit parameter. A velocity-dependent kLa, heat transfer and degassing belong to 175.
- Light/dark cycling from mixing and axial dispersion belong to 179 (T3).
- The steady periodic-state solver, its branch rule, the 183 tear solver and the DWSIM downstream sampler are unchanged.

## Acceptance

Backend tests. Each uses an independent reference.

1. **Circulation without dilution.** A closed loop of 4 PBRs, 2 tanks and a Pump with specified circulation, with no boundary streams, under constant light for 10 d.
   - The loop is accepted, grows from the inoculum, and never washes out.
   - The aggregate biomass and N balances close within max(1e-6, 100·rtol) relative.
   - The trajectory matches an independent `solve_ivp` of the same tanks-in-series model within 1e-5 relative.
   - The geometry is chosen so that μ_max·τ_loop ≤ 1e-5. Under that condition the trajectory also matches a single well-mixed inventory with the illuminated fraction, within 1e-3.
2. **Circulation drives hydraulics, not biology.** Scale the circulation by 0.25×, 1× and 4×.
   - u, Re, ΔP, power and the transit times follow the 104 correlations.
   - The loop-mean biomass changes by less than the derived bound 10·μ_max·τ_loop·μ_max·t, and by less than 1e-3 in the test geometry.
3. **Net throughput sets dilution.** Constant light, an N-replete feed, and a matching harvest outflow at D_net ∈ {0.1, 0.25, 0.5} d⁻¹.
   - The loop reaches the steady biomass found by an independent root solve of f·μ(X) − k_d = D_net, where f is the illuminated fraction, with self-shading.
   - D_net above the maximum net growth washes out.
   - A `feed_change` event inside the pumped loop keeps Q_circ.
4. **Typed refusals.**
   - An unspecified circulation is refused with `FLOW_UNDERDETERMINED`, naming the cycle's units.
   - A velocity mismatch warns.
   - A steady Run with a tank is refused.
5. **Steady path.**
   - Existing 170/180/181/183 tests are unchanged, and the new outputs are present.
   - `PBR_LOOP_AS_PROCESS_RECYCLE` keeps the 10 × μ_max threshold on real DWSIM, on the 183 recycle shape at 0.9 return converged with Broyden. With the 183 geometry (100 m tubes) the process-inlet D is 0.184 h⁻¹ = 2.3 μ_max, so it does **not** fire. With 10 m tubes, D exceeds 10 μ_max and it fires. It never fires on an open chain. (Amended at implementation: the 183 geometry alone does not reach the threshold.)
   - Every existing dynamic test topology stays full-rank and green.
6. **Real DWSIM.** The 172 real-DWSIM downstream test passes. A continuous harvest stream leaving a culture loop is sampled downstream with DWSIM-solved outputs.
7. **Performance.** A 30-day BlueRev-scale loop (4 PBRs, 2 tanks, Q_circ ≈ 5e-4 m³/s) runs in under 1 s per simulated day on the qualification host. The wall time is recorded.
8. **Gates.** The full backend suite in a clean environment; ruff, ratchet and architecture; and the frontend build. The PBR results view shows the new circulation outputs, and the process-inlet labels.

## Non-goals

- Semi-batch events, volume changes and campaign KPIs (185); state-triggered actions (186). Semi-batch harvest is a dynamic inventory operation (draw a fraction → inventory decreases → optional refill) on tanks in 185. It must not be implemented by actuating a circulation-constrained hydraulic Splitter.
- Steady HoldupTank.
- Spatial loops, light/dark cycling from mixing, and orientation (175/179).
- Gas–liquid units, pH and CO₂ (175).
- The Dynamic Studio UI (173).
- Making steady circulation loops converge. They stay truthfully unconverged and carry the warning.
