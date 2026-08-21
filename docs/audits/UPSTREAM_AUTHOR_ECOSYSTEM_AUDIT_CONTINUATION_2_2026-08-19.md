# Upstream Author Ecosystem Audit — Continuation 2 — 2026-08-19

Status: audit/reference document only. No implementation authorization is implied.

This file continues `UPSTREAM_AUTHOR_ECOSYSTEM_AUDIT_CONTINUATION_2026-08-19.md` and records the code-first findings produced after commit `673b034441fd29bb9157289fed3c4da067a9ffea`.

Standing reuse rule remains unchanged: permissive/commercially-compatible software should be integrated or vendored when technically appropriate rather than recreated by default; model/data licenses are tracked separately from source-code licenses; permissive licensing never makes a component a security boundary by itself.

## 1. `anomalyco/opencode` — A component mine / worker candidate, MIT

OpenCode has a materially stronger permission engine than small coding-agent hooks: rules can resolve to `allow`, `deny`, or `ask`; an approval request is tied to session/tool-call state; responses support once/always/reject. Unknown permissions and empty rule sets fall back to asking.

Important limitation: matching uses ordered rules and the last matching rule wins. A later broad wildcard allow can therefore weaken an earlier specific deny. This is suitable for worker-level policy but not for Jarvis root authority, where higher-level restrictions must remain monotonic/non-weakenable.

### High-value LSP subsystem

OpenCode's LSP implementation is substantially more general than a TypeScript-only plugin:

- multiple language servers selected by extension/root;
- concurrent spawn deduplication;
- lifecycle cleanup;
- diagnostics;
- hover;
- definition/references/implementation;
- workspace/document symbols;
- call hierarchy.

Candidate: extract or integrate as a Jarvis/Cline/OpenCode code-intelligence service if dependency boundaries are acceptable.

### Snapshot race lesson

OpenCode's tests document a real race where a very fast tool can mutate the repository before an asynchronous start-step snapshot is captured, producing identical before/after state. Jarvis checkpoints must therefore be captured synchronously in the execution wrapper before any side effect, not inferred from later telemetry events.

## 2. `anomalyco/browser-control` — S TransactionalBrowser candidate, MIT

This currently outranks `vercel-labs/agent-browser` for authenticated/transactional browser control.

Useful features:

- controls an existing logged-in Chromium profile;
- typed same-origin HTTP requests;
- redirects blocked for the typed request path;
- bounded responses and mutation-safe retry behavior;
- sensitive-output redaction;
- captured network requests with secret references rather than blindly exposing credentials;
- explicit human handoff for CAPTCHA, 2FA and payment flows;
- local trusted-code driver model, so Jarvis/OpenShell remains the hard authority/sandbox.

### Code-first stale-ref behavior

The implementation is more fail-closed than `agent-browser`:

- navigation clears the snapshot/ref registry;
- navigation occurring during snapshot capture makes the snapshot fail;
- `ref()` rejects an unknown/stale ref and checks current page/URL state;
- it reconstructs a locator from the selector captured at snapshot and intersects the captured ARIA role, instead of intentionally searching for a semantically-similar replacement node.

Jarvis should still add its own `snapshot_id/page_epoch` for sensitive mutations, including dynamic DOM changes that do not trigger navigation.

### Decision

Preferred candidate split:

- `browser-control`: authenticated/transactional browser worker;
- Vercel `agent-browser`: still useful alternative/general worker and plugin ecosystem;
- Jarvis/AIRI-style preflight: final sensitive-action observation binding;
- OpenShell: OS/network boundary.

## 3. `anomalyco/terminal-control` — A+/S terminal/TUI worker, MIT

This is not merely a background shell. It exposes real PTY/session control with:

- persistent terminal sessions;
- wait-for-visible-state semantics instead of sleep-based automation;
- PNG/text/SVG evidence capture;
- semantic snapshots;
- stable pane identifiers;
- multi-pane workspaces;
- MCP and TypeScript test clients.

Candidate: terminal/TUI automation and testing beneath Jarvis authority + OpenShell. It complements rather than duplicates Cline's background-terminal plugin.

## 4. anomalyco benchmark repositories — REFERENCE_ONLY for now

`agents-benchmark` and `opencode-bench` did not expose a clear root software license during this audit.

`opencode-bench` is methodologically interesting: real baseline/production commits, multiple isolated episodes, patch/diff evaluation, three LLM judges and a variance/disagreement penalty. The project itself points toward deterministic analysis as a desirable complement.

Use the disagreement/variance idea as benchmark reference only. Harbor/TB-Science remains the stronger Jarvis engineering benchmark foundation because it can use deterministic artifacts/verifiers rather than relying primarily on judges.

## 5. Hugging Face ecosystem

### `huggingface/smolagents` — A / optional component, Apache-2.0

Its CodeAgent uses an AST interpreter with explicit import/submodule allowlists and operation limits. Upstream correctly states that local code execution is not a complete security sandbox and documents stronger remote/container executors.

Decision: useful reference/component for restricted code-action experiments, but Monty + OpenShell already gives Jarvis a cleaner separation between restricted intermediate code and true OS execution. Do not add another complete runtime without a concrete winning primitive.

### `huggingface/trl` — S future engineering training layer, Apache-2.0

Critical integration finding: current TRL includes native Harbor support through `trl.experimental.harbor`.

`HarborSpec` converts a Harbor suite into:

- training dataset;
- environment factory;
- reward functions.

The policy model can generate turns, tools act inside the Harbor environment, and the Harbor verifier becomes a scalar reward for GRPO.

This creates a short permissive path for a future engineering-specialized open model:

`Terminal-Bench-Science / Jarvis Engineering Bench -> Harbor verifier -> TRL GRPO`.

Microsoft Agent Lightning remains useful when stronger decoupling between agent runtime and trainer is desired, but TRL+Harbor is the more direct first path for Hugging Face/Qwen models.

### `huggingface/peft` — S, Apache-2.0

Direct candidate for engineering specialization using LoRA/adapters rather than full fine-tuning. Supports modern Qwen workflows, multiple adapters and runtime switching, and integrates with Transformers/TRL/Accelerate.

Candidate direction:

`base open model + one or more Jarvis engineering adapters`, with domain/version-specific adapters where useful.

### `huggingface/accelerate` — A+/S training/offload utility, Apache-2.0

Useful existing primitives include CPU offload, automatic device-map inference and large-checkpoint dispatch. This is a training/loading utility layer for limited hardware; it does not replace the serving backends.

### TGI status

Hugging Face `text-generation-inference` is archived. Do not invest a new Jarvis serving integration there unless project status materially changes. Current serving focus remains llama.cpp / Ollama / vLLM.

### Consolidated training direction

`base Qwen/open model -> PEFT engineering adapter -> TRL + Harbor deterministic reward training -> torchAO quantization/QAT when appropriate -> Accelerate device/offload`.

## 6. DeepSeek ecosystem

### `deepseek-ai/DeepSpec` — A/S targeted optimization, MIT

Supports DSpark, DFlash and Eagle3 speculative draft-model training/evaluation and publishes Qwen3 draft checkpoints, including 4B/8B/14B variants.

Training draft models locally is not a current Jarvis priority: the upstream reference pipeline warns of data-cache requirements on the order of tens of TB even for small Qwen3 targets and commonly assumes multi-GPU training.

Decision: reuse released compatible draft checkpoints and benchmark actual acceptance/latency using GuideLLM; do not build a local DeepSpec training pipeline now.

### `deepseek-ai/deepseek-harness` — S runtime/authority bake-off candidate, MIT

One of the strongest discoveries in this audit. Current project is a 2026 developer preview, so API stability remains a risk, but the architecture closely matches Jarvis requirements.

High-value architecture:

- model adapters, tool registries, session logs, agent loop, sandbox, approval, credentials and telemetry are replaceable plugins/providers;
- typed service/event seams;
- reversible effects and layered profiles/patches;
- append-only SessionEvent log as durable truth;
- invariant: model-visible information must be logged;
- replay/fork/resume semantics.

#### Tool execution pipeline

The documented pipeline is explicit:

1. log tool call;
2. pre-execute;
3. monotonic guards may deny or abstain;
4. approval;
5. execute wrappers such as timeout/retry/metrics;
6. tool body;
7. filesystem-intent gate;
8. post-execute;
9. normalize/finalize;
10. freeze authoritative result;
11. create model-facing/logged result.

Code Mode subcalls are routed through the same execution pipeline rather than bypassing it.

#### Approval

Approval is fail-closed:

- outcomes include `allowed-once`, rejected, cancelled and unavailable;
- only `allowed-once` grants execution;
- missing/broken/nonconforming approval answerer becomes unavailable;
- an `ask` and its decision must be logged consistently in the same open turn;
- approval links to the tool call id.

#### Permission presets

Presets combine sandbox and approval policy but do not own enforcement. Canonical services do. A workspace-write preset requires a confining shell capability and asks on escalation; loading fails if required sandbox capability is absent.

#### Sandbox boundary

DeepSeek Harness has a real, fail-closed cross-platform filesystem sandbox using platform-specific mechanisms including bwrap/Landlock, Seatbelt and a Windows runner. However upstream explicitly scopes its sandbox policy to filesystem effects. Network, process visibility, syscalls, devices and credentials are outside that sandbox's policy model.

Therefore:

- DeepSeek Harness runtime/authority/session pipeline: S candidate;
- DeepSeek native sandbox: useful filesystem layer, not replacement for OpenShell;
- candidate stack: `DeepSeek Harness runtime/authority -> OpenShell hard isolation`.

#### Escalation code-first result

Sandbox escalation is one-shot and fail-closed:

- target must be strictly broader than current mode;
- a justification is required;
- approval is resolved before execution;
- missing service/agent, rejected, cancelled or unavailable approval all fail;
- only an `allowed-once` decision enables the broader mode for the single call.

DeepSeek Harness should join Pydantic AI/Harness, Hermes and Microsoft Agent Framework in the direct runtime integration bake-off.

### `deepseek-ai/ESFT` — A future MoE specialization

Code and model licenses are separate:

- source code: MIT;
- bundled/published model artifacts: DeepSeek custom model license with separate restrictions/obligations.

The ESFT technique selects and trains only domain-relevant experts in sparse MoE models. This may be useful if Jarvis's future engineering backbone is MoE, but PEFT/LoRA + TRL/Harbor is currently more general and operationally simpler.

### `deepseek-ai/DeepSeek-OCR-2` — A+/S experimental DocumentIngest candidate

Repository source is Apache-2.0. It provides image and concurrent-PDF inference paths, Transformers/vLLM integration and layout-aware document-to-Markdown extraction.

Potential Jarvis capability:

`DocumentIngest -> local OCR/layout extraction -> provenance-preserving chunks/artifacts -> RAG`.

High-value domains include technical reports, datasheets, P&IDs and engineering PDFs.

Caveats:

- verify the exact Hugging Face checkpoint/model-card license independently before bundling weights;
- reference stack is Linux/CUDA/FlashAttention/vLLM-oriented, so initial deployment may fit WSL or a future local server better than native Windows laptop integration.

## 7. EleutherAI ecosystem

The sibling scan did not identify a new core Jarvis runtime component beyond `lm-evaluation-harness`.

### `EleutherAI/cupbearer` — B+/R&D, MIT

Framework for mechanistic anomaly detection tasks/detectors. Interesting future model-safety research tool, but not a production runtime guardrail for Jarvis tool authority.

### `EleutherAI/sparsify` — B+/future interpretability, MIT

Trains k-sparse autoencoders/transcoders on Hugging Face model activations and can compute activations on the fly rather than requiring large disk caches. Potential future model-analysis/interpretability capability for an engineering specialist, not a Jarvis runtime dependency.

## 8. n0 / Iroh ecosystem

### `n0-computer/iroh` — A+/S optional Jarvis node transport, dual MIT/Apache-2.0

Iroh provides encrypted QUIC connectivity addressed by endpoint public key, direct-path/hole-punching with relay fallback, concurrent streams/datagrams and ALPN protocol routing.

#### Code-first identity finding

After the cryptographic handshake, Iroh derives the remote `EndpointId` from the public key encoded in the peer TLS certificate. A connection lacking peer identity or ALPN fails; an `after_handshake` hook can reject and close the connection before delivery to the application.

Candidate principle:

`JarvisNodeId = cryptographic EndpointId`.

But identity is not authorization. Jarvis must separately map EndpointId to user/device trust, ACLs and capability grants. A valid Iroh peer must never receive tool authority merely because it authenticated cryptographically.

### `n0-computer/iroh-ffi` — A+/S enabler, dual MIT/Apache-2.0

Important practical finding: official bindings for stabilized Iroh 1.0 are already published for Python, Node.js, Kotlin and Swift (plus community Go). The stable surface covers endpoints, connections, paths, tickets, relays and services.

This means the current Python Jarvis backend can prototype Iroh directly; a Rust migration is not prerequisite.

### `n0-computer/irpc` — A internal Rust RPC, dual MIT/Apache-2.0

IRPC is deliberately lightweight Rust-to-Rust RPC for local async boundaries, cross-process or Iroh/noq network communication.

It supports:

- unary RPC;
- server streaming;
- client streaming;
- bidirectional streaming;
- typed protocol enums/macros;
- local and remote clients using the same service contract;
- OpenTelemetry span-context propagation;
- bounded wire messages (default 16 MiB).

Explicit non-goals include cross-language interoperability and protocol versioning.

Decision:

- use only where both sides are Rust and the lightweight typed protocol is beneficial;
- do not make IRPC Jarvis's universal public/client protocol;
- Agent Host Protocol or another versioned cross-language schema remains better for desktop/mobile/Python/TypeScript client synchronization.

### `n0-computer/iroh-blobs` — A future artifact/model transport, dual MIT/Apache-2.0

Provides BLAKE3-verified content-addressed streaming by hash/range over Iroh. Candidate future use: transfer model shards, checkpoints, generated artifacts or large workspace objects among trusted Jarvis nodes.

Current-main caveat: upstream explicitly says the current development line is not yet production quality and recommends a pinned older production-quality line. Do not adopt git `main` blindly; select/pin a documented stable release and review its license/dependencies.

### `n0-computer/iroh-gossip` — A-/PARKED multi-node event bus, dual MIT/Apache-2.0

Topic-based epidemic broadcast trees over Iroh. Potential future use for decentralized worker/event distribution, but overkill for the current single-user/small-node Jarvis architecture. Keep parked until multiple autonomous nodes create a real need.

### `n0-computer/iroh-docs` — A-/PARKED selective replica state, dual MIT/Apache-2.0

Signed, multi-dimensional KV replicas with namespace write-capability keys, author keys and range-based set reconciliation. Values point to BLAKE3 content rather than embedding it.

Potential use: selectively synchronize non-canonical metadata/memory between Jarvis nodes. Do not make it the canonical Jarvis database by default: its eventual/replicated model and dependency on blobs+gossip add complexity that the current backend does not need.

### `n0-computer/iroh-live` — PARKED

Interesting future P2P audio/video stack, but upstream currently labels it an early tech preview, Windows capture is missing, the relay lacks authentication and APIs are unstable. Do not integrate for the current Windows-first Jarvis path.

### Current Iroh architecture decision

Keep Iroh as an **optional node transport layer**, not as the Jarvis application architecture itself:

`Jarvis capability/ACL authority -> versioned Jarvis/AHP message protocol -> Iroh encrypted transport/identity`.

Optional additions only when justified:

- `iroh-blobs`: large content-addressed artifact transfer;
- `irpc`: Rust-to-Rust internal streaming RPC;
- `iroh-docs`: selective replicated metadata;
- `iroh-gossip`: larger multi-node pub/sub.

## 9. Architecture delta after Continuation 2

The strongest revised candidate stack is now:

- **root authority/policy:** Jarvis typed capabilities; evaluate Microsoft Agent Governance Toolkit;
- **hard OS isolation:** NVIDIA OpenShell;
- **agent runtime bake-off:** DeepSeek Harness vs Pydantic AI/Harness vs Hermes vs Microsoft Agent Framework;
- **coding worker:** Cline SDK and/or narrow OpenCode services, with OpenCode LSP as a strong reusable code-intelligence candidate;
- **Windows worker:** Microsoft UFO;
- **authenticated/transactional browser:** anomalyco/browser-control;
- **terminal/TUI worker:** anomalyco/terminal-control;
- **sensitive computer-use preflight:** Jarvis/AIRI-style observation epoch/snapshot binding;
- **model/provider public metadata:** anomalyco/models.dev + Jarvis-specific measurements;
- **local serving:** llama.cpp / Ollama / vLLM selected per host;
- **cross-runtime lifecycle/trajectory:** NeMo Relay;
- **skill/plugin admission:** SkillSpector + SkillEvaluator;
- **model evaluation:** lm-evaluation-harness/Lighteval;
- **engineering/tool evaluation:** Harbor/TB-Science + MCP-Universe/MCPEval + WindowsAgentArena;
- **engineering specialization:** PEFT + TRL/Harbor (+ torchAO/Accelerate); Agent Lightning as alternative trainer bridge;
- **document intelligence:** DeepSeek-OCR-2 candidate, subject to exact weight-license and deployment checks;
- **optional node networking:** Iroh + official language bindings, with Jarvis ACLs above transport identity;
- **client/session synchronization:** Microsoft Agent Host Protocol candidate over local or Iroh transport.

## 10. Next exact checkpoint

Resume with remaining high-value original-author/sibling waves from the resolved Nous provenance, prioritizing components not already duplicated:

1. LinkedIn ecosystem around `Liger-Kernel`: determine whether any sibling training/performance tooling adds a unique reusable primitive beyond torchAO/TRL.
2. HLC-Lab and any remaining research upstreams from the 49-fork provenance map: relevance scan before deep code audit.
3. Salesforce AI Research broader sibling scan if not already exhausted, focusing only on engineering/tool-use components beyond MCP-Universe/MCPEval.
4. Axolotl AI Cloud ecosystem: verify whether Axolotl offers a materially shorter PEFT/QLoRA training route than the direct HF stack and whether any reusable dataset/eval utilities are unique.
5. Harbor ecosystem siblings beyond Terminal-Bench-Science only where they add engineering-environment/verifier primitives.
6. Update the canonical `docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md` with the strongest promotions from both continuation audits and explicit disposition (`DIRECT_DEPENDENCY`, `VENDORED_COMPONENT`, `REFERENCE_ONLY`).
7. Re-read PR #309 exact final head and CI after all documentation writes. Do not merge unless separately authorized.
