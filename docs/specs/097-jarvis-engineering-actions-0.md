# 097 — JARVIS-ENGINEERING-ACTIONS-0

Status: **definition-only; implementation not authorized**  
Date: 2026-08-22  
Derived from exact reconciled master: `54485a1cd86fc124df354c219f18f6cfa30ba0eb`  
Depends on: 071b, 091, 058c

## 1. Purpose

Add the first bounded authority for Jarvis to help the operator change the existing 071b working configuration without creating a second engineering state store, bypassing deterministic validation, or silently mutating canonical project data.

The product contract is:

```text
operator intent / deterministic blocker
             ↓
        Jarvis assistance
             ↓
 typed engineering action proposal
 target + preconditions + old → proposed + unit + basis
             ↓
 exact validation against current working configuration
             ├─ stale / invalid → fail closed or regenerate
             └─ valid
                  ↓
       explicit consent when required
                  ↓
       atomic working-state patch
                  ↓
     Properties updates immediately
                  ↓
      deterministic preflight reruns
                  ├─ not ready → report blockers, NO run
                  └─ ready → Run only on explicit run intent
```

097 turns Jarvis from a conversational advisor that can only describe engineering state into a controlled operator interface over the **same transient working configuration already owned by 071b**. It does not grant Jarvis ownership of the working state, project records, model authority, run history, lifecycle, or provider policy.

This definition freezes operator semantics and safety requirements. A separate readiness decision derived from exact then-current master must identify the minimum transport/API seam required to carry structured actions. No runtime implementation is authorized by this file alone.

## 2. Exact-master authority inventory

Fresh inspection of reconciled master shows the following current boundaries.

### 2.1 071b / 058c working-state owner

`frontend/src/components/engineering/EngineeringProperties.tsx` currently owns one transient working configuration and exposes existing direct operator mutations such as value edit, compatible Parameter selection, Undo, Revert field, Revert all, object-transition conflict handling, deterministic preview/preflight and Run start/retry.

The controller already has a monotonically changing local `revision`. Preview acceptance is guarded against stale revision/model responses. Object-semantic adoption from 058c is also guarded by selected workspace/candidate/artifact/viewer-session/semantic target and by an explicit dirty-target transition.

This is the state authority 097 must reuse. 097 may add a narrow validated patch/action seam around this owner; it may not create a Jarvis-specific duplicate binding map, Redux/store hierarchy, browser persistence layer or new canonical database simply to let chat change values.

### 2.2 091 Jarvis interaction owner

`frontend/src/components/ai/useJarvisSidecar.tsx` currently composes workspace-scoped 090 threads in the existing sidecar. It can create/select threads, preview bounded project context, submit free-text prompts through the canonical thread API, render durable snapshots/provenance and reject stale workspace/thread/route/selection responses.

Current submit is conversational only. The frontend sends `prompt` plus optional inspected context digest through `frontend/src/api/threads.ts`; current thread interactions expose assistant text, canonical flow state and proposal references, but no typed working-configuration action object.

Therefore implementation must **not** obtain mutation authority by parsing assistant Markdown/free text, matching phrases in rendered messages, scraping DOM content, or trusting an arbitrary JSON-looking substring produced by a model. If a structured action transport is necessary, readiness must freeze the smallest server-owned typed contract and its trust boundary from exact runtime.

### 2.3 App composition

`frontend/src/App.tsx` currently instantiates both `useJarvisSidecar(...)` and `useEngineeringProperties(...)` under the same App-owned workspace/selection context, then supplies Jarvis and Properties into the single 096 sidecar.

This is a useful composition seam but not by itself authorization to couple arbitrary chat output to state mutation. Readiness must choose the minimum explicit bridge that preserves one state owner and testable preconditions.

### 2.4 Preserved AI/provider authority

091/090/042/059b/061 retain canonical conversation, context, egress, budget, provider permission, flow and attempt authority. Product AI execution continues through the existing canonical server path; frontend code never calls providers directly.

Deterministic blocker discovery continues to belong to the existing model contract / preview / validator authority. A model does not decide whether a working configuration is ready to run.

## 3. State and authority model

097 preserves four distinct engineering states:

1. canonical project/model data;
2. mutable transient working configuration owned by 071b;
3. immutable execution snapshot created only after ready preflight and explicit Run intent;
4. persisted run results/evidence.

A Jarvis engineering action may mutate **only state 2** in this slice.

It may not:

- silently edit accepted Parameters, Assumptions, Decisions, Constraints or Specifications;
- write through to a linked source Parameter merely because Properties displays it;
- change BLUECAD candidate/source identity;
- promote proposals;
- archive/delete/supersede records;
- create variants/history objects;
- create a simulation run when preflight is not ready;
- reinterpret a failed run as a valid baseline;
- alter provider, budget, egress or sensitivity policy.

Canonical record lifecycle belongs to 098. Variants belong to 006b. Comparison belongs to 058b.

## 4. Two Jarvis output classes

Jarvis continues to support ordinary conversation. Engineering mutation adds a second distinct class: **structured engineering action**.

The UI and server contract must never treat ordinary assistant prose as an executable instruction merely because it contains a number, unit or imperative wording.

A structured engineering action must be machine-typed and validation-ready. At minimum, the conceptual payload has:

- stable action/request identity suitable for idempotent UI handling where needed;
- workspace identity;
- semantic target identity when an object is selected;
- active model/contract identity or precondition where needed;
- working-config revision/precondition captured at proposal time;
- one or more field/model operations;
- current/old effective value or model expectation;
- proposed value/model;
- exact contract unit for numeric values;
- basis/source classification;
- human-readable reason;
- confirmation requirement;
- optional explicit run intent, separate from mutation intent.

The exact persisted/transient representation is a readiness decision. This definition does **not** require a new database table or durable action ledger by default.

## 5. Deterministic blocker assistance

Deterministic preview/preflight owns blocker truth.

When current authoritative preview reports one or more blockers, Jarvis may surface a bounded proactive explanation such as:

```text
1 blocker prevents Run.
Bed void fraction is required by the active Ergun contract.

[Use previous successful value]
[I'll edit]
[Ask Jarvis for a suggestion]
[Other]
```

Whenever Jarvis presents a bounded typed choice set for a blocker, decision or engineering action, that choice set must include an explicit **`Other`** escape hatch. `Other` may collect operator-supplied alternative input, but selecting it is inert by itself: free text does not become an executable mutation until the alternative is converted into a separately typed, deterministically validated action under the same target/revision/atomicity/consent rules.

The blocker notification itself must not depend on successful provider execution. If Jarvis AI is unavailable, the deterministic blocker remains visible in Properties and may still be represented in the Jarvis area using deterministic local/server evidence.

Jarvis may explain authoritative blocker codes in operator language, but must not invent new severity or claim a condition is blocking when the validator does not say so.

## 6. Mutation classes and consent

### 6.1 Precise unambiguous operator command

A command such as:

`Set inlet pressure to 34 bar.`

may count as consent to apply that **specific working-state change** without an additional confirmation dialog when all of the following are true:

- target field resolves unambiguously in the current working context;
- exact unit is supported by the authoritative contract or the input is already in the exact contract unit;
- requested value is syntactically valid;
- no model choice or additional field is inferred;
- current target/model/revision preconditions still match at apply time;
- the resulting change remains Undo/Revert-able;
- canonical source records are not mutated.

Readiness must prove how a precise command becomes a typed action without heuristic frontend text parsing. If current canonical AI/thread contracts cannot guarantee this safely, the first implementation may require a structured action proposal/confirmation even for precise natural-language commands; it must not weaken safety just to match this ergonomic target.

### 6.2 Generic, inferred or multi-field request

Requests such as:

- `Fix the blockers.`
- `Use a better pressure-drop model.`
- `Restore the last successful values.`
- `Adjust the tube for this flow rate.`

require a structured preview before mutation whenever Jarvis must infer a value, select among alternatives, switch a model, or change multiple fields.

The preview must identify, for every operation:

- engineering target/field;
- `old → proposed` value/model;
- exact unit when numeric;
- basis/source;
- reason;
- whether the value is deterministic reuse or AI suggestion.

The operator confirms the whole action or rejects it. A future per-field partial-selection UI is not required here unless readiness proves it minimum; an action advertised as atomic must not silently apply only a subset.

### 6.3 Model choice

A model switch is always a semantic change and uses the authoritative 058c model-choice contract when one exists. Jarvis may never infer mutually exclusive models from prose/labels alone.

If a model switch changes which fields are active/required, the proposed action must expose the model transition and any explicit associated value changes. Retained inactive values remain governed by the working-state owner.

## 7. Provenance and basis classes

Jarvis actions must distinguish deterministic reuse from AI-generated advice.

Allowed operator-facing bases include only authority that can be proven at runtime, for example:

- `Current canonical value`;
- `Compatible linked Parameter`;
- `Previous successful run`;
- `CAD source` where current authoritative semantic source proves it;
- `User command`;
- `Jarvis proposal — AI suggested — not validated`.

A value generated or recommended by AI must be labeled exactly in substance as **AI suggested — not validated** until another explicit authority validates/accepts it. The UI must not call it measured, accepted, verified, validated, safe, optimal or recommended-by-evidence unless that separate evidence actually exists.

Opaque record IDs, flow IDs, request IDs and provider metadata remain Inspect/Audit rather than primary action text.

## 8. Safe-fix contract

`Apply safe fixes` is narrower than `Ask Jarvis to fix everything`.

It may automatically prepare/apply only operations whose proposed value and compatibility have a deterministic/credible existing basis, such as:

- restore a field from the current working baseline;
- reuse a known compatible previous successful-run value when exact model/contract/unit provenance is available;
- reuse an authoritative compatible linked source value without mutating that source;
- remove a local malformed working override by reverting to an already authoritative baseline.

It must not invent arbitrary numeric values simply to make blocker count reach zero.

If no deterministic basis exists, the blocker remains unresolved and the UI offers either:

- manual operator edit; or
- an explicitly labeled AI suggestion that requires confirmation.

A provider/model answer alone never upgrades an unsafe inferred fill into a `safe fix`.

## 9. Previous successful run assistance

097 may expose previous successful-run values only if exact runtime already provides or readiness authorizes the minimum truthful projection needed to prove:

- same workspace;
- compatible model/contract identity;
- exact unit compatibility;
- actual successful terminal run;
- exact source snapshot/value.

If exact current APIs cannot reconstruct these facts without broad new history infrastructure, previous-run automated restore remains deferred to 006b rather than approximated from UI history.

When available, a previous-run value is displayed with explicit provenance, not as a hidden default.

The explicit operator intent:

`Restore the last successful values and rerun.`

means:

1. prepare/validate a working-state patch;
2. apply only if current preconditions still match;
3. rerun deterministic preflight;
4. execute only if preflight is ready;
5. otherwise stop and report remaining blockers;
6. never promote the restored values to canonical project data.

## 10. Stale-action safety

Every action that can mutate working configuration is bound to the state it was derived from.

At minimum, preconditions include sufficient identity to detect:

- workspace change;
- model/contract change;
- working revision change;
- selected semantic object change where the action is object-specific;
- candidate/artifact/source change where 058c authority requires it;
- old/effective field value no longer matching the proposal expectation.

If any required precondition changes before apply:

- the action does not partially execute;
- the UI marks it stale/invalid;
- Jarvis may offer to regenerate it against current state;
- old proposal content remains non-authoritative historical conversation text only.

Late AI responses from an older workspace/thread/route/selection may be persisted by canonical 090 authority as appropriate, but they must not gain mutation authority over the new current working configuration.

## 11. Atomicity, idempotency and partial failure

A multi-operation action presented as one confirmed change-set is atomic from the operator perspective.

Implementation must choose one of these safe outcomes:

- all operations validate and apply to current working state; or
- none apply and the action reports the first/bounded validation failures.

No silent partial apply.

Repeated UI events, double click, route reopen or uncertain response must not apply the same change-set twice if a second application would create a different semantic result. Readiness must determine whether the transient frontend owner can provide sufficient local action identity/compare-and-apply semantics or whether a narrow server-owned idempotency seam is necessary.

Do not add a generic distributed transaction/idempotency framework unless exact runtime proves it necessary.

Because 071b working configuration is currently frontend-memory-owned, any server action contract must not falsely claim that the server committed a working-state mutation before the frontend owner actually adopted it.

## 12. One working-state owner and mutation adapter

097 must preserve a single source of working-state truth.

The preferred conceptual shape is:

```text
Jarvis structured action
         ↓
validated action adapter
         ↓
071b EngineeringProperties working-state owner
         ↓
existing revision / Undo / Revert / preflight
```

The action adapter may expose a narrow typed method such as `applyWorkingPatch(...)` from the existing owner if readiness proves this is the minimum seam. It must not bypass the owner by independently calling `setState`, maintaining a shadow action binding map, writing browser storage, or mutating a linked backend Parameter.

After successful apply:

- Properties immediately reflects the same effective values;
- dirty count/markers reflect the change;
- Undo/Revert can reverse it under the same working-state rules;
- working revision changes;
- any old preflight is invalidated;
- deterministic preview reruns.

## 13. Run intent remains separate

Mutation and execution are separate authorities.

Default behavior after a confirmed action:

- apply working-state patch;
- rerun deterministic preflight;
- if ready, optionally offer `Run now`;
- do not auto-run.

Jarvis may execute after mutation only when the operator's current explicit intent includes Run, for example `set pressure to 34 bar and run` or `restore last successful values and rerun`.

Even with explicit Run intent:

- non-ready preflight creates zero simulation run records;
- a real execution failure remains persisted as failed run evidence;
- successful execution may become working baseline under 071b rules;
- no successful run silently promotes canonical project records.

## 14. Conversation and action presentation

Jarvis remains conversational. Engineering actions must be visually distinct from ordinary text without becoming a second modal application.

A bounded action card/request may show:

- operator-readable target;
- action summary;
- old → proposed table/rows;
- unit;
- basis/source;
- reason;
- stale/current status;
- typed bounded choices when the action asks the operator to choose among alternatives; every such choice set includes `Other` as an escape hatch;
- Confirm / Reject / Regenerate / Undo where applicable.

Selecting `Other` opens operator-supplied alternative input but does not itself authorize mutation. The supplied text remains advisory/inert until it is converted to a separately typed action and passes the same deterministic validation, stale-precondition, consent and atomic-apply rules. `Other` must therefore never become a backdoor for executing free-form chat text.

Machine identifiers and exact precondition tokens belong under `Technical details` / Audit.

An action that has already been applied/rejected/staled cannot keep an enabled `Confirm` control after state changes.

Normal assistant prose around the action is advisory and inert.

No permanent 062 `Was this useful?` grading control is introduced.

## 15. Context boundary and provider safety

Jarvis action reasoning uses only context admitted through existing canonical context/execution authority.

The frontend must not send:

- raw complete application state;
- the whole Properties controller object;
- hidden DOM text;
- credentials/secrets;
- filesystem paths;
- arbitrary raw project databases;
- unbounded run history;
- uninspected Notes/scratchpad content.

If action generation requires current working values that are not currently part of the canonical context pack, readiness must define the smallest explicit, sensitivity-aware, bounded working-state context projection and how it is covered by existing 059b egress/budget policy. Do not simply append raw working state to a provider prompt in frontend code.

## 16. Deterministic versus AI-origin actions

Not every Jarvis action requires a provider call.

Deterministic UI/server logic may create action proposals from authoritative evidence where no model reasoning is needed, for example a `restore baseline` or exact compatible-value reuse action.

AI-origin actions continue through canonical AI flow. The structured action result must be validated after generation against current contracts and current working-state preconditions before it becomes confirmable.

A syntactically valid typed action from an AI model is still untrusted advisory input until deterministic validation passes.

## 17. Failure modes

Implementation/readiness must explicitly cover:

### 17.1 Provider unavailable

- deterministic blocker surfaces remain usable;
- manual Properties editing remains usable;
- deterministic safe fixes remain available where supported;
- AI suggestion controls report unavailable without changing state.

### 17.2 AI returns malformed/unsupported action

- ordinary assistant text may still render if canonical flow supports it;
- malformed action is inert;
- no partial mutation;
- no attempt to recover executable semantics by regex/Markdown parsing.

### 17.3 Action target disappears or changes

- fail closed as stale/unavailable;
- no fallback to display label or mesh ordinal;
- current 092 semantic identity rules remain authoritative.

### 17.4 Unit/model/contract drift

- fail closed before mutation;
- regenerate against current contract if desired;
- no frontend unit guess/conversion.

### 17.5 Working revision changes during generation

- proposal may display as stale context if useful;
- cannot be confirmed against newer state without revalidation/regeneration.

### 17.6 Confirmation response uncertainty

If implementation introduces any server-side state during confirmation, exact readiness must specify idempotent reconciliation. If working-state apply remains purely local, the UI must avoid claiming server commit semantics.

### 17.7 Run after action

- preflight non-ready → no run;
- create/execute uncertainty continues to use existing 071b request-key behavior;
- Jarvis must not add a second run execution endpoint.

## 18. Operate / Inspect / Audit requirements

### OPERATE

Primary action card shows engineering meaning:

- target label;
- current/proposed value/model;
- unit;
- basis;
- concise reason;
- blocker resolved/remaining when authoritative;
- Confirm/Reject/Run-now controls as applicable.

### INSPECT

May show:

- linked source identity;
- previous-run provenance;
- formula/model/dependency evidence already owned by 058c;
- validator/preflight reason codes translated without changing semantics;
- whether action was deterministic or AI-origin.

### AUDIT

Collapsed technical details may show:

- semantic IDs;
- working revision/precondition token;
- thread/interaction/flow/request IDs;
- exact contract digest;
- raw typed action payload where safe and bounded.

Raw JSON must use bounded internal scroll and never dominate the normal sidecar.

## 19. Responsive, keyboard and accessibility

097 preserves the merged 096 Jarvis-over-Properties sidecar geometry.

At normal desktop:
- action cards live inside Jarvis scrollable transcript/content region;
- Properties remains independently scrollable and updates in place.

At effective 200% / compact width:
- existing `Jarvis | Properties` tab degradation remains usable;
- confirmation cannot require viewing two panes simultaneously;
- no page-level horizontal overflow.

Keyboard requirements:

- action controls reachable in logical order;
- Enter/Space activation follows normal button semantics;
- focus does not jump unexpectedly when preflight refreshes;
- stale/failed action status is announced accessibly without stealing focus;
- after confirmation, focus lands on a stable action status/control or remains predictable;
- Undo remains keyboard reachable.

Reduced-motion, light/dark/system semantics and hostile-text inert rendering remain inherited.

## 20. Implement-now versus prepared-not-implemented

### Implement in 097

Subject to exact readiness proving minimum seams:

- structured engineering action representation;
- deterministic validation against current 071b/058c contract and working revision;
- action preview/confirmation presentation;
- exact-command path only if it can be typed safely without heuristic parsing;
- deterministic blocker assistance and safe-fix classification;
- bounded AI-origin proposal flow through canonical AI authority;
- atomic working-state apply through the single 071b owner;
- stale action rejection/regeneration;
- immediate Properties/dirty/Undo/preflight update;
- explicit separate Run intent.

### Prepared but not required in 097

- previous-successful-run restore when current exact runtime cannot expose a truthful compatible snapshot without broad expansion;
- richer per-field partial approval of multi-field actions;
- bulk `apply to similar selected objects`;
- spreadsheet/dense editing;
- model/tool agent controls beyond actual authority;
- durable engineering-action history beyond existing conversation/run evidence.

### Explicitly deferred

- canonical engineering-record write/lifecycle semantics: 098/101 as ordered by current canonical queue;
- variants: 006b;
- comparison/history: 058b;
- global visual identity: 100;
- Engineering Evidence Contract: 102;
- process stack changes/evaluators: 103+;
- Notes/scratchpad;
- 062 grading UI;
- Hermes/MCP frozen lanes 066–068;
- 080 review-repair.

## 21. Non-goals

097 does not authorize:

- a second conversation engine;
- a second working-configuration store;
- autonomous background optimization;
- agent loops that repeatedly mutate/run until success;
- direct provider calls from frontend;
- arbitrary tool execution from chat;
- new secrets/credentials/provider routes;
- broad schema migration merely for action history;
- canonical project-record mutation;
- proposal promotion/rejection redesign;
- record delete/archive/supersede;
- hidden unit conversion;
- frontend-invented model/formula/domain validity;
- mesh/name/color/bounds fallback identity;
- auto-run after every successful patch;
- auto-fill arbitrary numbers to eliminate blockers;
- unsafe parsing of natural-language/Markdown as executable mutation;
- global UI restyling.

## 22. Expected minimum implementation boundary

Definition does not freeze exact files beyond current ownership signals. Readiness must inspect exact current master and produce an allow-list.

Likely existing seams to consider:

- `frontend/src/App.tsx` only for minimum composition between current Jarvis and EngineeringProperties owners;
- `frontend/src/components/engineering/EngineeringProperties.tsx` for one typed validate/apply patch seam on the existing owner;
- `frontend/src/components/ai/useJarvisSidecar.tsx` for action presentation/orchestration without a shadow state store;
- `frontend/src/api/threads.ts` only if current 090 read model gains a bounded structured-action projection;
- existing backend 090/thread/AI task modules only if readiness proves a typed structured-action server seam cannot safely be represented through existing canonical output/proposal authority;
- focused tests/browser evidence.

Any new database table, durable store, provider route, generic command bus, global state framework or new runner endpoint is presumptively out of scope and requires explicit readiness proof of minimum necessity.

## 23. Deterministic acceptance criteria

Implementation is acceptable only when all applicable criteria are proven on one exact immutable head.

1. Properties and Jarvis mutate the same 071b working configuration; no duplicate working-state owner exists.
2. Ordinary assistant text cannot mutate engineering state, including JSON-looking or command-like hostile text.
3. A valid typed single-field action applies only when workspace/model/target/revision/value preconditions still match.
4. Applying an action updates Properties immediately, increments/changes working revision, marks dirty state and remains Undo/Revert-able.
5. A stale proposal after manual edit, model switch, workspace change or semantic target change cannot overwrite newer working state.
6. A multi-field action is atomic/fail-closed; deliberately invalidating one operation proves zero partial apply.
7. AI-generated numeric advice is visibly `AI suggested — not validated` and requires confirmation before apply.
8. `Apply safe fixes` never fills an ungrounded required numeric field with a fabricated value.
9. Deterministic blocker notification remains usable with provider execution disabled/unavailable.
10. After patch, deterministic preflight reruns; old ready preview cannot authorize a later revision.
11. Patch alone never creates a simulation run.
12. Explicit patch+Run intent executes only after ready preflight; invalid preflight creates zero run records.
13. Existing 071b create/run retry idempotency remains the sole execution-start path; 097 adds no alternate runner endpoint.
14. Linked canonical Parameter/CAD source remains unchanged after working override unless a later explicit lifecycle/write authority is invoked outside 097.
15. Frontend tests/network inspection prove no direct provider calls.
16. Workspace/thread/route/selection races cannot cause late AI/action responses to mutate current state.
17. Effective-200%, keyboard/focus, theme/reduced-motion and no-global-overflow behavior remain valid.
18. Hostile user/model strings render inertly and cannot create executable action controls without typed validated action data.
19. Raw action/audit payload remains bounded/collapsed.
20. Every bounded typed blocker/decision/action choice set includes `Other`; choosing `Other` leaves operator-supplied alternative text inert until it becomes a separately typed, deterministically validated action, and free text cannot mutate working state through this escape hatch.
21. Repository CI, spec-status gate and BLUECAD proof remain green on the exact implementation head.

## 24. Required browser/adversarial matrix

Readiness must turn these into reproducible exact-head browser/evidence cases.

1. Single precise typed action → valid current revision → working value changes, dirty/Undo/preflight update.
2. Action proposed → manual Properties edit → Confirm old action → stale rejection, no overwrite.
3. Action proposed on object A → select object B → old Confirm cannot mutate B.
4. Action proposed in workspace A → switch B → late result/confirm cannot mutate B.
5. Action proposed for model X → switch model/contract → stale rejection.
6. Two-field action where field 2 becomes invalid → neither field applies.
7. AI suggestion for missing numeric blocker → label `AI suggested — not validated`; no mutation before confirmation.
8. Deterministic safe fix with valid existing basis → apply without provider dependency.
9. Missing blocker with no deterministic basis → `Apply safe fixes` leaves it unresolved.
10. Provider unavailable → blocker/manual editing/deterministic safe fixes remain functional.
11. Hostile assistant text containing fake JSON/HTML/`set x=...` → inert text only.
12. Double Confirm / repeated UI event → no double semantic mutation.
13. Confirm patch → preflight non-ready → zero run created.
14. Explicit patch-and-run → ready preflight → existing runner path exactly once.
15. Explicit patch-and-run → response-loss/retry condition → existing 071b request identity reconciles; no duplicate run.
16. 200%/compact sidecar tab mode → action confirmation and Properties result remain reachable without horizontal overflow.
17. Keyboard-only confirmation/rejection/Undo; focus stable across preflight refresh.
18. Theme/system/reduced-motion and long engineering labels/units/reasons.
19. Bounded typed choice request exposes `Other`; selecting it accepts operator alternative input but performs no mutation, and hostile/command-like text entered there remains inert until separately typed and validated.

If previous-successful-run restore is authorized by readiness, add exact compatibility/stale provenance cases before implementation.

## 25. Migration, legacy and rollback

097 should require no migration by default because working configuration is transient and existing thread/run/project authority remains intact.

Historical 090 interactions without structured actions remain ordinary conversation and render normally. They must never be retroactively parsed into executable actions.

If readiness proves a small additive structured-action persistence/projection is necessary, legacy rows without that field must remain readable and inert; no migration may reinterpret old assistant prose as an action.

Rollback removes 097-specific action composition/validation/presentation while preserving:

- 090/091 threads and transcript history;
- 071b working configuration and manual editing;
- 058c semantic object/property contracts;
- existing preflight/run authority;
- canonical project data and run evidence.

Rollback must not require rewriting canonical project records or historical runs.

## 26. Readiness questions — mandatory before implementation

A separate exact-master readiness record must answer all of the following from current code/runtime evidence.

1. What is the smallest typed action transport? Can an existing canonical AI/proposal output surface carry a structured action safely, or is one narrow 090/internal API projection necessary?
2. Where can a structured action be validated without duplicating the 071b working-state owner?
3. What exact 071b controller/app seam should expose compare-and-apply / atomic patch behavior?
4. Which identities/preconditions are required for model-level versus object-specific actions after merged 058c?
5. Can exact natural-language commands be converted to typed actions through current canonical server AI output without frontend heuristic parsing? If not, what ergonomic subset must be deferred?
6. Can deterministic blocker evidence be projected into Jarvis without any provider call and without duplicating validator logic?
7. Which deterministic bases are actually available now for `Apply safe fixes`?
8. Is previous-successful-run exact compatible snapshot retrieval already available? If not, defer restore semantics to 006b rather than adding broad history API work.
9. Does structured action generation require current transient working values to enter AI context? If yes, what is the smallest sensitivity-aware server-owned context projection under existing 042/059b authority?
10. Is any durable action persistence actually necessary, or can typed proposal data be transient while the existing 090 transcript remains durable?
11. How is double-confirm/idempotent apply proven with frontend-memory-owned working state?
12. Which exact files are allowed to change, and what additions would constitute unauthorized new state/provider/runner infrastructure?
13. Which deterministic/unit/browser tests prove no Markdown/text parsing path can mutate state?
14. How are action proposal/apply errors represented without conflating AI/provider failure, stale precondition and deterministic validation failure?
15. How does explicit `...and run` reuse the existing 071b preflight/create/run/retry path without a second execution route?
16. How are typed bounded choice requests required by 095 represented with an explicit `Other` escape hatch while guaranteeing that operator alternative free text remains inert until separately typed and validated?

If exact runtime cannot answer these safely within a bounded slice, readiness must reduce the implementation surface rather than invent a new generic command/action architecture.

## 27. Downstream seam

After 097 implementation merges and is registry-reconciled, the canonical queue proceeds to 098 ENGINEERING-RECORD-LIFECYCLE-0.

097 leaves 098 a clean boundary:

- 097 mutates transient working configuration only;
- 098 introduces explicit server-owned project record lifecycle/write actions;
- any future Jarvis request to persist/promote a working value into canonical project authority must go through 098/101-era explicit mutation contracts, never be smuggled into 097.

The remaining downstream order and all freezes in `STATUS.md` are unchanged.

## 28. Definition acceptance

This definition is complete when:

1. it is merged from exact current authority with no runtime mutation;
2. registry row 097 remains `planned` and Implementation PR remains `—`;
3. a separate fresh readiness decision is required before any 097 runtime code;
4. readiness is required to derive the exact typed action transport/allow-list from runtime rather than presuming a new schema/store;
5. every maintainer-approved 095 Jarvis action rule is represented as a testable contract or explicit deferral, including typed bounded choices with an explicit `Other` escape hatch whose alternative free text is inert until separately typed and validated;
6. 071b remains the sole working-state owner;
7. 058c remains the source of engineering object/model/property semantics;
8. canonical data mutation/lifecycle, variants, comparisons, Notes, 062 grading, visual identity and later engineering-stack work remain outside scope;
9. no free-text/Markdown parsing path is authorized for mutation;
10. exact-head deterministic gates and one independent review find no material P0/P1/P2 issue.