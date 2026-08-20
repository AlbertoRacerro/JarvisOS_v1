# Core software ecosystem audit — continuation 4 — 2026-08-20

Status: exploratory code-first continuation; **not implementation authority**  
Parents: `CORE_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-20.md` and continuations 1–3  
Canonical implementation authority remains `docs/specs/STATUS.md`.

This pass follows three still-open core layers: a generic OpenAI agent SDK beneath Codex, specialized AI-memory products, and desktop frontend↔native capability authority.

---

# 1. OpenAI Agents SDK — generic agent primitives below the Codex product runtime

Upstream: `openai/openai-agents-python`  
Root license: MIT  
Evidence: current README/package tree plus source-level tool-identity implementation.  
Initial grade: **S- direct comparison candidate for generic AgentRuntime/tool/session contracts**.

Codex and the Agents SDK should not be treated as the same architectural layer.

Current Agents SDK exposes:

- agents with instructions/tools/guardrails/handoffs;
- sandbox agents with persistent workspaces;
- realtime/voice agents;
- agents-as-tools and handoffs;
- function/MCP/hosted tools;
- human-in-the-loop;
- sessions/history management;
- tracing;
- provider-agnostic model use, including non-OpenAI models.

The SDK is intentionally lightweight compared with the full Codex app-server/state/client stack.

## 1.1 Tool identity is explicitly namespaced and persistable

The inspected `_tool_identity.py` distinguishes lookup identities such as:

- bare function tool;
- namespaced function tool;
- deferred top-level tool;
- hosted-MCP identity including server label and tool name;
- call/request identities.

Lookup keys serialize to a JSON-friendly form and can restore routing identity when a tool call returns without the namespace that was needed to disambiguate it.

This prevents a failure class relevant to JarvisOS:

> two providers/servers/plugins exposing the same short tool name must not collapse into one permission/routing identity.

The code also validates auto-derived function names against a bounded ASCII-safe shape rather than silently emitting invalid API names.

## 1.2 Approval identity must include the server/provider boundary

Hosted MCP approval extraction validates request ID, server label and tool name before constructing a persistent approval identity.

This independently agrees with Gemini CLI's policy engine and Jarvis's existing exact-packet authority philosophy:

```text
approval identity != display tool name
approval identity = origin/server + capability + exact call/request identity
```

A future Jarvis generic tool contract should preserve that tuple through persistence, UI approval and execution.

## 1.3 Sandbox agents expose a useful portability constraint

The current SDK distinguishes local Unix sandbox support from Windows, where the documented path is a Docker sandbox client or hosted sandbox.

Any proposal to reuse the SDK for Jarvis coding/engineering workers must therefore benchmark the exact Windows deployment path rather than assuming feature parity from a Unix example.

## 1.4 Candidate relation to existing #309 stack

```text
Codex
  full coding product/runtime + app-server/state/memory/client protocol

OpenAI Agents SDK
  generic agent/run/tool/session/HITL/tracing primitives

Hermes / Pydantic / MAF / Kimi core
  competing generic runtime layers
```

Jarvis should compare the generic layers separately from the complete coding clients.

---

# 2. Mem0 — useful memory algorithms, but managed benchmark claims are not OSS evidence

Upstream: `mem0ai/mem0`  
Root license: Apache-2.0  
Evidence: root/runtime structure plus explicit OSS-vs-managed boundary in current documentation.  
Initial grade: **A candidate for non-canonical agent/user memory experiments; not canonical engineering truth**.

The current open-source tree has separate packages for:

- memory core;
- embeddings;
- LLM adapters;
- vector stores;
- rerankers;
- proxy/server/client surfaces;
- telemetry.

Its main memory implementation is a substantial independent module rather than a thin SDK wrapper.

## 2.1 Do not use managed-platform benchmark numbers as proof of the OSS implementation

The current README explicitly states that its 2026 benchmark figures reflect a managed production stack with **proprietary optimizations not available in the open-source SDK**.

That is a blocker against a common audit error:

> “upstream benchmark > Jarvis result” is invalid if the benchmark did not execute the code we could actually integrate.

Any Jarvis bake-off must run the exact OSS commit/config locally against the same memory corpus and model stack.

## 2.2 Interesting current memory hypotheses

The documented newer algorithm emphasizes:

- ADD-only fact extraction instead of LLM UPDATE/DELETE decisions;
- agent-generated facts as first-class memories;
- entity linking;
- parallel semantic/BM25/entity retrieval signals;
- temporal ranking.

These are worth testing independently.

The ADD-only direction is particularly relevant to Jarvis because it reduces destructive LLM authority. However, accumulation alone creates new failure modes:

- contradiction growth;
- obsolete facts remaining retrievable;
- duplicate memories;
- storage/retrieval drift;
- hidden temporal precedence.

Jarvis should test whether explicit supersession/validity metadata, such as Graphiti-style temporal edges or canonical MemoryStore records, handles those cases better than deletion.

## 2.3 Recommended Jarvis role

Mem0 is a candidate for **derived/personal/agent working memory**, not for accepted engineering parameters, requirements or evidence.

A safe prototype should consume a bounded derivative of threads/accepted context and return retrieval candidates with source IDs. It must not gain direct authority to mutate MemoryStore canonical rows.

---

# 3. Cognee — graph/vector memory plus operational failure modes are exposed explicitly

Upstream: `topoteretes/cognee`  
Root license: Apache-2.0  
Evidence: current architecture/configuration documentation; deeper code pass still required before direct component reuse.  
Initial grade: **A candidate/reference for derived knowledge memory**.

Cognee combines ingestion, graph/vector retrieval and persistent/session memory with optional local/self-hosted operation.

Current product/runtime concepts include:

- permanent graph-backed memory;
- faster session memory with background graph synchronization;
- graph + vector retrieval;
- ontology/relationship construction;
- tenant/user isolation claims;
- OpenTelemetry/audit surfaces;
- API, CLI and MCP deployment;
- modular LLM/vector/graph backends.

## 3.1 Explicit background synchronization is a consistency problem, not only a latency optimization

Session memory can be read before background synchronization to the graph is complete.

A Jarvis prototype would therefore need exact semantics for:

- whether session memory or graph result wins on conflict;
- what “synced” means;
- retries after partial graph construction;
- stale reads while the background job is pending;
- deletion/forget propagation;
- process crash during synchronization.

Do not treat “eventually in graph” as a sufficient canonical-consistency model.

## 3.2 Operational documentation reveals a real concurrency guard

Cognee documents a dataset queue that protects concurrent processing and warns that disabling it can lead to file-lock leaks and resource exhaustion.

This is useful code-audit guidance: if Cognee is ever prototyped inside Jarvis, the queue/concurrency implementation and crash cleanup should be inspected before performance tuning removes it.

## 3.3 Candidate comparison

```text
Mem0     -> compact personalized/agent memory + retrieval
Graphiti -> temporal knowledge graph projection
Cognee   -> broader ingestion + session + graph/vector knowledge platform
Letta    -> stateful agent runtime with memory/approval/session lifecycle
Jarvis   -> canonical engineering records + episodic threads + governed derivatives
```

The correct outcome may be one narrow component from one project, not adoption of any full memory platform.

---

# 4. Tauri — frontend privilege should be capability-scoped at the IPC boundary

Upstream: `tauri-apps/tauri`  
Root project is dual MIT / Apache-2.0; inspected ACL source carries both SPDX identifiers.  
Evidence: source-level capability/ACL implementation.  
Initial grade: **S reference for a future packaged desktop Jarvis shell and frontend↔native authority**.

Tauri's capability model controls which windows/webviews may call application/core/plugin commands over IPC.

The inspected `Capability` structure supports:

- capability identity and human description;
- exact/window glob bindings;
- webview-specific binding;
- platform-specific activation;
- local/remote-origin distinction;
- remote URL pattern restrictions;
- permission-set identifiers;
- per-permission scope extensions, such as allowed filesystem paths.

Most importantly, the source documents this fail-closed rule:

> if a webview/window does not match a capability, it has no IPC access at all.

## 4.1 This is directly relevant to Jarvis frontend authority

Current/future Jarvis surfaces do not all require equal native power.

A packaged desktop architecture should be able to state, for example:

```text
main operator workbench
  -> bounded project/file/native capabilities

settings/secrets surface
  -> credential/settings capabilities

untrusted/remote/web content view
  -> no native IPC by default

plugin webview
  -> only plugin-specific scoped commands
```

A frontend XSS or compromised remote view should not automatically inherit every backend/native action merely because it runs in the same desktop application.

## 4.2 Capability identity should align with Jarvis authority but remain a separate layer

Tauri-style IPC capability is not the same as Jarvis engineering/business authorization.

Both may be required:

```text
Desktop IPC capability allows command transport
        AND
Jarvis policy approves exact action/workspace/arguments
        AND
executor performs + verifies effect
```

This prevents frontend privilege configuration from becoming the sole security policy.

## 4.3 Tauri sibling queue

If Jarvis moves from browser-served UI to a packaged desktop shell, inspect:

- Tauri IPC authority resolution;
- plugin permission generation/signing/distribution;
- updater behavior;
- filesystem/shell plugins;
- window/webview origin isolation;
- sidecar process lifecycle;
- compare with Electron's process/sandbox/contextIsolation model and existing VS Code extension-host evidence.

Do not choose Tauri/Electron solely on bundle size or UI taste; compare native-process authority, updater/signing, WebView compatibility and Windows operational behavior.

---

# 5. Updated memory authority model

The current memory wave strengthens a layered architecture:

```text
CANONICAL
Jarvis MemoryStore / engineering records / accepted evidence
  authoritative, explicit lifecycle, provenance, stale/supersession semantics

EPISODIC
threads / run histories / interaction state
  durable but not canonical engineering truth

WORKING / PERSONAL MEMORY
Mem0-like / Letta-like / local Markdown
  model-facing, mutable, bounded by workspace/user/agent identity

DERIVED SEMANTIC MEMORY
Graphiti / Cognee graph/vector projections
  rebuildable from explicit sources, never silently outranks canonical data

RETRIEVAL INDEX
FTS/vector/entity/code indexes
  disposable/rebuildable and freshness-bound
```

Any memory backend must declare which layer it implements before benchmark comparison. “Recall accuracy” alone cannot justify authority promotion.

---

# 6. New failure-mode requirements

1. **tool collision:** namespaced origin survives persistence, approval and tracing;
2. **cloud-vs-OSS evidence:** managed benchmark claims are not attributed to unavailable open-source code;
3. **ADD-only memory:** contradiction/obsolete/duplicate behavior is explicitly tested;
4. **background graph sync:** partial synchronization has observable state and deterministic recovery;
5. **memory tenant leakage:** project/user/agent identity isolation is tested adversarially;
6. **frontend compromise:** a low-privilege window/webview cannot access unrelated native IPC commands;
7. **remote origin:** remote web content receives no native authority unless explicitly scoped;
8. **two-layer authorization:** desktop IPC access never substitutes for Jarvis exact-action policy.

---

# 7. Next traversal

Still open and high-value:

- OpenAI Agents SDK session/HITL/sandbox implementation details and JS parity;
- Mem0 OSS `Memory.add/search` code paths and benchmark harness;
- Cognee dataset queue/session-to-graph synchronization implementation;
- Electron security/process model versus Tauri;
- Tauri sidecars/updater/plugin supply-chain;
- Google ADK concrete service interfaces;
- current Jupyter/Julia runtime bridges;
- remaining memory platforms only when they add a distinct mechanism;
- exact `REF-000` Jarvis runtime comparison after discovery coverage is sufficient.

No runtime integration, deletion, dependency adoption or product-queue change is authorized by this audit.