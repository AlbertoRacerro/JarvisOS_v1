# 191 — Engineering Studio procedure authoring: declarative temporal procedures over the typed culture actions

State: **accepted and ready**. Written under the maintainer directive of 2026-10-13 (golden workflow 4). Reviewed against master `bb85d739`. Architecture record: [Engineering Studio architecture](../implementation/engineering-studio-architecture-2026-10-13.md).

- **Hard dependencies:** 186, 188 (and 185, 184, 172 beneath them). Both are merged.

## Fresh evidence (master `bb85d739`)

- **The typed plan already exists and is validated.** `dynamic_models.Schedule` holds up to `MAX_EVENTS` = 1000 `ScheduleEvent`s (`:11`, `:165`). An `actions` event carries 1 to `MAX_ACTIONS` = 16 actions from the closed discriminated union `draw | separate | refill | dose | inoculate` (`:24-93`). It may carry a `StateCondition` with observed `<unit>.X|N|O2|loop_X|loop_N`, direction, threshold, hysteresis, cooldown and `max_fires` (`:97-117`). Every model is `extra="forbid"`, strict, no NaN.
- **Repetition is already declarative.** `time_s`, `every_s`, `count` and `end_s` are expanded in `dynamic_engine.prepare` (`:623`). A recurring campaign needs no loop or code.
- **Host validation is the owner.** `_validate_actions` (`dynamic_engine.py:205`) refuses unknown tanks, unobservable units and volume violations (`EVENT_VOLUME_INVALID`). Run time asserts every event balance (`EVENT_BALANCE_NOT_CLOSED`) and the aggregate (`BALANCE_NOT_CLOSED`). A state-triggered overdraw fails with `EVENT_VOLUME_INVALID_RUNTIME`.
- **Where a schedule lives.** It is a draft document entry written by the `set_schedule` op (`draft_models.py:591`, `draft.py:538`) and revalidated against `Schedule` (`draft.py:566`). A scenario names it by `schedule_id`. Runs go through `dynamic_jobs.start`, which records `snapshot_digest`.
- **No actuator authority.** Actions change tank inventories in the simulated ODE state only. No module in this path talks to hardware.
- **Studio hooks.** `studio/routes.py:14` already lists category `procedure` as unavailable ("planned"). `studio_runtime` caps source at 64 KiB, wall at 15 s and result at 64 KiB (`runtime.py:21-25`).
- **No dynamic GUI yet.** `frontend/src` has no schedule, scenario or dynamic-run surface (173 is planned). The workflow therefore needs a minimal one here.

## Decision

1. **Procedures are declarative, not user Python.** A procedure is a validated typed structure whose compiled form is exactly a `Schedule`. The alternative, user Python in the 187 sandbox emitting a JSON plan, was considered. It would add nothing 185 and 186 do not already give (`every_s`/`count`, conditions, ordered atomic actions), it would cost 0.09 s to 0.55 s per sandbox call, and it would make the plan depend on executed code. It is deferred. If later needed it also needs no boundary change, because the plan would pass the same host validators.
2. **Category.** The `procedure` category becomes available, version kind `studio_procedure_v1`. The 188 draft, Save Draft, Test, Publish, immutable version, library and revise flow applies. The artifact is the procedure JSON. Nothing is executed, so it works with the 187 runtime disabled.
3. **Contract.**
   - Steps: an ordered list of the existing `ScheduleEvent` shapes restricted to `type: "actions"`. Each step has an authoring label, a `time_s` (earliest time when conditioned), an `actions` list, and either optional `every_s`/`count`/`end_s` recurrence fields or an optional `condition`. A conditioned step repeats only through `condition.max_fires`; the recurrence fields are forbidden on it, as in the existing `ScheduleEvent` validator. Authoring labels are omitted from the compiled `Schedule`. The action and condition fields and units are those of 185 and 186, with no new action.
   - Parameters: 188 `Variable`s (Pint unit, optional bounds). A numeric field may be `{"$param": "name"}`. Substitution is host-side and typed. There is no expression language, loop or conditional.
   - Tanks and units are referenced by tag and resolved only on Apply.
4. **Compile.** `compile(procedure, parameter_values, draft) -> Schedule` is deterministic. The result must pass `Schedule.model_validate`. Same inputs give byte-identical JSON, with a `compiled_sha256`.
5. **Test.** A case gives parameter values and a target draft and scenario. The report holds the compiled hash and the result of `dynamic_engine.prepare`, so every `EVENT_*` refusal of 185 and 186 applies. The test may also run the simulation and check expected values with tolerances. The report is bound to the source and contract hashes. Publish rules are those of 188.
6. **Apply.** An explicit user action. It writes the compiled schedule with the existing `set_schedule` op under a chosen schedule id. A Studio-owned link records workspace, draft, schedule id, `version_id`, `source_sha256`, `contract_sha256`, the parameter values and `compiled_sha256`. A later hand edit of that schedule makes the link read "modified, no longer the pinned procedure". Publishing a newer version never changes an applied schedule. "Update to vN" is explicit and re-applies.
7. **Simulation only.** Run uses the existing `dynamic_jobs.start` with its limits unchanged (120 days, 20000 points, 1000 events). Results, balances and per-event records come from the existing owners. Each run shows its procedure link: version, hashes, parameter values.
8. **Minimal test bench.** Studio gains a panel to pick a draft and one of its scenarios, create a minimal scenario if none exists, Apply, Run and view the event log, balance status and series. It is not 173: no controller editor and no timeline editing. 173 may replace it.
9. **Fail closed.**
   - A procedure that does not validate as a `Schedule`, a tank that is absent, an unobservable condition, or a time-triggered volume violation is refused at Test and Apply with the host's typed code. It is never clipped or auto-corrected.
   - An unbound parameter, a unit mismatch or a value out of declared bounds is refused.
   - An artifact whose hash does not match is refused.
   - A run that fails a balance keeps 185's behaviour: failed, with partial artifacts.
10. **Honest limits on screen.** "Simulation only. Actions change modelled tank inventories. This does not command any equipment. Unqualified." is shown on the procedure, the Apply step and the run results.

No security boundary changes. A procedure is data checked by the existing host models. It runs no user code and adds no new route to the 187 runtime. It gives no actuator or hardware authority, and no new action type. So this spec needs no maintainer decision like 189.

## Acceptance

1. **Golden workflow 4, real browser.** On the qualification host, an operator using the GUI only:
   - creates a procedure with the Studio wizard (a parameter `draw_fraction` in percent);
   - adds the steps: every 48 h a `draw` of `draw_fraction`, a `separate` (recovery 0.95, concentration factor 20, return to the tank) and a `refill` to volume; then a conditioned `dose` on `loop_N` below a threshold with cooldown and `max_fires`;
   - tests it and publishes v1;
   - opens the test bench, selects the draft and scenario, applies the procedure and runs it;
   - sees the event log, the closed balances and the per-cycle KPIs;
   - changes `draw_fraction`, re-applies and re-runs, and sees different results;
   - publishes v2 and sees the applied schedule stay on v1 until "update to v2" is chosen.
   The workflow fails if any step needs a backend edit, a new spec, hand-written JSON or a terminal.
2. **Independent closed form.** On the 185 dark, zero-loss reference case (one PBR, one tank, draw 20 %, separate 0.95 and CF 20, refill, dose), the GUI-authored procedure compiles to the same `Schedule` JSON as the 185 test fixture, and every inventory immediately after each event matches the 185 closed form to 1e-12. A conditioned step on the 186 constant-rate case fires within 1e-6 relative of the analytic crossing time.
3. **Determinism.** The same procedure, values and draft compile to byte-identical JSON.
4. **Guards.** An over-draw is refused at Test with `EVENT_VOLUME_INVALID`. A forced runtime over-draw fails with `EVENT_VOLUME_INVALID_RUNTIME`. A missing tank, a unit mismatch and an out-of-bounds parameter are refused with typed codes.
5. **Pinning.** A hand edit of an applied schedule is flagged. Publishing v2 leaves the applied schedule and past runs unchanged. A tampered artifact hash is refused.
6. **Boundary.** With the 187 runtime disabled, procedures still compile, test, apply and run. No procedure path calls the runtime. The 187 hostile suite passes unchanged, and no action type or route outside 185 and 186 exists.
7. **Compatibility.** The 172, 185, 186 and 188 suites pass without edits. A draft without an applied procedure keeps a byte-identical document and snapshot digest.

## Required evidence

- Backend tests for criteria 2 to 7, with the real dynamic engine. Criterion 2 compares to independent closed forms, not the engine.
- A frontend test file gating the build for the wizard, the step editor and the test bench.
- A real-browser proof of criterion 1 with screenshots on the exact head.
- Full backend suite in a clean environment, ruff, frontend build and the registry checks.

## Non-goals

- No hardware, PLC, valve or pump control, no real-time execution, and no new actuator authority. Simulation only.
- No new action or condition type, no compound or rate-of-change conditions, no expression language, loops or user Python. User-code plans are deferred.
- No controller editor, timeline drag-editing or full Dynamic Studio (173).
- No procedure inside a steady solve, no use of impulsive actions by controllers, and no optimization of procedures.
- No binding of procedure parameters to project Parameters in this slice.
- No CAD (189), custom units (190), notebooks or spreadsheets (192). No automatic qualification.
