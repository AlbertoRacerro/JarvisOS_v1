# Core software ecosystem audit — continuation — 2026-08-20

Status: exploratory code-first continuation; **not implementation authority**  
Parent: `CORE_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-20.md`  
Canonical implementation authority remains `docs/specs/STATUS.md`.

This continuation follows the graph outward from the first OpenAI/Anthropic/Moonshot/Serena/Wolfram pass into Google, protocol standards, Microsoft's current agent stack, durable/checkpoint infrastructure, WebAssembly plugins and GenAI observability.

---

# 1. Google Gemini CLI — another full core-runtime candidate

Upstream: `google-gemini/gemini-cli`  
Root license: Apache-2.0  
Evidence: CODE-FIRST for policy/tool registry; repository/package structure inspected for the rest.  
Initial grade: **S-** as architecture/reference and possible reusable package family.

The current repository is not merely a terminal wrapper around Gemini. Its package boundary currently includes:

- `packages/core`;
- `packages/cli`;
- `packages/sdk`;
- `packages/a2a-server`;
- `packages/vscode-ide-companion`;
- developer/test utility packages.

The core package contains an explicit policy engine, tool registry, telemetry, prompt/provider/config layers, agents/local execution, sandbox services and MCP machinery.

## 1.1 Policy engine: authority is richer than an allowlist

The inspected `packages/core/src/policy/policy-engine.ts` matches rules against combinations of:

- exact or wildcard tool identity;
- MCP server identity;
- subagent identity;
- approval mode;
- tool annotations;
- stable-stringified argument patterns;
- interactive/non-interactive mode;
- trusted/untrusted workspace state;
- shell parse details;
- sandbox knowledge of dangerous/safe commands.

Several failure-mode choices are directly relevant to JarvisOS:

1. **MCP server identity is part of policy**, so two servers exposing the same short tool name do not silently inherit the same authority.
2. **Untrusted workspace changes command policy**, particularly around Git.
3. Shell parser failure does not become permissive by accident. In normal mode the engine falls back to the configured default (`ASK_USER`, or `DENY` for non-interactive); even in permissive/YOLO mode a rule with argument restrictions fails closed if the arguments cannot be validated.
4. Known-safe shell commands may reduce prompting, but only after successful parsing and other workspace conditions.
5. Dangerous-command handling is separate from ordinary rule matching and is mediated through a sandbox manager.

Candidate Jarvis rule:

```text
PolicyDecision = f(
  actor,
  workspace trust,
  capability identity,
  provider/server identity,
  exact arguments,
  mode,
  annotations,
  sandbox state,
  interaction availability
)
```

not merely `tool_name in allowed_tools`.

## 1.2 Tool registry: known, active and executable are distinct states

`ToolRegistry` explicitly stores all known tools while documenting that callers must use active-tool queries for tools currently usable. This is a useful semantic separation for JarvisOS.

The project also supports project-discovered tools. The inspected invocation path:

- obtains configured discovery/call commands;
- sends tool parameters over stdin as JSON;
- optionally asks the sandbox manager to prepare the process command/environment;
- captures stdout/stderr/error/exit code/signal;
- returns structured tool errors on any failed subprocess outcome.

Important caveat: this is not by itself a complete hostile-code sandbox. Jarvis should compare the sandbox path separately against OpenShell/Extism/hard OS isolation before allowing untrusted discovered commands.

## 1.3 Gemini CLI's package graph exposes a useful product split

The coexistence of core + CLI + SDK + A2A server + IDE companion supports a recurring architectural conclusion:

> the terminal/UI is a client of a reusable agent/runtime core, not the core itself.

JarvisOS should be evaluated for the same property: frontend, future desktop shell, CLI/testing harness and external clients should converge on typed runtime contracts rather than each owning a separate execution path.

## 1.4 Google next traversal

Continue through:

1. Gemini CLI sandbox manager and confirmation bus;
2. config layering / schema / last-known-good behavior;
3. A2A server implementation and SDK boundary;
4. telemetry and content-redaction behavior;
5. Google ADK current repositories;
6. A2A upstream and SDKs independently from Gemini CLI;
7. Google/DeepMind repositories only where source exposes runtime/tool/eval/memory/protocol primitives, not model-only research artifacts.

---

# 2. A2A — agent-to-agent is a third protocol layer, not MCP or ACP

Upstream: `a2aproject/A2A` under the Linux Foundation  
License: Apache-2.0  
Evidence: protocol repository/docs + current multi-language SDK inventory.  
Initial grade: **S- standard/interoperability target**.

The current A2A project describes a protocol for communication between **opaque agentic applications** running on separate servers/frameworks.

It supports:

- capability discovery through Agent Cards;
- JSON-RPC 2.0 over HTTP(S);
- synchronous responses;
- SSE streaming;
- asynchronous push notifications;
- text/files/structured JSON;
- long-running task collaboration;
- authentication/security/observability concepts;
- operation without exposing the remote agent's internal tools, memory or implementation.

Current official SDKs include Python, Go, JS, Java, .NET and Rust.

## 2.1 Keep the protocol taxonomy explicit

The audit now has three separate standards-level boundaries:

```text
MCP  -> model/agent <-> tools, resources and context servers
ACP  -> interactive agent runtime <-> client/editor/UI session
A2A  -> opaque agent application <-> opaque remote agent application
```

They overlap at the product edge but solve different ownership problems.

Do not create a universal “Jarvis MCP” abstraction that hides these distinctions.

## 2.2 Potential JarvisOS role

A2A is particularly relevant if Jarvis later delegates to:

- remote specialist engineering agents;
- a lab/edge/server agent owned by another machine/team;
- cloud agent products that should remain opaque;
- partner/vendor agents where exposing internal MCP/tool registries is undesirable.

Jarvis authority should still own whether the remote task may be dispatched and what data may leave the workspace. A2A interoperability is not egress authorization.

---

# 3. Microsoft — the current target is Agent Framework, not historical AutoGen alone

## 3.1 Serendipitous correction to the initial audit queue

Searching Microsoft's current ecosystem found `microsoft/agent-framework`, which explicitly provides migration guides **from Semantic Kernel and AutoGen**. Therefore a new audit that focused only on AutoGen/Semantic Kernel would start from an outdated architecture frame.

AutoGen and Semantic Kernel remain valuable genealogy/reference material, but the primary current comparison target is Microsoft Agent Framework (MAF).

Upstream: `microsoft/agent-framework`  
Root license: MIT  
Initial grade: **S candidate/reference**.

## 3.2 Current MAF capability surface

The current source/repository advertises and exposes a multi-language Python/.NET architecture including:

- multiple model/provider integrations;
- middleware around request/response/error pipelines;
- graph workflow/orchestration patterns;
- sequential, concurrent, handoff and group collaboration;
- checkpointing;
- streaming;
- human-in-the-loop;
- time-travel;
- OpenTelemetry integration;
- declarative YAML agents;
- agent skills;
- A2A/self-hosted/Foundry hosting patterns;
- developer UI;
- experimental lab/evaluation/RL packages.

This overlaps strongly with capabilities JarvisOS has built separately across provider routing, review/agents, persistence, jobs, UI and telemetry.

The correct question is not “integrate MAF wholesale”. It is:

> which MAF packages/contracts replace duplicated generic agent/runtime plumbing while Jarvis retains engineering identity, MemoryStore, sensitivity/egress, budget, canonical evidence and BLUECAD authority?

## 3.3 Provider convenience has a security cost

MAF's own README warns that broad development credential helpers such as `DefaultAzureCredential` can create latency, unintended credential probing and fallback-security risk in production, recommending a specific credential mechanism instead.

This aligns with Jarvis's existing fail-closed provider/secret boundary: convenience credential discovery must not silently become production authority.

## 3.4 Durable execution is a separate extension

`microsoft/agent-framework-durable-extension` is maintained as a separate repository/package family. It contains .NET and Python Durable Task integration, durable agents/workflows and Azure Functions hosting.

This separation is architecturally useful even if Jarvis never adopts Microsoft's durable stack:

- basic agent runtime does not need to carry all durable workflow operational weight;
- durability can remain an independently removable adapter;
- integration tests require substantial local infrastructure (scheduler emulator, Azurite, Redis and additional hosting tooling), which demonstrates the real operational cost of “durability”.

For current single-user/local Jarvis, preserve the minimum-necessary test: do not adopt a distributed durable stack until restart/resume/idempotency needs exceed the current SQLite/job solution.

## 3.5 Microsoft sibling queue

Priority order after MAF:

1. MAF source around workflow checkpoints, middleware, tools, skills, persistence and protocol hosting;
2. durable extension exact replay/idempotency/failure semantics;
3. AutoGen and Semantic Kernel only to identify mechanisms retained, removed or redesigned in MAF;
4. `microsoft/magentic-ui` for human/agent UI interaction patterns if it adds non-overlapping runtime evidence;
5. `microsoft/SafeAgents`, `azure-trust-agents` and agent-governance siblings when they expose executable security mechanisms beyond the governance toolkit already audited;
6. `TaskWeaver` as archived historical evidence where its plugin/code-interpreter mechanisms illuminate why current designs changed;
7. avoid tutorials/sample megarepos unless they expose a unique implementation contract.

---

# 4. LangGraph — checkpoint conformance is more interesting than another agent graph

Upstream: `langchain-ai/langgraph`  
Root license: MIT  
Evidence: current checkpoint code/package layout and conformance-test inventory.  
Initial value: **A+ for checkpoint/persistence contracts; lower priority for generic agent orchestration unless benchmarks justify it**.

The current repository contains independently structured checkpoint packages:

- base checkpoint interface;
- in-memory implementation;
- PostgreSQL implementation;
- async/sync variants;
- a dedicated `checkpoint-conformance` package with tests over supported backend behavior;
- migration tests in the runtime.

The checkpoint contract carries explicit concepts such as thread identity, checkpoint namespace/ID, pending writes and history/list semantics.

## 4.1 Reusable lesson: persistence backends need a conformance suite

Jarvis currently has several persistence authorities and derived stores. A useful pattern from LangGraph is:

```text
Checkpoint / State contract
          |
          +-- SQLite/local implementation
          +-- future alternative implementation
          |
          +-- same conformance battery
```

The conformance suite should test semantic behavior, not merely API success:

- round-trip identity;
- ordering/history;
- pending/intermediate writes;
- pruning;
- migration;
- namespace/thread isolation;
- retry/replay behavior.

This is potentially more valuable than adopting LangGraph's entire graph execution model.

---

# 5. Extism — a serious candidate for future sandboxed plugin execution

Upstream: `extism/extism`  
Root license: BSD-3-Clause  
Evidence: current root implementation/docs and SDK/PDK ecosystem.  
Initial grade: **A+ candidate for a bounded extension host**.

Extism is a cross-language WebAssembly plugin framework with current support across Rust, JS, Go, Java, .NET, Python, C/C++, Zig and others.

Relevant host-controlled capabilities include:

- arbitrary Wasm plugin execution;
- persistent module memory/variables;
- host-controlled HTTP rather than unrestricted WASI networking;
- runtime limiters/timers;
- host-function linking;
- typed/generated bindings through an IDL toolchain;
- Windows targets, including x86_64 MSVC.

## 5.1 Potential Jarvis role

A future Tier-2 engineering-validator/plugin interface could use:

```text
Jarvis capability manifest / policy
          |
          v
Extism host
  explicit host functions
  explicit network/config permissions
  time/memory limits
          |
          v
third-party validator/tool compiled to Wasm
```

This can be materially safer and more portable than importing arbitrary Python plugin code into the Jarvis process.

## 5.2 Important non-goal

Extism/Wasm is not automatically the correct runtime for:

- full CAD kernels;
- native GPU solvers;
- tools requiring broad OS/device access;
- existing executables that already have a safe process boundary.

For those, OpenShell, external subprocess/service adapters or native library boundaries may remain better.

The eventual bake-off should compare at least:

`in-process plugin` vs `MCP subprocess` vs `ordinary subprocess` vs `OpenShell` vs `Extism/Wasm`.

---

# 6. OpenTelemetry GenAI — do not invent a proprietary tracing vocabulary by default

Current upstream: `open-telemetry/opentelemetry-python-genai` plus the wider OpenTelemetry semantic-conventions ecosystem.

The current GenAI Python repository emits spans, metrics and logs using GenAI semantic conventions and already contains released instrumentation for:

- Anthropic;
- OpenAI;
- OpenAI Agents SDK;
- Google GenAI;
- LangChain;
- Qwen Agent;
- smolagents;
- Agno;

with additional framework instrumentation under development, including Claude Agent SDK and LlamaIndex.

## 6.1 Jarvis use

JarvisOS already has product-specific canonical flow, cost, egress and evidence records. Those should remain domain authority.

OpenTelemetry is instead a strong candidate for the **operational correlation substrate**:

```text
Jarvis AgentRun / Run / Attempt IDs
        |
        +-- provider/model spans
        +-- tool spans
        +-- MCP/A2A/ACP calls
        +-- backend/solver process spans
        +-- DB/cache spans
        +-- frontend request correlation
```

Do not make tracing data the canonical source for engineering truth or provider spend. Traces may be sampled/dropped and often contain sensitive payload risks.

## 6.2 Privacy gate

Before enabling GenAI auto-instrumentation:

- inspect exactly which prompts/completions/tool args are captured;
- default to identifiers, timing, model/provider, token/cost counters and safe metadata;
- require explicit policy for prompt/tool-content capture;
- ensure secrets and S2/S3 engineering content do not leak into exporters/log backends.

---

# 7. Updated protocol/runtime map

The audit now has enough independent evidence to avoid one overloaded “integration” abstraction.

```text
                           JARVIS AUTHORITY CORE
        identity / workspace / policy / egress / budget / provenance
                                      |
             +------------------------+-------------------------+
             |                        |                         |
             v                        v                         v
       AgentRuntime               Capability                Runtime bridge
  Codex/Kimi/MAF/...         native / MCP / Serena      subprocess/native/Wasm
             |                        |                         |
             +-----------+------------+-------------------------+
                         |
                         v
                  Client / remote protocols
             ACP            A2A             HTTP/app protocol
       agent<->client   agent<->agent      product-specific
```

Protocol choice should follow ownership/lifecycle semantics, not whichever acronym already exists in the repository.

---

# 8. New failure-mode checklist created by this continuation

Any future Jarvis core redesign should explicitly test:

1. **parser failure:** authority becomes ASK/DENY, not implicit allow;
2. **server/name collision:** same short tool name from distinct MCP/server/plugin origins does not inherit authority;
3. **known vs active capability:** inactive/disconnected tools are not presented as executable;
4. **workspace trust:** commands that are harmless in a trusted repo may require confirmation in an untrusted one;
5. **checkpoint backend drift:** alternative persistence implementations satisfy one semantic conformance suite;
6. **replay/idempotency:** durable workflow replay does not repeat side effects;
7. **credential probing:** provider helper chains do not silently try unintended identities/accounts;
8. **Wasm/plugin escape:** plugin receives only declared host capabilities and bounded resources;
9. **trace leakage:** observability does not become an alternate egress channel for prompts/secrets/engineering data;
10. **protocol ID conflation:** MCP/ACP/A2A/provider/local IDs retain explicit namespaces and ownership.

---

# 9. Next graph traversal

This continuation deliberately leaves the audit open. Highest-value next branches:

## Google / DeepMind

- Gemini CLI sandbox, confirmation bus, config and telemetry source;
- Google ADK Python/TS/Java/Go current package boundaries;
- A2A official SDK implementation and auth/task-state semantics;
- DeepMind executable agent/eval/reasoning/tool projects where source—not a paper claim—adds unique machinery.

## Microsoft

- MAF workflow/persistence/tool/middleware source and design records;
- Durable extension replay/idempotency internals;
- AutoGen/Semantic Kernel migration deltas;
- Magentic UI and security siblings only for non-overlapping mechanisms.

## Memory / state

- Letta Code source-level memory/identity lifecycle;
- Graphiti temporal contradiction/supersession behavior;
- Mem0 and Cognee;
- LangGraph Store/checkpointer separation;
- SQLite/Litestream-like recovery only if current local durability tests reveal a need.

## Extensions / isolation

- Wasmtime/WASI component model beneath/alongside Extism;
- Extism Python/.NET SDK exact host controls;
- VS Code extension-host isolation and crash/restart boundaries;
- plugin update/signature/provenance systems;
- compare against OpenShell, MCP subprocess and Jarvis's existing runner registry.

## Observability

- OpenTelemetry GenAI semantic conventions and redaction controls;
- Pydantic Logfire only if it adds useful agent-specific semantics without creating a second telemetry authority;
- end-to-end trace propagation through external engineering solvers/services.

## Other labs/companies

Continue relevance-scoped traversal across Meta/FAIR, AllenAI, Berkeley/Stanford labs, Hugging Face siblings not already audited, Sourcegraph, Jupyter, Julia and other mature software/runtime organizations. Follow newly discovered upstreams rather than forcing the search back into a fixed list.

---

# 10. Promotion remains prohibited by this audit

No finding here changes the live JarvisOS queue or authorizes replacing code. Promotion requires the `REF-000` runtime comparison, exact-version/license review, minimal prototype, deterministic acceptance tests and explicit governing ADR/spec.