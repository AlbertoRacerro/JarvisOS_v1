# 079 — AUTONOMOUS-DEVELOPMENT-LOOP-0: durable bounded development continuation

Status: full specification complete; `docs/specs/STATUS.md` remains authoritative and keeps 079 `planned`.

Depends on: 004, 017, 019, 022

Full-spec baseline: `9c3c8ce90a9048c1797f2560025790162012d423`

Authority and evidence:

- `079-autonomous-development-loop-source-evidence.md`
- `079-architecture-evidence-closure-2026-07-31.md`
- `079-architecture-source-evidence-2026-07-31.md`

## 1. Goal

Allow one already and explicitly authorized JarvisOS repository-development slice to continue safely across agent-session termination without repeated conversational `continue` prompts.

The v0 control plane may:

- reconstruct durable authority from GitHub;
- claim exactly one repository-wide development front;
- create one derived work branch from an exact authorized base;
- invoke one bounded implementer on that branch;
- create or reconcile one exact-head pull request idempotently;
- collect deterministic gates tied to the exact work head;
- invoke one independent reviewer;
- perform at most two bounded finding/fix/re-review rounds;
- recover from duplicate delivery, process restart, stale local state, and ambiguous API responses;
- present a fully evidenced pull request to the maintainer;
- release a fully reconciled terminal front back to canonical `idle` without erasing history.

The control plane may never merge, enable auto-merge, approve authoritatively, change priority, create a second active front, infer authorization from activity, or turn model output into repository authority.

## 2. Full-spec boundary

This document freezes the v0 contract for:

- canonical state and event encoding;
- explicit authorization, expiry, revocation, recovery, terminalization, and release;
- repository-wide claim and work-branch lease;
- exact-head branch and pull-request lifecycle;
- state machine and transition table;
- exact-parent Git ref compare-and-swap;
- webhook, queue, and reconciliation behavior;
- implementer and reviewer adapter contracts;
- deterministic gate policy;
- finding, fix, and re-review semantics;
- provider-dispatch, spend, secret, permission, and content boundaries;
- deployment class, retention, recovery objectives, and notifications;
- tests, isolated proofs, rollout, kill switches, and compatibility.

This document does not:

- install or configure a GitHub App;
- create a hosted service, queue, database, secret, ruleset, branch, or workflow;
- modify `AGENTS.md` or `STATUS.md`;
- invoke Codex, Claude, another model, or a paid service;
- authorize implementation while 079 remains `planned`;
- authorize a governance amendment, readiness promotion, repository-setting change, merge, or auto-merge.

Current `AGENTS.md` remains binding. In particular, live development-agent model dispatch is prohibited until the separate governance amendment in section 24 explicitly reconciles the execution-spine invariant and the manual/explicit-only review rules. The implementation contract becomes actionable only after that amendment and the dated readiness decision.

## 3. Binding repository invariants

Any 079 implementation must preserve all of the following:

1. `docs/specs/STATUS.md` is the only live roadmap and status authority.
2. Only one product or implementation front may be active repository-wide.
3. A planning document, branch, PR, issue label, review, check, workflow run, timer, or model message is not authorization.
4. V0 starts only from a maintainer-authored command naming the exact spec, slice, base SHA, scope, adapters, and budget policy.
5. Every side-effect-authorizing transition rechecks grant currency, claim ownership, exact GitHub facts, stop state, role capacity, provider policy, and budget authority.
6. Deterministic gates and advisory review inform readiness; the maintainer alone owns merge.
7. The reviewer is advisory and cannot mutate code.
8. The implementer cannot supply the authoritative review verdict.
9. No automated actor may merge, enable auto-merge, force-push, delete protected refs, change secrets/settings, or bypass branch protection.
10. Paid or external-model work requires explicit repository-development content, provider, credential, and budget authority separate from runtime policy 059b.
11. Frozen, `planned`, `blocked`, cancelled, expired, revoked, or dependency-incomplete work is never selected or continued automatically.
12. Lease expiry, grant expiry, inactivity, process death, or a timer never releases the active front.
13. Any work-head change invalidates head-bound gates and review.
14. Safety takes precedence over liveness; the control plane is allowed to stop indefinitely.

## 4. Selected architecture

### 4.1 Control service

The primary dispatcher is an installed GitHub App operated by a small stateless Python 3.11 ASGI service.

The selected implementation class is:

- one OCI container image;
- FastAPI/ASGI HTTP entry point;
- GitHub REST and Git Data client;
- PostgreSQL 16 for non-authoritative delivery, queue, deduplication, and projections;
- no Redis, agent framework, vector database, browser automation, or second orchestration engine;
- one or more identical replicas permitted.

The service is outside the JarvisOS product runtime. It must not share JarvisOS SQLite authority, runtime provider secrets, runtime egress state, or `C:\JarvisOS` data.

### 4.2 Canonical GitHub state

Canonical state lives on a protected branch provisionally named `jarvis-control` in exactly one file:

`.jarvis/development-loop/authority.json`

Comments, checks, workflow runs, queue rows, database rows, dashboards, and digests are projections. They are rebuildable and never own a transition.

### 4.3 Non-authoritative PostgreSQL

PostgreSQL may contain only rebuildable operational state:

- webhook delivery IDs and payload digests;
- queued reconciliation jobs;
- bounded retry metadata;
- cached authority projections;
- provider-request correlation metadata;
- notification deduplication;
- service health and audit summaries.

It must not contain the only copy of a grant, claim, lease, PR binding, gate verdict, finding disposition, budget reservation, terminal outcome, or release decision. Complete database loss may delay work but cannot alter canonical authority.

## 5. Canonical encoding and integrity

### 5.1 Deterministic JSON

`authority.json` uses deterministic UTF-8 JSON:

- object keys sorted lexicographically;
- separators `,` and `:` with no insignificant whitespace;
- UTF-8 without BOM;
- UTC RFC 3339 timestamps ending in `Z`;
- integer quantities for money, counters, durations, and sizes;
- no floating-point values, `NaN`, or infinity;
- SHA-256 digests as lowercase `sha256:<64 hex>`.

Canonical bytes are equivalent to:

```python
json.dumps(
    value,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
).encode("utf-8")
```

### 5.2 File envelope

```json
{
  "schema_version": 1,
  "repository": {
    "repository_id": 0,
    "full_name": "owner/repo",
    "default_branch": "master",
    "control_branch": "jarvis-control"
  },
  "sequence": 0,
  "snapshot": {},
  "snapshot_digest": "sha256:...",
  "events": []
}
```

Requirements:

- `repository_id` is the immutable GitHub numeric repository ID.
- `sequence` equals the final event sequence, or zero for bootstrap.
- `snapshot` derives entirely from `events` and rebuilds to `snapshot_digest`.
- unknown top-level or event fields are rejected in v1.
- v1 has no compaction.
- before event 4097 or 2,000,000 canonical bytes, halt with `authority_capacity_reached`; never truncate history.

### 5.3 Event schema

```json
{
  "sequence": 1,
  "event_id": "evt_<64 hex>",
  "event_type": "authorization_recorded",
  "occurred_at": "2026-07-31T16:00:00Z",
  "actor": {
    "actor_id": "github:123",
    "login": "example",
    "role": "control"
  },
  "idempotency_key": "sha256:...",
  "previous_event_digest": null,
  "payload": {},
  "payload_digest": "sha256:...",
  "event_digest": "sha256:..."
}
```

Rules:

- sequence increments by one;
- `event_id` derives from the idempotency-key bytes;
- payload and event digests use canonical bytes;
- previous-event digest matches exactly;
- identical duplicate input is a no-op returning the existing event;
- reuse of an idempotency key with different bytes is an integrity failure;
- sequence and Git ancestry, not timestamps, own ordering.

### 5.4 Double integrity chain

A transition requires both the in-file hash chain and linear Git ancestry on `jarvis-control`. Missing, altered, reordered, duplicated, forked, force-pushed, or non-linear history causes `control_integrity_failure` and permits no external side effect.

## 6. Closed identifiers, roles, states, and outcomes

### 6.1 Identifier prefixes

- run: `run_<32 hex>`
- grant: `grant_<32 hex>`
- global claim: `claim_<32 hex>`
- branch lease: `lease_<32 hex>`
- PR operation: `pr_<32 hex>`
- gate collection: `gates_<32 hex>`
- review round: `review_<32 hex>`
- finding: `finding_<32 hex>`
- fix attempt: `fix_<32 hex>`
- provider request: `provider_<32 hex>`
- human request: `human_<32 hex>`

All IDs are Control-App-derived from canonical idempotency inputs. No model or provider may choose authoritative IDs.

### 6.2 Actor roles

Closed roles:

- `maintainer`
- `control`
- `implementer`
- `reviewer`
- `gate_collector`
- `system_reconciler`

Effective credentials determine roles; text cannot self-assert them.

### 6.3 States

Closed states:

- `idle`
- `authorized`
- `claimed`
- `implementing`
- `awaiting_pr`
- `awaiting_gates`
- `awaiting_review`
- `fix_required`
- `awaiting_re_review`
- `awaiting_maintainer`
- `terminal`
- `halted`

`terminal` returns to `idle` only through explicit reconciled `front_released`. `halted` must first recover to a reachable safe state or terminalize through a valid maintainer command.

### 6.4 Terminal outcomes

- `merged_by_maintainer`
- `closed_without_merge`
- `superseded_by_maintainer`
- `completed_without_pr`
- `authorization_revoked`
- `authorization_expired`
- `abandoned_after_human_decision`

### 6.5 Stop reasons

Closed reasons include:

- `authorization_missing`
- `authorization_invalid`
- `authorization_expired`
- `authorization_revoked`
- `registry_ineligible`
- `dependency_unmerged`
- `active_front_conflict`
- `claim_race_lost`
- `control_integrity_failure`
- `authority_capacity_reached`
- `scope_violation`
- `base_head_mismatch`
- `work_head_ambiguous`
- `work_head_changed_after_review`
- `pr_missing`
- `pr_mismatch`
- `pr_ambiguous`
- `pr_closed_unexpectedly`
- `lease_expired_pending_reconciliation`
- `gate_missing`
- `gate_stale`
- `gate_cancelled`
- `gate_action_required`
- `gate_infrastructure_failure`
- `gate_flaky_or_ambiguous`
- `review_invalid`
- `review_inconclusive`
- `finding_needs_human`
- `maximum_rounds_reached`
- `provider_disabled`
- `provider_ambiguous`
- `cost_unknown`
- `spend_cap_exceeded`
- `secret_unavailable_or_changed`
- `security_signal`
- `destructive_action_required`
- `governance_decision_required`
- `merge_boundary`
- `human_decision_required`

Generic `unknown`, `provider_error`, or `failed` is forbidden when a precise reason exists.

## 7. Authorization, expiry, revocation, recovery, and release

### 7.1 Control issue and maintainer identity

Readiness bootstraps one control issue and allow-listed maintainer numeric IDs. A command is eligible only when the author ID, repository ID, issue, new-comment event, exact command syntax, SHAs, and repository facts validate. Comments are command inputs, never canonical authority.

### 7.2 Authorization command

~~~~text
```jarvis-authorization-v1
{
  "command": "authorize",
  "repository_id": 123,
  "spec_id": "079",
  "slice_id": "079-implementation-v0",
  "base_branch": "master",
  "base_sha": "<40 lowercase hex>",
  "scope": {
    "allow_paths": ["services/devloop/**", "docs/specs/STATUS.md"],
    "deny_paths": [".github/workflows/**", "AGENTS.md"],
    "max_changed_files": 40,
    "max_diff_lines": 6000
  },
  "implementer_adapter_id": "approved-implementer-v1",
  "reviewer_adapter_id": "approved-reviewer-v1",
  "budget_policy_id": "devloop-budget-v1",
  "max_fix_rounds": 2,
  "expires_at": null,
  "reason": "Implement the merged and ready 079 slice."
}
```
~~~~

Validation:

- spec ID is exactly three digits;
- slice ID is 1–80 lowercase ASCII letters, digits, `_`, or `-`;
- base SHA equals current base head when recorded;
- normalized non-empty allow/deny globs use deny precedence;
- maximum files is 1–100 and diff lines 1–20,000;
- maximum fix rounds is 0–2;
- implementer/reviewer identities are distinct and approved;
- expiry is future UTC and at most 30 days after issue;
- reason is bounded to 500 safe characters.

The normalized scope produces `scope_digest`; work branch is derived as `jarvis-work/<run_id>`. V0 never infers a grant from a row, branch, PR, label, review, schedule, prior run, chat, or model recommendation.

### 7.3 Grant currency and expiry

Every transition that can authorize branch/PR mutation, workflow action, implementer call, reviewer call, reservation, or other external side effect must re-read and prove that the grant is present, unrevoked, and unexpired at transition commit time.

When `expires_at` is reached:

- no new side-effect-authorizing transition may commit;
- a canonical `authorization_expired` event records the stop and enters `awaiting_maintainer`;
- already accepted external work is not retried or discarded; it is reconciled and recorded without authorizing follow-on work;
- expiry never releases the claim, lease, branch, PR, budget evidence, or history;
- the maintainer may terminalize through recovery/revocation and then explicitly release.

### 7.4 Revocation

A valid maintainer `revoke` command records `authorization_revoked`, blocks new side effects, permits only proven-safe bounded cancellation, and enters `awaiting_maintainer` or terminal outcome `authorization_revoked`. It never erases evidence.

### 7.5 Recovery

A `recover` command binds repository/run/exact control head, action `resume` or `terminalize`, target state/outcome, and reason. The service independently reconciles repository, branch, PR, workflows, providers, reservations, lease, budget, and security facts. Security stops require referenced remediation evidence. Target state must be reachable under section 11.

### 7.6 Release and `terminal → idle`

Release is accepted only from `terminal` after proving no implementer, reviewer, workflow dispatch, provider request, reservation, cancellation, integrity anomaly, or security anomaly remains active or ambiguous and branch/PR facts match terminal outcome.

A release command binds repository, run, grant, exact control head, and reason. Successful CAS appends one `front_released` event and derives `idle` by clearing active-run fields while preserving immutable completed-run identity, terminal outcome, PR/branch bindings, findings, usage, cost, event chain, and Git history.

Duplicate identical release is a no-op. Non-terminal or ambiguous release fails closed. A later run requires a new grant from `idle`.

## 8. Canonical snapshot

```json
{
  "state": "idle",
  "run_id": null,
  "authorization": null,
  "global_claim": null,
  "branch_lease": null,
  "work": null,
  "gates": null,
  "review": null,
  "budget": null,
  "next_action": null,
  "stop": null,
  "terminal_outcome": null,
  "last_completed_run": null
}
```

Authorization binds grant source/identity/spec/slice/base/scope/adapters/budget/rounds/expiry/revocation. Work binds branch/head/PR/base/PR state/ancestry/attempt/diff/scope digest. Review binds round/exact head/effective reviewer/provider request/response digest/findings/dispositions/verdict. Budget uses integer micro-USD and binds policies, ceilings, reservations, finalized/released/unknown amounts, provider IDs, and role call counts.

## 9. Repository-wide claim, work branch, and lease

### 9.1 Claim

`claim_acquired` requires state `authorized`, current grant, eligible registry/dependencies, repository-wide vacancy, no competing PR/owner/run, exact master base, current policies, and no stop. It atomically records the global claim and initial 60-minute lease. Losing or ambiguous writers perform zero side effects.

### 9.2 Control-App create-only work ref

After claim success, the Control App may create only `refs/heads/jarvis-work/<run_id>` in the exact repository at the exact grant base SHA, only when absent and canonical state/claim/lease match. An existing exact ref is idempotently accepted. The App may not subsequently update, force-update, delete, or author commits on that ref.

After exact creation/reconciliation, `work_branch_recorded` commits. A mismatched pre-existing ref or ambiguous result halts. Later engineering writes are implementer-only under lease, with human emergency authority.

### 9.3 Work lease

V1 lease duration is 60 minutes; renewal may start with 20 minutes or less remaining; only one mutation request may be active. Renewal cannot change scope, round, adapter, budget, or grant. Every renewal is canonical and requires a current unexpired grant and reconciled facts.

Expiry never releases ownership. It records `lease_expired_pending_reconciliation`; branch, PR, workflows, provider calls, comments, reservations, budget, and security facts must be reconciled before renewal/recovery.

## 10. Exact-head authority CAS

Every canonical transition:

1. reads exact `refs/heads/jarvis-control`;
2. reads parent commit/tree/blob;
3. validates schema, event chain, snapshot, and Git ancestry;
4. re-reads all transition preconditions;
5. computes one deterministic event and replacement bytes;
6. creates blob and tree based on expected parent tree;
7. creates a commit whose sole parent is exact expected control head;
8. updates control ref with `force=false`;
9. accepts only unambiguous candidate success;
10. on rejection/timeout/disconnect/ambiguity, performs no external side effect and reconciles.

Contents API blob updates are forbidden as authority CAS. Ambiguous success is resolved by rereading ref/ancestry/event ID; unresolved ambiguity halts. Same idempotency key never creates a different event.

## 11. Closed state machine

### 11.1 Global dispatch precondition

The only events that may authorize implementer or reviewer dispatch are `implementation_requested`, `gate_repair_authorized`, `review_fix_authorized`, and `review_dispatch_authorized`.

Each must atomically record, before the external call:

- current unexpired/unrevoked grant;
- current global claim and no stop;
- exact repository, branch, PR, base, and work head as applicable;
- valid role identity and remaining role call capacity;
- current provider policy and adapter identity;
- canonical cost/quota reservation, even when projected marginal cost is zero;
- deterministic request idempotency key;
- for mutations, a valid reconciled lease and current scope digest;
- for reviews, exact eligible gates and exact recorded PR/head.

No other event or prose authorizes an external model call.

### 11.2 Transition table

| Current state | Event | Binding preconditions | Next state | Side effect after commit |
| --- | --- | --- | --- | --- |
| `idle` | `authorization_recorded` | valid maintainer command | `authorized` | none |
| `authorized` | `claim_acquired` | section 9.1 and CAS | `claimed` | create/reconcile exact work ref |
| `claimed` | `work_branch_recorded` | exact derived ref at base | `claimed` | none |
| any active state | `lease_renewed` | current grant, lease, reconciliation, window | same | none |
| `claimed` | `implementation_requested` | section 11.1 including lease/reservation/capacity | `implementing` | one implementer request |
| `implementing` | `work_head_recorded` | exact descendant or bounded no-change; scope passes | `awaiting_pr` | none |
| `implementing` | `provider_ambiguous` | accepted request with unresolved completion/charge | `halted` | none |
| `awaiting_pr` | `pr_creation_authorized` | exact branch/head/base; no conflict; grant current | `awaiting_pr` | create/reconcile one PR |
| `awaiting_pr` | `pr_recorded` | exactly one matching open PR and exact head | `awaiting_gates` | observe/request deterministic gates only |
| `awaiting_gates` | `gates_passed` | all required gates green on exact recorded PR/head | `awaiting_review` or `awaiting_re_review` | none |
| `awaiting_gates` | `gate_defect_reproduced` | deterministic in-scope defect only | `fix_required` | none |
| `fix_required` | `gate_repair_authorized` | gate defect plus section 11.1 lease/reservation/capacity | `implementing` | one implementer repair |
| `awaiting_gates` | `gate_ambiguous_or_infra` | stale/flaky/cancelled/missing/action-required/infra | `halted` or `awaiting_maintainer` | none |
| `awaiting_review` | `review_dispatch_authorized` | section 11.1 review reservation/capacity | `awaiting_review` | one reviewer request |
| `awaiting_re_review` | `review_dispatch_authorized` | section 11.1 review reservation/capacity | `awaiting_re_review` | one reviewer request |
| `awaiting_review` or `awaiting_re_review` | `provider_ambiguous` | accepted review request with unresolved completion/charge | `halted` | none |
| `awaiting_review` | `review_clean` | valid structured review on exact head | `awaiting_maintainer` | presentation only |
| `awaiting_review` | `review_findings_recorded` | valid normalized findings on exact head | `fix_required` | deterministic triage only |
| `awaiting_review` | `review_inconclusive` | valid inconclusive review | `awaiting_maintainer` | none |
| `fix_required` | `findings_disposed_no_change` | all findings false/superseded with evidence | `awaiting_re_review` | none |
| `fix_required` | `review_fix_authorized` | genuine blocker plus section 11.1 lease/reservation/capacity/round | `implementing` | one implementer fix |
| `fix_required` | `finding_requires_human` | scope/security/ambiguity/dependency/round boundary | `awaiting_maintainer` | none |
| `awaiting_re_review` | `review_clean` | valid exact-head review | `awaiting_maintainer` | presentation only |
| `awaiting_re_review` | `review_findings_recorded` | valid findings and rounds remain | `fix_required` | triage only |
| `awaiting_re_review` | `review_inconclusive` | valid inconclusive review | `awaiting_maintainer` | none |
| `awaiting_re_review` | `maximum_rounds_reached` | negative result after round 2 | `awaiting_maintainer` | none |
| `awaiting_maintainer` | `work_head_changed` | valid scoped descendant differs from reviewed head | `awaiting_pr` | none |
| `awaiting_maintainer` | `human_merge_observed` | allow-listed maintainer; merged SHA equals exact current gated/reviewed head | `terminal` | none |
| `awaiting_maintainer` | `human_close_observed` | recorded PR closed/deferred/superseded by maintainer | `terminal` | none |
| any active non-terminal state | `authorization_expired` | current time reaches grant expiry | `awaiting_maintainer` | reconcile accepted work only |
| any non-terminal state | `authorization_revoked` | valid revocation | `awaiting_maintainer` or `terminal` | proven-safe cancellation only |
| any non-terminal state | `security_halt` | authenticated compromise evidence or verified anomaly | `halted` | none |
| `halted` | `human_recovery_recorded` | valid recovery and reconciled facts | reachable safe state or `terminal` | recorded recovery action only |
| `terminal` | `front_released` | section 7.6 and full reconciliation | `idle` | none |

### 11.3 Exact-head invalidation

Any push or ref observation that changes the active work head invalidates prior `gates`, review verdict, presentation-ready status, and merge eligibility.

- Before clean review: record the new scoped head and return through `awaiting_pr` and gates.
- From `awaiting_maintainer`: `work_head_changed` returns to `awaiting_pr`; no stale clean verdict remains active.
- A non-descendant, force-push, scope violation, or ambiguous head halts.
- `human_merge_observed` is valid only when the actual merged commit/head equals the exact current head that passed required gates and received the current clean review. Any mismatch fails closed and cannot terminalize as cleanly merged.

### 11.4 Idempotent PR lifecycle

`pr_creation_authorized` binds repository/run/branch/exact head/base/scope/version. The App reconciles PRs for the derived head:

- none: create one non-draft PR with base `master`, derived head, and bounded run/scope marker;
- exactly one correct open PR: reuse;
- duplicate, wrong base/head/marker, fork, unknown state: fail closed;
- previously recorded PR closed by maintainer: never create replacement; reconcile terminal/human decision;
- timeout after create: search and validate before retry; never create a second PR.

`pr_recorded` commits numeric PR ID, repository, base, head branch, current exact work head, operation key, and state. Gates/review are forbidden before it. After every code-changing repair/fix, the same PR is rebound to the new head through `awaiting_pr`; second PR creation is forbidden.

## 12. Branch and scope contract

Exactly one work branch exists. Control App creates it once at exact base; implementer supplies later commits; automated force-push/deletion is denied; PR base is `master`; forks unsupported.

Before every mutation request and after every resulting head, normalize and verify changed paths, allow/deny precedence, file/line limits, linear ancestry, submodules, LFS pointers, symlink escapes, binaries, and secret-file risks; bind verification digest.

Denied absent exact separate authorization:

- `AGENTS.md`
- `.github/workflows/**`
- `.github/CODEOWNERS`
- settings/ruleset exports
- secrets/credentials/keys/tokens
- protected conformance tests
- vendored dependencies/lockfiles
- canonical authority file.

## 13. Deterministic gate policy

Readiness freezes exact gate names, workflow/action pins, and path conditions. Initial gates include registry, manual-review offline boundary, BLUECAD license boundary, Ruff, full Pytest, geometry canary, frontend build when needed, strict real-tool proof for relevant changes, and 079 service unit/integration/conformance/reconstruction tests.

Eligible results are successful, repository-bound, exact-head, policy-matching, and not skipped/stale/cancelled/action-required/superseded. One zero-model-cost infrastructure rerun is allowed per collection only absent source/test failure. Further or ambiguous infrastructure failure halts. Tests/workflows cannot be weakened.

## 14. Reviewer contract and finding identity

Reviewer credential is read-only for repository, code, PR, checks, and statuses; it has no contents write, workflow dispatch, merge, settings, secret, ref-delete, or ruleset authority. Reviewer and implementer effective identities differ.

Review request binds repository/spec/slice/scope/non-goals/base/head/diff/PR/gates/round/prior findings/fixes/content digest/provider policy/reservation/idempotency.

Reviewer response:

```json
{
  "schema_version": 1,
  "reviewed_head_sha": "<40 hex>",
  "verdict": "clean",
  "summary": "bounded text",
  "findings": [
    {
      "severity": "P1",
      "category": "correctness",
      "path": "path/or/null",
      "line": 1,
      "claim": "bounded text",
      "reproduction": "bounded text or null",
      "suggested_resolution": "bounded text or null"
    }
  ]
}
```

The reviewer must not provide authoritative finding IDs. After schema validation and deterministic normalization, the Control App derives each `finding_<32 hex>` from review round, exact head, normalized severity/category/path/line/claim digest, and occurrence index. A model-supplied `finding_id` is rejected as an unknown field in v1.

Verdict is `clean`, `findings`, or `inconclusive`; maximum 50 findings and 2,000 characters per text field. Malformed, oversized, wrong-head, unknown-field, or non-JSON output is invalid. Inconclusive review records `review_inconclusive` and stops for human action.

P0/P1 block until disposed. P2 blocks only when independently reproduced as a binding violation. P3 is advisory and never triggers mutation.

## 15. Finding disposition and fix loop

Closed dispositions: `reproduced`, `accepted_without_reproduction`, `false_positive`, `superseded`, `needs_human`.

Reproduced requires deterministic evidence or precise current path; accepted-without-reproduction is limited to direct spec-invariant contradiction; false-positive requires evidence; superseded points to later head/finding; needs-human stops.

Limits: initial review round 0; maximum fix rounds 2; maximum reviewer calls 3; maximum implementer calls 3; one fix per negative round; every code change returns through PR binding, gates, and review; no-change rebuttal still re-reviews; negative round 2 stops; scope/destructive/governance/secret/dependency expansion requires human action.

## 16. Implementer/reviewer provider adapters and current execution-spine block

Immutable adapter requests bind repository/installation, branch/exact head, spec/slice, scope/non-goals, task type, defect/findings, provider/budget policy, reservation, and idempotency. Responses bind provider request/status, resulting head/no-change, safe summary/digests, usage/cost/idempotency, and error class.

Adapters cannot alter base/branch/scope/spec/tests/provider/budget; implementer commits only on work branch; neither actor may merge/approve/force-push/delete refs/change settings/secrets/write control authority. Ambiguous accepted request halts without retry unless provider idempotency and reconciliation prove exact outcome.

Current `AGENTS.md` requires all AI calls through `run_ai_task` and `ai_jobs`. The selected hosted control service deliberately does not share product runtime SQLite or runtime egress state. Therefore live 079 implementer/reviewer calls remain impossible under current governance.

Before readiness, the separate governance amendment must choose and bind exactly one route:

- **Selected v0 route:** create a narrow repository-development exception allowing only canonical 079 adapter calls outside product `run_ai_task`, provided every call has a committed 079 grant/claim/exact head/PR/scope/provider/reservation/idempotency event and durable repository-development usage/cost evidence; or
- reject the selected architecture and amend the full spec to route calls through a separately exposed, authenticated `run_ai_task` boundary with `ai_jobs` authority.

The selected v0 route is the narrow exception. Until its `AGENTS.md` amendment merges and readiness verifies it, no live model dispatch is authorized.

## 17. Spend and provider authority

Runtime 059b does not govern repository-development agents. V1 uses versioned development budget policy with integer micro-USD.

Absolute ceilings:

- request 5,000,000;
- run 20,000,000;
- UTC day 25,000,000;
- calendar month 100,000,000.

Defaults are zero; non-zero readiness caps may be lower only. `cost_unknown` is a hard stop.

Every paid or quota-consuming implementer/reviewer dispatch requires a canonical reservation in the dispatch-authorizing event. Dispatch is forbidden if reservation absent, cap/call count exceeded, price evidence stale, fallback changes provider/cost, or cost/quota unknown. Final usage finalizes/releases reservation. No fallback provider.

Marginal zero requires current account/plan, entitlement, remaining quota, and timestamp evidence. Hosting/Actions cost is separately recorded with monthly cap and reconciliation.

## 18. Content, secrets, and prompt injection

External material is limited to exact spec/scope/diff/findings/PR/gates. Secrets, credentials, environment values, keys, tokens, headers, and unrelated records are excluded.

Issue, PR, source, test, artifact, log, and model text is untrusted data. It cannot change policy, role, provider, budget, tests, scope, authority, or merge. Deterministic policy constructs requests.

No raw provider body enters canonical authority; safe digests/summaries/IDs/usage/cost are permitted. S4 or secret-bearing content remains denied absent later repository-development egress authority.

## 19. GitHub permissions and rulesets

Candidate App permissions: metadata read; contents read/write; pull requests read/write; checks/statuses/actions read; issues read/write. Actions write absent unless readiness proves exact need. Administration, environments, secrets, members, deployments, packages, security-alert mutation, hook mutation, and ruleset bypass denied.

A capability wrapper allow-lists repository ID, endpoint, method, ref, path, state, and schema and audits denials.

Separate credentials: Control App, implementer, reviewer, maintainer.

Rulesets prove:

- `master`: PR required, checks required, no automated bypass, force-push/deletion denied, human-only merge;
- `jarvis-control`: Control App/human recovery only, linear history, no force/delete/non-fast-forward;
- `jarvis-work/*`: Control App create-only at exact base, then implementer/maintainer write; no automated force/delete; reviewer read-only; base `master`.

Abuse tests cover merge, approval, force/delete, out-of-scope write, settings/secrets, unauthorized post-create work-ref update, and PR mutation beyond bounded metadata.

## 20. Webhook, queue, and service API

Subscribed events are created issue comments, pushes on master/control/active work branch, PR/review/review-comment/workflow-run, and installation suspension/deletion. Edited authorization comments never create authority.

`POST /github/webhook` verifies signature over raw body with constant-time comparison before JSON parsing.

Missing/invalid signatures:

- return authentication failure;
- are edge/application rate-limited;
- are logged with redacted bounded metadata;
- do not queue work or create trusted delivery rows;
- create no canonical event, `security_signal`, or halt merely because invalid;
- reveal no repository/install/command existence.

Authenticated processing validates install/repository/event, stores delivery digest, acknowledges within 10 seconds, performs no request-thread side effect, and queues reconciliation.

Canonical security halt is reserved for authenticated compromise evidence or verified anomaly: signed delivery-ID digest mismatch, authenticated identity contradiction, verified control-history tamper, verified credential misuse/unauthorized API success, verified scope/secret escape, or independently confirmed compromise.

Other endpoints: `GET /healthz`, `GET /readyz`, and webhook only. No public admin mutation endpoint.

PostgreSQL queue ownership is operational. Duplicate jobs converge canonically. Read reconciliation retries at most five times. Side-effect retry requires committed authorization and proven idempotency. Webhook order is untrusted.

Retention: delivery 30 days, queue/projection 90 days, logs 30 days; no raw model/secret/header logs. Canonical RPO zero, DB RPO 24 hours, service RTO target 4 hours; GitHub uncertainty stops indefinitely.

## 21. Presentation and notifications

At most one non-authoritative check, sticky PR comment, control-issue status comment, and weekly digest. Updates follow canonical state changes and are idempotent.

Between weekly reviews, direct notification only for human decision, authenticated security signal, or budget overrun/disabled cost authority. Weekly digest: Europe/Rome, Monday 08:00, max one per seven days, omitted without state change, never grants authority.

## 22. Security and supply chain

Use short-lived tokens, secret store, rotation, immutable pins/digests, SBOM, dependency/container scanning, outbound allow-list, repository/SHA validation, and deny untrusted fork execution with write/secret credentials. Webhook process never executes PR code.

Invalid unauthenticated signatures do not canonically halt. Authenticated compromise evidence, verified history anomaly, signed delivery mismatch, verified scope escape, or verified secret exposure does.

## 23. Verification and acceptance

### 23.1 Offline unit tests

Prove deterministic JSON/digests; event/snapshot reconstruction; duplicate convergence; invalid schema/field/float/timestamp/digest rejection; full transition matrix; grant/expiry/revoke/recover/release parsing; maintainer identity; scope/path limits; reservations/caps/call counts; finding normalization and Control-App ID derivation; lease lifecycle; PR idempotency; exact-head invalidation; provider ambiguity; notification dedupe; and invalid-signature no-state-change behavior.

### 23.2 Offline integration tests

With fake GitHub/PostgreSQL/implementer/reviewer, prove restart reconstruction; duplicate webhook/job convergence; one create-only work ref; denial of later Control-App update/delete; one PR before gates; PR timeout reconciliation; same-PR rebinding after fixes; grant expiry blocks every new dispatch; every dispatch has reservation/capacity; expired lease blocks repair until reconciled renewal; head movement invalidates clean review and returns through gates; inconclusive review stops; ambiguous implementer/reviewer call halts; finding IDs are Control-App-derived; terminal release preserves history and enables later grant; no merge/self-approval; invalid signatures cannot cause canonical DoS; inactivity is silent.

### 23.3 Disposable-repository proofs before readiness

Prove:

1. multi-dispatcher single-winner claim;
2. stale exact-parent/ref rejection even with unchanged blob;
3. timeout-after-CAS reconciliation once;
4. signed webhook replay convergence after DB loss;
5. full authority reconstruction after external-state deletion;
6. history tamper halt;
7. lease expiry never starts another claimant;
8. create-only exact-base work ref and denial of later App mutation;
9. one exact-head PR before gates and no duplicate after timeout/replay;
10. wrong/forked/closed/duplicate/mismatched PR fail-closed;
11. grant expiry before initial/review/repair dispatch creates zero new calls;
12. reservation/call-capacity required for every implementer/reviewer call;
13. expired lease blocks mutation repair;
14. reviewed-head drift invalidates presentation and merge eligibility;
15. actual merged head must equal exact gated/reviewed head;
16. inconclusive review and provider ambiguity produce canonical stop states;
17. reviewer-supplied finding ID is rejected and deterministic ID is reproduced;
18. terminal release preserves history and allows sequential run;
19. automated credentials denied merge/approval/force/delete/settings/secrets/out-of-scope writes;
20. reviewer cannot write and implementer cannot author review;
21. untrusted fork cannot access secrets/write;
22. prompt injection cannot change authority;
23. exceeded/unknown cost creates zero calls;
24. provider timeout creates no duplicate request/charge;
25. GitHub outage reconciles without duplicate action;
26. kill switches stop effects;
27. Actions concurrency cannot release authority;
28. invalid/unsigned traffic cannot canonical-halt;
29. authenticated verified anomaly does halt;
30. inactivity/replay creates no noise or calls.

### 23.4 Repository gates and conformance

Implementation passes backend Pytest/Ruff/status self-test, existing CI/canaries, and deterministic `services/devloop` tests. No CI live model, paid service, or production mutation.

Readiness freezes maintainer-owned vectors for transitions, race, work-ref permission, PR lifecycle, grant/lease expiry, budget dispatch, exact-head invalidation, provider ambiguity, finding IDs, merge denial, release/sequential runs, webhook authentication, rounds, cost stops, and kill switches. Implementation agents cannot weaken them.

## 24. Governance, rollout, readiness, and kill switches

### 24.1 Required `AGENTS.md` amendment

A separate PR must explicitly amend both:

1. the manual-only/explicit-only automated review and Codex dispatch clauses; and
2. the hard invariant requiring all AI calls through product `run_ai_task`/`ai_jobs`.

The narrow v0 exception must state that repository-development model calls may occur outside product `run_ai_task` only through the approved 079 adapter when one canonical run has a current maintainer grant, global claim, exact branch/head/PR, scope, actor identities, deterministic gates as applicable, role capacity, provider policy, and canonical reservation/idempotency evidence. The adapter must write durable 079 request/usage/cost evidence and may not access product runtime authority or secrets.

The exception must continue to forbid automatic spec selection, merge, auto-merge, priority change, workflow/ruleset bypass, force-push, branch deletion, settings/secrets change, destructive action, scope expansion, provider fallback, or work after expiry/revocation/security/cost/integrity/human-decision stop.

Until that amendment is merged, no live implementer or reviewer dispatch is authorized.

### 24.2 Rollout

1. Merge full spec with 079 `planned`.
2. Merge narrow governance amendment, dormant until readiness.
3. Build proof prototype only in disposable repository/separate fixture with fake actors and zero paid calls.
4. Explicitly approved read-only JarvisOS shadow: no claim, branch/PR write, workflow, or provider.
5. Dated readiness records host, App/actor IDs, rulesets, adapters, pricing/caps, proofs, vectors, owners, rollback; only then `ready`.
6. After readiness, one bounded implementation PR.
7. After implementation and separate operational grant, one low-risk documentation-only activation with human merge.
8. Broader use separately approved after first-run evidence.

No implementation skeleton enters JarvisOS while 079 is `planned`.

### 24.3 Kill switches

Canonical halt, App suspension, App/webhook credential rotation, provider credential revocation, service/queue stop, caps zero, dispatch workflow disable, and protected human recovery. Rollback halts/reconstructs/records; never force-pushes or erases evidence.

### 24.4 Readiness evidence

079 remains `planned` until a dated PR proves dependencies/current vacancy; merged architecture/full spec/governance; every disposable proof; exact permissions/rulesets/wrapper/IDs; execution-spine exception; automated abuse denials; work-ref/PR lifecycle; grant/lease/budget dispatch controls; exact-head drift; provider ambiguity; finding IDs; release/sequential behavior; selected host/DB/secrets; selected adapters/effective identities; current price/quota; approved caps; frozen gates/vectors; named implementation/rollback owners; bounded first activation; and no unresolved P0/P1 authority/security blocker.

Only that PR may set `ready`.

## 25. Compatibility and migration

No product SQLite migration. Runtime execution spine, budget, Hermes, MemoryStore, BLUECAD, and product events do not become control-plane authority. Hosted PostgreSQL v1 remains rebuildable. Bootstrap creates new protected control branch explicitly; no chat/old PR/branch is imported. Existing work requires exact grant/reconciliation and normally a fresh work branch. Review workflows remain manual until governance/readiness. Authority version changes require additive versioning/migration proof. Force-push/history rewrite is never migration.

## 26. Likely implementation scope

Expected bounded paths after readiness: `services/devloop/`, pinned service manifest/container, fake actors/fixtures, secret-free deployment docs, normal `STATUS.md` implementation transition, and CI only for offline service tests.

Not in implementation PR: `AGENTS.md` amendment, live App/settings/rulesets/secrets, provider credentials/raw account data, product backend/frontend/runtime, Hermes/MCP/MemoryStore/BLUECAD/process-kernel/078. New dependencies must be pinned, justified, scanned, service-limited; no agent framework.

## 27. Binding non-goals

No automatic next-spec selection; simultaneous fronts/branches/implementers/reviewers/PRs; autonomous merge/approval/release/deploy/priority/governance/ruleset/secrets; force-push/delete/history rewrite/protected-test mutation; arbitrary shell beyond adapter/scope; provider fallback/bidding/swarm; unbounded loops; untrusted-fork execution; replacement of runtime 059b/Hermes/Actions; raw model/secret canonical storage; outage availability guarantee; or implementation of 078/another frozen front.

## 28. Definition result

Full-spec step is complete when:

- this document replaces the planning kernel on current-master PR;
- 079 remains `planned` with no Implementation PR;
- architecture, schemas, state machine, authorization/expiry, branch/PR lifecycle, dispatch reservations/capacity, lease, exact-head invalidation, provider ambiguity, finding IDs, permissions, cost, tests, rollout, compatibility, and kill switches are explicit;
- PR creation occurs before gates and remains same-PR idempotent across fixes;
- terminal release preserves history and returns idle;
- Control App create-only work-ref capability is explicit;
- unauthenticated signature failures cannot canonical-halt;
- current execution-spine conflict is explicitly blocked pending governance amendment;
- ref-level CAS remains proof-gated;
- no runtime/workflow/App/provider/secret/ruleset/dependency/setting is created or changed;
- exact-head deterministic gates pass;
- review findings are resolved;
- PR stops for maintainer merge decision.

Merging this specification does not authorize governance amendment, readiness, implementation, external provider calls, or automated merge.
