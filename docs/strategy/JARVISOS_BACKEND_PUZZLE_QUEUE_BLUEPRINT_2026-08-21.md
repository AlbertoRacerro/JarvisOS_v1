# JarvisOS Backend Puzzle — Future Queue Blueprint

Status: **PLANNING BLUEPRINT ONLY — NOT `STATUS.md`, NOT IMPLEMENTATION AUTHORITY**  
Prepared: 2026-08-21  
Depends on: `JARVISOS_BACKEND_PUZZLE_STRATEGY_2026-08-21.md`  
Planning labels below (`PZ-*`, `ENG-*`) are temporary handles, **not canonical spec IDs**.

## 0. Activation gate

This blueprint must remain dormant until all three conditions are true:

1. the currently active functional product queue is complete and reconciled;
2. the frontend visual-identity phase is complete and its stable product/API seams are known;
3. a fresh exact-master revalidation confirms or amends the backend-puzzle strategy and current upstream candidates.

Only after those conditions may the maintainer promote work into `docs/specs/STATUS.md` through the normal definition -> readiness -> implementation -> reconciliation lifecycle.

Nothing in this file authorizes starting backend-puzzle runtime work while PR #319 / 058c or later current-queue slices are active.

---

# 1. Queue design rules

The future queue should be **contract-first and capability-first**, not repository-first.

Bad queue shape:

`integrate Serena -> integrate AgentScope -> integrate LocalAI -> integrate NanoClaw`

Preferred shape:

`freeze Jarvis contract -> prove adapter boundary -> bake off candidates -> migrate one capability -> verify -> remove duplicate code`

Each promoted slice must answer:

- What exact incumbent behavior is being replaced, wrapped or retained?
- Who owns canonical state before and after the slice?
- What is the typed input/output contract?
- Which authority is required: capability, egress, state commit, or a combination?
- What can fail, retry, resume or roll back?
- What deterministic acceptance test proves the slice useful?
- What old code becomes deletable after cutover?
- What exact upstream/version/license is involved?

No queue item should exist solely because an upstream library is interesting.

---

# 2. Lifecycle required for every promoted puzzle slice

When these planning handles are eventually converted to canonical spec IDs, each substantial slice should normally pass through:

1. **Definition** — exact product boundary, non-goals, owner and acceptance criteria.
2. **Readiness** — inspect fresh runtime/upstream; freeze exact contracts, versions, licenses and test plan.
3. **Implementation** — one bounded implementation front.
4. **Independent evidence** — deterministic CI plus subsystem-specific conformance/qualification; adversarial diff review where useful.
5. **Reconciliation** — update `STATUS.md`, delete/retire superseded code only when cutover is proven.

For risky replacements, add explicit shadow/canary phases before cutover.

---

# 3. Macro dependency graph

```text
CURRENT FUNCTIONAL QUEUE
        |
        v
FRONTEND VISUAL IDENTITY
        |
        v
PZ-00  Exact-master / upstream revalidation + governing architecture ADR
        |
        +--------------------+
        |                    |
        v                    v
PZ-01 Contract Kit       PZ-02 Run Identity + Conformance Spine
        |                    |
        +----------+---------+
                   |
       +-----------+-----------+-----------+-----------+
       |                       |           |           |
       v                       v           v           v
PZ-03 AgentRuntime         PZ-06 Model   PZ-09       PZ-10
read-only adapter          Runtime       Derived     Code
spine                      control       Memory      Intelligence
       |                       |           |           |
       +-----------+-----------+-----------+-----------+
                   |
                   v
             PZ-04 Capability / Tool Gateway
                   |
       +-----------+-------------------+
       |                               |
       v                               v
PZ-05 Sandbox Lane                  PZ-07 Egress Privacy Plugins
       |                               |
       +---------------+---------------+
                       |
                       v
              PZ-08 Canonical Commit/Event Gateway
                       |
                       v
             PZ-13 State-changing Agent/Tool Cutover
                       |
                       v
             PZ-14 Legacy Deletion / Consolidation
                       |
          +------------+-------------+
          |                          |
          v                          v
      ENG-* adapters             PZ-11 Native IPC
                                  only if required
          |
          v
      PZ-12 Training/Specialization
      only after traces/evaluators mature
```

Some branches can run in parallel after PZ-01/PZ-02, but only one canonical product implementation front should be active where current repository policy requires that. “Parallel” here means dependency independence for future planning, not permission to violate the repo's live single-front discipline.

---

# 4. Foundation wave

## PZ-00 — Revalidate strategy and issue governing architecture ADR

### Purpose

Prevent this 2026-08-21 research snapshot from becoming stale authority.

### Must inspect fresh

- exact master and all relevant current subsystems;
- the final state of the current queue and visual-identity changes;
- current versions/licenses/maintenance of runtime, MCP, sandbox, memory and local-model candidates;
- Windows/local/offline deployment assumptions;
- current hardware targets;
- any new security research materially changing authority design.

### Output

One governing ADR/spec family that freezes:

- small authoritative Jarvis kernel;
- three-authority separation;
- canonical vs derived state;
- adapter ownership;
- migration discipline;
- final set of puzzle slices to promote.

### Exit criterion

No implementation begins until strategy and exact runtime agree.

---

## PZ-01 — Canonical cross-boundary contract kit

### Goal

Create the minimum Jarvis-owned contracts that prevent upstream adapters from defining system authority.

Candidate contracts:

- `ActorIdentity`
- `ActionProposal`
- `CapabilityDescriptor`
- `CapabilityGrant`
- `ResourceClaim`
- `RuntimeManifest`
- `ExecutionManifest`
- `EgressEnvelope`
- `CommitIntent`
- `CommitReceipt`
- `EvidenceRef`
- `BackendQualification`

### Constraints

- schemas must be versioned;
- canonical serialization/digest rules explicit;
- no runtime-framework-specific fields in the core contract unless unavoidable;
- lower layers may narrow authority, never broaden it;
- visibility does not imply invocation permission;
- payload-bound grants available for high-impact actions;
- all external IDs/provenance normalize to stable Jarvis identities.

### Test focus

- canonical round trips/digests;
- schema migration/unknown version fail-closed behavior;
- malformed payloads;
- grant expiry/use limits;
- resource conflict semantics;
- no privilege restoration by child/subagent.

### Blocks

PZ-03/04/05/06/08 production adoption.

---

## PZ-02 — Unified run identity, telemetry and conformance spine

### Goal

Give every later bake-off one comparable evidence language.

A correlation/run identity should join:

- user/automation trigger;
- agent session/turn;
- model call;
- tool call;
- sandbox execution;
- engineering run;
- egress decision;
- canonical commit;
- verifier result;
- latency/cost/token/resource use.

### Deliverables

- normalized event/run envelope;
- OpenTelemetry-compatible operational export, without making OTel canonical engineering truth;
- adapter conformance harness;
- DwarfStar-style `backend + version + platform + hardware + artifact/model + capability -> qualification evidence` records;
- historical regression fixtures for known failures.

### Exit criterion

A candidate adapter cannot advertise a production capability without machine-readable qualification evidence or an explicit experimental/unqualified label.

---

# 5. Replaceable read-mostly subsystem wave

These slices can be researched/prototyped after PZ-01/PZ-02 because they can initially remain read-only or proposal-only.

## PZ-03 — AgentRuntime adapter spine and runtime bake-off

### Phase A: read-only runtime contract

Normalized operations:

- probe/version/capabilities;
- create/attach session;
- submit task/turn;
- stream typed events;
- interrupt/cancel;
- checkpoint/resume where genuinely supported;
- return artifacts/evidence;
- unsupported-feature response.

No state-changing tools in the first production slice.

### Candidate bake-off

At revalidation time compare current candidates such as:

- Codex/app-server;
- Kimi Code;
- AgentScope;
- Microsoft Agent Framework;
- Pydantic AI;
- Hermes;
- Pi;
- OpenCode;
- Goose;
- other materially stronger newly discovered runtimes.

Claude Code/Agent SDK may remain an external runtime even where source/license boundaries make direct embedding undesirable.

### Metrics

- session/resume correctness;
- event contract stability;
- Windows/local support;
- tool request transparency;
- checkpoint behavior;
- context control;
- provider neutrality;
- dependency/upgrade footprint;
- latency and failure recovery;
- ability to remain below Jarvis authority.

### Cutover target

Replace current generic `modules/agents` skeleton rather than extending it by sunk cost.

---

## PZ-06 — ModelRuntime adapter/control plane

### Keep above this boundary

Jarvis:

- provider/model routing policy;
- privacy/egress authority;
- cost/token budgets;
- capability requirements;
- fallback permission;
- model qualification metadata.

### Put below this boundary

Replaceable inference engines/control planes such as:

- LocalAI;
- llama.cpp;
- vLLM;
- Ollama;
- DwarfStar;
- Unsloth serving paths;
- future hardware-specific runtimes.

### First migration target

Generalize away from hard-coded `OllamaRuntimeLifecycle` ownership without breaking current local routes.

### Qualification matrix

Minimum tuples should include:

`engine/version + model artifact + quantization + OS + GPU/CPU + context + tool-call mode + checkpoint/cache mode`.

### Cutover/delete gate

Remove engine-specific Jarvis lifecycle code only after the generalized path passes the existing local route tests plus hardware qualification on target machines.

---

## PZ-09 — Derived Memory/Index backend

### Goal

Add stronger retrieval/temporal/index behavior without moving canonical truth out of Jarvis.

### Candidate interface

- index canonical/evidence refs;
- search;
- temporal query where supported;
- summarize/compact;
- delete/forget scope;
- rebuild;
- health/version;
- provenance lookup.

### Candidate bake-off

Graphiti, Mem0, Cognee, Letta or a simpler local implementation may compete.

### Hard invariants

- every derived result links to source refs;
- indexes/summaries are disposable projections;
- sensitivity/retention scopes explicit;
- project/global/user memory distinct;
- no direct canonical promotion path;
- delete/forget semantics tested;
- stale source invalidation/rebuild behavior deterministic.

### Acceptance benchmark

Use realistic Jarvis engineering/coding sessions and measure exact useful retrieval, provenance retention, delete behavior, latency, local/offline operation and context savings — not generic RAG benchmarks alone.

---

## PZ-10 — Code Intelligence sidecar

### First candidate

Serena/LSP + Tree-sitter where complementary.

### Initial scope

- symbol lookup;
- references;
- semantic repository retrieval;
- structured read-only analysis;
- project indexing/status.

### Later write support

Only after ToolGateway/grants exist. All edits must use compare-and-set semantics bound to exact base content/hash/version. A stale file causes re-read/replan, never blind line-based mutation.

### Boundary

Code index/memory is derived developer state. Git/files remain source truth; Jarvis/Git authority controls writes.

---

# 6. Authority-bearing execution wave

## PZ-04 — Capability/Tool Gateway + MCP

### Goal

Replace the current name-only tool skeleton with one live capability gateway.

### Required pipeline

`tool sources -> normalize identity/schema/provenance -> catalog -> visibility policy -> grant check -> resource reservation -> invocation -> hooks/evidence -> bounded result/spillover`

### MCP role

MCP may provide tool/context transport and discovery. It does **not** define Jarvis authorization.

### Required features

- namespaced collision-safe capability IDs;
- exact server/package/version provenance;
- schema digest;
- resource read/write claims;
- network/credential requirements;
- side-effect/idempotency/transaction class;
- cancellation/timeout;
- large-result spillover;
- same guardrail path for direct and bridge/progressive calls;
- progressive disclosure for large catalogs where useful.

### First production lane

Read-only capabilities only.

### State-changing lane

Blocked on PZ-05 and PZ-08.

---

## PZ-05 — Real sandbox execution lane

### Preserve

Current Jarvis runner safety:

- exact path containment;
- input/output/hash contracts;
- AST/import restrictions;
- clean environment;
- time/output/artifact bounds.

### Add

OS/container boundary for untrusted/generated code:

- explicit mounts;
- non-root identity;
- filesystem policy;
- network default deny / controlled proxy;
- no host secrets;
- CPU/RAM/PID/time limits;
- fail-closed admission;
- lifecycle/reaping/adoption;
- sandbox policy digest in execution manifest.

### First candidate prototype

OpenShell, with NanoClaw/container/WASI patterns as comparison/reference.

### Required prototype matrix

- Windows native/WSL deployment;
- repository coding workload;
- BLUECAD/engineering Python workload;
- local model endpoint access;
- GPU requirements where relevant;
- file/artifact transfer;
- cancellation/timeout/kill;
- startup overhead;
- network isolation verification;
- credential leakage probes.

### Cutover

Generated/untrusted code loses host-subprocess execution only after this lane proves all required workloads and rollback exists.

---

## PZ-07 — Privacy transform and credential-isolation plugins

### Keep

Existing Jarvis egress authority remains canonical.

### Add transform stage

`source refs -> sensitivity -> secret/PII detectors -> deterministic validators -> redact/pseudonymize -> policy -> confirmation -> dispatch -> local restore`

### Candidate

Rizzo-pii as optional detector/local worker; architecture usable even if detector coverage is insufficient for every domain.

### Security additions

Evaluate NanoClaw/agent-vault-style design in which untrusted workers receive credential references or proxy access rather than real provider secrets.

### Required tests

- partial-span PII leakage;
- stale reversible-map reuse;
- cross-session map isolation;
- restore bound to exact transform manifest;
- local reset/delete semantics;
- false-negative secret patterns;
- proxy bypass/raw socket attempts where forced egress is enabled;
- fail-closed gateway unavailable behavior.

---

## PZ-08 — Canonical Commit/Event Gateway

### Goal

Generalize the good authority patterns already present in accepted Parameter replacement and flow-grade events.

### Target flow

`proposal -> identity/grant/freshness/invariant validation -> begin transaction -> append canonical event -> update projections/domain state -> write evidence -> commit -> receipt`

### Important non-goal

Do **not** rewrite the entire database into pure event sourcing.

### Initial migration candidates

Choose mutation paths where payload binding, replay/idempotency or stale-write safety matter most, for example:

- agent-originated memory promotion;
- capability-granted state changes;
- high-impact engineering configuration mutations;
- approvals with one-shot payload binding.

### Acceptance

- exact idempotent replay;
- stale source/version rejection;
- atomic event + projection behavior;
- payload digest mismatch rejection;
- grant consumed atomically where one-shot;
- deterministic verifier/postcondition outcome;
- crash/retry behavior proven.

---

# 7. Cutover and deletion wave

## PZ-13 — State-changing agent/tool cutover

This is the first stage where generic external runtimes may request real state-changing capabilities.

Prerequisites:

- PZ-01 contracts;
- PZ-02 conformance/run identity;
- PZ-03 runtime adapter;
- PZ-04 ToolGateway;
- PZ-05 sandbox for relevant execution;
- PZ-07 egress boundary where network access is involved;
- PZ-08 commit gateway for canonical mutations.

Use increasing authority levels:

1. read-only;
2. proposal-only;
3. reversible/low-risk mutation with explicit grant;
4. broader state change only after verifier/rollback evidence.

No “manager agent” receives ambient authority.

---

## PZ-14 — Legacy deletion and consolidation

Delete only after production cutover evidence.

Candidates:

- `modules/agents/base.py`, `modules/agents/registry.py`;
- `modules/tools/base.py`, `modules/tools/registry.py`;
- duplicate provider/model registry representations;
- superseded Ollama-specific lifecycle branches;
- host execution lane for generated/untrusted scripts;
- duplicate derived-memory caches/indexes;
- bespoke protocol glue replaced by stable MCP/ACP adapters.

### Deletion gate

For every removal record:

- old callgraph/callers = zero or migrated;
- replacement conformance PASS;
- rollback window completed;
- docs/tests no longer depend on old path;
- dependency/SBOM cleanup performed;
- no stale feature flag silently keeps both implementations alive.

The goal is a smaller system after the puzzle, not a larger system containing every old and new implementation.

---

# 8. Engineering backend adapter family

These are separate domain capability families built on top of the generic contract/tool/sandbox/run-evidence spine. Do not couple them to one AgentRuntime.

Planning handles below are illustrative.

## ENG-01 — Property/Thermodynamics adapter contract

Candidates: CoolProp, ChEDL thermo/chemicals/fluids/ht, ThermoSTEAM, IDAES property packages, DWSIM Thermodynamics where license boundary permits.

Jarvis/BLUECAD owns units, compound identity, source/provenance and acceptance; backend owns calculations.

## ENG-02 — Process engine adapter contract

Candidates: BioSTEAM, IDAES/Pyomo, DWSIM external engine, Modelica/OpenModelica/FMU paths.

Freeze stream/unit/flowsheet translation boundaries and round-trip/provenance tests before selecting default engines.

## ENG-03 — Geometry and mesh adapters

Candidates: CadQuery/OCCT, PicoGK/LEAP71 family, Gmsh, Netgen, meshio.

Keep semantic engineering objects inside BLUECAD; geometry/mesh artifacts carry stable source bindings and hashes.

## ENG-04 — CFD/FEM solver adapters

Candidates: OpenFOAM, SU2, FEniCSx, CalculiX, Code_Aster and future qualified engines.

External solver success is not acceptance: ingest artifacts, validate schema/mesh/field identity and run independent physical/numerical verification where possible.

## ENG-05 — Coupling/optimization adapters

Candidates: OpenMDAO, CasADi, Pyomo, SUNDIALS, PETSc.

Keep optimization problem identity, objective/constraint provenance and solver configuration in canonical manifests.

## ENG-06 — Scientific results/visualization contract

Use VTK/PyVista/ParaView-compatible field data and meshio-style interchange so scientific data remains the artifact and frontend scene state remains a view.

### Engineering promotion order

Do not promote all ENG-* families at once. Select them from real product demand after the generic substrate is stable; each requires a separate definition/readiness/implementation path and license/performance matrix.

---

# 9. Optional native/desktop branch

## PZ-11 — Desktop/native capability IPC

Only promote if the post-visual-identity product deliberately chooses a native shell or needs privileged desktop actions.

Candidate pattern: Tauri-style capability ACL or equivalent.

Requirements:

- no ambient webview authority;
- individual native commands capability-scoped;
- file/process/network/workspace scopes explicit;
- same Jarvis grant/approval system for high-impact calls;
- no frontend-owned canonical policy;
- browser/web deployment remains possible unless product decision explicitly removes it.

Do not start this slice merely because native packaging is fashionable.

---

# 10. Training/specialization tail

## PZ-12 — Specialist training and self-improvement pipeline

This remains last/conditional.

Activation prerequisites:

- production traces with normalized failures exist;
- authoritative task evaluators exist;
- baseline model/runtime scores exist;
- data provenance/licenses are clean;
- holdout and regression suites exist;
- there is a measured task/latency/cost gap worth training for.

Then compare current Unsloth/SERA/DataTrove/Axolotl/TRL/PEFT/Agent-Lightning-style paths.

Promotion rule:

`candidate specialist must beat explicit incumbent under stable holdout evaluators`.

Never let live authority-bearing code/policy self-modify without the normal offline candidate -> deterministic gates -> review -> spec/PR promotion path.

---

# 11. Suggested future promotion waves

These waves are planning order only.

## Wave 0 — Revalidation

- PZ-00

## Wave 1 — Common substrate

- PZ-01
- PZ-02

## Wave 2 — Read-mostly replaceable adapters

- PZ-03 AgentRuntime read-only
- PZ-06 ModelRuntime
- PZ-09 Derived Memory
- PZ-10 Code Intelligence

These can be independently benchmarked after Wave 1, but repository live-front policy may still serialize implementation.

## Wave 3 — Authority-bearing execution

- PZ-04 ToolGateway
- PZ-05 Sandbox
- PZ-07 Privacy transforms
- PZ-08 Commit/Event gateway

## Wave 4 — Controlled autonomy and cleanup

- PZ-13 State-changing cutover
- PZ-14 deletion/consolidation

## Wave 5 — Engineering engine expansion

Promote only required ENG-* adapters based on product demand.

## Wave 6 — Optional product/platform tail

- PZ-11 native IPC if required
- PZ-12 training/specialization only if evidence justifies it

---

# 12. Queue-level stop / merge / delete rules

A future slice should be **cancelled or parked** when:

- the upstream adds no measurable value over current Jarvis;
- its license/dependency/supply-chain burden exceeds the saved complexity;
- it requires moving canonical authority outside Jarvis;
- Windows/local/offline requirements cannot be met where required;
- a simpler adapter/backend already satisfies the acceptance criteria;
- its main justification is popularity or hypothetical future scale.

A future slice should be **merged** only when:

- exact-head deterministic gates pass;
- relevant qualification/conformance matrix passes;
- current-vs-candidate evidence shows same or stronger behavior;
- migration/rollback is explicit;
- no hidden second authority path is introduced;
- the next exact action is unambiguous.

Old code should be **deleted** when:

- replacement is production-reachable;
- callgraph is migrated;
- rollback evidence window is satisfied;
- no canonical data/provenance is lost;
- old dependencies/config/docs/tests are cleaned at the same time or in an immediately governed cleanup slice.

---

# 13. Expected end-state after the puzzle

The queue should finish with **fewer bespoke generic framework components** than it started with.

Expected stable ownership:

- Jarvis: authority, grants, egress policy, canonical domain/evidence, engineering identity, commit rules, routing policy, acceptance/verifiers.
- Upstream adapters: agent loops, MCP transport/tool implementations, sandbox mechanisms, inference engines, code intelligence, derived-memory indexes, numerical solvers, telemetry transport and training stacks.
- Frontend: operator-facing view/controller over backend truth, with capability-scoped native IPC only if intentionally adopted.

The final system should be easier to replace piece-by-piece because no generic runtime, model engine, memory index or solver owns canonical Jarvis state.

---

# 14. Handoff rule when activation time arrives

When the current queue and frontend visual identity are finished, the future coordinating chat must **not** copy these PZ handles directly into `STATUS.md`.

It must first:

1. fetch fresh master and active PR state;
2. read the merged strategy and this blueprint;
3. re-audit all materially changed incumbent subsystems;
4. refresh upstream evidence/licenses;
5. mark each strategic disposition KEEP/REPLACE/WRAP/HYBRID/DELETE/PARK again;
6. collapse, split or reorder PZ handles based on actual dependencies at that time;
7. derive the first definition-only canonical slice;
8. proceed through the normal readiness and implementation lifecycle.

This prevents a 2026 planning artifact from becoming stale queue authority by inertia.