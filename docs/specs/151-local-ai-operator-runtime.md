# 151 — Local AI operator runtime

State: **ready**. Combined definition, full contract and readiness, authorized by the maintainer's 2026-09-25 Frontier Coordinator directive that recorded real operator evidence from the Jarvis Sidecar. It repairs the human-facing local-AI path; it does not reopen 090, 091, 147 or 061b.

## Operator evidence that defines the defect

On 2026-09-25 the maintainer operated the current frontend with the backend in WSL2 and Ollama 0.34.2 native on Windows. A Sidecar message reached `thread_service.submit_interaction → run_ai_task → LocalOllamaAdapter → gemma4:12b-it-qat` and was persisted, which proves the thread/inference/persistence spine. It also exposed four defects, confirmed by fresh code inspection at `df06ddfb`:

1. **Every successful local answer is recorded as `partial_terminal`.** The local responder drops Ollama `done_reason`, so `finish_reason` is always `None` → `finish_unknown`. No `num_predict` derived from the route token budget is sent; the answer is instead sliced to `max_output_tokens × 4` characters (2 048 characters at the 512-token default) in Python, producing visible mid-sentence cutoffs while Ollama itself reported a normal stop. Thinking-capable models may spend hidden reasoning tokens that are neither separated nor accounted. The existing 061b continuation machinery is never entered because a `length` finish is never reported, and the Sidecar has no way to continue.
2. **Configured is presented as available.** `LocalOllamaAdapter.health()` reports healthy when a model name string exists; `/ai/threads/conversation-options` projects YAML presence as `configured`; the Sidecar ignores availability and offers routes that cannot answer. The real probe (`local_ai/runtime/status.py`) already exists but is not used for conversation routes.
3. **The model does not know it is Jarvis.** With no context blocks `assemble_prompt` sends the bare user prompt with no system envelope, so "funzioni jarvis?" was answered about Marvel JARVIS.
4. **The supported local runtime path requires manual networking.** The backend enforces a localhost-only local endpoint (a real security boundary). Windows-native Ollama is not reachable at WSL loopback under the default NAT networking mode, so the maintainer had to hand-build a TCP bridge and export dev variables. There is no first-class llama.cpp runtime, which the maintainer prefers for serious GGUF inference.

## Accepted capability

1. **Truthful local completion.** Local adapters send an explicit generation bound derived from the route's `max_output_tokens`, propagate the runtime finish reason (`stop`/`length`/error) into the existing token-flow terminalization, keep hidden reasoning out of the visible answer while accounting its token use when the runtime reports it, and never cut a normally stopped answer with a smaller character slice. Local conversational budgets are sized from measurement for the configured models, not fixed at 512. A genuine `length` finish uses the existing 061b bounded continuation machinery; the Sidecar shows a truncated answer as incomplete and offers the existing governed continuation where the flow is eligible. `complete` still requires an exact successful stop.
2. **Truthful availability.** Conversation routes expose separate states for configured, runtime reachable, model installed, model loaded and qualified/unqualified, with actionable reason codes, computed by the existing runtime-status owner behind a short-lived cache. The Sidecar does not offer an unreachable route as ready and explains why. The fake/test responder is visibly labelled as a test responder.
3. **Jarvis identity and capability envelope.** Every thread interaction carries a bounded, model-independent system envelope from Jarvis: what JarvisOS is, the active workspace, the current capability/availability projection from the existing capability owners, and the explicit authority statement (what the assistant may read, what it cannot execute from chat, and that it must not claim actions it did not perform). It stays data-not-instructions safe, fits the existing context budget, and does not change the canonical transcript. Model identity stays separate from Jarvis identity; the same envelope is used whichever local or policy-admitted model answers.
4. **Local runtime owner with llama.cpp.** One Jarvis local-runtime owner covers the Ollama backend and a llama.cpp `llama-server` backend behind the existing provider registry and `run_ai_task`. The llama.cpp route is `local_compute`, loopback-only, credential-free and never classified as an external provider. Jarvis can start, health-check, stop and restart one configured `llama-server` (pinned upstream build, configured GGUF path, launch arguments, context size and GPU offload) with a single shared instance rather than one per consumer; status reports backend, build, model file and digest, PID/health, context, offload, VRAM/RAM and request state where observable. Configuration uses data-root/settings, never a hard-coded maintainer path. The localhost-only boundary is not weakened; unsupported Windows↔WSL topologies produce an actionable diagnostic instead of a manual proxy.

## Non-goals and boundaries

- No frontend call to Ollama, llama.cpp or any provider; no new provider-routing stack; no removal of Ollama.
- No non-loopback local endpoints, no ad-hoc proxy as a product startup mechanism, no credentials in local runtimes.
- No large model download; the existing Windows-side GGUF files are used in place.
- No change to paid-provider defaults, budgets or egress policy.
- Hermes agent turns in the Sidecar are 152, not this slice.

## Required evidence

- Deterministic tests: finish-reason propagation for stop/length/error, generation bound sent to the runtime, no sub-budget character cut of a stopped answer, thinking separation/accounting, continuation eligibility for a real `length` finish, availability state matrix (unreachable, missing model, installed, loaded), envelope presence/bounds/injection safety, llama.cpp adapter classification as loopback `local_compute`, lifecycle start/stop/restart with a fake server.
- Real runtime: pinned llama.cpp build in WSL on the RTX 5070 Laptop GPU (or a measured justification for another placement) serving the existing Qwen3.8-27B GGUF — record build revision, GGUF SHA256, launch arguments, context, offload, VRAM/RAM, prompt and generation speed, restart.
- Real browser at exact head: a Sidecar message answered by the local llama.cpp route with `complete` state, identity-correct answer to "funzioni jarvis?", truthful unavailable-route rendering, an honestly marked truncated answer with continuation, and zero relevant console/page errors. A supported operator reaches the working state without the manual TCP bridge.

## Completion

A human can open the Sidecar, see which local models can really answer, receive complete JarvisOS-aware answers from the governed local runtime (llama.cpp or Ollama), recognise and continue a genuinely truncated answer, and restart the runtime without manual networking. Registry and PR association are reconciled after merge.
