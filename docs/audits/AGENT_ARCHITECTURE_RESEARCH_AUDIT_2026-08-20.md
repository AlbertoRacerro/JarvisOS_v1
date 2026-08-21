# Agent Architecture Research Audit — 2026-08-20

Status: research/intake evidence only; **not implementation authority**.  
Purpose: extract architectural principles for a later JarvisOS strategy document and backend "puzzle" plan.  
Queue boundary: complete the current product queue first, then the planned frontend visual-identity phase, then separately authorize any backend architecture queue.

## Method

Papers are treated as research evidence, not implementation proof. Where a current source repository exists, repository/licensing evidence is considered separately. A paper can justify a design hypothesis or benchmark, but it does not authorize copying code or replacing current JarvisOS components.

The central question is not "which agent framework is best?" It is:

> What must JarvisOS itself own canonically, and what should remain replaceable behind contracts?

---

## 1. AIOS — LLM Agent Operating System

Paper: https://arxiv.org/abs/2403.16971  
Repository: https://github.com/agiresearch/AIOS

### Research contribution

AIOS separates agent applications from an OS-like kernel that owns shared services and resource management: scheduling, context, memory, storage, access control, LLM access and external tools. Agents consume those services through an SDK rather than each rebuilding them.

### Jarvis interpretation

This supports a **kernel/adapters split**, but not necessarily AIOS's exact kernel contents.

Strong candidate Jarvis-owned kernel responsibilities:

- canonical identity and object IDs;
- authorization/policy and approval binding;
- canonical state transitions;
- evidence/provenance;
- secrets/egress boundaries;
- budgets/leases/cancellation;
- execution manifests and verification;
- adapter capability registry.

Likely replaceable services behind contracts:

- generic agent loops;
- model/provider clients;
- code intelligence;
- sandbox implementations;
- derived retrieval/indexes;
- training/inference runtimes.

### Important license caveat

The current AIOS repository reports NOASSERTION and its root `LICENSE` file is effectively empty. Treat AIOS as **REFERENCE_ONLY** until a usable license is explicitly established.

### Grade

Architecture reference: **S-**. Direct dependency: **blocked by license clarity**.

---

## 2. ESAA — Event Sourcing for Autonomous Agents

Paper: https://arxiv.org/abs/2602.23193

### Research contribution

ESAA separates probabilistic cognitive intent from deterministic project mutation. Agents emit structured intentions; an orchestrator validates and appends events, applies effects, maintains a materialized view and supports replay/hash verification.

### Why it matters to Jarvis

This is one of the closest research matches to the desired authority boundary.

Candidate canonical rule:

> An LLM/runtime may propose a mutation, but only a deterministic Jarvis authority layer commits canonical state.

A future state mutation pipeline could be:

`proposal -> schema validation -> policy/approval -> precondition check -> append event -> deterministic effect -> postcondition verification -> materialized projection -> evidence`

Potential benefits:

- resume/replay after crashes;
- provenance of every change;
- stale-action rejection;
- deterministic audit of multi-agent work;
- easier rollback/reprojection;
- separation of UI/chat transcript from actual state truth.

### Caution

ESAA is a recent preprint and its case studies are not enough to prove production scalability. Adopt the principle only after prototyping against Jarvis-specific state and failure cases.

### Grade

Architecture hypothesis: **S**. Needs prototype before promotion.

---

## 3. MemGPT — virtual context management

Paper: https://arxiv.org/abs/2310.08560

### Research contribution

MemGPT treats the limited LLM context as a fast tier and moves information between multiple memory/storage tiers, inspired by virtual memory.

### Jarvis interpretation

The useful idea is **tiered context**, not LLM ownership of truth.

Recommended separation:

- canonical store: authoritative objects/evidence;
- episodic store: thread/run/event history;
- derived semantic/index store: vector/graph/search projections;
- working context: bounded temporary model-visible pack.

The model may request context promotion/eviction, but should not silently rewrite canonical engineering truth.

### Grade

**A+** for context-management principle; not a canonical-memory design by itself.

---

## 4. SWE-agent / Agent-Computer Interface (ACI)

Paper: https://arxiv.org/abs/2405.15793

### Research contribution

SWE-agent shows that interface design is a first-order determinant of agent performance. Agents should not merely receive human-oriented interfaces; tool surfaces can be designed specifically for machine users.

### Jarvis interpretation

Do not expose every subsystem through raw shell, giant JSON blobs or UI automation when a narrow typed operation is possible.

A Jarvis tool contract should optimize for:

- small structured input;
- stable identity;
- explicit preconditions;
- bounded output;
- canonical error classes;
- deterministic effect verification;
- resumability/idempotency where applicable.

This also supports separating human UI affordances from agent APIs over the same underlying engineering object.

### Grade

**S** as interface-design evidence.

---

## 5. ToolSandbox — stateful tool-use evaluation

Paper: https://arxiv.org/abs/2408.04682  
Repository: https://github.com/apple/ToolSandbox

### Research contribution

ToolSandbox evaluates agents in stateful environments with implicit dependencies, conversational interaction and intermediate/final milestones, including difficult categories such as state dependency, canonicalization and insufficient information.

### Jarvis interpretation

Jarvis tool evaluation should not be reduced to `did function_call parse?`.

A future tool qualification suite should include:

- pre-existing state;
- hidden/implicit dependency state;
- missing required information;
- stale state;
- canonicalization/normalization;
- partial progress milestones;
- wrong-but-plausible tool output;
- interruption/retry;
- duplicate/idempotent requests;
- postcondition verification.

This complements Harbor/Verifiers rather than replacing them.

### Grade

**S-** for evaluation methodology.

---

## 6. Agent Lightning — Training-Agent Disaggregation

Paper: https://arxiv.org/abs/2508.03680

### Research contribution

Agent Lightning proposes separating agent execution from reinforcement-learning/training infrastructure through a trajectory/transition interface, so diverse agents can be trained without embedding training logic inside each runtime.

### Jarvis interpretation

This strongly supports a future architecture where:

`Jarvis/agent runtime -> normalized trajectory/evidence stream -> training/evaluation backend`

Training backends such as Unsloth, SERA, Axolotl/TRL/PEFT or future alternatives should consume recorded trajectories without owning production execution.

### Grade

**A+** for future specialist-training architecture.

---

## 7. AgentScope research + AgentScope 2.0 implementation

Paper: https://arxiv.org/abs/2402.14034  
Repository: https://github.com/agentscope-ai/agentscope

### Research/implementation contribution

The current Apache-2.0 AgentScope 2.0 implementation has moved far beyond simple message passing. It now includes event, permission/HITL, middleware, sandbox/workspace, memory backends, persistence, multi-session/multi-tenant services, MCP/skills and scheduling.

### Jarvis interpretation

Two separate lessons:

1. runtime subsystems can be modular and independently replaceable;
2. a generic framework may already implement enough plumbing that Jarvis should not re-create it without a benchmark.

AgentScope belongs in the later exact `AgentRuntime` bake-off.

### Grade

**S- candidate implementation/reference**.

---

## 8. Instruction hierarchy / untrusted tool output

Paper: https://arxiv.org/abs/2404.13208

### Research contribution

The instruction-hierarchy line of work formalizes privilege ordering between system/developer/user/model/tool content and targets indirect prompt injection from lower-trust tool outputs.

### Jarvis interpretation

Jarvis should enforce trust boundaries structurally, not rely only on the model remembering a warning.

Candidate information classes:

- policy/system authority;
- maintainer/user intent;
- canonical repository/engineering state;
- verified tool result;
- untrusted external/tool content;
- derived model interpretation.

Untrusted content should not be able to grant capabilities, change policy, mark work verified or directly mutate canonical state.

### Grade

**S-** for trust-model design.

---

## 9. Capability-based least privilege for agents

Relevant research family:

- Progent: programmable privilege control for LLM agents;
- capability-safe / tracked-capability agent systems;
- recent attenuating capability-token approaches for multi-agent shared state.

### Jarvis interpretation

A flat `allowed_tools=[...]` list is likely too weak for the long-term system.

A stronger future authority object should be able to bind:

- actor/agent identity;
- exact capability/action;
- resource/object scope;
- operation/read-write scope;
- argument constraints;
- budget/time/lease;
- sensitivity/egress class;
- delegation rules;
- approval identity;
- expiry/revocation.

Capabilities should be **attenuating**: a delegated child capability may become narrower, never silently broader.

This is consistent with findings from Tauri ACL, Google Gemini policy, OpenAI tool identity, Agent Governance Toolkit and OpenShell.

### Grade

**S architectural direction**, but implementation mechanism remains to be selected.

---

## 10. A-MEM / linked agent memory

Paper: https://arxiv.org/abs/2502.12110

### Research contribution

A-MEM uses dynamically linked memories inspired by Zettelkasten and can update representations/links as new memories arrive.

### Jarvis interpretation

This is useful only for **derived/personal/semantic memory**. Historical canonical records must not be silently rewritten merely because a new model interpretation appears.

Safe boundary:

`immutable/canonical source evidence -> mutable derived memory graph/index`

Derived links can be regenerated and discarded.

### Grade

**A-** for derived memory; **REJECT** as canonical truth model.

---

## 11. Multi-agent shared state / blackboard patterns

Blackboard-style multi-agent research shows useful coordination benefits from a shared workspace, dynamic role selection and centralized intermediate artifacts.

### Jarvis interpretation

A single unrestricted shared blackboard would be a security/provenance hazard. If used, it should be a **derived coordination projection** over canonical records with per-field/per-object authority and provenance.

Do not let "shared context" become equivalent to "shared write authority".

### Grade

**B+** pattern with strict authority constraints.

---

## 12. Consolidated candidate architecture

The research and source audit now converge on a provisional decomposition.

### 12.1 Jarvis authoritative kernel

JarvisOS should probably own only the product-specific invariants that cannot be delegated safely:

- identity: user, agent, workspace, engineering object, run/action IDs;
- policy, capability and approval authority;
- canonical engineering/application state transitions;
- event/evidence/provenance log;
- secrets and egress classification;
- budgets, leases, cancellation and concurrency ownership;
- adapter registry and capability qualification;
- deterministic verification/postconditions.

### 12.2 Replaceable runtime plane

Behind typed contracts:

- generic agent loops: Codex/Kimi/AgentScope/Pydantic/Microsoft/Hermes/etc.;
- models/providers: cloud and local;
- inference: llama.cpp/vLLM/Unsloth/DwarfStar/Ollama/etc.;
- sandbox: OpenShell/container/WASM/other;
- code intelligence: Serena/LSP/Tree-sitter;
- derived memory: Graphiti/Mem0/Cognee/Letta/indexes;
- training: SERA/Unsloth/Axolotl/TRL/PEFT/etc.

### 12.3 State mutation plane

Provisional rule:

`agent proposal != state mutation`.

Only the Jarvis authority layer should turn a validated proposal into a canonical event/effect. External runtimes can be changed without invalidating canonical history.

### 12.4 Observation/evaluation plane

Every runtime/tool/backend should emit a normalized evidence envelope with:

- actor/runtime/model/tool identity;
- input/object version;
- action/proposal ID;
- policy/approval decision;
- timing/cost/resource usage;
- raw/structured result reference;
- postcondition/verification status;
- errors/retries/fallbacks.

This stream can feed observability, benchmark suites and later specialist training without coupling those systems to production authority.

---

## 13. Strategic document that should come after audit closure

A separate future document should convert the audit into explicit decisions. It should not be written as a generic wish list. For every current Jarvis subsystem, require one disposition:

- `KEEP_JARVIS`;
- `REPLACE_WITH_UPSTREAM`;
- `WRAP_UPSTREAM`;
- `HYBRID`;
- `DELETE`;
- `PARK`.

For each disposition record:

1. current implementation and failure modes;
2. competing upstreams;
3. canonical owner of state/authority;
4. contract/interface between parts;
5. migration path and backward compatibility;
6. deterministic acceptance tests;
7. Windows/local/offline constraints;
8. license/SBOM boundary;
9. rollback strategy;
10. queue dependency and sequencing.

Only after that strategic document is reviewed should a future backend "puzzle" queue be derived.

**Hard sequencing constraint:** this research must not interrupt the currently active queue. Finish the current queue, complete the frontend visual-identity phase, and only then begin implementation from the later backend puzzle queue.
