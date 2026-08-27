# Final product specification-promotion contract — 2026-08-27

Status: maintainer-approved specification-quality contract for the final operator-product packet; **not** runtime implementation authority and **not** a parallel queue.

## 1. Purpose

Define the minimum information that `100c FINAL-PRODUCT-DIRECTION-AUTHORITY-0` and every later promoted canonical specification must contain before a builder is allowed to implement one of the final operator-product capabilities.

The purpose is not to preselect APIs, database tables, components, libraries or service boundaries before exact-master audit. The purpose is to remove a different source of ambiguity: a future builder must not receive a vague requirement such as “implement Roadmap”, “make the HTML functional”, or “add Repository Inspector” and fill in the missing semantics from personal judgement.

The product behavior is already frozen by the canonical preservation packet. Exact implementation ownership is derived later from exact repository evidence.

## 2. Required source packet

Every full specification promoted from FV-B01..FV-B23, FV-F01..FV-F15, or a merged successor must cite the exact revisions of the sources it implements:

1. `docs/design-references/APPROVED_OPERATOR_UI_MANIFEST_2026-08-27.md`;
2. the applicable canonical HTML file(s), including manifest SHA-256 and Git blob identity;
3. `docs/design-references/FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md`;
4. the most-specific approved surface reference document;
5. `docs/design-references/FRONTEND_CONFORMANCE_CONTRACT_2026-08-27.md` for user-facing work;
6. PD-08 and the relevant PD-03/PD-04/PD-05/PD-07 contract;
7. every applicable row of `docs/spec-drafts/FINAL_OPERATOR_CAPABILITY_MATRIX_2026-08-27.md`;
8. every applicable FV pseudo-spec in `docs/spec-drafts/FINAL_VISUAL_IMPLEMENTATION_PACK_2026-08-27.md`;
9. the exact `100c` ownership/disposition output;
10. exact current code/ADR/spec/readiness owners discovered during definition.

A promoted spec is incomplete if it cites only the pseudo-spec name or only the HTML screenshot.

## 3. No-interpretation rule

A promoted spec must answer explicitly, rather than leave to the implementer:

- what exact user-visible capability is in scope;
- what exact capability is intentionally out of scope;
- which canonical state owner is authoritative;
- which existing records/tables/services are reused;
- whether a new state owner is genuinely required;
- which actions are `PRESENTATION`, `READ`, `CONTEXT`, `PROPOSE`, `COMMIT`, `EXECUTE`, or `NAVIGATE`;
- what exact preconditions authorize each non-presentation action;
- what exact mutation/result occurs;
- what exact stale-target/conflict rule applies;
- what evidence is returned;
- what loading/empty/unavailable/error states exist;
- which visible canonical controls remain disabled because another spec owns them;
- which security/egress/secret boundaries apply;
- how exact version/model/repository/runtime identity is represented;
- what deterministic tests prove the behavior;
- what browser states prove frontend fidelity;
- what rollback/recovery behavior applies to mutations or execution;
- what later spec owns every deferred approved behavior.

If a required answer cannot yet be derived from exact repository evidence, the spec remains definition/readiness work. The builder does not decide the missing answer during implementation.

## 4. Canonical action table requirement

Every user-facing promoted spec must contain an action table with one row per visible or otherwise operator-triggerable action owned by that slice.

Minimum columns:

| Field | Required meaning |
| --- | --- |
| `Surface/control` | canonical surface and human-visible control/gesture |
| `Action class` | one of the seven classes in the final interaction contract |
| `Exact target identity` | record/version/ref/path/run/session that the action operates on |
| `Precondition` | deterministic/user/policy conditions required |
| `Backend owner` | exact accepted service/domain owner or `REFERENCE_ONLY` |
| `Mutation/execution` | exact allowed effect; `none` for presentation/read/navigation |
| `Success evidence` | exact returned/persisted evidence |
| `Failure/conflict` | deterministic failure state and stale-target behavior |
| `Frontend result` | exact approved visible state transition |
| `Deferred owner` | canonical later spec if only unavailable state is delivered now |

A spec may group controls only if their semantics, authority and failure behavior are genuinely identical.

## 5. Backend/domain full-spec requirements

A retained backend/domain capability spec must define the following before readiness.

### 5.1 Problem and ownership

- exact capability/problem;
- existing canonical owners audited;
- overlap disposition from 100c;
- one final write owner;
- read projections and consumers;
- proof that no second truth store is introduced.

### 5.2 Domain identity and invariants

Define stable identity for every new/extended domain object and all invariants that determine correctness.

Examples of identity dimensions that must be explicit when applicable:

- project;
- model;
- reconciled model version;
- working revision/change set;
- Roadmap item;
- Calendar block;
- Brainstorm Raw/IDEA/revision;
- Literature source/document/claim/citation;
- repository/ref/blob/PR/exact head;
- local runtime installation/executed SHA;
- terminal session;
- provider/integration identity.

Human display labels such as `v13.01`, short SHAs, filenames or titles are never a substitute for exact backend identity.

### 5.3 State machine

For each mutable object, define:

- allowed states;
- legal transitions;
- actor/authority for each transition;
- deterministic guards;
- concurrency/stale-target behavior;
- idempotency/retry semantics where relevant;
- event/audit/provenance emitted;
- immutable history requirements.

Do not hide state changes inside generic CRUD.

### 5.4 Persistence and migration

State explicitly:

- reused table/store/record ownership;
- new schema only when minimum-necessary proof succeeds;
- migration/backfill strategy;
- uniqueness/foreign-key/provenance constraints;
- deletion/archive semantics;
- compatibility with existing records;
- rollback or forward-recovery behavior.

### 5.5 API/read-action contract

Only after ownership is resolved, define exact typed backend contracts:

- request/response schemas;
- IDs/revision/ref fields required to avoid stale mutation;
- validation;
- error classes/status semantics;
- pagination/filter/sort where needed;
- bounded preview/size limits where relevant;
- authentication/local-only constraints;
- no-secret response rules;
- deterministic evidence fields.

Do not use a generic `/action` endpoint when typed operations are semantically different.

### 5.6 AI/Jarvis boundary

Whenever Jarvis/model output participates:

- exact input context identities;
- sensitivity/egress policy;
- `run_ai_task`/accepted AI execution spine ownership when inference occurs;
- proposal schema;
- deterministic validation/promotion boundary;
- audit ledger;
- stale proposal invalidation;
- prohibition on direct canonical mutation from model prose.

### 5.7 Failure-mode matrix

Every backend spec must enumerate material failures before implementation.

At minimum consider, when applicable:

- missing/not-found identity;
- stale version/ref/head;
- concurrent mutation;
- invalid transition;
- deterministic criterion failure;
- required recomputation unavailable;
- GitHub/network unavailable;
- file unsupported/too large;
- provider unavailable/auth failed;
- secret redaction/isolation failure;
- local runtime identity unknown;
- dirty worktree;
- migration/build/smoke/restart/health failure;
- PTY spawn/interrupt/session failure;
- rollback failure.

The spec must define the truthful resulting state, not merely “show an error”.

### 5.8 Deterministic acceptance tests

Acceptance must name exact tests proving:

- domain invariants;
- legal and illegal transitions;
- stale/concurrent behavior;
- persistence/provenance;
- no-fake/no-secret rules;
- failure/rollback behavior;
- exact evidence binding.

LLM review is supplementary evidence, never the deterministic acceptance criterion for domain correctness.

## 6. Frontend full-spec requirements

A retained frontend spec must define the following before readiness.

### 6.1 Canonical reference identity

Record:

- canonical HTML repository path;
- manifest SHA-256;
- Git blob;
- reference viewport;
- applicable shared-shell overlay;
- most-specific approved reference;
- exact interaction-contract sections.

A builder may not start from memory or from a screenshot.

### 6.2 Route and information architecture

Define:

- exact canonical route;
- peer navigation that is present;
- peer navigation that is forbidden/superseded;
- deep-link/legacy redirect behavior;
- selected-object/version/ref URL state when required;
- browser history/back-forward expectations.

### 6.3 Layout invariants

Define from the canonical HTML/reference:

- major regions and ordering;
- persistent vs contextual/collapsible regions;
- panel hierarchy;
- dominant/subordinate surfaces;
- bounded scrolling/virtualization behavior;
- right-side Jarvis/Properties rules where applicable;
- typography/icon roles;
- responsive behavior constraints.

Do not restate raw pixel values when the canonical HTML itself is the stronger authority; cite it and state the invariants a refactor must not break.

### 6.4 Data binding table

Every displayed non-static datum must have:

| UI datum | Backend source | Exact identity/freshness | Loading state | Empty/unknown state | Error state |
| --- | --- | --- | --- | --- | --- |

Fixture values in HTML are never valid production sources.

### 6.5 Interaction/state table

Use the canonical action table from section 4 for every owned control.

For presentation-only interactions, define local UI state explicitly so it cannot be confused with canonical domain state.

Examples:

- expanded/collapsed section IDs;
- active Timeline/Calendar view;
- selected Literature entries;
- Repository Inspector selected result;
- terminal tab selection.

### 6.6 Truthful deferral/unavailable state

If the canonical HTML contains a capability whose backend owner has not landed:

- preserve its composition if the active staged spec requires it;
- disable or mark unavailable/future truthfully;
- explain the reason without fake data;
- link the exact later owner in the spec;
- do not replace it with a different local-only behavior.

### 6.7 Accessibility and keyboard behavior

Define at least:

- focus order;
- keyboard activation for all controls;
- disclosure ARIA state;
- tabs/listbox/menu semantics where applicable;
- non-color status labels;
- focus preservation during inline expansion;
- terminal keyboard/interrupt separation when terminal is in scope.

### 6.8 Browser-proof matrix

A frontend PR must prove one exact head against the canonical viewport.

The spec must enumerate screenshots/browser states required, including:

- default/normal state;
- each major disclosure/modal/popover/tab owned;
- empty/loading/unavailable/error states that are in scope;
- selected/context state;
- proposal-before/after-accept state where owned;
- stale/conflict state where owned;
- responsive smoke state if required.

Evidence from a different head becomes stale after mutation.

## 7. Surface-specific mandatory questions

The following questions must be answered by the final owning specs, not by builders.

### 7.1 Process

- Which exact existing/future process-topology owner implements each approved add/connect/disconnect/edit action?
- Which visible controls remain unavailable until topology authority is reopened?
- Which selected-object Properties are editable and through which change authority?
- What exact input snapshot identifies Validate/Solve?
- How are solver/validation results bound to model/revision/run?

### 7.2 BLUECAD

- Which existing CAD/BLUECAD services own feature/object selection, properties and modifications?
- Which operations are viewer-only versus mutating?
- How are geometry/version/artifact identity and validation evidence preserved?
- Which technical-dock states come from real services?

### 7.3 Project Basis

- What exact records represent project-level basis versus model-version data?
- How is a bounded Jarvis batch identified?
- What exact transaction creates the working revision on `Approve all`?
- How are criterion-only changes re-evaluated immediately?
- What dependency evidence proves Process/BLUECAD recomputation is required?
- What exact action reconciles a working revision?

### 7.4 Models

- Which existing records project each dossier section?
- What exact selected model/version/revision owns every run/result/artifact/source?
- How are compact summaries computed?
- What pagination/virtualization boundary prevents unbounded dossier growth?

### 7.5 Literature

- How are existing `source_ref` records bridged to structured provenance without duplication?
- Which file types can preview safely?
- How is relevant PDF page/location selected?
- How are multiple inline expansions represented as presentation state?
- How does `Open file` preserve Memory route/context?

### 7.6 Roadmap

- What is the one canonical Roadmap item identity/store?
- How are dependencies, blockers, constraints and `Done when` evaluated?
- What makes `Ready` deterministically true?
- What does manual Add/Edit/Delete commit directly?
- What does Jarvis only propose?
- How do Timeline and embedded Execution status remain projections of the same item?

### 7.7 Calendar

- What is a Calendar block versus a Roadmap item?
- How are date/time/time-zone represented?
- How are zero/one/many Calendar blocks linked to one Roadmap item?
- How are create-from-cell/create-from-roadmap prefill semantics implemented without duplication?
- What real data backs effort metrics?
- What exact approval applies to Jarvis schedule proposals?

### 7.8 Brainstorm

- What is immutable Raw identity/content?
- What are legal Raw lineage states/transitions?
- What constitutes a Reconciled IDEA revision?
- How is variable-length discussion synthesis stored/provenanced?
- How are multiple explicit Jarvis context references represented?
- How does promotion create Roadmap/Design/Coding proposals without direct target mutation?
- How does future speech transcription enter the canonical AI execution/audit spine?

### 7.9 Settings

- What existing provider/credential/policy stores are canonical?
- How are provider API identity and Codex/Claude Code integration identity kept distinct?
- Which providers expose catalogue/cost/usage and how is unsupported capability represented?
- What is the exact secure credential update/test/disconnect boundary?
- Which orchestration controls are policy projections rather than model-routing authority?
- What real accounting backs budget/usage?
- Which System health states are observed versus unavailable?

### 7.10 Repository

- What exact GitHub/repository facade is used for repo/ref/PR/check/review truth?
- Which file types/paths/sizes are safe to inspect?
- How are exact ref/path/blob identities preserved through search/preview?
- What does `Add to Jarvis context` persist or reference?
- What proposal record does `Suggest modification` create?
- How does `Open on GitHub` generate an exact safe URL?
- How is active development lifecycle state projected without inventing authorization?

### 7.11 Runtime

- How is the actually executed local SHA observed independently from GitHub?
- How are local branch/path/dirty/service-health facts observed?
- How is aligned/local-behind/divergent/unknown derived?
- How are semantic deltas grounded in exact commits/files?
- What constitutes an approved update target?
- What exact dirty-state/migration/build/smoke/restart/health/rollback contract applies?

### 7.12 Integrated terminal

- What local auth boundary can create a terminal session?
- Which PTY/process adapter is used on Windows and in CI?
- Which environment variables/secret locations are scrubbed or denied?
- What secret-safe display/redaction boundary executes before frontend delivery?
- What path/cwd allow/deny policy exists?
- What constitutes high-risk/destructive command confirmation?
- How do stdin, Ctrl+C, resize, exit and reconnect/session loss behave?
- What bounded output can enter Jarvis context?
- What condition causes arbitrary PTY streaming to remain `DEFER_TRIGGERED`?

## 8. 100c promotion output

For every retained capability, 100c must emit or queue a canonical spec definition containing:

- final spec ID/name;
- exact dependency list;
- backend/frontend ownership;
- source packet;
- capability-matrix rows;
- interaction-contract sections/action classes;
- exact overlapping old specs/rows and their disposition;
- state owner/reused infrastructure;
- staged/deferred controls and their later owners;
- acceptance-test obligations;
- browser-proof obligations where user-facing.

100c may combine FV drafts when one real owner is smaller and safer. It may not combine them by deleting behavior.

## 9. Builder start gate

A builder is authorized to implement a final-product slice only after all are true:

1. live `STATUS.md` identifies that slice as the single implementation front;
2. a canonical full spec exists;
3. readiness explicitly says implementation is allowed;
4. all implementation-blocking questions from this contract are answered;
5. exact dependencies are merged/available;
6. canonical HTML/reference identities are recorded for frontend work;
7. no visible action is left with an unspecified action class/backend owner;
8. no required backend datum is sourced from fixture/frontend-only state;
9. deterministic tests/browser evidence are enumerated before coding begins.

If any item is false, the next work is definition/spec/readiness—not implementation by inference.

## 10. Definition of complete preservation

The final design-session work is considered mechanically preserved only when:

- every canonical surface exists byte-identically in the manifest;
- every approved user-visible behavior/state transition exists in the final interaction contract;
- every capability has a row in the capability matrix or an explicit reference-only statement;
- every required backend/frontend family exists in the pseudo-spec pack;
- every family is eventually given a single final owner/disposition by 100c;
- every promoted spec satisfies this promotion contract;
- every implementation proves the applicable canonical HTML and interaction states on one exact head.

This is the boundary between “the design is documented” and “a builder can implement it without inventing the missing contract”.
