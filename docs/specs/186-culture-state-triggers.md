# 186 — State-triggered culture actions with exact crossing times

State: **accepted and ready**. Written under the maintainer directive of 2026-10-07 ("Lane D — … then add state-triggered harvest cleanly"). Reviewed against the dynamic engine at master `9fecfe1b`.

- **Hard dependency:** 185.

## Fresh evidence (master `9fecfe1b`)

- **Polled conditions.** 172 conditional events are polled at `controller_cadence_s` (`_conditional_events`, `dynamic_engine.py:1355`), so trigger times are quantized to the sample.
- **Re-arm.** It is a hysteresis band only. There is no cooldown and no fire cap.
- **Observables.** `observed` accepts only `<unit>.<X|N|O2>` in kg/m³ (`:117-123`).
- **Integrator.** `dynamics.integrate_ode` exposes no events. The pinned scikit-sundae 1.1.3 `CVODE` supports `eventsfn`, `num_events` and terminal events.

## Decision

1. **Root-found triggers.** `dynamics.integrate_ode` gains optional root functions.
   - A 185 action event may carry a `condition`: `observed`, `direction` (above/below), `threshold` (kg/m³), `hysteresis` ≥ 0, `cooldown_s` ≥ 0, `max_fires` ≥ 1, and an earliest `time_s`.
   - The engine passes g = observed − threshold for armed conditions. Integration stops at the crossing, and the actions apply at that time.
   - Integration then restarts, and a second root (the band edge) re-arms the condition.
   - A condition cannot fire again within `cooldown_s` or after `max_fires`.
2. **Observables:**
   - `<unit>.X|N|O2` for a PBR or tank;
   - `<unit>.loop_X|loop_N`: the inventory mean of that unit's culture loop.
3. **Runtime volume guard.** A conditional action that would leave [`min_volume`, `max_volume`] fails the run with `EVENT_VOLUME_INVALID_RUNTIME`.
4. **Provenance.** One log entry per fire. It links the condition, the root time, the observed value, and the 185 action record.
5. **Legacy unchanged.** 172 conditional events keep polling.

## Acceptance

1. **Exact crossing time.** A constant-rate reference: `loop_X ≥ X_high` fires within 1e-6 relative of the analytic crossing time.
2. **Chatter control.** Hysteresis and cooldown prevent chatter on an oscillating forcing, `max_fires` is honoured, and re-arm happens only after leaving the band.
3. **Campaign equivalence.** A state-triggered campaign closes every event and the aggregate balance, as in 185. It matches an independent `solve_ivp` with terminal events within 1e-4.
4. **Runtime refusal.** A runtime over-draw fails with the typed error.
5. **Compatibility.** The 172 polling tests are unchanged.
6. **Gates.** The full backend suite in a clean environment; ruff, ratchet and architecture.

## Non-goals

- Rate-of-change or compound conditions.
- Controllers actuating impulsive actions.
- UI (173).
