# 071b — ENGINEERING-PROPERTIES-1

Status: **definition-only draft; implementation not authorized**  
Date: 2026-08-18  
Depends on: 071, 096

## 1. Purpose

Add the first operator-first engineering state layer on top of the already-merged 071 model input-contract / binding-preview / scenario-run authority and the merged 096 workstation shell correction.

071b turns the lower sidecar `Properties` region into a real engineering editor driven by authoritative model/input contracts. It introduces a transient **working configuration** for safe exploration, deterministic preview/preflight before execution, effective values with operator-readable provenance, and bounded dirty/Undo/Revert behavior.

This slice is additive. It does **not** reopen historical 071 implementation evidence, invent a second engineering database, make the scene graph authoritative, add Jarvis mutation authority, or implement canonical record lifecycle changes.

The central contract is:

```text
canonical project/model authority
          ↓ resolve
mutable working configuration
          ↓ deterministic preview/preflight
          ├─ non-ready → blocker UI, NO run created
          └─ ready
               ↓ explicit Run
        immutable execution snapshot
               ↓
        persisted result / failure evidence
```

A successful run may establish the next working baseline. It never silently promotes working values into canonical Parameters, Assumptions or Decisions.

## 2. Preserved authority from merged 071

071 remains authoritative for:

- immutable versioned model input contracts and their digest;
- caller-authoritative numeric values with exact contract units;
- side-effect-free binding preview;
- `missing` / `manual` / `parameter` / `invalid` binding state;
- forward input DOF (`structural`, `bound`, `unresolved`);
- workspace validation of parameter-backed bindings;
- `normalized_input_set` only when preview is ready;
- execution through the existing runner boundary;
- persisted `simulation_runs` as immutable execution evidence;
- no automatic parameter mutation/promotion from scenario execution;
- no equation-oriented inverse solver, optimization or hidden defaults.

071b may adapt these contracts into the operator workstation but may not weaken them. In particular, frontend state never makes an invalid binding valid, never performs implicit unit conversion, and never creates a run merely because the UI considers a form complete.

## 3. State ownership

Four state classes remain distinct.

### 3.1 Canonical project/model data

Server-owned existing authority: model version/input contract, accepted or proposed engineering records, linked Parameters, current run history and existing provenance.

071b does not add canonical record mutation endpoints. Those belong to 098.

### 3.2 Working configuration

A mutable, operator-session configuration derived from one selected eligible model implementation plus an initial baseline.

Version 1 is intentionally transient:

- stored in frontend memory only;
- never in `localStorage`, `sessionStorage`, URL query parameters or a new database table;
- may be lost if the page/application is left before an execution establishes a baseline;
- does not mutate the source Parameter when a parameter-backed field receives a working override;
- does not become a design decision merely because it is used in a run.

The working configuration owns:

- current field binding/value for the active contract;
- retained inactive-choice field values when a contract-defined choice temporarily hides them, where authoritative metadata exists;
- dirty state relative to the current baseline;
- a monotonically changing local revision/precondition identity;
- bounded Undo/Revert history sufficient for operator correction, not an audit ledger.

No second general-purpose frontend state framework is authorized. Reuse current React state/component patterns unless exact-master inspection proves a smaller existing shared mechanism is already appropriate.

### 3.3 Run snapshot

Only when deterministic preflight is ready and the operator explicitly starts execution does existing runner authority create/persist the execution record. Its normalized effective input set is immutable evidence.

### 3.4 Results

Outputs, logs, artifacts and genuine execution failures remain server-owned run evidence. 071b does not reinterpret them as canonical design truth.

## 4. Initial working baseline

For one eligible model implementation, the working configuration resolves an initial value per contract variable from existing authority only.

Permitted initial sources are:

1. a currently selected/compatible canonical Parameter binding already represented by existing 071 authority;
2. an explicit current manual scenario value already held by the active UI session;
3. the most recent successful run only when an existing API can unambiguously reconstruct the same model-version contract and exact units without inventing provenance;
4. otherwise `Empty`.

Readiness must inspect exact current APIs and choose the minimum truthful subset. If source (3) cannot be implemented without new run-query/backend authority, it is deferred to 006b rather than approximated client-side.

There is no numeric product default, fixture fill, “recommended” hidden seed, or Mark-1 design injected by 071b.

The baseline has a human-readable label when available, for example `Baseline: Run 41` or `Baseline: current bindings`. Opaque run IDs belong to Inspect/Audit.

## 5. Properties surface

071b populates the bounded lower Properties pane established by 096. It does not change the 096 Jarvis-over-Properties geometry.

### 5.1 Operator header

The header leads with the best authoritative human/model identity available, not UUIDs. Until 092 adds stable scene-selection → engineering-object binding, 071b may operate on model/scenario context already available from merged 071/096 surfaces. It must not claim that a Three.js mesh is a real engineering object.

Show compactly:

- human model/contract label;
- model implementation label/version when meaningful;
- `Ready`, blocker count, or warning count from deterministic preview;
- dirty summary such as `4 unsaved changes · Baseline: Run 41`.

Machine IDs, contract digest and exact timestamps are under `Technical details` / Audit.

### 5.2 Contract-driven rows

Render fields from server-authoritative contract metadata, never from a production hard-coded list of BlueRev numbers.

Each visible field may contain:

- human label;
- effective working value or `Empty`;
- exact contract unit;
- semantic source label;
- editability;
- dirty marker;
- authoritative blocker/warning if present;
- link/inspect affordance when the source is another canonical record;
- derived/formula affordance only when authoritative formula metadata exists.

At minimum, merged 071 categories (`design`, `operating`, `property`, `model_parameter`, `equipment`) must be rendered meaningfully without pretending they are the final domain taxonomy. 058c later owns richer engineering object/property grouping such as Geometry, Hydraulics, Thermal, Optical and Fouling where real semantics exist.

071b may provide a stable renderer grouping seam, but must not infer domain groups from field names.

### 5.3 `Empty` semantics

`Empty` is first-class operator information.

- Optional field with no value: neutral `Empty`; no blocker.
- Required active-contract field with no valid binding: `Empty` plus deterministic blocker returned/derived from the existing preview contract.
- Fields belonging only to a known inactive sub-contract are hidden in normal Operate view, not rendered as a long wall of empty rows.

If current server contracts cannot authoritatively distinguish active/inactive sub-contracts, 071b must not fabricate that distinction. The complete model-choice semantics are finalized in 058c; readiness must freeze exactly what 071b can render truthfully now.

## 6. Effective value and semantic provenance

The primary row value is the value that would be sent to deterministic preview **now**.

Operator-facing provenance uses semantic labels, for example:

- `User` / `Working override`;
- `Parameter` with human source identity;
- `Measured` only when existing authority explicitly says measured;
- `CAD` only when an authoritative existing CAD link says so;
- `Linked stream` only when an authoritative link exists;
- `Calculated` only for actual derived output/evidence;
- `Scenario override`;
- `Previous successful run` only when exact run provenance is known;
- `Jarvis proposal` / `AI suggested — not validated` are reserved seams for 097 and are not created by 071b itself.

Never infer `Measured`, `Validated`, `Accepted`, `CAD`, or `Linked stream` from prose, naming conventions or UI origin.

Opaque `source_parameter_id`, model UUID, request ID and contract digest remain Inspect/Audit, copyable when useful.

### 6.1 Linked-authority rule

A value may be displayed contextually in Properties while remaining authoritative elsewhere. Editing a contextual linked value must either:

- create an explicit working override for this configuration, leaving the linked source unchanged; or
- navigate/open the authoritative source for editing in a later authorized lifecycle surface.

071b never silently writes through to the source Parameter/stream/CAD record.

## 7. Editing contract

### 7.1 Manual edit

Editing a value updates working state only. Validate syntax locally for immediate usability, but final binding validity belongs to server preview.

No implicit unit conversion is added. A row uses the exact canonical contract unit. Unsupported alternate-unit entry fails clearly rather than being silently converted.

### 7.2 Dirty state

A field is dirty when its effective working binding differs semantically from the baseline binding/value/source state.

The surface provides:

- discreet per-field dirty indication without relying on colour alone;
- total dirty count;
- `Undo` for recent working changes;
- `Revert` for a field where practical;
- `Revert all` to restore the current baseline.

Undo history is bounded and session-local. It is not persisted evidence and is not used to reconstruct canonical provenance.

After a successful execution is authoritatively observed and adopted as the next working baseline, dirty markers clear against that baseline. After a failed execution, the current working edits remain so the operator can repair and retry.

### 7.3 Working revision

Every working-state mutation increments/changes a revision token. Async preview responses are accepted only if they correspond to the current model/contract and working revision/request generation.

This establishes the stale-action seam for 097. 071b does not yet let Jarvis mutate it.

## 8. Model-choice seam and inactive values

The maintainer-approved product contract requires mutually exclusive model alternatives (for example constant pressure versus Ergun) to be one selector whose choice determines the visible input sub-contract, with inactive values retained.

071b must preserve a clean seam for this behavior, but implementation may expose a model selector **only when current backend contract metadata explicitly defines the alternatives and their required variables**. It must not infer mutually exclusive models from independent Assumption records.

Where authoritative model-choice metadata is available:

- exactly one alternative is active in normal working state;
- switching alternative updates visible required fields;
- values associated with the previous alternative remain in transient working state and are restored if reselected;
- they are not submitted in the normalized active input set unless the selected contract requires them;
- imported/legacy state declaring incompatible simultaneous alternatives is a deterministic blocker.

Where that metadata is absent, 071b renders the existing 071 contract as-is and 058c owns the later semantic expansion. This avoids a fake BlueRev model taxonomy in frontend code.

## 9. Derived values and formula Inspect seam

071b must not turn outputs into editable inputs or invent formulas.

A value is rendered read-only `Calculated`/derived only when existing server evidence identifies it as such. `fx`/formula Inspect may be exposed in this slice only if exact existing metadata can supply:

- formula/model identity;
- effective inputs and exact units;
- result;
- validity/domain evidence where available.

Otherwise the UI may reserve an affordance/component seam but must not render fabricated equations. 058c owns complete formula/dependency Inspect semantics.

## 10. Deterministic preview and blocker model

Every meaningful working change schedules or explicitly triggers the existing 071 side-effect-free binding preview using the active model version and current bindings.

Preview authority, not frontend heuristics, owns:

- `ready` / `incomplete` / `invalid`;
- structural/bound/unresolved input DOF;
- invalid binding codes;
- normalized input set;
- parameter-workspace/unit/domain validation.

071b translates that evidence into operator language without inventing severity.

### 10.1 Quiet when valid

When preview is `ready`, show one compact `Ready` state. Do not permanently list successful DOF/unit/dependency checks.

When non-ready:

- show a bounded summary such as `3 blockers`;
- mark the affected rows;
- state the actual issue (`Required value is empty`, `Expected unit m`, `Parameter is outside this workspace`, etc.) from stable error/state authority;
- provide `Go to first issue` / focus navigation.

A warning is shown only when an existing authoritative contract explicitly allows execution with a caveat. 071b does not downgrade a blocker or invent a warning.

### 10.2 Preview failure

Network/server/parse failure during preview does not mean the model is valid or invalid. Show `Preflight unavailable` / equivalent uncertainty and prevent a new Run because readiness is unproven.

Do not reuse an older `ready` response after working revision changes.

## 11. Run-start semantics

The operator's Run action is two-stage:

1. obtain/confirm deterministic preview for the exact current working revision;
2. only if `state=ready`, use that preview's normalized input set through the existing runner execution spine.

### 11.1 Pre-execution failure creates no run

These are UI/preflight attempts, not simulation runs:

- required binding missing;
- invalid unit/value/domain/source;
- unresolved required input DOF;
- authoritative model-choice conflict;
- required stale/missing dependency when current backend authority exposes it;
- preview unavailable/uncertain.

The operator sees the blocker and navigation to repair it. Repeated Run clicks in this state must not create failed run-history noise.

### 11.2 Execution-start snapshot

Once the ready normalized input set is accepted by existing runner start authority, the resulting run owns the immutable execution snapshot. The frontend must not mutate that run if working state changes afterward.

### 11.3 Genuine failed execution

If the runner actually starts and then script/solver/runtime validation fails or does not converge, the failed run remains persisted and inspectable under existing run authority. 071b must not hide it as a form-validation error.

### 11.4 Successful execution

When execution succeeds:

- the run persists normally;
- exact executed effective inputs remain immutable evidence;
- no canonical Parameter/Assumption/Decision is automatically changed;
- the UI may set this successful run as the next **working baseline** for the same eligible model/contract;
- dirty markers then clear against that baseline.

A later explicit project-promotion operation belongs to existing/future record authority, not Run.

## 12. Concurrency, stale data and uncertain outcomes

### 12.1 Rapid edits / preview races

Use request generation plus working revision. A response for revision N must not overwrite preview state for revision N+1. Abort in-flight preview where convenient, but correctness must not depend on successful abort.

### 12.2 Model/contract switch

Switching model/version invalidates outstanding preview and run-start preparation. No old response may populate the new contract.

### 12.3 Double Run

Once a ready run-start request is in flight, disable/hold duplicate Run submission. Re-enable only after the existing execution API returns a definite result or its existing idempotency/recovery semantics have been resolved.

Do not invent a second run idempotency protocol in frontend code. Readiness must verify existing runner behavior and freeze the safe call sequence.

### 12.4 Uncertain run creation

A timeout/network loss after dispatch must not be rendered as `not started` unless existing server authority proves absence. Use current run/job read-back/idempotency authority where available; otherwise expose an uncertain state and require refresh/reconciliation instead of blind duplicate dispatch.

### 12.5 Successful run versus later edits

If working revision changes while a run executes, the completed run remains evidence for the revision that started it. It may become available as a baseline, but must not silently overwrite newer dirty working edits. The operator can explicitly revert/load later; automatic baseline replacement is allowed only when the working revision still matches the started revision.

### 12.6 Malformed/legacy contract

Missing, malformed or digest-inconsistent contracts remain ineligible as required by 071. Properties shows a bounded unsupported/error state; it must not guess fields from result JSON.

## 13. Responsive and containment behavior

071b inherits 096 layout authority:

- desktop: Jarvis ~40–45% upper sidecar, Properties ~55–60% lower;
- each pane scrolls internally;
- Properties header/status remains reachable while property rows scroll;
- effective 200%/compact mode uses `Jarvis | Properties` tabs when the split is no longer usable;
- no page-level horizontal overflow from labels, units, values, source names or machine IDs;
- long machine identifiers are truncated/wrapped and recoverable only in Inspect/Audit.

The property grid must remain operable by keyboard. Labels, dirty state, blockers and source state cannot rely on colour alone. Preserve existing focus return, reduced-motion and light/dark/system appearance contracts.

## 14. API and implementation shape to inspect at readiness

Readiness must resolve exact-master ownership before authorizing code. Expected minimum seams are:

- existing 071 model implementation/input-contract read;
- existing 071 binding-preview route/service;
- existing runner job/run-start/read APIs;
- current 096 sidecar/Properties shell components;
- current frontend API client and model scenario state;
- existing run details sufficient to distinguish actual execution from preflight.

Prefer a small frontend working-configuration module/hook only if current component boundaries cannot safely own the state. Do not create a generic Redux-like store, new persistence service, scenario database or model DSL.

Backend changes are permitted only if readiness proves a **minimal missing contract** is necessary to preserve the approved semantics (for example an exact read-back field needed to distinguish an uncertain dispatch or reconstruct a compatible successful baseline). Any such addition must be additive, bounded and separately called out in readiness; do not broaden 071b into 092/058c/097/098.

## 15. Explicitly implemented now

Subject to readiness inspection, 071b owns:

- contract-driven population of the existing Properties pane for eligible model/scenario context;
- transient working configuration;
- effective value/unit/source presentation from real authority;
- optional/required empty presentation where the existing contract supports it;
- manual/parameter working bindings using existing 071 semantics;
- dirty count/per-field dirty indication;
- Undo/Revert/Revert all in working state;
- revision-safe deterministic preview/preflight;
- quiet Ready vs blocker summary and `Go to issue`;
- preflight-invalid → no run;
- ready → existing run-start spine;
- failed execution persistence distinction;
- successful-run working-baseline adoption when it cannot clobber newer edits;
- technical-details progressive disclosure for machine identity.

## 16. Prepared but not implemented

071b must leave clean seams, but does not implement:

- stable CAD/scene selection → engineering object identity (092);
- full domain property-group taxonomy, model-choice schema or formula/dependency semantics where existing contracts lack them (058c);
- Jarvis reading blockers and applying working-state patches (097);
- canonical Edit / Active-Inactive / Archive / Supersede / Delete (098);
- variant trees, persistent named configurations, `Load prior run as configuration` if new authority is required, or bulk alternative management (006b);
- engineering variant comparison/history (058b);
- Notes/scratchpad;
- spreadsheet-like paste/bulk edit/apply-to-similar;
- permanent 062 grading UI;
- global visual identity changes.

## 17. Non-goals

- No second engineering store or persistent draft table.
- No localStorage/sessionStorage draft persistence.
- No automatic canonical Parameter mutation or promotion.
- No automatic design decision acceptance.
- No hidden numerical defaults, guesses or AI-filled Empty fields.
- No frontend provider/model call.
- No Jarvis mutation parser/action execution.
- No natural-language-to-binding parsing.
- No unit conversion library.
- No inverse solver, equation-oriented DOF analysis, optimizer or target solver.
- No scene semantic identity based on mesh index, Three.js UUID or exporter ordering.
- No hard-coded BlueRev property taxonomy that current backend authority does not support.
- No reconstruction of formulas from labels or source code in the browser.
- No broad shell, Runs, Review or visual-identity redesign; 096 owns the corrective layout already merged.

## 18. Migration and rollback

Preferred 071b implementation requires no schema migration: working state is transient and canonical data remains unchanged.

If readiness proves an additive backend field/route is indispensable, the readiness record must include migration compatibility, legacy behavior and rollback before registry promotion.

Frontend rollback is removal of the 071b Properties/working-state integration back to the truthful 096 bounded Properties shell. Existing model contracts, Parameters and simulation runs remain valid because 071b never rewrites them as part of UI editing.

## 19. Required deterministic verification

Readiness may refine exact filenames/test harnesses, but implementation must prove at least:

1. properties are generated from server contract metadata, not a hard-coded field list;
2. exact units remain visible and no implicit conversion occurs;
3. an empty required binding returns/appears as non-ready and an optional empty does not become a fabricated blocker;
4. manual override changes working state only and leaves source Parameter unchanged;
5. dirty count and field markers reflect semantic change from baseline;
6. Undo restores the preceding working binding; Revert all restores baseline;
7. stale preview response for revision N cannot overwrite N+1;
8. model/version switch invalidates old preview results;
9. preview failure is fail-closed for Run;
10. repeated Run while non-ready creates zero simulation runs/jobs;
11. ready Run uses the exact normalized preview input set through existing runner authority;
12. double-submit while start is in flight creates at most one execution under existing idempotency/disable semantics;
13. real runner failure remains a persisted failed run;
14. successful execution does not mutate/promote source Parameters;
15. successful run can clear dirty state only when the completing execution corresponds to the unchanged working revision;
16. completion of an older in-flight run does not overwrite newer working edits;
17. missing/malformed/digest-inconsistent contract does not produce guessed fields;
18. machine IDs/raw contract data remain secondary and bounded;
19. no provider/AI call occurs from Properties/preflight/run presentation;
20. existing 071 contract/preview tests and 096 browser/layout tests remain green.

## 20. Required browser acceptance

Use real app/browser evidence on an immutable product head. At minimum prove:

1. desktop Properties remains inside the lower bounded sidecar with independent internal scroll;
2. an eligible contract renders all authoritative fields and exact units;
3. changing a value produces an immediate dirty marker/count without persisting a canonical record;
4. required `Empty` visibly blocks Run and `Go to first issue` focuses/navigates to it;
5. optional `Empty` remains neutral;
6. fixing the field to a server-valid value changes state to compact `Ready`;
7. Undo and Revert all visibly restore the baseline;
8. a non-ready Run attempt creates no run in the run list;
9. a ready execution produces a persisted run and leaves source Parameter data unchanged;
10. a genuine execution failure remains visible as a failed run while Properties keeps the working edits;
11. while a run is in flight, later working edits are not overwritten by its completion;
12. compact/effective-200% `Jarvis | Properties` tab behavior remains usable;
13. long values/source labels do not produce page-level horizontal overflow;
14. keyboard navigation and focus remain usable without colour-only state;
15. light/dark/system and reduced-motion behavior remain intact;
16. no UI path exposes a hidden product default or fabricated provenance.

Browser fixtures may supply data but must not be shipped as product defaults. Evidence harness failures must be distinguished from product failures.

## 21. Readiness questions that must be answered from exact master

Before changing registry state from `planned` to `ready`, a separate 071b readiness record must determine:

1. exact current frontend component owning the 096 Properties region;
2. whether an existing 071 scenario panel/state can be reused or must be moved/composed;
3. exact input-contract and binding-preview client types/routes currently present;
4. whether preview request contains enough source/value information to reconstruct effective working bindings without ambiguity;
5. exact runner creation/start/read path and idempotency/uncertain-dispatch behavior;
6. how an actual failed execution is distinguished from rejected preflight in current runtime;
7. whether a compatible latest successful run can be recovered without new backend/query behavior; if not, defer run-as-baseline loading rather than adding broad scope;
8. whether optional contract inputs exist and how current preview counts them;
9. whether any current contract has authoritative model-choice/sub-contract metadata; if not, defer selector semantics to 058c while preserving the seam;
10. whether formula metadata exists; if not, do not render `fx` content in 071b;
11. minimal files/routes/tests allowed for implementation;
12. exact browser fixtures and read-back checks proving zero canonical mutation;
13. migration requirement, expected to be none unless exact runtime evidence proves otherwise;
14. rollback path;
15. collision check with open PRs and the still-blocked old 092 front.

## 22. Stop conditions

Stop before implementation and report if:

- the existing runner cannot preserve the exact executed normalized input set;
- truthful non-ready → zero-run behavior requires deleting/rewriting historical run evidence;
- current APIs cannot distinguish uncertain dispatch from definite no-run without a materially new execution/idempotency subsystem;
- a required implementation would need a second engineering state store;
- editing Properties would require direct canonical Parameter mutation;
- model-choice behavior would have to be inferred from unrelated Assumption prose;
- formula/domain information would have to be invented client-side;
- the only path requires reopening 071 equations/047 numerical behavior;
- an open PR owns the same runtime surface;
- implementation would need direct provider/Ollama/model calls from frontend code.

## 23. Definition acceptance

The definition is complete when:

1. it preserves merged 071 as historical runtime authority and uses merged 096 as the UI shell;
2. working configuration, canonical project state, run snapshot and results have explicit separate ownership;
3. no hidden autosave or automatic project promotion is authorized;
4. deterministic preview/preflight owns readiness and pre-execution non-ready creates no run;
5. genuine post-start execution failures remain persisted evidence;
6. dirty/Undo/Revert and successful-baseline behavior cannot overwrite newer edits;
7. Properties is contract-driven with exact units and truthful semantic provenance;
8. model-choice/formula/object semantics are implemented only where real authority exists and otherwise explicitly deferred to 058c/092;
9. stale/race/uncertain-dispatch failure modes are fail-closed;
10. browser/accessibility/200%/containment and no-provider-call acceptance are explicit;
11. downstream seams for 092, 058c, 097, 098, 006b and 058b remain non-circular and independently removable;
12. a separate exact-master readiness decision is still required before implementation authority.