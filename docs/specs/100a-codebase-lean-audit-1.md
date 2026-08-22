# 100a — CODEBASE-LEAN-AUDIT-1

Definition status: **complete planning boundary; implementation requires fresh readiness from exact post-100 master**  
Depends on runtime authority: 100

## 1. Purpose

Audit the complete first-party JarvisOS codebase after the functional beta and global visual identity, before the post-beta authority/process replatforming work begins.

The objective is not a cosmetic refactor and not a literal line-count contest. The objective is to minimize **active semantic surface at equal or better product behavior** so that future AI coding/review agents have fewer files, concepts, duplicate boundaries, historical residues and ambiguous paths to inspect.

The audit must distinguish four different questions that are often collapsed incorrectly:

1. Is this code reached today?
2. Is the capability still desired?
3. Is this implementation the best boundary for that capability?
4. Does it matter to runtime performance?

A negative answer to question 1 is **not** deletion authority. In particular, a backend capability with no current frontend caller may be a desired capability that should be wired later rather than removed.

## 2. Governing principles

### 2.1 Minimum semantic surface

Optimize for the smallest sufficient implementation, not pedagogical architecture and not code golf.

Prefer direct functions/modules over class/factory/facade/manager chains when the extra boundary does not enforce a real policy, authority, transaction, security, scientific contract, replacement seam or independently useful abstraction.

Do not split cohesive code merely to make files shorter. One direct 250-line module can be better than eight 40-line modules connected by ceremony.

### 2.2 Zero sunk-cost privilege

Existing JarvisOS code receives no preference because it already exists. A generic in-house subsystem may be retained, wrapped, reduced to domain fixtures, replaced by an upstream or deleted when current evidence supports that decision.

### 2.3 Unwired is not dead

Absence of a current runtime/frontend consumer is evidence of missing reachability, not evidence that a capability is unwanted.

Before any `DELETE` recommendation, product intent must be established from current authority and evidence. Desired-but-unwired functionality is classified `WIRE` or `DEFER`, never `DELETE` merely because a caller is absent.

### 2.4 Performance is measured separately

Fewer source lines can reduce maintenance/AI-review cost but do not prove faster runtime. Runtime optimization requires profiling. I/O, provider latency, SQLite/filesystem work, CAD kernels and external solvers must be distinguished from first-party CPU cost before low-level optimization is proposed.

## 3. Scope

Audit all first-party executable/product surfaces present on the exact implementation base, including at minimum:

- `backend/app/**`;
- `frontend/src/**`;
- `backend/tests/**` and frontend tests as ownership/behavior evidence;
- `scripts/**`;
- `.github/workflows/**`;
- launchers and first-party configuration that participate in product/development execution;
- schemas, storage/migration logic, route surfaces, provider/routing code, AI/context/memory code, runner code, engineering/CAD/CAE/process code, frontend API clients/hooks/components and repository-development automation.

Exclude generated/vendor/runtime data such as `.venv`, `node_modules`, build outputs, caches, persisted JarvisOS data and historical report artifacts unless they reveal an active ownership problem.

Documentation/spec history is evidence for intent and provenance, not source LOC targeted for cleanup by this slice.

## 4. Authority for product intent

For each suspicious or apparently unreachable capability, determine intent before recommending removal.

Use, in descending authority for current product intent:

1. `docs/specs/STATUS.md` and merged/accepted current specifications/readiness decisions;
2. `docs/ARCHITECTURE.md` and accepted architectural decisions;
3. current observable product/runtime behavior and active API/UI contracts;
4. current tests and callers as implementation evidence;
5. historical/cancelled/superseded specs only as provenance or evidence of why code may exist.

Historical existence alone does not preserve code. Current lack of a caller alone does not delete code.

If intent remains ambiguous after this trace, classify the item `UNKNOWN` and leave it untouched.

## 5. Required classification

Every audited component receives exactly one primary disposition plus evidence/confidence:

- `KEEP` — necessary and already sufficiently direct;
- `SIMPLIFY` — necessary but contains avoidable LOC/branching/indirection;
- `MERGE` — separate modules/layers should become one cohesive boundary;
- `INLINE` — wrapper/facade/helper adds no meaningful policy or reuse;
- `WIRE` — desired capability exists but is not yet connected to the product surface that should consume it;
- `DEFER` — desired capability is intentionally not active in the current product/queue;
- `REPLACE_UPSTREAM` — behavior remains desired but custom generic implementation lacks justification against a stronger upstream;
- `STRANGLE` — currently consumed but should disappear after callers migrate to an identified replacement;
- `REFERENCE_ONLY` — runtime implementation should not survive, but equations, fixtures, tests, examples or scientific evidence remain valuable;
- `DELETE_CANDIDATE` — apparently unnecessary, pending the deletion gate;
- `DELETE` — deletion gate fully satisfied;
- `PROFILE` — runtime-cost suspicion requiring measurement before optimization;
- `UNKNOWN` — insufficient evidence; no mutation authorized.

A component may carry secondary notes such as security-critical, authority-boundary, migration-boundary, scientific-fixture or UI-wiring-gap.

## 6. Deletion gate

A runtime/source component may be classified `DELETE` only when the audit establishes all of the following:

1. no relevant current runtime, UI, API, workflow, script or supported external consumer requires it;
2. the capability is not desired by the current product architecture/queue, **or** its desired behavior is already covered by an identified replacement;
3. it is not required by a current or future registered specification except as historical evidence;
4. it is not a necessary authority, security, migration, provenance, compatibility or transaction boundary;
5. any useful equations, scientific fixtures, golden cases, conformance tests or domain knowledge have an explicit preservation destination;
6. it is not simply a desired backend capability awaiting frontend/product wiring;
7. if behavior remains desired, replacement reachability and migration path are concrete rather than hypothetical.

Failure or uncertainty on any item means `DELETE` is forbidden. Use `WIRE`, `DEFER`, `STRANGLE`, `REFERENCE_ONLY`, `DELETE_CANDIDATE` or `UNKNOWN` instead.

## 7. Audit dimensions

The audit must inspect at least:

### 7.1 Reachability and ownership

- application/router registration and import reachability;
- frontend API/client/hook/component consumers;
- CLI/script/workflow consumers;
- test-only consumers versus product consumers;
- duplicated entry points for the same authority;
- desired backend functionality not yet exposed in the frontend.

### 7.2 Complexity and indirection

- pass-through services/facades/managers;
- one-consumer abstractions;
- unnecessary class hierarchies/factories/registries;
- excessive call depth;
- compatibility shims without real consumers;
- repetitive error/validation/serialization layers;
- large conditional surfaces whose branches are obsolete.

### 7.3 Duplication and schema churn

- near-identical DTO/Pydantic/TypeScript types;
- repeated JSON → model → dict → model transformations;
- duplicate constants/enums/status vocabularies;
- duplicate repository/storage helpers;
- backend/frontend models that can share a simpler authoritative contract without coupling forbidden layers.

### 7.4 Historical residue

- code belonging only to cancelled/superseded features;
- old review/autonomous-development paths no longer authorized;
- obsolete compatibility behavior;
- placeholder modules and skeleton registries;
- previous experimental engines that current architecture already intends to replace or re-evaluate.

### 7.5 Tests

Distinguish tests that protect externally meaningful behavior/invariants from tests that merely freeze obsolete implementation structure. Do not delete a behavior contract because its only current consumer is a test; first establish whether that test represents desired product/scientific/security behavior.

### 7.6 Upstream replacement

Identify generic custom infrastructure whose main value is already supplied by current/queued upstream candidates. Route domain-specific process replacement decisions to 103/104 rather than pre-empting that bake-off.

### 7.7 Runtime performance

Profile only representative offline/local paths that can be measured safely without provider spend or new credentials. Separate wall time into first-party CPU work, database/filesystem/serialization, CAD/native kernels, external solver work and waiting/network/model time where applicable.

A suspected hotspot without measurement remains `PROFILE`; this audit does not authorize a language rewrite based on intuition.

## 8. Quantitative baseline

Record the exact audited master SHA and a reproducible baseline using repository-native or standard-library tooling where practical:

- tracked first-party source LOC by major area/language;
- tracked file/module count by major area;
- backend route count and route ownership;
- frontend API/client surface count;
- workflow/script count;
- obvious module dependency/fan-in/fan-out hotspots;
- selected complexity/duplication indicators that materially aid the decisions.

Do not add a permanent analysis framework or dependency merely to collect metrics. Temporary local scripts are preferred unless a small reusable checker has clear future value.

No arbitrary percentage reduction target is allowed. A lower LOC count is useful only when behavior and important boundaries are preserved.

## 9. Required deliverable

Commit one audit artifact under `docs/audits/` named with spec ID and the audited short SHA, for example:

`docs/audits/100a-codebase-lean-audit-<shortsha>.md`

The artifact must include:

1. exact audited SHA and baseline metrics;
2. coverage statement for every first-party source area in section 3;
3. component inventory with disposition, evidence, confidence and owning capability/spec;
4. a separate **desired-but-unwired capability register** (`WIRE`/relevant `DEFER` findings);
5. a separate removal/simplification register ranked by expected ROI and risk;
6. all `DELETE` candidates with explicit deletion-gate evidence;
7. performance/profile findings with measured versus unmeasured claims separated;
8. mapping of findings that belong to later 101, 103, 104, 105 or other existing specs rather than 100b;
9. a proposed bounded candidate set for fresh 100b derivation.

The audit document is evidence, not a second live roadmap. `STATUS.md` remains the queue authority.

## 10. Non-goals

This spec does **not** authorize:

- deletion, rewiring or runtime refactoring merely because the audit discovers it;
- feature implementation, including wiring backend capabilities to the frontend;
- changing API/schema/database semantics;
- pre-empting 101 canonical-write remediation;
- pre-empting 103/104 process-upstream selection/strangling;
- pre-empting 105 engineering-domain cleanup;
- changing visual identity;
- new frameworks, static-analysis services, paid tooling, provider calls, credentials or durable stores;
- rewriting Python/TypeScript in C/C++/Rust or another language without measured hotspot evidence and a separately authorized implementation boundary.

## 11. Acceptance criteria

1. Audit is run from exact post-100 master and records that SHA.
2. Every first-party source area in section 3 is covered; no major executable area is omitted because it looks unrelated.
3. Every audited component has one primary disposition from section 5, evidence, confidence and owner/capability mapping.
4. Every apparently unused backend/API capability is checked for desired product intent before any deletion recommendation.
5. Desired-but-unwired capabilities are listed separately and cannot appear in the deletion list solely because a frontend/client caller is absent.
6. Every `DELETE` recommendation satisfies all seven deletion-gate conditions explicitly.
7. Historical/cancelled code, generic custom infrastructure, duplicate boundaries, pass-through layers and test-only paths are examined rather than assumed safe.
8. Baseline semantic-surface metrics are reproducible without adding a broad permanent analysis framework.
9. Runtime-performance claims are backed by measurement or labelled `PROFILE`/unmeasured.
10. No product/runtime behavior changes in the audit implementation PR beyond documentation/audit tooling strictly necessary to produce the evidence.
11. The artifact proposes a bounded high-confidence 100b candidate set and routes domain-specific findings to their correct later specs.
12. Normal exact-head deterministic gates remain green.

## 12. Minimum-necessary test

Criterion: obtain enough evidence to reduce JarvisOS semantic surface safely before the post-beta architecture work.  
Is this work necessary? **Yes.** The repository has accumulated many sequential implementation generations, cancelled/superseded features and experimental boundaries; simplifying after rather than before 101–110 would make those later changes reason over avoidable historical surface.  
Can the criterion be achieved by deleting all currently unreachable code automatically? **No.** That would confuse missing reachability with unwanted product intent and can destroy desired backend capabilities that simply have not been wired to the frontend yet.  
Why not add a permanent analysis platform? The audit can use repository inspection and lightweight reproducible scripts; infrastructure is justified only if 100a itself demonstrates repeated value.

## 13. Definition of done

- exact post-100 master audited;
- required artifact committed;
- coverage, classification and deletion-gate acceptance criteria satisfied;
- no runtime cleanup smuggled into the audit;
- exact-head deterministic gates green;
- registry reconciled after merge;
- 100b is freshly re-derived from the audit evidence before receiving readiness or implementation authority.
