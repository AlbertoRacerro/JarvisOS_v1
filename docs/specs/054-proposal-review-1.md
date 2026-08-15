# 054 — PROPOSAL-REVIEW-1

**Definition status:** complete definition; registry remains `planned` until a separate readiness decision.

**Derived from:** exact `master` `2fc8250bcd2ed8c249136ca12816dcdbd2e1249c` after merged/reconciled 089 ANALYTICS-DOCK-1.

**Depends on:** 040, 041, 083, 035, 087.

## Goal

Replace the APP-SHELL-1 Review placeholder with one bounded workspace-scoped proposal-review workbench over the existing MemoryStore proposal lifecycle. The operator must be able to inspect enough real proposal content and provenance to make an informed decision, explicitly accept or reject eligible proposals, and see the resulting canonical state without introducing a second proposal store, a second review engine, fake AI authority, or the blocked 062 grading surface.

The slice must preserve the central product invariant: model/calculation output is a proposal until an explicit user promotion succeeds through the existing backend authority.

## Current runtime truth

The current backend already owns proposal lifecycle in `backend/app/modules/memory/`:

- `GET /memory/proposals?workspace_id=...&status=...` lists assumption, parameter and decision records under the facade states `proposed|accepted|rejected|superseded`;
- `POST /memory/{record_kind}/{id}/promote` accepts an ordinary proposed record;
- `POST /memory/{record_kind}/{id}/reject` rejects a proposed record;
- configured Parameter replacements must use `POST /memory/parameter/{id}/promote-replacement`, which atomically accepts the replacement, supersedes the prior Parameter and records freshness invalidation;
- MemoryStore remains the only proposal transition authority;
- `ReviewStage.tsx` is currently an honest placeholder explicitly reserved for re-derived spec 054;
- App already owns the transient workspace id and passes it through `PrimaryStageProps`;
- 035 and 087 already provide engineering-record navigation and lineage/freshness context elsewhere in the shell.

One concrete contract gap exists: current `MemoryRecordRead` deliberately omits several persisted fields needed for meaningful review (for example Parameter value/unit/range/value-status/symbol/confidence, Assumption scope/confidence, and Decision rationale/linked-run). A review UI that hides those fields could induce an uninformed promotion. This slice may therefore make a narrow additive read-model expansion over existing columns. It may not add storage, lifecycle states, or new engineering truth.

## Authorized product behavior

### Workspace and selection

- Reuse App-owned `workspaceId`; do not create Review-local workspace authority.
- When no workspace is selected, show an explicit bounded empty/unavailable state and no stale proposal content.
- Proposal list, active filter and selected proposal are Review-local transient UI state only.
- Default view is `proposed`. The operator may inspect `accepted`, `rejected`, `superseded`, or all statuses for history, but only `proposed` records expose lifecycle actions.
- Ordering must be deterministic: newest `created_at` first, then stable record kind/id tie-breakers if timestamps collide.
- Workspace A→B→A and selection X→Y→X late responses must not overwrite current visible state. Use request generation plus identity, not identity alone.

### Proposal list and inspector

The Review stage must expose, using only backend-returned real values:

- record kind and status;
- a human label derived from title, parameter name, assumption statement, or bounded id fallback;
- origin (`ai_proposed`, `calc`, or legacy/user when visible in historical filters);
- created/updated/promoted timestamps when present;
- source AI job id or source reference when present, rendered as provenance text only unless an already-existing safe navigation target is proven at readiness;
- record-specific substantive fields required to judge the proposal:
  - Assumption: statement, scope, confidence, source reference, notes;
  - Parameter: name, symbol, value, unit, value status, value_min/value_max, confidence, source reference, notes, replacement target id when configured;
  - Decision: title, decision text, rationale, linked run id, notes.

Long/untrusted text is inert text, never HTML/Markdown execution. Null/unknown values render as explicit unavailable/not-recorded states rather than fabricated defaults.

The existing navigator region should carry the proposal list/filter. The primary Review stage should carry the selected proposal body and lifecycle actions. A compact sidecar contribution may show provenance/lifecycle metadata only if it materially improves inspection without duplicating the main body. Do not add a dock merely to fill space.

### Accept and reject

- `Accept` and `Reject` are explicit operator actions on `proposed` records only.
- Ordinary assumptions, decisions and non-replacement parameters use existing generic promote/reject routes.
- A Parameter with `supersedes_parameter_id` must use the existing `promote-replacement` route for acceptance; generic promote is forbidden for that case.
- Rejecting a configured replacement continues to use the normal reject route.
- The UI must not optimistically claim a transition. Keep the selected record visibly pending/busy, execute the backend mutation, then canonically reload the current proposal list and selected result before showing the terminal state.
- Disable duplicate mutation submission while the current mutation is in flight.
- If workspace or selection changes during a mutation, the late completion may not overwrite the new context. The backend mutation may already have succeeded; the UI must surface its result only after a canonical reload in the then-current context.
- Domain failures such as stale state, already-transitioned records, replacement conflicts, missing records, freshness-limit conflicts or network failures must remain visible and actionable; never convert them into success.

### Parameter replacement consequence

When `promote-replacement` succeeds, display the real response summary: accepted replacement, superseded parameter and freshness invalidation affected count/source/replacement refs. Do not compute or estimate additional impact in the frontend. 087 remains the authority for broader lineage/freshness inspection.

### Relationship to Engineering Data and Lineage

054 must compose with 035 and 087, not duplicate them:

- Review owns proposal decision workflow.
- Engineering Data owns broad record navigation/search.
- Lineage owns dependency/provenance/freshness overview.
- A bounded navigation handoff from Review to an existing Engineering Data or Lineage surface is allowed only if it uses existing route/selection contracts without introducing a new cross-stage identity taxonomy. Otherwise defer the handoff rather than creating an abstraction solely for 054.

## Minimum necessary backend read expansion

Readiness must inspect the exact current schema and freeze the smallest additive `MemoryRecordRead` expansion needed to expose persisted substantive fields already stored by 040/041/modeling. Expected additions are nullable/read-only and include only fields already present in the three source tables, such as:

- Assumption: `scope`, `confidence`;
- Parameter: `symbol`, `value`, `unit`, `value_status`, `value_min`, `value_max`, `confidence`;
- Decision: `rationale`, `linked_run_id`.

The expansion must be implemented by extending the existing union SELECT/model projection. No schema migration, new route, new table, new join-heavy aggregate, new event type, or new mutation semantics are authorized. Existing clients must remain compatible because all new response fields are additive.

If readiness proves current responses already provide all necessary facts through an existing safe endpoint without extra round trips or authority ambiguity, omit this backend change.

## Accessibility and responsive behavior

- Full keyboard operation for proposal list, status filters, Accept and Reject.
- Visible focus using 070 tokens; no color-only status communication.
- Mutation busy state is exposed semantically (`aria-busy` or equivalent) and actions remain understandable to screen readers.
- Focus recovery after a selected proposal disappears from the active filter must land on the next deterministic proposal, then previous, then the proposal-list heading/filter control; never disappear into document body.
- Effective 200% zoom / compact desktop must produce no page-level horizontal overflow. Long ids, source refs, notes and decision text wrap or use local bounded scrolling where technically appropriate.
- Respect `prefers-reduced-motion`; no new decorative motion is required.
- Preserve system/light/dark behavior from 070. The maintainer reference guides density and hierarchy, but this slice does not own global visual identity.

## Failure modes that must be proven

1. no workspace / empty proposal list;
2. workspace discovery or proposal-list failure without stale prior-workspace content;
3. A→B→A workspace late-response race;
4. X→Y→X selected-proposal/list refresh race;
5. unknown/null/additive backend fields without crash or invented meaning;
6. malformed or very long inert text without HTML execution or page overflow;
7. ordinary accept success and reject success followed by canonical reload;
8. double-submit prevention;
9. record transitioned elsewhere between list and action: backend conflict/error remains failure and canonical reload reconciles truth;
10. configured Parameter replacement uses only `promote-replacement`, and its real invalidation summary is shown;
11. replacement conflict/freshness failure does not claim acceptance;
12. selected record disappears from active filter after a successful transition with deterministic focus recovery;
13. workspace changes while mutation is in flight: no stale completion contaminates current context;
14. legacy Model/Results/Flowsheet, BLUECAD, Runs, Engineering Data, Analytics and Lineage surfaces remain reachable and unchanged outside the bounded Review integration.

## Expected implementation boundary

Readiness must re-read exact `master` and narrow the allow-list. The likely minimum set is:

- `backend/app/modules/memory/models.py` — additive read fields only if required;
- `backend/app/modules/memory/service.py` — matching SELECT projection only if required;
- `frontend/src/api/memory.ts` — typed MemoryStore read/mutation client;
- `frontend/src/stages/ReviewStage.tsx` — replace placeholder with workbench;
- one small Review-local state/helper module and deterministic harness only if race/focus logic is materially clearer and independently testable there;
- local CSS selectors in existing frontend style files only where needed for Review layout/containment;
- `scripts/check_proposal_review.py` — dependency-free conformance/preservation checker;
- `docs/specs/STATUS.md` only for lifecycle transitions during implementation.

Do not add a state library, query library, Markdown renderer, icon dependency, charting dependency, modal framework, backend aggregate route, polling loop, websocket, or generalized cross-stage store.

## Binding non-goals

- No 062 grade placement, choice, revision, withdrawal, stale-subject conflict or grade-derived routing behavior.
- No proposal generation, chat, AI call, provider call, rerun, repair or automated critique.
- No auto-accept/reject, bulk transition, policy promotion or approval delegation.
- No requirement-record proposal lifecycle; MemoryStore currently owns assumption/parameter/decision proposals only.
- No direct SQLite/filesystem/provider access from frontend.
- No second engineering-data browser or lineage graph.
- No global font/palette/component-grammar redesign.
- No new durable state, schema migration, dependency, workflow, credential, budget or egress authority.

## Acceptance criteria

1. `/review` replaces the placeholder with a real workspace-scoped proposal workbench using the existing shell and App-owned workspace id.
2. The default `proposed` list and optional historical filters render deterministic real MemoryStore records across assumption, parameter and decision kinds, with honest empty/loading/error states.
3. The selected proposal exposes all persisted substantive fields necessary for an informed decision; if the current read model is insufficient, the implementation adds only the frozen additive read fields over existing columns.
4. Ordinary proposed records can be explicitly accepted or rejected through existing MemoryStore routes; no non-proposed record exposes an enabled transition action.
5. Configured Parameter replacement acceptance can only call the existing `promote-replacement` route and surfaces the returned supersession/freshness-invalidation facts.
6. Every mutation uses canonical post-mutation reload; no optimistic terminal state or fabricated consequence is shown.
7. Request/mutation guards prevent stale A→B→A, X→Y→X and context-change completions from overwriting the active workspace/selection.
8. Keyboard, visible focus, screen-reader state, reduced motion and deterministic focus recovery satisfy the behavior above.
9. Effective 200% zoom and long-content fixtures produce no page-level horizontal overflow.
10. Untrusted proposal content is inert text and cannot inject executable markup.
11. Existing 035/087 surfaces and all previously merged primary stages remain behaviorally preserved; 054 adds no alternate authority/store.
12. 062 grading remains absent and untouched.
13. Exact-head deterministic checker(s), frontend locked install/build, repository CI, BLUECAD Real Tool Proof, and a browser proof covering the frozen matrix are green on one unchanged implementation head before merge.

## Readiness questions

Before implementation, readiness must freeze:

- exact additive MemoryRecordRead fields after inspecting current tables and serialization;
- exact frontend file allow-list and whether a state helper/harness is justified;
- whether safe existing cross-stage navigation can be reused without new taxonomy;
- deterministic ordering/focus fallback details;
- exact browser fixture strategy for AI-origin, calc-origin and Parameter replacement without live provider calls;
- preservation checker lifecycle so already-merged 083/035/087/088/089 gates do not falsely reject a legitimate later slice;
- rollback: removing 054 frontend client/stage changes and any additive read projection must restore the honest Review placeholder without affecting stored proposal truth.

Until that separate readiness decision is merged and registry row 054 is `ready`, runtime implementation is not authorized.