# Upstream author ecosystem audit — continuation 3 — 2026-08-19

Status: audit checkpoint; documentation only; **not implementation authority**  
Parent register: `docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`  
Prior continuation: `docs/audits/UPSTREAM_AUTHOR_ECOSYSTEM_AUDIT_CONTINUATION_2026-08-19.md`

## Scope of this continuation

This checkpoint closes the remaining high-value training/data/distributed systems wave and resolves the material provenance gaps left in the original 49-fork Nous Research map. It also records several earlier discoveries from the same uninterrupted audit pass that had not yet been persisted after the prior checkpoint.

The selection rule remains: prefer a maintained permissively licensed upstream component when it materially solves a JarvisOS problem; do not add frameworks merely because they are capable. Product authority, security policy and execution authority remain JarvisOS concerns even when a worker/runtime is reused.

## A. Browser and authenticated computer-use boundary

### `anomalyco/browser-control` — top-tier transactional browser candidate

MIT. Code-first inspection found a materially stronger stale-reference behavior than the earlier Vercel `agent-browser` path:

- the snapshot-ref registry is cleared on frame navigation;
- snapshot capture fails when the page navigates during capture;
- refs are rejected when the page/URL no longer matches the captured state;
- element lookup is reconstructed from the captured selector and ARIA role rather than deliberately re-resolving a stale semantic ref to a fresh lookalike element.

**Disposition:** `DIRECT_DEPENDENCY` candidate for the authenticated/transactional browser worker, inside Jarvis/OpenShell authority. Retain a Jarvis-level page/snapshot epoch for sensitive mutations, including dynamic same-page mutations that do not cause navigation.

`vercel-labs/agent-browser` remains useful as a general browser worker, but its stale-node fallback behavior is not strong enough to be the sole grounding guarantee for high-risk actions.

### `anomalyco/terminal-control` — terminal/UI evidence worker

MIT. Provides persistent PTYs, semantic snapshots, pane/workspace identity, state-based waiting rather than sleeps, screenshots/evidence, MCP and a TypeScript client.

**Disposition:** strong candidate for terminal/UI-test capability implementation. Execute underneath OpenShell/Jarvis authority rather than treating the terminal worker itself as a sandbox.

## B. Runtime / agent-framework bake-off additions

### `deepseek-ai/deepseek-harness` — S-tier runtime candidate

MIT. The architecture separates model adapters, tool registry, session log, agent loop, sandbox, approvals, credentials and telemetry into replaceable plugins. The append-only session log is the source of model-visible context and enforces the useful invariant that model-visible material must be logged.

Code inspection confirmed a fail-closed tool/approval path and one-shot escalation semantics: broader sandbox permissions require non-empty justification and approval before execution; missing approval service/agent, rejection, cancellation or unavailable state fail rather than silently executing.

Its native sandbox should **not** replace OpenShell: the inspected sandbox documentation scopes its guarantee primarily to filesystem confinement rather than comprehensive network/process/syscall/device/credential isolation.

**Candidate composition:** `DeepSeek Harness authority/runtime mechanics -> OpenShell hard isolation`.

### Prime Intellect `verifiers` v1 — S-tier evaluation/RL harness

MIT. The current project is now under `PrimeIntellect-ai/verifiers` and v1 is explicitly organized around:

- `Taskset`;
- `Harness` (Codex, Claude Code, mini-swe-agent, custom harnesses);
- `Agent = harness × model × runtime policy`;
- `Environment`;
- MCP `Toolset`;
- rich `Trace` with rewards, metrics, errors and per-model-call telemetry.

It includes native Harbor taskset support. Particularly valuable behavior:

- Harbor network policy can be applied to agent runtimes;
- artifacts/collect hooks are treated as grading inputs;
- a failing collect hook fails the rollout rather than grading a silently stale artifact state;
- a verifier can run in a separate fresh environment that the solver never touched;
- verifier-infrastructure failure is not silently converted into reward zero.

**Disposition:** S-tier candidate for the common `Jarvis Engineering Bench` harness above Harbor/TB-Science. This may be a cleaner long-term eval/RL layer than a bespoke Jarvis wrapper around Harbor.

### `PrimeIntellect-ai/prime-rl` — A+/S future agentic-RL stack

Apache-2.0. Native integration with `verifiers`; end-to-end SFT/RL/eval; vLLM/FSDP2; LoRA; multimodal and large MoE support; async RL and large-scale deployment.

The project includes single-GPU debug/basic paths, but the complete RL reference stack is naturally multi-GPU and the system is designed to scale far beyond current Jarvis hardware.

**Disposition:** future unified `eval -> agentic RL` backend after the first engineering adapter experiments. Do not make it the first fine-tuning path merely because it is comprehensive.

### `axon-rl/gem`

Apache-2.0. A framework-agnostic Gym-like environment suite for agentic LLM online RL, with async vectorized environments, tool wrappers, MCP and integrations with OAT/verl/other trainers.

**Disposition:** A environment-library/interoperability reference. Harbor/Verifiers remains more directly aligned with real engineering/tool/artifact verification.

## C. Training stack — concrete hierarchy

### `axolotl-ai-cloud/axolotl` — S training appliance

Apache-2.0. Current feature set covers modern Qwen/GLM model families, LoRA/QLoRA, QAT, GRPO/GDPO, multimodal/MoE paths and integrations with Liger/torchAO.

**Role:** preferred first appliance for a reproducible engineering-specialist adapter when the target model/hardware path is supported.

### Hugging Face `TRL + PEFT + Accelerate` — core primitive toolbox

All permissive. Most important connection found in the audit: TRL has direct Harbor integration, allowing a Harbor suite to supply dataset/environment/reward functions to GRPO. PEFT supplies LoRA/adapter composition and Accelerate handles device/offload/distributed mechanics.

**Role:** shortest explicit `Harbor verifier -> reward -> adapter training` path when Axolotl's higher-level configuration is too restrictive.

### `LinkedIn/Liger-Kernel`

BSD-2-Clause. Triton kernels and model patching for common transformer operations; Qwen support; convergence tests.

**Role:** optional measured training accelerator below Axolotl/TRL/PEFT, not a required framework.

### `NVIDIA-NeMo/RL` — A+/S future distributed agentic training

Apache-2.0 and actively developed. Current support includes Qwen3.5/GLM-family GRPO, LoRA GRPO, multi-turn tool-use RL, async RL, NeMo-Gym, vLLM/SGLang/Megatron rollout backends, DTensor and Megatron training backends.

Its useful architectural primitive is the explicit `RL Actor` abstraction: each policy trainer, inference engine, reward environment or critic is separately resourced, isolated, coordinated and connected. Ray virtual clusters/worker groups let the same algorithm scale from small experiments to large distributed runs.

**Disposition:** later-stage training system when Jarvis moves from one adapter to heterogeneous distributed agentic rollouts. Too heavy for the first engineering LoRA.

### `NVIDIA-NeMo/Automodel` — A+/future; notable Qwen3.8 support

Apache-2.0. PyTorch Distributed/DTensor-native fine-tuning with broad current HF model coverage. On 2026-08-14 upstream added full-parameter SFT and LoRA support for `Qwen/Qwen3.8-27B`.

The published Qwen3.8-27B LoRA recipe uses `--nproc-per-node 8`, BF16 and FSDP2 with activation checkpointing. This is useful evidence that Qwen3.8 is already a first-class training target, but the reference recipe is not a practical Predator-laptop fine-tuning plan.

**Disposition:** candidate when access to multi-GPU training exists; not the immediate local adapter path.

### `NVIDIA-NeMo/Megatron-Bridge` — A future cluster/model-conversion layer

Apache-2.0. Provides HF <-> Megatron conversion/verification plus pretraining/SFT/LoRA for very large dense/MoE/multimodal models.

**Disposition:** valuable for future large-model training/checkpoint conversion; no current need in Jarvis laptop runtime.

### `pytorch/torchtitan` — A research/distributed reference

BSD-3-Clause. Clean PyTorch-native distributed training with FSDP2/TP/PP/CP, checkpointing, Float8/MXFP8, debugging and structured logs. Current 2026 development also includes experimental `TitanRL`.

**Disposition:** reference and possible future training substrate, but it does not beat Axolotl/TRL for the first specialist adapter or NeMo for later heterogeneous agentic training. Reference usage is strongly multi-GPU/nightly-PyTorch oriented.

### `huggingface/nanotron` — A-/cluster pretraining reference

Apache-2.0. Explicit DP/TP/PP + expert parallelism and an educational/scalable pretraining stack.

**Disposition:** useful learning/performance reference, but redundant for Jarvis compared with the training paths above.

### `OAT` and Agent Lightning

Prior findings retained: OAT is a strong Apache online-RL Actor/Learner/Oracle runtime; Agent Lightning remains a useful decoupled rollout/training layer. Neither should be made mandatory until a concrete training experiment demonstrates an advantage over `Verifiers/Harbor + TRL/Axolotl`.

## D. Training-data pipeline

### `huggingface/datatrove` — A+/S future engineering data layer

Apache-2.0. This is one of the strongest late discoveries for BlueRev/Jarvis training work.

It offers platform-agnostic processing pipelines that run locally, under Slurm or Ray, with:

- readers/writers/extractors/filters/stats/token blocks;
- MinHash deduplication;
- sentence-level exact deduplication;
- exact-substring/decontamination workflows;
- synthetic-data generation/inference pipelines;
- fsspec local/remote storage;
- task sharding and completion markers so failed jobs can resume only incomplete shards.

**Disposition:** strong direct-dependency candidate for building future engineering corpora from manuals, reports, papers, code and synthetic trajectories. Jarvis should not build a bespoke large-scale ETL/dedup framework.

## E. Distributed MoE / cluster transport

### `deepseek-ai/DeepEP`

MIT. High-performance expert-parallel communication for MoE dispatch/combine, including FP8 and a V2 `ElasticBuffer`; focused on Hopper/SM90, NVLink and RDMA-scale deployments.

**Disposition:** A future cluster-only component. Irrelevant to current Predator hardware; revisit if Jarvis/BlueRev runs distributed Qwen/GLM/DeepSeek-class MoE serving or training.

### `SalesforceAIResearch/LeastLoadedEP`

Apache-2.0 in GitHub metadata; README also labels the repository research-purpose oriented. Dynamically spills overloaded expert work/parameters to less loaded devices while preserving the model's logical routing.

**Disposition:** research/future multi-GPU MoE reference, not current dependency.

### `NVIDIA/nccl-tests` and `HLC-Lab/pico`

`nccl-tests` is BSD-3-Clause and remains the canonical low-level NCCL qualification tool. PICO has a mixed per-component permissive provenance and is more useful as a reproducibility/metadata/tracing harness across collective communication tests.

**Disposition:** future cluster qualification, not product runtime.

## F. Model/runtime side findings retained from this tranche

### `torchAO` vs Optimum-Quanto

`torchAO` is the current preferred PyTorch quantization/QAT primitive; `optimum-quanto` was explicitly placed into maintenance mode by upstream. Do not start new core integration work around Quanto.

### ExecuTorch

BSD and relevant for edge/mobile/appliance deployment. Desktop CUDA remained experimental in the audited state, so it is not a llama.cpp/vLLM replacement for the Predator. Revisit for future mobile/Raspberry/embedded Jarvis clients.

### Candle and `xn`

Candle is a strong dual-permissive embedded Rust multimodal runtime candidate for small standalone STT/vision/embedding/TTS capabilities. `xn` is an early inference-first Rust framework and should remain experimental until maturity improves.

### `xn-ptts`

Dual MIT/Apache wrapper/runtime with Rust/Python/WASM/WebSocket surfaces and audio-reference voice conditioning. Strong experimental local-TTS candidate. The exact Pocket TTS model-weight license must be audited separately before bundling weights; wrapper code license must not be assumed to govern model checkpoints.

### DeepSeek OCR-2

Apache repository and strong candidate for local document-ingest/OCR/layout-to-Markdown experiments. The exact model checkpoint license must still be verified separately before redistribution/bundling.

## G. Skill/plugin admission and lifecycle plane

Prior findings retained as top-tier:

- `NVIDIA/SkillSpector` — admission scanner; installation should fail if risk threshold is exceeded, scan fails or files remain wholly uninspected;
- `NVIDIA/SkillEvaluator` — quality/live evaluation, including Harbor reuse;
- `NVIDIA/NeMo-Relay` — lifecycle/trajectory/guardrail plane;
- `NVIDIA/OpenShell` — hard execution boundary.

Target layering remains:

`candidate skill/plugin -> SkillSpector -> SkillEvaluator/tests -> human/policy approval -> CapabilityRegistry -> NeMo Relay lifecycle -> OpenShell execution`.

Generated/distilled skills (e.g. ToolLibGen-style extraction from successful trajectories) must never bypass this admission pipeline.

## H. Residual provenance closure from the original Nous 49-fork map

The remaining material `PENDING` entries are now resolved:

- `NousResearch/logfire-rust` -> `pydantic/logfire-rust`, MIT. Same Pydantic ecosystem already audited; no new Jarvis component required.
- `NousResearch/yellowstone-grpc` -> `rpcpool/yellowstone-grpc`, AGPL-3.0. Solana-specific and out of Jarvis scope; no integration.
- `NousResearch/hf-hub` -> `huggingface/hf-hub`, Apache-2.0. Useful only if a Rust Jarvis component needs a small HF Hub client; otherwise ordinary HF tooling suffices.
- `NousResearch/wterm` -> `vercel-labs/wterm`, Apache-2.0. Web-terminal UI primitive only; lower priority than `terminal-control` for actual agent/test lifecycle.
- `NousResearch/lm-evaluation-harness-pretraining` -> `EleutherAI/lm-evaluation-harness`, MIT. Same upstream already audited; not a distinct framework.
- `NousResearch/harbor` -> `harbor-framework/harbor`, Apache-2.0. Confirms the earlier Harbor attribution; not a second Harbor project.
- `NousResearch/curve25519-dalek` -> `dalek-cryptography/curve25519-dalek`. Treat crypto as a maintained upstream dependency through higher-level components rather than implementing Jarvis crypto primitives.
- `NousResearch/image-size` traces through a security-patched intermediate fork to `image-size/image-size`, MIT. No architecture value, but reinforces the supply-chain rule that small parsers handling untrusted files deserve bounds/fuzzing/sandbox review.

The remaining writing/EQ benchmarks were also resolved during the prior continuous pass: permissive components such as Judgemark can be used to qualify LLM judges; repositories with missing or conflicting licenses stay `REFERENCE_ONLY`.

## I. Updated recommended architecture / adoption order

### Near-term integration candidates

1. **Canonical Capability Registry + Microsoft governance semantics** — authority remains Jarvis-owned.
2. **OpenShell** — hard worker sandbox/isolation.
3. **DeepSeek Harness / Pydantic / Hermes bake-off** — choose the runtime/tool-loop substrate empirically rather than stacking all three.
4. **Cline SDK** — coding worker, not authority.
5. **`browser-control`** — authenticated/transactional browser worker; `agent-browser` remains a lower-risk/general browser worker candidate.
6. **UFO + AIRI-style snapshot epoch** — Windows computer-use worker and safety preflight.
7. **terminal-control** — persistent PTY/test/evidence worker.
8. **SkillSpector + SkillEvaluator** — admission quality/security gate for third-party skills/plugins.
9. **models.dev + LiteLLM community gateway + Jarvis local-first egress policy** — model metadata/provider abstraction without delegating cloud policy.
10. **Verifiers v1 + Harbor/TB-Science** — common engineering agent benchmark/eval harness.

### First engineering-model training experiment

Preferred order:

1. curated engineering corpus/trace set with **DataTrove**;
2. **Harbor/Verifiers** deterministic tasks/verifiers;
3. base open model selected from local-serving benchmark results;
4. **Axolotl** LoRA/QLoRA first if supported;
5. otherwise **TRL + PEFT + Accelerate**, with Harbor reward integration;
6. optionally Liger/torchAO if benchmarked gains justify them;
7. evaluate via the same Harbor/Verifiers suite before promotion.

Only after this should Jarvis consider Prime-RL, OAT, NeMo RL, Megatron-Bridge or other larger distributed stacks.

### Explicit non-goals

- no custom Jarvis training framework;
- no custom vector/data ETL framework if DataTrove suffices;
- no custom cryptography;
- no reliance on agent/plugin hook layers as hard sandbox boundaries;
- no automatic local->cloud fallback;
- no automatic generated-skill installation;
- no code reuse from missing/unclear/noncommercial licenses merely because a concept is attractive.

## Checkpoint conclusion

The upstream expansion has now reached diminishing returns for the original Nous-fork provenance set. The useful result is no longer a longer repository list but a much smaller set of replaceable, licensed components with explicit roles and boundaries.

Next audit work should therefore be demand-driven: when a JarvisOS spec reaches one of these capability areas, perform a focused current-version bake-off and integration/security review against the short-listed upstreams rather than continuing broad repository collection indefinitely.
