# 159 — Sidecar conversation UX

State: **ready**. Combined definition, contract and readiness under the maintainer directive of 2026-09-30. Dependencies 152, 156 and 157 are `merged`. This slice changes presentation and operator plumbing. It adds no provider, egress, budget or authority surface.

## Fresh baseline (master `d5811792`)

- **Sidecar structure.** `useJarvisSidecar.tsx` renders every message with inline flow and persistence details. Below the transcript it adds a separate cloud escalation form, a separate cloud advice list, a separate Relay composer with its run list, and the pinned process proposals.
- **Waiting state.** Turns are synchronous, and waiting shows only "Jarvis is thinking · Ns".
- **Cloud escalation (156).** The operator must type or choose a source record reference, a rewritten safe text, an approved **derivative ID** and a **task family**; the client sends `request_id`, `source_interaction_id`, `derivative_id` and `task_family`. The client hardcodes the derivative level `S1`. No server path creates a derivative from an interaction.
- **Per-turn cost data.** The interaction read model omits provider, tokens, cost and latency, although `ai_jobs` records them.
- **Hermes tool activity.** It is recorded as `hermes.tool_result` events keyed by interaction, but no API exposes it.
- **Error reasons.** The client discards server error `detail`, so refusal reasons never reach the operator.

## Accepted capability

1. **Chat-first transcript.**
   - The default view is the operator's message and Jarvis's answer, rendered as a clean conversation.
   - Flow ids, persistence state, attempts, digests, derivative and packet ids, pricing, Relay workspace and commit data, and proposal refs are no longer inline. None of this information is deleted.
   - Cloud advice and Relay runs appear as transcript entries linked to their source turn, not as separate stacked panels.
   - Process proposals keep their approve/reject review card.
2. **Progress.**
   - While a turn, escalation or Relay run is in flight, the transcript shows one pending entry: a spinner, the elapsed time, and a concise status derived from real server state, such as `Thinking…`, `Using process draft…`, `Searching knowledge…`, `Waiting for cloud model…` or `Waiting for Relay…`.
   - Statuses map from recorded flow, tool-event, escalation and Relay states. A status is never invented, and raw internals are never shown.
3. **Metadata and info disclosure.**
   - Each assistant entry carries one subdued line: model, provider, local or cloud, elapsed time, and cost when known.
   - An info control (keyboard- and touch-accessible) reveals the full provenance/audit detail already available today, plus the tokens, cost and latency that the server now returns from existing records.
4. **One-action escalation.**
   - On a completed local turn, one `Escalate` action is enough. The server:
     - resolves that source interaction;
     - builds the cloud task text from the operator's prompt;
     - screens it with the existing deterministic floor;
     - infers `task_family` deterministically, with the operator able to override it under Advanced;
     - selects the eligible provider/model with the existing catalog policy;
     - returns a human-readable approval card: the exact text to be sent, the provider/model, the projected maximum cost and the task family.
   - One operator approval of that exact text then creates and approves the sanitized derivative server-side. The derivative is bound to the source interaction and to the approved text digest. The server then generates the request id and executes through the unchanged 156 path.
   - If the existing egress gate independently requires packet confirmation, that confirmation is shown in the same human terms.
   - S4/secret content is refused.
   - Content whose floor exceeds the cloud-eligible level cannot be sent as is. The operator edits the shown text into a cloud-safe version, and the edited text is re-screened. Nothing leaves until approved text passes the floor.
   - The operator never types or selects a request, derivative or packet id.
   - Error reasons from the server are shown in plain language.
5. **Relay through the same composer.**
   - A composer target (Jarvis / Relay agent) replaces the second Relay text box.
   - The 157 admission rules, agent allowlist, and the STRICT_IP cloud-safe attestation for Relay submission are unchanged.
   - Relay run details move behind the info control.

## Boundaries / non-goals

- STRICT_IP, sanitized-derivative authority, the 156 catalog, qualification, budget and confirmation gates, the 157 admission and sandbox, `private_domain_data.enabled=false`, and advisory-only cloud output are all unchanged.
- No semantic or LLM sanitizer. Sanitization stays operator text plus the deterministic floor.
- No automatic egress without operator approval, and no second cloud hop.
- No streaming transport rewrite. Polling of existing records is sufficient.
- No redesign of other pages.
- Paid AI stays off by default. Tests use fake providers.

## Required evidence

- **Backend tests:**
  - escalate-prepare resolves the source interaction, infers the family, honours an override, selects a candidate and returns human text with no side effect;
  - approve creates an interaction-bound derivative, egresses only the approved text, and refuses on digest drift;
  - S4 is refused and an above-floor text is refused until edited;
  - unknown or foreign interactions are refused;
  - the 156 invariants still hold;
  - the interaction read model returns provider, tokens, cost and latency;
  - activity status derives from real events.
- **Frontend tests:**
  - no inline ids or audit fields in the default message markup;
  - the metadata line and info disclosure;
  - the pending status and elapsed time;
  - escalation needs no id or family input;
  - the Relay composer target.
- **Real browser acceptance** on the canonical host:
  1. a clean chat turn on local Gemma;
  2. progress visible while waiting;
  3. a metadata line with info revealing the provenance;
  4. `Escalate` from that turn produces a human-readable approval card with no ids or family required;
  5. approve reaches the governed cloud path. Where no paid spend is authorized, this proof uses the fake provider mode and says so; any live provider call stays within the existing 156 budget/credential configuration;
  6. restricted text pauses for human-readable editing and approval;
  7. Relay submission from the composer when the gateway is enabled.
- Exact-head CI green.
