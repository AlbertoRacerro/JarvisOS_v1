# Maintainer control room — canonical builder launch 2026-09-22

Status: ACCEPTED PLANNING / READINESS AUTHORITY. This document authorizes only the spec rows that STATUS.md marks ready. Runtime work still requires every hard dependency to be merged and the normal exact-head lifecycle.

Planning base SHA: 7748b022d4a95f20943444672ba332b4dd69819f

## 1. Purpose

Convert the maintainer-accepted JarvisOS architecture into the smallest canonical contract and builder launch surface needed for implementation. This document does not reopen the Hermes, second-brain, typed local decision, local routing, or Aspen/Dynsim-like Engineering product decisions.

Runtime and deterministic evidence remain stronger than prose. Canonical SQL/Git owners remain authoritative. Derived retrieval/index stores are rebuildable. Hermes is a generic agent runtime, not the Jarvis authority boundary. Scientific backends own numerical algorithms, not product authority. Local semantic decisions are advisory and never grant permission.

## 2. Fresh reconciliation and dispositions

- master at planning: 7748b022d4a95f20943444672ba332b4dd69819f.
- PR #661 is merged; spec 144 is therefore merged, not in_review.
- PR #662 is merged and is the canonical capability-manual consolidation.
- issues #655 and #656 are complete.
- mapping PRs #657-660 are superseded by #662 and must remain closed without merge.
- capability manual runtime map is the preferred jump table for existing owners/files/tests.

Canonical identity disposition:

| Identity | Disposition | Re-derived meaning |
| --- | --- | --- |
| 014 | REDERIVE / READY | OpenFOAM CFD adapter over existing BLUECAD/mesh/evidence owners; solver execution and field ingest must be explicit, qualified, and non-canonical. |
| 025 | RETAIN | Provider/task semantic routing evaluation remains distinct from local-model selection. It does not own the new local decision router. |
| 060 | REDERIVE, definition-only umbrella | Hermes is mandatory generic agent runtime; Jarvis retains state/policy/egress/budget/credentials/promotion authority. |
| 063 | CANCEL / SUPERSEDE | Old markdown-vault/no-vectors-over-canonical-records contract conflicts with the accepted derived second brain. Replaced by 148. |
| 064 | CANCEL / SUPERSEDE | Literature semantic retrieval is absorbed into 148 rather than a second RAG authority. |
| 066-068 | CANCEL / SUPERSEDE | Frozen historical Hermes slices are replaced by 146 under the re-derived 060 umbrella. |
| 069 | CANCEL / SUPERSEDE | Memory consolidation becomes part of the 146/148 integration boundary; no independent memory authority. |
| 102 | REDERIVE / READY | Engineering evidence and qualification contract, preserving 044/077 authority while adding fidelity/validity/uncertainty references needed by scientific adapters. |
| 103 | REDERIVE / READY | Targeted upstream qualification of the accepted shortlist; not a new broad ecosystem audit. |
| 104 | REDERIVE / READY | Strangle duplicated generic custom process-solver infrastructure according to 103 evidence. |
| 105 | REDERIVE / READY | Engineering-domain cleanup only after 104 establishes the surviving owners. |
| 106 | REDERIVE / READY | Minimal engineering evaluator/adapter protocol consuming 145/102 contracts; no universal solver schema. |
| 107 | REDERIVE / READY | Dynamic BlueRev/PBR evaluator framework plus qualification harness; biology/physics are not called validated without evidence. |
| 108 | REDERIVE / READY | Reproducible design-study controller over evaluator results, feasibility, failures, uncertainty and Pareto evidence. |
| 109 | REDERIVE / READY | ProcessDesignEnvelope to BLUECAD/geometry handoff with physical-verification feedback. |
| 110 | REDERIVE / READY | Decision-driven multifidelity orchestration across qualified reduced models, CFD/FEM and specialists. |
| 144 | RECONCILE | merged through #661. |
| 145 | NEW / READY | FOUNDATION-CONTRACTS-1 — shared AI/retrieval/resource contracts and serialization boundary. |
| 146 | NEW / READY | HERMES-RUNTIME-1 — governed Hermes worker integration. |
| 147 | NEW / READY | LOCAL-DECISION-ROUTING-1 — typed semantic decision service plus local-model routing/resource owner. |
| 148 | NEW / READY | SECOND-BRAIN-1 — rebuildable hybrid retrieval/index layer over canonical sources. |
| 149 | NEW / READY | ENGINEERING-OPERATOR-INTEGRATION-1 — final coherent operator surfaces over real H/L/R/P/C capabilities. |

## 3. External candidate baselines

Hermes:
- current upstream main observed during planning: be65eab584a8490d39f7552b93e603d82c929d17;
- latest stable release observed during planning: v0.21.4 / d337b736aa1e8ebecfab043842d13e4a2d2f48a3;
- H must qualify the stable release against the Jarvis contracts before locking the dependency. Do not follow main implicitly.

Typed local decision model:
- candidate: fastino/gliner2.5-multi-v1;
- observed model card: 287M parameters, multilingual, Apache-2.0;
- candidate is replaceable and is not pinned by this planning change;
- L must resolve an immutable model revision and benchmark it against the typed-decision corpus before promotion.

## 4. Shared contract freeze

145 is the sole first-wave implementation owner for shared AI/retrieval/resource contracts and any shared migration/manifests needed by them. No other builder may invent incompatible equivalents.

Freeze only these shared shapes:

A. Hermes ↔ Jarvis
- AgentSessionRef: jarvis_thread_id, hermes_session_id, profile_id, workspace_id, generation, upstream_revision.
- AgentControlCommand: start/interrupt/resume/close, correlation_id, expected_generation, deadline.
- AgentEvent: event_id, session_ref, kind, timestamp, bounded payload_ref/digest, evidence_refs.
- CapabilityGrantRef: server-owned capability id, scope/constraints, expiry/revocation metadata. It is not permission inferred from model output.

B. Governed inference/tool exchange
- InferenceEnvelope: task kind, Jarvis job/flow correlation, context-bundle ref/digest, route/model candidate, sensitivity/policy refs, deadline/cancellation, provenance.
- StructuredToolCall and StructuredToolResult: call id, capability id, typed args/result or artifact ref, status, deadline/cancellation, provenance/evidence refs.
- All product inference ultimately maps through the existing run_ai_task/ai_jobs and egress/budget authority. Auxiliary Hermes inference is not exempt.

C. Decision layer
- DecisionRequest: decision_type, bounded candidate_set, constraints, RuntimeResourceSnapshot, evidence_refs.
- DecisionResult: selected candidate or abstain, typed bool/enum/score outputs, model_ref, calibration_ref, evidence_refs, diagnostic reason code.
- No free-form JSON dependency and no permission fields.

D. Retrieval
- SourceRef: authority_owner, object_type, object_id/path, revision, digest, location/range where applicable.
- RetrievalHit: SourceRef plus lexical/vector/graph score components and bounded excerpt.
- ContextBundle: ordered resolved refs, evidence manifest, token estimate, expansion level, digests.
- IndexStore protocol: rebuild/upsert/delete/search_lexical/search_vector/expand_graph/resolve_authoritative.
- Index data is derived/rebuildable and never replaces authoritative reread.

E. Engineering
145 freezes only cross-workstream identity/value envelopes, not a universal process schema:
- EngineeringProjectRef / EngineeringRevisionRef;
- Quantity(value, unit, basis/provenance ref);
- ComponentRegistryRef / PropertyBasisRef;
- MaterialStateRef;
- ProcessModelIRRef / DynamicModelRef / EnvironmentalScenarioRef;
- ProcessDesignEnvelopeRef;
- GeometryAssetRef / MeshArtifactRef / PhysicsCaseRef;
- EvaluationRequestRef / EvaluationResultRef;
- StudyRef;
- ValidityEnvelopeRef with domain, uncertainty, qualification status and evidence refs.

102/106 own the engineering-specific content and evaluator semantics on top of these envelopes.

F. Resource arbitration
- RuntimeResourceSnapshot: CPU/RAM/GPU/VRAM, loaded models, worker/solver occupancy, timestamp/generation.
- ResourceReservationRequest/Lease: requested resources, owner/correlation, deadline/expiry, state, release reason.
- Decision recommends; deterministic reservation/revalidation admits execution.

## 5. Dependency graph and merge order

Planning merge
→ K0 145 shared contracts
→ parallel:
  - H 146
  - L 147
  - R 148
  - K1 102 → 106 engineering contract adoption
→ after 102: P starts 103
→ after 106: C starts 014
→ P: 103 → 104 → 105 → 107 → 108 → 109
→ C/P integration: 110 after 106 + 108 + 109
→ U 149 after 146 + 147 + 148 + 107 + 108 + 109 + 110
→ Astra checkpoints at the explicit gates below.

One owner of time/state is mandatory for each dynamic simulation. Co-simulation may couple engines but must not create competing time/state authorities.

## 6. Builder work packets

### K — CONTRACTS / FOUNDATION

task_id: K-145-102-106

title: Shared contract and engineering-evidence freeze

product outcome: Stable minimal contracts that prevent H/L/R/P/C from inventing incompatible session, inference, tool, decision, retrieval, resource, evidence and evaluator envelopes.

canonical spec/readiness identity: 145 first; then 102 followed by 106 after 145 merges. All are ready in STATUS.

exact prerequisite/base SHA: planning authority base 7748b022d4a95f20943444672ba332b4dd69819f. Implementation MUST re-resolve and use the exact master SHA containing this planning PR; K1 must use the exact master SHA containing K0.

dependencies: existing canonical SQL, AI execution, egress/budget, context/action, Project Knowledge, repository-truth and architecture-enforcement owners. K1 starts after merged 145; 106 additionally waits for merged 102.

existing owners/interfaces to reuse: backend/app/core database/schema/repository/paths; run_ai_task and ai_jobs; 059b/061 flow/egress owners; 111 context/action contracts; 112 Project Knowledge; 118 repository truth; 044/077 evidence.

allowed write scope: shared contract modules in their existing owning packages; additive shared migrations/manifests only when strictly required; backend contract tests; STATUS only by the coordinator when lifecycle changes.

forbidden/conflicting scope: Hermes worker implementation, retrieval algorithms/index population, model runtime/router implementation, scientific equations/solver adapters, frontend product work, second canonical stores.

shared contracts consumed: none for K0; K1 consumes 145.

implementation requirements: additive/versioned contracts; serializable stable identifiers; explicit digest/revision/provenance; deadline/cancellation; no permission in semantic outputs; migration idempotence; resource lease CAS/generation behavior.

non-goals: generic event bus, universal engineering schema, generic agent runtime, new provider gateway.

deterministic tests: schema roundtrip/backward rejection where required; migration idempotence; stale generation/CAS refusal; cancellation/deadline parsing; architecture gate; pytest/ruff/mypy ratchet causally affected.

runtime/browser/hardware/solver evidence: no browser required; one Windows + Linux contract import/migration smoke if platform-sensitive.

scientific qualification requirement: 102/106 may encode qualification metadata only; they must not declare any model qualified.

stop condition: 145 merged, then 102 and 106 merged with no competing shared schema owners and downstream builders can consume frozen versions.

expected handoff: exact SHAs, schema/module paths, version numbers, migration IDs, tests, compatibility notes.

safe parallel peers: after K0 merge, H/L/R may run while K1 completes. K0 itself is the sole shared-contract writer.

required realtime coordination: mandatory for any proposed change to a frozen field or shared migration.

preferred worker capability: strong repository coding agent plus adversarial reviewer.

### H — HERMES

task_id: H-146

title: Governed Hermes worker integration

product outcome: Full Hermes generic agent functionality available through a bounded Windows↔WSL worker while Jarvis remains authoritative for policy, canonical state, inference admission and evidence.

canonical spec/readiness identity: 060 umbrella + 146 implementation.

exact prerequisite/base SHA: exact master containing merged K0/145.

dependencies: 145, 059b, 061a, 061b, 090, 111, 124, 129.

existing owners/interfaces to reuse: AI threads, run_ai_task, provider registry/gateway, sensitivity/egress/budget, Jarvis context/actions, capability/tool registry, existing local process supervision.

allowed write scope: a dedicated Hermes integration/worker adapter surface, bounded WSL lifecycle scripts/config templates, tests and operator diagnostics; narrow existing-owner adapters only where required by 145.

forbidden/conflicting scope: Hermes-owned canonical transcript, provider keys in Hermes, direct provider bypass, Hermes security policy as Jarvis boundary, a second Jarvis memory/store, arbitrary host filesystem/process authority.

shared contracts consumed: AgentSessionRef, control/events, InferenceEnvelope, tool call/result, resource snapshot/lease, SourceRef/ContextBundle.

implementation requirements: qualify stable v0.21.4 candidate before lock; jarvis_thread_id↔hermes_session_id↔profile mapping; interrupt/resume/recovery; all auxiliary inference relayed/governed; bounded tool/capability broker; session/event evidence projection; failure isolation and worker restart.

non-goals: redesign Hermes internals, fork Hermes without concrete blocker, move Jarvis policy into Hermes.

deterministic tests: session mapping/idempotence, stale generation, cancellation, worker loss/recovery, direct-provider bypass rejection, capability denial, evidence correlation.

runtime/browser/hardware/solver evidence: real WSL2 worker smoke on Windows; real interrupt/resume; one long-running session recovery; verify no hidden direct external inference path in exercised features.

scientific qualification requirement: none.

stop condition: Hermes core loop/tools/sessions/delegation/skills/memory-search paths are reachable through Jarvis boundaries and Checkpoint A can exercise them without authority bypass.

expected handoff: pinned upstream revision, dependency method, worker launch/health protocol, exact smoke transcript/evidence refs, unresolved upstream quirks.

safe parallel peers: L, R, K1; P research/qualification when shared files do not overlap.

required realtime coordination: with L on inference/resource arbitration and R on memory/session retrieval seam; with K for any contract change.

preferred worker capability: strong repository coding agent with WSL/runtime verification.

### L — LOCAL AI

task_id: L-147

title: Typed decision service and local-model routing

product outcome: Local constrained semantic decisions plus evidence-based local model selection, separated from deterministic permission/admission.

canonical spec/readiness identity: 147. Spec 025 remains separate provider/task-route evaluation.

exact prerequisite/base SHA: exact master containing merged K0/145.

dependencies: 145, 061a, 136.

existing owners/interfaces to reuse: backend/app/modules/local_ai, local_ai_eval, existing routing/default resolution, AI job/flow evidence, local runtime status.

allowed write scope: local_ai/local_ai_eval and narrowly owned local routing/resource-supervision modules/tests; no shared migrations outside K.

forbidden/conflicting scope: external egress permission, secret access decisions, arbitrary model loading, arbitrary tool execution, bypassing run_ai_task/admission, free-form JSON as decision contract.

shared contracts consumed: DecisionRequest/Result, RuntimeResourceSnapshot, reservation lease, InferenceEnvelope/evidence refs.

implementation requirements: qualify fastino/gliner2.5-multi-v1 or replace it from evidence; bounded bool/enum/score/candidate choice with abstention; measured quality/calibration refs; model capability/context/resource/loaded-state/latency ranking; revalidate and reserve resources after semantic ranking.

non-goals: provider-policy replacement, autonomous permission engine, universal LLM router.

deterministic tests: invalid candidate refusal, abstention, schema/type bounds, stale runtime snapshot, competing reservation race, fallback after load failure, no-egress guarantee.

runtime/browser/hardware/solver evidence: CPU decision-model benchmark; RTX 5070 local-model routing/reservation smoke where available; resource pressure case; cold vs loaded model latency evidence.

scientific qualification requirement: none, but semantic benchmark quality must be measured rather than inferred from valid structure.

stop condition: local selection runs as deterministic admission → semantic ranking → revalidation/reservation → execution → evidence, with permission still outside the model.

expected handoff: immutable model revision if promoted, benchmark corpus/results, calibration thresholds, resource-owner API, failure/fallback matrix.

safe parallel peers: H, R, K1.

required realtime coordination: with H for auxiliary inference/resource competition and K for contract changes.

preferred worker capability: strong coding agent plus model-evaluation worker.

### R — RETRIEVAL

task_id: R-148

title: Rebuildable second brain

product outcome: Token-efficient lexical/vector/graph/symbol/revision-aware retrieval that always resolves authoritative refs before use.

canonical spec/readiness identity: 148; supersedes 063/064 and absorbs their valid intent.

exact prerequisite/base SHA: exact master containing merged K0/145.

dependencies: 090, 112, 113, 114, 115, 118, 145.

existing owners/interfaces to reuse: canonical SQLite repositories, Project Knowledge, Model Dossier, Literature, Project Search, Coding repository truth, AI Threads, Git exact-SHA truth.

allowed write scope: dedicated derived retrieval/index implementation, index rebuild tooling, symbol indexers, retrieval tests/benchmarks; additive derived-index persistence only through K-owned schema/migration change.

forbidden/conflicting scope: canonical record mutation, second project/memory authority, vector result treated as truth, direct provider/Ollama calls, unbounded repository rereads.

shared contracts consumed: IndexStore, SourceRef, RetrievalHit, ContextBundle, evidence manifest/digests.

implementation requirements: FTS5/BM25; multilingual-e5-small candidate behind embedding abstraction; sqlite-vec behind IndexStore; typed temporal graph; Git revision-bound symbol index; hierarchical summaries; progressive expansion; optional Hermes session/memory adapter after 146; authoritative reread before final bundle.

non-goals: cloud vector DB, hidden canonical copy, generic web RAG, semantic promotion.

deterministic tests: full rebuild equality/invariants, deleted/stale revision invalidation, exact-id/phrase recall, lexical+vector fusion, bounded graph expansion, authoritative reread mismatch refusal, token budget metrics.

runtime/browser/hardware/solver evidence: real repository index/rebuild benchmark; median target <=2k tokens and ordinary <=4k on representative tasks, reported as evidence not a hard semantic guarantee.

scientific qualification requirement: scientific retrieval must preserve source/provenance/conditions/units; retrieval relevance is not scientific validity.

stop condition: representative coding/engineering/project queries retrieve bounded evidence with stable refs/digests and no stale/canonical ambiguity.

expected handoff: index schema/version, rebuild command, benchmark dataset/results, token distributions, known recall gaps.

safe parallel peers: H, L, K1.

required realtime coordination: with H for Hermes-memory adapter and K for any derived persistence changes.

preferred worker capability: strong repository/data coding agent; cheap worker acceptable for corpus/benchmark fixture construction.

### P — PROCESS / BLUEREV

task_id: P-102-109

title: Dynamic BlueRev process and scientific stack

product outcome: A coherent dynamic process-design environment for Nannochloropsis gaditana cultivation, harvest and storage, with explicit evidence/qualification and no invented validation.

canonical spec/readiness identity: 102→103→104→105→107→108→109.

exact prerequisite/base SHA: 102 uses exact master containing merged 145; later phases use exact master containing their hard predecessor.

dependencies: STATUS rows as re-derived here.

existing owners/interfaces to reuse: 047/048/049 equations/tests as incumbent evidence only; 071b properties; 075 process-kernel fixtures where useful; 044/077 evidence; 112 Project Knowledge; 145 contracts.

allowed write scope: selected process/property/dynamics adapters and BlueRev-specific model modules/tests/study controllers; no shared contract edits without K.

forbidden/conflicting scope: preserving custom solver code for sunk-cost reasons, installing every candidate, one-off 047-only beta, static-only plant representation, hidden CAD process authority, invented biological parameters.

shared contracts consumed: engineering refs, Quantity/MaterialState, DynamicModel/EnvironmentalScenario, EvaluationRequest/Result, validity/evidence envelopes, ProcessDesignEnvelope.

implementation requirements:
- 103 is targeted qualification of the accepted backend shortlist, deciding roles/adapters/boundaries rather than rediscovering candidates;
- thermo/process candidates include CoolProp, ChEDL thermo/chemicals/fluids/ht, ThermoSTEAM/BioSTEAM, IDAES/Pyomo, QSDsan/WaterTAP, DWSIM/DTL/CAPE-OPEN, NeqSim and specialists where evidence justifies them;
- dynamics/control candidates include FMI/FMPy, OpenModelica where justified, CasADi, do-mpc, SUNDIALS;
- studies use OpenMDAO where justified;
- one time/state owner per dynamic simulation;
- explicit holdup, levels, pressure/flow, pumps/valves/controllers, harvest/replenishment, cleaning/shutdown, daily light/weather, initialization and balances where the model requires them;
- 107 separates model availability from scientific qualification.

non-goals: every solver installed, pretending literature candidates are validated, universal flowsheet engine before role qualification.

deterministic tests: units/dimensionality, mass/energy/species balances, edge cases, initialization failure taxonomy, dynamic conservation, restart/reproducibility, adapter failure mapping, solver comparison fixtures where overlap exists.

runtime/browser/hardware/solver evidence: real selected solver smokes on supported Windows/WSL; at least one periodic day/night dynamic scenario; real recycle/design case where claimed; no synthetic solver success presented as real.

scientific qualification requirement: mandatory for every BlueRev-specific model: source, organism/strain, conditions, units, uncertainty, calibration basis, validity domain, benchmark evidence, qualification status.

stop condition: 109 emits a traceable ProcessDesignEnvelope from qualified/clearly-unqualified dynamic study evidence without CAD becoming process authority.

expected handoff: selected role matrix, adapter boundaries, deleted/wrapped custom owners, benchmark evidence, scientific qualification ledger, study artifacts.

safe parallel peers: after 145, 103 may run while H/L/R execute. P internal phases remain dependency-serialized.

required realtime coordination: K for evaluator/evidence contracts; C for 109/110 interface; U only once product surfaces exist.

preferred worker capability: strong numerical/process coding agent plus independent scientific/numerical reviewer.

### C — CAD / CAE

task_id: C-014-110

title: Qualified geometry, mesh, CFD/FEM and multiphysics adapters

product outcome: Reuse BLUECAD/Gmsh/CalculiX evidence paths and add qualified OpenFOAM/multifidelity integration without creating a second geometry/evidence authority.

canonical spec/readiness identity: 014 first after 106; 110 after 108/109. Existing 005/006/024/038/044 capabilities remain owners.

exact prerequisite/base SHA: 014 uses exact master containing merged 106; 110 uses exact master containing merged 108 and 109.

dependencies: 014 → existing CAD/FEM owners + 106. 110 → 106,108,109.

existing owners/interfaces to reuse: backend/app/modules/bluecad GeometrySpec/build/export/ledger/evidence; mesh_adapter Gmsh boundary; fem_adapter CalculiX parsing/verification; runner tool registry; VTK/field artifacts where already present.

allowed write scope: BLUECAD/CAE adapter modules, solver case bundles, result parsers/ingest, benchmark fixtures/tests; no shared schemas outside K.

forbidden/conflicting scope: duplicate GeometrySpec/evidence ledger, unqualified solver-success claims, automatic fidelity escalation without 110 policy/evidence, optional solver sprawl without decision need.

shared contracts consumed: GeometryAsset/MeshArtifact/PhysicsCase, EvaluationRequest/Result, ProcessDesignEnvelope, Study/ValidityEnvelope.

implementation requirements: 014 OpenFOAM case generation/execution/ingest through registered external-tool boundary; meshio/VTK/PyVista/ParaView-compatible results where useful; preserve Gmsh/CalculiX; optional SU2/FEniCSx/PETSc/Code_Aster/Netgen only after explicit qualification need; 110 carries fidelity/validity evidence and feeds results back to the study.

non-goals: replacing BLUECAD, generic CAE desktop suite, mandatory installation of every candidate.

deterministic tests: manifest/label identity, unit/frame consistency, parser hostile/missing fields, mesh/result lineage, benchmark residuals, stale geometry refusal, solver-not-installed truthfulness.

runtime/browser/hardware/solver evidence: real Gmsh/CalculiX/OpenFOAM execution where claimed; benchmark case with preserved inputs/mesh/solver/version/results; rendering/inspection proof only when product criteria depend on it.

scientific qualification requirement: CFD/FEM correlations/turbulence/material/boundary assumptions carry validity/benchmark status; no false physical validation from numerical convergence alone.

stop condition: qualified high-fidelity results can be attached to the same study/evidence graph and can reopen process design when they invalidate reduced assumptions.

expected handoff: solver/version matrix, case artifacts, benchmark evidence, adapter failure taxonomy, result-ingest refs.

safe parallel peers: 014 can run after 106 while P continues; 110 is an integration phase with P.

required realtime coordination: with P at ProcessDesignEnvelope and study feedback; K for evaluator contract changes.

preferred worker capability: CAE/CFD coding agent plus independent numerical reviewer.

### U — PRODUCT / UI

task_id: U-149

title: Integrated AI + Engineering operator environment

product outcome: Human-usable process/dynamics/studies/geometry/physics/results workflows over real backend capabilities, preserving 144 usability standards.

canonical spec/readiness identity: 149.

exact prerequisite/base SHA: exact master containing merged 146,147,148,107,108,109,110.

dependencies: 144,146,147,148,107,108,109,110.

existing owners/interfaces to reuse: application shell, Jarvis sidecar, Properties, Runs, Lineage, Analysis Dock, Process scaffold, BLUECAD workbench, Settings, API client/codegen, exact-head browser proof.

allowed write scope: frontend operator surfaces and contract-generated client changes; only minimal backend projection adapters when an existing owner lacks a read projection and the relevant owner approves.

forbidden/conflicting scope: frontend direct provider/Ollama/filesystem/tool calls, React-owned engineering state, hidden canonical stores, redesign of backend semantics to make UI easier, fake enabled controls.

shared contracts consumed: all stable H/L/R/engineering read/control/evidence contracts.

implementation requirements: coherent flowsheet/process/dynamics/studies/geometry/physics/results navigation; truthful availability and qualification states; source/evidence drill-down; progressive disclosure; safe interruption/recovery controls; resource/model state visible where operationally relevant.

non-goals: decorative digital twin without real backing, duplicate engineering data editor, UI-side solver orchestration.

deterministic tests: generated contract drift, accessibility/interactions, hostile/stale payloads, no-direct-authority guards.

runtime/browser/hardware/solver evidence: exact-head real Chromium task smokes against real local backend; representative end-to-end process→study→CAD/CAE→results flow; unavailable solver/model states rendered truthfully.

scientific qualification requirement: UI must distinguish candidate/calibrated/benchmarked/qualified and show validity limits; never collapse “solver ran” into “physics validated”.

stop condition: an operator can configure, run, inspect, compare and trace a BlueRev engineering study without reading raw backend internals or bypassing Jarvis authority.

expected handoff: browser-proof artifacts, task matrix, screenshots only as supplemental evidence, backend capability gaps discovered.

safe parallel peers: none for the same final surfaces; targeted read-only review may run in parallel.

required realtime coordination: with all backend owners for contract mismatches; no UI-local workaround for authority gaps.

preferred worker capability: strong frontend/product coding agent plus browser/runtime verifier.

## 7. Safe parallel launch groups

Group 0 — governance:
- merge this planning/readiness PR only after maintainer authorization.

Group 1 — shared freeze:
- K0/145 only. Other builders may perform read-only preparation but no product mutation that depends on unfrozen shared contracts.

Group 2 — first real parallel wave after 145 merge:
- H/146;
- L/147;
- R/148;
- K1/102→106;
- P may perform bounded 103 qualification preparation, but implementation using shared engineering contracts waits for 102;
- no C runtime mutation until 106.

Group 3 — engineering parallel wave:
- P/103→104→105→107→108→109 follows its hard chain;
- C/014 starts after 106 and may run in parallel with P until the 109/110 integration boundary;
- H/L/R continue repair/evidence work on frozen heads.

Group 4 — integration:
- 110 with P+C coordination;
- 149 UI after backend prerequisites are merged.

## 8. Agent Relay topology

Agent Relay is development infrastructure only.

- one maintainer coordinator owns GitHub/shared-authority mutation at a time;
- one K shared-writer lane during contract/migration freeze;
- isolated H/L/R/P/C/U branches/worktrees after their dependencies are merged;
- realtime channels: foundation-contracts, ai-runtime, retrieval, engineering-interface, product-integration;
- Relay messages carry coordination and ephemeral evidence pointers only; GitHub commits/PRs/exact SHAs remain durable authority;
- no worker edits another worker's owned files without explicit handoff;
- shared-contract change requests go to K, not via opportunistic cross-branch edits.

Cheap/free workers are suitable for: fixture/corpus construction, targeted upstream doc/license checks, benchmark data normalization, deterministic test enumeration, browser smoke execution when tooling is reliable.

Stronger coding agents are required for: K contracts/migrations, H worker/inference governance, L reservation/routing concurrency, process dynamics, solver adapters, final UI integration.

Independent scientific/numerical review is mandatory for 107 and high-fidelity 110 claims. Adversarial security/authority review is mandatory for 146/147.

## 9. Cross-review and integration strategy

- K ↔ H/L/R: contract consumer review before K frozen head merges.
- H ↔ L: inference/resource/cancellation paths.
- R ↔ H: Hermes operational memory/session search adapter.
- P ↔ C: ProcessDesignEnvelope, geometry/physics feedback and validity envelopes.
- P/C ↔ U: truthfulness of availability, qualification and failure states.
- independent adversarial reviewer: H/L authority bypass and resource races.
- independent scientific reviewer: P/107 and C/110.
- browser verifier: U/149 and any H control surface exposed to the operator.

Reviews must target frozen exact heads. Do not rerun unrelated evidence after changes that cannot affect it.

## 10. Astra return checkpoints

CHECKPOINT A — AI runtime integration
Entry: 145,146,147,148 merged; Windows/WSL runnable; real session, retrieval, local inference/routing and resource evidence available.
Astra task: inspect runnable integration, attack authority/isolation/context/resource failure modes, and directly repair material defects.

CHECKPOINT B — process/dynamics/scientific architecture
Entry: 102-108 sufficient to run representative dynamic BlueRev scenarios with explicit scientific qualification ledger.
Astra task: inspect equations/units/dynamics/solver role boundaries/qualification evidence, challenge false validity, repair integration defects.

CHECKPOINT C — multiphysics + product finish
Entry: 109,110,149 candidate exact heads integrated on Windows/WSL/browser with real solver/model availability evidence.
Astra task: run end-to-end product, inspect process↔CAD↔CFD/FEM feedback, browser usability and recovery, directly repair final blockers.

Do not spend Astra on ordinary adapters, CRUD, routine tests or mechanical review.

## 11. Stop boundary

This planning change stops before bulk implementation.

The only action that may follow immediately after merge is K0/145. Every later builder must verify fresh STATUS, exact master SHA, hard dependencies and its allowed scope before mutation.
