# 162 — Process editor human acceptance

State: **ready**. This spec combines definition, contract and readiness under the maintainer directive of 2026-10-01. Dependencies are 155, 158 and 161; it consumes 161's shared `ContextMenu` primitive. It owns the Process draft backend (`backend/app/modules/process_stack/draft*`), `ProcessDraftEditor` and `ProcessStage`.

## Fresh evidence (master `fc34a316`)

- **Layout.**
  - Units store only `x`/`y` in the draft.
  - Port anchors are fixed: material inlets on the left, outlets on the right, energy ports on the bottom.
  - No context menu exists in the frontend.
  - Results go stale on `move` because `expected()` includes x/y. A route-only change does not make them stale.
- **Streams.**
  - Feeds accept T, P and mass flow (kg/s internally) plus mass-fraction composition.
  - `FEED_SPEC_MISSING` blocks a missing value, but a zero flow passes.
  - The pinned DWSIM MCP also accepts `molar_flow_mol_s` and `vapor_fraction`.
  - The 158 manifest has no MaterialStream entry.
- **Guidance.**
  - `validate_document` emits blockers only.
  - `solve.errors` text is captured but not rendered ("DWSIM reported errors.").
  - `runtime_failed` keeps only the exception class.
  - The Hermes `jarvis_process_read` view omits DWSIM check findings, solve errors and result values.
- **Controls.**
  - The controls are: stage tabs `Flowsheet draft` / `Native DWSIM cases (advanced)`; a toolbar with Draft select, revision, `Validate (DWSIM)`, `Run (DWSIM)`, state badge and History.
  - Unit boxes are a fixed 76×44 px, so `Plug flow reactor` and `Distillation column` labels overflow.
- **Editing after Run.** Editing is never disabled. The trapped feeling is presentation: result state dominates and inputs and results are not distinguished.

## Accepted capability

1. **Orientation.**
   - A unit can be mirrored left↔right and top↔bottom. Port sides, port stacking and edge routing follow the orientation.
   - Orientation is stored in the authoritative draft as a revisioned layout-only operation.
   - Layout-only operations (orientation, route and position) never change process meaning. They do not make results stale, and the DWSIM materialization comparison stays truthful.
   - Actions are available from a unit's context menu (right-click), from the keyboard (context-menu key or Shift+F10 on the focused unit), and from an inspector secondary menu.
2. **Material stream specification from probed DWSIM 10.2.9.**
   - Probe the pinned MCP to determine which feed specifications are real operator inputs, which are mutually exclusive alternatives, and which are calculated or read-only. Candidates include mass versus molar flow basis, T versus vapor fraction, and mass versus mole composition.
   - Expose only the probe-proven alternatives, with engineering units. Store the probe evidence alongside the 158 evidence.
   - Results show the calculated flows (mass, molar and volumetric when available) clearly separated from inputs.
3. **Physical-meaningfulness guidance.**
   - Jarvis-side assessment distinguishes **blocking errors** (cannot run) from **warnings/advice** (can run but the result may be meaningless). Examples:
     - zero or missing feed flow;
     - incomplete composition;
     - unconnected optional ports;
     - a reactor without reactions or with zero volume;
     - heater, cooler or exchanger specifications that do nothing;
     - column specification gaps;
     - a recycle without a meaningful tear;
     - post-run results that indicate degenerate output, such as zero-flow products or failed objects.
   - Real DWSIM check findings, solver errors and refused or failed steps reach the UI as plain text.
   - The Hermes process read view includes blockers, warnings, DWSIM findings and errors, and key current results, so Jarvis can answer "what is missing for this flowsheet to make physical sense?" from structured evidence.
4. **Editing after Run.**
   - The canvas stays fully editable after a run.
   - The inspector shows editable inputs together with read-only calculated results labelled with their run revision.
   - Any process-meaning edit creates the next revision and marks prior results visibly stale. Run is immediately available again.
5. **Primary workflow.**
   - The primary path (draw, specify, Run, read results) is obvious.
   - Run is primary, and a visible readiness chip shows the blocker and warning counts.
   - Validate-only, revision history, draft switching or creation, and Native DWSIM cases move into secondary or advanced disclosure.
   - Equipment labels fit their symbols: boxes are sized to the label, or a short type label is used with the full name accessible. Labels are not just shrunk.

## Boundaries / non-goals

- DWSIM remains the simulator. There are no frontend equations and no physics reimplementation beyond simple deterministic sanity checks on declared inputs and returned results.
- The draft stays the single authority. There is no second layout store.
- The 155/158 revision CAS, materialization verification and proposal approval are unchanged.
- There are no new unit operations and no change to the property-package catalogue.
- Native DWSIM cases (149) remain reachable, in secondary placement.

## Required evidence

- **Backend tests:**
  - the orientation op is revisioned, layout-only, keeps results current and round-trips;
  - new stream-spec alternatives are validated and compiled to the MCP calls;
  - warnings are distinguished from blockers;
  - solve errors and runtime failures are surfaced as text;
  - the agent view contains guidance and results.
- **Real pinned DWSIM 10.2.9 evidence:**
  - the probe of feed-spec alternatives;
  - a flowsheet with a molar-flow feed solves;
  - a zero-flow feed shows a warning;
  - a mirrored-unit recycle flowsheet still solves with current results.
- **Real Chromium** at 1280 and 1440 px:
  - right-click and keyboard mirror;
  - no label overflow on PFR or column;
  - edit after Run creates a stale state, then re-Run;
  - the readiness chip and the guidance list;
  - DWSIM error text visible on a deliberately failing case;
  - no horizontal overflow.
- Exact-head CI green.
