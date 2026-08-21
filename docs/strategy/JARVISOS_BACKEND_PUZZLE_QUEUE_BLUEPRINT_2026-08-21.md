# JarvisOS Backend Puzzle — ROI-Ordered Future Queue Blueprint

Status: **PLANNING BLUEPRINT ONLY — NOT `STATUS.md`, NOT IMPLEMENTATION AUTHORITY**

Prepared: 2026-08-21

Audit base: exact `master` `e21edd6a8dab99fe2daf4193a0a258fd494b1eae`

Active runtime front observed separately: PR #319, branch `impl/058c-scene-semantics-a1`, exact head `d365d5296ee5c5c5fe738f9b3bcbbcb3b9d6cd0`

Depends on: `JARVISOS_BACKEND_PUZZLE_STRATEGY_2026-08-21.md`
Planning labels below (`CS-*`, `EF-*`, `DX-*`, `GE-*`) are temporary handles, **not canonical spec IDs**.

## 0. Authority and activation boundary

`docs/specs/STATUS.md` remains the sole live status and queue authority. This file records a future dependency plan only. It must not be copied into `STATUS.md`, treated as a ready specification, or used to start runtime work.

The activation order is binding for this blueprint:

1. complete and reconcile the current functional queue;
2. complete the independently removable global visual-identity phase;
3. re-fetch exact `master`, all active PRs and relevant upstreams;
4. re-derive the smallest core-software/Hermes slices through normal definition and readiness;
5. qualify and extend the highest-ROI engineering foundations already present;
6. introduce Design Explorer at the first point where it reuses qualified incumbent execution;
7. consider advanced generative engineering only after measured demand and evaluator evidence.

PR #319 remains the sole active runtime front observed during this audit. This PR does not edit it, its branch, its runtime files or its `STATUS.md` row.

The future canonical sequence remains:

`definition -> readiness -> implementation -> independent evidence -> exact-head merge -> registry reconciliation`

Existing specs 066–068 are frozen in the audited `STATUS.md`. This blueprint may recommend their future re-derivation, but grants no authority to unfreeze or implement them.

---

# 1. Audit method and disposition vocabulary

This revision classifies current reality from code, tests, workflows, canonical specs and operator-facing call paths rather than from roadmap names alone.

The required primary dispositions are:

- **KEEP** — production-reachable ownership or behavior is already correct enough to retain.
- **HARDEN** — retain the incumbent and close reliability, safety, lifecycle or operational gaps.
- **QUALIFY** — retain or compare only after exact platform/version/license/performance evidence.
- **EXTEND** — add a bounded capability through the incumbent contract; do not rebuild the incumbent.
- **REPLACE** — migrate a weak or skeletal incumbent behind a stable boundary, then delete it.
- **BUILD** — no adequate production-reachable incumbent exists.

Multiple labels may apply in sequence, for example `KEEP -> QUALIFY -> EXTEND`. `BUILD` is not used merely because a component is externally packaged or disabled by safe default.

Audit surfaces inspected:

- canonical queue/spec authority: `docs/specs/STATUS.md`, `docs/specs/README.md`, 005/007/008/009/016/021b/024/038/043/044/047/052/056/060/066–069/070/083–092/095–099 records where present;
- architecture and candidate evidence: backend-puzzle strategy, BLUECAD design/licensing docs, core/software/engineering/Nous audits, and the canonical candidate-integration register;
- runtime: FastAPI composition, AI execution/routing/egress, BLUECAD builders/export/registry/mesh/FEM/loop/evidence, runner registration/binding/execution, memory, agents/tools skeletons and local-AI lifecycle;
- frontend: Vite API base/proxy, shared API clients, application shell, BLUECAD workbench/viewer, Runs, Engineering Data, Properties, Analytics and Jarvis sidecar;
- proof: offline adapter/conformance suites, geometry determinism canary, strict real-tool workflow and the current GitHub check state.

This is a repository audit, not a claim that every optional tool is installed on the maintainer's Windows host or that every planned engineering model is scientifically validated.

---

# 2. Verified incumbent inventory — do not duplicate

| Area | Evidence on exact audit base | Reality | Disposition | Consequence for future queue |
| --- | --- | --- | --- | --- |
| Canonical state and authority | FastAPI + SQLite services, events, data-root boundary, promotion semantics, `STATUS.md` discipline | Real incumbent | **KEEP / HARDEN** | Do not move canonical truth or queue authority into Hermes, an MCP server, a vector DB or a solver. |
| AI execution, routing, egress and economics | `run_ai_task`, `ai_jobs`, provider registry, safe-default fake mode, sensitivity/exact-packet gates, token/cost controls, DPAPI secret path | Real incumbent | **KEEP / HARDEN / EXTEND** | Hermes and future runtimes must traverse this spine; no second provider gateway. |
| Backend/frontend connection | FastAPI routers, CORS, optional built-SPA serving, Vite/API client, BLUECAD/Runs/Engineering/Jarvis screens | Real end-to-end application seam | **KEEP / HARDEN** | Visual identity is a frontend phase over stable APIs, not a backend rewrite. Add contract/browser smoke only where gaps are observed. |
| BLUECAD semantic CAD | `GeometrySpec`, deterministic builders/assembly, build123d/OCP, STEP/STL/GLB/manifest export, stable artifacts and validation | Real production path | **KEEP / HARDEN / EXTEND** | Do not rebuild a generic geometry engine. Add new primitives/backends only behind the existing semantic/artifact boundary. |
| BLUECAD operator lifecycle | candidate/attempt loop, aggregate read model, archive/promote, GLB workbench, evidence and source navigation | Real product path | **KEEP / HARDEN** | Reuse for study candidates and result inspection. Do not create a parallel design database/UI. |
| Geometry -> mesh | `mesh_adapter.py` emits deterministic Gmsh `.geo`, physical groups and CalculiX `.inp`; registry invokes hash-pinned subprocess only | Implemented and tested; shipped external tool entry is safely disabled | **KEEP / QUALIFY / HARDEN** | Operator installation/registry qualification is work; adapter implementation is not. |
| Mesh -> static FEM/CalculiX | `fem_adapter.py` builds bounded static decks, invokes registry-bound CalculiX, parses FRD/DAT and evaluates criteria | Implemented and tested; shipped external tool entry is safely disabled | **KEEP / QUALIFY / EXTEND** | Qualify target hosts and workloads. Modal/thermal or alternative solvers are later extensions, not replacements by default. |
| Full CAD -> mesh -> FEM wiring | BLUECAD loop and CAD-link topology execution call `_run_simulation_stage`, persist simulation runs, artifacts and mesh/FEM evidence | Real opt-in advisory end-to-end path | **KEEP / HARDEN / QUALIFY** | First engineering milestone is production qualification and failure UX, not `ENG-03/04 BUILD`. |
| FEM verification | C3D10, pressure/reaction and analytic verification battery plus strict real-tool workflow | Real verification foundation | **KEEP / EXTEND** | Extend fixtures only for new analysis classes or actual BlueRev decisions. Passing a solver remains insufficient without acceptance evidence. |
| Bundled deterministic runner | model registration, input contracts/binding preview, queued claim, bounded subprocess, artifacts/logs/results and process models | Real incumbent | **KEEP / HARDEN / EXTEND** | Design Explorer evaluations should reuse runner identities, bindings, artifacts and evidence. |
| Caller-supplied/generated runner | historical `bluecad_l2_v0`; normal instantiation disabled; AST/hash/limits exist but host subprocess is not OS isolation | Not an approved untrusted-code lane | **REPLACE / BUILD** | Keep trusted bundled execution. Before external agents can execute generated code, build/qualify a real sandbox and retire unsafe reachability. |
| Canonical memory/evidence | accepted/proposed records, context packs, typed evidence and provenance | Real incumbent | **KEEP / HARDEN** | External memory systems may only be disposable derived indexes. |
| Generic `modules/agents` | base/registry placeholder with no product authority path | Skeleton | **REPLACE** | Do not elaborate it. Introduce a runtime adapter only after bake-off and delete the skeleton after cutover. |
| Generic `modules/tools` | name/description/callable registry placeholder, distinct from the mature BLUECAD tool registry | Skeleton | **REPLACE** | Use one capability/MCP boundary under Jarvis authority; preserve BLUECAD's qualified numerical-tool registry as a domain adapter. |
| Hermes | audited upstream and planning kernels exist; no pinned runtime/profile/passthrough/MCP implementation is active on exact base | Candidate, not integrated | **QUALIFY / BUILD** | Re-derive a narrow Hermes lane after current queue + visual identity. Do not vendor or grant ambient authority. |
| Other reference repositories | canonical register and deep audits cover runtime, sandbox, model, memory, code-intelligence and engineering candidates | Reference evidence, not dependencies | **QUALIFY** | Select by capability bake-off and exact license/version evidence. Never create a “clone every repo” milestone. |
| Ollama-specific local lifecycle | production-reachable narrow lifecycle and tests | Useful incumbent with future scaling limit | **KEEP / EXTEND**, then selective **REPLACE** | Preserve current local routes; later introduce a ModelRuntime adapter and migrate only after parity/target-hardware proof. |
| Process/hydraulic engineering kernels | versioned `calc_v0`, process kernel, flowsheet, runner contracts, 047/072/075 evidence and CAD links | Real bounded foundations | **KEEP / HARDEN / EXTEND** | Add property/thermo/process capabilities from real decisions; do not restart a generic simulator. |
| CFD | OpenFOAM adapter remains planned/conditional; no production CFD path verified in this audit | Gap, but demand-gated | **BUILD** only when proxy/model evidence leaves a decision unresolved | CFD is not an early foundation milestone. |
| Optimization/DOE/Pareto study orchestration | inputs and single-run execution exist; no canonical study/batch/Pareto domain found | Real gap above existing evaluators | **BUILD** by reusing runner/BLUECAD | This is the correct Design Explorer insertion point. |
| Generative/implicit geometry | PicoGK/LEAP71 family is audited as a candidate; no BLUECAD adapter exists | Advanced gap | **QUALIFY / BUILD** later | Add only after study/evaluator infrastructure proves a geometry objective that B-Rep primitives cannot meet. |

## 2.1 End-to-end boundary confirmed

The production-shaped path already present is:

```text
operator / Jarvis proposal
        |
        v
BLUECAD candidate + GeometrySpec
        |
        v
deterministic build123d/OCP build
        |
        +--> STEP/STL/GLB + canonical manifest/digests
        |
        v
registry-bound Gmsh subprocess
        |
        +--> mesh.inp / mesh.msh / groups / quality result
        |
        v
registry-bound CalculiX subprocess
        |
        +--> FRD/DAT/log + parsed ResultSummary
        |
        v
simulation run + artifacts + typed evidence + acceptance criteria
        |
        v
FastAPI aggregate/read APIs -> BLUECAD/Runs/Analytics frontend
```

Safe defaults deliberately keep the shipped Gmsh and CalculiX entries disabled. Reachability therefore requires an operator-owned registry with exact executable, version, provenance and SHA-256. The strict GitHub proof installs real tools, generates such a registry and exercises the registry-bound chain. Safe default disablement is not missing adapter implementation.

## 2.2 Confirmed gaps that remain real

- no pinned, isolated Hermes runtime profile is integrated;
- no standards-compatible Hermes passthrough through the complete Jarvis AI authority spine exists;
- no bounded Jarvis MCP/domain-tool server exists;
- generic agent/tool modules remain skeletons;
- trusted bundled runner execution is not an OS sandbox for generated/untrusted code;
- local model lifecycle is Ollama-specific rather than a qualified engine adapter family;
- code intelligence and derived-memory backends remain candidates, not product integrations;
- no canonical DesignStudy/DOE/Pareto orchestration exists;
- CFD, advanced coupling, implicit/generative geometry and training remain conditional future capabilities.

---

# 3. Queue design rules after audit

1. **Capability and ROI before repository adoption.** Every external project must win an exact acceptance test against the incumbent or a proven gap.
2. **Incumbent-first reuse.** A new slice states which existing service, run, artifact, evidence, UI and authority contracts it reuses.
3. **No foundation theatre.** Do not require a universal agent runtime, event rewrite, vector database or optimizer before one bounded product outcome needs it.
4. **Authority stays in Jarvis.** Upstreams may execute replaceable mechanics; they do not own route, budget, sensitivity, canonical state, engineering acceptance or promotion.
5. **Safe defaults remain safe.** Disabled paid AI, zero budget, fake provider, disabled external engineering tools and offline tests remain valid defaults.
6. **Read/proposal before mutation.** Hermes/MCP/runtime adoption begins read-only or proposal-only. State-changing authority is a later, separately proven slice.
7. **Qualification precedes replacement.** Use shadow/bake-off/canary, exact versions and rollback before deleting an incumbent.
8. **Delete after cutover.** Replacement work is incomplete until duplicate skeletons, lifecycle branches, dependencies and stale flags are removed.
9. **One live canonical front.** Planning independence never overrides repository single-front policy.
10. **No false implementation claims.** Docs, fakes and marker-gated tests are evidence of contracts; target-host/tool qualification must be reported separately.

Every promoted slice must answer:

- What is the measurable operator or engineering outcome?
- Is the incumbent KEEP/HARDEN/QUALIFY/EXTEND/REPLACE/BUILD?
- What exact source/master/upstream heads and licenses were inspected?
- Which existing API/service/state/artifact/evidence/UI seams are reused?
- What new authority, durable state, dependency or external process is unavoidable?
- What deterministic test proves value and prevents regression?
- What fails closed, retries, resumes or rolls back?
- What duplicate code becomes deletable?

---

# 4. ROI-ordered macro queue

```text
CURRENT FUNCTIONAL QUEUE
  058c -> 097 -> 098 -> 006b -> 058b, as revalidated by canonical STATUS.md
        |
        v
GLOBAL VISUAL IDENTITY
  identity/tokens/assets/application only; preserve stable backend authority
        |
        v
CS-00 EXACT REVALIDATION + GOVERNING ADR
        |
        v
CS-01 MINIMUM CROSS-RUNTIME CONTRACT + CONFORMANCE HARNESS
        |
        +------------------------------+
        |                              |
        v                              v
CS-02 HERMES READ/PROPOSAL LANE    EF-00 TARGET-HOST ENGINEERING QUALIFICATION
  passthrough + bounded MCP           current CAD/Gmsh/CalculiX/runner chain
  + isolated pinned profile                    |
        |                                       v
        v                                  EF-00/01 qualified run spine
CS-04 OBSERVED CORE HARDENING                + high-ROI adapters
  sandbox only if execution needed                 |
  model runtime/code intelligence                  v
  only by measured ROI                         DX-00..06
        |                                  Design Explorer reusing
        v                                  incumbent evaluators
CS-05 CUTOVER + LEGACY CLEANUP                     |
                                                   v
                                               GE-* advanced
                                               generative engineering
```

CS-02 and target-host engineering qualification may be dependency-independent after CS-01, but implementation remains serialized when repository policy requires one active front.

---

# 5. Phase A — finish the live product before backend expansion

## A-00 — Current functional queue

Primary disposition: **KEEP / COMPLETE**

At each future handoff, read fresh `docs/specs/STATUS.md`; do not trust this snapshot as live authority. On the audit base, the remaining intended functional order is:

1. finish 058c SCENE-SEMANTICS-A1 in PR #319 and reconcile it;
2. 097 JARVIS-ENGINEERING-ACTIONS-0;
3. 098 ENGINEERING-RECORD-LIFECYCLE-0;
4. 006b PARAMETRIC-VARIANTS-1, freshly re-derived;
5. 058b VARIANT-COMPARISON-1, freshly re-derived.

No CS/EF/DX/GE runtime work begins while this queue is active. If the canonical registry changes the order, the registry wins.

## A-01 — Global visual identity

Primary disposition: **BUILD** presentation identity over **KEEP** product/runtime seams.

This phase begins only after the functional queue is complete and reconciled. It may define brand assets, typography, semantic tokens, motion and product-level visual consistency, but it must remain independently removable from backend architecture.

Exit evidence:

- stable application navigation and API contracts;
- light/dark/accessibility/browser evidence at supported targets;
- no frontend-owned provider, filesystem, execution, sensitivity or canonical-state authority;
- explicit record of any product seam that changes the later backend-puzzle assumptions.

---

# 6. Phase B — core Jarvis software and Hermes, minimum useful path first

## CS-00 — Fresh exact-master/upstream revalidation and governing ADR

Primary disposition: **QUALIFY**

Re-fetch exact master, active PRs and exact upstream versions. Re-audit the final application seams, 066–068 status, current Hermes, MCP SDK, sandbox, model-runtime and reference candidates.

The ADR freezes only what is required for the first bounded outcome:

- Jarvis remains authority for state, egress, budget, grants and acceptance;
- Hermes is replaceable and advisory;
- canonical vs derived state;
- exact transport/auth/isolation boundary;
- migration, rollback and deletion rules;
- the smallest first dogfood job and its acceptance metrics.

Exit: a definition-only canonical slice exists; no runtime is installed by this planning handle.

## CS-01 — Minimum cross-runtime contract and conformance kit

Primary disposition: **BUILD / EXTEND**

Do not start with a universal ontology. Freeze only fields exercised by the first Hermes/runtime lane:

- runtime and actor identity;
- task/turn correlation;
- model alias and bounded request envelope;
- capability descriptor and proposal-only grant;
- evidence/provenance reference;
- cancellation/timeout;
- qualification record.

Reuse existing `ai_jobs`, runner/simulation IDs, evidence refs and workspace identities. Add translation instead of replacing them.

Acceptance:

- canonical serialization/digests and version failure behavior;
- no privilege broadening by runtime/subagent;
- correlation from Hermes turn to model/tool/evidence rows;
- exact unsupported-feature response;
- offline conformance fixture with no provider call.

## CS-02 — Pinned Hermes read/proposal-only dogfood lane

Primary disposition: **QUALIFY / BUILD**

This is the first concrete core-software integration, re-derived from frozen 066–069 rather than implementing a generic agent platform first.

One coherent delivery may be split into independently reviewable canonical slices, but the usable lane requires all of these boundaries:

1. **Jarvis AI passthrough** — the exact Hermes-used OpenAI-compatible subset traverses `run_ai_task`, policy, exact-packet egress, budget and `ai_jobs`; no provider credential reaches Hermes.
2. **Bounded Jarvis MCP/domain tools** — begin with read-only context/search/evidence and proposal-only MemoryStore/BLUECAD/calc operations through existing services; no raw SQL/path/shell/code/provider tool.
3. **Pinned isolated profile** — immutable Hermes identity/fingerprint, disposable home, explicit allowlist, no direct provider credentials, no repository/data-root access, no browser/cron/computer/messaging and bounded delegation.
4. **First dogfood** — use proposal-only memory consolidation or another equally bounded job with exact sources, conflicts preserved, cost/tool/model limits and human promotion.

Hermes mechanisms worth reusing only after pin-level verification:

- progressive disclosure for large tool catalogs;
- strict malformed-tool-call failure;
- conflict-aware ordered parallelism;
- checkpoint/session persistence;
- large-result spillover;
- tool-performance and compression-survival evaluation patterns.

Explicit exclusions:

- no Hermes vendoring or fork by default;
- no ambient terminal/filesystem/provider access;
- no canonical state ownership;
- no state-changing engineering action;
- no autonomous cron or proactive loop;
- no claim that every Hermes subsystem must be integrated.

Success metrics:

- useful proposal rate and provenance completeness;
- unsupported-claim/conflict-loss rate;
- tool retries/duplicates/fallback waste;
- exact resume after compression/checkpoint;
- cost/token/latency per accepted useful result;
- zero unauthorized provider, state, filesystem or network action.

## CS-03 — Capability gateway evolution

Primary disposition: generic skeleton **REPLACE**; BLUECAD tool registry **KEEP / EXTEND**

Do not collapse the mature numerical-tool registry into the placeholder generic tool registry. Introduce a Jarvis capability catalog/gateway that can normalize MCP/runtime tools while the BLUECAD registry remains the qualified execution adapter for Gmsh/CalculiX and other numerical binaries.

Required path:

`source -> namespaced identity/schema/provenance -> visibility -> grant -> resource claim -> invoke existing service/adapter -> evidence -> bounded result`

First lane: read/proposal only. State-changing capabilities wait for an exact commit/grant boundary and, where code execution is involved, a real sandbox.

Delete `modules/tools` placeholder code only after all callers are migrated and conformance/rollback evidence is complete.

## CS-04 — Observed high-ROI core hardening

These are conditional, measured slices, not automatic prerequisites for Design Explorer.

| Candidate slice | Incumbent disposition | Activation trigger | First proof |
| --- | --- | --- | --- |
| Real sandbox lane | trusted bundled runner **KEEP**; generated host execution **REPLACE / BUILD** | Hermes/external runtime needs code, terminal or non-bundled execution | Windows/WSL isolation, mount/network/secret/resource/cancel matrix; OpenShell first candidate, alternatives compared |
| ModelRuntime adapter | Ollama lifecycle **KEEP / EXTEND**, selective later **REPLACE** | second engine/hardware target or measured lifecycle burden | same local-route behavior across exact engine/model/OS/hardware tuples |
| Code intelligence | **BUILD** via qualified upstream | repository-scale semantic retrieval/editing saves measured tool/context cost | Serena/LSP/Tree-sitter bake-off; Git/files remain truth; writes use compare-and-set |
| Derived memory/index | canonical MemoryStore **KEEP**; derived backend **BUILD** | bounded dogfood shows retrieval/context failure | provenance, stale invalidation, forget/rebuild and useful-retrieval benchmark |
| Privacy transforms | egress authority **KEEP / HARDEN / EXTEND** | exact workloads need reversible PII transforms or credential proxying | leakage, restore binding, cross-session isolation and fail-closed tests |
| Unified telemetry export | canonical evidence **KEEP**; operational export **EXTEND** | cross-runtime diagnosis lacks comparable traces | one correlation chain without making OTel canonical engineering truth |

## CS-05 — Runtime cutover and cleanup

Primary disposition: **REPLACE**, then delete

Only after shadow/canary evidence:

- route qualified work to the winning runtime adapter;
- increase authority from read-only to proposal-only, then separately to low-risk reversible mutation if justified;
- remove obsolete generic agent/tool skeletons and superseded lifecycle glue;
- remove duplicate registries only where semantic ownership truly overlaps;
- clean dependencies, flags, docs, tests and SBOM entries;
- retain rollback until the evidence window closes.

No “manager agent” receives ambient authority.

---

# 7. Phase C — engineering foundations ordered by ROI

Engineering work begins from the verified incumbent, not from an empty `ENG-*` map.

## EF-00 — Target-host BLUECAD/runner qualification and operational hardening

Primary disposition: **KEEP / QUALIFY / HARDEN**

This is the highest-ROI engineering foundation because it turns already implemented capability into dependable daily operation.

Scope candidates, re-derived from fresh product evidence:

- prove build123d/OCP, Gmsh and CalculiX on supported maintainer targets using exact versions, hashes and provenance;
- provide or verify operator setup/diagnostics for the external registry without enabling tools unsafely by default;
- exercise brief/CAD-link -> geometry -> mesh -> static FEM -> evidence -> frontend inspection on representative BlueRev cases;
- surface actionable disabled/missing/hash/mesh/solver/parse/criteria failures;
- preserve deterministic manifests, run identity, artifacts and rollback;
- measure runtime, resource use and failure recovery.

This slice must not reimplement geometry, meshing, FEM or the runner.

## EF-01 — Engineering evaluation/result contract consolidation

Primary disposition: **KEEP / EXTEND**

Normalize only the cross-study fields missing from existing model, runner, BLUECAD and evidence records:

- evaluator identity/version/digest;
- exact normalized inputs and units;
- tool/model/platform qualification reference;
- outputs, diagnostics and artifact refs;
- feasibility/acceptance outcome;
- deterministic failure taxonomy;
- parent study/candidate correlation.

Avoid a parallel run store. Extend or translate existing `simulation_runs`, runner jobs, BLUECAD attempts and evidence.

## EF-02 — Property and thermodynamics adapters

Primary disposition: **BUILD / EXTEND** from real process needs

First compare the smallest adequate libraries/backends for current BlueRev questions, for example CoolProp and focused ChEDL packages before adopting a full process platform.

Jarvis owns compound identity, units, conditions, provenance, validity domain and acceptance. The backend returns calculations and diagnostics.

Exit: versioned reference cases and domain-of-validity failures, not merely a successful library call.

## EF-03 — Process-model extension

Primary disposition: current kernels **KEEP / HARDEN / EXTEND**

Extend 047/075/078/093-derived work only where a decision requires it:

- canonical serial BlueRev topology before broad alternative topology generation;
- PBR model only after its existing planning spec receives readiness;
- mass/energy/property coupling through the existing flowsheet/runner identity;
- external BioSTEAM/IDAES/DWSIM/Modelica paths only when they beat bounded internal models on a concrete use case.

Do not build a generic Aspen replacement.

## EF-04 — Scientific field/result visualization

Primary disposition: existing GLB/Analytics **KEEP / EXTEND**; general field contract **BUILD** when required

Use VTK/PyVista/ParaView-compatible or meshio-style artifacts only when field data is needed. The field artifact remains engineering data; frontend scene state remains a view.

## EF-05 — Additional solvers by unresolved decision

Primary disposition: **QUALIFY / EXTEND / BUILD** only on demand

- modal/thermal CalculiX: extend the incumbent adapter and verification battery;
- alternative FEM: qualify FEniCSx/Code_Aster only for a capability or verification gap;
- CFD: build an inspectable OpenFOAM/SU2 case-bundle lane only when lighter process/hydraulic models cannot resolve a named decision;
- no solver portfolio milestone whose only result is “more backends installed”.

---

# 8. Phase D — Design Explorer at the first reusable point

Design Explorer starts after EF-00 and EF-01, once at least one deterministic evaluator is qualified. It does **not** wait for every engineering adapter, CFD, advanced geometry or training stack.

Its first valuable conversation is:

`natural-language goal -> structured study proposal -> user confirmation -> deterministic batch -> feasibility/Pareto -> provenance-grounded explanation`

The AI proposes and explains. Deterministic code owns study validation, candidate generation, execution, feasibility, ranking and evidence.

## DX-00 — Design Study domain contract

Primary disposition: **BUILD** over existing model/run contracts

Objects:

- `DesignVariable` referencing an existing contract variable/binding where possible;
- `Constraint` with unit, bound, hard/soft semantics and evidence source;
- `Objective` with minimize/maximize, unit and comparison contract;
- `DesignStudy` with exact evaluator/version, seed, method and budgets;
- `CandidateDesign` with canonical input digest and parent study;
- `EvaluationResult` referencing existing runs/artifacts/evidence;
- `FeasibilityResult` and `ParetoSet` as reproducible derived records.

No duplicate Parameter, runner, BLUECAD candidate, artifact or evidence store.

## DX-01 — Conversational Study Builder

Primary disposition: **EXTEND** existing Jarvis sidecar/AI spine

Natural language becomes a typed proposal. The UI shows variables, bounds, constraints, objectives, evaluator, units, sample budget and unresolved assumptions. Nothing executes until deterministic validation passes and the user explicitly confirms.

Unsupported variables, unit mismatches, missing bounds and unavailable evaluators fail closed.

## DX-02 — Deterministic candidate evaluator adapter

Primary disposition: **KEEP / EXTEND** runner and BLUECAD

Map one candidate to one existing evaluator path:

- bundled `calc_v0`/process model;
- BLUECAD geometry and optional qualified mesh/FEM stage;
- later property/process/CFD adapters through the same result envelope.

Cache only exact duplicate evaluator/input/version digests. Preserve failed and infeasible outcomes; never fabricate missing metrics.

## DX-03 — Reproducible batch/DOE engine

Primary disposition: **BUILD**

Start with the smallest methods that meet real studies:

- deterministic grid for small discrete spaces;
- seeded random and Latin hypercube;
- Sobol only after a tested implementation/dependency is justified;
- strict candidate/run/concurrency/time/cost limits;
- resume from persisted terminal candidate results;
- no live provider call per numerical candidate.

## DX-04 — Failure and feasibility taxonomy

Primary disposition: **BUILD / EXTEND**

Normalize without hiding subsystem detail:

- invalid study/input/unit;
- evaluator unavailable/unqualified;
- geometry invalid;
- mesh failed/error;
- solver failed/timeout/parse error;
- criterion infeasible;
- stale evidence/source;
- cancelled/budget/resource exhausted.

Feasibility is deterministic. AI text cannot reclassify a failed or infeasible run.

## DX-05 — Pareto and comparison engine

Primary disposition: **BUILD**

- unit/comparability checks before ranking;
- deterministic dominance and tie behavior;
- hard constraints filter feasibility before Pareto ranking;
- soft constraints remain explicit penalties, never silently converted;
- every point links to exact candidate/run/evidence;
- recomputation from the same study/result set yields the same Pareto digest.

## DX-06 — Provenance-grounded conversational explanation

Primary disposition: **EXTEND** Jarvis sidecar and evidence/context spine

The conversation may explain:

- what was varied and held fixed;
- why candidates failed or were dominated;
- trade-offs among Pareto points;
- sensitivity observed within the sampled domain;
- which evidence is missing or unqualified;
- the next highest-value study.

It must distinguish computed fact, deterministic comparison and model interpretation. Selection/promotion remains explicit human authority.

## DX first release acceptance

- one real BlueRev study uses an existing qualified deterministic evaluator;
- hundreds of bounded candidates can be generated, resumed and audited without duplicate execution;
- failures and infeasible cases remain visible;
- Pareto output is reproducible and unit-safe;
- every claim links to exact inputs, evaluator, artifacts and evidence;
- the user can inspect a selected BLUECAD candidate through the existing workbench;
- no surrogate, CFD, implicit geometry or autonomous promotion is required.

---

# 9. Phase E — advanced generative engineering

These handles remain after Design Explorer proves demand and produces trustworthy study traces.

## GE-00 — Coupling and mathematical optimization

Primary disposition: **QUALIFY / BUILD**

Compare OpenMDAO, CasADi, Pyomo or a smaller method only against named studies. Preserve objective/constraint/evaluator identity and verify candidate solutions independently through the same DX evaluator contract.

## GE-01 — Advanced/generative geometry adapter

Primary disposition: BLUECAD semantic IR **KEEP**; PicoGK/LEAP71-style backend **QUALIFY / BUILD**

Activation requires a geometry class or manufacturing objective that existing B-Rep primitives cannot satisfy efficiently. Generated geometry must retain stable semantic source bindings, units, manifests, meshability and independent acceptance evidence.

No external geometry library becomes canonical engineering truth.

## GE-02 — Multi-physics and high-fidelity solver campaigns

Primary disposition: **QUALIFY / BUILD**

Add CFD/FEM/thermal/modal/coupled campaigns only when lower-cost evaluators leave a decision unresolved. Use multi-fidelity promotion: cheap deterministic filters first, expensive solvers only for surviving candidates.

## GE-03 — Surrogates and adaptive search

Primary disposition: **BUILD** only after qualified datasets

Require train/validation/holdout provenance, uncertainty and domain-of-validity checks. A surrogate proposes candidates; authoritative evaluators decide acceptance.

## GE-04 — Specialist training/self-improvement

Primary disposition: **PARK**, later **QUALIFY / BUILD**

Activation prerequisites:

- stable production traces and normalized failure classes;
- authoritative evaluators and holdouts;
- clean data provenance/licenses;
- measured quality/latency/cost gap;
- offline candidate -> deterministic gates -> review -> normal promotion.

Live authority-bearing code, policy or engineering truth never self-modifies.

---

# 10. Promotion order and ROI gates

| Order | Planning outcome | Primary disposition | Must already be true | Measurable payoff |
| ---: | --- | --- | --- | --- |
| 1 | Current functional queue complete | **KEEP / COMPLETE** | canonical `STATUS.md` dependencies | stable usable product |
| 2 | Global visual identity complete | **BUILD** presentation only | functional application seams stable | coherent operator experience |
| 3 | CS-00 exact revalidation/ADR | **QUALIFY** | fresh master/upstreams | prevents stale or duplicative adoption |
| 4 | CS-01 minimum runtime contract | **BUILD / EXTEND** | first dogfood chosen | replaceability and comparable evidence |
| 5 | CS-02 pinned Hermes proposal lane | **QUALIFY / BUILD** | 066–068 freshly re-derived and authorized | useful bounded conversation/delegation without second authority |
| 6 | EF-00 target-host existing pipeline qualification | **KEEP / QUALIFY / HARDEN** | supported host/tool identities | converts existing CAD/mesh/FEM into dependable daily capability |
| 7 | EF-01 evaluation/result consolidation | **KEEP / EXTEND** | real runs expose exact missing fields | reusable evaluator identity without second store |
| 8 | EF-02/03 highest-value property/process extension | **EXTEND / BUILD** | named BlueRev decision | better engineering answers per unit effort |
| 9 | DX-00..06 first Design Explorer | **BUILD / EXTEND** | at least one qualified deterministic evaluator | conversational batch exploration and reproducible Pareto trade-offs |
| 10 | CS-03/04 additional core hardening | mixed | measured bottleneck/authority need | avoids speculative platform work |
| 11 | EF-04/05 higher-fidelity result/solver extensions | mixed | simpler models insufficient | resolves named engineering uncertainty |
| 12 | GE-* generative engineering | **QUALIFY / BUILD** | DX traces/evaluators and measured demand | optimized/generative designs with independent verification |
| 13 | CS-05 cleanup after proven cutovers | **REPLACE / DELETE** | production evidence + rollback window | smaller, maintainable system |

The exact canonical order may interleave CS hardening with EF/DX only when a promoted slice proves it is a real dependency. A hypothetical future need is insufficient.

---

# 11. Qualification, merge and deletion gates

## Upstream/dependency qualification

Record for every adopted external component:

- repository/package and immutable version/commit;
- source/package/binary fingerprint;
- license/SPDX, redistribution boundary and notices;
- supported OS/hardware/runtime tuple;
- capability and unsupported-feature matrix;
- dependency/SBOM delta;
- exact benchmark/conformance evidence against incumbent or gap;
- upgrade, rollback and failure-mode plan.

## Exact-head merge gate

A future slice merges only when:

- remote PR head equals the reviewed/tested expected SHA;
- exact-head deterministic gates pass;
- subsystem qualification/conformance passes;
- no current blocking finding remains;
- no hidden authority, state, egress, credential or spend path exists;
- runtime scope matches the canonical accepted spec;
- `STATUS.md` is changed only when its lifecycle requires it.

## Replacement/deletion gate

Delete an incumbent only when:

- migrated callers/callgraph are proven;
- replacement behavior is production-reachable;
- state/provenance compatibility is proven;
- rollback window has completed;
- config, flags, tests, docs, dependencies and SBOM are cleaned;
- no stale path silently keeps two authorities alive.

---

# 12. Stop rules

Cancel or park a slice when:

- the incumbent already meets the acceptance criterion after modest hardening;
- an upstream adds no measured value;
- license, supply-chain, footprint or Windows/local/offline cost exceeds benefit;
- it moves canonical authority outside Jarvis;
- it is justified by popularity, demo appearance or hypothetical scale;
- a simpler evaluator resolves the engineering decision;
- it requires building advanced generative infrastructure before trustworthy baseline evaluation exists.

---

# 13. Expected end state

The backend puzzle should leave JarvisOS smaller in bespoke generic framework code and stronger in engineering evidence.

Stable ownership:

- **JarvisOS:** authority, grants, egress, budget, canonical state/evidence, engineering identity, routing policy, commit/promotion rules and acceptance/verifiers.
- **BLUECAD:** semantic geometry, stable source bindings, artifact/run identity and engineering-facing adapter contracts.
- **Replaceable upstreams:** agent loops, MCP transport/tool implementations, isolation mechanisms, inference engines, code intelligence, derived indexes, numerical kernels and telemetry transport where they win qualification.
- **Frontend:** operator view/controller over backend truth; visual identity without provider, filesystem, execution or canonical-state authority.

The first Tony-Stark-like Design Explorer conversation arrives only after the program and engineering spine work. When it arrives, it is not theatre: it reuses real models, CAD, mesh, FEM, evidence, workbench and authority boundaries already proven by the product.

---

# 14. Handoff rule at activation time

The future coordinating agent must:

1. fetch fresh exact `master`, `STATUS.md`, active PRs and checks;
2. verify the current queue and visual-identity completion;
3. re-read the strategy, this blueprint and the candidate register;
4. re-audit every materially changed incumbent and upstream;
5. reclassify each area KEEP/HARDEN/QUALIFY/EXTEND/REPLACE/BUILD;
6. collapse, split or reorder these handles by actual ROI and dependencies;
7. derive exactly one definition-only canonical slice;
8. proceed through readiness, implementation, exact-head evidence, merge and registry reconciliation.

Never copy `CS-*`, `EF-*`, `DX-*` or `GE-*` into `STATUS.md` by inertia.
