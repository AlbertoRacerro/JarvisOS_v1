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

For huge upstream organizations such as Microsoft, NVIDIA, NVIDIA-NeMo, Hugging Face and vLLM, "audit the author's other repositories" means a complete relevance-scoped inventory across:

- agents, tool use, MCP/plugins, sandboxing, identity/governance and policy;
- coding agents, IDE/CLI automation, browser/computer use;
- local inference, serving, quantization, model routing and model lifecycle;
- evaluation, RL/training, reasoning, data pipelines and distributed execution;
- engineering/CAD/simulation or infrastructure directly useful to JarvisOS/BLUECAD.

After inventory, code-first audit only non-redundant candidates with material value. Unrelated repositories are recorded as out of scope rather than mechanically read.

## Complete current Nous fork queue

The following 49 fork names are the current `fork:only` result set and define the resumable queue. Upstream fields marked `PENDING` must be resolved from repository metadata before attribution.

| # | Nous fork | Verified upstream | Upstream license / status | Audit state |
|---:|---|---|---|---|
| 1 | `llm-abliteration` | PENDING | PENDING | QUEUED |
| 2 | `agent-governance-toolkit` | `microsoft/agent-governance-toolkit` | MIT | CODE-FIRST STARTED |
| 3 | `NemoClaw` | `NVIDIA/NemoClaw` | Apache-2.0 | CODE-FIRST STARTED |
| 4 | `torchtitan` | PENDING | PENDING | QUEUED |
| 5 | `Gym` | `NVIDIA-NeMo/Gym` | Apache-2.0 | CODE-FIRST STARTED |
| 6 | `local_generative_agents` | PENDING | PENDING | QUEUED |
| 7 | `Automodel` | `NVIDIA-NeMo/Automodel` | Apache-2.0 | UPSTREAM VERIFIED |
| 8 | `RL` | `NVIDIA-NeMo/RL` | Apache-2.0 | UPSTREAM VERIFIED |
| 9 | `Nemotron` | PENDING | PENDING | QUEUED |
| 10 | `OpenShell` | `NVIDIA/OpenShell` | Apache-2.0 | CODE-FIRST STARTED |
| 11 | `harbor-fork` | PENDING | PENDING | QUEUED |
| 12 | `cline` | `cline/cline` | Apache-2.0 | UPSTREAM VERIFIED; CODE AUDIT NEXT |
| 13 | `axolotl-func-calling` | PENDING | PENDING | QUEUED |
| 14 | `litellm` | `BerriAI/litellm` | GitHub reports Other/NOASSERTION; license text must be audited | LICENSE REVIEW NEXT |
| 15 | `nanotron` | PENDING | PENDING | QUEUED |
| 16 | `funcchain` | PENDING | PENDING | QUEUED |
| 17 | `lighteval` | PENDING | PENDING | QUEUED |
| 18 | `datatrove` | PENDING | PENDING | QUEUED |
| 19 | `vllm` | `vllm-project/vllm` | Apache-2.0 | UPSTREAM VERIFIED; CODE AUDIT NEXT |
| 20 | `iroh` | PENDING | PENDING | QUEUED |
| 21 | `nous-llama.cpp` | `ggml-org/llama.cpp` | MIT | UPSTREAM VERIFIED; CODE AUDIT NEXT |
| 22 | `OpenShell-Community` | PENDING | PENDING | QUEUED |
| 23 | `Megatron-LM` | PENDING | PENDING | QUEUED |
| 24 | `TextArena` | PENDING | PENDING | QUEUED |
| 25 | `ink` | PENDING | PENDING | QUEUED |
| 26 | `Megatron-Bridge` | PENDING | PENDING | QUEUED |
| 27 | `DeepEP` | PENDING | PENDING | QUEUED |
| 28 | `jedi` | PENDING | PENDING | QUEUED |
| 29 | `logfire-rust` | PENDING | PENDING | QUEUED |
| 30 | `tch-rs` | PENDING | PENDING | QUEUED |
| 31 | `yellowstone-grpc` | PENDING | PENDING | QUEUED |
| 32 | `iroh-blobs` | PENDING | PENDING | QUEUED |
| 33 | `hf-hub` | PENDING | PENDING | QUEUED |
| 34 | `harbor` | PENDING | PENDING | QUEUED |
| 35 | `iroh-gossip` | PENDING | PENDING | QUEUED |
| 36 | `longform-writing-bench` | PENDING | PENDING | QUEUED |
| 37 | `Liger-Kernel` | PENDING | PENDING | QUEUED |
| 38 | `ollama` | `ollama/ollama` | MIT | UPSTREAM VERIFIED; CODE AUDIT NEXT |
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
5. upstreams of `local_generative_agents`, `funcchain`, `TextArena`, `OpenShell-Community`, `wterm`
6. relevance-scoped scans of Microsoft, NVIDIA, NVIDIA-NeMo and Cline organizations for sibling agent/security/coding projects

### Wave B — local inference and provider abstraction

1. `BerriAI/litellm` license split and code audit
2. `vllm-project/vllm` + `vllm-project/speculators`
3. `ggml-org/llama.cpp`
4. `ollama/ollama`
5. upstreams of `Nemotron`, `nanotron`, `hf-hub`, `llm-abliteration`
6. sibling-repository scans of BerriAI, vLLM, ggml-org, Ollama and relevant model-runtime organizations

### Wave C — engineering-specialist training and evaluation

1. `NVIDIA-NeMo/Gym`
2. `NVIDIA-NeMo/RL`
3. `NVIDIA-NeMo/Automodel`
4. upstreams of `torchtitan`, `Megatron-LM`, `Megatron-Bridge`, `Liger-Kernel`, `DeepEP`
5. upstreams of `lighteval`, `lm-evaluation-harness-pretraining`, `eqbench3`, `openai-evals`, writing benchmarks
6. compare with Nous Atropos/Nomos/toolperf/compression-eval so JarvisOS does not adopt duplicate frameworks unnecessarily

### Wave D — data, distributed systems and lower-priority infrastructure

Audit `datatrove`, `iroh` family, `pico`, `nccl-tests`, `LeastLoadedEP`, crypto/network bindings and remaining forks. Promote only mechanisms that materially improve local/distributed JarvisOS, BlueRev edge workers, offline resilience or model infrastructure.

## Phase 1 findings

### Microsoft Agent Governance Toolkit — high-value direct-reuse candidate

Upstream is MIT. Current Python policy implementation includes:

- schema-versioned YAML/JSON policy documents;
- lifecycle stages `pre_input`, `pre_tool`, `post_tool`, `pre_output`;
- `allow`, `deny`, `warn`, `require_approval`, `log` actions;
- validated rate-limit syntax;
- bounded expression parsing and fail-closed behavior on evaluation errors;
- hierarchical `extends` with cycle/path-traversal protection;
- additive-only inheritance: child policy cannot weaken an inherited deny;
- separate execution-context enforcement for `inner_loop`, `ci_cd`, and `autonomous` runtime.

Current package consolidation exposes `agent-governance-toolkit-core` 5.0.0 (Python >=3.11, MIT), but that core is broad and force-includes policy, runtime, hypervisor and mesh source trees plus a non-trivial dependency set. Integration decision therefore remains open between an official narrow package/module and the consolidated core.

Important caveat: one inspected trust evaluator returns allow if no policies are loaded. Any JarvisOS integration must enforce its own fail-closed bootstrap invariant rather than inherit an accidental no-policy allow state.

**Current disposition:** `DIRECT_DEPENDENCY` candidate if a narrow supported package surface can provide the required policy/identity primitives; otherwise consider a tracked `VENDORED_COMPONENT` of compatible upstream modules before rewriting them.

### NVIDIA OpenShell — high-value sandbox runtime candidate

Upstream is Apache-2.0. Code inspection confirms a real sandbox boundary rather than a prompt-level permission system:

- typed filesystem allowlists (`read_only`, `read_write`, optional workdir write access);
- network mode defaults to `Block`, with explicit `Proxy` and `Allow` modes;
- Landlock compatibility can be best-effort or hard-required;
- separate run-as user/group;
- Linux seccomp filtering blocks fileless execution primitives, `ptrace`, BPF, cross-process memory access, `io_uring`, mount APIs, namespace-manipulation paths and dangerous socket domains/flags;
- provider/inference profiles separate provider credential discovery from request-time credential/header use.

OpenShell should therefore be evaluated as a real `DIRECT_DEPENDENCY` / external runtime for autonomous coding and tool execution, especially Hermes and other local coding agents, rather than recreated in JarvisOS. Remaining checks: Windows/WSL deployment model, process/container overhead, policy control from JarvisOS, local inference route support, update cadence and trust boundary around credentials.

### NVIDIA NemoClaw — agent packaging/orchestration over OpenShell

Upstream is Apache-2.0 and now explicitly supports Hermes among its agent ecosystem. Its policy layer manages built-in/agent-specific presets, validates sandbox policies, protects policy ownership/baseline transitions, previews network endpoints and contains guards against network-policy bypass shapes such as arbitrary `allowed_ips`.

This is more likely useful as an integration/reference layer **on top of OpenShell** than as JarvisOS's central authority system. Audit continues before deciding whether to depend on NemoClaw itself or use OpenShell directly with JarvisOS-owned orchestration.

### NVIDIA-NeMo Gym — evaluation/training environment candidate

Upstream is Apache-2.0. Initial inspection confirms active environment/resource-server and remote-agent surfaces, including MCP-oriented resources. This is the likely maintained successor/reference to compare against archived Nous Atropos for a future engineering-specialist environment. Full code-first environment/reward/trajectory/verifier audit remains queued in Wave C after the sandbox/runtime path.

### Confirmed high-priority permissive upstreams for next phase

- `cline/cline` — Apache-2.0; audit coding-agent task loop, approvals, checkpoints, terminal/browser/MCP, diff/edit model and SDK boundaries.
- `vllm-project/vllm` — Apache-2.0; audit serving engine, scheduler/KV/cache, structured output/tool parsing, local endpoint integration and consumer-hardware relevance.
- `ggml-org/llama.cpp` — MIT; audit local server API, GGUF/model lifecycle, quantization/runtime controls, embeddings/tool/chat template support and Windows/GPU deployment.
- `ollama/ollama` — MIT; audit model lifecycle, local server, scheduler/runner management, Modelfile/config and whether it should be a JarvisOS local-runtime adapter rather than duplicated logic.
- `BerriAI/litellm` — current GitHub metadata reports `Other/NOASSERTION`; do **not** assume permissive reuse until exact current license files and component split are audited.

## Resume checkpoint

Next code-first work should continue in this exact order unless a new urgent repository appears:

1. finish OpenShell/NemoClaw integration-boundary audit;
2. code-first audit `cline/cline` and scan other Cline organization repos;
3. inspect current LiteLLM license split, then provider/router code only if compatible;
4. code-first audit vLLM + sibling `speculators` and other relevant vLLM-project repos;
5. code-first audit llama.cpp + relevant ggml-org sibling repos;
6. code-first audit Ollama + relevant Ollama sibling repos;
7. return to NVIDIA-NeMo Gym/RL/Automodel for engineering-specialist training/eval;
8. resolve remaining PENDING upstream provenance from the 49-fork table and process Waves C/D.
