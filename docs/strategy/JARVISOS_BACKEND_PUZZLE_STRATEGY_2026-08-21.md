# JarvisOS Backend Puzzle — Strategic Architecture and Replacement Plan

Status: **STRATEGY ONLY — NOT IMPLEMENTATION AUTHORITY**  
Prepared: 2026-08-21  
Runtime baseline inspected: `master@3ca34a83fc7b960aa9f899bf7482bd8ce3720c16`  
Upstream evidence source: candidate register and dated audits produced by PR #309  
Authority: `docs/specs/STATUS.md` remains the sole live queue/spec/implementation authority.

## 0. Hard sequencing boundary

This document deliberately does **not** change the active product queue.

Required product order remains:

1. finish the currently active functional queue;
2. complete the frontend visual-identity phase;
3. only then derive, authorize and implement the backend **puzzle** queue from a fresh exact-master revalidation of this strategy.

At preparation time, 058c `SCENE-SEMANTICS-A1` is the sole authorized runtime implementation front and PR #319 is the active draft implementation. Nothing in this strategy may compete with, redirect or silently broaden that work.

The purpose of this document is to prevent a later backend overhaul from becoming a pile of unrelated integrations. It defines **ownership boundaries, candidate dispositions, target contracts, deletion candidates, migration gates and dependency order** while implementation is still forbidden.

---

# 1. Executive decision

The audit does **not** support replacing JarvisOS with one upstream agent framework.

It supports a different architecture:

> **Keep a small authoritative Jarvis kernel and make AI agents, tools, sandboxes, model runtimes, code intelligence, derived memory and engineering solvers replaceable adapters around it.**

The key invariant is:

`agent/model proposal != canonical state mutation`

Three authorities must remain independently enforceable:

`capability authority != information-flow/egress authority != state-commit authority`

A worker may be allowed to read a value without being allowed to send it outside the machine. A worker may be allowed to compute a candidate result without being allowed to promote it into canonical engineering state. A tool may be visible to a model without being invocable under the current grant.

This architecture is intentionally asymmetric:

- **Jarvis owns authority, canonical engineering identity, canonical evidence/state transitions and postcondition acceptance.**
- **Upstreams own generic capabilities when they are already better at them:** agent loops, MCP plumbing, sandbox primitives, inference engines, LSP/symbol intelligence, derived-memory indexes, numerical solvers, telemetry exporters and training stacks.

The desired system is therefore a **federated control plane**, not a mega-agent and not a mega-backend.

---

# 2. What the current JarvisOS already does well

The zero-sunk-cost audit still finds several incumbent subsystems worth preserving.

## 2.1 Egress authority is a real Jarvis strength

Current evidence:

- `backend/app/modules/ai/egress_authority.py`
- `egress_confirmation_core.py`
- `egress_lifecycle.py`
- `egress_persistence.py`
- `egress_policy.py`
- `egress_revalidation.py`
- `egress_runtime.py`
- `egress_sanitizer.py`
- `egress_service.py`
- `egress_spine.py`
- `backend/app/modules/ai/sensitivity.py`

The current code already distinguishes `eligible / pause / deny`, hashes exact raw prompts, applies deterministic sensitivity floors, refuses S4 secret-bearing input, keeps external-eligible body separate from raw input, and supports local-only sanitization/approved derivatives.

**Disposition: `KEEP_JARVIS` + targeted `HYBRID`.**

Do not replace this authority with an agent framework's generic permission callback. Add Rizzo-pii-style deterministic PII/checksum transforms and NanoClaw-style credential/egress isolation **under this authority**, not instead of it.

## 2.2 Canonical memory/evidence already has promotion semantics

Current evidence:

- `backend/app/modules/memory/models.py`
- `backend/app/modules/memory/service.py`
- `backend/app/modules/memory/replacement.py`
- `backend/app/modules/flowsheet/freshness.py`
- `backend/app/modules/events/service.py`

The current memory domain already distinguishes:

- `proposed / accepted / rejected / superseded`;
- origins such as `user / ai_proposed / calc`;
- AI proposal provenance through `source_ai_job_id`;
- accepted-parameter replacement as an atomic transaction;
- downstream freshness invalidation and graph digest evidence.

This is materially stronger than treating vector memory or an agent notebook as truth.

**Disposition: `KEEP_JARVIS`.**

Derived memory products may index or infer over canonical records, but they must never bypass the promotion boundary.

## 2.3 Provider/routing policy is already substantial

Current evidence:

- `backend/app/modules/ai/provider_registry.py`
- `backend/app/modules/ai/contracts.py`
- `backend/app/modules/ai/routing/*`
- `backend/app/modules/ai/budget.py`
- `backend/app/modules/ai/costs.py`

The incumbent already carries provider/model identity, route classes, context windows, max output, pricing versions/effective dates, execution classes, network requirements, cost/token caps and fallback chains.

**Disposition: `HYBRID`, with Jarvis remaining policy owner.**

The local inference engines below it should become replaceable. The registry itself should be consolidated because provider/model concepts currently appear in more than one internal registry representation.

## 2.4 Engineering identity, evidence and verification belong in Jarvis/BLUECAD

Current evidence includes:

- `backend/app/modules/bluecad/*`
- `backend/app/modules/process_kernel/*`
- `backend/app/modules/flowsheet/*`
- `backend/app/modules/runner/input_contracts.py`
- `backend/app/modules/runner/process_kernel_registration.py`
- FEM verification battery/parsers/sampling/analytics
- CAD-link topology preflight/execute/reconciliation/source contracts

The upstream engineering audit strongly supports reusing external numerical kernels, but not outsourcing BLUECAD's canonical engineering IR, provenance, run manifests, object identity or verified result ingestion.

**Disposition: `KEEP_JARVIS` for engineering authority; `WRAP_UPSTREAM` for numerical engines.**

---

# 3. What should not survive merely because it already exists

## 3.1 Generic agent abstraction is effectively a placeholder

Current files:

- `backend/app/modules/agents/base.py`
- `backend/app/modules/agents/registry.py`

Current `Agent` is only a protocol carrying `name` and a list of two-field capabilities. The registry is an in-memory dictionary keyed by name. It has no durable session lifecycle, interruption/resume, tool identity, permissions, checkpointing, transport, sandbox ownership, event contract or provider independence comparable to the audited runtimes.

**Disposition: `REPLACE_WITH_UPSTREAM` / `DELETE` after cutover.**

Do not invest in turning this stub into another home-grown AgentScope/Codex/Kimi/OpenCode.

## 3.2 Generic tool abstraction is also a placeholder

Current files:

- `backend/app/modules/tools/base.py`
- `backend/app/modules/tools/registry.py`

Current `Tool` is name + `run(dict) -> ToolResult`; registry is another in-memory dictionary keyed by name. It lacks namespaced identity, schema/version, authority requirements, read/write resources, idempotency, side-effect class, MCP provenance, cancellation, streaming, approval binding or conformance.

**Disposition: `REPLACE_WITH_UPSTREAM` / `DELETE` after ToolGateway cutover.**

The richer existing AI/runner authority must wrap the replacement.

## 3.3 Host Python preflight is not an OS sandbox

Current runner safety is valuable:

- exact path containment;
- canonical JSON and size limits;
- import/name allowlists;
- forbidden marker/AST checks;
- clean environment for local Python;
- timeout and output bounds;
- artifact constraints.

But `backend/app/modules/runner/local_python.py` ultimately invokes the host interpreter with `subprocess.run`. These application-level checks are not a hostile-code OS boundary.

**Disposition: `HYBRID`.** Keep preflight and evidence contracts; wrap untrusted/generated execution in a proven sandbox runtime. After sandbox admission is proven, direct host execution must be restricted to explicitly trusted bundled implementations.

## 3.4 Narrow Ollama lifecycle should not become the universal local-AI control plane

`backend/app/modules/local_ai/runtime/lifecycle.py` currently knows how to discover/start/warm/stop Ollama. That is useful today, but it should not accrete llama.cpp, vLLM, Unsloth, DwarfStar, MLX and future hardware dispatch as more bespoke branches.

**Disposition: `WRAP_UPSTREAM` / `HYBRID`; eventual deletion of engine-specific lifecycle code when superseded.**

---

# 4. Target architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND / CLIENTS                        │
│ React UI | future desktop shell | CLI | automation | ACP client │
└───────────────────────────────┬──────────────────────────────────┘
                                │ typed API / capability-scoped IPC
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                  JARVIS AUTHORITY / EVENT KERNEL                 │
│ identity | policy | grants | approvals | budgets | commit rules │
│ idempotency | canonical event envelope | evidence | audit       │
└───────┬──────────────┬──────────────┬───────────────┬────────────┘
        │              │              │               │
        ▼              ▼              ▼               ▼
 AgentRuntime     ToolGateway     Egress/Privacy   Commit Gateway
 adapters         + MCP           + credentials    + canonical DB
        │              │              │               │
        └───────┬──────┴──────┬───────┘               │
                ▼             ▼                       │
          Execution       Model Runtime               │
          Sandbox         / Provider                  │
                │             │                       │
      ┌─────────┴──────┐      │                       │
      ▼                ▼      ▼                       │
 code intelligence  tools  local/cloud models         │
 Serena/LSP/tree   MCP/...  LocalAI/llama/vLLM/...     │
      │                │      │                       │
      └────────── evidence / proposals ───────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    CANONICAL DOMAIN STATE                        │
│ workspace | parameters | decisions | BLUECAD IR | artifacts     │
│ runs | evidence | provenance | freshness | engineering lineage  │
└───────────────────────────────┬──────────────────────────────────┘
                                │ read-only/index feeds
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                   DERIVED MEMORY / INDEX                         │
│ temporal graph | embeddings | summaries | code index | caches   │
│                 NEVER canonical authority                        │
└──────────────────────────────────────────────────────────────────┘
```

---

# 5. Core cross-boundary contracts

Before selecting individual upstream implementations, freeze a small Jarvis-owned contract layer. These are conceptual names; exact schemas require later spec work.

## 5.1 `ActionProposal`

Minimum fields:

`proposal_id, actor_id, runtime_id, goal_id, capability_id, action_kind, canonical_payload, payload_digest, resource_claims, side_effect_class, evidence_refs, created_at, expires_at`

An agent proposes. It does not mutate canonical state directly.

## 5.2 `CapabilityDescriptor`

`capability_id, namespace, version, input_schema, output_schema, side_effect_class, resources_read, resources_write, network_posture, required_grants, provenance, qualification_refs`

Visibility and authority are separate fields/concepts.

## 5.3 `CapabilityGrant`

`grant_id, actor_id, capability_id/version, scope, payload_constraint/digest, resource_constraint, issued_by, issued_at, expires_at, use_limit, consumed_at`

Lower layers may reduce a grant; they may never restore authority denied above them.

## 5.4 `RuntimeManifest`

`runtime_id, runtime_kind, version/commit, protocol, provider/model bindings, supported_features, workspace/sandbox binding, checkpoint semantics, platform, qualification_refs`

The manifest must distinguish advertised capability from qualified capability.

## 5.5 `ExecutionManifest`

`run_id, exact_input_digest, exact_base/version, runtime_manifest_digest, tool versions, sandbox policy digest, resource limits, network policy, model artifact, hardware, started_at, terminal_outcome`

This is where DwarfStar-style qualification and BLUECAD run provenance meet.

## 5.6 `EgressEnvelope`

`egress_id, source_refs, sensitivity_manifest, transform_manifest, reversible_map_ref, destination/provider, network_authority, credential_ref, payload_digest, approval_ref, dispatch_receipt`

Raw secret/PII content must not be present in the provider adapter when policy forbids it.

## 5.7 `CommitIntent` / `CommitReceipt`

`CommitIntent` binds the proposed canonical mutation to exact source versions/digests. The deterministic commit gateway validates freshness, authority and invariants, appends the event, updates projections atomically and returns a receipt.

This generalizes the good pattern already present in Parameter replacement and AI flow-grade event handling.

## 5.8 `EvidenceRef`

Every result that may influence engineering state must be referable by stable identity and digest, not merely embedded prose.

## 5.9 `BackendQualification`

`backend, version, platform, hardware, artifact/model, capability, test_suite_version, evidence_digest, result, tested_at`

A backend may advertise a capability only for qualified tuples, or the UI/runtime must mark it experimental/unqualified.

---

# 6. Twelve-slot disposition matrix

| Slot | Current Jarvis state | Primary disposition | Upstream role | What Jarvis must own |
| --- | --- | --- | --- | --- |
| 1 Authority/Event Kernel | strong domain transactions, egress authority, local audit events; no single generalized commit kernel | **HYBRID / KEEP core** | ESAA/event-sourcing patterns; Governance Toolkit as policy reference/component | canonical mutation authority, actor/grant identity, idempotency, event envelope, projections, evidence |
| 2 AgentRuntime | generic `agents` module is skeletal; AI execution is bespoke elsewhere | **REPLACE_WITH_UPSTREAM + WRAP** | Codex, Kimi, AgentScope, MAF, Pi, OpenCode, Goose, Pydantic/Hermes as runtime adapters | dispatch policy, runtime selection, grants, canonical commit boundary |
| 3 Tool/Capability Gateway | generic `tools` registry is skeletal | **REPLACE_WITH_UPSTREAM + HYBRID** | official MCP SDK/protocol, Hermes progressive disclosure, collision-safe namespacing patterns | canonical capability identity, policy/grant checks, resource reservations, audit |
| 4 Execution/Sandbox | strong preflight/limits, host subprocess final execution | **HYBRID** | OpenShell first serious candidate; container/NanoClaw patterns; WASI for suitable plugins | admission policy, exact manifests, trusted-vs-untrusted classification, result verification |
| 5 Model Runtime/Provider | substantial Jarvis routing/budget/egress; Ollama-specific lifecycle | **HYBRID** | LocalAI/llama.cpp/vLLM/Ollama/DwarfStar/Unsloth behind adapters | model policy, cost/privacy routing, qualification record, provider-independent request contract |
| 6 Code Intelligence | no dedicated semantic layer | **WRAP_UPSTREAM** | Serena/LSP + Tree-sitter | scope/authority, repository identity, provenance; never let code index become source of truth |
| 7 Canonical Memory/Evidence | strong proposal/promotion/replacement/freshness semantics | **KEEP_JARVIS** | external systems may read/index only | accepted engineering truth, provenance, lifecycle, freshness/invalidation |
| 8 Derived Memory/Index | limited compared with specialist systems | **WRAP_UPSTREAM / HYBRID** | Graphiti, Mem0, Cognee, Letta or simpler local backend through one interface | source refs, sensitivity/retention policy, promotion gateway, delete/forget authority |
| 9 Egress/Privacy | one of Jarvis's strongest subsystems | **KEEP_JARVIS + HYBRID** | Rizzo-pii detector/transform patterns; NanoClaw credential/egress isolation | sensitivity classification, transformation authorization, dispatch authority, restore binding |
| 10 Observability/Evaluation | substantial bespoke evidence/evals, fragmented telemetry | **HYBRID** | OpenTelemetry GenAI, conformance suites, Harbor/ToolSandbox patterns | run identity, domain verifier truth, acceptance gates, retention/redaction |
| 11 Training/Specialization | research/eval scaffolding, no need for immediate production trainer ownership | **PARK** | Unsloth, SERA, DataTrove/Axolotl/TRL/PEFT, Agent Lightning patterns | task definitions, authoritative evaluators, promotion criteria, artifact provenance |
| 12 Desktop/Frontend IPC | React calls localhost REST directly; product UI evolving | **HYBRID, defer until after visual identity** | Tauri capability ACL / ACP-like client-server ideas if desktop shell is adopted | product API semantics, user approvals, canonical state; native host capabilities must be ACL-scoped |

---

# 7. Slot-by-slot strategic design

## 7.1 Authority/Event Kernel — preserve Jarvis authority, generalize commit mechanics

### Keep

- current egress authority semantics;
- memory proposal/accept/reject/supersede lifecycle;
- freshness invalidation;
- idempotent AI flow-grade event pattern;
- domain-specific BLUECAD/runner evidence and validation;
- SQLite transactional boundaries where they are already correct.

### Change

`modules/events/service.py` is currently primarily an append-only audit logger with redaction. Do not pretend this alone is event sourcing. Introduce a generalized **canonical mutation gateway** only when the future puzzle queue is authorized.

Target flow:

`proposal -> validate identity/grant/freshness -> begin transaction -> append canonical event -> update materialized domain rows -> write evidence/audit -> commit -> receipt`

Do not rewrite every existing table into event sourcing on day one. Existing tables remain projections/source stores; migrate only mutation paths where event identity/idempotency/replay materially improves correctness.

### Disposition

**`HYBRID`: KEEP current authoritative semantics; add a common event/commit envelope.**

## 7.2 AgentRuntime — stop building a generic agent framework internally

### Current problem

The small `modules/agents` abstraction is not the runtime actually carrying the mature Jarvis AI behavior. Extending it would duplicate years of work already present upstream.

### Target

Define one `AgentRuntimeAdapter` contract around externally maintained runtimes. Required normalized operations should include:

- create/attach session;
- submit turn/task;
- stream typed events;
- interrupt/cancel;
- resume/checkpoint where supported;
- expose tool/capability requests;
- return artifacts/evidence;
- health/version/capability probe;
- explicit unsupported-feature response.

Do **not** force all runtimes to fake the same feature set.

### Runtime selection

There should not be a permanent universal winner. A later bake-off may select:

- one default general runtime;
- one coding-specialist runtime;
- one local/open runtime;
- optional external runtimes reachable through ACP/other stable protocols.

Codex/Claude/Kimi/OpenCode/Goose/Pi can remain separate workers if a normalized adapter is cheaper and safer than embedding one framework for everything.

### Delete

After production cutover and compatibility tests:

- `backend/app/modules/agents/base.py`
- `backend/app/modules/agents/registry.py`

unless one is repurposed into the normalized adapter protocol with meaningful semantics. Do not preserve the old API merely for continuity if no caller needs it.

## 7.3 Tool/Capability Gateway — MCP underneath, Jarvis authority above

### Target

Use MCP for tool/context interoperability where appropriate, but MCP registration is **not** permission.

Pipeline:

`live tool sources -> normalize identity/schema/provenance -> capability catalog -> visibility filter -> grant filter -> optional progressive disclosure -> invocation -> same authority/hooks/evidence path -> result spillover`

Borrow Hermes's progressive disclosure for large catalogs:

`tool_search -> tool_describe -> tool_call`

but keep Jarvis as authority owner.

### Required details

- collision-safe namespaced IDs;
- exact server/package/version provenance;
- schema digest;
- resource read/write declarations;
- network/credential requirements;
- destructive/idempotent/transactional side-effect class;
- bounded outputs with artifact spillover;
- one-shot grants bound to canonical payload digest where appropriate;
- no hidden bypass path for tools called through bridge/proxy.

### Delete

After cutover:

- current name-only `modules/tools/base.py` / `registry.py` if no compatibility consumer remains.

## 7.4 Execution/Sandbox — two execution lanes, not one fake sandbox

Define two explicit lanes:

### Trusted bundled execution

For checked-in, reviewed, exact-digest engineering implementations:

- current runner preflight;
- clean env;
- bounded IO;
- exact input/artifact hashes;
- direct process execution may remain where risk is understood.

### Untrusted/generated execution

Must use a real OS/container sandbox boundary:

- filesystem allowlists;
- network default deny/explicit proxy;
- non-root identity;
- CPU/RAM/PID/time limits;
- explicit mounts;
- no host credential environment;
- fail-closed admission;
- teardown/adoption semantics;
- exact sandbox policy digest in run record.

**OpenShell is the leading audited direct-runtime candidate**, subject to Windows/WSL/GPU/local-provider prototype. NanoClaw is a strong reference for credential-less containers, mount allowlists, forced egress and surviving-session adoption.

Never call AST/regex preflight a security boundary against hostile code.

## 7.5 Model Runtime/Provider — keep routing policy, stop owning every engine lifecycle

### Keep

Jarvis provider-neutral request/response contracts, privacy classes, pricing/budget, route classes, fallback policy and egress gate.

### Consolidate

There are overlapping provider/model registry concepts across `ai/contracts.py` and `ai/provider_registry.py`. The future puzzle should derive one canonical model/provider capability schema and adapters around it rather than keep parallel abstractions indefinitely.

### Replace engine-specific lifecycle

Generalize from `OllamaRuntimeLifecycle` to a `ModelRuntimeAdapter` or external control-plane contract.

Candidate engines/control planes:

- LocalAI for broad multi-backend control-plane behavior;
- llama.cpp for efficient local GGUF execution;
- vLLM for throughput/server workloads;
- Ollama for simple local deployment;
- DwarfStar for exact qualified specialist tuples;
- Unsloth for selected serving/training paths.

Do not pick by feature count. Build a qualification matrix on the user's real target platforms/hardware.

## 7.6 Code Intelligence — add, do not rebuild

Use Serena/LSP as the first candidate semantic code-intelligence sidecar, with Tree-sitter below/alongside it for syntax-level parsing where useful.

It should provide:

- symbol lookup/references;
- semantic retrieval;
- structured edit/refactor support;
- repository/project context;
- optional project/global technical memory only as derived developer state.

Jarvis retains repository/workspace authority and file-write grants.

Adopt **compare-and-set edit semantics** inspired by antirez: every edit must bind to exact base content/version/hash; stale base means reject/re-read, never blindly apply line coordinates.

## 7.7 Canonical Memory/Evidence — protect this boundary

Canonical memory remains the Jarvis domain system.

AI-derived statements enter as proposals. Calculated parameters retain run provenance. Accepted parameter replacement must continue to invalidate downstream stale dependencies atomically.

Extend canonical classes only from concrete product requirements; do not turn every conversation memory into an engineering `Parameter/Decision/Assumption`.

## 7.8 Derived Memory/Index — pluggable, disposable, rebuildable

Define `DerivedMemoryBackend` with operations such as:

`index(canonical refs), search, temporal_query, summarize, delete_scope, rebuild, health, provenance`

Requirements:

- every result points back to canonical/evidence source refs;
- indexes/summaries are disposable projections;
- sensitivity and retention scopes are explicit;
- project/global/user memory are distinct;
- rename/delete preserve or invalidate references deterministically;
- a derived backend cannot call canonical promotion directly.

Graphiti is a strong temporal-graph reference; Mem0/Cognee/Letta remain bake-off candidates. The simplest backend that satisfies real retrieval tests should win.

## 7.9 Egress/Privacy — strengthen the incumbent rather than replace it

Add a typed transform chain before provider dispatch:

`source selection -> sensitivity -> secret detector -> PII detectors/verifiers -> local transform/pseudonymize -> policy -> confirmation if needed -> credentialed dispatch -> local restore`

Rizzo-pii current root is MIT but exact packaged dependencies/SBOM still require review. Treat its detector as an optional local adapter and its architecture as the stronger immediate value.

Reversible mappings must bind to exact session/egress identity and be cleared with authoritative state, not merely UI state.

Longer-term, real provider credentials should preferably remain outside untrusted agent processes/containers and be injected at a trusted gateway/proxy boundary where feasible.

## 7.10 Observability/Evaluation — one run identity across everything

Jarvis already has rich domain evidence, local-AI eval fixtures and flow-grade events. The problem is fragmentation.

Adopt a stable run/correlation identity that can join:

- agent turn;
- model request;
- tool call;
- sandbox execution;
- engineering run;
- egress decision;
- canonical commit;
- verifier outcome;
- cost/latency/token usage.

Use OpenTelemetry-compatible spans/events as an export/operations layer, **not** as canonical engineering evidence.

Every adapter needs conformance plus tuple qualification, not merely unit tests.

## 7.11 Training/Specialization — intentionally parked

Do not build a training platform before tasks and evaluators are stable.

Prerequisites for promoting this slot:

1. production traces exist with normalized error classes;
2. task-specific deterministic/primary-source graders exist;
3. baseline model/runtime performance is recorded;
4. data provenance/licensing is explicit;
5. holdout tests exist.

Then compare Unsloth, SERA, DataTrove/Axolotl/TRL/PEFT and related stacks. A specialist model must beat the incumbent under stable evaluators before promotion.

## 7.12 Desktop/Frontend IPC — defer architectural mutation until visual identity closes

Current frontend primarily calls localhost REST via `fetch`. That is a reasonable web application boundary, but native desktop privileges should not become ambient simply because a future shell embeds the UI.

After visual identity is complete, if Tauri/native desktop packaging is chosen, use capability-scoped IPC concepts:

- webview has no ambient native authority;
- native commands are individually capability-gated;
- workspace/file/process/network scopes are explicit;
- high-impact calls flow through the same Jarvis approval/authority system.

Do not mix the visual-identity project with this backend authority work.

---

# 8. Engineering backend rule: canonical IR inside, numerical kernels outside

The engineering audit establishes a general integration rule for BLUECAD:

```text
BLUECAD canonical engineering objects / IR
        │
        ├─ PropertyPackageAdapter -> CoolProp / ChEDL / ThermoSTEAM / IDAES / DWSIM DTL
        ├─ ProcessEngineAdapter   -> BioSTEAM / IDAES / DWSIM / Modelica / FMU
        ├─ GeometryAdapter        -> CadQuery/OCCT / PicoGK family
        ├─ MeshAdapter            -> Gmsh / Netgen / meshio
        ├─ CFDAdapter             -> OpenFOAM / SU2
        ├─ FEMAdapter             -> FEniCSx / CalculiX / Code_Aster
        ├─ OptimizationAdapter    -> Pyomo / CasADi / OpenMDAO
        └─ ResultsAdapter         -> VTK / PyVista / ParaView-compatible field data
```

Jarvis/BLUECAD owns:

- semantic object identity;
- units and parameter source identity;
- immutable run input manifest;
- backend/version/license provenance;
- result artifact hashes;
- verification/invalidation;
- scene binding and operator semantics.

The external engine owns numerical implementation. This prevents BLUECAD from becoming a weak reimplementation of mature solvers while preserving a coherent user-facing engineering system.

---

# 9. Deletion and consolidation register

Deletion is a successful outcome when an upstream or a clearer boundary wins.

| Current component | Planned treatment | Delete condition |
| --- | --- | --- |
| `modules/agents/base.py`, `registry.py` | replace with normalized runtime adapter contract | all callers migrated; runtime conformance tests pass |
| `modules/tools/base.py`, `registry.py` | replace with namespaced capability/MCP gateway | all tools flow through new gateway with same-or-stronger authority |
| duplicate provider/model registry concepts | consolidate | one canonical registry schema covers routing, capability, pricing and runtime bindings |
| Ollama-specific lifecycle orchestration | reduce to adapter or remove | generalized model-runtime/control-plane path passes Windows/local qualification |
| host execution for generated/untrusted scripts | disable | sandbox lane proves required BLUECAD/coding workloads and failure semantics |
| ad-hoc derived memory caches that duplicate chosen backend | delete/rebuild | canonical source refs preserved and retrieval acceptance passes |
| bespoke interop glue duplicated by MCP/ACP/stable upstream protocols | delete | protocol adapter passes identity/authority/conformance gates |

Do **not** delete incumbent code before the replacement proves equivalent or stronger behavior and rollback exists.

---

# 10. Migration method: strangler, not flag-day rewrite

Every future puzzle slice should follow the same pattern:

1. **Freeze the incumbent contract** from exact master.
2. **Measure baseline** behavior, latency, correctness, failure semantics and resource use.
3. Introduce a **new adapter behind the same Jarvis-owned boundary**.
4. Run both paths in read-only/shadow mode where possible.
5. Compare deterministic outputs/postconditions and operational evidence.
6. Canary the replacement on bounded scopes.
7. Promote one route/capability at a time.
8. Keep rollback to incumbent until sufficient runtime evidence exists.
9. Delete duplicate code only after cutover.

No subsystem replacement should be justified by repository popularity, benchmark marketing or architecture aesthetics alone.

---

# 11. Qualification gates required before any upstream can win

For each candidate record:

- exact repository + version/commit;
- direct and material transitive licenses;
- maintenance/archive status;
- install/update strategy;
- supported OS/hardware tuple;
- startup/health/readiness behavior;
- offline/local behavior;
- failure and timeout semantics;
- credential exposure;
- network behavior;
- persistence/checkpoint semantics;
- concurrency/resource behavior;
- data deletion/retention behavior;
- deterministic conformance suite;
- rollback/uninstall path;
- SBOM/provenance entry.

A capability is not production-supported merely because the upstream documents it.

---

# 12. Future backend puzzle dependency graph — planning aid only

This is **not the live queue**. It is a dependency graph for the later queue derivation after current queue + visual identity complete.

```text
PZ-00  Exact-master revalidation + architecture ADR
  │
  ├── PZ-01 Canonical contract kit
  │      ActionProposal / Capability / Grant / RuntimeManifest /
  │      ExecutionManifest / CommitIntent+Receipt / EvidenceRef
  │
  ├── PZ-02 Unified run identity + conformance harness
  │
  ├── PZ-03 AgentRuntime adapter spine
  │       └── runtime bake-off / first production adapter
  │
  ├── PZ-04 Capability/Tool Gateway + MCP
  │       └── progressive disclosure / resource claims / grants
  │
  ├── PZ-05 Sandbox lane
  │       └── OpenShell/alternative prototype -> bounded production lane
  │
  ├── PZ-06 ModelRuntime adapter/control plane
  │       └── local backend qualification matrix
  │
  ├── PZ-07 Egress privacy transform plugins
  │       └── Rizzo-pii adapter / reversible mapping lifecycle
  │
  ├── PZ-08 Canonical Commit/Event gateway generalization
  │       └── migrate selected high-value mutation paths only
  │
  ├── PZ-09 Derived Memory backend
  │
  ├── PZ-10 Code Intelligence sidecar
  │
  ├── PZ-11 Desktop/native capability IPC, only if product shell requires it
  │
  └── PZ-12 Training/specialization, only after evaluators/traces are mature
```

Not all slices must be sequential. After `PZ-01/PZ-02`, AgentRuntime, sandbox, model runtime, derived memory and code intelligence can be prototyped largely in parallel, but production promotion must respect authority/dependency edges.

Engineering backend adapters should be separate capability families on top of the same contract kit rather than being interleaved into generic runtime infrastructure.

---

# 13. Minimum acceptance criteria for the completed backend puzzle

The puzzle should be considered architecturally complete only when:

1. no model/agent can mutate canonical engineering state except through the deterministic commit boundary;
2. capability visibility and invocation authority are separate;
3. egress authority is independent of read/tool authority;
4. untrusted/generated code cannot execute on the host merely because it passed AST/regex checks;
5. agent runtimes are replaceable without changing canonical domain models;
6. model inference backends are replaceable without changing routing/privacy policy;
7. MCP/ACP/A2A roles are not conflated;
8. canonical memory and derived retrieval/index memory are explicitly separate;
9. every result can carry stable provenance/evidence identity;
10. every production backend capability has exact tuple qualification evidence;
11. frontend/native calls cannot silently bypass backend authority;
12. all replaced home-grown stubs/duplicate layers are actually removed after cutover;
13. Windows/local/offline operation remains a first-class acceptance target where required by JarvisOS;
14. deterministic engineering verification remains stronger than model confidence.

---

# 14. Decisions with confidence level

| Decision | Confidence | What could change it |
| --- | --- | --- |
| Preserve Jarvis canonical engineering/memory authority | **HIGH** | only evidence that an upstream can preserve exact domain semantics, provenance and promotion better without moving authority outside Jarvis |
| Preserve/extend Jarvis egress authority | **HIGH** | no audited generic agent framework currently justifies replacing it |
| Delete current generic agents/tools stubs after replacement | **HIGH** | an unexpected production caller requiring the exact old interface |
| Use replaceable AgentRuntime adapters rather than one embedded mega-framework | **HIGH** | only if one upstream proves uniquely necessary and its lock-in is lower than adapter cost |
| Add real sandbox under current runner guardrails | **HIGH** | no credible argument makes host subprocess + AST checks an OS isolation boundary |
| OpenShell as first sandbox prototype | **MEDIUM-HIGH** | Windows/WSL/GPU/network integration may fail or impose unacceptable overhead |
| Keep Jarvis provider policy but externalize inference-engine lifecycle | **HIGH** | none expected; exact engine winners remain open |
| LocalAI as a possible control-plane backend | **MEDIUM** | real Windows/hardware/latency footprint may favor direct llama.cpp/Ollama adapters |
| Serena/LSP for code intelligence | **MEDIUM-HIGH** | integration overhead or repository-scale tests may favor a narrower LSP/tree-sitter implementation |
| Graphiti/Mem0/Cognee/Letta derived-memory winner | **LOW — BAKE-OFF REQUIRED** | choose by real Jarvis retrieval/retention/provenance tests |
| Rizzo-pii as optional privacy detector | **MEDIUM-HIGH** | language/domain coverage and packaged dependency/licensing review |
| Training/specialization remains parked | **HIGH** | may advance only when stable production traces/evaluators create a concrete ROI case |

---

# 15. Anti-patterns explicitly rejected

- **No mega-agent authority:** Codex/Claude/Hermes/AgentScope/etc. must not become canonical state owners.
- **No framework-per-feature:** do not import a second agent framework just for one helper abstraction.
- **No MCP = permission assumption.**
- **No vector DB = memory authority assumption.**
- **No README capability = production support assumption.**
- **No green CI = complete qualification assumption.** Backend/platform/model tuples need dedicated matrices.
- **No LLM self-assigned least privilege.**
- **No prompt-only privacy boundary.**
- **No model confidence replacing engineering verification.**
- **No raw secrets in untrusted worker environments when a gateway/credential-ref design can avoid it.**
- **No flag-day backend rewrite.**
- **No preserving dead abstractions for aesthetic continuity.**
- **No backend puzzle implementation before the current queue and visual-identity phase are complete.**

---

# 16. Evidence map

Canonical intake index:

- `docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`

Core runtime/software audits:

- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_2_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_3_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_4_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_5_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_6_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_7_2026-08-20.md`

Research/safety:

- `docs/audits/AGENT_ARCHITECTURE_RESEARCH_AUDIT_2026-08-20.md`
- `docs/audits/AGENT_ARCHITECTURE_RESEARCH_AUDIT_CONTINUATION_2026-08-20.md`

Engineering ecosystem:

- `docs/audits/ENGINEERING_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-19.md`
- `docs/audits/ENGINEERING_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_2026-08-19.md`
- `docs/audits/ENGINEERING_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_2_2026-08-19.md`

Nous/upstream provenance:

- `docs/audits/NOUS_RESEARCH_REPO_AUDIT_2026-08-19.md`
- `docs/audits/NOUS_FORK_UPSTREAM_EXPANSION_2026-08-19.md`
- `docs/audits/UPSTREAM_AUTHOR_ECOSYSTEM_AUDIT_2026-08-19.md`
- continuation files in the same family.

Current incumbent code inspected for this strategy includes at minimum:

- `backend/app/modules/agents/*`
- `backend/app/modules/tools/*`
- `backend/app/modules/ai/contracts.py`
- `backend/app/modules/ai/provider_registry.py`
- `backend/app/modules/ai/egress_*`
- `backend/app/modules/ai/sensitivity.py`
- `backend/app/modules/ai/flow_grade_event_store.py`
- `backend/app/modules/memory/*`
- `backend/app/modules/events/service.py`
- `backend/app/modules/local_ai/runtime/*`
- `backend/app/modules/runner/safety.py`
- `backend/app/modules/runner/local_python.py`
- `backend/app/modules/bluecad/*`
- `backend/app/modules/process_kernel/*`
- `frontend/src/api/client.ts`

---

# 17. Revalidation rule before future implementation

This document intentionally precedes the backend puzzle implementation by a potentially long interval. Therefore none of its upstream selections may be treated as fresh implementation evidence later.

When the current functional queue and visual identity are complete:

1. record exact new master SHA;
2. diff the relevant incumbent subsystems against this baseline;
3. re-check upstream versions, maintenance, licenses and current capabilities;
4. re-run the minimum bake-offs/prototypes;
5. update this strategy if material facts changed;
6. create the authoritative architecture ADR/spec set;
7. only then derive `docs/specs/STATUS.md` puzzle slices through the normal definition/readiness/implementation lifecycle.

Until that promotion occurs, this file is a strategic map only.