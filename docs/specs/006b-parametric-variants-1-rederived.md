# 006b — PARAMETRIC-VARIANTS-1

Status: **definition-only; implementation not authorized**  
Date: 2026-08-23  
Depends on: 006, 071b, 083, 085, 092, 058c

## 1. Purpose

Re-derive the historical BLUECAD parametric-variant idea under the operator-workstation authority established by 095 and the merged 071b/092/058c/097/098 runtime contracts.

A JarvisOS variant is an alternate **engineering working configuration / immutable run snapshot**, not a child CAD candidate tree, not a copied project database, and not a second source of engineering truth. The operator may take a compatible prior successful run or the current working baseline, load it explicitly into the single 071b working-configuration owner, adjust engineering values/model choice through existing Properties/Jarvis authority, preflight deterministically, and execute a new immutable run. None of those actions implicitly promotes values into canonical project records.

This definition supersedes the old `006b-bluecad-parametric-variants.md` implementation concept of frontend-generated GeometrySpec sliders, `origin=parametric_variant` child candidates, variant-specific parked states, or a dedicated BLUECAD variant endpoint. That file remains historical context only. Runtime implementation is unauthorized until a separate exact-master readiness record proves the minimum existing run/query and working-state seams sufficient or identifies one narrowly bounded missing seam.

## 2. Preserved authority

006b must reuse, not duplicate:

- 071b as the **only mutable working-configuration owner**, including dirty state, revision/preconditions, Undo/Revert, deterministic preview/preflight, run-start idempotency and successful-run baseline adoption;
- 092 for stable scene-hit → engineering-object identity only;
- 058c for authoritative property groups, model-family/model-option semantics, exact units and formula/dependency Inspect behavior;
- 097 for structured stale-safe Jarvis working-state mutations; loading a variant must not create a second AI mutation path;
- 098 for canonical engineering-record lifecycle; variants are not an alternate Parameter/Assumption/Decision lifecycle store;
- existing Runs authority for persisted execution snapshots, results, failures and human run labels;
- existing runner/provider/budget/egress boundaries; variant selection itself performs no provider call and does not bypass deterministic preflight.

006b does not reopen those merged slices or broaden their authority.

## 3. State model

The following remain distinct:

1. **Canonical project data** — server-owned accepted/project authority.
2. **Working configuration** — one mutable operator-session state owned by 071b.
3. **Immutable run snapshot** — exact effective input/model state persisted when execution actually starts.
4. **Run result/evidence** — server-owned execution outcome.
5. **Variant reference** — an operator-facing way to choose a compatible baseline/snapshot; it is not a fifth engineering data store unless readiness proves a minimal durable naming/reference seam is actually necessary.

The minimum product must prefer existing persisted runs plus their human labels over a new variants table. A run can act as a reusable variant source only when the server can reconstruct its exact model/contract identity, effective input values and units without frontend inference.

## 4. Operator contract

### 4.1 Load prior successful run

The normal action is explicit, for example `Load as working configuration`.

Loading a prior successful run:

- replaces the current 071b working configuration only after compatibility and stale checks pass;
- establishes a human-readable baseline such as `Baseline: Run 41`;
- labels loaded provenance `Previous successful run` where exact provenance is available;
- does **not** mutate canonical Parameters, Assumptions, Decisions, Specifications or Constraints;
- does **not** create a new run merely by loading;
- does **not** rerun automatically;
- immediately re-enters deterministic preflight against the current authoritative model contract;
- preserves exact contract units and refuses silent unit conversion.

A successful subsequent execution may establish a new working baseline under 071b, still without canonical project promotion.

### 4.2 Branch from current baseline

The operator may continue from the current working baseline, edit values/model choice through the existing Properties/Jarvis seams, give the execution a meaningful run label, and execute. The resulting run is a new immutable comparison candidate by virtue of existing run history; no child-candidate genealogy is required for the first implementation.

If a lightweight operator label such as `Variant A` is desired, readiness must first determine whether the existing run label is sufficient. A new durable variant-name store is forbidden unless the existing run label cannot meet the acceptance criteria.

### 4.3 Unsaved working changes

Loading another run/baseline while the current working configuration is dirty must never silently discard edits.

Minimum fail-safe behavior:

- no automatic overwrite;
- present the existing dirty state and require an explicit replace/discard decision;
- if the operator cancels, working state is unchanged;
- if replacement is confirmed, the complete compatible snapshot replaces the working configuration atomically from the operator perspective and Undo/Revert behavior is defined by readiness from the existing 071b mechanism.

No partial field merge is part of this slice. Selective merge/bulk application is deferred unless readiness proves it is already safely supported by existing authority.

## 5. Compatibility and fail-closed rules

A prior run is loadable only when compatibility can be established deterministically from authoritative data.

Readiness must freeze the exact predicate from current runtime, including at minimum where available:

- workspace ownership;
- model implementation/version identity;
- input-contract digest/schema compatibility;
- exact variable identity and requiredness;
- exact units;
- model-family/model-option semantics introduced by 058c;
- semantic target/object applicability when object-specific fields are involved.

If the current contract has changed and exact compatibility cannot be proven, the action is disabled/fails closed with an operator-readable reason. The frontend must not map old fields by label similarity, position, fuzzy name, unit guess, mesh identity or AI inference.

A compatible snapshot may still become non-ready under current dependencies/validation; loading is allowed only if the snapshot can be represented truthfully, but **Run remains blocked until current deterministic preflight is ready**.

Historical runs that lack enough persisted information remain inspectable in Runs but are not loadable as working configurations.

## 6. Effective values, model choice and provenance

A loaded variant must preserve the effective engineering meaning already defined by 058c:

- exact variable identity and unit;
- active model-family/model-option choice where authoritative;
- values belonging to inactive alternatives only when existing working-state contracts can retain them truthfully;
- linked/source provenance only when the persisted snapshot proves it;
- no relabelling of a previous-run value as current canonical Parameter merely because the numeric value matches.

The primary provenance for restored snapshot values is `Previous successful run`. Inspect/Audit may expose the source run identity and exact immutable evidence.

If a source Parameter referenced by the historical run has since changed, the restored **effective snapshot value** remains the historical run value; it must not silently resolve to the Parameter's new current value. Any later explicit switch back to a live Parameter binding is a new working edit under 071b.

## 7. Run semantics

006b does not alter 071b run semantics:

```text
load/adjust working configuration
        ↓
deterministic preflight
  ├─ not ready → zero new run records
  └─ ready
       ↓ explicit Run
immutable snapshot
       ↓
execution
  ├─ real failure → persisted failed run
  └─ success → persisted successful run / optional new working baseline
```

Loading, selecting or renaming a variant is never execution authority. Variant comparison/history does not grant execution authority either.

The existing stable request-key/retry rules remain unchanged; 006b must not add a second run launcher.

## 8. UI surface

006b adds only the minimum operator surface needed to find and load compatible prior configurations.

Preferred integration points, subject to readiness inspection:

- Runs detail/list: `Load as working configuration` on eligible successful runs;
- Properties baseline/working header: show the loaded human baseline and dirty state;
- optional compact baseline/variant selector only if it can reuse the same single working-state owner without parallel state.

Normal UI leads with human run/variant labels, model choice and useful engineering context. UUIDs/digests stay Inspect/Audit.

Do not implement the 058b comparison matrix in 006b. This slice may expose a downstream navigation/selection seam, but multi-run unit-aware comparison belongs exclusively to re-derived 058b.

Responsive behavior must preserve the existing Jarvis-over-Properties sidecar, internal scroll containment, keyboard/focus order, reduced motion, light/dark/system themes and effective-200% behavior. No page-level horizontal overflow.

## 9. Failure, stale and race behavior

Readiness and implementation must cover at least:

- current working state changes while a historical run/snapshot is being fetched;
- workspace/model/semantic target changes before load completes;
- source run becomes unavailable/deleted from the current read surface;
- contract/model digest changes between eligibility display and apply;
- dirty state exists when load is requested;
- duplicate rapid load actions;
- late responses from a previously selected run;
- current preflight response arriving after a baseline replacement;
- a loaded snapshot is representable but current preflight is non-ready;
- historical run contains missing/unknown/extra fields;
- exact-unit mismatch;
- object-specific semantic context no longer matches current target.

Every stale/ambiguous path fails closed and leaves the newer working configuration unchanged. No partial silent apply.

## 10. Backend/read-model boundary

Definition does **not** pre-authorize a new backend route, table or schema.

Readiness must inspect the exact current run list/detail APIs and persisted runner/simulation-run records. The preferred implementation is frontend composition over existing immutable run evidence if that evidence already exposes all fields needed for exact reconstruction.

Only if exact-master inspection proves a concrete information gap may readiness authorize one minimal read-only reconstruction seam. Any such seam must:

- remain server-owned and workspace-scoped;
- expose only persisted authoritative snapshot data, not recompute/guess it;
- add no second execution path;
- add no variant database by default;
- be separately justified by the mandatory minimum-necessary test.

Durable CRUD for arbitrary unexecuted variant drafts is explicitly outside this slice.

## 11. Explicit non-goals

006b does not implement:

- old child BLUECAD candidate variants, `parent_candidate_id`, `origin=parametric_variant`, new parked reasons or a slider-generated GeometrySpec mutation path;
- parameter sweeps, DOE, optimization, sensitivity search or automatic batch execution;
- multi-run comparison charts/tables (058b);
- canonical project promotion or lifecycle mutation (098 remains authority);
- new model/property semantics (058c remains authority);
- Jarvis free-text mutation parsing or a second action path (097 remains authority);
- persistent unsaved draft variants;
- cross-workspace variant copying;
- fuzzy migration of incompatible historical runs;
- new provider/AI calls;
- process flowsheet/topology editing or the later 058d scaffold;
- global visual identity work.

## 12. Migration and legacy behavior

No migration rewrites historical BLUECAD candidates or simulation runs.

The old 006b spec is superseded as implementation authority by this definition but remains in the repository as historical planning evidence. Existing candidate lineage continues to work exactly as today; 006b simply stops treating candidate lineage as the product definition of an engineering variant.

Historical runs lacking sufficient snapshot/contract evidence remain read-only history. The UI states that they cannot be loaded rather than reconstructing values heuristically.

Rollback of 006b runtime must leave canonical project records, existing run history and BLUECAD candidates untouched.

## 13. Deterministic acceptance requirements

Readiness must turn the exact current runtime into deterministic tests for at least:

1. compatible successful run reconstructs the expected working bindings/model choice exactly;
2. load performs zero canonical record mutations;
3. load performs zero run creation/execution/provider dispatch;
4. incompatible contract/model/unit fails closed;
5. historical insufficient snapshot is inspectable but not loadable;
6. dirty current working state is not silently overwritten;
7. stale/late load response cannot replace newer workspace/model/selection/revision state;
8. loaded baseline reruns current deterministic preflight;
9. non-ready loaded state creates zero runs;
10. explicit subsequent Run still uses one 071b immutable snapshot/request-key path;
11. current Parameter changes do not rewrite the historical effective value restored from a snapshot;
12. failed execution preserves the edited working configuration;
13. 058b comparison and canonical promotion remain absent.

If current APIs cannot prove exact snapshot reconstruction, readiness must stop and document the smallest missing read-only seam instead of authorizing heuristics.

## 14. Browser acceptance matrix

The eventual implementation must include real browser evidence for:

- open a successful compatible Run and load it explicitly;
- Properties shows `Previous successful run` / human baseline context and exact units;
- dirty current state triggers explicit replacement protection;
- incompatible/legacy run is visibly non-loadable with reason;
- after load, `Ready` or real current blockers are shown from deterministic preflight;
- Run remains disabled when non-ready;
- editing after load creates normal dirty state and Undo/Revert still work;
- workspace/model/scene-target switch during load cannot apply stale state;
- keyboard-only operation and visible focus;
- effective 200% zoom without page-level horizontal overflow;
- light/dark/system theme behavior remains semantic;
- Runs, Jarvis/Properties and Analysis Dock containment do not regress.

No screenshot-only success criterion may substitute for state/effect assertions.

## 15. Readiness questions that must be answered from exact master

Before runtime implementation, a separate readiness record must inspect and freeze:

1. Which current Runs endpoint/model contains the persisted effective input snapshot, model-version identity, status and human run label?
2. Does that response preserve exact units and source bindings sufficiently to reconstruct the 071b `BindingMap`, or is one bounded read-only reconstruction seam necessary?
3. Can 058c active model-option identity be reconstructed exactly from persisted run evidence today?
4. What is the smallest exact compatibility predicate and error taxonomy?
5. Where should the operator action live with minimum duplication: existing Runs detail/list, Properties header, or both through one shared action?
6. How will the current 071b revision/preview generations invalidate an in-flight load without introducing a second state owner?
7. Is the existing `run_label` sufficient as the first human variant name, avoiding durable variant metadata?
8. What focused deterministic tests and browser harness can prove zero canonical/run/provider side effects on load?

Readiness may narrow this definition to the exact subset current authority supports, but may not reintroduce the old child-candidate/slider architecture or silently broaden into 058b.

## 16. Downstream seam

After 006b implementation merges and is registry-reconciled, re-derived **058b VARIANT-COMPARISON-1** may compare compatible immutable runs/working baselines using declared units, active model choices, real results and warnings rather than raw JSON/UUID history.

After 058b completes and is reconciled, the maintainer-mandated **058d PROCESS-WORKSPACE-SCAFFOLD-0** lifecycle occurs before VISUAL-IDENTITY-1. 006b must not implement any part of 058d early.

## 17. Definition acceptance

This definition is ready to merge when:

- it is reviewed against exact 095/071b/092/058c/097/098 authority and current runtime;
- it clearly supersedes the old child-BLUECAD-candidate interpretation without deleting history;
- no runtime/schema/provider/store change is included;
- deterministic gates are green on the exact immutable definition head;
- an independent exact-head review finds no material P0/P1/P2;
- `006b` remains `planned` until its separate readiness package merges and is reconciled.
