# JarvisOS Architecture Reconciliation — 2026-08-21

Status: **PLANNING / RECONCILIATION — `docs/specs/STATUS.md` REMAINS LIVE AUTHORITY**

Base inspected: `master` at `ad3ce781195d465c5db4f32168b13874ac9089f8` after README PR #324.

Active runtime front observed: PR #319, `Implement SCENE-SEMANTICS-A1`.

This reconciliation is intentionally documentation-first. It must not create a second runtime implementation front while 058c is active.

---

## 1. Why this reconciliation exists

A README/architecture audit was performed from the perspective of an external software developer with no prior JarvisOS context, followed by a code audit asking whether the implementation actually supports the public architecture claims.

The audit found three classes of problems:

1. **diagram/dataflow errors** — missing return arrows, authority represented as a one-way pipeline, Hermes shown too close to canonical state, optimizer feedback represented incorrectly;
2. **documentation drift / overclaim** — `docs/ARCHITECTURE.md` described earlier architecture as current, evidence/engineering contracts looked more universal than the implementation, CAD was credited with physical-synthesis capabilities not yet implemented;
3. **real architecture debt** — overlapping canonical-state write semantics, ambiguous Parameter lifecycle/value-quality semantics, a custom acyclic process kernel that is not a suitable final PBR process solver, a process/dependency “flowsheet” naming collision, and obsolete placeholder engineering code.

The public README and canonical architecture diagrams are corrected in the same documentation branch as this file.

---

## 2. Governing rule: zero sunk-cost privilege

Effective planning rule:

> **Current JarvisOS code has zero sunk-cost privilege.**

For every subsystem, the decision question is:

> If JarvisOS did not contain this code today, would we still choose to build and own it after comparing current upstream projects, licenses, interfaces, tests, maintenance burden and engineering requirements?

If the answer is no, the preferred dispositions are:

- `REPLACE_WITH_UPSTREAM`;
- `WRAP_UPSTREAM`;
- `DELETE`;
- `PARK` only when the evidence is not yet sufficient.

`KEEP_JARVIS` is earned by present architectural value, not historical effort.

This is especially important for numerical/process infrastructure. JarvisOS should own state, evidence, orchestration and engineering contracts; it should not become a general process-solver vendor by accident.

---

## 3. Immediate documentation corrections

The following are corrected directly rather than queued as runtime work:

### 3.1 High-level architecture

Correct relationship:

```text
Engineer ⇄ JarvisOS ⇄ AI / AgentRuntime
             │
             ↓
      engineering capability
             │
             ↓
      result / evidence
             └────────→ JarvisOS
```

No AI/agent/tool path may terminate without an explicit return path.

### 3.2 AI authority

Correct relationship:

```text
bounded context → AI/agent → response/proposal/ToolIntent
                              ↓
                        JarvisOS policy
                              ↓
                         tool execution
                              ↓
                        run / evidence
                              ↓
                    commit/promotion gate
                              ↓
                        canonical state
```

The human remains the final engineering authority. JarvisOS owns the software transition boundary.

### 3.3 Context/memory

Canonical state, evidence, external documents, derived retrieval and code intelligence are parallel context sources. They feed a Context Broker. They are not a serial `state → evidence → retrieval → code intelligence` chain.

MCP is an optional capability/resource interface, not the conceptual owner of external documents.

### 3.4 Engineering backends

The diagram now describes replaceable **EngineeringEvaluator** backends. It no longer implies one already-implemented universal backend interface.

### 3.5 PBR design loop

The optimizer receives every evaluation result directly. Jarvis is outside the tight per-candidate numerical loop.

Correct target:

```text
Engineer ⇄ Jarvis ⇄ DesignStudy ⇄ StudyController
                                 ⇅
                           DOE / optimizer
                                 ⇅
                        EngineeringEvaluator
                                 ⇅
                       EvaluationResult/evidence
```

### 3.6 CAD/FEM feedback

The existing BLUECAD structural repair loop is shown explicitly: failed criteria may provide attempt-scoped evidence to a bounded repair proposal, which rebuilds/resimulates without silently replacing the valid candidate.

---

## 4. Code findings that require runtime/spec work

### P0-A — canonical write semantics are duplicated

Current:

- `app/modules/memory` implements proposed/accepted/rejected/superseded lifecycle and promotion semantics;
- older `app/modules/modeling` CRUD paths can create engineering records directly.

The problem is not that a human may create an accepted value. The problem is that there are multiple write semantics and transition paths.

Target: one canonical-state service accepting typed intents from user, AI, calculations and imports, with consistent provenance, lifecycle and audit semantics.

### P0-B — Parameter lifecycle and value quality are ambiguous

Current Parameter semantics mix:

- record lifecycle (`proposed`, `accepted`, `rejected`, `superseded`);
- value/evidence quality (`candidate`, `literature`, `measured`, `validated`, `accepted`).

The context selector currently has paths based on value-quality state. A proposed record must never become authoritative context solely because its value-quality field says `accepted` or `validated`.

Target:

```text
include as authoritative context only when
record lifecycle == accepted
AND value/evidence quality is allowed for that context
```

Rename the value-quality field if necessary to remove the duplicate `accepted` semantic.

### P0-C — custom process kernel is not the target PBR solver

`app/modules/process_kernel` validates an acyclic typed graph and executes it in topological order.

That is a legitimate feed-forward experiment but not a sufficient basis for a serious PBR process model requiring some combination of recycle/algebraic loops, nonlinear equations, ODE/DAE integration, state/control coupling and optimization.

**No new generic solver features should be added to this kernel before the upstream bake-off.**

### P0-D — old canonical architecture was stale

`docs/ARCHITECTURE.md` previously claimed that memory runtime/schema did not yet exist and retained earlier local-model/Workbench/Foundry planning as current architecture. It is replaced by the current architecture in this reconciliation.

---

## 5. Process upstream bake-off

The process stack must be re-evaluated from zero before PBR implementation.

High-priority families include:

- IDAES / Pyomo / WaterTAP;
- BioSTEAM / QSDsan;
- CasADi / OpenMDAO;
- DWSIM / CAPE-OPEN where relevant;
- CoolProp / thermo / chemicals / fluids;
- additional maintained upstreams discovered during the fresh audit.

Evaluation dimensions:

- support for algebraic loops/recycles;
- equation-oriented modeling;
- ODE/DAE/dynamic support;
- nonlinear optimization and derivatives;
- property/model extensibility;
- units and semantic contracts;
- deterministic/reproducible execution;
- diagnostics/failure states;
- licensing and redistribution boundaries;
- Windows/local deployment fit;
- Python integration cost;
- scientific validation/community maturity;
- ability to preserve JarvisOS-owned run/evidence/state boundaries.

The current 047/048/049/072/075 calculations become **reference fixtures and incumbent competitors**, not privileged architecture.

Possible outcomes:

- keep selected domain equations as tests or small adapters;
- port domain equations into the chosen upstream framework;
- delete custom generic stream/flowsheet/unit-operation infrastructure;
- retain a tiny custom screening evaluator only if it is demonstrably simpler/stronger for a bounded use case;
- do not maintain two general process engines merely to preserve old code.

---

## 6. Evidence contract correction

Current typed `evidence_records` are strongest for validation, mesh and static FEM.

Future engineering evidence must be able to express at least:

- evaluator/tool/model identity + version;
- exact input/run/result/artifact digests;
- units;
- model fidelity;
- validity domain;
- qualification status;
- known exclusions;
- uncertainty/sensitivity where relevant;
- provenance;
- freshness;
- typed failure/outcome state.

A deterministic and traceable screening model is not automatically scientifically valid.

---

## 7. Naming and dead-code cleanup

### Dependency “flowsheet”

`app/modules/flowsheet` is a dependency/provenance/freshness graph, not a chemical-process flowsheet. The name collides with `app/modules/process_kernel/flowsheet.py` and with standard engineering terminology.

Post-visual-identity cleanup should rename it toward `lineage`, `dependency_graph` or `provenance_graph`, with migration/import compatibility where necessary.

### `app/modules/engineering`

The module is still largely a placeholder-era abstraction and is not the current integrated engineering runtime boundary.

Zero-sunk-cost disposition:

- delete if it has no production consumers; or
- rebuild it only if the future common evaluator contract genuinely needs one shared engineering module.

Do not keep it because the directory name looks architecturally desirable.

---

## 8. PBR target architecture

### 8.1 Process evaluator before detailed CAD

Tube diameter, active length, loop count and topology are first-class process-design variables even before detailed CAD exists.

Introduce a typed abstract handoff concept such as `ProcessDesignEnvelope` rather than forcing process design to generate a full `GeometrySpec` too early.

### 8.2 Inner and outer loops

Outer loop:

- human goals and engineering responsibility;
- Jarvis context, explanation, model selection, study definition and intervention.

Inner loop:

- deterministic/reproducible StudyController;
- DOE/optimizer/search;
- EngineeringEvaluator calls;
- explicit failure taxonomy;
- persisted study/evaluation evidence.

### 8.3 Multi-fidelity

CFD is not intrinsically a final CAD verification step. It may be invoked as a higher-fidelity study evaluator when mixing, shear, gas transfer, baffle behavior or another field quantity materially changes the process design.

Use the cheapest evaluator that resolves the decision.

---

## 9. Post-visual-identity implementation queue

The current functional operator-workstation queue remains first. Runtime architecture remediation begins only after the global visual identity checkpoint, unless a security/correctness defect requires an emergency interrupt.

The planned sequence registered in `docs/specs/STATUS.md` is:

1. **100 VISUAL-IDENTITY-1** — apply the independently removable global visual identity after the current functional beta queue.
2. **101 CANONICAL-STATE-WRITE-1** — unify modeling/memory write semantics and correct Parameter lifecycle versus value-quality authority.
3. **102 ENGINEERING-EVIDENCE-CONTRACT-1** — common evaluator/evidence metadata for fidelity, validity and qualification without erasing solver-specific semantics.
4. **103 PROCESS-UPSTREAM-BAKEOFF-1** — exact current-code versus upstream audit with zero sunk-cost privilege and an explicit keep/wrap/replace/delete decision.
5. **104 PROCESS-STACK-STRANGLER-1** — execute the 103 decision: migrate needed domain behavior and delete duplicated generic custom process infrastructure instead of maintaining parallel solvers.
6. **105 ENGINEERING-DOMAIN-CLEANUP-1** — remove/rebuild the obsolete engineering placeholder boundary and resolve the process-flowsheet versus lineage-graph naming collision.
7. **106 ENGINEERING-EVALUATOR-1** — establish the common typed evaluator/result boundary required by future process, CFD, CAD/CAE and commercial adapters.
8. **107 PBR-EVALUATOR-1** — build the integrated PBR evaluator on the selected process/dynamic upstream stack plus only necessary domain-specific equations.
9. **108 DESIGN-STUDY-CONTROLLER-1** — deterministic StudyController/DOE/optimizer inner loop with failure taxonomy and Jarvis in the outer loop.
10. **109 PROCESS-CAD-HANDOFF-1** — typed ProcessDesignEnvelope → detailed CAD realization plus explicit physical-verification feedback.
11. **110 MULTIFIDELITY-ENGINEERING-1** — decision-driven escalation across reduced-order models, CFD/FEM/specialist tools and qualification evidence.

Every row remains `planned` until the normal kernel/full-spec/readiness ladder authorizes it. This file does not authorize runtime work.

---

## 10. Existing specs affected by interpretation

The following merged work remains historical evidence and can continue to support current beta behavior, but receives no sunk-cost preference for future process architecture:

- 047, 048, 049 process/screening models;
- 072 explicit topology experiment;
- 075 custom process kernel.

Spec 078 PBR-MODELING-0 remains planning evidence only. Before implementation, it must be freshly re-derived against the 103 upstream bake-off and 106 evaluator contract rather than assuming that the current custom process kernel is the target runtime.

Spec 093 BLUEREV-SERIAL-TOPOLOGY-0 should also be re-evaluated after the process-design abstraction is established; topology must not become detailed-CAD authority prematurely.

Specs 066–068 remain frozen until their existing registry freeze is explicitly lifted after fresh revalidation.

---

## 11. Deletion policy during replatforming

When a replacement slice proves that an upstream path satisfies the required contract and exact regression/engineering checks:

1. migrate the needed tests/fixtures/domain equations;
2. switch production callers to the selected adapter;
3. remove the old generic implementation and dead compatibility code;
4. retain historical specs/PRs as history, not live code;
5. do not keep a second solver path merely as emotional insurance.

Rollback should be provided by Git history and reproducible fixtures, not permanent duplicated architecture.

---

## 12. Success criterion

This reconciliation is successful when a skeptical external engineer can trace the same architecture through:

```text
README
→ diagrams
→ docs/ARCHITECTURE.md
→ docs/specs/STATUS.md
→ source code
→ tests/evidence
```

without finding contradictory authority arrows, a planned feature colored as implemented, a screening model described as a general solver, or an internal subsystem retained only because it already exists.
