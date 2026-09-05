# 140 CODING-FRONTEND-INTEGRATION-1

Status: definition only; planned; no implementation authority.

Base authority: exact `master` `04bbb5e7ddf4a2c2a91a5745e112af1eb0ccfa2a`.

## Problem

The Coding acceleration backend authorities are now merged: 118 owns remote repository/ref/SHA/PR/check/review truth, 119 owns local runtime identity and remote-alignment truth, 120 owns inspectable development-pipeline state, and 123 owns bounded Jarvis Coding READ/PROPOSE behavior. The existing operator frontend predates that completed backend chain and therefore needs one bounded integration slice so the Coding surface consumes those accepted server-owned contracts rather than placeholders or parallel client-side truth.

This definition creates planning authority only. It does not authorize product-code implementation. A full specification and readiness decision remain mandatory before `140` can become `ready`.

## Dependencies and owners

Hard dependencies for derivation are `091`, `100f`, `100g`, `111`, `118`, `119`, `120`, and `123`. The frontend shell/visual ownership established by 091/100f/100g is reused; 111 remains the context/action foundation; 118/119/120/123 remain the sole backend/domain authorities for the facts and actions they already own.

No new repository, runtime, pipeline, proposal, context, credential, provider, filesystem, or GitHub authority is created by 140.

## Bounded delivery target

A later accepted implementation may only wire the existing Coding/operator surface so that:

- `Coding -> Repository` consumes 118 server-owned truth for the selected repository/ref/exact SHA, bounded tree/file preview/search, available PR/check/review evidence, and safe GitHub URLs;
- `Coding -> Runtime` consumes 119 server-owned executed path/ref/SHA/dirty/build/runtime identity and its deterministic `aligned` / `local_behind` / `divergent` / `unknown` relation to the exact remote target;
- the existing Coding/operator surface exposes the relevant 120 proposal-to-merge pipeline-state projection without introducing a second queue, store, roadmap, or workflow authority;
- the Jarvis sidecar/surface exposes only the 123 Coding `READ` / `PROPOSE` capabilities, including inspect/explain/context and bounded Suggest modification proposal/diff/plan behavior bound to exact base SHA, target paths, context digest, and stale refusal;
- ordinary repository browsing remains context-neutral; explicit context insertion continues through 111/123 rather than silently adding browsed material to model context.

## Security and authority boundary

The browser must never call GitHub directly, receive GitHub/provider credentials, or gain filesystem authority. 140 must not add `COMMIT`, `APPLY`, `EXECUTE`, file mutation, branch creation, pull-request creation, merge, workflow dispatch, STATUS mutation, provider dispatch, PTY, or self-update authority.

Safe external links may be rendered only from server-validated URLs already supplied by accepted backend contracts. Stale/exact-head failures remain fail-closed and visible; the frontend may not infer success, freshness, mergeability, runtime alignment, or proposal validity from local state.

## Frontend boundary

Reuse the existing operator-workstation composition and Coding surfaces established by 091/100f/100g. No general frontend redesign, new global store, duplicate API client, or parallel Coding page architecture is in scope. A minimal causal correction to an existing shared frontend integration point is allowed only when the full spec proves it necessary to consume the accepted contracts.

## Controlled-parallel compatibility with 113

At this base SHA, active 113 is the Knowledge model-dossier slice: its runtime scope is the model-dossier backend/read projection and `/memory/models`. 140 is a Coding frontend-integration slice over already merged 118/119/120/123 authority. It requires no 113 schema, store, model-dossier route, `/memory/models` component, or model/evidence mutation. Shared frontend/client integration remains serialized by the global ChatGPT writer mutex.

Accordingly 113 may truthfully remain parked `in_review` on its accepted exact-head real-browser proof while 140 advances through planning. This does not permit 114 to start: 114 remains held until both 113 and 140 are merged and mechanically reconciled under current maintainer scheduling authority.

## Failure modes to freeze in the full spec

The full specification must at minimum close these failure modes without broadening authority:

- stale repository/ref/SHA displayed as current;
- local runtime identity compared against a different remote target;
- frontend-derived pipeline state diverging from 120;
- direct browser GitHub/provider calls or credential exposure;
- repository browsing implicitly entering Jarvis context;
- proposal submitted against a stale base SHA or mismatched target paths/context digest;
- UI affordances implying commit/apply/execute/merge authority that 123 does not grant;
- placeholder/fixture data surviving when server truth is available;
- duplicate global stores or API ownership created solely for the integration.

## Expected verification shape

Readiness must freeze deterministic frontend/API contract tests for exact identity propagation, stale refusal, context-neutral browsing, absence of unauthorized actions, and truthful empty/unknown/error states. Because this is visible operator behavior, readiness should require exact-head real-browser proof of the accepted Coding interaction unless fresh canonical evidence proves an existing deterministic browser-proof mechanism already covers the same behavior.

The later implementation remains independently reviewable and bounded to the accepted integration diff. No Hermes derivation, Knowledge 114+, Development 116+, Ruff-autofix, CI-digest, or unrelated cleanup belongs in this slice.
