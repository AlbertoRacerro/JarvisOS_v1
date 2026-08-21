# Upstream author ecosystem audit — 2026-08-19

Status: active continuation audit; documentation only; **not implementation authority**  
Parent register: `docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`  
Fork map: `docs/audits/NOUS_FORK_UPSTREAM_EXPANSION_2026-08-19.md`

## Objective

Continue the Nous-fork audit at the true upstream/source repositories and then traverse the relevant software ecosystems of those original authors. The maintainer preference is explicit: when current upstream code is MIT/Apache/BSD/ISC/zlib or otherwise commercially compatible, prefer direct integration or controlled vendoring over needless reimplementation.

This document records the second-stage author/ecosystem work so it can resume exactly across conversations.

## Reuse rule

- `DIRECT_DEPENDENCY`: maintained permissive upstream package/binary/service/API; preferred when the boundary is clean.
- `VENDORED_COMPONENT`: permissive upstream source pinned with full provenance/NOTICE/SBOM when offline deployment, patch control or reproducibility justify vendoring.
- `REFERENCE_ONLY`: no/unclear/incompatible license, obsolete implementation or unacceptable dependency/security cost.

License compatibility is necessary but not sufficient: exact component, transitive licenses, platform fit, authority boundary, security posture, maintenance and benchmark evidence remain gates.

---

# Nous fork provenance closure

The current GitHub query `org:NousResearch fork:only` produced 49 repositories; page 2 was empty. The original/source chain is now resolved for all 49 at audit time.

## Forks 1–26

Detailed first-stage evidence lives in `NOUS_FORK_UPSTREAM_EXPANSION_2026-08-19.md`. Resolved upstreams include Microsoft Agent Governance Toolkit, NVIDIA OpenShell/NemoClaw, PyTorch TorchTitan, NVIDIA-NeMo Gym/Automodel/RL/Nemotron/Megatron-Bridge, Harbor, Cline, Axolotl, LiteLLM, Hugging Face Nanotron/Lighteval/DataTrove, vLLM, Iroh, llama.cpp, TextArena and Ink.

## Forks 27–49

| # | Nous fork | Original/source upstream | Current license posture | Disposition |
|---:|---|---|---|---|
| 27 | `DeepEP` | `deepseek-ai/DeepEP` | MIT | future inference/training component; DeepSeek sibling scan opened |
| 28 | `jedi` | `davidhalter/jedi` | GitHub metadata `Other/NOASSERTION` | exact license text required before reuse |
| 29 | `logfire-rust` | `pydantic/logfire-rust` | MIT | Pydantic sibling scan opened |
| 30 | `tch-rs` | `LaurentMazare/tch-rs` | Apache-2.0 | low-priority Rust/PyTorch bridge |
| 31 | `yellowstone-grpc` | `rpcpool/yellowstone-grpc` | AGPL-3.0 | out of scope/reference only for proprietary Jarvis core |
| 32 | `iroh-blobs` | `n0-computer/iroh-blobs` | Apache-2.0 | handle with Iroh distributed/edge family |
| 33 | `hf-hub` | `huggingface/hf-hub` | Apache-2.0 upstream | candidate model-artifact/HF registry client; HF sibling scan opened |
| 34 | `harbor` | `harbor-framework/harbor` | Apache-2.0 | same upstream family as `harbor-fork`; top agent-eval candidate |
| 35 | `iroh-gossip` | `n0-computer/iroh-gossip` | Apache-2.0 | handle with Iroh family |
| 36 | `longform-writing-bench` | `EQ-bench/longform-writing-bench` | no explicit current license found | reference only unless licensing changes |
| 37 | `Liger-Kernel` | `linkedin/Liger-Kernel` | BSD-2-Clause | direct-reuse candidate for memory-efficient future fine-tuning |
| 38 | `ollama` | `ollama/ollama` | MIT | code-first local runtime candidate already audited |
| 39 | `creative-writing-bench` | `EQ-bench/creative-writing-bench` | no explicit current license found | reference only unless licensing changes |
| 40 | `wterm` | `vercel-labs/wterm` | Apache-2.0 | optional web-terminal UX/runtime building block |
| 41 | `speculators` | `vllm-project/speculators` | Apache-2.0 | inference/speculation family |
| 42 | `pico` | `HLC-Lab/pico` | custom/NOASSERTION in metadata | exact terms required before reuse |
| 43 | `lm-evaluation-harness-pretraining` | `EleutherAI/lm-evaluation-harness` | MIT | direct-reuse model-eval candidate |
| 44 | `curve25519-dalek` | `dalek-cryptography/curve25519-dalek` | multi/custom classification in GitHub metadata | treat as transitive crypto infrastructure unless directly needed |
| 45 | `eqbench3` | `EQ-bench/eqbench3` | MIT | reusable specialist model-quality benchmark |
| 46 | `nccl-tests` | `NVIDIA/nccl-tests` | BSD-3-Clause | future multi-GPU interconnect qualification |
| 47 | `openai-evals` | `openai/evals` | GitHub metadata not a simple permissive SPDX classification | exact current OpenAI license required before reuse |
| 48 | `LeastLoadedEP` | `SalesforceAIResearch/LeastLoadedEP` | Apache-2.0 | future MoE/expert-parallel research; Salesforce sibling scan opened |
| 49 | `image-size` | ultimate source `image-size/image-size`, via `getitcheappro/image-size-patched` | MIT upstream | low architecture value; if used, ensure current upstream includes relevant security fixes or preserve patched provenance |

Result: **49/49 Nous forks now have resolved upstream/source attribution at the audit checkpoint.**

---

# Original-author ecosystem scans

## Pydantic — high-value agent runtime ecosystem

### `pydantic/pydantic-ai` — S/A+ direct component candidate

Current upstream is MIT and active. Code/docs inspection confirms:

- typed tools and structured outputs;
- per-run/per-step tool preparation and dynamic visibility;
- strict argument schema support;
- composable toolsets;
- MCP integration;
- explicit `ApprovalRequiredToolset` wrapper that refuses to execute until the run context marks the exact call approved;
- deferred/external tool calls that may either resolve inline or terminate a run and resume in a subsequent run with correlated conversation state;
- argument/context-dependent approval requirements;
- explicit distinction between human approval and authorization.

A particularly important upstream warning states that client-submitted approval is **not** an authorization boundary against an untrusted client. Sensitive tools must still authenticate/authorize server-side. This aligns with JarvisOS's intended authority separation.

**Integration interpretation:** Pydantic AI can be a typed Python agent/tool orchestration layer; it must not replace OpenShell/OS sandboxing or Jarvis-owned policy/identity.

### `pydantic/pydantic-ai-harness` — S direct-reuse candidate

MIT and active. This is not a thin demo: it is the official capability library/harness around Pydantic AI and exposes complete Coder/Researcher stacks plus granular capabilities.

Verified/advertised capability surface includes:

- workspace-rooted `FileSystem`, with traversal/symlink safety and protected secret behavior;
- allowlisted/denylisted `Shell`, timeouts and LLM API-key stripping from child environments;
- repo orientation (`AGENTS.md`/`CLAUDE.md` + structure);
- structured Planning;
- read-only explorer and other SubAgents;
- context compaction, cache-bust warnings, tool-output limits/spill;
- persistent namespaced Memory and conversation search;
- on-demand Skills;
- Browser Use integration;
- guardrails and prompt-injection defender;
- spend/token budgets;
- step persistence/durable execution support;
- `Code Mode`, in which one generated Python script can invoke many tools inside a Monty sandbox while intermediate data stays out of the LLM context;
- complete coding/research harnesses assembled from the same independently removable capabilities.

**Major consequence:** before implementing an internal all-purpose Python agent harness, prototype JarvisOS against Pydantic AI Harness directly. Compare it with Hermes and Cline instead of reimplementing equivalent primitives.

### Pydantic future queue

- inspect `pydantic-ai-harness` shell/filesystem/Code Mode implementations and security tests in more depth;
- compare its persistent memory/compaction to Hermes TaskMemory/compression survival findings;
- inspect Logfire/OpenTelemetry path only if Jarvis AgentRun telemetry needs an existing observability backend;
- inspect `pydantic/monty` as the execution substrate behind Code Mode if license/containment fit matters.

---

## Salesforce AI Research — MCP/tool-evaluation ecosystem

### `SalesforceAIResearch/MCP-Universe` — A+/S candidate for MCP benchmark infrastructure

Apache-2.0. It is a complete ecosystem for building/evaluating MCP agents rather than just a benchmark table. The current tree/docs expose:

- real MCP server interaction rather than synthetic tool schemas only;
- long-horizon tasks and large/unfamiliar tool spaces;
- live/time-sensitive environments;
- agent/workflow/MCP/LLM/benchmark/dashboard layers;
- benchmark domains including web search, navigation/browser automation, finance, repository management and **3D design**;
- MCP+ context management that post-processes verbose MCP results before model context;
- deep-research orchestration with parallel tool calls;
- trace collection and custom benchmark/task configuration.

**Jarvis use:** use or adapt its benchmark infrastructure when measuring MCP/tool-use competence across local and cloud models, especially once BLUECAD/engineering tools are exposed via typed capabilities/MCP.

### `SalesforceAIResearch/MCPEval` — A direct-reuse evaluation candidate

Apache-2.0. Provides automated task generation, verification/evaluation, multi-turn simulation, conversation replay, model comparison with statistical tests, SQLite persistence, REST API, and 15+ MCP servers.

Several included servers are deterministic/self-contained (HR, ecommerce, datetime, unit conversion, calculator, SQLite), which is useful for repeatable tool-use regression tests. Multi-turn judging covers clarification, context maintenance, tool efficiency, goal achievement and response quality.

**Jarvis use:** complementary to Harbor. Harbor evaluates terminal/environment outcomes; MCPEval/MCP-Universe evaluate MCP/tool interaction quality and can supply deterministic regression worlds.

### Salesforce future queue

Prioritize only if they add non-overlapping mechanisms:

1. `MCP-Universe` task/evaluator code and MCP+ implementation;
2. `MCPEval` verifier/task-generation pipeline;
3. `xRouter` for routing only if it beats/extends LiteLLM/vLLM semantic router under benchmark;
4. `Elastic-Reasoning` only if its adaptive compute allocation adds something beyond Nous Nomos;
5. `xLAM` as a tool-use specialist model family, not an authority/runtime.

---

## Vercel Labs — browser and shell building blocks

### `vercel-labs/agent-browser` — S browser-worker candidate

Apache-2.0 and very active. Security documentation/code surface is materially stronger than a generic Playwright wrapper:

- local encrypted auth vault; passwords excluded from LLM context and normal daemon IPC;
- credential-provider plugins run out-of-process with structured credential-resolution requests;
- content-boundary markers use a per-process CSPRNG nonce and expose provenance metadata in JSON mode;
- domain allowlist covers navigations, subresources, WebSocket, EventSource and Beacon; supported Chromium mode also disables WebRTC paths that could bypass HTTP interception;
- action policy is enforced by the daemon;
- selected actions can require confirmation; pending confirmations auto-deny and non-TTY interactive mode denies rather than guessing;
- output caps mitigate context flooding;
- risky browser attach/profile/state modes are rejected when containment cannot be guaranteed;
- documentation explicitly states that browser allowlisting is **not an OS firewall**, so a lower-level network sandbox is still required.

**Candidate architecture:** `Jarvis authority -> OpenShell/host egress policy -> agent-browser -> browser`, with separate Jarvis browser profiles for research/user-visible/transactional usage. This is a direct integration candidate, not something to rewrite with raw Playwright unless a benchmark proves a missing requirement.

### `vercel-labs/bash-tool` / `just-bash`

`bash-tool` is MIT and exposes an AI-agent shell/read/write adapter over a pluggable Sandbox interface, including pre/post hooks and persistent external sandbox support.

However, its default in-process backend `just-bash` currently has no license reported in GitHub repository metadata. Do not make that transitive dependency part of proprietary JarvisOS until its exact licensing is resolved. If `bash-tool` is otherwise useful, point its generic sandbox interface at a separately acceptable runtime rather than assuming `just-bash` is reusable.

**Current disposition:** `bash-tool` B/PARKED because Pydantic Harness Shell + OpenShell are stronger/currently better-bounded candidates.

### Vercel future queue

- `remote-agent-browser` only if it adds isolation/session semantics missing from agent-browser;
- `agent-eval` if it adds benchmark primitives missing from Harbor/MCPEval;
- `sandcastle`/other sandbox projects only if they are permissively licensed and benchmark better than OpenShell;
- `open-agents` only if it contributes a non-overlapping runtime primitive.

---

## DeepSeek — inference/training acceleration ecosystem

### `deepseek-ai/DeepSpec` — A research/inference acceleration candidate

MIT and current. Full-stack training/evaluation code for speculative-decoding draft models, including DSpark, DFlash and Eagle3.

Important practical findings:

- released draft checkpoints exist for Qwen3 4B/8B/14B and Gemma 12B targets;
- evaluation covers math, coding and chat benchmarks;
- the project includes third-party adapted code with explicit NOTICE attribution;
- training itself is not consumer-friendly: defaults assume 8 GPUs and the full target-cache preparation can require enormous storage (README gives roughly 38 TB for the default Qwen3-4B data pipeline).

**Jarvis implication:** do not plan to train DeepSpec drafts on the current laptop. Instead, investigate whether released compatible draft checkpoints can accelerate Jarvis local models through a serving backend that supports the same speculative algorithm. Only pursue custom training when there is dedicated compute/storage or a funded need.

### DeepSeek sibling queue

- `FlashMLA`, `DeepGEMM`, `TileKernels`: future GPU/kernel efficiency, mostly server-side;
- `LPLB`, `DualPipe`, `DeepEP`: distributed/MoE communication/load balancing;
- model repos (`DeepSeek-Coder-V2`, etc.) are model candidates, not Jarvis runtime components.

---

## Harbor Framework — scientific/engineering evaluation

### `harbor-framework/terminal-bench-science` — S engineering-eval reference/component

Apache-2.0 and active. This is directly relevant to a future Jarvis/BLUECAD engineering specialist because it evaluates agents on complex real scientific terminal workflows rather than isolated QA.

The repository includes task-authoring/review automation, separate verifier patterns and tasks across chemistry, materials science, physics, earth science, statistics and life science.

A code-first sampled task, `xrd-multiphase-qpa`, demonstrates the desired benchmark structure:

- explicit artifact contract (`/workspace/output/results.csv`);
- realistic inverse-problem work order rather than a hidden trivia answer;
- synthetic-but-physically-grounded data with exact hidden truth;
- separate deterministic pytest verifier;
- schema/contract validation;
- open-set identification checks;
- per-sample quantitative RMSE gates, so a local catastrophic error cannot disappear into a global average;
- explicit `unknown`/`amorphous` buckets;
- a committed gate battery of ablated/shortcut strategies that must fail, proving the task's claimed difficulty axis is actually load-bearing;
- evidence/provenance and domain metadata.

**Direct BLUECAD/HYSYS template:**

`environment + engineering task + required artifact schema + exact/physical truth + deterministic verifier + adversarial/ablated baselines + reproducible score`.

Candidate future tasks:

- flowsheet convergence and failure diagnosis;
- material/energy balance reconciliation;
- reactor parameter fitting and kinetic-model selection;
- unit consistency and equation implementation;
- CAD geometry/edit requests with hidden geometric invariants;
- mesh/solver setup and result validation;
- equipment sizing/economic calculations;
- PFD/P&ID state modification with topology/verifier checks.

This should strongly influence the engineering-benchmark design before model specialization/training begins.

### Harbor sibling queue

- `benchmark-template` as starting scaffolding for Jarvis engineering benchmarks;
- `terminal-bench` for generic coding/terminal competence;
- `terminal-bench-science` as domain pattern;
- avoid forking benchmark infrastructure until Harbor's extension points are tested directly.

---

# Other original-author scans already completed at inventory level

## Hugging Face

High-value siblings discovered for later code-first filtering:

- `transformers` / `hf-hub` foundational model/artifact interfaces;
- `optimum`, **`optimum-quanto`**, `optimum-intel`, `optimum-onnx` for local/quantized deployment;
- `text-embeddings-inference`, `inference-benchmarker`, `optimum-benchmark`;
- `lighteval`, `evaluate`;
- `smolagents`, `hf-agents`, `skills`, `responses.js`, `jupyter-agent`;
- `speech-to-speech` and `parler-tts` for local voice work;
- `meshgen` only after verifying actual scope/license;
- `text-generation-inference` is archived and should not outrank current vLLM.

Next HF priority: `optimum-quanto`, then `responses.js`/`smolagents` only if they add a concrete mechanism not already supplied by Hermes/Pydantic/Cline.

## EleutherAI

- `lm-evaluation-harness` is the priority MIT component to compare against Harbor/Lighteval for model-level evaluation;
- BIG-bench and training frameworks are secondary;
- interpretability projects (`SAELens`, `delphi`, `knowledge-neurons`) are lower priority because Nous neural-steering already covers the directly actionable model-steering question.

## n0-computer

Treat `iroh`, `iroh-blobs`, `iroh-gossip`, `quic-rpc`, NAT-traversal and sync components as one future distributed/edge connectivity family. Potential BlueRev/Jarvis worker value: identity-addressed connectivity and NAT traversal without stable public IP assumptions. Not current authority/runtime priority.

## PyTorch

Beyond BSD `torchtitan`, prioritize:

- `pytorch/ao` for low-bit/quantization techniques;
- `pytorch/executorch` for on-device/edge inference.

## EQ-bench

`eqbench3` is MIT and reusable. `creative-writing-bench` and `longform-writing-bench` currently lack explicit license metadata, so remain reference-only. Use EQ-bench primarily for model-behavior evaluation, not engineering truth.

## LinkedIn

`Liger-Kernel` itself is the main relevant BSD-2-Clause component: memory-efficient Triton kernels can matter when future engineering-specialist fine-tuning becomes compute constrained. No broad LinkedIn org audit is currently justified unless a sibling is directly connected to that training path.

---

# Current integration-stack hypothesis after upstream reuse audit

This is **not** an approved architecture. It is the smallest set of existing permissively licensed components currently worth integration experiments:

```text
JarvisOS canonical authority / identity / domain state
  |
  +-- policy candidate: Microsoft Agent Governance Toolkit (MIT)
  |
  +-- sandbox boundary: NVIDIA OpenShell (Apache-2.0)
  |
  +-- agent workers (benchmark, do not stack blindly)
  |     +-- Hermes Agent (MIT)
  |     +-- Pydantic AI + Harness (MIT)
  |     +-- Cline SDK for coding (Apache-2.0)
  |
  +-- browser worker: Vercel agent-browser (Apache-2.0)
  |
  +-- provider gateway: LiteLLM community/core MIT subset
  |
  +-- local model serving adapters
  |     +-- llama.cpp (MIT) — quantized/consumer local runtime
  |     +-- Ollama (MIT) — local model lifecycle/scheduler
  |     +-- vLLM (Apache-2.0) — high-throughput/tool-aware server
  |           +-- Agentic API (Apache-2.0) — stateful Codex/Claude-compatible gateway
  |
  +-- evaluation
        +-- Harbor / Terminal-Bench(-Science) (Apache-2.0)
        +-- MCP-Universe + MCPEval (Apache-2.0)
        +-- lm-evaluation-harness / Lighteval for model-level tests
        +-- Hermes toolperf/compression eval for runtime/context quality
```

Key rule: **integrate the narrowest maintained component that owns a problem well; do not run multiple overlapping policy/routing/runtime layers merely because all are permissively licensed.**

---

# Exact resume queue

Continue code-first in this order:

1. `pydantic/pydantic-ai-harness`: inspect `FileSystem`, `Shell`, `Code Mode`, step persistence and their security tests; determine whether Coder can run inside OpenShell without redundant/conflicting sandbox assumptions.
2. `SalesforceAIResearch/MCP-Universe`: inspect concrete task/evaluator classes and MCP+ result-reduction implementation; determine how easily BLUECAD tools/tasks can plug in.
3. `SalesforceAIResearch/MCPEval`: inspect automatic task verification/revalidation code and deterministic-server fixtures.
4. `vercel-labs/agent-browser`: inspect daemon enforcement/action-policy code and snapshot/ref semantics; compare directly with AIRI's stale-perception protection.
5. `harbor-framework/benchmark-template` and Terminal-Bench-Science verifier contract; sketch a minimum BlueCAD/HYSYS benchmark **only in documentation**, not implementation.
6. `EleutherAI/lm-evaluation-harness` vs `huggingface/lighteval`: compare extension/task APIs and choose model-eval layer.
7. `huggingface/optimum-quanto`, then `pytorch/ao`/ExecuTorch: consumer/local quantization and edge deployment.
8. DeepSeek `DeepSpec` integration feasibility with current vLLM/llama.cpp speculative-decoding support; prioritize released draft checkpoints over training.
9. return to high-priority Microsoft/NVIDIA/Cline siblings: agent-host-protocol, UFO/OmniParser, Agent Lightning, NeMo Agent Toolkit, SkillSpector/SkillEvaluator, Cline Bench/plugins.
10. lower-priority distributed/edge families: Iroh, DeepEP/LPLB/LeastLoadedEP, NCCL tests, only when distributed hardware work becomes relevant.

The 49-fork upstream-attribution phase is complete; remaining work is code-first depth and integration comparison, not provenance discovery.