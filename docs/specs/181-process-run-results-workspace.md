# 181 — Process run outcomes, results navigator, KPIs and flowsheet workspace

State: **accepted and ready**. Written under the maintainer directive of 2026-10-06 ("Process UI / run semantics", "Results — immediate product requirement", "Flowsheet UX — do now"). Reviewed against the current Process code at master `b99e4324` and real DWSIM 10.2.9.

- **Hard dependencies:** 158, 162, 167, 168 and 170 (all merged). It changes no science and no solver.
- **Place in the roadmap:** this slice makes steady-state Process runs inspectable and truthful. It comes before 173 (dynamic studio) and before any BlueRev rerun is treated as evidence.

## Fresh evidence

The code audit is at `/home/thera/jarvis-control/work/out/s1/` (process audit, 2026-10-06). It found:

1. **Green does not mean solved.**
   - The readiness chip says "Ready to run" whenever there is no Jarvis `blocker` finding (`ProcessDraftEditor.tsx:1262`). It ignores DWSIM and run outcomes.
   - A non-mixed Validate builds the case and runs the DWSIM check, but never solves. Its panel text, "DWSIM reproduced the draft exactly…", reads like success.
2. **Non-convergence is spread across five representations.**
   - Non-mixed DWSIM non-convergence is `status: failed` with `solve.ok=false` and `solve.failed_objects[]`.
   - Mixed runs use `unconverged` with `mixed_solve.reason` and `history[]`, or `segment_failed` with `failed_units`.
   - Exceptions become `materialization_*`, `JARVIS_SOLVE_TIMEOUT`, `runtime_failed` and others.
   - Only `materialization_mismatch`, `materialization_failed`, `failed` and `check_failed` get failure styling. `unconverged`, `segment_failed`, `runtime_failed` and timeouts look neutral.
3. **Results exist but are hidden.**
   - Non-mixed `failed` and mixed `unconverged` runs persist full stream and unit data in `run.json`.
   - `results_state` only ever picks `status == "completed"`, so the UI shows "No results".
   - After a later failed non-mixed attempt, an older completed run stays "current". Only mixed failures demote it (`draft.py:963`).
4. **A negative-coordinate bug turned valid drafts into failed runs.** DWSIM stores |x| and |y|, so a draft object above or left of the origin failed read-back. Fixed separately by PR #784 (`fix/158-negative-canvas-coordinates`).
5. **Results surface.**
   - Today only a stream table (T, P, flows, vapour fraction) and per-unit inspector fieldsets exist.
   - There is no composition or culture table, no boundary in/out view, no KPI, and no unit/stream result navigation from the canvas.
6. **Workspace.**
   - The Thermo/species fieldset fills the right inspector whenever nothing is selected. It stacks into the main column below 1100 px.
   - The canvas is a hand-built SVG capped at 520 px high, with an auto-fit `viewBox`. There is no zoom or pan, and there is no viewport library to reuse.
7. **Authoritative KPI inputs that already exist.**
   - The PBR reports `volumetric_productivity`, `net_biomass_production`, `outlet_biomass_throughput`, `volume_m3`, `volumetric_flow_m3_h` and `biomass_mean` (`pbr_unit.py:838`).
   - The tube count, inner diameter and length are draft parameters.
   - Stream culture values, mass fractions and flows are in `run.streams` / `run.culture`.
   - T1 does not model carbon: "carbon and phosphorus assumed externally supplied and non-limiting" (170).

## Decision

### 1. One backend run outcome

`draft.run_outcome(run) -> dict` is the single authority for a draft run's operator-facing outcome. It is stored on every new `run.json` as `outcome` and computed on read for older runs. The frontend never derives an outcome from raw statuses.

`outcome.state` takes exactly one of these values:

| state | meaning | source statuses |
|---|---|---|
| `validated` | Validate built and checked the case in DWSIM; **nothing was solved** | `validated` |
| `converged` | Run solved; all solved objects calculated; balances/verification passed | `completed` |
| `non_converged` | Solver ran but did not reach a converged, fully calculated flowsheet | mixed `unconverged`; non-mixed `failed` with a `solve` record whose `ok` is false or `failed_objects` is non-empty |
| `failed` | The run could not produce a solve (build, check, segment, verification, timeout, runtime) | `check_failed`, `materialization_mismatch`, `materialization_failed`, `segment_failed`, `JARVIS_SOLVE_TIMEOUT`, `native_reload_failed`, `runtime_failed`, kinetics verification failure, any other status |
| `cancelled` | Reserved; synchronous draft runs cannot be cancelled today | (dynamic 172 jobs only) |

`ready` (no blocking findings) and `running` (request in flight) are editor states, not run outcomes. The UI shows them distinctly and never in success colours.

`outcome` also carries:
- `label`;
- `reason` (typed code: mixed `reason`, `JARVIS_SOLVE_TIMEOUT`, `materialization_mismatch`, …);
- `message`;
- `failing` (`[{tag, stage, error}]` from `failed_objects`, `failed_units` / `failed_segment` or `error_detail.step`);
- `residual` (last `max_normalized_residual`, or null);
- `iterations` (`len(history)`, or null);
- `worst_tear`;
- `results_available` (`none` | `converged` | `last_iterate`);
- `artifact` (relative path of the persisted solved case, or null).

Each field is null when unknown. Nothing is invented.

### 2. Results state

`results_state` keeps its contract and adds `outcome` for the latest attempt. These rules change:
- a latest Run whose outcome is `non_converged` or `failed` on the same process fingerprint demotes an older converged run to `stale`, whatever the engine (fixes fact 3);
- `last_attempt` gains its `outcome`.

### 3. Results view

`GET /workspaces/{ws}/process/drafts/{draft_id}/runs/{run_id}/results` returns `process_stack.results_view.build(run, document_at_run_revision)`. This is a deterministic projection of the persisted run. It adds no new physics.

```
{run_id, draft_revision, outcome, label: "current"|"last_iterate"|"not_solved",
 streams: {tag: {role: "feed"|"product"|"internal", from, to,
                 temperature, pressure, mass_flow, molar_flow, volumetric_flow, vapor_fraction,
                 mass_fractions: {compound: q}, culture: {biomass, nitrogen, oxygen, ...},
                 owner, state_source}},
 units: {tag: {type, calculated, error, quantities: {key: q}, inlets: [tag], outlets: [tag]}},
 boundary: {inputs: [stream tags], outputs: [stream tags],
            totals: {mass_flow_in, mass_flow_out, by_compound_in, by_compound_out}},
 balances: {mass: {...}, culture: {...} | null, unit_balances: {...} | null},
 findings: [...], kpis: [kpi]}
```

Every quantity `q` has one of two forms:
- `{value, unit, label?}`, where a real zero stays the number 0;
- `{value: null, status: "unavailable" | "not_computed" | "failed", reason}`.

The UI renders the three null kinds differently from each other and from zero. A `last_iterate` view is permitted only for `non_converged` outcomes, and every number in it carries the label "Not converged — last iterate". A `failed` outcome returns `label: "not_solved"` with empty streams and units, unless the persisted run holds them. Any such values carry the same last-iterate label.

### 4. KPI summary (deterministic, model-independent schema)

`kpi = {id, label, value|null, unit, status: available|unavailable|not_applicable, reason, definition, sources: [json-pointer into run]}`.

KPIs are computed only for `converged` outcomes. Otherwise every KPI is `unavailable` with reason `run not converged`.

| id | definition | status rule |
|---|---|---|
| `biomass_product_rate` | Σ over product boundary streams of culture biomass (kg/m³) × volumetric flow (m³/d), kg/d, on the 167 culture biomass basis | unavailable if no product carries culture values |
| `pbr_volumetric_productivity` | per PBR, `reported.volumetric_productivity` | as reported |
| `pbr_net_biomass_production` | per PBR, `reported.net_biomass_production` | as reported |
| `pbr_projected_area_productivity` | per PBR, `net_biomass_production / A_proj`, where A_proj = n_tubes · D_inner · L, kg/(m²·d). This is the projected tube area normal to a beam perpendicular to the tube axis. It is **not** ground footprint, and the label says so | unavailable if a geometry parameter is missing |
| `culture_throughput` | per PBR, `reported.volumetric_flow_m3_h` | as reported |
| `outlet_biomass_concentration` | per product stream, culture biomass (kg/m³) | unavailable without culture values |
| `separator_biomass_recovery` | per SpecifiedSeparator: biomass mass rate in the concentrate outlet ÷ biomass mass rate at the inlet, from solved stream culture values | unavailable without culture values on both |
| `water_input` | Σ over feed streams of mass_flow × Water mass fraction, kg/h | unavailable if Water is not a compound |
| `nitrogen_input` | Σ over feed streams of culture nitrogen × volumetric flow, kg/d | unavailable without culture N |
| `mass_balance_closure` | \|residual\| / boundary mass flow, from `mass_balance` or mixed `balances.carrier_mass` | unavailable if not calculated |
| `co2_feed`, `co2_uptake`, `co2_per_biomass` | always `unavailable`, reason "T1 does not model carbon (spec 170): carbon is assumed externally supplied and non-limiting" | — |

Adding a KPI later requires an authoritative source quantity. A dashboard slot alone is not a reason.

### 5. Operator surface

- **Run state.** One toolbar run-state indicator shows `ready` / `running` / `validated (not solved)` / `converged` / `non-converged` / `failed` with distinct styling. Only `converged` is a success colour. The last-attempt panel shows every `outcome` diagnostic field that is present.
- **Results navigator.** After a run, clicking a stream or unit on the canvas opens its result panel in the inspector, with values from the results view:
  - stream: T, P, flows, composition, culture, owner;
  - PBR: reported quantities;
  - separator and other units: inlet/outlet stream links plus quantities.

  A Results tab shows the KPI summary, a boundary inputs/outputs table, a full stream table with composition, and balances and findings. Stale results and last-iterate results keep their labels.
- **Workspace.** The flowsheet canvas is the dominant central area. Species and thermodynamics move into a "Setup" drawer that can be opened and closed, and opens by default only while the draft has no compounds. The canvas fills the available height.
- **Viewport.** The flowsheet canvas has its own zoom and pan, implemented by transforming the SVG `viewBox` only:
  - wheel and pinch zoom at the cursor;
  - drag on the empty background to pan;
  - +/−, "Fit all" and "Reset" buttons;
  - a zoom range of 0.25×–4×.

  Object dragging keeps working at any zoom. Page zoom and the Sidecar are never affected.

### Non-goals

- `.jvsim` files, Save As, Open Simulation and filesystem project persistence are deferred until runs are trustworthy, by maintainer directive.
- No new solver behaviour, no async/cancellable steady-state runs, and no 172 dynamic studio (173).
- No frontend arithmetic on authoritative quantities beyond unit formatting.

## Acceptance

1. Unit tests map every known run status, including legacy runs without `outcome`, to exactly one outcome state with the diagnostics present.
2. `results_state` demotes an older converged run after a later non-mixed `failed` attempt.
3. The results view and KPI tests cover:
   - available, unavailable, zero and not-computed values;
   - the CO₂ KPIs as unavailable with their reason;
   - A_proj from the draft geometry;
   - separator recovery from stream culture;
   - a `non_converged` view labelled last-iterate.
4. Real DWSIM 10.2.9:
   - one converged non-mixed run with a feed, a Heater and a product;
   - one non-converged or failed run;
   - one converged PBR/separator mixed run.

   The results view and KPIs must be recorded for each.
5. Chromium acceptance:
   - toolbar states for ready, running, converged and a failed or non-converged run;
   - click a stream and the PBR to see their result panels;
   - the KPI and boundary tables;
   - Setup drawer open/close;
   - canvas zoom, pan and fit, with page scale unchanged and object drag still correct after zoom;
   - no page errors.
6. Full backend suite, ruff, the typecheck ratchet, the architecture gate and the frontend build all pass.
