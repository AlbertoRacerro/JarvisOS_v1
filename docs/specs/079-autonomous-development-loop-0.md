# 079 — AUTONOMOUS-DEVELOPMENT-LOOP-0: durable bounded development continuation

Status: full specification complete; `docs/specs/STATUS.md` remains authoritative and keeps 079 `planned`.

Depends on: 004, 017, 019, 022

Full-spec baseline: `9c3c8ce90a9048c1797f2560025790162012d423`

Authority and evidence:

- `079-autonomous-development-loop-source-evidence.md`
- `079-architecture-evidence-closure-2026-07-31.md`
- `079-architecture-source-evidence-2026-07-31.md`

## 1. Goal

Allow one **already and explicitly authorized** JarvisOS repository-development slice to continue safely across agent-session termination without repeated conversational `continue` prompts.

The control plane may:

- reconstruct durable authority from GitHub;
- claim exactly one repository-wide development front;
- invoke one bounded implementer on one exact work branch;
- collect deterministic gates tied to an exact head;
- invoke one independent reviewer;
- perform at most two bounded finding/fix/re-review rounds;
- recover from duplicate delivery, process restart, and stale local state;
- present a fully evidenced pull request to the maintainer.

The control plane may never merge, enable auto-merge, change priority, create a second active front, infer authorization from activity, or turn model output into repository authority.

## 2. Full-spec boundary

This document freezes the v0 contract for:

- canonical state and event encoding;
- explicit authorization and revocation;
- repository-wide claim and work-branch lease;
- state machine and transition table;
- exact-head Git ref compare-and-swap;
- webhook, queue, and reconciliation behavior;
- implementer and reviewer adapter contracts;
- deterministic gate policy;
- finding, fix, and re-review semantics;
- spend, secret, permission, and content boundaries;
- deployment class, retention, recovery objectives, and notifications;
- tests, isolated proofs, rollout, kill switches, and compatibility.

This document does **not**:

- install or configure a GitHub App;
- create a hosted service, queue, database, secret, ruleset, branch, or workflow;
- modify `AGENTS.md`;
- invoke Codex, Claude, another model, or a paid service;
- authorize implementation while 079 remains `planned`;
- authorize a governance amendment, readiness promotion, or repository-setting change;
- authorize merge or auto-merge.

The architecture and schemas are complete enough to implement only after the separate governance and readiness gates in section 24.

## 3. Binding repository invariants

Any 079 implementation must preserve all of the following:

1. `docs/specs/STATUS.md` is the only live roadmap and status authority.
2. Only one product or implementation front may be active repository-wide.
3. A planning document, open branch, open PR, issue label, review, check, workflow run, timer, or model message is not authorization.
4. Deterministic gates and the human maintainer own merge readiness; the maintainer alone owns merge.
5. The reviewer is advisory and cannot mutate code.
6. The implementer cannot supply the authoritative review verdict.
7. No actor may merge its own PR, enable auto-merge, force-push, delete protected refs, change secrets/settings, or bypass branch protection.
8. Paid or external-model work requires explicit content, provider, credential, and budget authority separate from runtime policy 059b.
9. Frozen, `planned`, `blocked`, cancelled, or dependency-incomplete work is never selected automatically.
10. The control plane is allowed to stop. Safety takes precedence over liveness.

The v0 dispatcher does **not** use the general AGENTS.md permission to pick the lowest-numbered `ready` spec. V0 starts only from a maintainer-authored authorization command that names the exact spec, slice, base SHA, and scope.

## 4. Selected architecture

### 4.1 Control service

The primary dispatcher is an installed GitHub App operated by a small stateless Python 3.11 ASGI service.

The implementation class is:

- one OCI container image;
- FastAPI/ASGI HTTP entry point;
- GitHub REST/Git Data client;
- PostgreSQL 16 for non-authoritative delivery, queue, deduplication, and projections;
- no Redis, agent framework, vector database, browser automation, or second orchestration engine;
- one or more identical replicas permitted.

The service is outside the JarvisOS product runtime. It must not share JarvisOS SQLite authority, provider secrets, runtime egress state, or `C:\JarvisOS` data.

### 4.2 Canonical GitHub state

Canonical state lives on a protected branch provisionally named:

`jarvis-control`

in exactly one file:

`.jarvis/development-loop/authority.json`

The branch and file are repository-development authority only. They are not product runtime data.

Comments, checks, workflow runs, queue rows, database rows, dashboards, and digests are projections. They are rebuildable and never own a transition.

### 4.3 Non-authoritative PostgreSQL

PostgreSQL may contain only rebuildable operational state:

- webhook delivery IDs and payload digests;
- queued reconciliation jobs;
- bounded retry metadata;
- cached authority projections;
- provider request correlation metadata;
- notification dedupe;
- service health and audit summaries.

It must not contain the only copy of a grant, claim, lease, gate verdict, finding disposition, budget reservation, or terminal outcome.

A complete database loss may delay work but must not alter canonical authority.

## 5. Canonical encoding and integrity

### 5.1 JSON encoding

`authority.json` uses deterministic UTF-8 JSON:

- object keys sorted lexicographically;
- separators `,` and `:` with no insignificant whitespace;
- UTF-8 without BOM;
- timestamps in UTC RFC 3339 form ending in `Z`;
- integer quantities only for money, counters, durations, and sizes;
- no floating-point values, `NaN`, or infinity;
- SHA-256 digests encoded as lowercase `sha256:<64 hex>`.

The canonical byte representation is equivalent to:

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

The top-level v1 object is:

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
  "events": [],
  "terminal_event_digest": null
}
```

Requirements:

- `repository_id` is the immutable GitHub numeric repository ID.
- `sequence` equals the final event sequence, or zero for bootstrap.
- `snapshot` is derived entirely from `events`.
- rebuilding the snapshot must reproduce `snapshot_digest`.
- `terminal_event_digest` is null while a run is active and equals the final event digest after terminalization.
- unknown top-level or event fields are rejected in v1.
- v1 has no compaction.
- before writing event 4097 or exceeding 2,000,000 canonical bytes, the control plane halts with `authority_capacity_reached`; it does not truncate history.

### 5.3 Event schema

Every event contains:

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

- `sequence` is previous sequence plus one.
- `event_id` is `evt_` plus SHA-256 of the idempotency key bytes.
- `payload_digest` hashes canonical `payload`.
- `event_digest` hashes the canonical event excluding `event_digest`.
- `previous_event_digest` equals the preceding event digest, or null for bootstrap.
- reusing an idempotency key with non-identical bytes is an integrity failure.
- duplicate delivery with identical bytes is a no-op and returns the existing event.
- timestamps are evidence, not ordering authority; sequence and commit ancestry own order.

### 5.4 Double integrity chain

A valid transition requires both:

1. the in-file event hash chain; and
2. linear Git commit ancestry on `jarvis-control`.

A missing, reordered, altered, duplicated, forked, force-pushed, or non-linear control history causes `control_integrity_failure` and permits no external side effect.

## 6. Closed identifiers and enums

### 6.1 Identifier prefixes

- development run: `run_<32 hex>`
- authorization grant: `grant_<32 hex>`
- global claim: `claim_<32 hex>`
- branch lease: `lease_<32 hex>`
- gate collection: `gates_<32 hex>`
- review round: `review_<32 hex>`
- finding: `finding_<32 hex>`
- fix attempt: `fix_<32 hex>`
- provider request: `provider_<32 hex>`
- human decision request: `human_<32 hex>`

IDs are deterministic from the canonical idempotency key, never model-selected.

### 6.2 Actor roles

Closed v1 actor roles:

- `maintainer`
- `control`
- `implementer`
- `reviewer`
- `gate_collector`
- `system_reconciler`

No actor may assert a different role from the effective credential and installation identity.

### 6.3 States

Closed v1 states:

- `idle`
- `authorized`
- `claimed`
- `implementing`
- `awaiting_gates`
- `awaiting_review`
- `fix_required`
- `awaiting_re_review`
- `awaiting_maintainer`
- `terminal`
- `halted`

`terminal` and `halted` are not automatically releasable. A new run requires a new authorization event after reconciliation.

### 6.4 Terminal outcomes

Closed v1 terminal outcomes:

- `merged_by_maintainer`
- `closed_without_merge`
- `superseded_by_maintainer`
- `completed_without_pr`
- `authorization_revoked`
- `abandoned_after_human_decision`

Observing a maintainer merge may terminalize a run; it never means the App owned the merge.

### 6.5 Stop reasons

Closed v1 stop reasons include:

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

Generic `unknown`, `provider_error`, or `failed` is not an acceptable durable reason when a more precise reason exists.

## 7. Explicit authorization and revocation

### 7.1 Control issue

Readiness must bootstrap one dedicated GitHub issue number into the initial authority state. Only commands created in that issue are eligible.

The issue and comments are command inputs, not canonical authority. The Control App validates a command and records a canonical event before any claim or side effect.

### 7.2 Maintainer identity

Readiness records the allowed maintainer GitHub numeric user IDs and logins.

A command is eligible only when:

- the comment author numeric ID is allow-listed;
- the repository ID and control issue match bootstrap state;
- the comment is newly created, not edited into eligibility;
- the body contains exactly one recognized fenced command object;
- all named SHAs and repository facts are current when ingested.

Author association strings alone are insufficient.

### 7.3 Authorization command

The exact command surface is a fenced JSON block labelled `jarvis-authorization-v1`:

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

- `spec_id` is exactly three ASCII digits.
- `slice_id` is 1–80 lowercase ASCII characters, digits, `_`, or `-`.
- `base_sha` is the exact current base head when the grant is recorded.
- `allow_paths` and `deny_paths` are non-empty, normalized, repository-relative glob lists.
- deny wins over allow.
- `max_changed_files` is 1–100.
- `max_diff_lines` is 1–20,000.
- `max_fix_rounds` is 0–2.
- implementer and reviewer adapter IDs must be distinct approved effective identities.
- `expires_at`, when present, must be future UTC and cannot exceed 30 days after issue.
- the reason is stored only as bounded safe text, maximum 500 characters.

The normalized scope object is hashed into `scope_digest`.

The work branch is derived as `jarvis-work/<run_id>` and is never supplied by a model.

### 7.4 V0 requires explicit authorization

V0 never creates a grant from:

- a `ready` registry row alone;
- an open issue, branch, or PR;
- a label;
- a review verdict;
- a previous run;
- a schedule;
- a chat transcript;
- a model recommendation.

### 7.5 Revocation command

Revocation uses:

~~~~text
```jarvis-authorization-v1
{
  "command": "revoke",
  "repository_id": 123,
  "grant_id": "grant_<32 hex>",
  "reason": "Maintainer stop."
}
```
~~~~

A valid revocation:

- records `authorization_revoked`;
- blocks all new mutations and provider requests;
- attempts bounded cancellation only where the external action contract proves cancellation safe;
- enters `awaiting_maintainer` or terminal outcome `authorization_revoked`;
- never deletes commits, comments, findings, usage, or spend evidence.

Editing or deleting the original authorization comment does not revoke a recorded grant.

## 8. Canonical snapshot schema

The derived snapshot contains:

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
  "terminal_outcome": null
}
```

### 8.1 Authorization snapshot

The authorization snapshot binds:

- grant ID;
- source comment ID and body digest;
- maintainer numeric ID;
- spec and slice;
- exact base branch and SHA;
- normalized scope and digest;
- implementer/reviewer adapter IDs;
- budget policy ID;
- maximum fix rounds;
- issue, expiry, and revocation state.

### 8.2 Work snapshot

The work snapshot binds:

- derived work branch;
- exact current work head;
- PR number and base;
- branch ancestry status;
- current implementation attempt;
- changed file list, line count, and scope verification digest;
- last verified commit and actor.

### 8.3 Review snapshot

The review snapshot binds:

- initial review round 0 and up to two re-review rounds;
- reviewed exact head;
- reviewer effective identity;
- provider request ID and response digest;
- finding IDs and dispositions;
- whether code changed since the prior review;
- clean/inconclusive/findings verdict;
- next allowed round.

### 8.4 Budget snapshot

Money is integer micro-USD.

The snapshot binds:

- policy ID and version;
- per-request, run, day, and month ceilings;
- projected, reserved, finalized, released, and unknown amounts;
- provider and request IDs;
- reservation idempotency keys;
- call counts by role.

## 9. Repository-wide claim and work lease

### 9.1 Claim preconditions

`claim_acquired` is allowed only when:

- state is `authorized`;
- the grant is current and not revoked;
- the canonical registry and dependencies satisfy the grant;
- no other active product or implementation front exists;
- no overlapping or competing open PR, branch owner, or run exists;
- exact `master` head still equals the grant base SHA;
- scope and provider policies exist and are current;
- no security, secret, or spend stop is active.

The registry check is deterministic. A model never decides eligibility.

### 9.2 Global claim

The global claim is repository-wide and contains:

- claim ID;
- run ID and grant ID;
- spec, slice, and scope digest;
- base branch and SHA;
- derived work branch;
- claimant installation ID;
- acquired sequence and time;
- reconciliation deadline;
- first permitted action.

A losing or ambiguous claim writer performs zero external side effects.

### 9.3 Work lease

A work lease serializes mutation inside the claimed front.

V1 constants:

- lease duration: 60 minutes;
- renewal may begin only when 20 minutes or less remain;
- one active mutation request per lease;
- lease renewal does not change scope, round, adapter, or budget;
- lease expiry never releases the global claim.

After expiry, the system records `lease_expired_pending_reconciliation` and reconciles branch, PR, workflows, provider requests, comments, budget, and security state before any renewal or recovery.

### 9.4 Release

Only one of these canonical events may release a front:

- maintainer-observed terminal outcome;
- explicit authorization revocation;
- explicit maintainer `release` command defined by the later governance amendment;
- verified `completed_without_pr`;
- verified human closure or supersession.

A timer, database lease, stopped worker, closed browser session, failed webhook, or provider timeout never releases ownership.

## 10. Exact-head authority transition

### 10.1 Required algorithm

Every canonical transition uses the raw Git-object protocol:

1. GET exact `refs/heads/jarvis-control`.
2. Read the parent commit and tree.
3. Read and validate `authority.json`.
4. Rebuild snapshot and verify both integrity chains.
5. Re-read all transition preconditions from GitHub.
6. Compute one event and replacement authority bytes.
7. Create one blob.
8. Create one tree derived from the expected parent tree with only the authority path replaced.
9. Create one commit whose sole parent is the exact expected control-head SHA.
10. PATCH the control ref to the candidate commit with `force=false`.
11. Treat only an unambiguous successful update to the candidate commit as immediate success.
12. On rejection, timeout, disconnect, or ambiguous response, perform no side effect and reconcile.

The Contents API is forbidden as the authority compare-and-swap.

### 10.2 Ambiguous timeout reconciliation

After an ambiguous ref update:

1. reread the control ref;
2. if it equals the candidate commit, validate the candidate and treat the transition as committed;
3. if it descends from the candidate, rebuild and confirm the same event ID appears exactly once;
4. if the candidate is absent, the transition did not win;
5. if ancestry or event occurrence is ambiguous, record no new side effect and halt for human recovery.

A retry never creates a different event for the same idempotency key.

## 11. State machine and transition table

| Current state | Event | Preconditions | Next state | Side effect allowed after commit |
| --- | --- | --- | --- | --- |
| `idle` | `authorization_recorded` | valid maintainer command | `authorized` | none |
| `authorized` | `claim_acquired` | section 9.1 and successful ref CAS | `claimed` | create/verify work branch |
| `claimed` | `implementation_requested` | valid lease, scope, budget/provider authority | `implementing` | invoke one implementer request |
| `implementing` | `work_head_recorded` | exact descendant head, scope passes | `awaiting_gates` | request/observe deterministic gates |
| `awaiting_gates` | `gates_passed` | all required gates green on exact head | `awaiting_review` or `awaiting_re_review` | invoke one reviewer request |
| `awaiting_gates` | `gate_defect_reproduced` | in-scope deterministic reproduction | `implementing` | one bounded implementer repair |
| `awaiting_gates` | `gate_ambiguous_or_infra` | stale, flaky, cancelled, missing, action-required, infrastructure ambiguity | `halted` or `awaiting_maintainer` | none |
| `awaiting_review` | `review_clean` | valid structured review on exact head | `awaiting_maintainer` | presentation only |
| `awaiting_review` | `review_findings_recorded` | valid findings | `fix_required` | triage only |
| `fix_required` | `findings_disposed_no_change` | all findings false/superseded with evidence | `awaiting_re_review` | invoke one reviewer request |
| `fix_required` | `fix_requested` | genuine in-scope blocker, rounds remain, lease and budget valid | `implementing` | invoke one implementer fix |
| `fix_required` | `finding_requires_human` | scope, security, ambiguity, or rounds boundary | `awaiting_maintainer` | none |
| `awaiting_re_review` | `review_clean` | valid review on exact head | `awaiting_maintainer` | presentation only |
| `awaiting_re_review` | `review_findings_recorded` | valid findings and rounds remain | `fix_required` | triage only |
| `awaiting_re_review` | `maximum_rounds_reached` | negative result after round 2 | `awaiting_maintainer` | none |
| `awaiting_maintainer` | `human_merge_observed` | PR merged by allow-listed maintainer | `terminal` | none |
| `awaiting_maintainer` | `human_close_observed` | PR closed/deferred/superseded by maintainer | `terminal` | none |
| any non-terminal | `authorization_revoked` | valid revocation | `awaiting_maintainer` or `terminal` | bounded cancellation only |
| any non-terminal | `security_halt` | security signal | `halted` | none |
| `halted` | `human_recovery_recorded` | explicit maintainer recovery and reconciled facts | prior safe state or `terminal` | only the recorded recovery action |

No transition permits merge, auto-merge, priority changes, settings/secrets changes, branch deletion, or force-push.

## 12. Branch and scope contract

### 12.1 Work branch

- exactly one work branch: `jarvis-work/<run_id>`;
- created from the exact grant base SHA;
- no force-push;
- no branch deletion by the App or implementer;
- PR base must be `master`;
- forks are unsupported in v0.

### 12.2 Scope enforcement

Before every implementer request and after every resulting head:

- compute changed files against the grant base;
- normalize paths;
- enforce allow and deny patterns;
- enforce maximum changed files and diff lines;
- reject submodules, Git LFS pointer surprises, symlink escapes, binary additions, and generated secret files unless the full spec for the slice explicitly authorizes them;
- verify no commit has a parent outside the expected linear work-branch ancestry;
- bind the scope verification digest into the canonical event.

The following paths are denied unless named exactly in the grant and separately authorized:

- `AGENTS.md`
- `.github/workflows/**`
- `.github/CODEOWNERS`
- repository settings or ruleset exports
- secret, credential, `.env`, key, certificate, or token paths
- protected conformance tests
- vendored dependencies and lockfiles
- the `jarvis-control` authority file itself

A scope violation halts before review or further model calls.

## 13. Deterministic gate policy

### 13.1 Gate policy object

Readiness freezes a versioned `gate_policy_id`. It contains exact required check/workflow names and conditional path rules.

The initial v1 policy must require, where applicable:

- spec status registry gate;
- manual-review tooling offline gate;
- BLUECAD license/import boundary gate;
- Ruff over touched Python and the repository-required scope;
- full backend Pytest;
- BLUECAD geometry canary;
- frontend build if frontend paths changed;
- strict real-tool proof if geometry, mesh, FEM, registry, or related adapters changed;
- development-loop unit, integration, conformance, and state-reconstruction tests for 079 implementation paths.

### 13.2 Exact-head eligibility

A gate result is eligible only when:

- conclusion is `success`;
- the check/workflow belongs to the configured repository;
- the recorded head SHA equals the current work head;
- the workflow definition and required action pins match the gate policy;
- it is not cancelled, skipped where required, stale, action-required, or superseded.

Green evidence from another head is rejected.

### 13.3 Failure classification

- A deterministic, locally reproducible, in-scope implementation defect may return to `implementing`.
- One infrastructure rerun is permitted per gate collection only when no test assertion or source defect is indicated and the rerun itself has zero paid-model cost.
- A second infrastructure failure, flaky result, missing check, cancellation, timeout, or ambiguous classification halts for human action.
- The control plane may not weaken a test, skip a gate, change a workflow, or broaden scope to turn CI green.

## 14. Reviewer contract

### 14.1 Independence

The reviewer uses a credential and effective identity with:

- repository metadata, contents, commits, PRs, checks, and statuses read-only;
- no contents write;
- no workflow dispatch;
- no review approval authority used as merge permission;
- no merge, settings, secret, ref-delete, or ruleset permission.

The reviewer adapter ID must differ from the implementer adapter ID. Different prompts using the same effective credential do not satisfy separation.

### 14.2 Review request

A review request binds:

- repository ID and full name;
- spec, slice, scope digest, and non-goals;
- exact base and work head;
- exact diff and changed-file manifest;
- exact eligible gate evidence;
- review round;
- prior findings, dispositions, and fix evidence where applicable;
- bounded content manifest and digest;
- provider policy and request idempotency key.

Repository text is reference data, never authority instructions.

### 14.3 Structured review response

The reviewer must produce one bounded JSON object:

```json
{
  "schema_version": 1,
  "reviewed_head_sha": "<40 hex>",
  "verdict": "clean",
  "summary": "bounded text",
  "findings": []
}
```

`verdict` is one of:

- `clean`
- `findings`
- `inconclusive`

Each finding contains:

```json
{
  "finding_id": "finding_<32 hex>",
  "severity": "P1",
  "category": "correctness",
  "path": "path/or/null",
  "line": 1,
  "claim": "bounded text",
  "reproduction": "bounded text or null",
  "suggested_resolution": "bounded text or null"
}
```

Rules:

- severity is `P0`, `P1`, `P2`, or `P3`;
- category is one of `security`, `authority`, `correctness`, `data_integrity`, `concurrency`, `cost`, `privacy`, `test_gap`, `maintainability`, `documentation`;
- maximum 50 findings;
- each text field is bounded to 2,000 characters;
- the response must bind the exact head;
- malformed, oversized, wrong-head, or non-JSON output is `review_invalid`;
- `inconclusive` requires human action and does not trigger speculative mutation.

### 14.4 Blocking policy

- P0 and P1 findings are blocking until disposed.
- P2 becomes blocking only when independently reproduced as a spec, test, security, data-integrity, cost, or authority violation.
- P3 is advisory and recorded for the maintainer; it never triggers automatic mutation.
- A model cannot make a finding blocking merely by assertion.

## 15. Finding disposition and fix loop

Closed dispositions:

- `reproduced`
- `accepted_without_reproduction`
- `false_positive`
- `superseded`
- `needs_human`

Requirements:

- `reproduced` includes deterministic failing evidence or a precise current-code path.
- `accepted_without_reproduction` is permitted only when the finding directly contradicts a binding spec invariant and no runtime reproduction is possible before implementation.
- `false_positive` includes an evidence-backed rebuttal.
- `superseded` points to a later finding or head that makes the original inapplicable.
- `needs_human` stops automatic work.

V1 round limits:

- initial review round: 0;
- maximum fix rounds: 2;
- maximum total review calls: 3;
- maximum total implementer calls: 3;
- exactly one fix attempt may follow a negative review round;
- every code-changing fix requires exact-head deterministic gates before re-review;
- a no-change false-positive disposition still requires re-review with the rebuttal;
- a negative review after round 2 enters `awaiting_maintainer`;
- scope expansion, destructive action, governance change, secret change, or new dependency always enters `awaiting_maintainer`.

The implementer may not mark its own finding resolved by assertion.

## 16. Implementer adapter contract

The implementer adapter accepts one immutable request containing:

- repository and installation identity;
- work branch and exact expected head;
- spec and slice;
- normalized scope manifest and digest;
- binding non-goals;
- task type: `initial_implementation`, `gate_repair`, or `review_fix`;
- exact gate failure or disposed findings;
- maximum output tokens/time where applicable;
- provider and budget policy;
- request idempotency key.

The adapter returns:

- provider request ID;
- accepted/started/completed/ambiguous status;
- resulting commit/head SHA or no-change result;
- bounded safe summary;
- output and response digests;
- usage and finalized cost evidence;
- provider-side idempotency evidence;
- error classification.

Requirements:

- the adapter cannot change the base, branch, scope, spec, tests, provider, or budget;
- it may create commits only on the recorded work branch;
- it may not merge, approve, force-push, delete refs, modify settings/secrets, or write `jarvis-control`;
- if the provider cannot guarantee request idempotency, an ambiguous post-acceptance timeout halts without retry;
- direct shell or tool authority is limited by the adapter and slice scope, not by model text;
- output is untrusted until GitHub state, ancestry, scope, and gates are revalidated.

## 17. Spend and provider authority

### 17.1 Separate development budget authority

Runtime policy 059b does not govern repository-development agents.

The development loop uses a versioned repository-development budget policy approved by the governance and readiness steps.

### 17.2 Money and ceilings

All monetary values are integer micro-USD.

Hard v1 absolute ceilings:

- per provider request: 5,000,000 micro-USD;
- per development run: 20,000,000 micro-USD;
- per UTC day: 25,000,000 micro-USD;
- per calendar month: 100,000,000 micro-USD.

Defaults are zero for every cap. Readiness may set lower non-zero values but may not exceed these ceilings without a new spec amendment.

`cost_unknown` is a hard stop.

An included subscription/quota may use projected marginal cost zero only when the adapter can prove:

- the exact account/plan basis;
- remaining bounded quota or seat entitlement;
- no per-request marginal charge for the requested operation;
- a versioned evidence timestamp.

Otherwise the cost is unknown.

### 17.3 Reservation

Before every paid or quota-consuming request, one canonical event reserves the projected amount and call count.

A dispatch is forbidden when:

- reservation is absent;
- any cap would be exceeded;
- provider price basis is stale;
- the request would exceed role call limits;
- fallback would use a different provider or higher cost;
- cost or quota is unknown.

Final usage either finalizes or releases the reservation. No fallback provider is authorized in v1.

### 17.4 Hosting and Actions cost

Hosting and GitHub Actions cost are recorded separately from model requests.

They do not require per-transition reservation in v1, but readiness must record:

- plan and account basis;
- included usage;
- monthly ceiling;
- notification threshold;
- method and cadence for reconciliation.

A budget overrun or inability to determine continuing cost disables new external actions.

## 18. Content, secrets, and prompt-injection boundary

Before any external model request:

- material is limited to the exact spec, scope, diff, findings, and gate evidence needed for the task;
- secrets, credentials, environment values, private keys, tokens, authorization headers, and unrelated project records are excluded;
- untrusted issue, PR, source, test, artifact, and log text is clearly delimited as data;
- model-visible text cannot change policy, role, provider, budget, tests, scope, or merge authority;
- a deterministic policy layer constructs the request; the model never constructs its own authority envelope;
- S4 or secret-bearing repository content is denied unless a later explicit repository-development egress spec authorizes it.

No raw provider request or response body is stored in the canonical authority file. Safe digests, bounded summaries, IDs, usage, and cost evidence are permitted.

## 19. GitHub App permissions and rulesets

### 19.1 Control App candidate permissions

Minimum candidate installation permissions:

- metadata: read;
- contents: read/write;
- pull requests: read/write;
- checks: read;
- commit statuses: read;
- actions: read;
- issues: read/write.

Actions write is absent unless a later readiness decision proves that exact workflow dispatch or rerun is required. Administration, environments, secrets, members, deployments, packages, security-alert mutation, hook mutation, and ruleset bypass are denied.

### 19.2 Credential separation

Use separate effective credentials for:

1. Control App;
2. implementer actuator;
3. reviewer actuator;
4. human maintainer.

The Control App credential is never provided directly to a model.

### 19.3 `master` ruleset

Readiness must prove:

- pull request required;
- force-push and deletion denied;
- required deterministic checks enforced;
- Control App, implementer, and reviewer have no bypass;
- auto-merge disabled for the actors;
- only the human maintainer can merge under repository governance.

### 19.4 `jarvis-control` ruleset

Readiness must prove:

- only the Control App and explicit human recovery identity may update;
- force-push and deletion denied;
- linear history required;
- update by non-fast-forward ref change rejected;
- no model or implementer credential can write;
- recovery operations are audited and require explicit maintainer action.

### 19.5 Work-branch rules

For `jarvis-work/*`:

- only the approved implementer identity and maintainer may write;
- force-push and deletion by automated actors denied;
- PR base restricted to `master`;
- Control App may read and record but does not author engineering commits;
- reviewer remains read-only.

Permissions are coarse. The implementation also requires a capability wrapper that allow-lists repository ID, endpoint, method, ref, path pattern, transition state, and request schema. Every denied attempt is audited.

## 20. Webhook, queue, and service API

### 20.1 Subscribed GitHub events

V1 subscribes only to required events:

- `issue_comment` created;
- `push` on `master`, `jarvis-control`, and the active work branch;
- `pull_request`;
- `pull_request_review`;
- `pull_request_review_comment`;
- `workflow_run`;
- GitHub App installation suspension or deletion events.

Edited authorization comments do not create authority. Other events are ignored after signature and repository validation.

### 20.2 Webhook handler

`POST /github/webhook`:

- validates HTTPS termination and GitHub signature before JSON processing;
- validates installation and repository ID;
- computes payload digest;
- stores delivery ID and digest;
- returns within 10 seconds;
- performs no model call, branch mutation, workflow dispatch, or canonical transition in the request thread;
- queues one reconciliation job.

Duplicate delivery IDs with different payload digests are a security signal.

### 20.3 Other HTTP endpoints

V1 exposes only:

- `GET /healthz` — process liveness, no repository detail;
- `GET /readyz` — database and required-secret readiness, no secret values;
- `POST /github/webhook`.

There is no public admin mutation endpoint in v1. Authorization, revocation, release, and recovery originate through validated GitHub maintainer commands and canonical events.

### 20.4 Queue behavior

- PostgreSQL job claiming may use transactional `FOR UPDATE SKIP LOCKED`;
- queue ownership is operational only;
- duplicate jobs converge through canonical idempotency;
- pure read/reconciliation jobs may retry at most five times with bounded exponential backoff;
- no side-effecting request retries unless the canonical event and adapter idempotency contract make duplication impossible;
- webhook order is never trusted.

### 20.5 Retention and recovery objectives

- delivery ID, event name, and payload digest: 30 days;
- queue attempts and projections: 90 days;
- service logs: 30 days;
- no raw model bodies, secret values, or authorization headers in logs;
- GitHub authority RPO: zero committed canonical events;
- non-authoritative database RPO: 24 hours;
- service RTO target: 4 hours;
- GitHub outage: stop indefinitely rather than act from stale cache.

## 21. Presentation and maintainer notifications

The service may maintain:

- one non-authoritative check run named `Jarvis Development Loop`;
- one sticky PR status comment;
- one dedicated control-issue status comment;
- one weekly digest.

Presentation updates occur only after a canonical state change and are idempotent.

Between weekly reviews, direct maintainer notification is allowed only for:

- a human decision;
- a security signal;
- a budget overrun or disabled cost authority.

Routine progress, provider liveness, and inactivity do not generate repeated notifications.

Weekly digest v1:

- timezone `Europe/Rome`;
- Monday at 08:00 local time;
- at most one digest per seven-day window;
- omitted when no canonical state changed;
- never releases a claim, authorizes a transition, selects a provider, or implies merge consent.

## 22. Security and supply-chain contract

The implementation must:

- verify webhook signatures using constant-time comparison;
- use short-lived installation tokens;
- keep App private key, webhook secret, database credential, and provider credentials in the hosting secret store;
- rotate/revoke credentials without editing canonical history;
- pin GitHub Actions and deployment dependencies to immutable versions/digests;
- generate an SBOM for the service image;
- scan dependencies and container image before deployment;
- deny untrusted fork execution with write-capable or secret-bearing credentials;
- never execute code from a PR in the webhook process;
- validate all GitHub API response repository IDs and SHAs;
- use outbound allow-listing for GitHub and approved provider endpoints;
- record security stops without storing sensitive payload bodies.

A suspected compromised credential, signature failure, control-history anomaly, duplicate delivery mismatch, scope escape, or secret exposure records `security_signal` and halts all new side effects.

## 23. Verification and acceptance

### 23.1 Offline unit tests

Prove:

1. deterministic canonical JSON and digest vectors;
2. event chain and snapshot reconstruction;
3. duplicate idempotency convergence;
4. invalid schema, unknown field, float, bad timestamp, and digest rejection;
5. state-transition allow/deny matrix;
6. authorization and revocation parsing;
7. maintainer identity and edited-comment rejection;
8. scope normalization, deny precedence, diff limits, and path escape rejection;
9. budget reservation/finalization and every cap;
10. finding normalization and blocking policy;
11. lease renewal, expiry, and non-release;
12. provider ambiguous-timeout halt;
13. presentation and notification dedupe.

### 23.2 Offline integration tests

With fake GitHub, PostgreSQL, implementer, and reviewer actors, prove:

1. process/database restart reconstructs the same state;
2. duplicate webhooks and queue jobs create one canonical effect;
3. changed work head invalidates gate and review evidence;
4. a reproducible gate defect returns to implementation;
5. infrastructure ambiguity does not mutate code;
6. clean review stops at `awaiting_maintainer`;
7. genuine finding creates one bounded fix;
8. false-positive no-change path still re-reviews;
9. maximum rounds stop without further provider calls;
10. revoke and every kill switch prevent new actions;
11. no actor can merge or approve its own work;
12. inactivity creates no model call or repeated comment.

### 23.3 Disposable-repository real-tool proofs

Before readiness, use a disposable repository or isolated organization fixture and prove:

1. at least two dispatchers race from one vacant control ref; exactly one wins;
2. a ref advance with unchanged authority blob rejects the stale candidate;
3. stale blob, tree, parent, and ref identities fail closed;
4. timeout after successful ref update reconciles without duplicate event or action;
5. duplicate and replayed webhook delivery converges after database loss;
6. authority reconstruction succeeds after deleting all external state;
7. altered, removed, reordered, or forked history causes an integrity halt;
8. lease expiry while a worker remains active starts no new claimant;
9. changed work head invalidates prior CI and review;
10. Control App, implementer, and reviewer credentials are denied merge;
11. automated credentials are denied force-push, ref deletion, settings/secrets mutation, and out-of-scope writes;
12. reviewer cannot write and implementer cannot submit authoritative review;
13. untrusted fork code cannot access secrets or write;
14. prompt-injection fixtures cannot change scope, role, provider, budget, tests, or merge authority;
15. exceeded and unknown cost make zero provider calls;
16. provider timeout cannot create an untracked duplicate request or charge;
17. GitHub outage pauses and later reconciles without duplicate action;
18. every independent kill switch stops new effects;
19. Actions concurrency/cancellation cannot release authority;
20. inactivity and duplicate events create no repeated model calls or notifications.

### 23.4 Repository gates

The full implementation must pass:

```bash
cd backend
python -m pytest -q
python -m ruff check app tests
python ../scripts/check_spec_status.py --self-test
```

and the existing repository CI/canary gates.

The new service must provide deterministic commands, expected initially as:

```bash
python -m pytest -q services/devloop/tests
python -m ruff check services/devloop
```

Exact commands and dependency pins are frozen by readiness after the implementation skeleton is reviewed.

No CI test may call a live model, require a paid service, or mutate the production repository.

### 23.5 Maintainer-owned conformance evidence

Before implementation, the readiness owner must add or separately freeze protected conformance fixtures for:

- state transitions;
- two-writer race outcome;
- exact-head invalidation;
- merge/permission denial;
- maximum rounds;
- cost stops;
- kill switches.

The implementation agent may not weaken those fixtures.

## 24. Rollout, governance, readiness, and kill switches

### 24.1 Required governance amendment

A separate PR must amend `AGENTS.md` narrowly to state:

> A merged readiness decision for spec 079 may authorize automatic implementer and reviewer dispatch only for the one canonical development run whose maintainer-authored grant, global claim, work branch, exact head, scope, provider identities, deterministic gates, round limits, and budget are current in the protected 079 authority ledger. This exception does not authorize automatic spec selection, merge, auto-merge, priority changes, workflow or ruleset bypass, force-push, branch deletion, secrets/settings changes, destructive actions, scope expansion, provider fallback, or work after a security, cost, integrity, or human-decision stop.

The amendment must also reconcile the current manual-only review and explicit-only Codex clauses without weakening the human merge boundary.

This full-spec PR does not apply that amendment.

### 24.2 Rollout phases

1. **Documentation:** merge this full spec with 079 still `planned`.
2. **Governance:** merge the narrow AGENTS.md amendment.
3. **Offline implementation skeleton:** deterministic schemas, state machine, fake adapters, no App installation.
4. **Disposable-repository proof:** GitHub App, rulesets, fake actors, PostgreSQL, all section 23.3 proofs.
5. **Shadow mode on JarvisOS:** read-only reconciliation and presentation; no claims, branch writes, workflow dispatch, or providers.
6. **Readiness decision:** record exact host, App IDs, rulesets, credentials, provider adapters, prices/caps, proof outputs, owners, and rollback.
7. **Implementation activation:** only after the registry is `ready`, then `in_progress`; first live run must be a low-risk documentation-only slice with explicit grant and zero merge authority.
8. **Broader use:** separately approved after the first run is reviewed and cost/security evidence is accepted.

### 24.3 Independent kill switches

V1 requires all of:

1. canonical `security_halt` or maintainer halt event;
2. suspend the GitHub App installation;
3. revoke/rotate App private key and webhook secret;
4. revoke provider credentials;
5. stop service replicas and queue consumers;
6. set provider caps to zero;
7. disable any selected dispatch workflow;
8. protected human-only recovery from the last verified control commit.

A repository variable may be defense in depth but is not canonical authority.

Rollback means halt, reconstruct, and record. It never means force-push, delete canonical events, erase findings, or remove spend evidence.

### 24.4 Readiness evidence required

079 remains `planned` until a dated readiness PR proves:

- all dependencies remain merged;
- no active competing front exists;
- architecture and full spec are merged;
- governance amendment is merged;
- disposable-repository proofs all pass;
- exact App permissions and rulesets are captured;
- all automated credentials fail merge and abuse tests;
- host, PostgreSQL, retention, RTO/RPO, and secret custody are selected;
- implementer/reviewer adapters and effective identities are selected;
- provider price/quota evidence is current;
- non-zero caps, if any, are explicitly approved and within section 17 ceilings;
- deterministic gate policy and conformance fixtures are frozen;
- implementation owner and rollback owner are named;
- the first activation slice is explicitly bounded;
- no unresolved P0/P1 or authority/security blocker remains.

Only that PR may move 079 to `ready`.

## 25. Compatibility and migration

- No JarvisOS runtime SQLite schema or migration is authorized.
- No existing AI execution spine, 059b runtime budget, Hermes state, MemoryStore, BLUECAD state, or product event table becomes control-plane authority.
- The hosted service PostgreSQL schema starts at v1 and remains rebuildable.
- Bootstrap creates a new protected control branch through explicit maintainer action; no chat, comment history, old branch, or old PR is imported as authority.
- Existing branches and PRs are not adopted unless an explicit grant names their exact base, branch, scope, and reconciliation result; v1 normally creates a fresh derived work branch.
- Existing manual review workflows remain manual until the governance amendment and readiness decision explicitly authorize the 079 path.
- Schema changes to `authority.json` require additive versioning and a separately reviewed migration proof. A v1 reader encountering another version halts.
- No force-push or history rewrite is a migration mechanism.

## 26. Likely implementation scope

Verify against then-current `master`. Expected bounded paths:

- `services/devloop/` — service, schemas, policy, GitHub client, queue, adapters, tests;
- a minimal service dependency/lock manifest and OCI container definition;
- deterministic fake GitHub, implementer, and reviewer fixtures;
- deployment documentation containing no secret;
- `docs/specs/STATUS.md` only for the normal implementation-state transition;
- existing CI only where required to run offline service tests.

Not part of the implementation PR:

- `AGENTS.md` governance amendment, which must merge first in its own PR;
- live repository settings, App installation, rulesets, or secrets, which are human readiness actions;
- provider credentials or raw price/account data;
- product backend/frontend/runtime modules;
- Hermes, MCP, MemoryStore, BLUECAD modeling, or process-kernel work.

A new dependency must be pinned, justified, scanned, and limited to the service. Do not add an agent framework.

## 27. Binding non-goals

079 v0 does not provide:

- automatic selection of the next spec or backlog item;
- multiple simultaneous fronts, branches, implementers, or reviewers;
- autonomous merge, approval, auto-merge, release, or deployment;
- autonomous priority, roadmap, governance, ruleset, or secret changes;
- force-push, branch deletion, history rewrite, or protected-test mutation;
- arbitrary shell access outside the adapter and scope contract;
- provider fallback, provider bidding, model routing, or an AI swarm;
- unbounded review/fix loops;
- execution from untrusted forks;
- a replacement for JarvisOS runtime 059b, Hermes, or GitHub Actions;
- storage of model bodies or repository secrets in canonical state;
- guaranteed availability during GitHub, host, database, or provider outage;
- implementation of spec 078 or any other frozen product front.

## 28. Definition result

The full-spec step is complete when:

- this document replaces the planning kernel on a PR based on current `master`;
- 079 remains `planned` with no Implementation PR;
- architecture, schemas, state machine, APIs, permissions, cost ceilings, tests, rollout, compatibility, and kill switches are explicit;
- the ref-level CAS remains proof-gated rather than asserted as proven;
- no runtime, workflow, App, provider, secret, ruleset, dependency, or repository setting is created or changed;
- deterministic repository gates pass on the exact PR head;
- review findings are resolved;
- the PR stops for the maintainer’s merge decision.

Merging this full specification does not authorize the governance amendment, readiness promotion, implementation, external provider calls, or any automated merge.
