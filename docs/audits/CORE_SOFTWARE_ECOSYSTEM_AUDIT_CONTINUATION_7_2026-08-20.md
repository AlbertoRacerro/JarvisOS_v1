# Core Software Ecosystem Audit — Continuation 7 — 2026-08-20

Status: audit/intake only; **not implementation authority**.  
Purpose: close the broad runtime/control-plane enumeration with Pi, OpenCode, Goose, NanoClaw and LocalAI, then stop adding frameworks unless a later comparison exposes a missing architectural slot.

---

## 1. Pi Agent Harness — current `earendil-works/pi`

Source: https://github.com/earendil-works/pi  
Historical note: `badlogic/pi-mono` now redirects to this repository.  
License observed: MIT.

### Current decomposition

Pi is already split into independent packages:

- coding-agent CLI;
- agent core with tool calling and state management;
- unified multi-provider model API;
- vendor-neutral telemetry contracts, adapter and conformance tests;
- TUI.

This is a useful proof that provider abstraction, generic agent state and UI need not live in one monolith.

### Security honesty is a feature

Pi explicitly states that it does **not** provide a built-in permission system and otherwise executes with the privileges of the launching user/process. For stronger boundaries it recommends external containment such as Gondolin micro-VM, Docker or OpenShell.

Jarvis should prefer this explicit contract to a framework that appears safe but silently inherits full host authority. If Pi is ever used, outer Jarvis policy/sandboxing remains mandatory.

### Supply-chain patterns worth retaining

Pi documents unusually concrete npm hardening:

- exact direct-dependency pins;
- minimum package release age;
- lockfile as dependency ground truth;
- explicit guard against accidental lockfile updates;
- shrinkwrap for transitive dependencies in the published CLI;
- install paths using `--ignore-scripts` where possible;
- lifecycle-script allowlist;
- isolated release smoke installs;
- npm audit and signature checks;
- versioned release source archives with SHA256 sums and offline provider-model data.

This belongs in the future plugin/skill/runtime admission design.

### Disposition

**Grade: S- / CANDIDATE in AgentRuntime bake-off.**

High value for clean modularity, provider abstraction, telemetry/conformance and supply-chain practice. It does not replace Jarvis authority/security.

---

## 2. OpenCode — current `anomalyco/opencode`

Source: https://github.com/anomalyco/opencode  
Default branch observed: `dev`.  
License observed: MIT.

### Current relevant surface

OpenCode is a mature cross-platform coding agent with terminal and desktop surfaces. The current README exposes distinct built-in agents:

- `build`: full-access development agent;
- `plan`: read-only analysis/exploration agent, denying edits and asking before bash;
- `general`: subagent for complex searches/multistep tasks.

The important architectural evidence is again that **research/planning authority can be structurally narrower than implementation authority**.

OpenCode also belongs in the client/runtime bake-off because it is large, active, cross-platform and provider-oriented. Its exact LSP/client-server internals should be compared only when that slot is actively selected; the broad inventory no longer needs another round of feature enumeration.

### Disposition

**Grade: S- / CANDIDATE in coding-client/AgentRuntime bake-off.**

Do not adopt only because of ecosystem size. Compare exact state/resume semantics, tool identity, permission binding, server/client separation, local-model compatibility and Windows behavior against Codex/Kimi/Cline/Pi/Goose/AgentScope.

---

## 3. Goose — current `aaif-goose/goose`

Source: https://github.com/aaif-goose/goose  
Governance: Agentic AI Foundation / Linux Foundation.  
License observed: Apache-2.0.

### Current relevant surface

Goose provides:

- native desktop application;
- CLI;
- API embedding surface;
- Rust implementation;
- many model providers;
- ACP-based provider/subscription connectivity;
- 70+ MCP extensions;
- custom distributions with preconfigured providers/extensions/branding.

This makes Goose a serious cross-platform general-agent candidate and an especially useful reference for the **desktop + runtime + protocol boundary**.

### Disposition

**Grade: S- / CANDIDATE in AgentRuntime/desktop-runtime bake-off.**

The Linux Foundation governance and permissive license are positives, but Jarvis-specific authority/evidence/engineering semantics should remain above Goose if it wins generic runtime duties.

---

## 4. NanoClaw — current `nanocoai/nanoclaw`

Source: https://github.com/nanocoai/nanoclaw  
License observed: MIT.  
Evidence: repository metadata, security model and `src/container-runner.ts` inspected.

### Primary value is security/lifecycle architecture, not the agent loop

NanoClaw treats OS/container isolation as the primary boundary:

- explicit mounts only;
- non-root execution;
- per-session containers;
- no project root mount;
- configuration files overlaid read-only;
- additional mounts denied unless an external allowlist permits them;
- symlinks resolved before path authorization;
- dangerous credential/config patterns blocked;
- read-write granted only when both request and allowlist permit it.

The implementation also keeps session-driver/runtime-specific lifecycle behind a seam while host-side composition owns mounts, environment and lifecycle policy.

### Credential isolation is stronger than environment redaction

The documented OneCLI pattern keeps real credentials outside the agent container and injects them at a gateway per outbound request. This is a materially stronger boundary than merely setting/unsetting environment variables.

For Jarvis, this suggests a future option:

`worker -> credential-less request -> trusted egress gateway -> policy/secret injection -> destination`

rather than handing raw API keys to every agent process.

### Egress lockdown is network-enforced and fail-closed

NanoClaw can place agents on an internal Docker network with no direct internet route, forcing traffic through the trusted gateway. If lockdown cannot be established, spawn fails instead of silently opening egress.

This is directly aligned with the three-plane Jarvis security model:

- capability authority;
- information-flow/egress authority;
- state-commit authority.

### Important caveats

- Egress lockdown is opt-in, not default.
- CPU and memory limits are also opt-in/unbounded by default.
- The in-repo security document warns that documentation can drift and points to source (`buildMounts`) as truth.

These caveats reinforce the need for Jarvis to qualify **effective runtime configuration**, not trust a framework name or README claim.

### Lifecycle patterns from source

`container-runner.ts` includes:

- in-flight wake deduplication to prevent duplicate sessions/replies;
- explicit composition of a typed session spec before driver preparation;
- terminal handlers armed before start to avoid startup race loss;
- single-shot finalization;
- startup reconciliation that adopts still-valid sessions rather than blindly killing all survivors;
- stale heartbeat cleanup before spawn.

These are highly reusable reliability patterns for long-running Jarvis workers.

### Disposition

**Grade: S / CANDIDATE as sandbox/credential/worker-lifecycle reference.**

Jarvis should compare NanoClaw's patterns primarily against OpenShell/container/WASM designs, not as a replacement for canonical Jarvis state or the full agent runtime.

---

## 5. LocalAI — current `mudler/LocalAI`

Source: https://github.com/mudler/LocalAI  
License observed: MIT.

### Current architecture is a model/control plane, not just an OpenAI-compatible server

The current project describes itself as a small core with backends pulled on demand. Backends wrap engines such as llama.cpp, vLLM, MLX, whisper.cpp and diffusion/voice engines behind common APIs.

Current documented surface includes:

- OpenAI/Anthropic/ElevenLabs-compatible APIs;
- LLM, vision, voice, image and video backends;
- NVIDIA/AMD/Intel/Apple/Vulkan/CPU paths;
- multi-user auth, quotas and roles;
- built-in agents, RAG, MCP and skills;
- distributed mode and hardware-aware routing;
- in-UI fine-tuning/quantization;
- prompt caching;
- on-demand backend images;
- backend image signing/integrity work in recent releases.

### Architectural lesson: Jarvis should not own every inference engine

LocalAI is direct evidence for the desired adapter principle:

`small control plane -> backend contract -> specialized runtime images`

A future Jarvis model plane could consume LocalAI as one adapter/control-plane option rather than integrating llama.cpp/vLLM/voice/image runtimes individually everywhere.

### But LocalAI is too broad to become Jarvis authority

Its growing agent/RAG/MCP/UI/control-plane scope overlaps with Jarvis product responsibilities. If adopted, the boundary must remain strict:

- LocalAI may own model/backend lifecycle and hardware routing;
- Jarvis owns policy, canonical state, engineering identity, egress classification and verification.

The fact that LocalAI itself can run agents should not cause nested/competing authority planes by accident.

### Disposition

**Grade: S / CANDIDATE in Model Runtime/Provider control-plane bake-off.**

Benchmark LocalAI against direct llama.cpp/vLLM/Unsloth/DwarfStar/Ollama adapters for footprint, Windows operation, model coverage, deterministic qualification, startup latency and control complexity.

---

## 6. Saturation conclusion for broad runtime enumeration

This wave did **not** reveal a missing top-level architectural slot. Instead it supplied stronger competitors and implementation evidence for slots already identified:

- Pi/OpenCode/Goose -> `AgentRuntime` / coding client;
- NanoClaw -> `Execution/Sandbox` + credential/egress boundary + worker lifecycle;
- LocalAI -> `Model Runtime/Provider` control plane.

Therefore the audit should now stop open-ended framework enumeration unless a later exact comparison exposes a genuine missing capability.

The next useful work is synthesis, not adding dozens more names.

---

## 7. Broad audit coverage is now sufficient for a strategic comparison

The candidate map now has multiple serious references for each major backend-puzzle slot:

1. Authority/Event Kernel — Jarvis current code, ESAA/event sourcing, Agent Governance Toolkit, policy/capability research.
2. AgentRuntime — Codex, Kimi, AgentScope, Microsoft Agent Framework, Pydantic AI, Hermes, Pi, OpenCode, Goose, Cline/OpenAI Agents.
3. Tool/Capability Gateway — Gemini policy, Tauri ACL, OpenAI tool identity, Progent/capability research, Hermes/MCP.
4. Execution/Sandbox — OpenShell, NanoClaw/container patterns, VS Code extension host, Extism/Wasmtime, generic containers.
5. Model Runtime/Provider — llama.cpp, vLLM, Unsloth, DwarfStar, LocalAI, Ollama.
6. Code Intelligence — Serena/LSP, Tree-sitter, editor/client references.
7. Canonical Memory/Evidence — Jarvis/Event-sourced candidate architecture.
8. Derived Memory/Index — Letta, Graphiti, Mem0, Cognee, A-MEM/MemGPT taxonomy.
9. Egress/Privacy — Rizzo PII, NanoClaw gateway/forced proxy, tracked-capability/information-flow research.
10. Observability/Evaluation — OpenTelemetry GenAI, Harbor/Verifiers, ToolSandbox, Pi/ADK/LangGraph conformance, DwarfStar qualification matrices.
11. Training/Specialization — SERA, Unsloth, DataTrove/Axolotl/TRL/PEFT, Agent Lightning architecture.
12. Desktop/Frontend IPC — Tauri ACL, Goose, ACP/client-server references.

This is enough breadth to begin the later subsystem-by-subsystem `KEEP / REPLACE / WRAP / HYBRID / DELETE / PARK` strategy.

Hard sequencing remains unchanged: **finish current queue -> frontend visual identity -> only then implement the backend puzzle queue**.
