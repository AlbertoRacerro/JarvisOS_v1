# 155 — Process flowsheet working draft

State: **ready**. Combined definition, full contract and readiness under the maintainer's 2026-09-28 ordering directive (155 after 156 and 157) and the 2026-09-29 architecture decision recorded below. Dependencies 149, 156 and 157 are `merged` in STATUS at fresh master `ff5a90b8`.

## Maintainer decision (2026-09-29): Jarvis owns the draft, DWSIM is derived

An earlier uncommitted draft of this contract proposed that the DWSIM revision chain *be* the draft, so that every canvas edit is a DWSIM round-trip. The maintainer rejected that design. The binding architecture is:

- **The editable flowsheet is a typed, declarative Jarvis draft.** Canvas edits are Jarvis-authoritative and effectively instantaneous. Adding, deleting, dragging, connecting, renaming, parameter changes and approved agent changes update only the Jarvis draft and create a new immutable Jarvis revision. Ordinary edits never contact DWSIM.
- **The supported vocabulary is deliberately constrained.** Every object type, port, property, unit, composition and equipment setting that the draft accepts has a deterministic DWSIM materialization. The draft schema, the frontend forms, the compiler mapping and the read-back mapping are one registry. Jarvis never exposes a supported state that its compiler cannot reproduce. Anything outside the registry is explicitly *unsupported*; it is not faked.
- **DWSIM is the derived validation and solver runtime.** Validate and Run compile the complete selected Jarvis revision into a fresh DWSIM flowsheet. A normalized semantic read-back then compares objects, types, tags, connections and ports, feed-stream specifications, compositions, supported equipment parameters, compounds and the property package against the compiler's expectation. **Any materialization mismatch refuses the solve** with a precise per-path diagnostic (path, expected, actual) and an optional retry. Drift is never silently accepted.
- **Determinism.** The same Jarvis revision compiled with the same compiler version, DWSIM version and MCP digest produces the same normalized materialization and the same materialization fingerprint.
- **Run binding.** Every solve and result is bound to the exact Jarvis revision it compiled, plus the materialization fingerprint, compiler version, DWSIM version and MCP digest. After any later draft edit, the results are reported **stale** immediately.

This supersedes the "DWSIM revision chain is the draft" design. The 149 DWSIM-native case editor stays available unchanged as an advanced surface for imported native cases and dynamics; it is not the 155 draft store.

## Fresh baseline (what already exists)

- 149: `process_stack/editor.py` (DWSIM-native revisioned case editor over the pinned DWSIM 10.2.9 MCP), `dwsim.py` (hash-pinned runtime resolution, connector read-back from saved XML, boundary mass balance), `frontend/src/stages/ProcessStage.tsx` (`/design/process`).
- 151/152/153/154b: Sidecar and Hermes on the local Gemma responder, with the broker tools `jarvis_context_preview`, `jarvis_retrieval_query` and `jarvis_decide`, all grant-scoped per interaction. 152 forbids engineering mutation from agent text.
- 154c/156/157: `STRICT_IP` default, governed cloud escalation, the Relay safe workspace, and `private_domain_data.enabled=false`.

## Accepted capability

1. **Draft owner** (`process_stack/draft*.py`, routes `/workspaces/{id}/process/drafts/...`).
   - The draft document holds `compounds`, `property_package`, and `objects` keyed by a stable Jarvis id. Each object has a type, a unique tag, a position, and typed parameters. Material streams carry `source` and `target` endpoints `{unit, port}`, so a stream without a source is a feed and a stream without a target is a product.
   - Edits are a typed operation list applied atomically under compare-and-swap (`expected_revision`, 409 on conflict). The operations are `add_unit`, `add_stream`, `delete`, `move`, `rename`, `connect`, `disconnect`, `set_stream_spec`, `set_unit_params` and `set_thermo`.
   - Each applied patch writes an immutable revision (`<seq>:<content sha256 prefix>`) with parent, operations, actor (`operator` | `hermes_proposal:<id>`) and timestamp. Any revision can be restored as a new revision.
   - Quantities arrive as value + unit and are converted server-side through the existing `Quantity` path. They are stored canonically in SI. No conversion happens in the frontend.
   - Delete and disconnect are supported, because the draft is Jarvis-owned.
2. **Supported registry (v1 subset).**
   - Compounds come from a curated list. Property packages are NRTL, Peng-Robinson (PR), Soave-Redlich-Kwong (SRK), Raoult's Law, UNIQUAC and Steam Tables (IAPWS-IF97).
   - Feed streams take temperature, pressure, mass flow and a mass-fraction composition.
   - Supported equipment:
     - Heater and Cooler: outlet temperature and pressure drop;
     - Pump: outlet pressure or pressure increase, plus efficiency;
     - Valve: outlet pressure or pressure drop;
     - Mixer: 2–3 feeds;
     - Flash vessel: vapor on port 0, liquid on port 1.
   - Energy streams, splitters, heat exchangers, columns, reactors and recycles are reported as unsupported in 155. Adding one later means a registry entry (schema + form + compiler + read-back) plus tests, with no architecture change.
3. **Jarvis-side pre-run validation** (instant, no DWSIM). It reports these findings with object and field: required ports unconnected, feed specification incomplete, composition not summing to 1 or naming undeclared compounds, a missing property package or compounds, duplicate tags, and product streams that carry specs.
4. **Compiler + read-back + solve** (`process_stack/draft_compiler.py`). `POST .../revisions/{rev}/validate` and `POST .../revisions/{rev}/run` compile the exact revision into a fresh DWSIM flowsheet.
   - **Read-back.** The compiler reads the materialization back from both the live MCP and the saved native XML (tags, simulation types, connector graph by tag/port, feed stream T/P/flow/composition, unit `CalcMode` and parameters, compounds, package). It normalizes that read-back and compares it field by field with the expected normalization derived from the draft.
   - **Mismatch refuses.** A mismatch stops the solve (`materialization_mismatch`) and reports the diffs.
   - **Validate** additionally runs DWSIM's `dwsim_flowsheet_check`.
   - **Run** solves and records a run with `run_id`, `draft_revision`, `materialization_fingerprint`, `compiler_version`, `dwsim_version`, `mcp_sha256`, `solve_status`, per-stream results (T, P, mass flow, vapor fraction where available), per-unit results, the boundary mass-balance residual, and the saved native case digest. The run is stored beside the draft, never in the draft.
   - **Results state.** The projection reports `none` | `current` | `stale`, with the solved revision and the number of edits since. There is no global `/runs` integration in 155; the local provenance is complete enough to add it later.
5. **Structured Hermes proposals.**
   - **Tools.** The broker gains two grant-scoped tools, installed per Sidecar interaction like `jarvis_decide`. `jarvis_process_read` is read-only and returns a compact draft projection (objects, tags, typed parameters in display units, results state). `jarvis_process_propose` takes changes of the form `{target tag, property, proposed value, unit}` plus `base_revision` and a rationale.
   - **Pending proposal.** Jarvis validates each change against the registry, resolves the target and fills the authoritative **current value** from the base revision. It stores a *pending proposal* and never touches the draft.
   - **Operator review.** The Sidecar shows the change set (target, property, current → proposed, unit) with Approve/Reject. The Process canvas highlights the affected objects with an old→new badge.
   - **Approve** applies the patch atomically through the draft owner (CAS on `base_revision`) and creates a new revision attributed to the proposal. **Reject** changes nothing. A proposal whose base revision is no longer head is shown as stale and cannot be approved.
   - **DWSIM** is not contacted until the operator validates or runs. This narrowly amends 152: agents may *propose* typed draft changes, and only operator approval mutates.
6. **Process page UX.**
   - The canvas is draft-backed. Its edits are optimistic and instant, and every edit is persisted as a revision.
   - Canvas features: palette, drag, port-aware connect by selecting a stream's endpoint, delete, and labels with key stream values.
   - Typed inspectors: feed streams take T/P/flow with unit selectors (°C/K, bar/kPa/Pa/psi, kg/h/kg/s/t/h) and a composition table. Equipment inspectors offer a mode selector plus unit-bearing fields.
   - Panels: a thermo panel (compounds and package), a validation panel (Jarvis findings and DWSIM check), and Validate/Run buttons with materialization diagnostics and retry.
   - Results: a results panel with a current/stale banner and revision provenance, plus a revision history with restore.
   - The 149 native case editor remains reachable as an advanced view.

## Boundaries / non-goals

- No frontend-owned or model-computed engineering values. DWSIM is the only solver. No second solver, no equation-oriented engine, no autonomous design loop.
- No attempt to cover all of DWSIM. No energy streams, recycles, columns or reactors in 155. No dynamics on drafts (149 dynamics stays on native cases).
- No global `/runs` integration. No cloud or Relay process tools: cloud and Relay stay advisory under `STRICT_IP`, and no mutating process tool is exposed off-host.
- Synthetic, non-sensitive fixtures only (water/methanol pump–heater–valve–flash). No BlueRev or private data. `private_domain_data.enabled=false` stays.

## Required evidence

- **Deterministic backend tests:**
  - draft operations and CAS;
  - unit conversion;
  - registry validation, including unsupported types and ports;
  - Jarvis validation findings;
  - compiler call plan and expected normalization;
  - read-back comparison that refuses with precise diffs on an injected mismatch;
  - fingerprint determinism;
  - run binding and current → stale → current;
  - proposal lifecycle: propose never mutates, current value filled server-side, approve creates an attributed revision, reject is a no-op, a stale base cannot be approved, and invalid targets or properties are refused;
  - broker grant checks for both tools.
- **Frontend tests:** instant edit without DWSIM calls, unit-selector payloads, the composition table, the stale banner, the mismatch diagnostics, and the proposal approve/reject UI and canvas badge.
- **Real host acceptance** (canonical WSL host, launcher, browser, pinned DWSIM):
  1. Build the synthetic train from the palette, with edits measured as instant.
  2. Validate: Jarvis findings, then DWSIM check.
  3. Run, and see results bound to revision N.
  4. Compile the same revision twice and get the same fingerprint.
  5. An injected materialization mismatch refuses the solve with diagnostics.
  6. After an edit, results go stale.
  7. Hermes proposes a change in the Sidecar, and the canvas and Sidecar show it.
  8. Reject changes nothing. Approve creates revision N+k.
  9. Rerun gives current results bound to the new revision.
- Exact-head CI green.

## Completion

The operator builds and edits a small flowsheet instantly in Jarvis in engineering units, validates it, and runs it through a verified deterministic DWSIM materialization. Results always name their exact Jarvis revision and go stale on edit. Hermes can propose precise typed changes that only the operator's approval applies. STATUS, devctx and evidence are reconciled after merge.
