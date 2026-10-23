# PROCESS-SOLVER-CONSOLE-1 — live recycle solver console

Accepted outcome and readiness: binding roadmap directive
`L20261022122708-233d` (P1 "Scientific solver console. Real numerical
iteration observability: residuals, convergence diagnostics, safe stop,
versioned retry and run comparison. Never present buffered final diagnostics
as live streaming."). It builds on the merged Process draft run record
(spec 155/181), the Jarvis-owned recycle/tear controller and its solver
settings (spec 183) and the mixed DWSIM/Jarvis solve (spec 168). Live state is
recorded only in STATUS.md.

## Why this solver

The Process recycle (tear) solve is the numerical iteration JarvisOS itself
owns: `tear_solver.solve` computes per-iteration normalized and physical
residuals, the contraction estimate, the worst tear and method events, and it
already exposes `before_iteration`/`on_history` hooks. Today the run is one
synchronous request: the operator sees nothing until the solve ends and then
reads the history table after the fact. DWSIM's internal flowsheet solve and
the Studio sandbox evaluations expose no iteration data, so they stay outside
this console and the console says so instead of inventing progress. Dynamic
runs (spec 172) are already background jobs with progress and cancel and are
not changed.

## Outcome

1. **Background solve with a live iteration log.** A Process draft `run`
   that needs the mixed/tear solve can be started as a background solve on an
   exact draft revision. Each controller history row is appended to a durable
   per-run event log at the moment the controller produces it, stamped with
   its wall-clock emission time and iteration index. The operator reads the
   log incrementally (cursor-based) while the solve runs. The final run record
   is the same `run.json` the existing run list and results view read; the
   synchronous action keeps working unchanged.
2. **Convergence diagnostics in the console.** Per iteration: maximum
   normalized residual (against tolerance 1), worst tear, contraction estimate
   and its validity, method step events, elapsed time; at the end: status,
   stop reason, the existing diagnostics and recommendation. A chart shows the
   normalized residual per iteration on a logarithmic axis with the tolerance
   line.
3. **Truthful liveness.** The console labels data as live only while the
   solve is running and events arrive with emission times during the run. A
   finished or recovered run is shown as a recorded history. A run without
   Jarvis-observed iterations (pure DWSIM or culture-only) states that its
   internal convergence is not observable. No final history is replayed as an
   animation or presented as streaming.
4. **Safe stop.** An operator stop is cooperative: it takes effect at the
   next iteration boundary, never interrupts a DWSIM build or a Studio sandbox
   evaluation, and ends the solve as `unconverged` with stop reason
   `operator_stop`. The last iterate is labelled "Not converged — last
   iterate" exactly like the other non-converged reasons. A stop request on a
   finished run is a typed no-op; a backend restart marks a running solve
   `interrupted` without inventing a result.
5. **Versioned retry.** A retry starts a new background solve linked to its
   parent run (`retry_of`). Changing solver settings for the retry goes
   through the existing `set_solver` draft patch, so every retry is bound to an
   exact, immutable draft revision; the retry record states the parent run and
   the solver-settings difference from it.
6. **Run comparison.** Two runs of the same draft can be compared: draft
   revision and content digest (and whether the process content differs or
   only solver settings), solver-settings difference, status and stop reason,
   iterations, final maximum normalized residual, residual-per-iteration
   series for both, and stream result differences (temperature, pressure,
   mass flow) for streams present in both, in operator units with the same
   "last iterate" qualification as the run views.

## Scope

- Backend owner for background Process solves: start, status with the event
  cursor, stop, retry, and recovery at startup; bounded concurrency (one
  active solve per draft, a small global cap) with typed refusals; the event
  log lives inside the existing run directory and is size-bounded.
- Comparison projection computed server-side (no frontend physics or unit
  math).
- Process draft editor: a compact solver console (state, iteration, live
  residual chart, current diagnostics, Stop), Retry from a run, and a two-run
  comparison view, in the Lumen design system.

## Non-goals and boundaries

- No change to the tear numerical methods, tolerances, convergence rule or
  the meaning of existing run records; no new solver, no DWSIM-internal
  instrumentation, no CFD/FEM residual streaming, no dynamic-engine change.
- No warm start of a retry from a previous iterate.
- No server push infrastructure is required: incremental polling of a durable
  log is sufficient as long as the liveness rules above hold.
- Persisted run records stay readable by the existing run list and results
  view; new fields are additive.

## Acceptance

- Backend tests on the exact head, with a controllable fake evaluation:
  events for iteration *k* are readable through the status cursor while the
  evaluation of iteration *k+1* is still blocked (proving they are not
  buffered to the end); emission times are monotonic and precede
  `finished_at`; an operator stop ends the solve at the next boundary with
  `operator_stop` and a recorded last iterate, without interrupting an
  evaluation; stop on a finished run is a no-op; the concurrency refusal; a
  recovered running record becomes `interrupted`; a retry records `retry_of`
  and the settings difference; the comparison reports settings and stream
  differences and flags differing process content; the final `run.json`
  remains readable by the existing run and results routes; the existing
  synchronous run path and the spec 183 tear-solver suites still pass.
- Frontend build, type check and test suite pass.
- Real-Chromium evidence, recorded in an implementation note: a recycle
  draft solve shows iterations arriving while running, the residual chart and
  diagnostics update, Stop ends the run as not converged with
  `operator_stop`, a retry with changed solver settings converges, and the
  comparison view shows both runs; no page or console errors and no contrast
  or focus failures on the new controls.
