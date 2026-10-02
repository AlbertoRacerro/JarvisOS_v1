# 168 — Process mixed-engine solve

State: **ready**. This spec combines definition, contract and readiness under the maintainer directive of 2026-10-02 (continue the planned PBR roadmap in dependency order). It builds on the merged [PBR engineering architecture record](../implementation/pbr-engineering-architecture-2026-10-02.md) §4.2/§5.1 and the ranked engineering inventory, which are joint authority.

- **Hard dependency:** 167 (culture streams, unit ownership in the registry).
- **167 coordination:** this spec supersedes 167's refusal of culture on recycles. See capability 2.
- **Place in the roadmap:** the second slice of the record's order of value (167 → 168 → 169 → 170).

It makes a Process flowsheet solvable when it contains a Jarvis-owned unit, including recycles that cross the DWSIM/Jarvis boundary. One Jarvis-native unit proves the boundary.

## Fresh evidence (master `a09ae8b9`, 167 in implementation)

Code survey: `out/wpbr/a168.report.md`. DWSIM probes: `evidence/pbr/p168/p168.report.md`, run on pinned DWSIM 10.2.9 through the compiler's own `plan()` and `_feed_calls()`. Contract review: `out/wpbr/r168.report.md`.

1. **One request, one DWSIM process.**
   - `draft.execute` opens one MCP client per Run.
   - `materialize` creates the flowsheet and replays `plan()`. It then saves, reads back, compares with `expected()`, solves, and reads every result.
   - The Run route is synchronous. Per-call timeouts are create 30 s, plan 60 s, and solve 120 s (150 s transport).
   - `results_state` accepts only a run with `status == "completed"` whose `process_fingerprint` matches the document.
2. **Re-solving the same handle after a feed update is wrong.** Probe 1 replayed `_feed_calls()` on an existing feed and solved the same handle. The result was `ok: true` 22 times.
   - Temperature, pressure and mass flow matched a fresh build.
   - Composition-dependent outputs did not: mass fraction was off by up to 0.152 absolute, enthalpy by 253 kJ/kg, and density by 37.8 kg/m³. The composition stayed stale.
   - Same-handle iteration is therefore not admitted.
3. **Measured cost.** Over 37 calls, flowsheet creation took 0.32–1.18 s (median 0.48 s). Plan, save, read-back, check and solve add about 0.1 s warm. The 162 completed small runs had a median `compile_seconds` of 1.64 s (maximum 2.70 s).
4. **Repeatability.** For this Water/Ethanol NRTL acyclic case, identical documents solved 10 times on one handle and in 10 fresh sessions gave bitwise-identical results (probe 2). Several fresh flowsheets built **within one session** were not compared with fresh-session builds.
5. **Zero and near-zero inlets.** A Mixer with a 0 or 1e-12 kg/s inlet solved cleanly (probe 3). No other unit type was probed.
6. **A native Recycle that cannot converge fails visibly.** It returned `ok: false` in 0.1 s with `NOT_CONVERGED` and its three error rows (probe 4). The surrounding streams still read as calculated. A converged native Recycle leaves residual errors larger than 0.01 K: the 158 case reported a temperature error of 0.0204.
7. **The current cycle check has a gap.** `validate_document` misses a Recycle-free loop when DFS has already visited a node through a Recycle path (probe 5: Splitter X → Recycle R → Mixer Y; X → Y; Y → X).

## Decision

**Jarvis masters a sequential-modular steady-state loop. DWSIM solves segments, Jarvis evaluates its own units, and loops through Jarvis units are converged by Jarvis as tears. DWSIM never sees Jarvis units or culture.**

### Partition

- **Tears are the operator's existing Recycle blocks.** A Recycle R is **consumed** if and only if both hold:
  - R lies on a directed cycle of the unit graph;
  - some Jarvis-owned unit J satisfies R ⤳ J and J ⤳ R (reachability).

  All consumed Recycles form one simultaneous tear vector. Every other Recycle is native: it is materialized inside its segment, and DWSIM converges it as today.
- **Cut and level.** Cut the consumed Recycles: the outlet stream becomes a tear and the inlet stream becomes a boundary product. What remains is acyclic, apart from native loops wholly inside DWSIM units. Then:
  - remove the Jarvis units;
  - give every DWSIM unit the level d(u), the maximum number of Jarvis units on any path that reaches u;
  - a **segment** is a weakly connected component of DWSIM units of equal level.
- **Boundary streams.** An edge between DWSIM units of different levels is cut. It becomes a boundary product of the lower segment and a boundary feed of the higher one.
- **How levels are computed.** Levels are computed on the graph after the consumed Recycles are cut, with each native cycle treated as one node.
- **Energy streams.** Units joined only by an energy stream stay in one segment. Jarvis units have no energy ports, so no energy stream crosses a segment boundary. If that merging would make the segment/Jarvis graph cyclic, the draft gets the blocker `ENERGY_STREAM_CROSSES_JARVIS_LEVEL`.
- **Evaluation order.** The segment/Jarvis graph is acyclic by construction and is evaluated in topological order. This handles the bypass case (Splitter → {U1 → separator, bypass} → Mixer) without a false loop.
- **Native Recycles on a Jarvis loop are excluded in 168.** A native Recycle must not sit inside a segment that contains a unit on a cycle through a consumed Recycle. Its residual noise is above the outer tolerances (fresh evidence 6), so the draft is refused with a finding.

### DWSIM calls

- **Fresh flowsheets every iteration.** Each segment is rebuilt as a new flowsheet on every outer iteration, then read back and verified. Handles are closed after use.
- **Sessions.** Builds run in one long-lived MCP session per Run, **if the session-equivalence probe passes** (Required evidence 1). In the one-session-per-build fallback, a build costs about 1.5–2.5 s, and the converging acceptance case may not fit in 90 s. If the gate selects the fallback, the implementer stops and reports to the coordinator, who amends the budget in this spec before building on it. In-place mutation is a later optimization: it must first prove equivalence to fresh builds on the probe 1 harness.

### Unchanged paths

- **Single-owner drafts.** A draft with no Jarvis unit keeps today's materialization, read-back, fingerprints and results byte-identical.
- **Culture-only loops.** A culture-carrying loop made only of DWSIM units keeps its native Recycle. Its culture is converged afterwards by a Jarvis-only fixed point on the converged DWSIM flows, which needs no DWSIM calls.

### Alternatives rejected

- **Same-handle feed updates:** proven wrong for composition.
- **A new tear op:** it duplicates the Recycle gesture that validation already requires.
- **An equation-oriented mixed solve (IDAES/Pyomo):** it duplicates DWSIM ownership (record §4.4).
- **Wegstein acceleration in 168:**
  - The acceptance loop converges by direct substitution in about 15 iterations.
  - Above a loop gain of about 0.63, direct substitution does not fit in 25 iterations. 177's medium recycle will need acceleration then.
  - The controller is engine-agnostic, so acceleration can be added without changing segments.
- **Consuming culture-carrying DWSIM loops:** this would cost two builds per iteration and fail above a gain of about 0.63.

## Accepted capability

### 1. Registry and the Jarvis-native specified separator

- **Owner values.** Owners are `dwsim` and `jarvis_bio` (record §5.1), with badges "DWSIM" and "Jarvis". `dwsim_type` and `native_types` are required only for `dwsim` units, and a registry self-test enforces this.
- **The new unit.** `SpecifiedSeparator` (label "Specified separator", owner `jarvis_bio`, `culture_rule: "separator"`):
  - one material inlet and two material outlets, `concentrate` and `clarified`;
  - no energy ports;
  - one mode, `specified`.
- **Parameters.**
  - `biomass_recovery`: `percent`, 0 < R ≤ 100. Formulas use the fraction R/100.
  - `concentration_factor`: `dimensionless`, 1 < f ≤ 1000.
- **Unit equations.** x is the mass-specific biomass (kg per kg of carrier stream, 167 basis). The DWSIM carrier flow m excludes biomass mass. With R as a fraction:
  - m_C = (R/f)·m_in;
  - m_K = m_in − m_C, which is > 0;
  - x_C = f·x_in;
  - x_K = (1 − R)·x_in·m_in / m_K.
- **Other outlet values.**
  - The carrier composition is identical in both outlets.
  - Temperature and pressure equal the inlet's: isothermal, isobaric, no duty.
  - Dissolved N, P, O₂, DIC and salinity follow the carrier: both outlets copy the inlet's mass-specific values.
  - pH is copied.
- **Zero inlet flow.** Both outlets have zero flow, and the mass-specific values copy the inlet's.
- **Unit result failures.**
  - The result fails if the inlet's solved vapor fraction is above 1e-6, under 167's liquid-only rule.
  - A Jarvis inlet with no DWSIM state fails the same way.
- **Unit results** carry:
  - the owner;
  - the evaluator id `jarvis.specified_separator`, version 1;
  - the fidelity label "screening — specified performance, not a mechanistic separator";
  - the caveats: dissolved species follow the carrier; no energy or pressure effect.

### 2. Validation (instant, `source: "jarvis"`)

- **Cycle check.** The check is that the unit graph is acyclic once every outgoing edge of every Recycle is removed. The graph includes material and energy streams, as today.
  - Each non-trivial strongly connected component of the reduced graph emits one `RECYCLE_REQUIRED` blocker.
  - The message is "Process loop [tags] requires a Recycle block.", with tags in sorted order. The object is the first tag.
  - For loops the DFS already reported, the finding is identical apart from tag order.
  - This is the only behavior change for single-owner drafts. Stored runs are not recomputed or invalidated.
- **New findings.**
  - `SEPARATOR_REQUIRES_CULTURE` (blocker): a SpecifiedSeparator whose inlet is not reached by culture.
  - `SEPARATOR_CONCENTRATE_IMPLAUSIBLE` (warning): f·x_in is above 0.25 kg/kg, a screening bound.
    - Before a run, x_in comes from the culture feed's volumetric value divided by 1000 kg/m³, ignoring dilution along the loop.
    - After a run, the converged inlet is used.
  - `NATIVE_RECYCLE_IN_JARVIS_LOOP` (blocker): a native Recycle inside a segment on a consumed tear's cycle.
  - `TEAR_CONSUMED` (info): names each Recycle that Jarvis will converge.
- **Supersession of 167.**
  - `Recycle.culture_rule` changes from `refuse` to `tear`.
  - 167's `CULTURE_RECYCLE_UNSUPPORTED` is retired in both code paths: the cycle scan and the `refuse` rule on a Recycle target.
  - 167's required "cycle" refusal case is replaced by 168's converged cases.
  - `Flash`, `DistillationColumn` and `PFR` keep `refuse`.
  - The 167 spec gets a one-line pointer to this supersession in the 168 implementation PR.

### 3. Outer loop (`jarvis_mixed_solve`, `MIXED_SOLVE_VERSION = 1`)

**Tear vector.** For each consumed Recycle outlet the tear vector holds:

- pressure, temperature and carrier mass flow;
- carrier mass fractions;
- the 167 culture fields: biomass, N, P, O₂ and salinity per kg, and DIC in mol/kg.

pH is carried, not converged.

**Initial guess.**

- Mass flow is 1e-6 × the sum of all feed mass flows. It is never exactly zero.
- Temperature, pressure, carrier composition and pH come from the first culture feed by tag, or the first feed if there is none.
- Culture values are zero.
- A culture field is `null` in the guess if and only if it is `null` on any culture feed.
- The tear is treated as a culture inlet, so `CULTURE_MIXED_WITH_UNSPECIFIED` does not fire for it.

**Residual and convergence.**

- At iteration k the segments and Jarvis units are evaluated with tear x_k and produce g(x_k).
- Field residual: r_i = g_i(x_k) − x_{k,i}. This is undamped.
- The tolerance tol_i is evaluated at x_{k,i}:
  - mass flow: 1e-5·max(|m|, 1e-6 kg/s);
  - temperature: 0.01 K;
  - pressure: 1e-6·max(|P|, 1 Pa);
  - each mass fraction: 1e-7;
  - each culture field: 1e-5·|value| + 1e-12 in its SI per-kg unit.
- Normalized residual: n_i = |r_i| / tol_i.
- A field that is null in both x_k and g(x_k) is converged. A null/value mismatch gives n_i = ∞.
- **Convergence** means max_i n_i ≤ 1. x_k is then the converged iterate, and every stored result comes from the solves at x_k.

**Update.**

- x_{k+1} = x_k + ω·(g(x_k) − x_k), with ω₁ = 1.
- Let R_k = max_i n_i. When R_k > 1.5·min_{j<k} R_j (growth, not noise), set ω ← max(ω/2, 0.125) and restart from the best iterate.
- A fourth growth event, which comes after ω has reached its 0.125 floor, ends the run `unconverged` with reason `damping_exhausted`.
- ω is never increased.
- Damping cannot stabilize a positive loop gain above 1, and the spec makes no such claim.

**Limits.**

- At most 25 iterations; at the cap the run ends `unconverged` with reason `max_iterations`.
- A 90 s wall budget covers the whole Run.
- Each DWSIM call's timeout is min(its unchanged timeout, remaining budget).
- **Reserve for the full path.** Before each iteration the controller requires: remaining budget ≥ (builds in this iteration) × t_build + reserve.
  - t_build is the slowest build seen so far, and 3 s before the first build.
  - reserve = (segments + final-sweep flashes) × 1.5 × t_build, floored at 3 s per build.
  - If the requirement fails, the run stops with reason `wall_budget`, and the full path runs on the stored iterate inside the reserve.
  - If the full path itself cannot finish, the run is `segment_failed` with reason `wall_budget`, and it records the iteration reached.
- These values are code constants under `MIXED_SOLVE_VERSION`, not document fields. Every run reports them.
- Longer runs wait for the 172 job path.

**Light and full solve paths.**

- **Intermediate iterations** use a light path: create, plan, save, read-back verify (required), check, solve. Results are read for **every material stream** of the segment, because `propagate_segment` needs every flow, vapor fraction and density. The light path skips only the scenario snapshot/compare, the compressed save, the mass balance and the per-unit result reads.
- **After the loop stops** (converged or not), every segment is rebuilt once at the stored iterate with the full `materialize()` path. This produces all results, `solved_case_sha256` and per-segment fingerprints.
- If the light and full paths give different tear values beyond tolerance, the run is `segment_failed`.

**Final sweep.** Every Jarvis outlet that has no DWSIM consumer is flashed through DWSIM as a one-feed segment. This covers terminal products and Jarvis → Jarvis streams. Its properties, vapor fraction and density then come from DWSIM, and it is marked `state_source: "jarvis_unit → dwsim_flash"`.

**Failure.**

- These end the run `segment_failed` at that iteration:
  - a segment `ok: false`, including a native Recycle `NOT_CONVERGED`;
  - a read-back mismatch;
  - a timeout or process death;
  - a Jarvis unit failure;
  - a 167 culture failure in any iteration.
- The DWSIM errors and the 167 finding code, stream and iteration are preserved.
- There is no retry on the same client after a timeout. Zeros or stale values are never accepted.
- On a failure message for a pressure residual whose sign stays constant for 3 iterations, the run reports "pressure falls by X Pa per pass around the loop; add a pump".

**Culture propagation.** `propagate_segment(segment, boundary_states, streams)` is a pure callable. It returns states, balances and findings, and is extracted from 167's per-unit rules: Mixer weighting, Splitter copy, pass-through, the pH rule and per-unit balances.

- It takes boundary culture as mass-specific values, with no density conversion.
- 167's single-owner `propagate` calls the same code, and 167 tests stay unchanged for culture without Jarvis units.
- Culture-only native loops are solved by repeated sweeps of this callable on the converged DWSIM flows.
  - The Recycle outlet starts from the first culture feed's mass-specific values.
  - The Recycle's DWSIM outlet flow is the weight.
  - The culture tolerance applies, with at most 10,000 sweeps.

**Engine-agnostic controller.** Segments and Jarvis units are callables. Unit tests use fake segments.

### 4. Run record, results and balances

**Run record.**

- `run.status` equals `mixed_solve.status`: `completed`, `unconverged` or `segment_failed`. `results_state` still accepts only `completed`.
- Non-completed runs store the last iterate's full-path results, labelled "Not converged — last iterate".
- Solved cases are kept as `runs/<id>/<segment>.dwxmz`.

**`mixed_solve` record** holds:

- status, reason, version and method;
- the tolerances and limits used;
- the history: per iteration, ω, the max normalized residual, the worst tear field, and per-tear per-field residuals;
- the partition: segments, units and levels, plus per-segment `materialization_fingerprint` and `solved_case_sha256` from the full path, for audit only;
- the failed segment, iteration and errors;
- `elapsed_s` per phase: build, solve and culture.

**Results by owner.**

- Stream and unit results carry their owner.
- A consumed Recycle shows Jarvis-synthesized rows in DWSIM's shape: mass flow error in kg/h, temperature error, pressure error. They are labelled "Converged by Jarvis (cross-engine tear)".

**Balances.** The carrier balance excludes biomass mass.

- **Per unit:** 167 culture residuals for every unit, including the separator, with 167's rule 1e-9·max + 1e-12. Every Recycle, consumed or native, is excluded: it is a tear, not a unit.
- **Whole graph:** carrier mass and each conserved culture field close to |Σin − Σout| ≤ Σ_tears tol_i + Σ_native |Mass Flow Error|·value + 1e-9·max + 1e-12.
  - The second term covers native Recycles: each one's reported mass-flow error (converted from kg/h to kg/s) times the mass-specific value.

A failing balance ends the run `unconverged` with reason `balance`.

### 5. Fingerprints, staleness and Validate

**Staleness fingerprint.** For a mixed draft, the run's `process_fingerprint` comes from the document's layout-free meaning:

- units, streams, parameters and culture;
- the partition and the consumed tear set;
- `MIXED_SOLVE_VERSION` and Jarvis evaluator ids and versions.

It is never computed from per-segment read-back, whose boundary feeds are loop outputs. Converged values are never fingerprinted. Layout edits do not stale results.

**Validate.** For a mixed draft, Validate builds and read-back-checks each segment once at the initial guess, with no solve.

**Determinism.** The real acceptance case and the injected non-convergence case are each run twice. The test compares:

- iteration counts;
- ω and residual histories;
- outputs, within 1e-9 relative.

Bitwise identity is reported when observed. For the injected case, the histories are compared over their common prefix. The reasons must be equal only when the reason is `max_iterations`.

### 6. Operator UI (Process editor)

**Adding and configuring the separator.**

- The palette shows the separator under a "Jarvis units" group.
- The registry `owner` drives the canvas and inspector badges. There is no hard-coded "DWSIM".
- The inspector edits R and f with units and inline validation, and shows the derived split R/f.

**Running and convergence.**

- During a Run the editor shows "Running mixed solve (DWSIM + Jarvis)…".
- The run summary shows one of:
  - "Converged in N iterations · max residual r";
  - "Not converged (reason) — last iterate";
  - "Segment failed: <unit>, <message>".
- A "Convergence" disclosure shows the iteration table: iteration, max normalized residual, ω, worst field. The table scrolls inside a bounded region.
- The disclosure also lists which units each owner solved, by segment.

**Results.**

- Results are grouped as `Results · DWSIM` and `Results · Jarvis`.
- The concentrate shows `Culture · Jarvis` with the separator's fidelity label.

**Layout.** The editor is readable at 1280 and 1440 CSS px, with no horizontal overflow and no raw JSON in the normal view.

### 7. Agent actions (166 vocabulary)

- **Building and editing.** `add_unit`, `insert_unit_after` and `connect` work for `SpecifiedSeparator` through the registry. `set_value` on R and f is confirm tier, with units validated.
- **Process surface brief.** It lists:
  - each unit's owner;
  - the separator's parameters and derived split;
  - the last run's status, reason, iteration count, worst field and residual (not the history);
  - the refusal rules.

  It stays within the 166 6000-character cap.
- **Non-convergence questions.** Asked why a run did not converge, the agent explains it from the brief and proposes no change.

## Boundaries / non-goals

- **Out of scope:**
  - biological reaction, growth, gas transfer or a PBR unit (170);
  - other Jarvis separators (177);
  - Wegstein or Newton acceleration;
  - async jobs, progress or cancel (172);
  - user-editable tolerances;
  - native Recycles inside a Jarvis loop.
- **Unchanged:**
  - single-owner DWSIM materialization;
  - the compound list;
  - property packages;
  - the frozen 145 contracts.
- **Never done:**
  - biology or culture inside DWSIM;
  - same-handle feed mutation.
- **Known limit:** loops with a gain above about 0.63 end `unconverged` until acceleration arrives.
- **FMU-neutral boundary** (record §4.4): segments and Jarvis units exchange typed, unit-bearing stream states.

## Required evidence

### 1. Implementation gate probes (real DWSIM 10.2.9, before the loop is built on them; recorded in evidence)

- **(a) Session equivalence.** In one session, build at least 10 fresh segment flowsheets with varying boundary feeds (composition, T, P, flow), closing each handle. Compare every result field bitwise with the same input built in a new session. Any difference selects the one-session-per-build fallback.
- **(b) Small and zero flows into other units.** Run 1e-6-scale and zero inlet flow into Pump, Heater, Valve, Splitter and HeatExchanger, and Splitter ratios 0 and 1. Record what solves. A unit type that fails at small flow raises `TEAR_CONSUMER_ZERO_FLOW` (info) when it is a tear's first consumer, and the initial guess then uses 1e-3·Σfeeds.

### 2. Focused backend tests

- **Partition:**
  - consumed vs native Recycles, including nested and side loops;
  - the bypass case;
  - the native-Recycle-in-Jarvis-loop refusal.
- **Cycle check:** a golden test replays all stored 155/158/162 acceptance documents plus the probe 5 graph, and compares findings before and after.
- **New findings:** every new finding.
- **Separator:**
  - its equations and balances, including R = 100 % and f near 1 (clarified flow near zero);
  - zero inlet flow;
  - vapor-inlet failure.
- **Controller, using fake segments:**
  - a loop of gain 0.455 converging in about 15 iterations;
  - one spurious increase not halving ω (1.5× rule);
  - true growth halving ω, then damping exhaustion;
  - the iteration cap and the wall budget;
  - segment failure, and culture failure ending `segment_failed`;
  - null-pattern rules;
  - light/full mismatch.
- **Tolerance and residual arithmetic:** per field, including floors and the undamped residual.
- **Culture:**
  - the culture-only native loop fixed point;
  - 167 tests unchanged for single-owner culture.
- **Fingerprints:**
  - what the result fingerprint includes and excludes;
  - single-owner drafts byte-identical, with a golden materialization fingerprint and outcome on a 158 case.
- **166:** actions on the separator, and the brief contents and cap.

### 3. Frontend checks

The frontend build passes. Node contract tests cover the palette group, separator inspector, convergence disclosure and per-owner result groups.

### 4. Exact-head real DWSIM 10.2.9

**Converging case.**

- Topology:
  - a culture feed and the recycle return enter Mixer → Pump → SpecifiedSeparator;
  - the concentrate goes to a product;
  - the clarified stream goes to Splitter → purge product + return;
  - the return goes through Heater → Recycle → back to the Mixer.
- Settings: R = 90 %, f = 10, 50 % purge, for a loop gain of 0.455.
- It converges within the limits with a reported history.
- Carrier and culture balances close.
- Running it twice is deterministic.

**Injected non-convergence.** The same graph with f = 100 and 0.5 % purge (gain about 0.986):

- ends `unconverged` with reason `max_iterations` or `wall_budget`, and records which;
- keeps its history;
- produces no current results;
- is deterministic when run twice.

**Segment failure.** The draft is mixed (it contains the separator), and it has a native Recycle forced to `NOT_CONVERGED` (probe 4 topology) off the consumed cycle, for example downstream of the concentrate. It ends `segment_failed` with the DWSIM message.

**Culture-only native loop.** A culture-carrying DWSIM-only loop (Mixer → Heater → Splitter → Recycle) converges its culture through the Jarvis fixed point.

### 5. Exact-head real Chromium at 1280 and 1440 CSS px

- Add the separator from the palette, connect it, and set R and f.
- Run. Read the convergence summary and table, then inspect the separator and concentrate results with owner badges and `Culture · Jarvis`.
- Set f = 100 and the purge to 0.5 %, and Run. The not-converged banner shows, with no current results.
- In the Sidecar with local Gemma:
  - "why did this run not converge?" gets an explanation that quotes the iteration count and worst field, with no Apply card;
  - "set the concentration factor of the separator to 20" yields an Apply card, and applying it creates the next revision.
- Inspect the screenshots. No raw JSON is visible.
