# 058b — VARIANT-COMPARISON-1

Status: **definition-only; implementation not authorized**  
Date: 2026-08-24  
Depends on: 006b, 071b, 083, 085, 089

## 1. Purpose

Re-derive the historical variant-comparison/design-history idea under the operator-workstation authority established by 095 and the merged 006b PARAMETRIC-VARIANTS-1 runtime.

A comparison in JarvisOS is a read-only operator view over existing immutable successful runs and their authoritative engineering/run evidence. It is not a new variant database, a copied project state, a child BLUECAD candidate tree, a design-history ledger, or a second analytics engine.

006b already establishes the minimum variant identity for V0: a compatible persisted successful run may be explicitly loaded as the single 071b working baseline. 058b adds the complementary read-only question:

> For a bounded set of compatible persisted runs, what engineering inputs/model choices and trustworthy recorded results differ, with exact units and explicit incompatibilities?

The implementation remains unauthorized until a separate exact-master readiness record proves which existing run/model/089 seams can satisfy this contract without duplicate state or semantic inference.

## 2. Preserved authority

058b must reuse, not duplicate:

- **006b** for prior successful runs as reusable variant references and for exact-model-version/unit loadability semantics;
- **071b** for the only mutable working configuration, preflight and run-start path;
- **058c** for engineering property/model-family/model-option semantics where those semantics are exposed by authoritative model contracts;
- **088 Runs** for persisted run list/detail evidence and human run labels;
- **089 Analytics Dock** for unit-bearing result observation extraction/comparability and the single existing comparison presentation region;
- **083 shell** for the one Analysis Dock and App-owned workspace;
- existing backend run/model/engineering records as the only source of truth.

058b does not reopen or broaden those slices.

## 3. State and ownership model

The product continues to distinguish:

1. canonical project data;
2. one mutable 071b working configuration;
3. immutable run snapshots;
4. persisted run results/evidence;
5. transient comparison selection and derived presentation.

Item 5 is not engineering truth. Comparison selection may live in transient frontend state owned by the existing Analysis Dock/comparison surface. It must not become a durable variant store, browser-storage history, or React-owned copy of project records.

Closing the comparison surface or changing workspace may discard selection. Persisted runs remain authoritative and unchanged.

## 4. Minimum operator workflow

The first implementation should support a bounded flow such as:

1. operator chooses two or more persisted runs in the current workspace;
2. one selected run is explicitly designated as the comparison baseline;
3. the comparison surface shows compatible engineering configuration fields/model choices and trustworthy result observations;
4. every value carries its declared unit or explicit unitless state;
5. differences are deterministic presentation derived from persisted evidence;
6. incompatible, unavailable or semantically different data is shown as incompatible/unavailable, never silently coerced;
7. an operator may navigate back to a source Run or invoke the already-006b-owned `Load as working configuration` action from a source run, but comparison itself performs no mutation or execution.

No automatic rerun, promotion, recommendation, ranking or best-variant selection is authorized.

## 5. Run compatibility classes

Readiness must freeze the exact comparison predicate from current master.

### 5.1 Engineering-configuration comparison

The safest V0 rule is expected to require, unless exact runtime proves a narrower authoritative compatibility seam:

- same workspace;
- successful persisted runs;
- non-null model-version identity;
- exact model implementation/version identity or another readiness-proven exact contract identity;
- authoritative input contract available;
- persisted input snapshot parseable without inference;
- exact variable identity;
- exact declared units;
- model-family/model-option semantics resolvable from authoritative contract data.

If two runs do not satisfy the engineering-configuration predicate, the UI must not align fields by display label, array order, fuzzy names, matching numeric values, mesh identity or guessed dimensional equivalence.

A run may still participate in result comparison under 089 rules even when configuration comparison is unavailable, provided the UI clearly separates those capabilities.

### 5.2 Result comparison

058b must reuse the comparability rules already owned by 089 rather than creating a second result parser/unit converter.

A recorded result is comparable only where 089 can prove:

- stable metric identity;
- finite numeric value;
- declared unit;
- selected source run identity;
- readiness-frozen unit compatibility.

If 089 currently permits only exact unit-string equality for a metric, 058b inherits that rule. 058b does not add an ad-hoc conversion table.

### 5.3 Partial compatibility is explicit

The UI may show:

- configuration comparable, results comparable;
- configuration comparable, some result groups incompatible;
- configuration unavailable, results comparable;
- historical run inspectable but not comparable.

It must never collapse these into a generic `compatible` badge that overstates evidence.

## 6. Comparison matrix

The normal comparison surface is engineering-first, not JSON-first.

A compact matrix/list may include, only when authoritative:

```text
                     Baseline      Variant A      Variant B
Model choice         Constant      Ergun          Ergun
Inlet temperature    600 °C        650 °C         700 °C
Inlet pressure       34 bar        34 bar         36 bar
ΔP                   0.00 bar      0.42 bar       0.61 bar
Conversion           0.82          0.79           0.76
```

Rules:

- human run labels lead; run UUIDs are secondary Inspect/Audit metadata;
- model-family/model-option values are shown as semantic model choices, not raw implementation IDs;
- units remain visible in text;
- unchanged rows may be visually quiet but must remain discoverable or filterable without losing evidence;
- changed rows must not be signaled by color alone;
- missing/unavailable/incompatible values use explicit semantic states, never numeric zero;
- raw JSON is secondary source evidence, not the comparison UI.

Readiness may narrow the exact row families to what current contracts can prove.

## 7. Baseline and deterministic deltas

Exactly one selected run is the comparison baseline for V0.

The baseline is operator-selected or deterministically defaults to the first explicitly selected run; readiness must freeze one rule and make it visible.

For comparable numeric rows, 058b may show only directly deterministic quantities already safe under 089 semantics, such as:

- recorded value;
- absolute delta from baseline;
- minimum/maximum/range where 089 already authorizes them.

Percentage change is not required and must not be added without an explicit zero/sign rule. No weighted score, desirability index, Pareto rank, optimization score or AI-generated recommendation is authorized.

## 8. Model choices and effective engineering inputs

When authoritative 058c/model-contract semantics exist, comparison should present mutually exclusive engineering model choices as one semantic row.

Examples must come only from real contract authority. No frontend hardcoded catalog of pressure/thermal/optical models is authorized.

For persisted run input snapshots:

- compare the effective historical value actually executed;
- do not silently relink historical values to current Parameters;
- if persisted evidence includes historical source IDs/revisions, those remain Inspect/Audit evidence;
- do not claim a historical value is currently `Measured`, `Parameter`, `CAD`, or `Linked stream` unless the persisted/read contract proves that exact historical provenance truthfully.

`Previous successful run` is a load/baseline provenance in 006b, not a claim that every comparison cell currently owns that source.

## 9. Relationship to 006b loading

Comparison is read-only.

From a source run, the operator may use the already-authorized 006b `Load as working configuration` path when that run is loadable. 058b must not implement a duplicate baseline loader, duplicate dirty-confirmation logic or second reconstruction helper.

If the comparison surface exposes `Load`, it must call the same 006b owner/controller action and inherit all exact-model, unit, stale, dirty-state and zero-side-effect guards.

Loading a run may close or preserve the comparison surface only according to readiness-frozen UI behavior; it must not automatically execute, promote canonical records or rewrite the compared run set.

## 10. Analysis Dock integration

The preferred V0 home is the existing **Analysis Dock**, because 089 already owns the single read-only run-comparison region and unit-safe result comparison semantics.

Readiness must determine whether to:

- extend the existing 089 comparison model with engineering-configuration rows; or
- add one tightly bounded variant-comparison mode inside the same dock while sharing the same run-selection/result-comparability helpers.

A second comparison drawer/page/store is forbidden unless readiness proves the existing dock cannot meet acceptance criteria.

The dock remains:

- transient;
- closed by default on fresh route load;
- keyboard reachable and Escape-closeable;
- bounded by local overflow;
- non-persistent;
- subordinate to the primary workstation/viewport.

## 11. Selection and scale bounds

Readiness must freeze practical limits for:

- maximum compared runs;
- maximum configuration rows;
- maximum result groups;
- maximum label/key lengths;
- handling of large persisted payloads.

The default should remain intentionally small enough for side-by-side engineering review. A 50-run spreadsheet replacement is outside V0.

Truncation must be explicit and may not silently change compatibility decisions.

## 12. Stale/race behavior

All asynchronous reads and derived comparison state must fail closed under at least:

- workspace A → B with late A response;
- selected set X → Y with late X detail response;
- X → Y → X with a late first-X response;
- baseline run removed from selection;
- selected run becomes unavailable;
- run detail refresh changes status/evidence before render;
- model implementation/contract becomes unavailable;
- one selected run detail fails while others succeed;
- malformed persisted input/result payload;
- comparison selection changes while an 006b load is in flight;
- route change while comparison reads are pending.

Changing authoritative comparison context clears stale derived rows synchronously before newer data is accepted.

A failed run fetch is not silently dropped from a comparison that still claims all selected runs are represented.

## 13. Failure and incompatibility states

The UI must distinguish at least:

- fewer than two selected runs;
- selected run not successful where success is required;
- model version unavailable;
- configuration contracts incompatible;
- unknown/missing/malformed configuration field;
- exact-unit mismatch;
- result metric identity mismatch;
- result unit incompatibility under 089 rules;
- selected run disappeared;
- partial read failure;
- no trustworthy comparable result observations;
- valid comparison ready.

Reasons should be semantic and operator-readable. Technical IDs/digests remain Inspect/Audit.

## 14. No hidden authority

058b comparison must perform zero:

- canonical Parameter/Assumption/Decision/Specification/Constraint mutation;
- engineering-record lifecycle mutation;
- run creation/execution/cancellation;
- provider/AI/thread call;
- solver call;
- BLUECAD candidate mutation;
- durable variant metadata creation;
- model-selection mutation;
- automatic 006b load.

It is presentation over persisted evidence only.

## 15. Accessibility and responsive behavior

058b inherits 070/083/089/096 requirements.

Required:

- semantic table/list structure with accessible row/column labels;
- units in accessible text;
- baseline identity available without color;
- incompatibility reasons available without hover;
- keyboard-only run selection, baseline choice, source navigation and any shared 006b Load action;
- visible focus;
- effective 200% zoom without document-level horizontal overflow;
- comparison columns may use bounded local horizontal scrolling inside the dock if needed;
- Jarvis/Properties and primary viewport remain usable;
- light/dark/system themes remain semantic;
- reduced-motion behavior preserved.

No inaccessible canvas-only comparison is authorized.

## 16. Visual boundary

058b owns only local comparison information hierarchy:

- compact rows/columns;
- baseline/changed/incompatible emphasis;
- local overflow;
- run labels/model labels/units.

It must reuse current semantic tokens and shared primitives.

No global fonts, palette, iconography, radius/shadow grammar, motion language or application-wide styling change belongs in 058b. VISUAL-IDENTITY-1 remains downstream.

## 17. Explicit non-goals

058b does not implement:

- a new variant/run database or durable comparison session;
- the old child-candidate genealogy interpretation of variants;
- parameter sweeps, DOE, optimization, sensitivity search or batch execution;
- automatic best-design ranking;
- AI-generated comparison summaries/recommendations;
- new statistical inference;
- unit guessing or independent conversion tables;
- canonical project promotion;
- 097 Jarvis mutation behavior;
- 098 lifecycle mutation;
- editable process flowsheet/topology;
- 058d process-workspace scaffold;
- global visual identity;
- Notes/scratchpad;
- 062 routine grading UI.

## 18. Readiness questions

Before implementation, a separate exact-master readiness record must answer:

1. Which current run list/detail APIs and frontend models expose the selected run snapshots needed for configuration comparison?
2. Can the current 006b reconstruction helper be reused read-only for comparison validation without mutating the 071b owner?
3. What exact same-model/contract predicate is sufficient for aligning engineering configuration rows?
4. Which schema-v3 model-family/model-option metadata survives in current model contracts and can be shown truthfully for historical runs?
5. Which historical source/provenance fields may be shown without reinterpreting them through current canonical records?
6. Which exact 089 helpers/contracts own result observation extraction and unit comparability, and how will 058b reuse them rather than fork them?
7. Can the existing Analysis Dock and run picker be extended without a second selection store?
8. What exact maximum run/row/group bounds preserve usability and prevent hostile payload amplification?
9. What generation/identity guards are required for selected-set/baseline/workspace races?
10. Which existing browser harness can prove comparison plus optional shared 006b Load without canonical/run/provider side effects?
11. Can implementation remain frontend-only? If not, what exact missing read evidence blocks it?
12. What exact file allow-list is minimum after current-runtime inspection?

If current contracts cannot prove engineering row identity or exact units, readiness must narrow the first implementation rather than authorize fuzzy alignment.

## 19. Deterministic acceptance requirements

Readiness must turn current runtime into tests for at least:

1. two compatible successful runs align exact engineering input identities and exact units correctly;
2. model choice is shown semantically only when authoritative;
3. different model/contract identity fails closed rather than fuzzy-aligning fields;
4. unit mismatch is explicit;
5. malformed/unknown/missing persisted fields do not become fake comparison cells;
6. historical source IDs are not silently reinterpreted as current live bindings;
7. 089 result comparability is reused and incompatible result units remain rejected;
8. baseline selection/delta calculation is deterministic;
9. selected-run/workspace generation guards reject late responses;
10. one failed run read makes incompleteness explicit;
11. comparison performs zero canonical/run/provider mutation;
12. any exposed Load action delegates to the single 006b/071b path;
13. closing/reopening the dock does not create durable comparison truth;
14. no 058d, visual-identity, optimization or AI recommendation behavior appears.

## 20. Browser acceptance matrix

The eventual implementation must include real browser evidence for:

- select at least two compatible successful runs;
- choose/identify a baseline;
- see human run labels and semantic engineering rows with exact units;
- see at least one changed value without color-only signaling;
- see model-choice difference where current authority supports it;
- see result comparison through reused 089 semantics;
- see a deliberate incompatible model/contract/unit case rejected visibly;
- navigate to a source Run;
- if Load is exposed, invoke the same 006b path and preserve dirty/stale protections;
- workspace/selected-set switch during reads cannot show stale comparison;
- keyboard-only operation and visible focus;
- effective 200% with no page-level horizontal overflow;
- light/dark/system behavior remains semantic;
- no run/provider/canonical mutation occurs merely by comparing.

Screenshot-only evidence is insufficient without state/effect assertions.

## 21. Migration and rollback

No migration rewrites historical runs, BLUECAD candidates or canonical project records.

Removing 058b runtime must leave:

- 006b load-previous-run behavior intact;
- 089 result analytics intact;
- 071b Properties/working configuration intact;
- persisted run history untouched.

Any new helper introduced by implementation must remain removable with the comparison surface and must not become a hidden execution or engineering-data authority.

## 22. Downstream seam

After 058b implementation merges and is registry-reconciled, the maintainer-mandated **058d PROCESS-WORKSPACE-SCAFFOLD-0** lifecycle occurs before VISUAL-IDENTITY-1.

058b must not implement 058d early. In particular it must not rename Lineage into a process flowsheet, add a Process canvas, invent node/stream semantics, or persist process topology.

If `docs/specs/STATUS.md` still lacks the 058d row after 058b reconciliation, the next authorized step is the small docs-only queue re-derivation/registry insertion required by the maintainer before any 100 definition/runtime work.

## 23. Definition acceptance

This definition is ready to merge when:

- it has been reviewed against exact merged 006b/071b/058c/088/089 authority;
- it establishes one read-only comparison surface rather than a second state/analytics system;
- result comparability remains owned by 089;
- no runtime/schema/provider/store mutation is included;
- deterministic gates are green on the immutable definition head;
- an independent exact-head review finds no material P0/P1/P2;
- `058b` remains `planned` until separate readiness merges and is reconciled.
