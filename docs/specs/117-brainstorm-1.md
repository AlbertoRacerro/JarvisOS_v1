# 117 BRAINSTORM-1

Status: full specification / readiness candidate

Exact re-derivation base: `ecd957f44ca1420dfb2e7e9894b7046b35ea7774` (`master`, after canonical 022 and 116 reconciliation).

Governing definition authority: `docs/specs/100c-queue-rederivation-2026-08-28.md`. Live implementation authority remains `docs/specs/STATUS.md`; product implementation is forbidden until the 117 row is explicitly `ready` on canonical `master`.

## Outcome

Provide one canonical Brainstorm capability inside the existing Development workspace that preserves captured RAW ideas immutably, records explicit NEW/DISCUSSED/RECONCILED/SUPERSEDED lineage, maintains revisable reconciled understanding with exact discussion/source provenance, and creates bounded promotion proposals to Roadmap, Design and Coding. Brainstorm must not become a second Roadmap, project-model store, Coding queue, AI thread store, generic notes system, or hidden target-domain commit path.

## Current owner evidence and selected owner

Fresh master already reserves `/development/brainstorm` in the final operator route/navigation composition. `frontend/src/App.tsx` still exposes the Brainstorm route truthfully as unavailable; `frontend/src/app/routes.ts` and `backend/app/modules/ai/jarvis_context_models.py` already recognize the route identity. There is therefore no need for a second route or frontend-owned state.

Fresh owner inspection also shows:

- `backend/app/modules/development/` is the existing server-side Development domain owner established by 116, with workspace-scoped typed API/service code, optimistic revision checks and durable redacting event evidence;
- `backend/app/modules/events/` is audit evidence, not mutable Brainstorm truth;
- MemoryStore proposal surfaces are specific to their existing memory record kinds and are not a generic downstream-domain proposal store;
- AI Threads may provide exact discussion/message provenance but must not become Brainstorm persistence;
- 111 owns generic explicit Jarvis context mechanics, while 122 owns later Development-domain Jarvis proposal/context actions.

The minimum owner is therefore one additive Brainstorm subdomain under the existing `backend/app/modules/development/` boundary, using the existing SQLite/data-root and event-audit infrastructure. It is the single Brainstorm truth store. No second database, event-sourced owner, generic workflow engine, AI-thread store, MemoryStore duplication or frontend persistence is authorized.

## Persistence contract

Use the next additive schema identity after current `0019_roadmap_calendar`: `0020_brainstorm`.

Implementation may organize the statements in the existing modular schema style, but the durable model must expose these exact logical records:

1. `brainstorm_raw_records`
   - stable `id`, `workspace_id`, immutable original `content`, immutable exact `attachment_refs` projection, `created_by`, `created_at`;
   - mutable lifecycle metadata is separate from original content and may only express `NEW | DISCUSSED | RECONCILED | SUPERSEDED`;
   - no API may replace original content or attachment identity after successful creation.
2. `brainstorm_ideas`
   - stable reconciled idea identity, current server-owned revision number, current lineage state, current revision pointer and optional exact superseding idea/revision identity;
   - revision changes use optimistic CAS.
3. `brainstorm_revisions`
   - immutable `(idea_id, revision)` snapshots containing title/takeaway/synthesis plus exact source/provenance refs and timestamps;
   - later reconciliation appends a new revision; it never overwrites an older revision.
4. `brainstorm_promotions`
   - stable proposal identity, exact source idea/revision, target enum `roadmap | design | coding`, proposal payload/digest, proposal state and downstream handoff identity when one exists;
   - this is proposal evidence only. It cannot itself create/update a Roadmap item, mutate Design, write repository files, execute code or mark downstream work accepted.

Attachment refs are exact references to already-owned file/artifact identities. Baseline 117 stores no duplicate binary/media payload. Missing, malformed or cross-workspace attachment refs fail closed.

Discussion provenance is an exact typed source manifest over canonical identities available at mutation time (RAW ids, prior Brainstorm revisions, exact AI-thread/message refs where used, and exact file/context refs). Generated synthesis text is not source authority by itself.

## State and lineage invariants

- RAW original content/attachment identity is immutable after creation.
- `DISCUSSED` means discussion evidence exists but useful content need not yet be consolidated.
- `RECONCILED` means an exact reconciled revision incorporates the RAW/source material.
- `SUPERSEDED` preserves history and names an exact successor; it is never deletion.
- one reconciled idea may acquire later immutable revisions; the stable idea identity does not change.
- supersession must reject self-links, cycles, missing successors and cross-workspace successors.
- reconciliation sources must exist in the same workspace and cannot silently resolve stale/current identities.
- a promotion is bound to an exact source revision. A stale or superseded source cannot silently promote as if current.

## API and CAS contract

The accepted server surface is workspace-scoped beneath the existing Development router. Exact path naming may follow current FastAPI conventions, but the semantic operations are frozen:

- create RAW capture;
- list/get RAW captures and their state/provenance;
- record discussion provenance for an exact RAW/idea identity without rewriting RAW;
- create a reconciled idea or append a reconciled revision from an exact source manifest;
- supersede an exact idea/revision with an exact successor;
- list/get reconciled ideas, immutable revisions and lineage;
- create/list promotion proposals for `roadmap | design | coding`.

Every mutable request carries the workspace identity and, for an existing mutable head, the exact server-owned `expected_revision`. The service verifies the revision again in the same transaction before mutation. A stale token returns a deterministic conflict and performs zero partial writes. Unknown fields/actions/states/targets, malformed source manifests, missing/cross-workspace refs and oversized payloads fail closed before commit.

Create operations must include a bounded idempotency key (or an equivalent deterministic request identity persisted transactionally) so retry-after-timeout cannot silently duplicate RAW records, reconciliation revisions or promotions. Reuse with a different payload fails closed.

All accepted writes emit redacting `events` evidence with workspace, actor, target identity, resulting revision/state and bounded field/digest metadata. Events remain evidence only and are never the Brainstorm read authority.

## Authority mapping

The immutable action classes from the 100c ownership audit remain `PRESENTATION | READ | CONTEXT | PROPOSE | COMMIT | EXECUTE | NAVIGATE`.

For Brainstorm:

- RAW capture and explicit reconciliation/supersession acceptance are 117 `COMMIT` inside Brainstorm only;
- Brainstorm reads/lineage inspection are 117 `READ` plus existing 100f/100g `PRESENTATION`;
- opening/reading never changes Jarvis context;
- explicit Jarvis context basket mechanics remain 111 `CONTEXT`, with Development-domain admissibility/actions deferred to 122;
- Jarvis-generated reconciliation remains 122 `PROPOSE`; acceptance of that proposed Brainstorm change remains 117 `COMMIT`;
- Add to Roadmap creates a 117 promotion proposal whose downstream acceptance is 116 authority;
- Promote Design creates a 117 proposal for the accepted Design owner at implementation time and never mutates Design directly;
- Promote Coding hands proposal identity into the existing 120/123 development-proposal lifecycle and never writes repository files directly;
- speech capture is `DEFER_TRIGGERED` and has no baseline 117 execution path.

This follows `docs/audits/100c-final-capability-interaction-ownership-f50eb0a.md`, including the explicit Brainstorm owner table and cross-surface rule that promotion reaches Roadmap/Design/Coding only through authority bridges.

## Product-direction and visual authority

Applicable product/interaction sources are:

- `docs/product-direction/03-project-memory-and-development-contract.md`;
- `docs/product-direction/08-final-visual-product-contract.md`;
- `docs/spec-drafts/FINAL_OPERATOR_CAPABILITY_MATRIX_2026-08-27.md` (Brainstorm reconciliation/proposal and promotion rows);
- `docs/design-references/FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md` (the seven action classes and context-neutral browsing rule);
- `docs/spec-drafts/FINAL_VISUAL_IMPLEMENTATION_PACK_2026-08-27.md`, FV-B10/FV-F08;
- `docs/design-references/development-beta/DEVELOPMENT_BETA_APPROVED_2026-08-27.md`.

Canonical repository HTML reference:

`docs/design-references/development-beta/development-brainstorm-beta-approved-2026-08-27.html`

At the exact re-derivation base its Git blob is `3aa529fa459919b4001091f4eb5c7bbcc59359a0`. The approved source identity recorded by the Development reference is SHA-256 `2b30f8d558045becf3c79b7d9a7bfcfd186a42a6278d92f53a0150be61f82631`; approved rendered reference SHA-256 is `faa74483fb5a7f084cdf8b9761c99c75f6d0cddeac78c864cc575cbd3691b9cd`.

Trusted Chromium proof uses desktop `1440x900` as the bounded acceptance viewport for the implementation route. Pixel identity is not required; semantics, hierarchy, usable controls and truthful unavailable states must match the accepted composition.

## UI activation boundary

117 replaces only the current truthful unavailable Brainstorm surface inside the existing Development shell. Canonical state is server-owned and reload must reproduce server truth.

Baseline active controls:

- RAW text capture;
- attachment selection only through exact existing file/artifact refs;
- RAW list and canonical lifecycle badges;
- compact reconciled list with inline expandable detail;
- discussion synthesis and exact provenance disclosure;
- reconciliation/revision and supersede actions with visible conflict failure;
- explicit `Add to Roadmap`, `Promote Design`, `Promote Coding` proposal actions showing proposal/pending identity rather than implied downstream completion.

Baseline inactive/deferred controls:

- microphone/record speech: visibly unavailable/future, owner FV-B22 after a bounded media/privacy path;
- Jarvis multi-record Development context/reconciliation assistance: 122;
- Roadmap acceptance/scheduling/time allocation: 116;
- Design-domain commit: accepted Design owner, never 117;
- Coding repository mutation/execution: 120/123 and later accepted Coding execution authority, never 117.

## Failure modes that block acceptance

Implementation must deterministically prove refusal without partial mutation for:

- attempted RAW content/attachment mutation;
- stale reconciliation or supersession CAS;
- missing/cross-workspace/malformed source or attachment refs;
- lineage self-link/cycle/invalid successor;
- stale/superseded promotion source;
- duplicate create/reconciliation/promotion retry with mismatched payload;
- direct target-domain COMMIT/EXECUTE through a promotion endpoint;
- hostile/unknown state, action or target values;
- malformed/oversized capture or synthesis payload;
- discussion-generated synthesis without exact provenance;
- frontend refresh/network failure that would otherwise leave local projection looking canonical;
- speech/media input reaching baseline 117.

## Deterministic implementation evidence

The implementation PR must add and pass, on its exact final head:

- `backend/tests/test_brainstorm.py`: immutable RAW, workspace isolation, lifecycle/lineage, revisions, provenance, promotion boundary, idempotency and stale-CAS cases;
- existing schema-current/migration tests updated for additive `0020_brainstorm` and restart persistence;
- `frontend/tests/117-brainstorm.mjs`: route composition, server-owned projection, active/deferred controls and no localStorage/browser-owned truth;
- exact-head backend deterministic suite relevant to Development plus `python scripts/check_spec_status.py` through normal CI;
- exact-head production frontend build;
- declarative `.github/browser-proof/plans/117-brainstorm.json` using the existing `jarvisos.browser-proof-plan.v1` toolbox, with no spec-coded controller primitive unless a concrete accepted interaction is otherwise impossible.

The trusted real-Chromium journey at `1440x900` must exercise at least:

1. open `/development/brainstorm` and create a RAW capture;
2. reload and prove original content/identity persists unchanged;
3. attach/record exact discussion provenance and create a reconciled revision;
4. expand the reconciled idea and inspect synthesis plus exact provenance;
5. append a later revision or supersede through valid lineage;
6. create one explicit promotion proposal and prove the UI reports proposal/pending state rather than downstream completion;
7. exercise one stale/rejected mutation and prove canonical state survives;
8. prove microphone/speech remains unavailable and ordinary reading did not silently alter Jarvis context.

## Non-goals

Baseline 117 does not add:

- speech/audio capture, transcription or media storage;
- a generic notes/wiki/document system;
- Board/Kanban or a second Roadmap store;
- direct Roadmap acceptance/scheduling, Design mutation, repository/file mutation or code execution;
- a new AI thread/conversation store;
- autonomous/background reconciliation or promotion;
- semantic/vector search;
- generic workflow/orchestration machinery;
- provider/egress/credential authority or frontend secrets.

## Readiness decision

The required kernel, exact current owner boundary, additive persistence shape, API/CAS/idempotency rules, downstream proposal authority, applicable product/action contracts, exact visual artifact identity, deterministic tests, browser proof and deferred-owner map are now frozen.

Hard dependency `111` is merged. No missing human credential, destructive authority or unresolved architecture choice remains for this bounded slice. After this planning PR changes the canonical 117 row from `planned` to `ready` and merges, implementation may begin on exactly one recovered/new implementation PR. Until that registry transition lands on `master`, product implementation remains unauthorized.