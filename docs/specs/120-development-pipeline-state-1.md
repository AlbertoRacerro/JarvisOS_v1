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

## Full specification

### Request and response boundary

The implementation exposes one GET-only endpoint under the existing Coding router:

`GET /api/coding/pipeline-state?repository=<owner/name>&pr_number=<positive-int>&spec_id=<registry-id>`

`repository` must be in the server-owned `Settings.coding_repositories` allowlist. `spec_id` is caller-supplied lookup input only and grants no authority; the response is non-unknown only when canonical `STATUS.md` evidence associates that ID with the inspected implementation PR where association is required.

The response contains:

- `repository`, `pr_number`, `spec_id`;
- exact observed `head_sha`, `base_sha`, `head_ref`, `base_ref`;
- current canonical `master_sha` used for reconciliation/status projection;
- exactly seven ordered stage objects named `proposal`, `plan`, `implementation`, `tests`, `independent_review`, `reconciliation`, `merge`;
- each stage has `state`, `reason`, and a bounded evidence summary containing only exact identifiers/names/conclusions needed to explain the classification;
- overall `partial` and a bounded `warnings` list for typed uncertainty.

Closed stage-state vocabulary:

`pending | complete | blocked | stale | not_applicable | unknown`.

No stage state is a merge/readiness decision. `complete` means only that the frozen evidence rule below is satisfied.

### Repository-truth ownership and one necessary supporting read

120 constructs and calls `RepositoryTruthService` using `Settings.coding_repositories`; it creates no transport of its own.

Current 118 already owns PR, exact check-run, review and exact-file/ref reads. The V3.2 Claude reviewer publishes its consumable `JARVIS_CLAUDE_REVIEW_V3_2_JSON` marker as an issue comment rather than a submitted GitHub review. Therefore 120 may add exactly one bounded read operation to the existing 118 owner: `pull_request_comments_truth(repository, pr_number, expected_head_sha=...)`.

That supporting operation:

- uses the same fixed GitHub host, allowlist, budget, timeout, retry, redaction and exact-head stale check as 118;
- reads only `/repos/{repository}/issues/{pr_number}/comments?per_page=100`;
- projects comment id, author login and a body truncated to 8 KiB, with pagination represented as `partial=true`;
- returns no generic issue API and no mutation ability;
- is used by 120 only to validate the structured V3.2 marker and, when present, a mechanically generated reconciliation-PR body marker;
- never treats arbitrary prose as authority.

This is an extension of the existing sole repository-truth owner, not a second provider or credential seam.

### Canonical STATUS projection

120 reads `docs/specs/STATUS.md` through 118 at two exact identities:

1. the inspected PR head SHA, to validate an implementation PR's in-PR registry association;
2. the current exact `master` SHA, resolved once through 118 and re-resolved before returning, to report current post-merge reconciliation state.

Only the single exact Markdown table row whose first cell exactly equals `spec_id` is parsed. Ambiguous/missing/duplicate row parsing yields `unknown`; no fuzzy matching is allowed.

Accepted row fields used by 120 are only `Spec`, `Status`, `Implementation PR`, `Depends on`, and `Name`. The parser does not copy the queue into another store.

### Stage rules

#### Proposal

`complete` when the exact current-master STATUS row for `spec_id` exists and has a recognized lifecycle status. Missing/ambiguous row is `unknown`. The stage does not infer proposal quality from a PR title or comment.

#### Plan

`complete` when the canonical row demonstrates that planning/readiness authority has advanced beyond `planned` or, for an implementation PR, the exact PR-head row is `in_review` and names this PR. Because `STATUS.md` is the live readiness/work-state authority, 120 does not independently reconstruct definition/full-spec/readiness approval from historical prose.

`pending` when the current canonical row is still `planned`. `blocked` only when the canonical row itself is `blocked`. No other source may create those states.

#### Implementation

For the inspected implementation PR, `complete` when exact PR truth and the PR-head STATUS row agree that:

- the row's `Implementation PR` equals the inspected PR number; and
- the row status is `in_review` or `merged`.

If the PR head moved relative to the evidence used for the row/check/review reads, state is `stale`. Missing/contradictory association is `unknown`, not guessed from branch/title/body text.

#### Tests

120 uses 118 `check_truth` for the exact inspected head. It does **not** infer branch-protection requiredness and does not treat a partial collection as complete.

For the current JarvisOS deterministic pipeline, the minimum recognized deterministic gate names are `backend` and `evidence`; aliases are not guessed. Full exact-head CI may expose additional check runs, which remain evidence but cannot weaken these two minimum gates.

`complete` only when:

- check evidence is non-partial;
- exact-head non-stale `backend` and `evidence` check runs are present;
- both are terminal with conclusion `success`;
- no exact-head deterministic check run explicitly classified by the implementation as required is terminal in a failure/cancelled/timed-out/action-required conclusion.

If either minimum gate is non-terminal, state is `pending`; if terminal non-success, `blocked`; stale head is `stale`; incomplete/malformed/partial evidence is `unknown`.

Legacy commit-status contexts are not exposed by current 118. 120 therefore never claims to be a branch-protection/merge-policy oracle; absence of legacy-status evidence is a residual limitation and merge authority continues to use raw GitHub rules/gates.

#### Independent Review

Submitted GitHub review objects alone are insufficient because current Claude V3.2 publishes the accepted structured marker in an issue comment.

120 scans only bounded exact PR comments for the literal marker prefix `JARVIS_CLAUDE_REVIEW_V3_2_JSON:` and parses the immediately following JSON object. A marker is consumable only when:

- `schema == "jarvis.claude-review.v3.2"`;
- `head_sha` equals the currently inspected PR head exactly;
- `base_sha` equals the currently inspected PR base exactly;
- `verdict` is `APPROVE` or `REQUEST_CHANGES`;
- `findings` is a bounded list of objects with recognized `severity` and `disposition` values.

`complete` only for `APPROVE` with no finding whose disposition is `BLOCK`. `blocked` for `REQUEST_CHANGES` or any qualifying `BLOCK`. A marker for another head/base is stale evidence and cannot satisfy the stage. If no consumable exact marker is present, state is `pending` when a current review workflow/check is visibly non-terminal, otherwise `unknown`.

Ordinary comment prose, a workflow `success` conclusion without marker, self-review, and reviewer severity labels without structured disposition cannot satisfy this stage.

#### Merge

`complete` when exact PR truth reports `merged=true`. Open is `pending`; closed-unmerged is `blocked`. Provider uncertainty is `unknown`.

Merge does not depend on 120's Tests or Review classifications and 120 never declares merge eligibility.

#### Reconciliation

`not_applicable` while the implementation PR is not merged.

After implementation merge, `complete` when current exact-master STATUS row has `Status=merged` and `Implementation PR` still names the inspected PR. This canonical result is sufficient even if the exact reconciliation PR identity is unavailable.

When a bounded issue-comment/PR-body marker from the canonical mechanical reconciler can prove a separate reconciliation PR identity, 120 may include that exact PR number as supporting evidence; failure to discover that identity does not downgrade a canonical exact-master `merged` row.

If the implementation PR is merged but current-master STATUS remains `in_review`, state is `pending`. Contradictory association is `unknown`.

### Freshness protocol

One inspection uses this order:

1. fetch PR truth and freeze observed head/base;
2. fetch exact PR-head STATUS, check evidence, review/comment evidence;
3. resolve current `master`, fetch current-master STATUS;
4. re-fetch PR truth and re-resolve `master` before response construction;
5. if PR head/base or master moved, invalidate affected stages to `stale`/`unknown`; never silently mix snapshots.

No retry loop attempts to chase a moving target. One bounded revalidation is enough; caller may retry.

### Failure and disclosure rules

118 typed provider failures are mapped to stage `unknown` plus a safe reason code. Raw provider bodies, credentials, arbitrary comments, file contents outside the single STATUS row, local filesystem paths and exception text are not returned.

Maximum projected evidence:

- 100 check runs inherited from 118;
- 100 reviews/comments inherited from 118;
- one STATUS row per observed identity;
- at most 16 warning/reason strings, each at most 256 characters.

If any underlying 118 collection is partial, the dependent stage cannot be `complete` unless the missing tail is provably irrelevant under a rule above. Independent Review is never complete from a partial comments collection because a later blocking exact-head marker could exist.

### Implementation surface

Minimum authorized runtime files:

- `backend/app/modules/coding/repository_truth.py` — add only bounded PR-comment read operation;
- `backend/app/modules/coding/pipeline_state.py` — stateless parser/projector/service;
- `backend/app/modules/coding/runtime_routes.py` — add GET-only pipeline-state route to the existing Coding router;
- `backend/tests/test_development_pipeline_state_120.py` — deterministic injected-transport/service/route acceptance coverage.

`backend/app/main.py` requires no new router because the Coding router already exists. No config, schema, migration, database, frontend, provider credential or architecture-enforcement change is authorized unless a deterministic implementation failure proves it technically necessary.

### Deterministic acceptance matrix

The implementation test file must cover at least:

1. exact configured repository + matching PR-head `STATUS in_review` association -> Proposal/Plan/Implementation complete;
2. planned canonical row -> Plan pending and no implementation authority inferred;
3. blocked canonical row -> Plan blocked;
4. missing/duplicate/malformed STATUS row -> affected stages unknown;
5. PR-head row names another implementation PR -> Implementation unknown;
6. PR head changes during observation -> head-bound Tests/Review/Implementation stale and no false completion;
7. base SHA changes -> old review marker stale;
8. master ref changes during observation -> Reconciliation/current-master-dependent projection stale/unknown;
9. exact `backend` + `evidence` success -> Tests complete;
10. either minimum deterministic gate pending -> Tests pending;
11. either minimum deterministic gate terminal failure -> Tests blocked;
12. partial check collection -> Tests unknown;
13. old-head successful checks cannot satisfy Tests;
14. exact V3.2 `APPROVE` marker with zero BLOCK findings -> Independent Review complete;
15. exact `REQUEST_CHANGES` or BLOCK finding -> Independent Review blocked;
16. marker for wrong head or base -> Independent Review stale/unknown, never complete;
17. workflow success without consumable structured marker -> Independent Review not complete;
18. partial comments collection -> Independent Review unknown;
19. open PR -> Merge pending; closed-unmerged -> blocked; merged -> complete;
20. merged implementation + current-master STATUS still in_review -> Reconciliation pending;
21. merged implementation + current-master STATUS merged with same PR -> Reconciliation complete;
22. canonical merged row with another implementation PR -> Reconciliation unknown;
23. supporting comments operation rejects stale expected head before projecting comments;
24. comments projection is bounded, pagination is explicit partial, arbitrary prose never creates review approval;
25. route rejects unconfigured repository and non-positive PR/spec identifiers without provider dispatch;
26. route/service expose no mutation, dispatch, merge, workflow, label, local Git, filesystem-write, database/cache or provider-credential path;
27. existing `/api/coding/runtime-truth` behavior and 118 public operations remain unchanged.

## Readiness decision — 2026-09-04

### Exact-master revalidation

Readiness was derived after definition PR #538 merged into exact master `484177293a96ae3a6db9192b9d956975d4dd6f53`.

Fresh code confirms:

- `RepositoryTruthService` already owns the sole fixed-host public GitHub transport and exact configured-repository allowlist;
- `check_truth` and `review_truth` perform exact expected-head stale checks and bounded projections;
- `review_truth` exposes submitted reviews but not the issue-comment channel that currently carries the V3.2 structured Claude marker;
- current Claude review evidence is therefore unreachable to a product projection unless the existing 118 owner gains the one bounded PR-comment read frozen above;
- `runtime_routes.py` already owns the `/api/coding` router and constructs `RepositoryTruthService` from `Settings.coding_repositories`, so no new router/config/provider owner is necessary;
- `STATUS.md` remains the sole live lifecycle authority and 120 can parse only the requested exact row rather than mirror the roadmap.

### Failure-mode disposition

- **False review approval from workflow green:** closed by requiring the exact structured V3.2 marker.
- **Stale review/check evidence after head/base move:** closed by exact identity plus final revalidation.
- **False test completeness from partial check evidence:** closed by fail-unknown behavior.
- **Legacy commit-status visibility gap:** PARK, non-blocking for 120; projection explicitly is not branch-protection/merge authority and current 118 has no status-context owner.
- **Unresolved review-thread state unavailable from current REST reviews:** PARK, non-blocking; 120 does not claim thread-resolution completeness and merge authority retains its independent raw evidence gate.
- **Second repository/provider owner:** closed by extending only `RepositoryTruthService` with one bounded read operation.
- **Second roadmap/store:** closed by stateless exact STATUS parsing only.
- **Comment/prose spoofing:** closed by exact schema/head/base/verdict/findings parsing; arbitrary prose is ignored.

### Minimum-necessary test

Criterio di accettazione: expose one inspectable exact-evidence seven-stage development projection.

Questo lavoro serve a soddisfarlo? **sì**.

Il criterio è raggiungibile senza il bounded PR-comment read? **no** — current independent Claude evidence is emitted as a structured issue comment and is not present in submitted-review truth. Reusing the existing 118 transport with one exact operation is smaller than a second client/provider or a review-system redesign.

### Readiness verdict

**READY after this planning PR merges and the live registry row is mechanically transitioned from `planned` to `ready`.**

No runtime implementation is authorized while `STATUS.md` remains `planned`.
