# 168 — Process mixed-engine solve

State: **ready**. This spec combines definition, contract and readiness under the maintainer directive of 2026-10-02 (continue the planned PBR roadmap in dependency order), with the merged [PBR engineering architecture record](../implementation/pbr-engineering-architecture-2026-10-02.md) §4.2/§5.1 and the ranked engineering inventory as joint authority. The only hard dependency is 167 (culture streams, unit ownership in the registry). It is the second slice of the record's order of value (167 → 168 → 169 → 170). It makes a Process flowsheet solvable when it contains a Jarvis-owned unit, including recycles that cross the DWSIM/Jarvis boundary, and proves the boundary with one Jarvis-native unit.

## Fresh evidence (master `a09ae8b9`, 167 in implementation)

Code survey: `out/wpbr/a168.report.md`. DWSIM probes: `evidence/pbr/p168/p168.report.md`, run on pinned DWSIM 10.2.9 through the compiler's own `plan()` and `_feed_calls()`.

1. **One request, one DWSIM process.** `draft.execute` opens one MCP client per Run. `materialize` creates the flowsheet, replays `plan()`, saves, reads back, compares with `expected()`, solves and reads every result. The Run route is synchronous, with per-call timeouts (solve 120 s). There is no job or progress path.
2. **Re-solving the same flowsheet handle after a feed update is wrong.** In probe 1, replaying `_feed_calls()` on an existing feed and re-solving the same handle returned `ok: true` 22 times. Temperature, pressure and mass flow matched a fresh build. Composition-dependent outputs did not: mass fraction was off by up to 0.152 absolute, enthalpy by up to 253 kJ/kg, and density by up to 37.8 kg/m³. The composition stayed stale. **Same-handle iteration is therefore not admitted.**
3. **Fresh flowsheets are cheap and repeatable.** Identical documents solved 10 times on one handle and in 10 fresh sessions were bitwise identical (probe 2). A small solve call took about 0.015 s, and a cold session with build took about 0.15–0.2 s plus materialization and read-back.
4. **Zero-flow inlets solve.** A Mixer with a 0 or 1e-12 kg/s inlet solved cleanly (probe 3).
5. **A native Recycle that cannot converge fails visibly.** It returned `ok: false` in 0.1 s with `NOT_CONVERGED` on the Recycle and its three error rows (probe 4). The surrounding streams still read as calculated.
6. **The current cycle check has a gap.** In the probe 5 graph, `validate_document` misses a Recycle-free loop when DFS has already visited a node through a Recycle path (Splitter X → Recycle R → Mixer Y; X → Y; Y → X). `RECYCLE_REQUIRED` does not fire.
7. **Registry.** 167 adds `owner` and `culture_rule` to `UnitSpec`. `plan()`, `expected()`, `read_back()` and the "Results · DWSIM" UI assume every unit is DWSIM-owned.

## Decision

**Jarvis masters a sequential-modular steady-state loop. DWSIM solves segments, Jarvis evaluates its own units, and cross-engine recycles are converged by Jarvis as tears. DWSIM never sees Jarvis units or culture.**

- **Partition.** Remove every Jarvis-owned unit from the graph. The remaining connected DWSIM subgraphs are the **segments**. A stream that crosses an owner boundary becomes a boundary feed or product of its segment.
- **Tears are the operator's existing Recycle blocks.** A Recycle is **consumed by Jarvis** when its cycle contains a Jarvis unit or carries culture. Otherwise it stays a native DWSIM Recycle inside its segment, exactly as today.
  - A consumed Recycle is not materialized. Its outlet stream becomes the tear: a boundary feed of the downstream segment, iterated by Jarvis. Its inlet stream is a boundary product upstream.
  - After the cut, the graph of segments and Jarvis units must be acyclic. It is then evaluated in topological order.
- **Every iteration rebuilds each segment as a new flowsheet** inside **one long-lived MCP session per Run**: materialize, read back, verify, solve. The probe shows feed mutation on an existing handle is unsafe. Fresh builds are bitwise repeatable and cheap at this flowsheet size. A verified in-place mutation path is a later optimization. It must first prove equivalence to fresh builds on the probe 1 harness.
- **Single-owner drafts are unchanged.** A draft with no Jarvis unit and no consumed Recycle takes today's path. Its DWSIM materialization, read-back, fingerprints and results stay byte-identical.

Alternatives rejected:

- **Same-handle feed updates:** proven wrong for composition (fresh evidence 2).
- **A new tear op or tear field in the document:** it duplicates the Recycle gesture that validation already requires.
- **An equation-oriented mixed solve (IDAES/Pyomo):** this duplicates DWSIM ownership (record §4.4).
- **Wegstein acceleration in 168:** the acceptance loop converges by direct substitution. Wegstein arrives with the first loop that needs it (177 medium recycle). The loop controller is engine-agnostic, so it can be added without changing segments.

## Accepted capability

1. **Registry and the Jarvis-native specified separator.**
   - Owner values are `dwsim` and `jarvis_bio` (record §5.1). The UI badge reads "DWSIM" or "Jarvis".
   - `dwsim_type` and `native_types` are required only for `dwsim` units, and a registry self-test enforces this.
   - The new unit `SpecifiedSeparator` (label "Specified separator", owner `jarvis_bio`, `culture_rule: "separator"`):
     - one material inlet and two material outlets, `concentrate` and `clarified`; no energy ports;
     - one mode, `specified`;
     - `biomass_recovery` (`percent`, 0 < R ≤ 100);
     - `concentration_factor` (`dimensionless`, f > 1).
   - Unit equations, with x the mass-specific biomass (kg per kg of total stream, 167 basis) and m the DWSIM mass flow:
     - m_C = (R/f)·m_in, and m_K = m_in − m_C, which is > 0 because R ≤ 1 < f;
     - x_C = f·x_in, and x_K = (1 − R)·x_in·m_in / m_K.
   - The carrier composition (DWSIM mass fractions) is identical in both outlets. Temperature and pressure equal the inlet's: isothermal, isobaric, no duty.
   - Dissolved N, P, O₂, DIC and salinity follow the carrier: both outlets copy the inlet's mass-specific values. pH is copied.
   - An inlet whose solved vapor fraction is above 1e-6 fails the unit result, as in 167's liquid-only rule.
   - Results carry the owner, evaluator id `jarvis.specified_separator` version 1, fidelity "screening — specified performance, not a mechanistic separator", and caveats: dissolved species follow the carrier; no energy or pressure effect.
2. **Validation (instant, `source: "jarvis"`).**
   - Cycle detection is replaced by strongly connected components on the graph with every Recycle outlet edge removed. Any remaining cycle raises the existing `RECYCLE_REQUIRED`.
     - This fixes the probe 5 gap for all drafts. A draft already missing a Recycle now gets the blocker it should have had, and this is the only behavior change for single-owner drafts.
     - The probe 5 graph is a regression test.
   - `SEPARATOR_REQUIRES_CULTURE` (blocker): a SpecifiedSeparator whose inlet carries no culture. Biomass recovery has no meaning without biomass.
   - `JARVIS_CYCLE_TEAR_MISSING` (blocker): after the partition, the segment/Jarvis-unit graph is still cyclic. Its message tells the operator to place a Recycle on the loop.
   - `TEAR_CONSUMED` (info, not a warning): it names each Recycle that Jarvis will converge, with the reason (crosses a Jarvis unit / carries culture).
   - 167's `CULTURE_RECYCLE_UNSUPPORTED` is retired. A culture-carrying Recycle is consumed instead. `Flash`, `DistillationColumn` and `PFR` keep `refuse`.
3. **Outer loop (`jarvis_mixed_solve`, `MIXED_SOLVE_VERSION = 1`).**
   - **Tear vector, per consumed Recycle outlet:** pressure, temperature, mass flow, carrier mass fractions, and the 167 culture fields with values (biomass, N, P, O₂ and salinity per kg; DIC mol/kg). pH is carried and not converged.
   - **Initial guess:** zero mass flow, with the temperature, pressure and carrier composition of the first culture feed, or else the first feed, by tag. Culture fields are zero, and unknown (`null`) fields stay `null`.
   - **Update:** damped direct substitution, x ← x + ω·(g(x) − x).
     - ω starts at 1.
     - ω halves when the maximum normalized residual increases from one iteration to the next. After three halvings without decrease, the run ends `unconverged`.
     - ω never exceeds 1.
   - **Convergence** requires every field of every tear to pass in the same iteration:
     - mass flow: |Δ| ≤ 1e-5·max(|m|, 1e-6 kg/s);
     - temperature: |Δ| ≤ 0.01 K;
     - pressure: |Δ| ≤ 1e-6·max(|P|, 1 Pa);
     - each mass fraction: |Δ| ≤ 1e-7;
     - each culture field: |Δ| ≤ 1e-5·|value| + 1e-12 in its SI per-kg unit.
     - The normalized residual of a field is |Δ| divided by its tolerance. "Max normalized residual ≤ 1" is convergence.
     - These are starting contract values, not a measured noise floor for every package. Probe 2 measured zero repeat noise for the acyclic case.
   - **Limits:** at most 25 iterations; the whole Run, including the final sweep, has a 90 s wall-clock budget; per-call DWSIM timeouts are unchanged.
     - Tolerances, limits and damping are code constants under `MIXED_SOLVE_VERSION`, not document fields. Each run reports them.
     - Runs longer than the budget wait for the 172 job path.
   - **Failure:**
     - A segment whose solve returns `ok: false` (including a native Recycle `NOT_CONVERGED`) ends the run as `segment_failed` at that iteration. So does a read-back mismatch, a timeout or process death. The DWSIM errors are preserved. There is no retry on the same client after a timeout, and zeros or stale values are never accepted.
     - Max iterations, the budget or damping exhaustion end the run as `unconverged`.
     - Neither status can become current results: `results_state` keeps requiring `completed`. The last iterate is stored and shown labelled "Not converged — last iterate".
   - **Final sweep:** after convergence, a Jarvis outlet that feeds no segment (a terminal Jarvis product) is flashed through DWSIM as a one-feed segment in the same session. Its properties and density (needed by 167 culture display) then come from DWSIM. Its result is marked `state_source: "jarvis_unit → dwsim_flash"`.
   - **Engine-agnostic controller:** segments and Jarvis units are callables. Unit tests drive the controller with fake segments at zero DWSIM cost.
4. **Results and balances.** The run outcome gains `mixed_solve`:
   - status (`completed` / `unconverged` / `segment_failed`), version, method, ω history;
   - iterations, the tolerances and limits used;
   - history: per iteration, per tear, per field residual, plus the max normalized residual;
   - partition: segments with their units and per-segment `materialization_fingerprint` and `solved_case_sha256` of the final iteration;
   - the failed segment and iteration with DWSIM errors, and `elapsed_s`.

   Stream and unit results carry their owner. A consumed Recycle shows Jarvis-synthesized rows in the same shape as DWSIM's (mass flow error kg/h, temperature error, pressure error), labelled "Converged by Jarvis (cross-engine tear)".

   **Balances:**
   - carrier mass closure over the whole graph (feeds in vs products out), with the loop mass-flow tolerance;
   - 167 per-unit culture residuals for every unit, including the separator, with 167's 1e-9·max + 1e-12 rule on the converged iterate;
   - whole-graph culture closure per conserved field, with the loop culture tolerance.

   A failing balance marks the run `unconverged`, not `completed`.
5. **Fingerprints and staleness.**
   - The result fingerprint of a mixed draft extends 167's culture-inclusive fingerprint with:
     - the partition digest;
     - Jarvis unit parameters;
     - the consumed tear set;
     - `MIXED_SOLVE_VERSION`;
     - Jarvis evaluator ids and versions.
   - Converged values are outputs and are never fingerprinted.
   - Layout edits still do not stale results. Any parameter, topology or culture edit does.
   - Determinism is tested: the real acceptance case run twice gives identical iteration counts and outputs within 1e-9 relative. Bitwise identity is reported when observed.
6. **Operator UI (Process editor).**
   - The palette shows the separator under a "Jarvis units" group with its owner badge. The registry `owner` drives the canvas and inspector badges (no hard-coded "DWSIM").
   - The inspector edits R and f with units and inline validation, and shows the derived split R/f.
   - Run shows "Running mixed solve (DWSIM + Jarvis)…". When it finishes, the run summary shows "Converged in N iterations · max residual r" or a clear "Not converged" or "Segment failed: <unit>, <DWSIM message>" banner.
   - A "Convergence" disclosure shows the per-iteration table: iteration, max normalized residual, ω, and the worst tear field. It also names the segments and which units each owner solved.
   - Results are grouped as `Results · DWSIM` and `Results · Jarvis`. The concentrate shows `Culture · Jarvis` with the separator's fidelity label.
   - Readable at 1280 and 1440 CSS px with no horizontal overflow. No raw JSON in the normal view.
7. **Agent actions (166 vocabulary).**
   - `add_unit` / `insert_unit_after` / `connect` work for `SpecifiedSeparator` through the registry.
   - `set_value` on R and f is confirm tier, with units validated.
   - The Process surface brief lists each unit's owner, the separator's parameters and derived split, the last run's solve status, iterations and worst residual, and the refusal rules.
   - Asked why a run did not converge, the agent explains it from the brief and proposes no hidden change.
   - The brief stays within the 166 6000-character cap.

## Boundaries / non-goals

- No biological reaction, growth, gas transfer or PBR unit (170). No other Jarvis-native separators: harvest methods arrive with 177.
- No Wegstein or Newton acceleration. No async job, progress stream or cancel (172). No user-editable tolerances.
- No change to the DWSIM materialization of single-owner drafts, the closed compound list, property packages or the frozen 145 contracts. No biology or culture inside DWSIM.
- No same-handle feed mutation in the solve path.
- FMU-neutral boundary (record §4.4): segments and Jarvis units exchange typed, unit-bearing stream states that a later adapter can export.

## Required evidence

- **Focused backend tests:**
  - partition and consumed-Recycle selection, including pure-DWSIM loops staying native;
  - the SCC cycle check with the probe 5 regression;
  - every new finding;
  - separator equations and balances, including R = 100 %, f near 1, and vapor-inlet failure;
  - the controller with fake segments: a linear loop of gain 0.2 converging in the expected number of iterations; ω halving and exhaustion; the iteration cap; the wall budget; segment failure stopping the run; determinism;
  - tolerance arithmetic per field, including the floors;
  - result fingerprint inclusion and exclusion;
  - single-owner drafts byte-identical: golden materialization fingerprint and outcome on a 158 case;
  - 166 actions on the separator and the brief contents.
- **Frontend build and node contract tests** for the palette group, separator inspector, convergence disclosure and per-owner result groups.
- **Exact-head real DWSIM 10.2.9:**
  - culture feed + recycle return → Mixer → Pump → SpecifiedSeparator;
  - concentrate → product;
  - clarified → Splitter → purge product + return → Heater → Recycle → Mixer.
  - With R = 90 %, f = 10 and a 50 % purge, the loop gain is (1 − purge)·(1 − R/f) ≈ 0.455. This case converges within the limits with a reported residual history. Carrier and culture balances close. Running it twice is deterministic.
  - **Injected non-convergence:** the same graph with f = 100 and 0 % purge (loop gain 0.991) ends `unconverged` at 25 iterations, with its history, and with no current results.
  - **Segment failure:** a segment containing a native Recycle forced to `NOT_CONVERGED` (probe 4 topology) ends `segment_failed`, with the DWSIM message shown.
- **Exact-head real Chromium at 1280 and 1440 CSS px:**
  - add the separator from the palette, connect it and set R and f;
  - Run, read the convergence summary and table, and inspect the separator and concentrate results with owner badges and `Culture · Jarvis`;
  - set f = 100 and the purge to 0 % and Run, which shows the not-converged banner and no current results;
  - in the Sidecar (local Gemma), "set the concentration factor of the separator to 20" yields an Apply card, and applying it creates the next revision.
- Screenshots inspected; no raw JSON visible.
