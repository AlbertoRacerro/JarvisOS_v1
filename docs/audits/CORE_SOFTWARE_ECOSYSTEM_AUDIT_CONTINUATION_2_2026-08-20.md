# Core software ecosystem audit — continuation 2 — 2026-08-20

Status: exploratory code-first continuation; **not implementation authority**  
Parents: `CORE_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-20.md`, `CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_2026-08-20.md`  
Canonical implementation authority remains `docs/specs/STATUS.md`.

This pass deepens Google ADK, stateful-agent recovery, temporal knowledge graphs, extension-host isolation and WebAssembly substrate evidence.

---

# 1. Google ADK — service decomposition and conformance deserve independent comparison

Upstream: `google/adk-python`  
Root license: Apache-2.0  
Evidence: current package/source inventory plus concrete service/tool paths.  
Initial grade: **S-** as generic agent-runtime/service-contract reference.

Google maintains ADK implementations in Python, Go, Java, JS and Kotlin, plus web/samples/community packages and a dedicated `google/adk-conformance` repository.

## 1.1 Current Python source is decomposed around services, not one global agent object

The current `src/google/adk` tree contains distinct modules for:

- `agents`;
- `a2a`;
- `apps`;
- `artifacts`;
- `auth`;
- `code_executors`;
- `environment`;
- `evaluation`;
- `events`;
- `flows`;
- `integrations`;
- `labs`;
- CLI/API server machinery;
- runners and invocation context;
- MCP/agent-tool adapters;
- service registry/factory code.

Search results also expose explicit `session_service`, `memory_service` and `artifact_service` construction/use in the runner and API/CLI surfaces.

This reinforces a useful Jarvis design rule:

> session state, memory, artifacts, execution and evaluation are independently substitutable services; a model/agent object should not become their shared accidental database.

## 1.2 Agent-as-tool and agent-as-A2A are distinct adapters

Current ADK contains both `tools/agent_tool.py` and A2A conversion utilities. This is another reason not to collapse “delegation” into one mechanism:

- an internal agent may be exposed as a callable tool under the parent runtime;
- a remote/opaque agent may be exposed through A2A;
- those two modes have different identity, context, trust, latency and failure semantics.

Jarvis should represent the delegation mode explicitly in provenance.

## 1.3 Conformance is maintained as a project, not an afterthought

`google/adk-conformance` exists specifically to host ADK conformance-test artifacts.

Combined with the LangGraph checkpoint-conformance package found in the previous continuation, this suggests a broader Jarvis pattern:

```text
Jarvis-owned interface/contract
       |
       +-- implementation A
       +-- implementation B
       +-- upstream adapter
       |
       +-- independent conformance suite
```

This is a stronger long-term strategy than testing each adapter only through its own mocked unit tests.

Candidate future conformance families:

- provider/model adapter;
- tool capability/executor;
- AgentRuntime;
- checkpoint/job state;
- engineering backend adapter;
- memory/index adapter;
- client protocol adapter.

---

# 2. Letta Code — recovery semantics are as important as persistent memory

Upstream: `letta-ai/letta-code`  
Root license previously verified: Apache-2.0 with brand-asset exclusions.  
Evidence: current source tree and approval-recovery implementation.  
Initial grade: **A+ core-runtime reference**.

The current source includes explicit agent IDs/tags, approval execution, approval recovery, approval-result normalization, backend switching, App Server client code and multiple external channel adapters.

This means Letta's value to Jarvis is broader than “agent with memory”.

## 2.1 Approval recovery is modeled as a state-resynchronization problem

The inspected `src/agent/approval-recovery.ts` separates pure recovery policy from network/backend side effects and exposes logic for:

- pending-approval errors;
- conversation-busy conflicts;
- empty responses;
- retryable vs non-retryable provider errors;
- quota limits;
- invalid tool-call IDs;
- retry-after parsing;
- run metadata recovery;
- rebuilding request input after stale approvals.

For stale approvals, the async recovery path rereads the agent/backend's current pending approvals, then rebuilds the input with fresh denial records. If recovery yields no retryable input, it fails rather than silently continuing.

Candidate Jarvis lesson:

> after restart/concurrent state change, never replay an old approval object merely because the UI still has it; re-bind to current server-owned pending authority or terminate safely.

This is directly relevant to any future persistent Jarvis tool/action approval flow.

## 2.2 Keep pure retry policy separate from network mutation

Letta deliberately puts pure classification/recovery policy in a separate module from helpers that call the backend.

That separation makes failure/retry decisions unit-testable without executing provider or server side effects and should be preferred in Jarvis provider/job/approval machinery.

---

# 3. Graphiti — temporal graph is a derived evidence structure, not a magical memory oracle

Upstream: `getzep/graphiti`  
Root license: Apache-2.0  
Evidence: source-level edge extraction/maintenance implementation.  
Initial grade: **A+ candidate for derived temporal knowledge projection**.

The inspected edge-maintenance code demonstrates several important semantics.

## 3.1 Facts carry temporal and episodic provenance

Extracted entity relations can carry:

- `created_at`;
- `valid_at`;
- `invalid_at`;
- `reference_time`;
- one or more source episode UUIDs;
- group identity;
- relation type and fact text.

For multi-episode extraction, the prompt asks the model to attribute each fact to explicit episode indices; those indices are then mapped back to episode UUIDs.

## 3.2 LLM extraction is followed by deterministic structural checks

Before accepting model-extracted edges, current code:

- verifies source entity name exists in the supplied node map;
- verifies target entity name exists;
- drops self-edges where both resolve to the same node;
- rejects empty fact strings;
- parses timestamps separately and warns on malformed values.

This is exactly the desired governance pattern:

```text
LLM proposes semantic relation
       |
       v
canonical-identity / structural checks
       |
       v
accepted derived graph relation
```

The graph still depends on model interpretation. It therefore must not silently outrank canonical Jarvis engineering records.

## 3.3 Potential Jarvis use

A useful architecture would be:

```text
MemoryStore / project records / threads / evidence
              |
              v
     deterministic source export
              |
              v
      Graphiti temporal projection
              |
       GraphRAG / discovery
```

Every graph fact should retain source identities so the projection can be rebuilt, challenged or discarded.

---

# 4. VS Code extension host — mature plugin isolation and lifecycle evidence

Upstream: `microsoft/vscode`  
Root/project source uses MIT licensing.  
Evidence: current local process extension-host implementation.  
Initial grade: **S reference for desktop extension lifecycle**.

The inspected `localProcessExtensionHost.ts` demonstrates that VS Code does not treat extension execution as ordinary in-renderer library code.

## 4.1 Extension host is a separately managed process

The main workbench owns an `ExtensionHostProcess` through an extension-host starter and receives:

- stdout;
- stderr;
- dynamic messages;
- process exit code/signal;
- start/kill/wait-for-exit operations.

The UI/workbench communicates using an explicit message-passing protocol.

## 4.2 Graceful shutdown has a bounded fallback

On disconnect/restart, VS Code:

1. sends a `Terminate` protocol message so extensions can run deactivation handlers;
2. waits only a bounded interval for the message protocol to become available;
3. uses a grace timer for process exit;
4. permits forceful termination after the grace period when needed.

This is substantially safer than either “kill immediately” or “wait forever”.

## 4.3 Child environment is treated as an attack/failure surface

Before launching the host, the code explicitly removes dangerous environment variables. Windows receives special process-detach behavior because renderer/child lifecycle differs by OS.

This is relevant to Jarvis plugin/MCP/solver subprocesses: inherited environment should be a deliberate whitelist/filtered projection rather than an accidental copy of the parent process.

## 4.4 Crash observability must live outside the crashing process

The source contains explicit handling for native-extension crashes where no JavaScript stack or in-process logging may survive. Raw stdout/stderr can be captured by the surviving renderer process for diagnostics.

Candidate Jarvis rule:

> the component responsible for crash evidence must not be exclusively inside the component that may crash.

This applies equally to local AI servers, MCP processes, CAD kernels and solver workers.

## 4.5 Candidate Jarvis extension architecture

The audit should compare:

```text
Frontend/main app
     |
     v
Jarvis extension/process supervisor
     |
     +-- typed IPC
     +-- filtered environment
     +-- capability manifest
     +-- startup/health
     +-- graceful stop + deadline + kill
     +-- outside-process logs/crash evidence
     |
     v
extension / MCP / validator / backend process
```

against today's per-tool process handling before designing a general plugin subsystem.

---

# 5. Wasmtime / Bytecode Alliance — substrate beneath a Wasm plugin architecture

Upstream: `bytecodealliance/wasmtime`  
Root license: Apache-2.0  
Evidence: current runtime/docs and language bindings.  
Initial grade: **A+ substrate candidate; lower-level than Extism**.

Wasmtime is a general WebAssembly runtime with:

- JIT/AOT execution through Cranelift;
- explicit focus on correctness/security;
- continuous fuzzing and a security process;
- configurable CPU/memory controls;
- WASI host interfaces;
- WebAssembly component support;
- official or project-supported bindings for Rust, C/C++, Python, .NET and Go;
- Windows binaries/support.

## 5.1 Extism and Wasmtime occupy different layers

The previous audit found Extism as a plugin framework with PDKs, host-controlled HTTP, simple host functions and limiter abstractions.

Wasmtime sits below that abstraction and is appropriate if Jarvis needs:

- direct WASI/component-model control;
- custom host capability composition;
- lower-level resource policy;
- runtime features not exposed by Extism.

Do not build a custom Wasm plugin protocol merely because Wasmtime is flexible. Prefer Extism or another maintained higher-level contract unless the lower-level control is demonstrably required.

## 5.2 Bytecode Alliance siblings worth following

- `wit-bindgen` for typed interface generation;
- WASI/component-model specifications and security boundaries;
- Wasmtime Python/.NET bindings relevant to the actual Jarvis implementation language;
- only then deeper compiler/runtime projects such as Cranelift where they answer a concrete Jarvis need.

---

# 6. New architecture hypotheses

## H7 — recovery objects need freshness just like engineering records

Jarvis already treats engineering/evidence selection as stale-sensitive. Letta shows the same principle applies to approvals and interrupted agent turns.

A future persisted action approval should contain enough immutable request identity to detect:

- target changed;
- arguments changed;
- policy changed;
- workspace changed;
- backing action no longer exists;
- approval already consumed.

Stale approval => explicit resync/deny, never replay.

## H8 — generic extension execution should become supervised, not ad hoc

VS Code + Extism + Wasmtime + OpenShell + Codex/Kimi MCP work point toward a possible generic supervisor boundary above individual executors.

The supervisor can own:

- extension identity/version/digest;
- declared capabilities;
- process/runtime choice;
- filtered environment;
- network/filesystem policy;
- lifecycle/health;
- crash evidence;
- time/resource budgets;
- version/protocol negotiation.

It should not own engineering semantic truth or user authorization.

## H9 — conformance suites should become first-class repo assets

Google ADK and LangGraph independently maintain conformance artifacts for substitutable implementations.

Jarvis should consider a future `backend_conformance` or equivalent test package covering all adapter kinds instead of accumulating unrelated mocks around each integration.

---

# 7. Next traversal after this continuation

Still high priority:

1. Google ADK concrete session/memory/artifact service interfaces and runner behavior;
2. `adk-conformance` actual artifact/spec semantics across language implementations;
3. Letta persistent agent/memory block storage and App Server protocol;
4. Graphiti contradiction/supersession/invalidation code and rebuild/delete behavior;
5. VS Code extension service selection, remote/web extension hosts and crash/restart policy;
6. Wasmtime/WASI capability/resource configuration and Extism host comparison;
7. Meta/FAIR, AllenAI and current lab ecosystems;
8. Sourcegraph/Tree-sitter/code-index infrastructure;
9. Julia/Jupyter runtime/package/plugin architecture;
10. update the canonical candidate register only after the current core-software wave is sufficiently reconciled.

No implementation or queue change is authorized.