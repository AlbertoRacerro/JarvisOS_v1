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
- explicit authorization, revocation, recovery, terminalization, and release;
- repository-wide claim and work-branch lease;
- exact-head branch and pull-request lifecycle;
- state machine and transition table;
- exact-parent Git ref compare-and-swap;
- webhook, queue, and reconciliation behavior;
- implementer and reviewer adapter contracts;
- deterministic gate policy;
- finding, fix, and re-review semantics;
- spend, secret, permission, and content boundaries;
- deployment class, retention, recovery objectives, and notifications;
- tests, isolated proofs, rollout, kill switches, and compatibility.

This document does not:

- install or configure a GitHub App;
- create a hosted service, queue, database, secret, ruleset, branch, or workflow;
- modify `AGENTS.md` or `STATUS.md`;
- invoke Codex, Claude, another model, or a paid service;
- authorize implementation while 079 remains `planned`;
- authorize a governance amendment, readiness promotion, repository-setting change, merge, or auto-merge.

The implementation contract becomes actionable only after the separate governance amendment and dated readiness decision in section 24.

## 3. Binding repository invariants

Any 079 implementation must preserve all of the following:

1. `docs/specs/STATUS.md` is the only live roadmap and status authority.
2. Only one product or implementation front may be active repository-wide.
3. A planning document, branch, PR, issue label, review, check, workflow run, timer, or model message is not authorization.
4. V0 starts only from a maintainer-authored command naming the exact spec, slice, base SHA, scope, adapters, and budget policy.
5. Deterministic gates and human review inform readiness; the maintainer alone owns merge.
6. The reviewer is advisory and cannot mutate code.
7. The implementer cannot supply the authoritative review verdict.
8. No automated actor may merge, enable auto-merge, force-push, delete protected refs, change secrets/settings, or bypass branch protection.
9. Paid or external-model work requires explicit repository-development content, provider, credential, and budget authority separate from runtime policy 059b.
10. Frozen, `planned`, `blocked`, cancelled, or dependency-incomplete work is never selected automatically.
11. Lease expiry, inactivity, process death, or a timer never releases the active front.
12. Safety takes precedence over liveness; the control plane is allowed to stop indefinitely.

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

Canonical state lives on a protected branch provisionally named:

`jarvis-control`

in exactly one file:

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

It must not contain the only copy of a grant, claim, lease, PR binding, gate verdict, finding disposition, budget reservation, terminal outcome, or release decision.

A complete database loss may delay work but must not alter canonical authority.

## 5. Canonical encoding and integrity

### 5.1 Deterministic JSON

`authority.json` uses deterministic UTF-8 JSON:

- object keys sorted lexicographically;
- separators `,` and `:` with no insignificant whitespace;
- UTF-8 without BOM;
- timestamps in UTC RFC 3339 form ending in `Z`;
- integer quantities only for money, counters, durations, and sizes;
- no floating-point values, `NaN`, or infinity;
- SHA-256 digests encoded as lowercase `sha256:<64 hex>`.

The canonical bytes are equivalent to:

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
  "events": []
}
```

Requirements:

- `repository_id` is the immutable GitHub numeric repository ID.
- `sequence` equals the final event sequence, or zero for bootstrap.
- `snapshot` is derived entirely from `events`.
- rebuilding the snapshot must reproduce `snapshot_digest`.
- unknown top-level or event fields are rejected in v1.
- v1 has no compaction.
- before event 4097 or 2,000,000 canonical bytes, the control plane halts with `authority_capacity_reached`; it never truncates history.

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
- `event_id` is `evt_` plus SHA-256 of the idempotency-key bytes.
- `payload_digest` hashes canonical `payload`.
- `event_digest` hashes the canonical event excluding `event_digest`.
- `previous_event_digest` equals the preceding event digest, or null for bootstrap.
- reusing an idempotency key with non-identical bytes is an integrity failure.
- duplicate delivery with identical bytes is a no-op returning the existing event.
- timestamps are evidence, not ordering authority; sequence and commit ancestry own order.

### 5.4 Double integrity chain

A valid transition requires both:

1. the in-file event hash chain; and
2. linear Git commit ancestry on `jarvis-control`.

A missing, reordered, altered, duplicated, forked, force-pushed, or non-linear control history causes `control_integrity_failure` and permits no external side effect.

## 6. Closed identifiers, roles, states, and outcomes

### 6.1 Identifier prefixes

- development run: `run_<32 hex>`
- authorization grant: `grant_<32 hex>`
- global claim: `claim_<32 hex>`
- branch lease: `lease_<32 hex>`
- PR operation: `pr_<32 hex>`
- gate collection: `gates_<32 hex>`
- review round: `review_<32 hex>`
- finding: `finding_<32 hex>`
- fix attempt: `fix_<32 hex>`
- provider request: `provider_<32 hex>`
- human decision request: `human_<32 hex>`

IDs are deterministic from canonical idempotency keys and are never model-selected.

### 6.2 Actor roles

Closed v1 roles:

- `maintainer`
- `control`
- `implementer`
- `reviewer`
- `gate_collector`
- `system_reconciler`

No actor may assert a role different from its effective credential and installation identity.

### 6.3 States

Closed v1 states:

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

`terminal` may return to `idle` only through the explicit, fully reconciled `front_released` transition. `halted` must first be recovered to a safe non-halted state or terminalized by a valid maintainer recovery command.

### 6.4 Terminal outcomes

Closed v1 outcomes:

- `merged_by_maintainer`
- `closed_without_merge`
- `superseded_by_maintainer`
- `completed_without_pr`
- `authorization_revoked`
- `abandoned_after_human_decision`

Observing a maintainer merge terminalizes the run; it never means the App owned the merge.

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

Generic `unknown`, `provider_error`, or `failed` is not acceptable when a more precise reason exists.

## 7. Explicit authorization, revocation, recovery, and release

### 7.1 Control issue and maintainer identity

Readiness bootstraps one dedicated GitHub issue number and an allow-list of maintainer numeric user IDs into initial authority state.

A command is eligible only when:

- the author numeric ID is allow-listed;
- repository ID and issue match bootstrap state;
- the comment is newly created, not edited into eligibility;
- the body contains exactly one recognized fenced command object;
- every named SHA and repository fact is current when ingested.

The issue and comments are command inputs, not canonical authority. A canonical event must commit before any side effect.

### 7.2 Authorization command

The exact command surface is:

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
- `base_sha` equals the exact current base head when recorded.
- allow and deny lists are non-empty normalized repository-relative globs; deny wins.
- `max_changed_files` is 1–100.
- `max_diff_lines` is 1–20,000.
- `max_fix_rounds` is 0–2.
- implementer and reviewer adapter IDs are distinct approved effective identities.
- expiry, when present, is future UTC and at most 30 days after issue.
- reason is bounded safe text, maximum 500 characters.

The normalized scope is hashed into `scope_digest`. The work branch is derived as `jarvis-work/<run_id>` and is never model-supplied.

V0 never derives authorization from a `ready` row alone, a schedule, branch, PR, label, review, chat transcript, or previous run.

### 7.3 Revocation command

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

A valid revocation records `authorization_revoked`, blocks new mutations and provider requests, attempts only proven-safe bounded cancellation, and enters `awaiting_maintainer` or terminal outcome `authorization_revoked`. It never erases commits, findings, usage, or spend evidence.

### 7.4 Recovery command

~~~~text
```jarvis-authorization-v1
{
  "command": "recover",
  "repository_id": 123,
  "run_id": "run_<32 hex>",
  "expected_control_head": "<40 lowercase hex>",
  "action": "resume",
  "target_state": "awaiting_maintainer",
  "reason": "Facts reconciled and safe state selected."
}
```
~~~~

`action` is `resume` or `terminalize`. Recovery binds the exact control head and independently reconciles repository, branch, PR, workflow, provider, budget, lease, and security facts. Security stops require referenced remediation evidence. The target must be reachable under section 11.

### 7.5 Release command and `terminal → idle`

Release is accepted only from canonical `terminal` and only after reconciliation proves:

- terminal outcome is recorded;
- no implementer, reviewer, workflow dispatch, provider request, reservation, or cancellation remains active or ambiguous;
- work branch and PR facts match the recorded terminal outcome;
- expected control head is current;
- no unresolved integrity or security anomaly exists.

~~~~text
```jarvis-authorization-v1
{
  "command": "release",
  "repository_id": 123,
  "run_id": "run_<32 hex>",
  "grant_id": "grant_<32 hex>",
  "expected_control_head": "<40 lowercase hex>",
  "reason": "Release the reconciled terminal front."
}
```
~~~~

A successful ref-CAS appends exactly one `front_released` event and derives an `idle` snapshot with all active-run fields cleared:

- `run_id`, authorization, claim, lease, work, gates, review, active budget reservations, next action, stop, and active terminal outcome become null;
- cumulative budget evidence, completed run identity, terminal outcome, PR/branch bindings, findings, usage, and every prior event remain immutable in history;
- the event chain and Git ancestry continue monotonically; no file truncation, branch deletion, PR closure, force-push, or history rewrite occurs.

Duplicate identical release commands are no-ops returning the existing event. A release from any non-terminal state, or with active/ambiguous external work, fails closed. A later run requires a new authorization command from canonical `idle`.

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
  "terminal_outcome": null,
  "last_completed_run": null
}
```

### 8.1 Authorization snapshot

Binds grant ID, command comment ID/body digest, maintainer numeric ID, spec, slice, exact base, normalized scope/digest, adapter IDs, budget policy, round limit, issue, expiry, and revocation state.

### 8.2 Work snapshot

Binds derived branch, exact head, PR number/base/head binding, PR state, ancestry status, current implementation attempt, changed files/lines, scope-verification digest, and last verified commit actor.

### 8.3 Review snapshot

Binds review round, exact reviewed head, effective reviewer identity, provider request/response digest, finding IDs/dispositions, clean/inconclusive/findings verdict, code-change flag, and next allowed round.

### 8.4 Budget snapshot

Money is integer micro-USD. The snapshot binds policy/version, request/run/day/month ceilings, projected/reserved/finalized/released/unknown amounts, provider/request IDs, reservation keys, and role call counts.

## 9. Repository-wide claim, work branch, and lease

### 9.1 Claim preconditions

`claim_acquired` is allowed only when:

- state is `authorized`;
- grant is current and not revoked;
- registry and dependencies satisfy the grant;
- no other active product or implementation front exists;
- no competing PR, branch owner, or run exists;
- exact `master` head equals grant base SHA;
- scope, provider, budget, and gate policies are current;
- no security, secret, integrity, or spend stop is active.

The successful `claim_acquired` transition atomically records the global claim and initial 60-minute work lease. A losing or ambiguous writer performs zero side effects.

### 9.2 Control-App create-only work-branch capability

After claim success, the Control App receives one narrowly constrained create-only operation:

- endpoint/action: create `refs/heads/jarvis-work/<run_id>` only;
- repository: exact recorded numeric repository ID;
- target SHA: exact grant base SHA;
- precondition: ref absent, current canonical state `claimed`, matching claim/lease/scope;
- idempotency: an existing ref is accepted only when its name and SHA match exactly;
- prohibition: the Control App may not subsequently update, force-update, or delete that work ref and may not author engineering commits.

After creation or exact reconciliation, the App commits `work_branch_recorded`. A pre-existing mismatched ref, ambiguous response, or unexpected ancestry halts before implementer dispatch.

Subsequent work-branch mutation is implementer-only under the active lease, with the human maintainer retaining emergency authority.

### 9.3 Work lease

V1 constants:

- duration: 60 minutes;
- renewal window: 20 minutes or less remaining;
- one active mutation request per lease;
- renewal cannot alter scope, round, adapter, or budget;
- expiry never releases the global claim.

Every renewal is a canonical `lease_renewed` event committed before additional mutation. Database heartbeats do not renew authority. Expiry records `lease_expired_pending_reconciliation`; branch, PR, workflows, provider requests, comments, budget, and security facts must be reconciled before renewal or recovery.

## 10. Exact-head authority transition

Every canonical transition uses the raw Git-object protocol:

1. GET exact `refs/heads/jarvis-control`.
2. Read parent commit, tree, and authority blob.
3. Validate schema, event chain, snapshot, and Git ancestry.
4. Re-read transition preconditions from GitHub.
5. Compute one deterministic event and replacement authority bytes.
6. Create replacement blob.
7. Create a tree derived from the expected parent tree with only the authority path replaced.
8. Create a commit whose sole parent is the exact expected control-head SHA.
9. PATCH the control ref to that commit with `force=false`.
10. Treat only an unambiguous update to the candidate commit as immediate success.
11. On rejection, timeout, disconnect, or ambiguity, perform no side effect and reconcile.

The Contents API is forbidden as the authority compare-and-swap.

After an ambiguous ref update:

- if the ref equals the candidate, validate it and treat the transition as committed;
- if the ref descends from the candidate, confirm the same event ID appears exactly once;
- if the candidate is absent, it did not win;
- if ancestry or event occurrence remains ambiguous, halt for human recovery.

A retry never creates a different event for the same idempotency key.

## 11. Closed state machine and transition table

| Current state | Event | Preconditions | Next state | Side effect permitted after commit |
| --- | --- | --- | --- | --- |
| `idle` | `authorization_recorded` | valid maintainer command | `authorized` | none |
| `authorized` | `claim_acquired` | section 9.1 plus successful CAS | `claimed` | create or reconcile exact work ref |
| `claimed` | `work_branch_recorded` | derived ref exists at grant base | `claimed` | none |
| any active state | `lease_renewed` | current lease and reconciled facts | same | none |
| `claimed` | `implementation_requested` | recorded branch, lease, scope, adapter, budget | `implementing` | invoke one implementer request |
| `implementing` | `work_head_recorded` | exact descendant head and scope pass, or bounded no-change result | `awaiting_pr` | none |
| `awaiting_pr` | `pr_creation_authorized` | exact branch/head/base; no conflicting PR; idempotency key current | `awaiting_pr` | create or reconcile one PR |
| `awaiting_pr` | `pr_recorded` | exactly one matching open PR bound to exact branch/base and current head | `awaiting_gates` | request or observe deterministic gates |
| `awaiting_gates` | `gates_passed` | all required gates green on exact head and PR recorded | `awaiting_review` or `awaiting_re_review` | invoke one reviewer request |
| `awaiting_gates` | `gate_defect_reproduced` | deterministic in-scope reproduction | `implementing` | one bounded implementer repair |
| `awaiting_gates` | `gate_ambiguous_or_infra` | stale, flaky, cancelled, missing, action-required, or infrastructure ambiguity | `halted` or `awaiting_maintainer` | none |
| `awaiting_review` | `review_clean` | valid structured review on exact head | `awaiting_maintainer` | presentation only |
| `awaiting_review` | `review_findings_recorded` | valid findings on exact head | `fix_required` | deterministic triage only |
| `fix_required` | `findings_disposed_no_change` | all findings false/superseded with evidence | `awaiting_re_review` | invoke one re-review request |
| `fix_required` | `fix_requested` | genuine in-scope blocker, rounds/lease/budget valid | `implementing` | invoke one implementer fix |
| `fix_required` | `finding_requires_human` | scope, security, ambiguity, dependency, or round boundary | `awaiting_maintainer` | none |
| `awaiting_re_review` | `review_clean` | valid review on exact head | `awaiting_maintainer` | presentation only |
| `awaiting_re_review` | `review_findings_recorded` | valid findings and rounds remain | `fix_required` | deterministic triage only |
| `awaiting_re_review` | `maximum_rounds_reached` | negative review after round 2 | `awaiting_maintainer` | none |
| `awaiting_maintainer` | `human_merge_observed` | recorded PR merged by allow-listed maintainer | `terminal` | none |
| `awaiting_maintainer` | `human_close_observed` | recorded PR closed/deferred/superseded by maintainer | `terminal` | none |
| any non-terminal | `authorization_revoked` | valid revocation | `awaiting_maintainer` or `terminal` | proven-safe cancellation only |
| any non-terminal | `security_halt` | authenticated compromise evidence or verified anomaly | `halted` | none |
| `halted` | `human_recovery_recorded` | valid recovery plus reconciled facts | reachable safe state or `terminal` | only recorded recovery action |
| `terminal` | `front_released` | section 7.5 command and full reconciliation | `idle` | none |

No transition permits merge, auto-merge, authoritative approval, priority changes, settings/secrets changes, branch deletion, or force-push.

### 11.1 Idempotent pull-request creation and recording

`pr_creation_authorized` is required before the App calls the PR creation endpoint. Its idempotency key binds repository ID, run ID, work branch, exact work head, base branch, scope digest, and operation version.

The App then reconciles all PRs for the derived head branch:

- zero matching PRs: create exactly one non-draft PR with base `master`, head `jarvis-work/<run_id>`, and a bounded machine-readable marker containing run ID and scope digest;
- exactly one matching open PR with correct base/head/run marker: reuse it;
- more than one matching PR, wrong base, wrong head branch, missing or conflicting run marker, unexpected fork, or unknown state: fail closed with `pr_mismatch` or `pr_ambiguous`;
- a previously recorded PR closed by the maintainer: do not create a replacement; reconcile to terminal or human decision;
- timeout after create: search and validate before retry; never create a second PR.

`pr_recorded` commits the numeric PR ID, immutable repository ID, base, head branch, current exact work head, source create/request idempotency key, and observed state. Gates and review are forbidden before this event.

After every code-changing gate repair or review fix, `work_head_recorded` returns to `awaiting_pr`. The same PR must be reconciled and rebound to the new exact head through `pr_creation_authorized` and `pr_recorded`; creating a second PR is forbidden.

The Control App may create and update bounded PR metadata or its sticky status comment, but may not approve, merge, enable auto-merge, close the PR as a substitute for the maintainer, or alter the engineering branch.

## 12. Branch and scope contract

### 12.1 Work branch

- exactly one branch: `jarvis-work/<run_id>`;
- initially created by the Control App through section 9.2 at the exact grant base;
- subsequent engineering commits by the approved implementer only;
- no automated force-push or deletion;
- PR base exactly `master`;
- forks unsupported in v0.

### 12.2 Scope enforcement

Before every implementer request and after every resulting head:

- compute changed files against grant base;
- normalize paths;
- enforce allow and deny patterns and deny precedence;
- enforce maximum files and diff lines;
- reject submodules, unexpected Git LFS pointers, symlink escapes, binary additions, and generated secret files unless explicitly authorized;
- verify linear expected work-branch ancestry;
- bind a scope-verification digest into the event.

Denied unless named exactly and separately authorized:

- `AGENTS.md`
- `.github/workflows/**`
- `.github/CODEOWNERS`
- repository settings or ruleset exports
- secrets, credentials, `.env`, keys, certificates, or token paths
- protected conformance tests
- vendored dependencies and lockfiles
- `.jarvis/development-loop/authority.json`

A scope violation halts before review or further model calls.

## 13. Deterministic gate policy

Readiness freezes a versioned `gate_policy_id` with exact required check/workflow names and conditional path rules.

Initial required gates, where applicable:

- spec-status registry gate;
- manual-review tooling offline gate;
- BLUECAD license/import boundary gate;
- Ruff;
- full backend Pytest;
- BLUECAD geometry canary;
- frontend build when frontend paths change;
- strict real-tool proof for geometry, mesh, FEM, registry, or related adapter changes;
- development-loop unit, integration, conformance, and state-reconstruction tests for 079 paths.

A result is eligible only when conclusion is `success`, repository and exact work head match, workflow definition/action pins match policy, and the result is not skipped where required, stale, cancelled, action-required, or superseded.

One zero-model-cost infrastructure rerun is permitted per gate collection only when no assertion or source defect is indicated. A second infrastructure failure, flaky result, missing check, cancellation, timeout, or ambiguous classification halts. Tests and workflows may not be weakened to obtain green status.

## 14. Reviewer contract

The reviewer uses a credential with repository metadata, contents, commits, PRs, checks, and statuses read-only. It has no contents write, workflow dispatch, merge, settings, secret, ref-delete, or ruleset permission.

The reviewer adapter ID differs from the implementer adapter ID. Different prompts under the same effective credential do not satisfy separation.

A review request binds repository, spec, slice, scope/non-goals, exact base/head, exact diff, changed-file manifest, PR number, eligible gate evidence, round, prior findings/dispositions/fixes, content digest, provider policy, and request idempotency key.

The response is bounded JSON:

```json
{
  "schema_version": 1,
  "reviewed_head_sha": "<40 hex>",
  "verdict": "clean",
  "summary": "bounded text",
  "findings": []
}
```

Verdict is `clean`, `findings`, or `inconclusive`. Each finding binds deterministic ID, severity `P0`–`P3`, closed category, path/line, claim, reproduction, and suggested resolution. Maximum 50 findings and 2,000 characters per text field. Malformed, oversized, wrong-head, or non-JSON output is invalid. `inconclusive` requires human action.

P0/P1 are blocking until disposed. P2 is blocking only when independently reproduced as a binding violation. P3 is advisory and never triggers automatic mutation.

## 15. Finding disposition and fix loop

Closed dispositions:

- `reproduced`
- `accepted_without_reproduction`
- `false_positive`
- `superseded`
- `needs_human`

`reproduced` includes deterministic evidence or a precise current-code path. `accepted_without_reproduction` is limited to direct spec-invariant contradictions not reproducible before implementation. `false_positive` requires evidence. `superseded` points to a later head/finding. `needs_human` stops automation.

Limits:

- initial review round 0;
- maximum fix rounds 2;
- maximum review calls 3;
- maximum implementer calls 3;
- one fix attempt after each negative round;
- every code-changing fix returns through `awaiting_pr`, exact-head gates, and re-review;
- no-change false-positive disposition still requires re-review;
- negative review after round 2 enters `awaiting_maintainer`;
- scope expansion, destructive action, governance/secret change, or new dependency requires human action.

The implementer cannot resolve its own finding by assertion.

## 16. Implementer adapter contract

The immutable request binds repository/installation, work branch and exact expected head, spec/slice, normalized scope/digest, non-goals, task type (`initial_implementation`, `gate_repair`, or `review_fix`), exact defect/findings, provider/budget policy, and idempotency key.

The adapter returns provider request ID, accepted/started/completed/ambiguous status, resulting head or no-change result, bounded safe summary, response digests, usage/final cost, provider idempotency evidence, and error class.

The adapter cannot change base, branch, scope, spec, tests, provider, or budget. It may commit only to the recorded branch, and may not merge, approve, force-push, delete refs, modify settings/secrets, or write `jarvis-control`. If provider idempotency is not proven, an ambiguous post-acceptance timeout halts without retry. All output is untrusted until GitHub ancestry, scope, PR binding, and gates are revalidated.

## 17. Spend and provider authority

Runtime policy 059b does not govern repository-development agents. The loop uses a versioned repository-development budget policy approved by governance and readiness.

All money is integer micro-USD.

Absolute v1 ceilings:

- per provider request: 5,000,000;
- per run: 20,000,000;
- per UTC day: 25,000,000;
- per calendar month: 100,000,000.

Defaults are zero. Readiness may set lower non-zero caps but cannot exceed these ceilings without a spec amendment. `cost_unknown` is a hard stop.

Before every paid or quota-consuming request, canonical authority reserves projected amount and call count. Dispatch is forbidden when reservation is absent, a cap would be exceeded, price evidence is stale, role call limit is exceeded, fallback would change provider/cost, or cost/quota is unknown. Final usage finalizes or releases the reservation. No fallback provider is authorized in v1.

Subscription/quota marginal cost may be zero only with current account/plan, entitlement, remaining quota, and timestamp evidence. Hosting and Actions costs are recorded separately with monthly ceiling, notification threshold, and reconciliation cadence.

## 18. Content, secrets, and prompt-injection boundary

External model material is limited to exact spec, scope, diff, findings, PR binding, and gate evidence needed for the task. Secrets, credentials, environment values, keys, tokens, authorization headers, and unrelated project records are excluded.

Issue, PR, source, test, artifact, log, and model text is untrusted data. It cannot change policy, role, provider, budget, tests, scope, authority, or merge boundary. A deterministic layer constructs every request envelope.

No raw provider body is stored in canonical authority. Safe digests, bounded summaries, IDs, usage, and cost evidence are permitted. S4 or secret-bearing repository content remains denied absent a later explicit repository-development egress specification.

## 19. GitHub App permissions and rulesets

### 19.1 Candidate permissions

Minimum candidate installation permissions:

- metadata: read;
- contents: read/write;
- pull requests: read/write;
- checks: read;
- commit statuses: read;
- actions: read;
- issues: read/write.

Actions write is absent unless readiness proves an exact dispatch/rerun need. Administration, environments, secrets, members, deployments, packages, security-alert mutation, hook mutation, and ruleset bypass are denied.

Permissions are coarse. A capability wrapper must allow-list repository ID, endpoint, method, ref, path, transition state, and request schema. Every denied attempt is audited.

### 19.2 Identity separation

Separate effective credentials are required for Control App, implementer, reviewer, and human maintainer. The Control App credential is never provided to a model.

### 19.3 `master` ruleset

Readiness proves PR required, force-push/deletion denied, required gates enforced, no automated bypass, auto-merge unavailable to actors, and human-only merge.

### 19.4 `jarvis-control` ruleset

Only Control App and explicit human recovery identity may update; force-push/deletion denied; linear history required; non-fast-forward update rejected; model, implementer, and reviewer cannot write.

### 19.5 Work-branch rules

For `jarvis-work/*`:

- Control App has only the section 9.2 create-only operation at exact grant base;
- after creation, only approved implementer and maintainer may write;
- automated force-push and deletion denied;
- PR base restricted to `master`;
- reviewer read-only;
- Control App may read, reconcile, create the one PR, and update bounded presentation, but cannot author engineering commits.

Readiness abuse-tests merge, force-push, ref deletion, out-of-scope writes, settings/secrets mutation, unauthorized branch update after create, and PR merge/approval.

## 20. Webhook, queue, and service API

### 20.1 Events

V1 subscribes only to required events:

- `issue_comment` created;
- `push` on `master`, `jarvis-control`, and active work branch;
- `pull_request`;
- `pull_request_review`;
- `pull_request_review_comment`;
- `workflow_run`;
- installation suspension/deletion.

Edited authorization comments do not create authority.

### 20.2 Webhook handler and unauthenticated traffic

`POST /github/webhook` validates the GitHub signature over the raw body using constant-time comparison before JSON parsing or repository processing.

A missing or invalid signature is unauthenticated Internet traffic. It must:

- return an authentication failure without queueing work;
- be rate-limited at edge and application layers;
- be logged operationally with redacted bounded metadata only;
- create no database delivery record treated as GitHub evidence;
- create no canonical event, `security_signal`, or global halt merely because the request was invalid;
- never reveal whether a repository, installation, or command exists.

Repeated invalid requests may trigger infrastructure-level blocking or alerting, but cannot alter repository authority. This prevents a trivial unauthenticated denial of service.

After signature success, the handler validates installation/repository/event, computes payload digest, stores delivery ID/digest, returns within 10 seconds, performs no side effect in the request thread, and queues one reconciliation job.

Canonical `security_signal` is reserved for authenticated compromise evidence or verified anomalies, including:

- a validly signed delivery ID reused with a different payload digest;
- authenticated repository/installation identity contradiction;
- verified control-history tampering;
- verified credential misuse or unauthorized API success;
- verified scope/secret escape;
- another independently confirmed compromise indicator.

Suspicion without authenticated evidence is logged and investigated but does not grant authority or necessarily halt the canonical run.

### 20.3 Other endpoints

V1 exposes only:

- `GET /healthz` — liveness, no repository detail;
- `GET /readyz` — database/secret readiness, no values;
- `POST /github/webhook`.

There is no public admin mutation endpoint. Commands originate through validated maintainer GitHub comments and canonical events.

### 20.4 Queue behavior

PostgreSQL job claiming may use transactional `FOR UPDATE SKIP LOCKED`. Queue ownership is operational only. Duplicate jobs converge through canonical idempotency. Pure reconciliation retries at most five times with bounded backoff. Side-effecting retries require a committed authorization event and proven adapter/API idempotency. Webhook order is never trusted.

### 20.5 Retention and recovery objectives

- delivery ID/event/payload digest: 30 days;
- queue attempts/projections: 90 days;
- service logs: 30 days;
- no raw model bodies, secrets, or authorization headers in logs;
- canonical GitHub RPO: zero committed events;
- non-authoritative database RPO: 24 hours;
- service RTO target: 4 hours;
- GitHub uncertainty: stop indefinitely rather than act from cache.

## 21. Presentation and notifications

The service may maintain one non-authoritative check run, one sticky PR status comment, one control-issue status comment, and one weekly digest. Updates occur only after canonical state changes and are idempotent.

Between weekly reviews, direct maintainer notification is limited to a human decision, authenticated security signal, or budget overrun/disabled cost authority. Routine progress and inactivity do not create repeated notifications.

Weekly digest:

- timezone `Europe/Rome`;
- Monday 08:00 local;
- at most one per seven-day window;
- omitted when no canonical state changed;
- never authorizes, releases, selects a provider, or implies merge consent.

## 22. Security and supply-chain contract

The implementation must use short-lived installation tokens, hosting secret storage, credential rotation, immutable dependency/action pins, SBOM generation, dependency/container scanning, outbound allow-lists, repository/SHA validation, and denial of untrusted-fork execution with write-capable or secret-bearing credentials.

The webhook process never executes PR code. Invalid unauthenticated signatures follow section 20.2 and do not canonically halt. Authenticated compromise evidence, verified control-history anomaly, signed delivery mismatch, verified scope escape, or verified secret exposure records `security_signal` and halts new side effects.

## 23. Verification and acceptance

### 23.1 Offline unit tests

Prove:

1. deterministic JSON and digest vectors;
2. event-chain and snapshot reconstruction;
3. duplicate idempotency convergence;
4. invalid schema/field/float/timestamp/digest rejection;
5. complete transition allow/deny matrix including `awaiting_pr` and `front_released`;
6. authorization, revocation, recovery, and release parsing;
7. maintainer identity and edited-comment rejection;
8. scope normalization, deny precedence, limits, and escapes;
9. budget reservations/finalization and caps;
10. finding normalization and blocking policy;
11. lease creation, renewal, expiry, and non-release;
12. PR operation idempotency and mismatch classification;
13. provider ambiguous-timeout halt;
14. notification deduplication;
15. invalid-signature rejection with no canonical state change.

### 23.2 Offline integration tests

With fake GitHub, PostgreSQL, implementer, and reviewer actors, prove:

1. process/database restart reconstructs identical state;
2. duplicate webhooks/jobs create one canonical effect;
3. claim creates one work ref through create-only Control App capability;
4. Control App cannot update/delete the work ref after creation;
5. initial implementation creates or reconciles exactly one PR before gates;
6. ambiguous PR creation reconciles without a duplicate;
7. every code-changing fix rebinds the same PR to the new exact head before gates;
8. changed work head invalidates gates and review;
9. reproducible gate defect returns to implementation;
10. infrastructure ambiguity does not mutate code;
11. clean review stops at maintainer boundary;
12. genuine finding creates one bounded fix;
13. false-positive no-change path re-reviews;
14. maximum rounds stop provider calls;
15. revoke and kill switches prevent actions;
16. terminal release returns to idle while preserving complete event history;
17. a second sequential run can be authorized only after release;
18. no actor can merge or self-approve;
19. invalid signatures cannot cause canonical denial of service;
20. inactivity creates no calls or repeated comments.

### 23.3 Disposable-repository real-tool proofs

Before readiness, in a disposable repository or isolated organization fixture, prove:

1. two or more dispatchers race from vacancy; exactly one claim wins and losers have zero side effects;
2. ref advance with unchanged authority blob rejects stale candidate;
3. stale blob/tree/parent/ref identities fail closed;
4. timeout after successful control-ref update reconciles once;
5. duplicate/replayed signed webhook converges after database loss;
6. authority reconstructs after all external state is deleted;
7. altered/removed/reordered/forked history halts;
8. lease expiry while worker remains active starts no claimant;
9. Control App creates only the exact derived work ref at exact base and cannot later update/delete it;
10. one exact-head PR is created before gates; create timeout/replay makes no duplicate;
11. wrong-base, forked, closed, duplicate, or mismatched PR fails closed;
12. sequential terminal release preserves history and permits a later new authorization;
13. changed work head invalidates prior CI/review and rebinds the same PR;
14. Control App, implementer, and reviewer credentials are denied merge;
15. automated credentials are denied force-push, ref deletion, settings/secrets mutation, and out-of-scope writes;
16. reviewer cannot write and implementer cannot provide authoritative review;
17. untrusted fork code cannot access secrets or write;
18. prompt-injection fixtures cannot change scope, role, provider, budget, tests, or merge authority;
19. exceeded or unknown cost makes zero provider calls;
20. provider timeout cannot create untracked duplicate request/charge;
21. GitHub outage pauses and reconciles without duplicate action;
22. every kill switch stops new effects;
23. Actions concurrency/cancellation cannot release authority;
24. invalid/unsigned webhook traffic is rejected and rate-limited but cannot create canonical halt;
25. authenticated delivery mismatch or verified compromise does create canonical security halt;
26. inactivity and duplicate events create no repeated calls/notifications.

### 23.4 Repository gates

The implementation must pass:

```bash
cd backend
python -m pytest -q
python -m ruff check app tests
python ../scripts/check_spec_status.py --self-test
```

plus existing CI/canary gates and deterministic service tests, expected initially as:

```bash
python -m pytest -q services/devloop/tests
python -m ruff check services/devloop
```

Exact commands and dependency pins are frozen at readiness. No CI test may call a live model, require paid service, or mutate production.

### 23.5 Maintainer-owned conformance evidence

Before implementation, readiness freezes canonical vectors for state transitions, two-writer race, work-ref create-only permissions, PR idempotency, exact-head invalidation, merge denial, terminal release/sequential run, maximum rounds, cost stops, webhook authentication behavior, and kill switches.

Protected conformance fixtures are maintainer-owned. The implementation agent may not weaken them.

## 24. Rollout, governance, readiness, and kill switches

### 24.1 Required governance amendment

A separate PR must amend `AGENTS.md` narrowly to permit automatic implementer/reviewer dispatch only for one current canonical 079 run with maintainer grant, global claim, exact branch/head/PR, scope, identities, gates, round limits, and budget. The exception must continue to forbid automatic spec selection, merge, auto-merge, priority change, workflow/ruleset bypass, force-push, branch deletion, secret/settings change, destructive action, scope expansion, provider fallback, or work after a security/cost/integrity/human-decision stop.

This full-spec PR does not apply that amendment.

### 24.2 Rollout phases

1. Merge this full specification with 079 still `planned`.
2. Merge the narrow governance amendment; dormant until readiness.
3. Build the proof prototype only in a disposable repository or separate fixture, using fake actors and zero paid-provider calls.
4. After explicit maintainer approval, run read-only shadow reconciliation against JarvisOS; no claims, branch/PR writes, workflows, or providers.
5. Dated readiness records exact host, App/actor identities, rulesets, adapters, prices/caps, proof outputs, conformance vectors, owners, and rollback; only then set 079 `ready`.
6. After readiness merge, set `in_progress` and implement service/offline tests in one bounded PR.
7. After implementation merge and separate operational authorization, run one low-risk documentation-only activation with human-only merge.
8. Broader use requires separate approval after first-run cost/security evidence.

No implementation skeleton may enter JarvisOS while 079 remains `planned`.

### 24.3 Independent kill switches

V1 requires:

1. canonical security/maintainer halt event;
2. suspend App installation;
3. revoke/rotate App key and webhook secret;
4. revoke provider credentials;
5. stop service replicas and queue consumers;
6. set provider caps to zero;
7. disable any selected dispatch workflow;
8. protected human-only recovery from last verified control commit.

Rollback means halt, reconstruct, and record. It never means force-push, event deletion, finding erasure, or spend-evidence removal.

### 24.4 Readiness evidence required

079 remains `planned` until a dated readiness PR proves:

- dependencies remain merged and no competing active front exists;
- architecture and full spec are merged;
- governance amendment is merged;
- every disposable-repository proof passes;
- exact App permissions, rulesets, capability wrapper, and actor IDs are captured;
- automated credentials fail merge and abuse tests;
- Control App create-only work-ref and idempotent PR lifecycle are proven;
- terminal release and sequential-run behavior are proven;
- host, PostgreSQL, retention, RTO/RPO, and secret custody are selected;
- implementer/reviewer adapters and effective identities are selected;
- current provider price/quota evidence exists;
- non-zero caps are explicitly approved within section 17;
- gate policy and conformance vectors are frozen;
- implementation and rollback owners are named;
- first activation slice is bounded;
- no unresolved P0/P1 or authority/security blocker remains.

Only that PR may move 079 to `ready`.

## 25. Compatibility and migration

- No JarvisOS runtime SQLite migration is authorized.
- Existing execution spine, runtime budget, Hermes, MemoryStore, BLUECAD, and product event tables do not become control-plane authority.
- Hosted PostgreSQL starts at schema v1 and remains rebuildable.
- Bootstrap creates protected control branch through explicit maintainer action; no chat/comment/old branch/old PR is imported as authority.
- Existing work is not adopted unless an explicit grant names exact base, branch, scope, and reconciliation; v0 normally creates a fresh derived branch.
- Existing review workflows remain manual until governance and readiness authorize 079.
- Authority schema changes require additive versioning and migration proof; unknown version halts.
- Force-push/history rewrite is never migration.

## 26. Likely implementation scope

Verify against then-current `master`. Expected bounded paths:

- `services/devloop/` — service, schemas, policy, GitHub client, queue, adapters, tests;
- minimal pinned service dependency/lock manifest and OCI definition;
- deterministic fake GitHub/implementer/reviewer fixtures;
- deployment documentation with no secrets;
- `docs/specs/STATUS.md` only for normal implementation state;
- existing CI only where required for offline service tests.

Not part of implementation PR:

- `AGENTS.md` amendment, which merges first separately;
- live settings, App installation, rulesets, or secrets, which are human readiness actions;
- provider credentials or raw account data;
- product backend/frontend/runtime modules;
- Hermes, MCP, MemoryStore, BLUECAD modeling, process-kernel, or spec 078 work.

New dependencies must be pinned, justified, scanned, and service-limited. No agent framework.

## 27. Binding non-goals

079 v0 does not provide:

- automatic next-spec selection;
- multiple simultaneous fronts, branches, implementers, reviewers, or PRs;
- autonomous merge, approval, auto-merge, release, deployment, priority, roadmap, governance, ruleset, or secret changes;
- force-push, branch deletion, history rewrite, or protected-test mutation;
- arbitrary shell access outside adapter/scope contract;
- provider fallback, bidding, routing, or AI swarm;
- unbounded review/fix loops;
- execution from untrusted forks;
- replacement of runtime 059b, Hermes, or GitHub Actions;
- storage of model bodies or secrets in canonical state;
- guaranteed availability during outages;
- implementation of 078 or another frozen front.

## 28. Definition result

The full-spec step is complete when:

- this document replaces the planning kernel on a PR based on current `master`;
- 079 remains `planned` with no Implementation PR;
- architecture, schemas, state machine, authorization, exact branch/PR lifecycle, permissions, cost ceilings, tests, rollout, compatibility, and kill switches are explicit;
- PR creation/reconciliation occurs before gates and remains idempotent across fixes;
- terminal release returns to idle without erasing history;
- the Control App create-only work-ref capability is explicit and abuse-tested;
- unauthenticated signature failures cannot canonically halt the repository;
- ref-level CAS remains proof-gated rather than asserted as proven;
- no runtime, workflow, App, provider, secret, ruleset, dependency, or repository setting is created or changed;
- deterministic repository gates pass on the exact PR head;
- review findings are resolved;
- the PR stops for the maintainer’s merge decision.

Merging this full specification does not authorize the governance amendment, readiness promotion, implementation, external provider calls, or automated merge.
