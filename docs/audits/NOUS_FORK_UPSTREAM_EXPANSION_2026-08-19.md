# Nous fork upstream expansion audit — 2026-08-19

Status: active audit queue; documentation only; **not implementation authority**  
Owner: repository maintainer  
Parent register: `docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`

## Purpose

This audit expands the earlier Nous Research review beyond repositories authored by Nous. A current GitHub search for `org:NousResearch fork:only` returned 49 forks; page 2 returned no additional results. Every fork must be attributed to its actual `parent` / `source`, audited at upstream, and then followed by a relevance-scoped scan of other repositories from the original author/organization.

The objective is not to rewrite useful software merely to own the implementation. When an upstream component is under a commercially compatible permissive license and passes architecture/security/maintenance review, JarvisOS should prefer direct reuse or a tracked vendored component.

## Reuse-mode policy used by this audit

- `DIRECT_DEPENDENCY`: consume the maintained upstream package/binary/service/API directly, pinning version/commit as appropriate and preserving all required license/NOTICE attribution.
- `VENDORED_COMPONENT`: include upstream source/component in the JarvisOS tree only when vendoring materially improves deployment, patch control, offline operation, or reproducibility; preserve provenance, copyright, license and update path.
- `REFERENCE_ONLY`: inspect concepts and interfaces but do not copy/integrate code. Use for absent/unclear licenses, incompatible reciprocal/source-available terms, obsolete code, or components whose dependency/security cost is not justified.

A permissive license makes direct reuse possible; it does not make adoption automatic. Every dependency still requires fit, attack-surface, transitive-license, maintenance, platform, performance and supply-chain review.

## Organization traversal rule

For huge upstream organizations such as Microsoft, NVIDIA, NVIDIA-NeMo, Hugging Face, PyTorch and vLLM, "audit the author's other repositories" means a complete relevance-scoped inventory across:

- agents, tool use, MCP/plugins, sandboxing, identity/governance and policy;
- coding agents, IDE/CLI automation, browser/computer use;
- local inference, serving, quantization, model routing and model lifecycle;
- evaluation, RL/training, reasoning, data pipelines and distributed execution;
- engineering/CAD/simulation or infrastructure directly useful to JarvisOS/BLUECAD.

After inventory, code-first audit only non-redundant candidates with material value. Unrelated repositories are recorded as out of scope rather than mechanically read.

## Complete current Nous fork queue

| # | Nous fork | Verified original/source upstream | Upstream license / status | Audit state |
|---:|---|---|---|---|
| 1 | `llm-abliteration` | `Orion-zhen/abliteration` via intermediate `jim-plus/llm-abliteration` | GPL-3.0 | SOURCE VERIFIED; REFERENCE_ONLY |
| 2 | `agent-governance-toolkit` | `microsoft/agent-governance-toolkit` | MIT | CODE-FIRST STARTED |
| 3 | `NemoClaw` | `NVIDIA/NemoClaw` | Apache-2.0 | CODE-FIRST STARTED |
| 4 | `torchtitan` | `pytorch/torchtitan` | BSD-3-Clause | SOURCE VERIFIED; WAVE C |
| 5 | `Gym` | `NVIDIA-NeMo/Gym` | Apache-2.0 | CODE-FIRST STARTED |
| 6 | `local_generative_agents` | `joonspk-research/generative_agents` | Apache-2.0 | SOURCE VERIFIED; LOW PRIORITY |
| 7 | `Automodel` | `NVIDIA-NeMo/Automodel` | Apache-2.0 | UPSTREAM VERIFIED |
| 8 | `RL` | `NVIDIA-NeMo/RL` | Apache-2.0 | UPSTREAM VERIFIED |
| 9 | `Nemotron` | `NVIDIA-NeMo/Nemotron` | Apache-2.0 | SOURCE VERIFIED; WAVE B/C |
| 10 | `OpenShell` | `NVIDIA/OpenShell` | Apache-2.0 | CODE-FIRST STARTED |
| 11 | `harbor-fork` | `harbor-framework/harbor` | Apache-2.0 | CODE-FIRST STARTED |
| 12 | `cline` | `cline/cline` | Apache-2.0 | CODE-FIRST AUDITED |
| 13 | `axolotl-func-calling` | `axolotl-ai-cloud/axolotl` | Apache-2.0 | SOURCE VERIFIED; WAVE C |
| 14 | `litellm` | `BerriAI/litellm` | mixed tree: non-`enterprise/` MIT; `enterprise/` separate license | CODE-FIRST AUDITED CORE |
| 15 | `nanotron` | `huggingface/nanotron` | Apache-2.0 | SOURCE VERIFIED; WAVE C |
| 16 | `funcchain` | `shroominic/funcchain` | MIT | SOURCE VERIFIED; LOW PRIORITY |
| 17 | `lighteval` | `huggingface/lighteval` | MIT | SOURCE VERIFIED; WAVE C |
| 18 | `datatrove` | `huggingface/datatrove` | Apache-2.0 | SOURCE VERIFIED; WAVE D/C |
| 19 | `vllm` | `vllm-project/vllm` | Apache-2.0 | CODE-FIRST AUDITED CORE |
| 20 | `iroh` | `n0-computer/iroh` | Apache-2.0 | SOURCE VERIFIED; WAVE D |
| 21 | `nous-llama.cpp` | `ggml-org/llama.cpp` | MIT | CODE-FIRST STARTED |
| 22 | `OpenShell-Community` | `NVIDIA/OpenShell-Community` | Apache-2.0 | SOURCE VERIFIED; SAME FAMILY AS OPENSHell |
| 23 | `Megatron-LM` | `NVIDIA/Megatron-LM` | GitHub reports Other/NOASSERTION | SOURCE VERIFIED; LICENSE REVIEW REQUIRED |
| 24 | `TextArena` | `TextArena/TextArena` | MIT | SOURCE VERIFIED; WAVE C |
| 25 | `ink` | `vadimdemedes/ink` | MIT | SOURCE VERIFIED; LOW-PRIORITY CLI UX |
| 26 | `Megatron-Bridge` | `NVIDIA-NeMo/Megatron-Bridge` | Apache-2.0 | SOURCE VERIFIED; WAVE C |
| 27 | `DeepEP` | PENDING | PENDING | QUEUED |
| 28 | `jedi` | PENDING | PENDING | QUEUED |
| 29 | `logfire-rust` | PENDING | PENDING | QUEUED |
| 30 | `tch-rs` | PENDING | PENDING | QUEUED |
| 31 | `yellowstone-grpc` | PENDING | PENDING | QUEUED |
| 32 | `iroh-blobs` | PENDING | likely n0-computer family; verify exact source/license | QUEUED WITH IROH FAMILY |
| 33 | `hf-hub` | PENDING | likely Hugging Face family; verify exact source/license | QUEUED WITH HF FAMILY |
| 34 | `harbor` | PENDING | name collision; verify exact source before attribution | QUEUED |
| 35 | `iroh-gossip` | PENDING | likely n0-computer family; verify exact source/license | QUEUED WITH IROH FAMILY |
| 36 | `longform-writing-bench` | PENDING | PENDING | QUEUED |
| 37 | `Liger-Kernel` | PENDING | PENDING | QUEUED |
| 38 | `ollama` | `ollama/ollama` | MIT | CODE-FIRST STARTED |
| 39 | `creative-writing-bench` | PENDING | PENDING | QUEUED |
| 40 | `wterm` | PENDING | PENDING | QUEUED |
| 41 | `speculators` | `vllm-project/speculators` | Apache-2.0 | UPSTREAM VERIFIED EARLIER |
| 42 | `pico` | `HLC-Lab/pico` | custom/NOASSERTION in GitHub metadata | UPSTREAM VERIFIED; LICENSE REVIEW LATER |
| 43 | `lm-evaluation-harness-pretraining` | PENDING | PENDING | QUEUED |
| 44 | `curve25519-dalek` | PENDING | PENDING | QUEUED |
| 45 | `eqbench3` | PENDING | PENDING | QUEUED |
| 46 | `nccl-tests` | PENDING | PENDING | QUEUED |
| 47 | `openai-evals` | PENDING | PENDING | QUEUED |
| 48 | `LeastLoadedEP` | PENDING | PENDING | QUEUED |
| 49 | `image-size` | PENDING | PENDING | QUEUED |

## Planned waves

### Wave A — authority, agent runtime, coding and sandboxing

1. `microsoft/agent-governance-toolkit`
2. `NVIDIA/OpenShell`
3. `NVIDIA/NemoClaw`
4. `cline/cline`
5. relevant sibling projects from Microsoft/NVIDIA/Cline
6. low-priority older agent frameworks only when they add a non-overlapping primitive

### Wave B — local inference and provider abstraction

1. `BerriAI/litellm` MIT/community subset
2. `vllm-project/vllm` + `agentic-api` + `guidellm` + `speculators`
3. `ggml-org/llama.cpp`
4. `ollama/ollama`
5. `NVIDIA-NeMo/Nemotron`
6. PyTorch AO/ExecuTorch and Hugging Face inference/quantization siblings

### Wave C — engineering-specialist training and evaluation

1. `harbor-framework/harbor`
2. `NVIDIA-NeMo/Gym`
3. `huggingface/lighteval`
4. `TextArena/TextArena`
5. `axolotl-ai-cloud/axolotl`
6. `pytorch/torchtitan`, `NVIDIA-NeMo/RL`, `NVIDIA-NeMo/Automodel`, `NVIDIA-NeMo/Megatron-Bridge`
7. remaining eval/training upstreams after provenance resolution
8. compare with Nous Atropos/Nomos/toolperf/compression-eval to avoid duplicate frameworks

### Wave D — data, distributed systems and lower-priority infrastructure

Audit `huggingface/datatrove`, `n0-computer/iroh` family, `pico`, `nccl-tests`, `LeastLoadedEP`, crypto/network bindings and remaining forks. Promote only mechanisms that materially improve local/distributed JarvisOS, BlueRev edge workers, offline resilience or model infrastructure.

## Phase 1 findings — authority/runtime

### Microsoft Agent Governance Toolkit — high-value direct-reuse candidate

Upstream is MIT. Current Python policy implementation includes schema-versioned policy documents; `pre_input`, `pre_tool`, `post_tool`, `pre_output`; allow/deny/warn/require-approval/log actions; validated rate limits; bounded expression parsing; fail-closed rule-evaluation errors; hierarchical `extends`; and additive-only inheritance so a child cannot weaken an inherited deny. Execution-context policy distinguishes inner-loop, CI/CD and autonomous modes.

Current package consolidation exposes a broad `agent-governance-toolkit-core` package rather than only a microscopic policy package. Prefer a narrow official module/package surface if available. One inspected trust evaluator allows when no policies are loaded, so JarvisOS must retain a fail-closed bootstrap invariant.

**Disposition:** `DIRECT_DEPENDENCY` first if a narrow supported API exists; `VENDORED_COMPONENT` only if necessary.

### NVIDIA OpenShell — high-value sandbox runtime candidate

Apache-2.0. Code confirms a real sandbox boundary: typed filesystem allowlists, network default Block with explicit Proxy/Allow, optional hard-required Landlock, separate run-as identity, Linux seccomp restrictions on dangerous escape/process primitives, and inference/provider profiles separating credential discovery from request-time use.

**Disposition:** evaluate as real external sandbox runtime for Hermes/Cline/coding workers rather than rebuilding this boundary in JarvisOS. Remaining checks: Windows/WSL deployment, policy-control API, overhead, local-inference route, credential boundary and upgrade strategy.

### NVIDIA NemoClaw

Apache-2.0 and currently includes Hermes in its supported agent ecosystem. Policy code manages presets/agent additions, validates sandbox policy, protects ownership/baseline transitions, previews endpoints and rejects some network-policy bypass shapes such as arbitrary allowed IPs.

**Disposition:** likely optional packaging/adapters over OpenShell, while JarvisOS remains canonical authority.

### Cline as a coding worker, not authority

`cline/cline` is Apache-2.0 and exposes an actual SDK, not merely a VS Code extension. `@cline/sdk` / `ClineCore` supports local/remote backend creation, sessions, provider/model configuration, tool-policy callbacks, custom tools/hooks/plugins, events, usage accounting, abort/stop, checkpoint/restore and agent/team/sub-agent APIs.

Its wrapper routes governed tools through current approval settings, but Cline's UI defaults are not a JarvisOS security policy. Current defaults include auto-approved read/edit/browser/MCP while safe-command execution is disabled by default. JarvisOS/OpenShell should therefore decide authority; Cline should perform coding work inside that boundary.

Useful lifecycle detail: session shutdown/replacement is serialized per session identity so stale cleanup cannot kill a successor session.

**Candidate integration:** `Jarvis coding adapter -> @cline/sdk`, optionally inside OpenShell. Do not automate the VS Code UI when the SDK already exposes the runtime.

## Phase 2 findings — provider/local inference stack

### LiteLLM — MIT community subset, mixed repository

Current root license explicitly says content outside `enterprise/` is MIT while `enterprise/` has separate terms. JarvisOS may therefore evaluate/integrate the community/core boundary directly, but dependency/SBOM checks must prevent accidental enterprise-tree incorporation.

Community router code already includes model groups, simple-shuffle/least-busy/usage/latency routing, per-error retry policy, cooldown/fail counts, fallbacks, context-window fallbacks, budgets and higher-level routing knobs.

**Role:** provider/API gateway only. JarvisOS must own egress/local-first policy and must never inherit implicit cloud fallback merely because LiteLLM can perform fallback.

### BerriAI sibling findings

`BerriAI/ai-gateway-bench` is MIT and directly reusable as a benchmark harness. It isolates gateway overhead with a deterministic local mock and tests TTFT/chunk jitter, tool-call delta reassembly, 1k/10k/100k context, concurrency/tail latency, invalid-key flood rejection, failover overhead, head-of-line blocking and memory/RSS. Use it to qualify LiteLLM or any Jarvis provider gateway instead of inventing an ad hoc benchmark.

`BerriAI/self-improving-agent` is MIT and implements a useful but bounded proposal workflow: externally approved proposal -> exact-one snippet replacement -> feature branch -> commit -> push -> draft PR, with path containment and one-shot git auth. Its apply function explicitly does not validate user approval and does not make deterministic tests/verifiers mandatory before push. Treat as a B-grade proposal-to-draft-PR component/reference, not as JarvisOS's promotion gate.

Other BerriAI sibling candidates queued: `lite-agents`, `litellm-agent-sdk`, `litellm-agent-runtime`, PR-review agents and skills. Audit only if they add capability beyond Cline/Hermes/Agentic API.

### vLLM core

Apache-2.0. Tool parsing is a real extensible registry with model-specific parsers, streaming state and structured decoding for required/named tool choice when a schema can be derived. This is strong for local tool-calling models. CPU offload exists in current runtime configuration.

**Role:** high-throughput/local GPU serving backend, especially for a future GPU server; compare consumer-laptop behavior with llama.cpp/Ollama before standardizing.

### vLLM Agentic API — top-tier discovery

`vllm-project/agentic-api` is Apache-2.0 and is designed as a stateful agentic API in front of vLLM. It supports Responses-style state hydration, SQLite persistence, server-side tool loops, HTTP/SSE/WebSocket, background work and compatibility surfaces for Codex and Claude Code.

The tool-ownership boundary is enforced in code: gateway-executable handlers are separate from client-owned function declarations; unregistered tool names classify as client-owned rather than becoming executable; dispatch executes only registered gateway handlers; name collisions fail configuration.

**Candidate stack:** `Codex/Claude Code/Cline client -> Agentic API -> vLLM/open model`, with JarvisOS/OpenShell retaining OS/filesystem authority. This may materially reduce cloud coding-credit consumption while keeping mature coding-client interfaces.

### GuideLLM

`vllm-project/guidellm` is Apache-2.0 and provides SLO-oriented load/latency benchmarking across OpenAI-compatible endpoints and in-process vLLM. It supports TTFT/ITL/E2E, multiple request/load profiles, real/synthetic/multimodal datasets, tool calling and machine-readable reports.

**Role:** reusable qualification harness for local serving backends; do not fold benchmark logic into JarvisOS unnecessarily.

### vLLM Semantic Router

Apache-2.0 and feature-rich: model selection plus keyword/embedding/domain/fact/feedback/language/context/complexity/modality/authz/jailbreak/PII signals, prompt guards, semantic cache/memory and rate limit.

**Disposition:** A-/PARKED. It becomes more compelling for a multi-user/multi-GPU gateway, but today it overlaps Jarvis authority/evidence/routing and LiteLLM. Do not add a broad dependency merely because it is permissive.

### llama.cpp

MIT. Particularly valuable current mechanism: auto-parser analyses the model's own chat template to derive reasoning/content/tool-call formats, then generates parser/grammar constraints rather than requiring a hand-coded parser for every model family. It recognizes JSON-native, tag+JSON and tag+parameter formats including Qwen/Hermes-style shapes.

**Role:** strong consumer/local quantized runtime candidate. This can reduce per-model integration work when Jarvis tests Qwen/GLM/Kimi/Hermes-like local models.

Relevant ggml siblings queued: `whisper.cpp` (high value for local STT), `ggml`, `Llama-Windows`, `llama.vscode`, `llama-connect`.

### Ollama

MIT. Its scheduler adds model/runner lifecycle management above low-level inference: resident-runner reuse, bounded queue, concurrency based on GPU availability, memory refresh/fit calculation, controlled eviction and one-shot OOM evict-all/retry behavior.

**Role:** operational local model lifecycle/scheduler. Provisional division:

- llama.cpp = low-level/quantized local runtime;
- Ollama = lifecycle/scheduler/deployment UX;
- vLLM = high-throughput serving + mature tool/structured output.

Do not assume one universal backend. JarvisOS may benefit from one `LocalModelRuntime` adapter contract with different backends per machine/task.

## Phase 3 findings — training/eval/distributed provenance

### Harbor Framework

`harbor-framework/harbor` is Apache-2.0 and current. It is the official harness for Terminal-Bench 2.0, evaluates arbitrary agents including Claude Code/OpenHands/Codex, supports custom benchmarks/environments, can parallelize large environment sets and generates RL rollouts.

**Disposition:** top candidate for the common agent/engineering evaluation harness. Compare directly against NVIDIA-NeMo Gym, Hugging Face Lighteval and TextArena before JarvisOS creates a new evaluation framework.

### TorchTitan / PyTorch siblings

`pytorch/torchtitan` is BSD-3-Clause and a PyTorch-native large-model training platform. It is relevant later to specialist training, not immediate Jarvis runtime.

A relevance-scoped PyTorch sibling scan identified `pytorch/ao` as the strongest quantization/low-bit candidate and `pytorch/executorch` as the strongest edge/on-device inference candidate. Queue both for Wave B/C; most other search hits were generic or archived.

### Hugging Face family

Nous forks currently resolve to at least `huggingface/nanotron` (Apache-2.0), `huggingface/lighteval` (MIT) and `huggingface/datatrove` (Apache-2.0). This justifies a dedicated Hugging Face sibling scan across evaluation, inference/quantization, data pipelines and agent tooling instead of treating each fork separately.

### Axolotl

`axolotl-ai-cloud/axolotl` is Apache-2.0 and active. The old Nous `axolotl-func-calling` fork should not be the integration target; evaluate current upstream Axolotl as a training/fine-tuning backend when an engineering specialist reaches implementation readiness.

### TextArena

`TextArena/TextArena` is MIT and active, providing competitive text-game environments for LLM evaluation/RL. Compare its environment API and reward semantics with Harbor/Gym; likely useful as an environment source/reference, not Jarvis authority/runtime.

### Iroh family

`n0-computer/iroh` is Apache-2.0 and current. It provides QUIC + NAT traversal keyed by identities rather than assuming stable IP endpoints. Potential future use: secure/direct worker or BlueRev edge-node connectivity where NAT/mobile networks make static endpoints fragile. Audit sibling `iroh-blobs`/`iroh-gossip` with this family rather than independently.

### Miscellaneous lower-priority resolved upstreams

- `joonspk-research/generative_agents` — Apache-2.0, historically important but old and lower value than current Jarvis task-memory/agent references. Sibling scan found mainly related research/course repos, no stronger runtime component.
- `shroominic/funcchain` — MIT, minimalist Python cognitive/function-chaining framework; likely superseded by Hermes/Cline/LiteLLM for JarvisOS.
- `vadimdemedes/ink` — MIT, strong interactive CLI UI library but not core architecture; only relevant if Jarvis ships a rich Node/React CLI.
- `NVIDIA-NeMo/Megatron-Bridge` — Apache-2.0, training library with bidirectional Hugging Face conversion; keep in specialist-training wave.
- `NVIDIA/Megatron-LM` — current GitHub metadata is not a simple permissive SPDX classification; exact license/component boundary must be reviewed before reuse.
- `Orion-zhen/abliteration` — GPL-3.0; reference-only for the proprietary JarvisOS core unless a separately distributed/process-isolated use is legally and architecturally justified.

## Relevant sibling-organization queues already discovered

### Microsoft

High-interest sibling candidates from relevance-scoped search: `microsoft/agent-framework`, `agent-lightning`, `autogen`, `UFO`, `OmniParser`, `TypeAgent`, `WindowsAgentArena`, `agent-host-protocol`, `magentic-ui`, `semanticworkbench`, `PromptWizard`. Prioritize `agent-host-protocol`, `UFO`, `OmniParser`, `agent-lightning` and `agent-framework` because they are most likely to add non-overlapping primitives.

### NVIDIA / NVIDIA-NeMo

High-interest siblings: `NeMo-Agent-Toolkit`, `SkillSpector`, `SkillEvaluator`, `NeMo-Relay`, `OpenShell-Community`, `game-agent-sdk`, `context-aware-rag`, plus Gym/RL/Automodel/Nemotron/Megatron-Bridge already in the fork provenance graph. Prioritize agent toolkit, skill evaluation and OpenShell ecosystem before generic model-training infrastructure.

### Cline

High-interest siblings: `cline-bench`, `plugins`, `mcp-marketplace`, `skills`, `sdk-skill`, `prompts`. Audit benchmark/plugin contracts before re-implementing coding-agent extension mechanisms.

### vLLM Project

Already opened `agentic-api`, `guidellm`, `semantic-router`; `speculators` was already known. Remaining potentially relevant siblings include `vllm-omni` and `aibrix` only if deployment needs justify them.

### BerriAI

Already opened LiteLLM core, `ai-gateway-bench`, `self-improving-agent`. Remaining siblings only if non-overlapping: `lite-agents`, `litellm-agent-sdk`, `litellm-agent-runtime`, review agents and skills.

### ggml-org

Prioritize `whisper.cpp`; then evaluate `Llama-Windows` only for deployment learnings. Core `ggml` matters indirectly through llama.cpp.

### Ollama

No separate sibling repository discovered that currently adds a stronger Jarvis-specific primitive than `ollama/ollama` itself.

### PyTorch

Prioritize `pytorch/ao` and `pytorch/executorch` after current inference/runtime wave.

### Hugging Face / Axolotl / n0-computer / Harbor

Dedicated sibling scans remain queued. They were added because multiple resolved Nous forks converge on these upstream organizations.

## Resume checkpoint

Next work should continue from this exact checkpoint:

1. continue provenance resolution at fork #27 `DeepEP`, then #28 `jedi`, #29 `logfire-rust`, #30 `tch-rs`, #31 `yellowstone-grpc`;
2. resolve #32/#35 iroh family, #33 Hugging Face hub, #34 second `harbor`, then #36-49;
3. during provenance resolution, code-first only newly discovered permissive upstreams that are immediately agent/runtime/eval relevant; otherwise queue them;
4. after all 49 are resolved, perform sibling scans for new original authors/orgs not already covered: Hugging Face, Axolotl AI Cloud, n0-computer, Harbor Framework, TextArena, PyTorch and any new sources from #27-49;
5. then compare the strongest integration stack candidates experimentally rather than stacking all of them: OpenShell vs alternatives for sandbox; Cline/Hermes for coding worker; LiteLLM vs minimal Jarvis adapter for provider gateway; vLLM/llama.cpp/Ollama for local serving; Harbor/Gym/Lighteval for engineering eval;
6. promote direct-dependency candidates only through a governing spec/ADR when implementation is authorized.
