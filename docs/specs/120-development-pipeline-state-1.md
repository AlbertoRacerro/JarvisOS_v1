# 120 — DEVELOPMENT-PIPELINE-STATE-1

## Definition

### Objective

Expose one inspectable, read-only development-pipeline projection for a concrete JarvisOS pull request so an operator can answer, from exact repository evidence, where that change is in the accepted delivery sequence:

`Proposal → Plan → Implementation → Tests → Independent Review → Reconciliation → Merge`.

The projection is evidence, not authority. It must make stale or missing evidence explicit and must never create a second roadmap, queue, planner, review authority, or merge actor.

### Existing owners to reuse

- `docs/specs/STATUS.md` remains the sole live roadmap/work-state authority. 120 must not mirror or persist its own lifecycle state.
- Spec 118 `CODING-REPOSITORY-TRUTH-1` remains the sole server-side GitHub repository/PR/check/review truth owner. 120 derives from its exact repository/ref/PR/check/review reads rather than creating another GitHub transport or credential boundary.
- Existing deterministic CI, `Manual Expert Review`, PR metadata/comments and the canonical post-merge reconciliation mechanism remain the evidence producers. 120 only projects their observable state.
- Existing merge and ChatGPT writer/mutex policy remain unchanged. A 120 response cannot authorize mutation.

### Bounded product boundary

120 owns a stateless, exact-evidence projection for one configured repository pull request. The implementation may expose the seven named delivery stages and their evidence/freshness, but it must not invent additional workflow stages or infer semantic acceptance from prose alone.

At minimum the projection must distinguish:

- evidence that is exact for the currently observed PR head/base/ref;
- evidence that is absent, partial, non-terminal or stale;
- deterministic tests/checks versus independent semantic review;
- an implementation PR versus a later mechanical reconciliation PR where that distinction is provable from canonical repository evidence;
- a merged PR versus an open/closed-unmerged PR;
- uncertainty when provider evidence cannot prove the requested state.

A head/base/ref move invalidates evidence whose identity no longer matches. Older green checks, reviews or reconciliation evidence must not silently remain current after the change they certify moves.

### Authority and safety invariants

1. **Read only.** No branch/file/status mutation, workflow dispatch, label mutation, review request, merge, auto-merge, reconciliation creation, service control or local Git execution.
2. **No second queue/store.** No database, cache, background poller, durable pipeline ledger or shadow roadmap. Fresh provider/canonical evidence is re-derived on demand.
3. **Exact identity.** Any non-unknown stage classification is bound to the exact PR/head/base/ref evidence that proves it. Stale evidence degrades explicitly rather than being carried forward.
4. **No semantic fabrication.** A successful workflow is test/execution evidence only. Independent review is satisfied only by the repository's accepted consumable exact-head review evidence; comments/titles cannot create approval by convention alone.
5. **No hidden authority.** The projection cannot decide readiness, request review, reconcile STATUS, or merge. It reports observable state and blockers only.
6. **Conservative uncertainty.** Provider failure, contradictory evidence, unsupported historical forms, missing exact identity or ambiguous process evidence yields an explicit unknown/unavailable result rather than optimistic completion.
7. **Bounded disclosure.** Reuse 118 disclosure/redaction/bounds; do not expose credentials, arbitrary provider payloads, local paths, or unbounded logs/comments.

### Stage semantics to freeze in full spec

The full spec must define deterministic evidence rules for each named stage without turning conventions into a second authority model. In particular it must resolve:

- which existing exact repository artifacts can prove Proposal and Plan without inventing a parallel planning store;
- how Implementation is associated with the exact implementation PR and canonical spec gate when applicable;
- which required deterministic check set and terminal conclusions prove Tests for the current head;
- the exact consumable evidence required for Independent Review and how head/base changes invalidate it;
- how a separate mechanical reconciliation PR is detected and related to the implementation merge without semantic inference;
- how Merge is reported for the exact implementation/reconciliation identities;
- representation of `pending`, `complete`, `blocked`, `stale`, `not_applicable`, and `unknown` (or a smaller equivalent closed vocabulary);
- response bounds, provider failure mapping and deterministic acceptance fixtures.

### Implementation surface deferred to full spec/readiness

This definition does not authorize runtime code. Full spec/readiness must select the smallest route/service/schema and exact test files after revalidation against then-current 118 owners. Prefer a thin derived service over new provider logic. Frontend presentation is not part of 120 unless readiness proves an existing bounded Coding surface requires it for the registered acceptance target.

### Acceptance target

120 is complete when JarvisOS can inspect one concrete development change and return a deterministic, exact-head-safe, read-only explanation of the seven registered pipeline stages, including stale-gate invalidation and typed uncertainty, while all mutation/roadmap/review/merge authority remains with its existing owners.

### Non-goals

- no auto-merge, merge queue, merge bot or reconciliation actuator;
- no planner, second roadmap, Board store, issue/task tracker or persistent pipeline ledger;
- no new GitHub client/transport, credential, provider adapter or generic SCM abstraction;
- no local runtime/update/restart/PTY behavior from 119/125/126;
- no Jarvis coding actions from 123;
- no broad CI/review redesign, workflow cleanup or reviewer-policy change;
- no frontend redesign or unrelated operator-workstation work.

`STATUS.md` remains `planned`; this definition grants no implementation authority.
