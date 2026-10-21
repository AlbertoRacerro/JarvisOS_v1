# 173 — Process Dynamic Studio: implementation evidence

Spec: [173](../specs/173-process-dynamic-studio.md). Implementation lane `k173`
(2026-10-15), recovered and rebased onto master `a5a7f9bd` on 2026-10-21 in
roadmap continuation cycle 3. Product head of this evidence:
`842fce7923296dd9d829e40bc41e89ebea87b406` (later commits on the PR are
documentation and registry only).

## Defects found by the browser proof and fixed

The real-Chromium golden workflow found five defects that the unit tests did
not catch. All are fixed on this branch, each with a frontend test:

1. **Process page crash.** Stored dynamic content omits fields left at their
   172 model default. A draft whose scenario had no `controllers` key crashed
   the whole Process stage (`Cannot read properties of undefined`).
   `contentOf` now restores the `dynamic_models` defaults and never changes a
   stored value.
2. **Refusal codes lost.** `failureText` read only `StudioApiError`, so draft
   patch refusals (`DraftApiError`) showed no backend code, contrary to
   decision 3. Both are read now; the proof shows
   `dynamic_content_invalid: Invalid controller content`.
3. **Initial state missing.** A new scenario preselected its first unit
   without a starting state, so Start was refused with
   `INITIAL_STATE_REQUIRED`. The preselected unit now gets the same editable
   starting state as a unit chosen later.
4. **Unstyled charts.** The uPlot stylesheet was imported only by the lazy
   Environment panel, so Process charts drew legends over their axes.
5. **KPI cards.** Labels and values ran together in an unstyled list.

## Real-Chromium golden workflow (acceptance 1)

Playwright 1.55.0 with cached Chromium 1187. The candidate backend served the
built `frontend/dist` same-origin (`VITE_API_BASE_URL=`) on a fresh
`JARVISOS_DATA_ROOT` bootstrapped with `app.core.bootstrap`. Its own origin
was in `JARVISOS_CORS_ORIGINS`, as the launcher sets it; without that, Studio
Apply is refused with `runner_origin_forbidden`.

Precondition fixture (seed script, not part of the operator journey): the
repository's spec 184 culture-loop fixture (Pump → PBR…PBR4 → TankA → TankB →
Split(harvest) → Mix(Feed) → Pump) with a pinned card and an environment
profile, plus one Studio procedure, "Daily draw" (draw/separate, refill),
created, tested and published through the public Studio routes. The operator
then used only the GUI:

| Step | Result |
| --- | --- |
| Schedule | Recurring draw: "Every 1 d from day 1, draw 10 % of the loop from tank TankA, 2 times." Conditioned dose: "When PBR.loop_N falls below 0.04 kg/m3 (0 hysteresis, 1 h cooldown), dose 0.001 kg N into TankA, at most 3 times, not before day 1." |
| Controller | Cadence 10 s refused with `dynamic_content_invalid`, then saved: "On/off keeps X of PBR above 0.5 kg/m3 by switching feed flow of Feed …, every 5 min, output 0 to 2e-7 m3/s (0.05 hysteresis)." |
| Scenario | `golden`, profile, 3 days, six culture units, circulation and feed flow, schedule and controller: draft revision 7. |
| Run | Succeeded. Chips: aggregate residual ~1e-13 relative against 1e-4, 2 of 2 action events closed, no downstream. KPIs per unit, cumulative harvest, 864 controller samples, productivities, 185 campaign figures. |
| Keyboard | Focused chart group: `+` and `→` changed the range end 3 → 2.625 d, `Escape` reset it. Three chart value tables. The schedule event was opened with `Enter`; comparison runs were selected with `Space`. |
| Edit and staleness | Draw raised to 20 %: draft revision 8, the run turned **Stale**. Re-run was refused with `EVENT_VOLUME_INVALID` (a second draw would empty TankA) and no run was created (acceptance 8). Set to 12 %: revision 9, re-run succeeded and reads Current. |
| Compare | Both runs, matching units overlaid, KPI difference table against the chosen baseline. |
| CSV | `dynamic-golden-<job>.csv`: job id, snapshot digest, fidelity, scenario, rows=75, the Unqualified notice, unit-bearing headers; 75 rows = 73 hourly outputs + 2 event-phase rows, equal to `total_points`. |
| 191 link | Studio bench Apply of "Daily draw v1" as schedule `procedure`: badge "applied, unmodified". A hand edit in the Dynamic Studio asked for confirmation naming the consequence, then the badge read "modified, no longer the pinned procedure". |

No page errors. Screenshots: [schedule](evidence-173/01-schedule.png),
[controller](evidence-173/02-controller.png),
[results](evidence-173/05-results-panel.png), [stale](evidence-173/06-stale.png),
[refused re-run](evidence-173/07-refused-overdraw.png),
[comparison](evidence-173/09-compare-panel.png),
[procedure modified](evidence-173/11-procedure-modified.png),
[390 px](evidence-173/12-narrow-390.png). The proof script, seed, log and
full capture set are kept on the qualification host in
`jarvis-control/work/evidence/173-gui/`.

## Deterministic verification

- `frontend/tests/173-process-dynamic.mjs` (descriptions, recurrence,
  conditions, staleness, series paging and CSV, comparison, defaults, wiring)
  gates `npm run build`. The full build, including every frontend suite and
  `tsc`, passes.
- `backend/tests/test_process_dynamic_studio_173.py` plus the 172, 185, 186,
  188 and 191 suites: 132 passed, 3 skipped. No existing dynamic or Studio backend test was
  edited. The frontend 191 source test changed only for the shared results
  view (decision 15). Full backend suite: 4435 passed,
  43 skipped.
- ruff, `check_spec_status.py`.
- `scripts/devctx.py` decodes git output as UTF-8, and its test fixtures are
  written as UTF-8. Without that, a CI shard whose earlier tests leave an ASCII
  locale fails (verified with `LC_ALL=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0`).

## Review

Coordinator exact-head review of the projection read, staleness, series paging
and CSV, comparison and link handling found no blocking defect. CSV export
fails closed on striding or truncation. Duplicate event-phase timestamps at
window boundaries are de-duplicated against the previous window. Comparison is
limited to one draft and at most four runs, with exact-time alignment and no
interpolation. Non-blocking: the CSV object URL is revoked right after
`click()`, which works in Chromium.
