# 190 — Engineering Studio custom process unit: author, place, solve

State: **accepted and ready**. Written under the maintainer directive of 2026-10-13 ("then plan the custom CAD geometry and user-defined process-unit slices using the evidence from Stage 5"; golden workflow 3). Reviewed against master `6b693d02`. Architecture record: [Engineering Studio architecture](../implementation/engineering-studio-architecture-2026-10-13.md).

- **Hard dependencies:** 168, 188 (and the 183 tear solver it uses).

## Fresh evidence (master `6b693d02`, WSL2 qualification host, 2026-10-14)

- **Jarvis-owned units already participate in the solve.** `mixed_runtime.JARVIS_EVALUATORS` maps a unit type to an evaluator `(unit, inlet, context) -> JarvisUnitEvaluation`. The mixed solve calls it once per tear iteration, checks outlet names and culture generation (`_check_evaluation`), then flashes each outlet through DWSIM from temperature, pressure, mass flow and mass fractions (`_feed_spec`). `SpecifiedSeparator` and `PhotobioreactorT1` use this path. No DWSIM IronPython is involved.
- **The registry is static.** `draft_models.UNIT_REGISTRY` is a module constant with fixed ports. Draft validation refuses any type not in it. The palette is `GET /process-draft/registry`, a projection of that constant.
- **One inlet only.** The runtime takes the first stream into a Jarvis unit (`incoming = next(...)`). Multi-inlet Jarvis units do not exist.
- **Dynamic support is a closed set.** `dynamic_engine._t1_reachable` lists the supported unit types.
- **Sandbox cost per call is small.** Measured with `studio_runtime.run` and the real bubblewrap sandbox, 8 calls each: a plain-Python unit evaluation takes 0.09 s median (0.086 to 0.092 s); with `import numpy, scipy.optimize` it takes 0.55 s median (0.44 to 0.95 s). The default solve is 25 tear iterations within a 90 s wall budget, so one sandboxed call per unit per iteration fits a few custom units.
- **The 188 owners are reusable:** wizard, deterministic scaffold, editor, derived documentation, Save Draft/Test/Publish, immutable versions, library, revise.

## Decision

1. **Category.** Studio gains the executable category `process_unit`, version kind `studio_unit_v1`. It is a steady unit operation. The 188 wizard, editor, documentation, lifecycle and library apply unchanged.
2. **Contract.** The wizard asks for:
   - 1 to 4 material inlet ports and 1 to 4 material outlet ports, each a Python identifier with a label;
   - parameters as 188 `Variable`s (unit parsed by Pint, optional bounds);
   - an optional sanitized SVG symbol. It is sanitized on save, and a symbol that fails sanitization is refused. Without one, a generic symbol labelled with the port names is used.
   No energy ports in this slice.
3. **Scaffold.** It is deterministic as in 188: `evaluate(inlets, params) -> outlets`. A stream is a plain dict: `mass_flow_kg_s`, `temperature_K`, `pressure_Pa`, `mass_fractions` (draft compounds) and `culture` (the 168 culture fields, mass-specific). Parameters arrive in their declared units. The placeholder body raises until edited.
4. **Host checks on every call.** These apply in Test and in the solve:
   - outlet names equal the declared outlets;
   - every number is finite, flows are ≥ 0, temperature and pressure are > 0, mass fractions are ≥ 0, cover only draft compounds and sum to 1 within 1e-9;
   - total mass and each compound's mass are conserved within 1e-9 relative;
   - culture species are conserved unless the version declares generation. Declared generation is returned and checked by the existing `_check_evaluation` and culture-balance owners.
   A violation fails the unit with a typed code. It is never clipped or renormalized.
5. **Test.** A case gives inlet streams and parameter values, and optionally expected outlet values with tolerances. The report is bound to the source and contract hashes. Publish rules are those of 188.
6. **Placement.** A published version appears in that workspace's Process palette. It comes from the registry projection, extended per workspace from published `studio_unit_v1` versions. The static `UNIT_REGISTRY` is not mutated. A placed unit is `type: "StudioUnit"` and pins `version_id`, `source_sha256` and `contract_sha256`. Its ports come from the pinned contract. Connections are allowed only to declared material ports. Parameter values are entered in the inspector in the declared units.
7. **Solve participation.**
   - `StudioUnit` is a Jarvis-owned unit. Its evaluator runs the pinned source through the 187 runtime, one sandboxed call per evaluation, with the `calculation` limits unchanged.
   - Results are cached for one Process Run, keyed by source hash, parameters and inlet states.
   - The mixed runtime gains multi-inlet support for Jarvis units: every inlet stream must be known at the unit's level, which the existing level ordering guarantees.
   - Outlets are flashed by DWSIM exactly as for the separator.
   - Running the solve is the explicit user action. Each run records, per custom unit: version id, both hashes, call count, runtime classification and duration.
8. **Fail closed.**
   - With the runtime disabled or unavailable, a flowsheet containing a `StudioUnit` is refused before the solve starts, with the reason. It is never skipped or treated as a pass-through.
   - A pinned version whose artifact hash does not match is refused.
   - The dynamic engine refuses `StudioUnit` with a visible "steady only" finding.
9. **Honest limits on the canvas and in results.** "Steady only; no energy balance is checked; outlet temperature and pressure are set by the model; unqualified" is shown on the unit and in its results. Inspect opens the pinned version in Studio.
10. **Superseded and stale.** Publishing a newer version does not change placed units. The inspector offers an explicit "update to vN" action that re-pins. A run made with an older pin is shown as superseded, and runs are never mutated.

No security boundary changes. User code runs only through the 187 runtime with the same limits and the same JSON-only channel. No files leave the sandbox, nothing new is mounted, and nothing reaches DWSIM except the host-checked stream state. So this spec does not need the escalation that 189 needs.

## Acceptance

1. **Golden workflow 3, real browser.** On the qualification host, with the runtime enabled and real DWSIM, an operator using the GUI only:
   - creates a custom nutrient dosing unit: inlets `culture` and `dose`, outlets `outlet` and `unused_dose`, and a parameter `dose_split` in percent. `dose_split` sends that share of the dose stream into `outlet` together with the culture stream, and the rest to `unused_dose`. Both outlets together conserve total mass, every compound and every culture species. A single-outlet dosing unit cannot respond to `dose_split` under these balances;
   - writes `evaluate`, tests it and publishes it;
   - places it from the Process palette;
   - connects a culture feed and a nutrient feed, with a product stream to a downstream Heater;
   - solves.
   The run shows the unit solved, with both outlets flashed by DWSIM and the Heater solved downstream of `outlet`. Whole-graph mass and culture balances close. The unit's provenance shows version, hashes and call count. Changing `dose_split` and re-solving changes the nitrogen concentration in `outlet`, while the balances over both outlets still close. Publishing v2 leaves the placed unit on v1 until "update to v2" is chosen. The workflow fails if any step needs a backend edit, a new spec, hand-written JSON or a terminal.
2. **Participation is real.** A unit whose `evaluate` raises fails the solve with the unit's tag and a typed code. A unit that breaks mass conservation fails with `STUDIO_UNIT_MASS_IMBALANCE`. Neither is skipped.
3. **Recycle.** A `StudioUnit` inside a recycle loop converges through the 183 tear solver on a case with a closed-form answer, within the wall budget.
   - **Runtime budget.** A recycle case with at least three sandboxed `StudioUnit`s converges within the default 90 s wall budget. The test records the per-unit call count, cache hits and sandbox time from run provenance. A budget too small for the sandbox calls stops with the typed timeout code, never with a silently truncated solve.
4. **Execution boundary.** With the runtime disabled, a flowsheet containing a `StudioUnit` is refused before the solve. A tampered artifact hash is refused. The 187 hostile suite passes unchanged.
5. **Ports.** Connections to undeclared ports, and missing required inlets, are refused at draft validation.
6. **Existing units unchanged.** The 168, 170, 183, 184 and 185 process suites pass without edits. Flowsheets without a `StudioUnit` keep a byte-identical compiled document and fingerprint.
7. **Dynamic refusal.** A dynamic run that reaches a `StudioUnit` is refused with the steady-only finding.

## Required evidence

- Backend tests for criteria 2 to 7, with the real 187 runtime for execution and real DWSIM 10.2.9 for criteria 1 to 3 and 6.
- A frontend test file gating the build for the palette entry, the port rendering and the inspector.
- A real-browser proof of criterion 1 with screenshots on the exact head.
- Full backend suite in a clean environment, ruff, frontend build and the registry checks.

## Non-goals

- No energy ports or energy balance, no dynamic (ODE/DAE) custom units, no custom thermodynamics or property packages.
- No user Python inside DWSIM IronPython, and no change to native DWSIM units.
- No binding of unit parameters to project Parameters in this slice. The inspector holds values, as for the built-in units.
- No CAD (189), procedures (191), notebooks or spreadsheets (192). PBR specs 173 to 179 are re-evaluated after this slice, not here.
- No automatic qualification.
