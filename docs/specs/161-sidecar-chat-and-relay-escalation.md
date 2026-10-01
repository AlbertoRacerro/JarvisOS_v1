# 161 — Sidecar chat shell and Relay-default escalation

State: **ready**. This spec combines definition, contract and readiness under the maintainer human-acceptance directive of 2026-10-01 (devctx `L20261001092537-96de`). Dependencies 156, 157 and 159 are `merged`.

## Decomposition of the 2026-10-01 directive (161–165)

The directive's findings map onto four owners. Shared surfaces are serialized so that no two lanes write the same file.

| Spec | Owner surfaces | Order |
| --- | --- | --- |
| 161 (this) | App shell (`Layout`, `ContextualSidecar`, `Rail`, shell CSS), `useJarvisSidecar`, the new shared `ContextMenu` primitive, Relay gateway escalation | First, because it owns the shell and the menu primitive. |
| 162 | Process draft backend, `ProcessDraftEditor`, `ProcessStage` | Implemented in parallel; merges after 161 because it consumes `ContextMenu`. |
| 163 | BLUECAD workbench, `ModelStage`, BLUECAD export/serving | Merges after 161 because it relies on the shell navigator reopen affordance. |
| 164 | Coding Runtime page and a read-only control-room projection | Independent. |
| 165 | Bambu print handoff | `planned` follow-up only. |

**Why Escalate lives here and not in a Relay-only spec:** the Escalate action, its context menu and the new transcript turns all live in `useJarvisSidecar`. Splitting them would put two writers on one file.

## Fresh evidence (master `fc34a316`)

- **Shell.**
  - Final routes have no TopBar. Once the Sidecar or the navigator is closed, nothing on screen can reopen it.
  - The Sidecar is 300 px wide and stacks a `Jarvis & Properties` header, two tabs and a Properties pane that takes half its height.
  - Sidecar text renders at 7.5 px.
  - The rail is 170 px wide.
  - Several pages embed Jarvis in their own fixed columns (310–360 px).
- **Sidecar.**
  - The responder and conversation selects, a readiness paragraph, a context disclosure and the welcome copy all sit above the transcript.
  - The composer carries a `Send to` select.
  - Cloud and Relay results render as nested sections inside the source turn.
  - Metadata shows raw model ids such as `gemma-4-12b-it-qat-q4_0`.
- **Escalation.**
  - `Escalate` always prepares the 156 metered-provider path. With the safe defaults (paid AI off, budget 0) it ends at `provider_gate_blocked`.
  - On the operator host the Relay gateway is disabled (`enabled=false`; the env override is unset).
  - Relay is installed (agent-relay 0.7.7, with authenticated `claude` and `codex` CLIs).
  - Relay runs record no model and no source turn.

## Accepted capability

1. **Shell proportions and reopen.**
   - One shared Jarvis width token is used by the shell Sidecar and by in-page Jarvis columns. It gives about 15% more width at ordinary desktop sizes (about 345 px at 1440 CSS px) and is clamped responsively.
   - The rail gets narrower without hiding labels.
   - When a shell Sidecar or navigator region has content but is closed, a small persistent, labelled, keyboard-reachable affordance on the current screen reopens it.
   - There is no horizontal overflow at 1024, 1280, 1440 or 1920 px.
2. **Chat-first Sidecar.**
   - The header reads `Jarvis · <status> · New conversation · Close`. Status detail moves into a tooltip or accessible description.
   - Properties stop reserving permanent Sidecar space. They remain reachable as a compact secondary view where a route supplies them.
   - The transcript gets the freed height. Each user message and each Jarvis answer is a separate turn, with actions under the answer.
   - Cloud and Relay answers render as subsequent Jarvis turns, not nested panels.
   - The composer sits at the bottom. Responder choice, Relay-agent targeting and project context become compact secondary controls.
   - Conversation history is low-priority, behind a disclosure.
   - Onboarding and redundant labels are removed.
   - Readable text sizes are restored.
3. **Human model names.**
   - Normal metadata shows concise names derived from the recorded model id, for example `Gemma 4 12B`, `Qwen 3.5 4B`, `GPT-6 Luna`, `Claude Opus 5.5`.
   - Unknown ids are humanised, never invented.
   - Exact model, provider, route and run provenance stay in the existing info disclosure.
4. **Relay-default escalation.**
   - A left click on `Escalate` prepares a Relay escalation of the source turn.
   - A context menu, also reachable by keyboard through a menu button, offers `Escalate with Relay` and `Escalate with API key…`. The second option is the unchanged 156/159 flow.
   - **Relay preparation and approval:**
     - The server resolves the source interaction.
     - It screens the operator text with the deterministic floor. S4 is refused, and above-cloud-safe text requires editing and re-screening.
     - It returns the exact text, the agent and its display model, and states that this is subscription-backed with no API charge.
     - One approval of that exact text is the cloud-safe attestation. The server re-screens the text and binds its digest.
     - The server then submits a Relay run linked to the source turn, with an advisory-answer framing and the configured explicit model.
   - Relay availability is truthful. A disabled gateway, missing login or failed run is reported in plain language.
   - Relay failure never falls back to an API provider. The operator may deliberately choose `Escalate with API key…`.
   - Relay turns are never shown as metered cost.

## Boundaries / non-goals

- The following are unchanged:
  - STRICT_IP, the deterministic floor, the 157 admission rules, agent allowlist and sandbox, and `private_domain_data.enabled=false`;
  - the 156 catalog, budget, credential and confirmation gates;
  - advisory-only cloud output;
  - no automatic egress without operator approval;
  - no second cloud hop.
- SPEC 156 is not deleted or weakened. The API path stays fully available as the explicit alternative.
- The repository default `configs/relay_gateway.json` stays `enabled=false` (safe default). The operator host enables the gateway through its private launcher configuration.
- There are no streaming or transport rewrites, no new provider, no new credential store, and no Hermes changes.
- The context menu is a progressive-disclosure primitive. Rare actions use it, primary actions stay visible, and every menu action has a keyboard and non-pointer route.

## Required evidence

- **Backend tests:**
  - Relay escalation prepare is side-effect free, resolves the source turn and screens it: S4 refused, above-floor edit required, foreign or unknown interaction refused, gateway-disabled state reported.
  - Approval refuses digest drift, records the run with the source interaction and model, applies the advisory framing, and never touches 156 provider or budget state.
  - The existing 156/157 tests stay green.
- **Frontend tests:**
  - The header has no redundant headings.
  - Turns are separate.
  - Model display names map correctly.
  - The Escalate default plus the context-menu alternatives are keyboard reachable.
  - The reopen affordance works.
- **Real browser evidence on the canonical host:**
  - screenshots at 1280, 1440 and 1920 px with no horizontal overflow;
  - a real local Gemma turn;
  - `Escalate` (left click) produces the Relay approval card, and approval returns a real Relay answer as a new Jarvis turn with the human model name;
  - `Escalate with API key…` still reaches the 156 gate;
  - close and reopen of Jarvis on the same screen.
- Exact-head CI green.
