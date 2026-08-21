# Core Software Ecosystem Audit — Continuation 5 — 2026-08-20

Status: audit/intake evidence only; **not implementation authority**.  
Scope: Rizzo PII, Unsloth, DwarfStar/antirez, AgentScope 2.0, plus cross-links exposed by the audit.  
Authority boundary: `docs/specs/STATUS.md` remains the only live implementation/queue authority.

## Audit rule

JarvisOS remains `REF-000`, one candidate implementation among upstream alternatives. This document records what should later be benchmarked, wrapped, reused, replaced or rejected; it does not authorize any runtime change. The current product queue must complete first, followed by the planned frontend visual-identity phase. Any backend architecture replacement belongs to a later separately governed "puzzle" queue.

---

## 1. Rizzo PII — current `Rizzo-AI-Academy/rizzo-pii`

Source: https://github.com/Rizzo-AI-Academy/rizzo-pii  
Observed current main: 2026-08-20 audit; root repository metadata reports MIT.  
Evidence: code/tree/changelog inspected, not README-only.

### What it actually is

The useful architecture is not merely a 0.3B Italian PII classifier. The system is a **local egress-transform boundary**:

1. detect sensitive spans locally;
2. combine probabilistic token classification with deterministic regex/checksum recognizers;
3. replace values with stable typed placeholders;
4. keep the reversible placeholder dictionary locally;
5. send only pseudonymized content to a remote frontier model;
6. restore values locally on the response path.

The current source separates app, detectors, data pipeline, inspection and training. `src/app/detectors.py` intentionally avoids importing the heavy model/PDF stack so deterministic detection is independently testable.

### Strong reusable patterns

#### A. Egress transformation must be a first-class pipeline stage

For JarvisOS, privacy cannot be a prompt instruction such as "do not send secrets". A future egress path should support a deterministic sequence such as:

`candidate payload -> classification -> deterministic secret/PII detectors -> transform/redact/pseudonymize -> policy decision -> provider adapter`

The provider adapter should never receive the unprocessed payload when the policy requires local transformation.

#### B. Probabilistic detector plus deterministic verifier

Rizzo PII uses regex/checksum validation for identifiers whose validity can be mechanically checked. This suggests a general Jarvis principle:

> Whenever a domain invariant can be proven deterministically, the verifier should outrank a model guess.

The same principle can cover secrets, engineering units, file paths, IDs, checksums, structured records and solver outputs.

#### C. Safety-biased span handling

The changelog records a real failure where token boundaries left reconstructable PII fragments despite showing a placeholder. The fix expands touched spans to word boundaries and prefers masking too much to leaking part of an identifier. Jarvis egress transforms should likewise define an explicit conservative failure policy, not merely an accuracy target.

#### D. Reversible state must have lifecycle identity

A prior bug allowed a PII map to survive UI "clear", then re-identify a later session with stale values. This is directly relevant to Jarvis caches/memory/tool state:

- session-bound reversible mappings need explicit session identity;
- UI reset must clear the authoritative backing store, not only hide state;
- stale-state reuse should fail closed;
- restore operations must bind to the exact map/version that produced the anonymized payload.

#### E. Offline/readiness boundary

The Docker path bakes the model into the image, sets HF/Transformers offline mode, binds localhost externally, and exposes a readiness health check that does not itself require inference. This is a good reference for local Jarvis workers.

#### F. Performance regressions are correctness-adjacent

The overlap merge path was previously quadratic and became extremely slow on long documents. The fix was validated against tens of thousands of randomized and constructed cases with zero output differences. For security/privacy transforms, performance optimization should require behavioral equivalence evidence.

### Licensing boundary

Root source is MIT, but binary/distribution obligations can differ because bundled third-party components have their own licenses. Do not infer the shipping license from the root SPDX label alone. Exact artifact/SBOM review remains mandatory.

### Candidate disposition

**Grade: S- / CANDIDATE as architecture and optional local privacy worker.**

Do not make Rizzo PII the canonical Jarvis policy engine. Instead evaluate:

- direct local detector adapter for Italian/general PII;
- the reversible egress-transform pattern;
- deterministic detector/verifier precedence;
- session-bound transformation manifests.

---

## 2. Unsloth — current `unslothai/unsloth`

Source: https://github.com/unslothai/unsloth  
Observed current main: active on 2026-08-20.  
Evidence: root/package/studio trees inspected.

### What it has become

Unsloth is no longer usefully described as only a fast LoRA trainer. The current repository spans:

- model running and training;
- hardware/backend detection;
- quantization and model-specific optimizations;
- dataset preparation;
- local OpenAI-compatible serving;
- Desktop/Studio UI;
- agent integration via `unsloth start`;
- Claude Code, Codex, Hermes, OpenCode/OpenClaw integration;
- local model use as a subagent while the primary client keeps another model;
- SFT, LoRA/QLoRA, full fine-tuning, RL/GRPO/DPO and export paths.

The package tree contains dedicated GPU initialization, device routing, compressed quantization, chat templates, data preparation, kernels and model integrations. It therefore belongs in both the **training backend bake-off** and the **local model runtime/adapter bake-off**.

### Strong reusable patterns

#### A. Client/harness and model backend are separable

`unsloth start ... --as-subagent` reinforces a pattern already observed in SERA: a mature coding client can remain the user-facing harness while a different local model serves as a worker/subagent.

Jarvis should therefore avoid hard-coding:

`agent implementation == provider == model == inference runtime`.

Use independent contracts for agent runtime, model endpoint, execution environment and authority.

#### B. Hardware qualification belongs below Jarvis authority

Unsloth owns a large compatibility matrix across CPU, Apple, NVIDIA, AMD, Intel, Vulkan and different training/inference stacks. Jarvis should not recreate this hardware dispatch logic unless a benchmark proves necessary. Prefer an adapter that records the resolved backend/version/capability in an execution manifest.

#### C. Local by default; remote exposure explicit

Studio is localhost-oriented by default, while remote access is a separate opt-in path. The secure-tunnel path is described as fail-closed if the tunnel cannot start. This is a useful deployment pattern for Jarvis local services.

### Licensing boundary is NOT uniform

This repository requires file/subtree-level license treatment:

- repository metadata/root reports Apache-2.0;
- `studio/` contains `LICENSE.AGPL-3.0`;
- the wider Unsloth ecosystem includes differently licensed components such as `unsloth-zoo`.

Therefore "Unsloth is Apache" is insufficient for integration decisions. Exact package/file boundaries and transitive dependencies must be reviewed before direct reuse.

### Candidate disposition

**Grade: S / CANDIDATE for future specialist training and local serving; PARKED for immediate product work.**

When the later backend puzzle phase is authorized, benchmark Unsloth against the existing candidate training chain (DataTrove + Axolotl/TRL/PEFT and SERA-style trajectory generation). A simpler Unsloth-led path should be allowed to replace multiple bespoke layers if it wins on reproducibility, hardware support, model coverage and quality gates.

Do not allow the training/runtime backend to own Jarvis policy, canonical memory or engineering identity.

---

## 3. DwarfStar — `antirez/ds4`

Source: https://github.com/antirez/ds4  
License observed: MIT.  
Evidence: README, `AGENT.md`, release-QA document and repository layout inspected.

### What it actually demonstrates

DwarfStar deliberately rejects the "universal runtime" goal. It is a small native engine specialized for a short list of strong open-weight models and hardware paths. Current scope includes DeepSeek V4 Flash/PRO and GLM 5.2 across Metal, CUDA and ROCm, with SSD streaming, distributed execution, server APIs, tool calls, agent runtime and KV state.

The important lesson is not "replace llama.cpp with DwarfStar". It is that **specialized runtimes can beat universal abstractions if they are qualified as replaceable adapters rather than made architectural authorities**.

### Strong reusable patterns

#### A. Narrow public API, deep implementation hidden

`AGENT.md` explicitly says CLI/server code should not know tensor internals. This matches the desired Jarvis adapter boundary: the rest of Jarvis should consume declared capabilities and manifests, not internal model/runtime details.

#### B. Correctness before speed

The project explicitly rejects faster paths with unexplained attention, KV-cache or logits drift. Performance changes must pass golden/vector and continuation-quality gates.

#### C. Quality matrix, not one generic CI status

`QA_BEFORE_RELEASES.md` records hardware, exact model artifact, context and flags and exercises historically fragile paths: loaders, API parsers, distributed snapshots, disk KV, malformed files, cache restore, tool/reasoning state machines and backend-specific execution.

Jarvis should copy this principle for every backend adapter:

`adapter + version + platform + capability + artifact -> qualification evidence`.

A capability should be advertised only if that tuple has passed the corresponding gate.

#### D. Reject unsupported combinations before execution

DwarfStar explicitly rejects model/quant/runtime combinations it has not qualified. This is preferable to optimistic fallback. Jarvis provider/runtime selection should similarly reject unsupported combinations before expensive or destructive work.

#### E. Authoritative verifier for speculative acceleration

DSpark proposals are only committed after target-model verification; strict/quality paths remain available. This generalizes beyond token generation:

> speculative/fast workers may propose, but a designated authoritative verifier decides what becomes committed state.

This aligns strongly with Jarvis deterministic verification and future multi-agent designs.

#### F. Disk checkpoints and long-running sessions are product concerns

DwarfStar treats live KV reuse and disk KV checkpoints as core requirements for long local sessions, with corruption/restore tests. Jarvis runtime adapters should expose resumability explicitly rather than hide it inside chat history.

### Serendipitous Unsloth link

DwarfStar currently documents an Unsloth-produced GLM quant as one supported artifact. This is useful evidence that the training/quantization ecosystem and native inference runtime need not be the same project; Jarvis should preserve that composability.

### Candidate disposition

**Grade: S- as local-runtime/QA reference; A candidate adapter for qualified supported models.**

Do not choose it globally over llama.cpp/vLLM/Unsloth/Ollama. Build a hardware/model qualification matrix and allow multiple runtimes to coexist behind one Jarvis model-runtime contract.

---

## 4. AgentScope 2.0 — `agentscope-ai/agentscope`

Source: https://github.com/agentscope-ai/agentscope  
License observed: Apache-2.0.  
Evidence: current README and source package structure inspected.

### Current architecture is materially relevant

AgentScope 2.0 now exposes separate subsystems for agent, event, credential, MCP, middleware, model, memory, workspace/sandbox and serving. Current documented capabilities include:

- unified event bus;
- permission/HITL layer;
- composable middleware around reasoning/acting/model/tool/permission/context paths;
- switchable memory backends;
- multiple sandbox/workspace backends;
- MCP and skill hubs;
- multi-tenant and multi-session service isolation;
- persistence and scheduling;
- agent teams.

This makes AgentScope a real candidate in the generic agent-runtime bake-off, not just a conceptual multi-agent framework.

### What to compare later

Against Codex, Kimi, Pydantic AI, Microsoft Agent Framework, Hermes and OpenAI Agents SDK, benchmark:

- session/state ownership;
- interruption/resume semantics;
- tool identity and permission binding;
- middleware determinism;
- event schema stability;
- workspace isolation;
- provider neutrality;
- Windows/local operation;
- checkpoint/recovery;
- observability;
- dependency footprint;
- authority escape hatches.

### Candidate disposition

**Grade: S- / CANDIDATE for runtime bake-off.**

Even if AgentScope wins generic runtime duties, Jarvis should retain canonical engineering identity, authority/policy, evidence/provenance and product-specific state above it.

---

## 5. Consolidated architectural implications from this wave

### 5.1 Do not build one universal backend

The evidence increasingly favors a small authoritative Jarvis kernel plus replaceable backend adapters:

- agent runtime adapters;
- model/inference adapters;
- sandbox/execution adapters;
- code-intelligence adapters;
- memory/index adapters;
- training adapters.

### 5.2 Egress is an explicit trusted boundary

A future canonical path should resemble:

`canonical object -> render/minimize -> sensitive-data scan -> reversible transform if required -> policy -> provider/runtime -> response scan -> controlled restore -> evidence record`.

### 5.3 Backend capability claims require qualification evidence

A provider/runtime must not simply declare `supports_tool_calls=true` or `supports_long_context=true`. Capability truth should be bound to exact implementation/model/platform/version evidence and be revocable when qualification expires.

### 5.4 Training is not runtime authority

Unsloth/SERA may eventually own large parts of data preparation/fine-tuning; DwarfStar/llama.cpp/vLLM may own inference; Claude/Codex/Cline/AgentScope may own agent loops. None should thereby acquire permission to mutate Jarvis canonical state.

---

## 6. Immediate follow-up queue for the audit only

1. inspect Rizzo sibling projects only where they expose reusable privacy/agent/runtime patterns;
2. inspect exact Unsloth Start/backend boundaries and license map before any direct-integration recommendation;
3. compare DwarfStar quality/qualification approach with llama.cpp/vLLM/Unsloth runtime qualification;
4. include AgentScope in the later exact `AgentRuntime` bake-off;
5. reconcile this wave into the canonical candidate register with a safe hunk-level edit once available;
6. do **not** convert any finding into the current product queue.
