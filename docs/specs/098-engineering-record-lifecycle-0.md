# 098 — ENGINEERING-RECORD-LIFECYCLE-0

Status: **definition-only; implementation not authorized**  
Date: 2026-08-22  
Derived from exact reconciled master: `c7613c4866821ffd6c2854f421cbf3beeb13b005`  
Depends on: 035, 040, 050, 051, 071b

## 1. Purpose

Add explicit server-owned lifecycle authority for canonical engineering records and expose it through the project-centric Engineering Data surface without creating a second record store, hiding destructive state only in the frontend, or collapsing distinct meanings into a generic `status` toggle.

The operator contract is:

```text
canonical engineering record
        ↓
server-owned lifecycle command
        ↓
validate workspace + kind + current state + references
        ├─ invalid / stale / unsafe → fail closed
        └─ valid
             ↓
      atomic lifecycle mutation
             ↓
 canonical list / lineage / context projections
             ↓
 Engineering Data refreshes from server truth
```

098 owns lifecycle semantics only. It does not own transient 071b working configuration, Jarvis working-state actions from 097, variants from 006b, comparison from 058b, or the broader canonical-write unification planned for 101.

A separate readiness decision derived from exact then-current runtime must choose the minimum per-record implementation seam and schema/API changes. This definition does not authorize guessed uniform CRUD across record kinds whose current contracts differ.

## 2. Exact-master runtime inventory

Fresh inspection of exact master shows a material lifecycle gap.

### 2.1 Engineering Data is read-only

`frontend/src/pages/EngineeringData.tsx` currently lists and inspects Model Specs, Assumptions, Parameters and Decisions. It has search, kind filters, workspace switching and exact Parameter source navigation, but no canonical record edit/lifecycle controls.

The page reads each record's persisted `status` as display data. It does not own lifecycle truth and must not implement archive/delete by client-side filtering or local-only flags.

### 2.2 Current modeling APIs are asymmetric

`backend/app/modules/modeling/routes.py` currently exposes create/list for Model Specs, Assumptions, Parameters and Decisions. Requirements additionally have get + patch. There is no current general update/delete/archive/supersede API for Assumptions, Parameters or Decisions.

`backend/app/modules/modeling/models.py` also proves that existing status vocabularies are not uniform:

- Assumption: `proposed | accepted | rejected | superseded`;
- Parameter: free-form `status` plus separate `value_status`, with `supersedes_parameter_id` and a rule that replacements are created as `proposed`;
- Requirement: `draft | active | retired` with an existing update model;
- Decision: free-form `status`;
- Model Spec: free-form `status` plus `maturity_status`.

Therefore 098 must not pretend these existing fields already implement one coherent lifecycle.

### 2.3 Existing lineage and promotion authority must remain intact

Specs 040/050/051 already own canonical proposal/promotion and dependency/staleness relationships. A lifecycle transition that affects visibility or operational use must preserve lineage and must not silently erase dependency evidence.

071b remains the sole transient working-configuration owner. Editing or retiring a canonical record must not silently overwrite an already-open working configuration.

## 3. Lifecycle vocabulary

098 freezes these operator-facing lifecycle meanings.

### Active

The record is eligible for normal current-model/project use under its existing domain rules.

`Active` does **not** mean scientifically validated, measured, fresh or accepted. Those are separate quality/provenance concepts.

### Inactive

The record remains legitimate and available but is deliberately not used in the current operational context.

Typical use: a valid alternative assumption/specification/parameter that should remain available without being treated as current authority.

### Superseded

The record is historical and has been replaced by a newer canonical record with explicit lineage.

Supersede must identify the replacement relationship. It is not equivalent to delete or archive.

### Archived

The record is legitimate historical/project information that is no longer operationally current. Archive preserves identity and lineage but removes the record from normal active views unless explicitly requested.

### Deleted

The operator has declared the record erroneous, duplicate or otherwise removed from normal product experience.

Deleted records disappear from ordinary Engineering Data and ordinary canonical context projections. When audit/lineage requirements require retention, deletion may be implemented server-side as a tombstone/soft-delete rather than physical row destruction.

`Deleted` is not a frontend-only hide flag.

## 4. Separate lifecycle from value/evidence quality

Lifecycle answers: **should this record participate in the current canonical project experience?**

It does not answer:

- is the numeric value measured, literature-derived, validated or accepted;
- is evidence fresh;
- is confidence high;
- is a proposal promoted;
- is a run successful;
- is a working override dirty.

For example, a Parameter may be lifecycle `Active` while its `value_status` remains `literature`; an archived record may still have high-quality historical evidence.

098 must not overload existing Parameter `value_status`, Assumption proposal status, Requirement state, or Model Spec maturity into the new lifecycle semantics without an explicit readiness mapping that preserves their existing meaning.

## 5. Canonical mutation authority

All lifecycle writes are server-owned.

The server must validate at least:

- record exists;
- record belongs to the requested/current workspace;
- record kind is supported by the transition;
- current lifecycle/precondition still matches when required;
- transition is legal;
- replacement/supersession target exists in the same authoritative domain when required;
- referential/dependency constraints are respected;
- the operation cannot silently corrupt canonical lineage.

The frontend may request an operation and render its result. It does not decide whether a transition is valid by local state alone.

Readiness must choose the smallest transition API shape. A generic command endpoint is not required if narrow existing per-kind routes are simpler and safer; conversely, duplicated per-kind lifecycle logic is not justified merely to preserve historical route layout.

## 6. Edit semantics

098 includes operator-visible canonical **Edit** only where readiness can prove a bounded current server contract for the record kind.

Canonical edit is distinct from 071b working-state edit:

- Properties / Jarvis 097 edit transient working configuration;
- Engineering Data edit mutates canonical record state.

The UI must label that distinction clearly enough that editing a project Parameter cannot be mistaken for changing only the current run configuration.

For fields with provenance, uncertainty, units, replacement relationships or downstream dependencies, server validation remains authoritative.

098 does not require a universal arbitrary JSON editor. Raw payload/schema internals remain Audit/technical surfaces.

## 7. Supersede semantics

Supersede is a two-record transition:

```text
old canonical record ──superseded by──> replacement canonical record
```

Required properties:

- old record remains addressable for lineage/audit;
- replacement identity is explicit;
- the relationship is workspace-safe and kind/domain-compatible;
- ordinary current views prefer the replacement;
- stale/dependency propagation continues to use canonical relationship authority rather than UI inference.

Existing `supersedes_parameter_id` is evidence of a Parameter replacement concept, but readiness must inspect exact service/schema behavior before reusing or generalizing it. This definition does not assume it is sufficient for all kinds.

## 8. Delete safety

Delete must be fail-closed.

Readiness must inspect actual references from flowsheet/dependency/evidence/run/proposal/canonical records and choose one of these outcomes per supported kind:

1. safe tombstone/soft-delete while preserving dependent lineage;
2. reject delete with a concrete dependency reason;
3. require an explicit replacement/supersede/archive action instead.

Physical cascade deletion of engineering evidence is not authorized by default.

A deleted record must not remain silently selectable as a normal canonical input merely because a legacy query forgot to filter it.

## 9. Normal view versus Audit

Engineering Data normal mode is project-centric and quiet.

Normal view:

- active/current records first;
- archived/superseded/deleted records excluded from ordinary results by default;
- lifecycle action names are human-readable;
- UUIDs and raw technical state remain secondary.

Advanced/Audit may expose:

- `Show archived`;
- `Show superseded`;
- `Show deleted`;
- exact record IDs;
- lifecycle timestamps/replacement IDs if authoritative;
- raw persisted status fields where needed for diagnosis.

No audit requirement forces deleted records back into the normal operator list.

## 10. Engineering Data action surface

For a selected supported canonical record, actions may include only those valid for its current state and server authority, for example:

```text
Edit
Deactivate / Activate
Archive
Supersede
Delete
```

The UI must not show every action for every kind/state if the backend cannot safely perform it.

Potentially destructive or semantically significant actions require an explicit confirmation that identifies the target and consequence. A transition response must come from server truth and the list/inspector must refresh from that response/current canonical reads.

Stale workspace/selection responses must not mutate a record in another workspace or leave the UI claiming a transition that the server rejected.

## 11. Context and downstream visibility

Lifecycle state must affect normal canonical projections consistently.

At minimum, readiness must inspect and test:

- Engineering Data listing;
- 042/context selection where canonical records are projected into AI context;
- 050/051 dependency and staleness views;
- any Parameter lookup used as source authority by 058c/071b;
- proposal/promotion surfaces from 040/054.

A deleted or archived record must not continue to enter normal authoritative context merely because one legacy query omits lifecycle filtering.

However, historical run/evidence provenance may still resolve the record for Audit/lineage.

## 12. Working-configuration interaction

098 does not retroactively mutate 071b transient working state.

If a canonical Parameter currently supplies a value to an open working configuration and the canonical record is later deactivated/archived/deleted/superseded:

- the existing transient working state is not silently rewritten;
- subsequent authoritative source resolution/preflight must detect that the source is no longer current where relevant;
- the operator receives a deterministic stale/unavailable/source-changed condition rather than an invisible replacement.

The exact reconciliation behavior is a readiness decision based on current 071b/058c seams.

## 13. Concurrency and idempotency

Lifecycle operations must tolerate duplicate clicks/retries without producing contradictory relationships or repeated destructive side effects.

Readiness must inspect current SQLite transaction patterns and choose the minimum server-owned protection. At minimum:

- transition validation and mutation occur atomically;
- stale expected state fails closed;
- supersede cannot produce two active replacements through a race if the domain contract requires one;
- delete/archive retries converge to the same canonical outcome or return an explicit already-transitioned result.

No generic event-sourcing system or command bus is authorized merely to implement these guarantees.

## 14. Failure modes that must be tested

Implementation/readiness must cover, as applicable:

1. wrong workspace record ID;
2. unsupported lifecycle transition;
3. stale current-state precondition;
4. duplicate/retried transition;
5. delete with canonical dependents;
6. supersede with missing/incompatible replacement;
7. two concurrent supersede attempts;
8. archived/deleted record absent from normal Engineering Data;
9. audit view can still resolve retained tombstone/history where required;
10. archived/deleted record absent from normal canonical AI/context projection;
11. historical run/evidence lineage remains inspectable;
12. canonical lifecycle change does not silently mutate open 071b working state;
13. workspace switch while a mutation is in flight cannot apply stale UI state to the new workspace;
14. backend rejection leaves UI unchanged and communicates the actual reason;
15. keyboard/focus/effective-200% behavior for confirmation/action controls;
16. no provider call, runner execution or simulation run is triggered by lifecycle mutation.

## 15. Browser acceptance

A browser/evidence harness for the implemented subset must prove:

- actions appear only for supported record/state combinations;
- selection and action confirmation remain usable at effective 200%;
- destructive actions identify the target and consequence;
- successful transition updates the normal list from server truth;
- rejected/stale transition does not optimistically leave false state;
- `Show archived/superseded/deleted` is secondary and does not contaminate normal view;
- workspace switching clears stale selection/action state;
- no page-level overflow or focus trap;
- existing light/dark/system and reduced-motion invariants remain intact.

## 16. Scope and implementation-now boundary

This definition authorizes a later readiness decision to implement only the minimum server + Engineering Data changes necessary for truthful lifecycle behavior over the currently supported canonical record families.

Readiness must explicitly list:

- record kinds implemented now;
- lifecycle transitions implemented now per kind;
- schema additions, if any;
- route/service changes;
- canonical query/context filters affected;
- frontend action/confirmation changes;
- migration/default semantics for existing rows;
- exact deterministic and browser tests.

If a record kind cannot safely support the full lifecycle with current authority, readiness must narrow it rather than invent semantics.

## 17. Prepared but not implemented here

The design must not preclude:

- future unified canonical write intent under 101;
- richer history/audit views;
- bulk lifecycle operations;
- Jarvis proposals that ask the operator to perform canonical lifecycle changes through a future typed canonical-write authority.

None of those are required by 098.

## 18. Non-goals

098 does **not** authorize:

- a second engineering/canonical database;
- event sourcing or a generic command bus;
- browser-only lifecycle state;
- physical cascade deletion by default;
- automatic deletion from AI/Jarvis prose;
- silent canonical mutation from 097 working-state actions;
- variant creation/comparison (006b/058b);
- run execution or preflight changes;
- provider, budget, egress or thread changes;
- Notes;
- 062 grading UI;
- global visual identity (100);
- 101 canonical-state-write unification ahead of its queue slot;
- broad cleanup of the placeholder `app/modules/engineering` boundary (105 owns that later cleanup).

## 19. Readiness questions

A separate readiness record must answer from exact then-current runtime:

1. Which current tables/records are the actual canonical lifecycle targets for 098?
2. Which existing `status` fields must remain domain/quality fields rather than lifecycle?
3. Is one additive lifecycle column sufficient, or do some kinds require a different minimal representation?
4. What is the safe existing-row migration/default?
5. Which references make delete unsafe and how are tombstones resolved?
6. What exact supersede relationship is already authoritative for Parameters and can it be reused safely?
7. Which canonical list/context/dependency queries must filter lifecycle state?
8. How does 058c/071b detect a linked canonical source that becomes non-current after the working state was opened?
9. What is the minimum exact per-kind edit surface that does not pre-empt 101?
10. What exact browser matrix and rollback prove no false UI state after failed/stale transitions?

Implementation cannot begin until those questions are answered and independently reviewed.

## 20. Definition of done for 098 implementation

A future implementation is complete only when:

1. lifecycle semantics are server-owned and distinct from evidence/value quality;
2. implemented transitions are atomic, stale-safe and workspace-safe;
3. supersede preserves explicit lineage;
4. delete is truthful, safe and hidden from normal view without destroying required audit lineage;
5. normal canonical projections consistently respect lifecycle state;
6. Engineering Data exposes only valid actions and refreshes from server truth;
7. open working configuration is never silently rewritten by canonical lifecycle changes;
8. deterministic and browser acceptance are green on one immutable exact head;
9. no current P0/P1/beta-blocking P2 remains;
10. merge and registry reconciliation complete before 006b begins.