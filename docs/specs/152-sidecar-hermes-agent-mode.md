# 152 — Sidecar Hermes agent mode

State: **ready**. Combined definition, full contract and readiness, authorized by the maintainer's 2026-09-25 Frontier Coordinator directive. It exposes the merged 146 Hermes runtime through the existing Jarvis Sidecar; it does not reopen 146 or create another chat product.

## Fresh baseline

At `df06ddfb` the qualified Hermes 0.21.4 worker (`d337b736…`) runs under `bwrap --unshare-net` with a relay that sends every model call through `run_ai_task`, a grant-checked broker exposing only `jarvis.context_preview`, and `HermesSupervisor.turn()` persisting into `ai_thread_interactions`. No product code calls `turn()`, the application supervisor has no route mapping so relayed inference falls back to `local:fake`, and the 146 smoke used a deterministic inference stub. The Sidecar therefore cannot reach Hermes, and no real-model Hermes turn has been demonstrated.

Accepted authority already fixes the seam: 111 places Hermes as an internal adapter behind the Jarvis thread/context service; ADR-060 and the 146 packet keep canonical transcripts, credentials, routing, budget, egress and promotion in Jarvis with `jarvis_thread_id ↔ hermes_session_id ↔ profile` mapping.

## Accepted capability

1. **One surface, two modes.** The existing Sidecar conversation route selector offers a Hermes agent mode next to direct model routes when the Hermes runtime is actually available, with truthful unavailable reasons otherwise. A Hermes turn is submitted through the existing thread interaction path and keeps its reservation, idempotency, request digest and captured-interaction semantics; there is no second transcript, conversation store or visible Hermes shell.
2. **Governed inference and bounded tools.** Hermes relay inference uses an explicitly selected Jarvis route (the 151 local runtime by default), never `local:fake` by accident, never a credential in the worker. The broker adds the 150 read-only Second Brain navigation tool alongside context preview under server-side grants scoped to the thread's workspace, with bounds and authoritative reread. Tool calls and results are recorded as evidence. Hermes gains no write, execution, filesystem, network or promotion authority.
3. **Operational lifecycle.** The supervisor starts one worker on demand for a thread session, reuses it, reports status/generation to the Sidecar, stops idle workers, and recovers from worker loss without losing the canonical transcript. Hermes shares the single local inference runtime instead of launching its own model.

## Non-goals

- No Hermes fork, no new Hermes tools beyond read/context navigation, no Hermes-owned memory as project truth, no engineering mutation from agent text.
- No external-provider Hermes route unless existing egress policy admits it explicitly.

## Required evidence

- Deterministic tests: route projection/availability, thread-path reservation and idempotency for agent turns, route selection for relay inference, grant-scoped retrieval tool with workspace isolation and bounds, worker loss recovery.
- Real runtime: a real Hermes worker under the pinned revision and isolation completes at least one Sidecar-initiated turn with real local-model inference (the 151 llama.cpp Qwen3.8 route where qualified), including a Second Brain tool call, with durable flow/thread evidence and a clean stop/restart.
- Jarvis-specific qualification of the local agent model: identity, instruction following, tool selection and arguments, multi-step tool use, abstention when a capability is unavailable, no invented tool outcomes, latency and memory pressure. A model that chats well but fails tool loops is recorded as unqualified for agent mode.
- Real browser at exact head: agent mode selected in the existing Sidecar, a grounded answer with evidence refs, truthful unavailable state when the worker/runtime is down.

## Completion

A human can choose Jarvis agent mode in the same Sidecar, get a Hermes-orchestrated answer grounded through governed Second Brain navigation and local inference, and see it in the same canonical thread. Registry and PR association are reconciled after merge.
