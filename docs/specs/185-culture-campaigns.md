# 185 — Semi-batch culture campaigns: conservative time-triggered inventory events

State: **accepted and ready**. Written under the maintainer directive of 2026-10-07 ("Lane D — semi-batch / fill-and-draw culture operation"). Reviewed against the dynamic engine at master `9fecfe1b`, with an independent current-code review.

- **Hard dependency:** 184, which provides culture loops, HoldupTanks and the single flow solver.
- **Place in the roadmap:** the intended BlueRev v0.1 operation is a campaign. Inoculate, then grow with no harvest while the culture circulates. Then harvest a fraction, separate, refill and regrow, and repeat. That is a dynamic inventory problem. Following the directive, this slice delivers deterministic time-triggered campaigns first. State-triggered actions are 186.

## Fresh evidence (master `9fecfe1b`, `process_stack/dynamic_engine.py` and `dynamic_models.py`)

- **Harvest.** `harvest` multiplies X, N and O₂ by (1 − f) at constant volume (`_apply_event`, `:1183-1230`). That is an *implicit refill with blank water*: no N, no O₂, no salinity. It is booked only as a Δc·V impulse, and the harvested N and O₂ are not product inventory.
- **Inoculation.** `inoculation` overwrites concentrations.
- **Missing events.** There is no refill, restore-volume or dose event. `ScheduleEvent.medium` is parsed and never read.
- **Volume.** Volume is a constant. The accumulator slots 3–6 are concentration integrals, multiplied by the constant `volume_m3` (`:814`, `:1077-1094`).
- **Event logging.** Feed, dilution and setpoint events log no before/after.
- **Event rows in the series.** When an event coincides with an output time, the series row is overwritten with the post-event state.
- **Balances.** They are computed once and reported, never asserted.
- **Productivity.** Whole-run productivity is the only KPI. There are no cycles.

## Decision

### 1. Inventory state

- Each HoldupTank (184) gets a liquid volume state V_k. It is constant between events, because flows stay balanced, and changes only at events.
- PBR tubes stay full.
- The accumulator slots become **inventories in kg**: generation, transfer and removal. Concentration integrals are retired, so volume changes cannot mis-scale the history.
- Explicit campaign accumulators record harvested biomass and N, purge, added medium N, added volume and removed volume.

### 2. Actions

A `ScheduleEvent` may carry an ordered `actions` list, executed atomically at its instant. It keeps the 172 `time_s` / `every_s` / `count` / `end_s` expansion and the stable ordering. Legacy single-type events keep their 172 behaviour.

| Action | Fields | Effect |
|---|---|---|
| `draw` | `tank`; `volume_m3` or `loop_fraction` | Removes culture from the tank at the tank's current concentrations. A `loop_fraction` f removes f·V_loop of the tank's loop. |
| `separate` | `recovery` (fraction in (0, 1]); `concentration_factor` > 1; `return_to` (a tank, or `none`) | Acts on the culture just drawn, with the same definition as the existing SpecifiedSeparator. The registry takes recovery in percent; actions take a fraction. **Concentrate:** volume V·recovery/CF, biomass recovery·m_X, dissolved species at draw concentration. **Clarified liquid:** the rest. It goes to `return_to`, or becomes **purge** when `none`. |
| `refill` | `tank`; `volume_m3` or `to_volume_m3`; `medium {N, O2}` (kg/m³, X = 0) | Adds medium. |
| `dose` | `tank`; `nitrogen_kg`; optional `volume_m3` (default 0) | Adds nutrient mass. |
| `inoculate` | `tank`; `volume_m3`; `culture {X, N, O2}` | Adds culture. |

**Harvested product.** Without `separate`, the whole draw is harvested product. With `separate`, only the concentrate is; purge is booked separately.

**Mixing.** Every addition mixes conservatively: c ← (c·V + c_add·V_add)/(V + V_add). Quota N travels with X.

**Legacy events.** `harvest` and `inoculation` are unchanged and logged with `semantics: "implicit_blank_refill"` and `"overwrite"` respectively.

**Volume guard.** A time-triggered action that would take a tank outside [`min_volume`, `max_volume`] is refused in `prepare()` with `EVENT_VOLUME_INVALID`. Volumes are deterministic between events, so the check is exact.

### 3. Conservation is asserted

- **Every action event** records the actions, `pre_state`, `post_state` and its inventory deltas: added, removed, harvested, purged and returned. Liquid volume, biomass, total N (dissolved plus quota) and O₂ must close within 1e-9 relative, with a 1e-15 floor. Otherwise the run fails with `EVENT_BALANCE_NOT_CLOSED`.
- **A run** with any action event must close its aggregate balance before it can succeed: initial + boundary + generation + additions − removals − final. The tolerance is max(1e-6, 100·rtol) relative to the throughput scale, plus an absolute floor. Otherwise it fails with `BALANCE_NOT_CLOSED`, keeping its partial artifacts and diagnostics.
- **Legacy runs** without action events keep today's reported, unasserted balance.

### 4. Series and log

- At an action event instant the series carries two rows with equal `t_s`, marked `phase: pre|post` and with the event order.
- Series consumers that interpolate (`_result_series` flow lookup) use the post row from that instant on.
- Legacy events keep today's single row.
- Feed, dilution and setpoint events now log their before/after values.

### 5. Campaign KPIs

A cycle runs from one `draw` on a loop to the next. For each cycle the manifest reports:
- length;
- harvested biomass and concentrate concentration;
- purge;
- medium and N added;
- loop-mean X before and after the draw;
- net volumetric productivity: harvested kg per V_loop per day;
- areal productivity: harvested kg per illuminated area π·d·L·n per day.

The campaign summary reports totals, the mean of the last k cycles, and cycle-to-cycle convergence: the relative change of pre-draw X over the last three cycles. It is labelled "periodic campaign reached" when that change is below 1 %.

## Acceptance

Backend tests, each with an independent reference:

1. **Hand-computed fill-and-draw.** One PBR and one tank, with specified circulation, in the dark with zero loss. The sequence is: draw 20 %, separate (0.95, CF 20, return to the tank), refill to volume with medium N, dose N.
   - Every inventory and concentration *immediately after each event* matches a closed form to 1e-12.
2. **Recurring campaign.** Every 48 h: draw 20 %, separate, refill to volume. Ten cycles with growth.
   - Every event balance and the aggregate balance close.
   - The trajectory matches an independent `solve_ivp`-plus-events implementation within 1e-4 relative.
   - Cycle KPIs match an independent recomputation from the series.
3. **Guards.**
   - An over-draw and an over-fill are refused in prepare with `EVENT_VOLUME_INVALID`.
   - A forced imbalance (test hook) gives `EVENT_BALANCE_NOT_CLOSED`.
4. **Compatibility.** Every 172 dynamic, jobs and downstream test is unchanged. Legacy semantics are labelled in the log.
5. **Performance.** A 60-day BlueRev-scale campaign (4 PBRs, 2 tanks, 48 h cycles) runs in under 1 s per simulated day on the qualification host. The wall time is recorded.
6. **Gates.** The full backend suite in a clean environment; ruff, ratchet and architecture.

## Non-goals

- State-triggered actions (186).
- The Dynamic Studio UI and campaign editor (173). This slice is headless API and engine.
- Downstream DWSIM sampling of impulsive draws. A batch has no flow rate; continuous harvest streams remain sampled.
- Continuous level control and evaporation.
- Salinity and DIC in medium (the dynamic state is X, N and O₂), and pH or dosing chemistry (175).
- Membrane physics (177), economics (178), and harvest optimization.
