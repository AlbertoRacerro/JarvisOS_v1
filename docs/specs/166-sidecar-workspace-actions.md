# 166 — Sidecar workspace actions

State: **ready**. This spec combines definition, contract and readiness under the maintainer directive of 2026-10-02 ("agentic workspace actions"). Dependencies are 155, 157, 161, 162 and 163. It owns the governed path by which a Sidecar turn (local Jarvis or Relay cloud reasoning) changes the visible Process or BLUECAD workspace.

## Fresh evidence (master `9e44fdfa`)

Operator test: on BLUECAD, "create another identical tube besides it" produced an answer about the Process PFR with raw tool-call JSON in the transcript; Relay said it had no scene or selection. On Process, "add monod type kinetics to the pfr-1" showed raw tool-call JSON; Relay correctly said Monod is unsupported.

Root causes (code-verified):

1. **No surface context.** The Sidecar never sends the route, and the turn always submits `DEFAULT_SELECTION = {}` (`useJarvisSidecar.tsx` preview and submit). The backend cannot tell BLUECAD from Process, or which object is selected.
2. **Cross-surface leak.** `thread_service._install_process_grants` grants `jarvis.process_read`/`jarvis.process_propose` and injects Process-draft instructions on every turn whenever the workspace has any draft.
3. **Name mismatch.** The injected instruction names `jarvis_process_propose`, but the relay only admits `mcp__jarvis__jarvis_process_propose`. `worker_shim.completion_message` then falls back to returning the call text as the answer.
4. **Unguarded text protocol.** Local tool calls are a flattened text protocol (`RELAY_TOOL_PROTOCOL`). Any call that is malformed or names a non-admitted tool becomes `assistant_text` and is rendered verbatim by `JarvisMessageText`.
5. **No BLUECAD actions.** No agent tool exists for BLUECAD. The only geometry mutations are candidate creation, archive and promote. `GeometrySpec` already supports several framed parts, and candidates already carry `origin` and `parent_candidate_id`.
6. **Relay gets only the user text.** The escalation contains the operator's text plus governed releases. It returns plain `result_text`.
7. **Process proposals are property-only.** `ProposalRequest.changes` supports only target/property/value. The draft already has a complete typed, revisioned op set (`AddUnit`, `Connect`, `SetStreamSpec`, `SetOrientation`, …) with `patch(expected_revision)` and `restore`.

## Decision

**Jarvis owns one workspace-action layer. Models only propose typed actions into it.**

Two kinds of model can reason about an action: the local agent (Hermes on Gemma, through tools) and the Relay cloud agent (through a structured block in its advisory answer). Both produce the same typed **action request**. Jarvis validates that request against the canonical owner at an explicit base revision, classifies it by policy tier, and either applies it through the owner's existing mutation path or records it as a pending proposal for one-click operator approval. Every outcome is recorded with provenance on the interaction and rendered as a human-readable action card.

Alternatives rejected:

- **Relay mutating directly.** Giving the cloud session a Jarvis write tool or MCP would cross the 157 boundary: the sandbox is advisory, read-only and network-confined. Returning a structured block that the operator then applies keeps all mutation local and visible.
- **Hermes as sole executor.** Hermes stays the local *planner* and calls Jarvis tools. Execution belongs to the workspace owners, so Relay and future surfaces reuse the same executor.
- **Exposing the whole tool catalog.** Gemma 12B's tool accuracy falls as the tool list grows (pre-155 evidence). Tools are scoped to the current surface: Jarvis filters each relayed model request and issues grants per surface.
- **Regex repair as the main fix.** When a local agent turn offers tools, the llama.cpp request is grammar-constrained by a JSON schema (`--jinja` server, `response_format` json_schema). The output can then only be `{"answer": …}` or `{"tool_calls": […]}` naming admitted tools. Repair stays as a fallback only. Text that still looks like a tool call is never shown as an answer.

## Accepted capability

1. **Surface context (bounded and inspectable).**
   - Each submit carries a `surface_context`: `route_id` plus canonical selection refs. For Process this is the draft id and an object id or tag. For BLUECAD it is a candidate id and a part id resolved through the fail-closed 163 scene binding.
   - The backend re-derives a bounded **surface brief** from the owners. It never trusts frontend values. The brief contains: surface; workspace; draft or candidate id and head revision; the selected object(s) with type, canonical id, tag and editable properties with units and current values; results state; and the surface's action vocabulary and known limits (e.g. "reactions: Arrhenius power-law only; Monod/custom rate laws unsupported").
   - The brief is stored with the interaction (digest + content) and shown to the operator as a compact context chip ("BLUECAD · tube candidate c… · selected: tube_run `tube`"). The full brief is under a disclosure.
   - Off-surface routes get no Process or BLUECAD grants or instructions. When no surface object exists, the chip says so truthfully.
2. **Surface-scoped agent tools (local).**
   - Process route: `jarvis_process_read` and `jarvis_process_act`.
   - BLUECAD route: `jarvis_bluecad_read` and `jarvis_bluecad_act`.
   - Other routes keep only the existing context, retrieval and decision tools. `jarvis_process_propose` is superseded by `jarvis_process_act`.
   - Grants are issued per turn for the current surface only. The relay strips non-surface tool schemas from each model request. Dispatch refuses calls without a live grant of that capability.
   - Instructions name the exact admitted tool names. Admission normalizes the `mcp__jarvis__` prefix both ways, so the bare and prefixed forms of the same admitted tool resolve to it and nothing else.
3. **Action vocabulary.** Actions are tag- and unit-explicit and are resolved to canonical ids by the executor.
   - **Process:**
     - `set_value(target, property, value, unit)` covers stream specs and unit params.
     - `add_unit(type, tag?, near?)`.
     - `insert_unit_after(type, after, tag?)`: rewires the single material outlet stream of `after` through the new unit. Refused if that outlet is ambiguous.
     - `connect(from, from_port?, to, to_port?)`.
     - `disconnect(stream)`.
     - `mirror(target, axis)`.
     - `move(target, dx, dy)`.
     - `rename(target, new_tag)`.
     - `delete(target)`.
     - Reactions and thermo stay operator-editor operations in this slice. The agent states the limit. It never substitutes an approximation (e.g. Arrhenius for Monod) unless the operator explicitly asks for an approximation.
   - **BLUECAD:**
     - `duplicate_part(part, placement: beside|above|along, gap_mm?)`. "Beside" offsets perpendicular to the part axis by its outer extent plus the gap. The default gap is half the outer diameter.
     - `set_part_param(part, param, value, unit)`.
     - `move_part(part, dx, dy, dz, unit)`.
     - `delete_part(part)`. This is refused when it would delete the last part.
     - Each BLUECAD action derives a **child candidate** from the base candidate's stored `GeometrySpec`. The child is built through the existing canonicalize → build → validate → export path, with `origin` set to the agent origin and `parent_candidate_id` set to the base. The base candidate is never modified.
4. **Executor and tiers.** `workspace_actions` validates each request by a dry run on the base revision and returns a structured outcome: `applied`, `proposed`, `refused` (with plain-text reason) or `stale`.
   - **Immediate (applied, with Undo).** Local-origin actions that are layout-only (`mirror`, `move`) or that create a BLUECAD child candidate. A BLUECAD child is non-destructive because the parent stays intact.
   - **Confirm (proposed; one-click Apply/Dismiss inline, never modal).** Process value, topology or tag changes (`set_value`, `add_unit`, `insert_unit_after`, `connect`, `disconnect`, `rename`, `delete`), and every Relay-origin action.
   - **Not agent-executable in this slice.** Running DWSIM, exports, promote/archive, reactions/thermo, native DWSIM cases, and anything outside Process or BLUECAD.
   - **Undo.**
     - Process: restore the parent revision. This is refused if the head has moved past the action's revision.
     - BLUECAD: archive the child and re-select the parent.
   - **Provenance.** Each applied or approved mutation records actor `agent:local:<thread>/<interaction>` or `agent:relay:<run>`, the action request digest, and the base and resulting revision or candidate. Process drafts keep their existing revision and stale semantics, so value or topology edits make prior results stale.
5. **Transcript presentation.**
   - Each turn shows the operator request, concise progress ("Reading flowsheet…", "Creating candidate…"), action cards (applied + Undo; proposed + Apply/Dismiss; refused + reason), then Jarvis's answer.
   - Raw tool calls, arguments, grant ids and JSON appear only under a "Technical details" disclosure.
   - A model output that is still tool-call-shaped after admission is never rendered as an answer. It becomes a refused action ("Jarvis produced an invalid action; nothing was changed") with details hidden.
   - Cards are keyboard-operable and labelled for assistive technology.
6. **Workspace refresh.** After an applied or approved action, the visible surface updates without a manual reload. The Process canvas and inspector show the new revision and stale results. BLUECAD selects and renders the child candidate, whose parts are inspectable in the 3D viewer.
7. **Relay produces actions locally applied.**
   - The Relay escalation draft (operator-approved, screened text, 161 flow) includes the surface brief and the action vocabulary. It also asks for an optional fenced `jarvis-actions` JSON block with the same request schema.
   - When the run finishes, Jarvis extracts at most one such block. Prose is rendered without it. The block is validated through `workspace_actions` with Relay origin and becomes **proposed** cards that the operator applies locally.
   - The Relay sandbox, its read-only advisory nature, STRICT_IP and 157/156 gates, and `private_domain_data.enabled=false` are unchanged.

## Boundaries / non-goals

- No new geometry or process authority. BLUECAD geometry remains `GeometrySpec` candidates and Process remains the 155 draft. No Monod or custom kinetics (planned under the PBR architecture specs). No agent-triggered DWSIM runs, exports, promote/archive or deletion of candidates.
- No change to Relay sandbox authority, egress or the repository default (`enabled=false`). No paid API usage by default.
- No whole-screen dumps: context is the bounded owner-derived brief only.

## Required evidence

- Focused backend tests:
  - surface-brief derivation per surface, including off-surface turns and turns with no context;
  - grant scoping per route;
  - tool admission and name normalization;
  - the constrained-output contract and leak guard;
  - each action's validate/apply/propose/refuse/stale/undo;
  - the tier policy table;
  - BLUECAD child-candidate lineage and built multi-part geometry;
  - Relay block extraction and validation, including malformed and smuggled blocks.
- Frontend build plus tests for context chip, cards and disclosure.
- Exact-head **real Chromium** acceptance on the deployed-style backend:
  - **BLUECAD, local Gemma.** Create a deterministic tube from a template; select it in the viewer; ask "create an identical tube beside it". A child candidate with two `tube_run` parts renders, its parts are selectable and their geometry is inspected (manifest bbox and part frames). Undo works. No raw JSON is visible.
  - **Process, local Gemma.** Select a stream and ask to change its pressure to 2 bar. An Apply card appears; applying creates the next draft revision; the canvas and inspector show 2 bar; prior results are stale; Undo restores the prior revision.
  - **Relay.** On real subscription Agent Relay, run the same Process or BLUECAD request through Escalate. The structured block becomes a proposed card; Apply changes the workspace locally.
  - **Unsupported.** "Add Monod kinetics to PFR-1" is answered as unsupported, with no fabricated approximation and no change.
  - Screenshots at 1280 and 1440 CSS px.
