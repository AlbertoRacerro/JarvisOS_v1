# Spec 210 — Process solver console evidence

The implementation is PR #893 (`impl/210-solver-console`). A background Process run uses the existing tear controller and writes each completed iteration to `events.jsonl` during the solve. The Process editor polls that log by cursor, shows the normalized residual on a logarithmic chart, and exposes cooperative Stop, revision-bound Retry, and server-side run comparison. Pure DWSIM solves state that internal iterations are not observable.

## Deterministic checks

- Focused backend suites `test_process_solver_console_210.py`, `test_process_mixed_168.py`, `test_tear_solver_183.py`: 96 passed, 2 skipped. The controlled evaluation test reads iterations 1 and 2 while iteration 3 is blocked; the operator-stop test checks the last iterate and `operator_stop`; another test checks that a method event is in the observed row before the next evaluation.
- `python -m ruff check app tests`: pass.
- Frontend `npm run build`: pass, including frontend tests, TypeScript, and Vite.
- The broad backend suite was stopped after 194 passed and 17 skipped because it had not reached most tests after 154 seconds; this is not a full-suite pass. Exact PR-head CI is the broad gate.

## Real-Chromium walk

Evidence: `/home/thera/jarvis-control/work/evidence/210-browser/r2/` (screenshots and `walk-report.json`, `final-report.json`, `a11y.json`, `focus.json`). Chromium used the actual Process editor and local FastAPI routes with isolated `/tmp/jarvis-210-browser-data`. Only the DWSIM evaluation was replaced by a controlled 0.18-second contraction; the real draft revisions, mixed runtime, tear controller, job and event-log code ran. The browser draft was a valid, connected recycle flowsheet with a Jarvis `Recycle` tear; the replacement did not invent iteration rows.

- Run `4acdaa30…` on revision `6:2179e0d96b2cd88c`: iterations appeared while the solve was running (captured at iteration 2, with chart and diagnostics). Stop requested during the run ended with `unconverged`, `operator_stop`, and "Not converged — last iterate". The five event emission times were monotonic and preceded `finished_at`. Browser console and page errors: 0.
- The operator changed settings through Setup to Wegstein and 100 maximum iterations. Retry `6bd4d18f…` on revision `7:65095a9014dc71bd` converged in 7 iterations and recorded `retry_of=4acdaa30…` plus settings differences. Its recorded history and run record reappeared after page reload.
- The comparison selected the stopped run and its retry: same process-content digest, distinct document digests, method and iteration differences, both residual series, and stream deltas in operator units. Browser console and page errors: 0.
- Dark and Light captures show the new controls. Measured text contrast ratios for summary/select/retry were at least 9.15:1 in both themes. Keyboard Tab put a visible 2px accent outline on the comparison summary and select in both themes. No focus failure was observed.

The real DWSIM host was not part of this browser walk; the spec's browser-observable live-iteration criterion was exercised with a controlled DWSIM evaluation, and deterministic backend tests cover the runtime handoff.
