# Core software ecosystem audit — continuation 3 — 2026-08-20

Status: exploratory code-first continuation; **not implementation authority**  
Parents: `CORE_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-20.md` and continuations 1–2  
Canonical implementation authority remains `docs/specs/STATUS.md`.

This pass deliberately leaves the major vendor/runtime track and samples research-lab, coding-specialization and code-intelligence ecosystems to preserve the audit's serendipity requirement.

---

# 1. Meta / FAIR — evaluation environments are more reusable than unrestricted self-improvement

## 1.1 Meta Agents Research Environments (ARE)

Upstream: `facebookresearch/meta-agents-research-environments`  
Root license: MIT  
Evidence: current repository/docs and benchmark architecture.  
Initial grade: **A+ evaluation candidate/reference**.

ARE models agent evaluation around **dynamic environments**, not static prompt/result pairs. Current concepts include:

- agents;
- interactive apps;
- events that change the world over time;
- scenarios combining apps/events/task validation;
- CLI and GUI execution;
- Gaia2 with hundreds of dynamic scenarios across multiple domains;
- multi-provider/local-model execution through LiteLLM-compatible configuration.

The useful Jarvis contribution is not another agent loop. It is a benchmark-world architecture in which the environment changes while the agent is operating.

This fills a gap between existing candidates:

```text
Harbor / TerminalBench
  -> terminal/environment outcome competence

MCP-Universe / MCPEval
  -> tool/MCP interaction competence

Meta ARE / Gaia2
  -> evolving-world adaptation and long-horizon scenario competence
```

A future engineering-agent benchmark could use the same pattern:

- telemetry changes during diagnosis;
- a solver job fails or becomes stale;
- a requirement changes mid-task;
- a resource/approval disappears;
- a competing engineering record supersedes the one initially selected.

The verifier should score final engineering state/evidence, not eloquent adaptation prose.

## 1.2 HyperAgents — research/negative evidence, not a commercial core dependency

Upstream: `facebookresearch/HyperAgents`  
Current license posture: CC BY-NC-SA 4.0 in the inspected repository.  
Mode: `REFERENCE_ONLY` for a commercial JarvisOS product.

The project explores self-referential/self-improving agents and explicitly warns that it executes untrusted model-generated code which may act destructively.

This is useful negative/experimental evidence for JarvisOS:

- self-improvement is not an authorization mechanism;
- generated code must remain inside an independently enforced sandbox;
- benchmark improvement must not automatically promote code into a trusted runtime;
- model-generated modifications require deterministic tests, provenance and human/maintainer promotion.

Do not import a “self-improvement loop” merely because it improves benchmark reward.

## 1.3 Meta follow-up queue

Inspect only when unique machinery appears:

- `MLGym` for agent-driven ML research/evaluation environments;
- `OpenApps` if its app/environment abstraction extends ARE;
- `DocAgent` if it contributes document/code navigation mechanics rather than another prompt wrapper;
- current `sira`/research projects only after executable code/license relevance is established.

---

# 2. Allen Institute for AI — SERA opens a concrete engineering-specialist coding path

## 2.1 SERA training/data-generation pipeline

Upstream: `allenai/SERA`  
Root license: Apache-2.0  
Evidence: current pipeline/docs, root structure and submodule provenance.  
Initial grade: **S- for specialist-coding data generation/training; not a Jarvis runtime replacement by itself**.

SERA is materially relevant to the specialist-training path already opened in PR #309 through DataTrove, Axolotl, TRL/PEFT and engineering-agent evaluation.

Current SERA supports:

- trajectory/data generation from arbitrary personal repositories;
- existing benchmark/container sources such as SWE-Bench/SWE-smith;
- open or closed teacher models;
- SWE-agent and mini-swe-agent harnesses;
- exact repository commits for reproducible environments;
- generated Docker environments and cached/persistent images;
- configurable codebase parsing depth/function extraction;
- single or multiple inference servers;
- data sharding across servers;
- staged generation/distillation/evaluation/post-processing;
- resuming interrupted experiments by run name/stage;
- specializing from repository-specific prior issue/PR text.

This creates a plausible Jarvis/BLUECAD route:

```text
JarvisOS / BLUECAD / open engineering repos
        |
        +-- pinned commits + tests + issue/task corpus
        |
        v
SERA-style trajectory generation
        |
        +-- strong teacher / multiple harnesses
        +-- deterministic execution outcomes
        |
        v
engineering-coding trajectory corpus
        |
        v
Axolotl / TRL / PEFT specialist training
        |
        v
Harbor + engineering deterministic evaluation
```

The important property is that specialization data is grounded in actual repositories and executable tasks rather than only synthetic engineering prose.

## 2.2 Supply-chain and privacy boundaries

The inspected `.gitmodules` resolves SERA's bundled harness families to:

- `allenai/SERA-SWE-agent`;
- `allenai/mini-swe-agent`.

Their inspected roots are MIT, while SERA's root is Apache-2.0. Exact dataset/model terms remain separate.

The SERA documentation warns that its shared GitHub mirror organization makes mirrored repositories publicly visible and recommends a private organization for private-source generation.

For JarvisOS/BlueRev this is a blocker-class issue:

> proprietary code must never be mirrored to a public training/evaluation organization merely because a data-generation helper defaults to it.

Any future specialist-training spec must define private-container/repo handling, egress policy and dataset provenance before code leaves the trusted workspace.

## 2.3 SERA CLI — mature coding client, open model backend

Upstream: `allenai/sera-cli`  
Root license: Apache-2.0.

The current CLI uses **Claude Code as the interaction/coding client while routing model inference to SERA through a proxy/vLLM endpoint**. It supports ephemeral Modal deployment, persistent shared deployments and self-hosted vLLM.

This independently confirms a recurring core-software conclusion:

> coding client/runtime UX and model provider do not have to be the same product.

The audit already found an analogous direction in vLLM Agentic API. SERA CLI is additional evidence that a mature coding client can be reused while inference moves to a local/open specialist model.

For Jarvis this suggests a future experimental matrix rather than one hardwired coding stack:

```text
Client/runtime: Codex CLI | Claude Code | Cline | Kimi | Jarvis-native
Model backend: cloud frontier | local vLLM | llama.cpp | specialist SERA-like model
Semantic layer: Serena/LSP | native client intelligence
Sandbox: OpenShell | host subprocess | future Wasm where applicable
```

Score combinations on task success, cost, latency, privacy and deterministic verification.

## 2.4 CodeNav — useful concept, stale-index failure is explicit

Upstream: `allenai/codenav`  
License: Apache-2.0  
Initial grade: **B reference; superseded in several practical aspects by Serena/current code-intelligence stacks**.

CodeNav indexes code blocks, retrieves relevant snippets and uses execution feedback so agents can exploit previously unseen codebases without manually registering every function as a tool.

This is conceptually relevant to large engineering libraries: expose retrieval over existing code rather than placing thousands of function schemas into model context.

However, the current design has important drawbacks:

- requires an Elasticsearch service;
- indexes a codebase once unless explicitly forced to reindex;
- documentation explicitly warns that modified repositories leave the index stale;
- the agent can execute arbitrary code and the project warns against security-sensitive use outside a sandbox.

Jarvis should therefore retain the **retrieve existing code capability** but prefer current semantic/index layers with freshness tied to repository/file digests rather than a manually refreshed Elasticsearch snapshot.

Potential architecture:

```text
exact repo/tree digest
      |
      +-- syntax index: Tree-sitter
      +-- semantic index: LSP/Serena
      +-- text/search index: optional
      |
      v
freshness-bound retrieval results
```

## 2.5 AllenAI next queue

- `agent-eval` / `agent-baselines` only if they add evaluator mechanics beyond Harbor/ARE;
- `DiscoveryWorld` if scientific-discovery environments can seed engineering-agent tasks;
- SERA codegraph/generation internals and its resolved SWE-agent forks;
- SERA training configs only after model/data licenses are audited separately;
- avoid promoting a model merely because its published SWE-Bench number is high.

---

# 3. Tree-sitter — cheap local syntax intelligence below LSP/Serena

Upstream: `tree-sitter/tree-sitter`  
Root license: MIT  
Evidence: current parser/runtime architecture and language ecosystem.  
Initial grade: **S- substrate candidate for structural code indexing/parsing**.

Tree-sitter is an incremental parser generator/runtime designed to:

- parse many programming languages;
- update syntax trees efficiently after edits;
- remain useful in the presence of syntax errors;
- embed as a dependency-free C runtime.

The organization maintains grammars/bindings for Python, JS/TS, C/C++, Rust, Java, Go, Bash and many others.

## 3.1 Complement, do not confuse, syntax with semantic intelligence

Tree-sitter and Serena/LSP solve different layers:

```text
Tree-sitter
  syntax tree / local structure / incremental parse / error-tolerant chunks

LSP / JetBrains / Serena
  symbols / types / references / definitions / workspace semantics
```

A layered Jarvis code-intelligence service may use Tree-sitter for fast deterministic structural indexing and delegate language-specific semantics to LSP/Serena only when needed.

That can reduce the cost/fragility of running every language server for every lightweight search task.

## 3.2 Freshness requirement

Unlike old CodeNav-style “index once” behavior, every derived syntax/search record should bind to an exact file/repository digest. Edits invalidate only affected structural regions or the relevant index generation.

The AI should never receive stale code snippets without an explicit stale marker merely because an index backend still answers queries.

---

# 4. Sourcegraph — strong architecture reference, weak direct-reuse default

Current public code surface inspected: `sourcegraph/sourcegraph-public-snapshot`.

The repository is archived and its root explicitly applies an Enterprise License except where a nested directory has a superseding license.

Disposition: **REFERENCE_ONLY by default; audit exact subcomponent license before any reuse**.

Sourcegraph remains valuable for architecture ideas around large-scale code search, indexing, navigation and Cody-era context, but the direct integration path is materially less attractive than permissive underlying primitives such as Tree-sitter, LSP and Serena.

This is also a useful negative rule for the broader audit:

> public source visibility is not permission to reuse code.

---

# 5. Updated coding-intelligence stack hypothesis

The accumulated evidence no longer supports one monolithic “coding agent”. A better comparison matrix is layered:

```text
INTERACTION / CODING CLIENT
  Codex | Claude Code | Cline | Kimi | Jarvis-native
             |
             v
AGENT RUNTIME / LOOP
  Codex core | Kimi core | MAF | Pydantic/Hermes | client-native
             |
             v
CODE INTELLIGENCE
  Tree-sitter syntax
  + Serena/LSP/JetBrains semantics
  + freshness-bound text/index retrieval
             |
             v
EXECUTION ISOLATION
  OpenShell | supervised subprocess | container | selected Wasm plugin
             |
             v
DETERMINISTIC VERIFICATION
  repo tests / typecheck / lint / engineering oracles / Harbor tasks
             |
             v
OPTIONAL SPECIALIST MODEL
  cloud frontier | local general | SERA-style code specialist | engineering specialist
```

This architecture allows each layer to compete independently.

A better semantic layer should not force a model change. A better model should not force a new editor. A better sandbox should not own provider routing.

---

# 6. New evaluation hypothesis — benchmark environmental change, not only static completion

ARE + SERA + Harbor + MCP-Universe suggest a future Jarvis/BLUECAD evaluation stack with four orthogonal axes:

1. **static deterministic task outcome** — tests/solver/artifact state;
2. **tool/protocol competence** — correct/efficient MCP/typed tool use;
3. **dynamic adaptation** — environment, evidence or requirement changes during work;
4. **specialist coding competence** — repository-grounded engineering implementation/repair.

Model/provider/client promotion should require improvements on the relevant axis without unacceptable regressions in cost, privacy or authority behavior.

---

# 7. Immediate traversal after this continuation

The audit remains deliberately open. Next high-value branches include:

- Sourcegraph subcomponents only where permissive licensing is independently verified;
- current LSP clients/server managers and Tree-sitter query/tag APIs;
- AllenAI SERA generation internals and specialist training data provenance;
- Meta ARE scenario/app validator internals;
- Julia/Jupyter runtime/package architecture;
- Mem0/Cognee and other memory-specific candidates not yet audited deeply;
- Tauri/Electron desktop process/permission architectures;
- current OpenAI Agents SDK and Google ADK concrete service interfaces;
- remaining AI labs only where executable source reveals non-overlapping machinery.

No runtime integration, deletion or implementation queue change is authorized by this document.