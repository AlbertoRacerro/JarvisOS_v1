# 117 BRAINSTORM-1

Status: planning/readiness draft — **not implementation authority**

Re-derived from exact `master` `ecd957f44ca1420dfb2e7e9894b7046b35ea7774` after canonical reconciliation of spec 022. Governing planning authority is `docs/specs/100c-queue-rederivation-2026-08-28.md`; live lifecycle authority remains `docs/specs/STATUS.md`, where 117 stays `planned` until every readiness obligation below is closed.

## Outcome

Provide one canonical Brainstorm capability under the existing Development workspace that preserves raw captured ideas immutably, makes discussion/reconciliation lineage explicit, and creates bounded promotion **proposals** into existing Roadmap/Design/Coding authorities. Brainstorm must not become a second Roadmap, project-model store, coding queue, AI thread store, or hidden domain commit path.

## Current-master owner evidence

Current master already reserves the visible `/development/brainstorm` route and Development `Roadmap | Brainstorm` navigation. `frontend/src/App.tsx` currently renders `FinalOperatorUnavailableSurface` for Brainstorm and explicitly states that no accepted persistence owner exists yet. The route identity is also already present in `frontend/src/app/routes.ts` and `backend/app/modules/ai/jarvis_context_models.py`. Therefore 117 must replace only that truthful unavailable surface after a server-side owner is accepted; it must not introduce a parallel route or frontend-owned truth.

The canonical approved visual reference remains:

`docs/design-references/development-beta/development-brainstorm-beta-approved-2026-08-27.html`

It visibly defines the intended RAW capture, NEW/DISCUSSED/RECONCILED/SUPERSEDED states, reconciled idea view, discussion synthesis/provenance, explicit promotion controls and a future-only voice affordance. The reference is presentation/design authority only; it does not define persistence or mutation authority.

## Accepted kernel from 100c

The implementation contract must preserve all of the following:

- immutable RAW identity and original content after capture;
- lineage states `NEW`, `DISCUSSED`, `RECONCILED`, `SUPERSEDED`;
- reconciled revisions rather than destructive rewriting of RAW content;
- explicit discussion-synthesis provenance linking synthesis/reconciliation to its exact source material;
- explicit promotion **proposals** to Roadmap, Design and Coding;
- speech capture excluded from baseline 117 and trigger-deferred;
- no second truth store and no hidden direct domain COMMIT authority.

## Proposed bounded ownership model

This planning PR does **not** yet freeze the persistence owner. The implementation must select the minimum server-side owner only after exact-current inspection of the existing file/event/proposal/decision and MemoryStore boundaries required by 100c. The selected owner must satisfy these invariants:

1. RAW capture receives a stable server-owned identity and immutable content after successful creation.
2. Later discussion or reconciliation appends lineage/revision records; it never rewrites the original RAW payload.
3. Every reconciled revision names its predecessor/source RAW records and stores deterministic synthesis provenance sufficient to reconstruct why the revision exists.
4. `SUPERSEDED` is a lineage relationship/state, not deletion of historical evidence.
5. Promotion creates a typed proposal targeted at an already-authoritative downstream owner. Roadmap acceptance remains 116 authority; Design/Coding acceptance remains their respective domain authority. 117 itself never commits those domains.
6. Browser state is a projection only. Reloading must reproduce canonical server truth; localStorage/React state cannot be authoritative.
7. Existing AI Threads/Jarvis surfaces may contribute discussion/context through accepted contracts but cannot become a second Brainstorm store.

## Required mutation semantics

Before readiness, the full spec must freeze exact request/response contracts and CAS/concurrency behavior for at least:

- create RAW capture;
- record/attach discussion provenance without mutating RAW;
- create reconciled revision from an exact source/revision set;
- mark a prior reconciled revision superseded by an exact successor;
- create a promotion proposal for `roadmap`, `design` or `coding`;
- read/list/search exact Brainstorm records and lineage.

Every write must be workspace-scoped, fail closed on stale expected revision where applicable, reject unknown action/state values, reject cross-workspace references, and produce durable audit/provenance. Retrying an already-accepted mutation must be either idempotent or return a deterministic conflict; duplicate semantic records must not appear silently.

## Failure modes that must be proven

- attempted mutation of existing RAW content;
- stale reconciliation against a superseded/currently changed revision;
- reconciliation whose source records are missing, cross-workspace or malformed;
- lineage cycle or self-supersession;
- promotion proposal whose source revision is stale/superseded;
- target-domain proposal attempting direct COMMIT/EXECUTE instead of proposal creation;
- duplicate submission/retry after timeout;
- malformed/oversized capture or synthesis payload;
- missing provenance for discussion-generated synthesis;
- frontend refresh/network failure causing local projection to disagree with server truth;
- hostile/unknown state/action strings;
- speech/media input reaching baseline 117 despite being deferred.

## UI boundary

The accepted visible composition is the existing Development workspace and approved Brainstorm reference, not a new peer application. Baseline implementation should activate only controls backed by accepted server contracts. Any reference control without a landed owner must remain visibly unavailable and name its deferred owner rather than becoming a fake local action.

The following visible semantics are required if implementation becomes ready:

- RAW capture and immutable RAW list;
- state badges reflecting canonical lineage state;
- reconciled revision list/detail with discussion synthesis and provenance;
- exact source lineage disclosure;
- explicit proposal controls to Roadmap/Design/Coding with proposal/pending state, never implied completion;
- Jarvis context interaction only through existing 111-style explicit context/proposal boundaries;
- voice/speech control unavailable or clearly future/deferred.

## Deterministic acceptance obligations

Readiness must name exact tests; implementation acceptance must include at minimum:

1. backend contract tests proving immutable RAW content and valid state transitions;
2. concurrency/CAS tests proving stale reconciliation/supersession fails closed;
3. lineage tests rejecting cycles, missing/cross-workspace sources and invalid successor relationships;
4. provenance tests showing reconciled synthesis points to exact discussion/source identities;
5. proposal-boundary tests proving all Roadmap/Design/Coding actions stop at typed proposal creation and cannot directly commit target domains;
6. idempotency/retry tests for capture/reconciliation/promotion writes;
7. migration/schema-current tests if persistence schema changes;
8. frontend tests proving reload reflects server truth and unavailable/deferred controls stay inert;
9. exact-head production frontend build;
10. trusted exact-head Chromium proof covering capture → discussion/reconciliation → explicit proposal, plus failure-state visibility for at least one stale/rejected write.

## Non-goals

Baseline 117 must not add:

- speech/audio capture, transcription or media storage;
- a generic notes/wiki/document system;
- a Board/Kanban or second Roadmap store;
- direct Roadmap acceptance, scheduling, Design model mutation, repository/file mutation or code execution;
- a new AI thread/conversation store;
- autonomous background reconciliation or promotion;
- semantic/vector search unless separately justified by evidence and authorized;
- generic workflow/orchestration machinery;
- a frontend token/credential path or provider bypass.

## Deferred owners

- Speech/voice capture: trigger-deferred capability FV-B22 after 117 with bounded media handling and canonical AI job/ledger inference path.
- Jarvis scheduling/reconciliation assistance and multi-record Development context: 122 JARVIS-DEVELOPMENT-ACTIONS-1.
- Roadmap acceptance/time allocation: 116.
- Coding file/repository mutation or execution: existing/future Coding development authorities, not 117.
- Design-domain commit: the accepted Design owner at implementation time, never Brainstorm.

## Readiness decision — OPEN

117 intentionally remains `planned` in this planning revision. Promotion to `ready` is not yet truthful because the following evidence is still missing from this document:

- exact selection of the existing server-side persistence/write owner after current-master inspection of file/event/proposal/decision/MemoryStore boundaries;
- exact schema/API/CAS contract and migration impact;
- applicable product-direction/capability-matrix/interaction-contract row citations and action classes;
- canonical visual reference Git blob/hash and the exact viewport(s) that trusted Chromium must prove;
- exact deterministic test files/commands and browser proof plan;
- explicit mapping of every active/inactive reference control to its landed or deferred owner.

The same planning PR should be extended to close those items. Only then may it change the canonical STATUS row from `planned` to `ready`; no product implementation PR is authorized before that transition and merged hard dependency 111 remains required.