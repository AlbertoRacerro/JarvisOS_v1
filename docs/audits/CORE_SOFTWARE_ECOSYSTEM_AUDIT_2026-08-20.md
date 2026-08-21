# Core software ecosystem audit — 2026-08-20

Status: exploratory code-first candidate-integration audit; **not implementation authority**  
Scope: JarvisOS core software architecture surrounding AI runtimes, memory, tools, model/provider adaptation, frontend↔backend↔external-runtime boundaries, agent/client protocols, persistence, plugins, durable jobs, observability and developer tooling.  
Canonical implementation authority remains `docs/specs/STATUS.md`.

---

# 0. Audit doctrine

This continuation deliberately changes the comparison frame used for upstream discovery.

## 0.1 JarvisOS is `REF-000`, not the privileged baseline

During this audit, current JarvisOS is treated as one candidate implementation among many. Existing code receives no preference merely because it is already written.

For every core capability, the eventual comparison may conclude:

- `KEEP_JARVIS`: current JarvisOS implementation is materially stronger or more appropriate;
- `REPLACE_WITH_UPSTREAM`: a maintained upstream component solves the problem better;
- `WRAP_UPSTREAM`: JarvisOS should own policy/identity/IR while delegating execution to upstream;
- `HYBRID`: retain a narrow Jarvis authority layer and combine multiple upstream primitives;
- `DELETE`: the local component creates duplicate complexity without unique value;
- `PARK`: potentially useful but premature or unproven.

No such disposition in this document authorizes code deletion or integration. It creates hypotheses for later prototype/benchmark/ADR/spec work.

## 0.2 Serendipity is a requirement

The audit is intentionally graph-shaped rather than a fixed checklist. Starting from a relevant repository or organization:

1. inspect actual code, tests, package boundaries and license where possible;
2. identify forks and resolve their original upstreams;
3. inspect relevant sibling repositories from the same author/organization;
4. follow important dependencies and protocols when they expose reusable architectural primitives;
5. follow new authors/organizations discovered through those links;
6. retain unexpected findings when they plausibly improve AI, memory, tools, state, runtime bridges, plugins, security, observability or developer infrastructure;
7. record negative evidence so weak patterns are not repeatedly rediscovered.

The search is relevance-scoped, not name-scoped. A repository does not need to describe itself as an “AI framework” to matter. Editor infrastructure, notebook kernels, workflow runtimes, plugin systems and databases can be more important to JarvisOS than another agent wrapper.

## 0.3 Evidence rule

- `CODE-FIRST`: implementation/tests/contracts were inspected directly.
- `CODE-HISTORY`: current tree plus concrete recent implementation/failure-mode commits were inspected; representative source paths still require a deeper second pass before direct reuse.
- `DOCS/STRUCTURE`: repository structure and primary documentation were inspected, but the relevant execution path has not yet received enough source-level inspection.
- `QUEUED`: discovered and plausibly relevant, not yet audited deeply enough.

README claims never become implementation evidence by themselves.

---

# 1. First core-software candidate map

| Source | Area | Evidence | License posture at inspected root/component | Initial value | Main reason to continue |
| --- | --- | --- | --- | --- | --- |
| `openai/codex` | agent runtime / app server / state / MCP / memory | CODE-HISTORY + tree | Apache-2.0 | S | current monorepo contains reusable core-runtime primitives far beyond a CLI |
| `openai/openai-agents-*` | agent SDK / tools / handoffs / tracing | QUEUED/PARTIAL | component-specific permissive roots require exact check | A+? | compare generic agent-loop primitives against Hermes/Pydantic/Codex/Kimi |
| `openai/codex-security` | evidence-grounded security workflow | CODE-HISTORY | verify exact component | A | deterministic scan/artifact lifecycle and failure handling |
| `anthropics/claude-agent-sdk-python` | agent adapter / hooks / MCP / permissions | CODE-FIRST/DOCS | repository has MIT component license; README also binds SDK use to Anthropic commercial terms except separately licensed components | A+ | clean programmable boundary over bundled Claude Code, hooks and in-process MCP |
| `anthropics/claude-code` | coding runtime / plugins / skills | DOCS/STRUCTURE | all rights reserved; Anthropic commercial terms | A reference | strong runtime reference but not a permissive code-reuse source |
| `MoonshotAI/kimi-code` | full agent core / protocol / server / SDK / store | CODE-HISTORY + package manifests | MIT | S | unusually direct comparison candidate to JarvisOS core |
| `oraios/serena` | semantic code intelligence / MCP / memory | CODE-FIRST | MIT | S- | reusable semantic intelligence below multiple coding clients; useful memory integrity primitives |
| `WolframResearch/Chatbook` | LLM tools / personas / model capability adaptation | CODE-FIRST | MIT | S- | mature capability-resolution and tool/persona patterns |
| Wolfram WSTP / LibraryLink / Python client / LSP | runtime bridges / language interop | PARTIAL | per-repo verification required | A+? | decades-old external-runtime boundary problem maps directly to Jarvis↔solver/backend integration |
| `zed-industries/zed` + ACP | agent-client protocol / editor runtime / LSP | CODE-HISTORY | exact per-component license review required | S- reference | separates client protocol identity/session concerns from agent implementation |
| `agentclientprotocol/agent-client-protocol` | standard agent↔client boundary | CODE-HISTORY | exact license review required | S- | current independent protocol with cancellation/session evolution and multi-client ecosystem |
| `letta-ai/letta-code` | stateful agent runtime / app server / channels / memory | DOCS/STRUCTURE | Apache-2.0 excluding brand assets | A+ | direct comparison for persistent agent identity/state and channels |
| `getzep/graphiti` | temporal knowledge graph / derived memory | DOCS/STRUCTURE | exact root license review pending | A | compare as derived semantic memory, not canonical engineering truth |
| `jupyter-server/jupyter_server` + kernel protocol family | external kernels / sessions / execution channels | PARTIAL | permissive Jupyter family terms; exact component check | A+ | mature language/runtime process boundary independent of AI |
| `temporalio/*` | durable workflow execution | PARTIAL | exact component license check | A+ | benchmark custom Jarvis job/retry/resume semantics against a mature durable runtime |
| `dapr/*` | sidecar / service invocation / state / pubsub / workflows | PARTIAL | exact component license check | A | architectural reference for externally hosted capabilities behind a local sidecar |
| `hashicorp/go-plugin` | subprocess plugin RPC lifecycle | PARTIAL | exact current license must be reviewed | A | long-lived pattern for isolating plugins as child processes rather than loading arbitrary code in-process |

Existing PR #309 findings for Hermes, Cline, OpenShell, NemoClaw, Pydantic AI/Harness, LiteLLM, vLLM/Agentic API, llama.cpp/Ollama, Harbor, Lighteval and related ecosystems remain valid and are not duplicated here. This audit compares the newly opened core-software families against those earlier candidates.

---

# 2. OpenAI: Codex must be audited as a core runtime, not merely a coding CLI

Upstream: `openai/codex`  
Root license inspected: Apache-2.0.

The current Rust monorepo contains first-class packages for app-server protocols/clients/daemons, agent graph and identity, analytics, state, MCP, execution and other runtime concerns. This materially changes its relevance to JarvisOS.

## 2.1 Typed app-server boundary

The current tree includes `codex-rs/app-server-protocol`, `app-server-client`, `app-server-daemon` and test clients. Recent work continuously evolves typed RPC/schema surfaces rather than exposing UI internals as the integration contract.

Candidate Jarvis lesson:

```text
Frontend / desktop / CLI
        |
        v
versioned typed application protocol
        |
        v
Jarvis runtime authority
        |
        +-- AI worker
        +-- tool execution
        +-- memory/state
        +-- BLUECAD/backends
```

Do not make React component state, Python object identity or HTTP-route accidents the permanent cross-client contract.

## 2.2 Distinct state domains rather than one accidental SQLite blob

The inspected `codex-rs/state` tree contains separate migrations for main state plus memory, goals, queue, logs and thread history domains.

Recent implementation history contains two especially relevant patterns:

- shared state DB handles are initialized once and injected into consumers instead of each subsystem lazily reopening SQLite; this specifically prevents lock contention / `database is locked` failure classes;
- load-bearing state migrates forward rather than deleting databases on version changes.

Jarvis hypothesis: differentiate durable authoritative stores from rebuildable indexes/caches and inject process-owned handles rather than allowing every subsystem to independently open/create state.

## 2.3 Durable truth versus derived index: `doctor` pattern

A recent Codex `doctor` thread-inventory path compares durable rollout JSONL source data against SQLite indexed state and reports missing/stale/mismatched/duplicate records.

This is a strong pattern for JarvisOS:

```text
canonical durable artifact / event truth
             |
             +----> derived DB/index/cache
                         |
                         +----> doctor/reconcile check
```

A successful parse or existing row is not proof that the index still represents canonical truth.

## 2.4 MCP lifecycle is server-specific and lazy where safe

Recent Codex changes show useful implementation detail:

- optional cached MCP servers may remain stopped until one of their tools is actually invoked;
- root/required/reconnect-sensitive servers can remain eager when needed;
- a call that needs one server waits for that server before entering the broader parallel-tool gate so unrelated tool calls are not unnecessarily blocked;
- OAuth/routing settings are applied per MCP server/plugin, with disabled/unowned environments excluded;
- callback-port ownership is per server rather than one implicit global callback endpoint.

Candidate Jarvis lesson: capability discovery, server readiness, authorization and execution are different states. “MCP configured” must not imply “process eagerly running” or “tool authorized”.

## 2.5 Agent roles preserve parent authority and reduce capability

Recent role/subagent work uses role configuration as bounded overrides while preserving parent permission/provider/endpoint/MCP boundaries. Role files are treated as an authority surface and symlinked role definitions are rejected in hardened paths.

This aligns with the existing Jarvis rule that personas/subagents are advisory configurations, not independent authorities.

Potential direct lesson: preserve authenticated actor identity/registry semantics separately from model-generated role names and keep replacement/resume/release operations consistent in the registry.

## 2.6 Memory is both model-generated and deterministically verified

The current memory pipeline has concrete hardening against several failure modes:

- dedicated memory DB separated from durable thread state;
- memory data treated as rebuildable where appropriate;
- consolidation runs under sandbox constraints inherited from the parent and narrowed to the memory workspace when possible;
- symlinked memory roots/artifacts are rejected/purged;
- required artifacts such as `MEMORY.md` / versioned summaries are deterministically validated before a consolidation job is marked successful;
- the orchestrator waits for consolidation-agent shutdown before releasing job/lease state;
- provider/model defaults are owned by the active provider while explicit configuration overrides win.

This is more relevant to JarvisOS than copying Codex's prose-memory format. The reusable idea is **model-assisted memory behind deterministic lifecycle and filesystem/state controls**.

## 2.7 OpenAI sibling queue

Follow-up OpenAI work should inspect, without assuming equivalence:

1. `openai/openai-agents-python` and `openai/openai-agents-js` — tools, sessions, handoffs, guardrails, tracing and model abstraction;
2. `openai/codex-security` — artifact lifecycle, evidence-grounded scan state, resumability and trust boundaries;
3. `openai/openai-cli` only for generic CLI/service integration patterns not already supplied by Codex;
4. SDK repositories only where they reveal cross-provider/realtime/streaming/pagination/telemetry contracts useful to Jarvis core;
5. Cookbook memory/agent examples as test ideas, not implementation evidence.

---

# 3. Anthropic: separate Claude Code product terms from reusable SDK/runtime patterns

## 3.1 `anthropics/claude-code`

The public Claude Code repository is not a permissive source tree. Its root license says all rights reserved and use is subject to Anthropic commercial terms.

Therefore:

- use it as runtime/product/UX/reference evidence;
- do not copy implementation merely because source/supporting material is visible;
- prefer separately licensed SDKs, skills/plugins or standards where they expose the needed boundary.

## 3.2 `anthropics/claude-agent-sdk-python`

The SDK repository has an MIT license file, but its README also states use of the SDK is governed by Anthropic commercial terms except where a component/dependency has a different license. Exact reuse therefore needs a component-level legal boundary, not a blanket “MIT repo” assumption.

Technically, however, it exposes valuable architecture:

- simple async `query()` over the bundled/system Claude Code CLI;
- bidirectional `ClaudeSDKClient`;
- explicit message/block/result/error types;
- custom tools as **in-process SDK MCP servers**;
- external MCP servers can coexist with in-process servers;
- deterministic application hooks such as `PreToolUse` can deny/modify behavior independently of the model;
- `allowed_tools` means auto-approval, not tool visibility; `disallowed_tools` and permission callbacks are distinct mechanisms;
- subagents/session forking and settings isolation exist as programmatic concepts.

This distinction is critical for Jarvis:

```text
tool exists
≠ tool visible to model
≠ tool auto-approved
≠ tool authorized by Jarvis policy
≠ tool execution succeeded
```

Those states must never collapse into one boolean.

A recent SDK hardening change also validates skill/tool names before serializing them through CLI argument syntax because commas/spaces/control characters could be reinterpreted by the receiving CLI parser. This is a reusable rule: **typed authority must survive serialization without widening**.

## 3.3 Anthropic sibling queue

- `anthropics/skills`: inspect skill packaging, metadata and admission boundaries;
- official/community plugin repositories: inspect lifecycle/discovery/versioning but treat untrusted plugin content as supply-chain input;
- TypeScript Agent SDK if its runtime/transport differs materially;
- Claude Code Action only for CI/remote-worker lifecycle patterns that are not already covered by Jarvis 079/Codex/Cline.

---

# 4. Moonshot: `kimi-code` is a direct Jarvis-core comparison candidate

Upstream: `MoonshotAI/kimi-code`  
Root license: MIT.

This repository is unusually relevant because its current monorepo already decomposes a complete coding/agent application into reusable-looking packages.

Current package inventory includes:

- `agent-core` and `agent-core-v2`;
- `acp-adapter` and `acp-server`;
- `kap-server`;
- `klient`;
- `node-sdk`;
- `protocol`;
- `telemetry`;
- `transcript`;
- `oauth`;
- `minidb`;
- terminal/PTY and parser components.

## 4.1 Agent Core v2 — DI Scope architecture

`@moonshot-ai/agent-core-v2` describes itself as Kimi's unified agent engine using a DI Scope architecture. Its package scripts generate contract, configuration, wire and state manifests and separately check import boundaries.

Dependencies include Anthropic, Google and OpenAI SDKs, MCP SDK, Moonshot protocol/OAuth/minidb packages, PTY, browser/readability/parsing utilities and schema validators.

This deserves a direct architecture comparison against Jarvis backend modules and against Hermes/Pydantic/Codex, rather than being treated as another model-specific CLI.

## 4.2 `minidb` — state primitive worth independent audit

The MIT `@moonshot-ai/minidb` package describes a pure-Node embedded key/value store combining Redis-style in-memory access with durable WAL + snapshot persistence. It exports cluster and worker-runtime surfaces.

Do not adopt it merely because it exists; Jarvis already has SQLite authority. But compare:

- persistence semantics;
- crash recovery;
- snapshot/WAL compaction;
- worker concurrency;
- cluster behavior;
- schema/migration requirements;
- ability to audit/repair state.

## 4.3 Failure-mode evidence from current Kimi development

Recent code history exposes high-value engineering lessons:

- **last-known-good configuration:** failed reload preserves the prior valid configuration and taints state so persistence is blocked instead of overwriting disk with defaults;
- **merge external edits:** configuration persistence rereads/merges rather than blindly overwriting concurrent external changes;
- **provider-empty response:** a provider-filtered deterministic empty response is treated as non-retryable rather than burning repeated model calls/compactions;
- **protocol compatibility:** strict OpenAI-compatible validators may require `content: null` on tool-call-only assistant messages; protocol adapters must test semantic interoperability, not only nominal schema similarity;
- **DI collisions:** duplicate dependency-injection registration can allow an older service to shadow a newer implementation depending on import order; service token ownership needs deterministic uniqueness/testing;
- **file indirection:** daemon media/file stores use stable application-owned references instead of persisting transient local `file://` paths that poison later retries;
- **updater robustness:** staged updates use unique paths, digests, locks, PID/liveness and ownership checks, swap mutexes, rollback preservation and path-traversal defenses.

The updater work is not immediately needed for JarvisOS, but it is retained as serendipitous evidence for a future packaged desktop/runtime updater.

---

# 5. Serena / Oraios: semantic intelligence should be separable from the coding agent

Upstream: `oraios/serena`  
License: MIT.

## 5.1 Main architectural value

Serena should not be classified merely as “another coding agent”. Its strongest role is a semantic-code-intelligence layer that can sit below different clients/agents through MCP and language intelligence backends.

Candidate stack:

```text
Codex / Claude Code / Cline / Jarvis worker
                    |
                    v
           Serena semantic tools
                    |
            LSP / JetBrains backend
                    |
                    v
       symbols / references / edits
```

This permits the model/client to change without discarding the code-intelligence substrate.

## 5.2 Capability composition instead of tool accumulation

Serena contexts can suppress capabilities that the host client already provides. This is a strong rule for JarvisOS: do not give an agent five overlapping file-read/edit/search stacks just because each integration ships one.

Potential canonical process:

1. compute host-native capabilities;
2. compute worker/plugin capabilities;
3. remove semantically duplicate tools unless independent verification requires both;
4. expose the smallest sufficient catalog;
5. retain authority checks independently of visibility.

## 5.3 Memory implementation has useful integrity primitives

The inspected memory code is deliberately simple Markdown, but contains reusable controls:

- project-local and explicit `global/` memory namespaces;
- read-only and ignored-memory patterns;
- explicit `mem:<name>` references;
- rename/move can propagate marked references;
- delete is described as requiring explicit instruction/permission;
- literal/regex editing can reject ambiguous multiple matches;
- memory paths reject `..`, absolute paths and empty segments;
- containment is checked before directory creation;
- memory maintenance instructions are themselves a versionable memory artifact;
- symlinked directories may be intentionally supported while lexical path escape remains blocked.

Jarvis should compare these ideas to MemoryStore/Obsidian/Cavemem findings. The likely lesson is not “replace canonical engineering memory with Markdown”; it is stronger referential integrity and explicit project/global/editability semantics for non-canonical working memory.

## 5.4 Oraios siblings

`oraios/sensAI`, `sensAI-utils` and the public JetBrains integration should be scanned only where they add code-intelligence, model-evaluation or integration primitives not already visible in Serena.

---

# 6. Wolfram Research: audit the software ecosystem, not only Mathematica/CAS

## 6.1 Chatbook

Upstream: `WolframResearch/Chatbook`  
License: MIT.

Chatbook is a strong core-Jarvis reference because it integrates LLMs, tools, personas, model families, front-end notebooks and Wolfram execution in a mature application.

### Tool/persona matrix

`Source/Chatbook/ToolManager.wl` combines global tools with tools contributed by personas, canonicalizes tool identity and exposes scoped enablement. The important idea is that a persona can contribute/default capabilities without becoming an independent authority/store/runtime.

This matches JarvisOS's desired bounded persona semantics.

### Hierarchical model capability resolver

`docs/adding-model-support.md` documents an eight-level model-setting lookup:

1. service + exact model name;
2. service + model ID;
3. service + model family;
4. service-agnostic + exact name;
5. service-agnostic + model ID;
6. service-agnostic + family;
7. service default;
8. global default.

Capabilities include context size, multimodality, tool support, reasoning, synchronous/streaming behavior, tokenizer, unsupported parameters, tool-call method, response roles, message splitting/retry behavior and tool-response limits.

This is a serious comparison target for the Jarvis provider registry. A provider binding alone is not enough; model-specific behavioral capability metadata must be first-class and overrideable without scattering special cases across runtime code.

A particularly good pattern is explicit `NotSupported` rather than silently omitting or passing an unsupported parameter.

## 6.2 Wolfram runtime-bridge family

Relevant sibling projects discovered:

- `WolframClientForPython`;
- `LibraryLinkUtilities`;
- `LSPServer`;
- `wstp-rs` / `wolfram-library-link-rs` historical Rust bridges;
- Jupyter/Wolfram kernel integrations;
- packaging/paclet CI tooling.

These need a deeper code pass. Their strategic relevance is the general problem Wolfram has solved repeatedly:

> stable communication between a central symbolic/application runtime and external languages, kernels, native libraries and tools.

That maps directly to JarvisOS/BLUECAD's need to connect Python, native CAD/CAE libraries, external solver processes, local AI servers and possibly remote workers without making any one backend's object model canonical.

## 6.3 Wolfram next pass

1. inventory every current WolframResearch repository and classify by original/fork/archive;
2. inspect Chatbook `DefaultTools`, `LLMUtilities`, `SendChat`, settings/model files and resource installation lifecycle;
3. code-first WSTP/LibraryLink/Python-client session/error/lifetime semantics;
4. inspect LSP/parser/code-inspection repos for reusable diagnostics/semantic-index patterns;
5. inspect paclet packaging/update/signing/version boundaries;
6. follow non-Wolfram upstreams used by these bridges when they expose reusable protocols/runtime mechanics.

---

# 7. Zed and Agent Client Protocol: the missing client↔agent standard layer

Zed is useful not merely as an editor UI. Its ACP work exposes a protocol boundary between an agent client and heterogeneous agent runtimes.

Recent implementation history provides concrete failure-mode evidence:

- cancellation support is propagated to non-side-effectful handlers;
- session configuration replaces ad hoc unstable selectors;
- one change explicitly separates ACP `protocol_id` from the Zed-native `client_id`: protocol IDs group streamed agent messages, while client IDs own truncate/rewind/edit/checkpoint/token-usage/persistence semantics;
- a macOS development crash exposed how protocol dispatch implementation can exceed GCD worker stack limits, leading Zed to move ACP polling to a dedicated thread.

The ID split is particularly relevant to JarvisOS. Provider message IDs, local thread IDs, run IDs, attempt IDs and UI row IDs must not be conflated just because one implementation happens to use the same string today.

Independent upstream `agentclientprotocol/agent-client-protocol` is active and should be audited directly rather than inferred only through Zed.

Candidate question:

> Should JarvisOS expose/adopt an ACP-compatible client-agent boundary so Codex/Kimi/other agents can plug into one UI without bespoke adapters?

This competes with, rather than replaces, MCP. MCP primarily standardizes tools/context servers; ACP addresses agent↔client/session interaction.

---

# 8. Memory systems: split the problem before choosing a framework

The external scan reinforces that “memory” is several different problems:

```text
canonical engineering records        -> JarvisOS authority / MemoryStore
conversation/thread persistence       -> episodic state
agent working memory                  -> mutable model-facing state
project notes                         -> local Markdown/vault layer
semantic retrieval index              -> rebuildable derived index
knowledge graph                       -> rebuildable/traceable semantic projection
model-generated consolidation         -> governed transformation job
```

A single vector database or graph framework should not own all six.

## 8.1 Letta Code

The old `letta-ai/letta` repository now explicitly points to `letta-ai/letta-code` as current source. Current Letta Code includes the agent harness, interactive terminal UI, App Server, channels and runtime used by desktop/web applications.

Root license is Apache-2.0 with brand-asset exclusions.

High-value comparison questions:

- persistent agent identity versus session identity;
- memory block/object lifecycle;
- server/client/channel separation;
- local vs cloud synchronization and authority;
- memory edit/consolidation semantics;
- provider independence;
- whether the App Server offers a narrower reusable boundary than importing the entire runtime.

## 8.2 Graphiti / Zep family

`getzep/graphiti` is a current temporal-knowledge-graph implementation with explicit observability material and a substantial codebase. It should be evaluated as a **derived temporal semantic view**, not as the source of canonical BlueRev/Jarvis engineering truth.

Critical tests before any promotion:

- source/provenance retention per node/edge/fact;
- contradiction and supersession semantics;
- temporal validity versus ingestion timestamp;
- deterministic deletion/rebuild from canonical source data;
- graph DB and model-provider operational footprint;
- behavior when extraction/model calls fail partially.

## 8.3 Other memory queue

Audit next: `mem0ai/mem0`, Cognee, LlamaIndex memory/index primitives, LangGraph persistence/checkpointing and any current Pydantic/Codex memory components already found. Compare by memory subtype rather than benchmark marketing claims.

---

# 9. Non-AI infrastructure is intentionally in scope

## 9.1 Jupyter Server / kernel ecosystem

Jupyter's server/kernel architecture is a mature reference for:

- lifecycle of external language/runtime processes;
- sessions separate from kernels;
- structured multi-channel messaging;
- interrupt/restart/shutdown semantics;
- kernel discovery/specification;
- reconnect behavior and client independence.

This deserves comparison to WSTP, ACP, MCP and Jarvis runner/backend adapters. The goal is not to turn BLUECAD into Jupyter; it is to avoid inventing a brittle process/session protocol when mature contracts already exist.

## 9.2 Temporal

Temporal is a candidate **durable execution reference**, not an automatic dependency. Compare it against Jarvis scheduled/deferred jobs when a real workflow needs:

- crash/restart survival;
- retry policy;
- long waits/signals;
- resumable multi-step state;
- versioning of workflow code;
- idempotent external activities.

For current single-user local Jarvis workflows, Temporal may be excessive. The audit must quantify whether its operational cost is justified before replacing lightweight SQLite/job machinery.

## 9.3 Dapr

Dapr is relevant as a sidecar/reference for heterogeneous service invocation, state stores, pub/sub, secrets/configuration, workflows and resilient reconnect behavior. It is likely too large as a default single-user desktop dependency, but its separation of application code from infrastructure capabilities is a useful architecture reference for external BLUECAD/solver/edge services.

## 9.4 HashiCorp `go-plugin`

`go-plugin` represents another non-AI pattern: run extension code in separate child processes and communicate through RPC/gRPC rather than loading untrusted/unstable plugins into the host address space.

The exact current license and applicability to Jarvis's Python/Windows stack require review. Conceptually, however, this is a useful competitor to:

- in-process Python plugins;
- MCP subprocess servers;
- Jarvis runner subprocesses;
- future native solver/CAD extension hosts.

---

# 10. Cross-ecosystem architecture hypotheses produced by the first pass

These are hypotheses to test, not product decisions.

## H1 — Jarvis should own policy and identity, not every execution engine

Repeated independently across Codex, Kimi, Claude SDK, Serena, ACP, Wolfram bridges, Jupyter and the earlier engineering audit.

Possible target shape:

```text
JarvisOS authority core
  identity / workspace / sensitivity / budget / provenance / canonical records
        |
        +-- AgentRuntime adapter
        |      Codex / Kimi / Hermes / Cline / Claude SDK / future
        |
        +-- ToolCapability adapter
        |      native / MCP / Serena / engineering backend
        |
        +-- RuntimeBridge adapter
        |      subprocess / ACP / Jupyter-like kernel / native library / service
        |
        +-- DerivedMemory adapter
               local notes / indexes / graph / consolidation
```

## H2 — protocol contracts deserve first-class status

Current JarvisOS has many valid backend boundaries, but external evidence suggests we should explicitly compare its protocol layer against:

- Codex app-server protocol;
- ACP agent-client protocol;
- MCP tool/context protocol;
- Kimi protocol packages;
- Jupyter messaging;
- WSTP/LibraryLink;
- gRPC/subprocess-plugin patterns.

One universal protocol is unlikely to win every layer. The key is **typed stable boundaries with explicit ownership**, not protocol monoculture.

## H3 — capability visibility, approval and execution must be separate

Claude SDK, Hermes, Codex and Serena all expose reasons to distinguish:

1. capability installed/known;
2. capability relevant/visible to model;
3. exact action allowed by policy;
4. approval needed/obtained;
5. executor ready;
6. execution succeeded;
7. effect verified.

Jarvis should be judged against this complete state machine, not only by whether a tool registry exists.

## H4 — derived state needs reconciliation tooling

Codex `doctor`, Kimi last-known-good config and Jarvis's own provenance work point toward the same rule:

> every rebuildable index/cache/view should have a way to prove whether it still represents canonical durable truth.

Do not silently trust “database row exists”, “JSON parses” or “cache loaded”.

## H5 — model/provider capability metadata should be hierarchical

Wolfram Chatbook's capability resolver is currently the strongest newly found reference for avoiding provider-specific conditionals spread across an application.

Compare it directly against Jarvis provider registry and LiteLLM metadata before adding more local/frontier providers.

## H6 — use the smallest sufficient runtime

The audit must resist replacing a 200-line local queue with Temporal, or a narrow subprocess adapter with Dapr, solely because the larger project is sophisticated. Upstream maturity is only valuable when its failure modes overlap the product's actual needs.

---

# 11. `REF-000` JarvisOS comparison plan

A later code-first pass must evaluate current JarvisOS against the candidate map component-by-component. Do not compare repository slogans.

Required dimensions:

| Dimension | Failure modes to test |
| --- | --- |
| canonical state | duplicate truth, stale rows, destructive migration, partial write, lock contention |
| memory | hidden promotion, stale context, lost provenance, unbounded consolidation, cross-project leakage |
| tools | duplicate capability, authority widening, schema drift, stale server registry, parse failure |
| agent runtime | orphan workers, stale results, identity confusion, parent-permission widening, context leakage |
| provider/model | unsupported params, capability drift, bad fallback, wrong tokenizer/context limit, cost routing |
| IPC/protocol | version mismatch, reconnect, cancellation, duplicate IDs, partial messages, replay semantics |
| external backends | crash/timeout, stale artifact, incompatible version, license boundary, unverified side effects |
| frontend↔backend | UI-owned truth, stale subscriptions, optimistic mutation mismatch, hidden authority |
| jobs | restart, duplicate execution, retry storms, lease expiry, idempotency, queued-state drift |
| plugins/extensions | supply-chain install, duplicate registration, version conflict, escape from permission scope |
| observability | secrets in logs, missing correlation, sampled-away failure, model-vs-deterministic evidence confusion |

Only after this matrix is populated should a deletion/replacement shortlist be proposed.

---

# 12. Broad traversal queue — deliberately non-exhaustive and self-expanding

The following are seeds, not the boundary of the audit. Each discovered relevant organization may add siblings/upstreams.

## Agent/runtime and AI companies

- OpenAI: Codex deeper pass, Agents SDKs, Codex Security, SDK/runtime siblings;
- Anthropic: Agent SDK Python/TS, skills, plugins, Claude Code reference;
- Moonshot AI: complete `kimi-code` package graph and siblings;
- Google / Google DeepMind: agent tooling, ADK, A2A, sandbox/eval/runtime, Gemini CLI and code-assist open components;
- Microsoft: Semantic Kernel, AutoGen, VS Code/Copilot-adjacent open components, already-audited governance/OpenShell-adjacent work where applicable;
- Meta / FAIR: agent/tool/eval/retrieval/runtime projects;
- AllenAI: agent/retrieval/evaluation/data systems;
- Stanford / CRFM and Berkeley labs: executable agent/eval/tool/runtime systems only;
- Salesforce AI Research: continue MCP-Universe/MCPEval siblings already identified;
- Pydantic: AI/Harness deeper code pass, Logfire if observability overlap justifies it;
- LangChain/LangGraph: persistence/checkpoint/durable graph mechanisms, not generic chain abstractions;
- LlamaIndex: index/retrieval/data-agent infrastructure where it adds non-overlapping machinery.

## Developer-platform and code-intelligence ecosystems

- Serena/Oraios deeper pass;
- Zed + independent ACP;
- VS Code extension host / language client / task/debug adapter architecture;
- Language Server Protocol ecosystem and mature server managers;
- JetBrains plugin/runtime boundaries where public reusable code exists;
- Sourcegraph code-intelligence components with exact current licensing review;
- Tree-sitter and parser/index infrastructure;
- Jupyter server/kernel/client ecosystem.

## Memory/data/state

- Letta Code;
- Graphiti/Zep;
- Mem0;
- Cognee;
- SQLite and Litestream/LiteFS-style durability/replication references where needed;
- DuckDB/Arrow only for analytic/result data paths, not as automatic canonical state replacement;
- Tantivy/Lucene/SQLite FTS/vector-index candidates only when retrieval measurements justify them.

## Durable/runtime plumbing

- Temporal;
- Dapr;
- Ray where distributed worker scheduling is actually needed;
- Prefect/Dagster for workflow/state UX reference;
- NATS/Redis streams only if event distribution becomes a real product need;
- HashiCorp go-plugin / plugin protocols;
- Wasmtime / Extism / WASI component model for sandboxed extension execution;
- gRPC/protobuf and Connect-like protocol stacks;
- OpenTelemetry for end-to-end AgentRun/tool/backend correlation.

## Frontend↔backend application architecture

- Tauri and Electron process/permission/plugin boundaries;
- VS Code desktop/web extension-host separation;
- JupyterLab server-extension/frontend-extension contract;
- local-first sync/state projects only if Jarvis grows beyond the current single-user local authority model.

## Scientific/computational software architecture

- Wolfram Research complete relevance-scoped organization traversal;
- MATLAB/MathWorks public open components where actual source exists;
- Julia language/package-server/runtime boundaries;
- scientific Python projects with mature plugin/backend registries;
- existing engineering candidates from the engineering audit, now revisited only for how they expose adapters/plugins/state/provenance rather than for their numerical science.

---

# 13. Promotion gate

Before any core-software candidate replaces a JarvisOS component:

1. identify the exact current Jarvis capability and runtime path being compared;
2. reproduce at least one current failure/requirement test against both implementations;
3. inspect exact dependency/component license and transitive obligations;
4. measure operational footprint, startup, memory, latency and failure behavior where relevant;
5. test Windows/local/offline requirements explicitly;
6. verify secret, workspace, filesystem, network and model/provider authority boundaries;
7. prove migration/reversibility and retain canonical data ownership;
8. prefer an adapter prototype before invasive refactor;
9. delete duplicate Jarvis code only after replacement behavior is proven;
10. create a governing ADR/spec only after the evidence supports promotion.

**This audit authorizes none of those implementation actions.**