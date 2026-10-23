# 211 — Dynamic Studio plant and equipment information architecture

State: **accepted and ready** under binding roadmap directive `L20261022122708-233d` (Dynamic Studio P1/P2). Hard dependencies 155, 172 and 173 are merged. This contract uses the existing Process draft and dynamic-run authorities; it does not authorize new scientific results.

## Outcome

An operator opens a completed Dynamic Studio run and understands the plant at a glance, selects equipment on an interactive process flowsheet to inspect its own results, and chooses any available metric for one shared comparison table and chart. The choice and order survive leaving and returning to the draft. The UI keeps aggregate plant quantities distinct from equipment quantities and carries every value's unit, source run, fidelity, qualification and stale/partial state.

## Accepted boundaries

- The Process draft projection owns topology and equipment identities. The dynamic run status, manifest and series own numerical results and provenance. A layout representation of the existing draft graph may be shared with Dynamic Studio, but it is read-only there. No independent graph or KPI store is introduced.
- The interactive graph is explicitly a **PFD**: units and material streams in the draft, with equipment selection. It is not called a P&ID. Instrumentation, valves, control-loop piping and any claim of a true P&ID require their own accepted data contract and proof; an existing controller record is not sufficient to infer that drawing.
- Plant overview defaults to a small set of genuinely plant-level quantities already reported or directly derivable from the current run, such as cumulative harvested biomass and aggregate balance status. A per-unit concentration or productivity is never relabelled or summed as a plant total. Missing and non-qualifying metrics say why they are unavailable.
- Selecting a unit shows only metrics and channels attributable to that equipment. The operator can add or remove any available plant or equipment metric from the shared comparison table and charts, reorder selections, and compare compatible values across runs without mixing units or provenance. An unavailable metric remains visible with its reason instead of becoming a fabricated zero.
- Persist only presentation choices (chosen run, equipment, metric IDs, display order, chart/table preference) for this single-user operator, scoped by workspace and draft. The stored choice cannot create or promote a result. Validate restored IDs against current topology and run data; stale or removed references are shown as unavailable or dropped with an explanation. The server's revision and result truth always wins.
- Preserve the 173 scenario/schedule/controller editing, run actions, series paging, CSV and simulation-only notice. Reuse its chart and comparison functions where suitable. No new provider, execution, physics, backend route, schema or product authority is implied.

## Acceptance

1. In a real browser, an operator opens a draft with at least two equipment items and a completed dynamic run, sees a compact plant overview and a PFD, selects each item by pointer and keyboard, and sees different local metrics. The overview never repeats every local KPI as global cards.
2. The operator adds an aggregate metric and local metrics from both units, reorders them, removes one, and sees the same ordered set in the shared table and charts. Selection and order survive reload and switching away and back to the draft. A changed topology, unavailable channel, stale run and partial run are represented truthfully.
3. A two-run comparison uses only metrics with compatible units and definitions. Table and chart identify the source run/scenario/revision, equipment or aggregate scope, unit, fidelity and qualification. Missing values and sampled/strided views are explicit. No equipment-specific metric is called a plant aggregate.
4. The graph is labelled PFD. The UI does not offer or imply a true P&ID from the present draft/controller data.
5. Existing 173 editing, run, result and comparison workflows still work. Frontend tests cover metric scope, selection persistence/validation and comparison qualification; a real-browser workflow proves the interaction and responsive/keyboard presentation on the exact implementation head. Run the frontend build and relevant backend tests if server code changes.

## Non-goals

- New dynamic model, solver, KPI formula, numerical qualification, instrumentation/P&ID schema, history store, workspace permission, multi-user synchronization or backend mutation.
- Replacing the authoritative Process draft editor or changing the steady-state Process results surface.
