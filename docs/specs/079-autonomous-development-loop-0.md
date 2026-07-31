# 079 — AUTONOMOUS-DEVELOPMENT-LOOP-0: durable bounded development continuation

Status: full specification complete under the explicit documentary sequencing decision in section 2.1; `docs/specs/STATUS.md` remains authoritative and keeps 079 `planned`.

Depends on: 004, 017, 019, 022

Full-spec baseline: `9c3c8ce90a9048c1797f2560025790162012d423`

Authority and evidence:

- `079-autonomous-development-loop-source-evidence.md`
- `079-architecture-evidence-closure-2026-07-31.md`
- `079-architecture-source-evidence-2026-07-31.md`

## 1. Goal

Allow one already and explicitly authorized JarvisOS repository-development slice to continue safely across agent-session termination without repeated conversational `continue` prompts.

The v0 control plane may reconstruct GitHub-owned authority, claim one repository-wide front, create one exact-base work branch, invoke one bounded implementer, create or reconcile one exact-head PR, collect exact-head gates, invoke one independent reviewer, run at most two fix/re-review rounds, recover from replay/restart/ambiguity, present evidence to the maintainer, truthfully record any human PR outcome, and release a reconciled terminal front to `idle` without erasing history.

It may never merge, auto-merge, approve authoritatively, change priority, create a second front, infer authorization from activity, or turn model output into authority.

## 2. Full-spec boundary

This document freezes the v0 contract for canonical state/events; authorization/expiry/revocation/recovery/release; claim/lease; exact branch/PR lifecycle; state machine; Git ref CAS; webhook/queue; implementer/reviewer adapters; gates; findings/fixes; dispatch/spend/content/permissions; deployment/retention/notifications; proofs/rollout/kill switches/compatibility.

It does not install/configure an App, service, database, secret, ruleset, branch, workflow, provider, or dependency; modify `AGENTS.md` or `STATUS.md`; invoke a model or paid service; authorize governance, readiness, implementation, repository settings, merge, or auto-merge.

Current `AGENTS.md` remains binding. Live development-agent dispatch is impossible until section 24’s separate governance amendment reconciles both the execution-spine invariant and manual/explicit-only review rules.

### 2.1 Explicit documentary sequencing decision

The merged architecture/evidence closure originally labelled the disposable-repository concurrency, CAS, credential, cost, PR, and recovery proofs mandatory before full-spec promotion.

After PR #205 merged, the maintainer explicitly instructed this full-spec step to proceed. This is recorded as a narrow sequencing decision:

- the complete documentary contract may merge while 079 remains `planned`;
- every unproven mechanism remains marked proof-gated and unavailable;
- the decision does not assert that CAS, permissions, cost controls, adapters, or recovery work;
- no governance exception, live App, proof prototype in JarvisOS, readiness promotion, implementation, or provider call is authorized;
- every mandatory proof from the architecture closure remains a hard blocker before the dated readiness decision and implementation.

This section supersedes the earlier phrase “before full-spec promotion” only for the order of the documentation PR. It does not waive, weaken, or silently reclassify any proof.

## 3. Binding invariants

1. `STATUS.md` is the only live roadmap/status authority.
2. One product/implementation front repository-wide.
3. Branches, PRs, labels, reviews, checks, workflows, timers, and model text are not authorization.
4. V0 begins only from a maintainer command naming exact spec/slice/base/scope/adapters/budget.
5. Every side-effect transition rechecks grant currency, claim, GitHub facts, stop state, role capacity, provider policy, and budget; mutations also require a valid reconciled lease.
6. Deterministic gates and advisory review inform readiness; maintainer alone merges.
7. Reviewer cannot mutate; implementer cannot author authoritative review.
8. Automated actors cannot merge, auto-merge, force-push, delete protected refs, change settings/secrets, or bypass rulesets.
9. Repository-development provider authority is separate from runtime 059b.
10. Planned/blocked/cancelled/dependency-incomplete/expired/revoked work never starts or continues automatically.
11. Lease/grant expiry, inactivity, process death, or timers never release ownership.
12. Any head change invalidates head-bound gates/review.
13. Human PR actions are observed and recorded truthfully even when they occur before system-prepared readiness.
14. Safety dominates liveness.

## 4. Selected architecture

### 4.1 Service

Installed GitHub App plus stateless Python 3.11 FastAPI/ASGI service, GitHub REST/Git Data client, and PostgreSQL 16 for non-authoritative queue/dedupe/projections. One OCI image; replicas allowed. No Redis, agent framework, vector database, browser automation, or second orchestrator.

The service is outside product runtime and does not share JarvisOS SQLite, runtime egress state, runtime provider secrets, or `C:\JarvisOS` data.

### 4.2 Canonical state

Protected branch `jarvis-control`, one file `.jarvis/development-loop/authority.json`. Comments/checks/workflows/DB/dashboard are rebuildable projections only.

### 4.3 PostgreSQL

May store delivery IDs/digests, queue attempts, cached projections, provider correlation, notification dedupe, and health summaries. It never owns the only grant, claim, lease, PR binding, gate/review, finding disposition, reservation, terminal outcome, or release. DB loss delays but cannot change authority.

## 5. Canonical encoding and integrity

Deterministic UTF-8 JSON: sorted keys, compact separators, UTC `Z` timestamps, integers for money/counters/durations/sizes, no float/NaN/inf, lowercase SHA-256 identifiers.

Top level:

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

Every event binds sequence, deterministic event ID, type, timestamp, effective actor/role, idempotency key, previous digest, payload/digest, and event digest. Identical duplicate is no-op; same key with different bytes is integrity failure. Sequence and Git ancestry own ordering.

Both event hash chain and linear `jarvis-control` ancestry must validate. Missing/reordered/altered/forked/force-pushed/non-linear history causes `control_integrity_failure` and zero external side effects. V1 has no compaction; halt before event 4097 or 2,000,000 canonical bytes.

## 6. Closed identifiers, roles, states, outcomes

IDs: `run_`, `grant_`, `claim_`, `lease_`, `pr_`, `gates_`, `review_`, `finding_`, `fix_`, `provider_`, `human_` plus deterministic hex. Control App derives IDs; models never choose them.

Roles: `maintainer`, `control`, `implementer`, `reviewer`, `gate_collector`, `system_reconciler`; effective credentials decide role.

States:

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

Terminal outcomes:

- `merged_by_maintainer`
- `closed_without_merge`
- `superseded_by_maintainer`
- `completed_without_pr`
- `authorization_revoked`
- `authorization_expired`
- `abandoned_after_human_decision`

A terminal event also records `prepared_state_at_human_action`, `human_action_head`, and `evidence_status` (`current_clean`, `stale_or_incomplete`, or `not_applicable`). Thus a human merge is recorded honestly without pretending the system had current clean evidence.

Closed stop reasons include authorization missing/invalid/expired/revoked; registry/dependency/front conflict; claim race; integrity/capacity; scope/base/head/PR mismatch or ambiguity; head changed after review; lease expiry; gate missing/stale/cancelled/action-required/infra/flaky; review invalid/inconclusive; finding/round boundary; provider disabled/ambiguous; cost unknown/cap; secret/security/destructive/governance/merge/human decision.

## 7. Authorization lifecycle

### 7.1 Maintainer commands

Readiness bootstraps one control issue and allow-listed maintainer numeric IDs. Eligible commands are newly created, exactly formatted, repository/issue/author validated, and rechecked against current SHAs/facts. Comments are inputs, not authority.

Authorization command binds repository, three-digit spec, bounded slice, `master` and exact SHA, normalized allow/deny globs and file/line caps, distinct approved adapter IDs, budget policy, max fix rounds 0–2, optional future expiry no more than 30 days, and bounded reason. Scope produces `scope_digest`; work branch derives as `jarvis-work/<run_id>`.

V0 never infers grants from rows, branches, PRs, labels, schedules, chat, previous runs, or models.

### 7.2 Currency and expiry

Every branch/PR/workflow/provider/reservation side-effect event proves grant present, unrevoked, and unexpired at commit time.

At expiry: no new side-effect event; record `authorization_expired`; enter `awaiting_maintainer`; reconcile already accepted work without follow-on action; never release claim/lease/history automatically. Maintainer may terminalize and later release.

### 7.3 Revocation and recovery

Revocation blocks new work, permits only proven-safe cancellation, and enters `awaiting_maintainer` or terminal. Recovery binds exact control head, action `resume` or `terminalize`, target/outcome, and independently reconciles repository, work ref, PR, workflows, providers, reservations, lease, budget, and security. Security recovery references remediation evidence.

### 7.4 Release

Only from `terminal`, after proving no external action/reservation/cancellation/integrity/security ambiguity and PR/ref facts match outcome. `front_released` clears active snapshot fields but preserves complete completed-run, PR/ref, findings, usage/cost, events, and Git history. Duplicate release is no-op; later run needs new grant from `idle`.

## 8. Snapshot

Snapshot binds state, active run/grant/claim/lease, work branch/head/PR/base/PR state/ancestry/diff/scope digest, gates, review round/exact head/effective reviewer/request/findings/dispositions/verdict, integer-micro-USD budget/reservations/call counts, next action, stop, active outcome, and last completed run.

## 9. Claim, work ref, and lease

`claim_acquired` requires current grant, eligible registry/dependencies, repository-wide vacancy, no competing owner/PR/run, exact base, current policies, and no stop. One CAS atomically records global claim and initial 60-minute lease. Losers/ambiguity produce zero side effects.

After claim, Control App may create only `refs/heads/jarvis-work/<run_id>` at exact grant base when absent and state/claim/lease match. Existing exact ref is idempotent. App cannot later update/force/delete/commit on it. `work_branch_recorded` follows exact reconciliation. Later commits are implementer-only under lease; maintainer retains emergency authority.

Lease duration 60 minutes; renewal window last 20 minutes; one active mutation request; renewal cannot alter grant/scope/round/adapter/budget. Expiry never releases; it records pending reconciliation and blocks mutation until branch/PR/workflow/provider/reservation/security facts reconcile and lease renews canonically.

## 10. Exact-head Git CAS

Read exact control ref/commit/tree/blob; validate schema/chains/snapshot; reread preconditions; compute one event; create blob/tree/commit with sole parent exact expected head; update ref `force=false`; accept only unambiguous candidate success. Contents API blob update is forbidden as CAS.

On timeout/rejection/disconnect, perform no external side effect and reread ref/ancestry/event ID. Candidate present exactly once means committed; absent means lost; unresolved ambiguity halts. Same idempotency key never creates a different event.

## 11. Closed state machine

### 11.1 Dispatch authority

Only `implementation_requested`, `gate_repair_authorized`, `review_fix_authorized`, and `review_dispatch_authorized` can authorize model calls. Before call, the event atomically binds current grant/claim/no-stop, exact repo/ref/PR/head, role/call capacity, current adapter/provider policy, canonical cost/quota reservation even at marginal zero, idempotency key, and—when mutating—valid lease/scope. Review dispatch additionally binds exact eligible gates and PR/head.

No other event or prose authorizes a model call.

### 11.2 Transition table

| State | Event | Preconditions | Next | Side effect after commit |
| --- | --- | --- | --- | --- |
| `idle` | `authorization_recorded` | valid command | `authorized` | none |
| `authorized` | `claim_acquired` | section 9 and CAS | `claimed` | create/reconcile work ref |
| `claimed` | `work_branch_recorded` | exact ref at base | `claimed` | none |
| active | `lease_renewed` | current grant/lease/reconciliation/window | same | none |
| `claimed` | `implementation_requested` | section 11.1 | `implementing` | one implementer request |
| `implementing` | `work_head_recorded` | descendant/no-change, scope valid | `awaiting_pr` | none |
| `implementing` | `provider_ambiguous` | accepted unresolved request/charge | `halted` | none |
| `awaiting_pr` | `pr_creation_authorized` | exact branch/head/base, no conflict, grant current | `awaiting_pr` | create/reconcile one PR |
| `awaiting_pr` | `pr_recorded` | exactly one matching open PR/head | `awaiting_gates` | observe/request deterministic gates only |
| `awaiting_gates` | `gates_passed` | all required exact-head gates green | `awaiting_review` or `awaiting_re_review` | none |
| `awaiting_gates` | `gate_defect_reproduced` | deterministic in-scope defect | `fix_required` | none |
| `fix_required` | `gate_repair_authorized` | section 11.1 including valid lease/capacity | `implementing` | one repair |
| `awaiting_gates` | `gate_ambiguous_or_infra` | stale/flaky/cancelled/missing/action-required/infra | `halted` or `awaiting_maintainer` | none |
| `awaiting_review` or `awaiting_re_review` | `review_dispatch_authorized` | section 11.1 review authority | same | one reviewer request |
| `awaiting_review` or `awaiting_re_review` | `provider_ambiguous` | accepted unresolved review/charge | `halted` | none |
| `awaiting_review` | `review_clean` | valid exact-head response | `awaiting_maintainer` | presentation only |
| `awaiting_review` | `review_findings_recorded` | valid normalized findings | `fix_required` | triage only |
| `awaiting_review` or `awaiting_re_review` | `review_inconclusive` | valid inconclusive response | `awaiting_maintainer` | none |
| `fix_required` | `findings_disposed_no_change` | evidence-backed false/superseded | `awaiting_re_review` | none |
| `fix_required` | `review_fix_authorized` | genuine blocker, section 11.1, round remains | `implementing` | one fix |
| `fix_required` | `finding_requires_human` | scope/security/ambiguity/dependency/round | `awaiting_maintainer` | none |
| `awaiting_re_review` | `review_clean` | valid exact-head response | `awaiting_maintainer` | presentation only |
| `awaiting_re_review` | `review_findings_recorded` | valid findings, rounds remain | `fix_required` | triage only |
| `awaiting_re_review` | `maximum_rounds_reached` | negative after round 2 | `awaiting_maintainer` | none |
| `awaiting_maintainer` | `work_head_changed` | valid scoped descendant differs from reviewed head | `awaiting_pr` | none |
| any active state with recorded PR | `human_merge_observed` | human action reconciled; no active/ambiguous request remains | `terminal` | none |
| any active state with recorded PR | `human_close_observed` | human action reconciled; no active/ambiguous request remains | `terminal` | none |
| active non-terminal | `authorization_expired` | expiry reached | `awaiting_maintainer` | reconcile accepted work only |
| non-terminal | `authorization_revoked` | valid revoke | `awaiting_maintainer` or `terminal` | safe cancellation only |
| non-terminal | `security_halt` | authenticated verified anomaly | `halted` | none |
| `halted` | `human_recovery_recorded` | valid command/reconciliation | reachable safe state or `terminal` | recorded recovery only |
| `terminal` | `front_released` | section 7.4 | `idle` | none |

### 11.3 Human PR outcomes from any active PR state

The maintainer may merge or close a recorded PR at any time. The control plane must never strand the claim merely because the human acted before `awaiting_maintainer`.

Before terminalization it reconciles all accepted implementer/reviewer/workflow/provider requests and reservations. If any outcome is ambiguous, record/honor the halt first; recovery then records the actual human PR outcome.

For merge:

- actual merged SHA, actor, timestamp, and prior canonical state are recorded;
- if merged SHA equals the current exact gated and clean-reviewed head, `evidence_status=current_clean`;
- otherwise `evidence_status=stale_or_incomplete`; prior gates/review are invalidated for presentation and the terminal record must not claim system-prepared readiness;
- terminal outcome is still `merged_by_maintainer`, because merge authority is human and the ledger’s duty is factual observation, not retroactive approval.

For close/supersede, record actual PR state and corresponding terminal outcome. No replacement PR is created automatically.

### 11.4 Head invalidation and merge equality

Any work-head change invalidates gates/review/presentation. Before clean review return via `awaiting_pr`; from `awaiting_maintainer`, `work_head_changed` returns via PR/gates/review. Non-descendant/force/scope ambiguity halts.

A system claim of `current_clean` requires actual merged SHA equal the exact current gated/reviewed head. A different human-merged head is recorded only as a human override with stale/incomplete evidence, never as a clean system verdict.

### 11.5 Idempotent PR lifecycle

`pr_creation_authorized` binds repository/run/branch/head/base/scope/version. Zero matching PR creates one non-draft PR with run/scope marker; exactly one correct open PR is reused; duplicates/wrong base/head/marker/fork/unknown fail closed; closed recorded PR is never replaced; create timeout searches/reconciles before retry.

`pr_recorded` binds PR ID/repository/base/head branch/exact work head/operation/state. No gates/review before it. Every code-changing repair rebinds the same PR through `awaiting_pr`; second PR forbidden.

## 12. Scope

One work branch; App creates once; implementer commits later; no automated force/delete; base master; forks unsupported.

Before/after mutation verify normalized paths, allow/deny precedence, file/line caps, linear ancestry, submodules/LFS/symlink/binary/secret risk and bind digest. Denied absent exact separate authority: `AGENTS.md`, workflows/CODEOWNERS, settings/rulesets, secrets/keys/tokens, protected conformance tests, vendored dependencies/lockfiles, canonical authority file.

## 13. Deterministic gates

Readiness freezes exact checks/workflow/action pins/path conditions: registry, manual-review offline boundary, BLUECAD license boundary, Ruff, full Pytest, canary, frontend build if needed, strict tool proof where relevant, and 079 service unit/integration/conformance/reconstruction tests.

Eligible means success, correct repo/head/policy, not stale/skipped-required/cancelled/action-required/superseded. One zero-model-cost infra rerun per collection absent assertion/source defect; further ambiguity halts. Never weaken tests/workflows.

## 14. Reviewer and finding IDs

Reviewer is read-only; no write/dispatch/merge/settings/secrets/ref/ruleset authority; effective identity differs from implementer.

Request binds repo/spec/slice/scope/non-goals/base/head/diff/PR/gates/round/prior findings/fixes/content/provider/reservation/idempotency.

Response JSON includes exact head, verdict `clean|findings|inconclusive`, bounded summary, and findings with severity/category/path/line/claim/reproduction/resolution—but no authoritative finding ID. Control App validates/normalizes and derives `finding_<32 hex>` from review round, head, normalized finding digest, and occurrence index. Model-supplied `finding_id` is rejected as unknown field.

Max 50 findings, 2,000 chars per field. Malformed/oversized/wrong-head/unknown-field/non-JSON is invalid. Inconclusive records canonical human stop. P0/P1 block; P2 only if independently reproduced as binding violation; P3 advisory.

## 15. Disposition and rounds

Dispositions: `reproduced`, `accepted_without_reproduction`, `false_positive`, `superseded`, `needs_human`, each evidence-bound. Initial round 0; max two fix rounds, three reviewer calls, three implementer calls; one fix per negative round; every code change rebinds PR/gates/review; no-change rebuttal re-reviews; negative round 2 stops; scope/destructive/governance/secret/dependency expansion stops.

## 16. Adapters and execution-spine governance block

Adapter requests bind repo/install, branch/head, spec/slice, scope/non-goals, task/defect/findings, provider/budget/reservation/idempotency. Responses bind provider request/status, resulting head/no-change, safe digests/summary, usage/cost/idempotency/error.

Adapters cannot alter authority; implementer writes only work branch; neither merges/approves/force-deletes/settings/secrets/control. Accepted ambiguous outcome halts without retry absent proven idempotency/reconciliation.

Current `AGENTS.md` requires all AI calls through `run_ai_task` and `ai_jobs`; selected hosted service does not share product SQLite/egress. Therefore live 079 calls are blocked now.

The selected v0 governance route is a narrow repository-development exception: approved 079 adapter calls may occur outside product `run_ai_task` only with committed grant/claim/exact branch/head/PR/scope/identity/provider/reservation/idempotency and durable 079 usage/cost evidence. The amendment must merge before readiness; otherwise full spec must be amended to route through an authenticated product execution-spine boundary. Until then, no live dispatch.

## 17. Cost

Separate development budget, integer micro-USD, defaults zero. Hard maxima: request 5,000,000; run 20,000,000; UTC day 25,000,000; month 100,000,000. `cost_unknown` stops.

Every implementer/reviewer call reserves amount/quota/call count canonically before dispatch. No reservation, stale price, exceeded cap/calls, unknown cost/quota, or fallback change means zero call. Final usage finalizes/releases. No fallback provider. Marginal zero requires current plan/entitlement/quota/timestamp evidence. Hosting/Actions tracked separately.

## 18. Content and secrets

Only exact spec/scope/diff/findings/PR/gates required for task. Exclude secrets/credentials/env/keys/tokens/headers/unrelated records. All repo/model text is untrusted and cannot change authority. Deterministic policy constructs request. No raw provider body in authority; safe digests/summaries/IDs/usage/cost only. S4/secret-bearing content denied absent later egress spec.

## 19. Permissions and rulesets

Candidate App: metadata read; contents read/write; PR read/write; checks/status/actions read; issues read/write. Actions write only if readiness proves need. No admin/environments/secrets/members/deployments/packages/security-alert/hook/ruleset bypass.

Capability wrapper allow-lists repository/endpoint/method/ref/path/state/schema and audits denials. Separate Control/implementer/reviewer/maintainer credentials.

Rulesets: master PR/checks/no force-delete/no automated bypass/human merge; control App/human recovery only/linear/no force-delete; work App create-only then implementer/maintainer write/reviewer read-only/base master. Abuse tests cover merge/approval/force-delete/out-of-scope/settings/secrets/post-create ref update/PR mutation.

## 20. Webhook and service

Events: new issue comments, pushes on master/control/work, PR/review/review-comment/workflow-run, installation suspension/deletion. Edited authorization comments ignored.

Webhook verifies raw-body signature constant-time before JSON. Missing/invalid: auth failure, edge/app rate-limit, redacted log, no trusted delivery/queue/canonical event/security halt, no information disclosure. Authenticated processing validates install/repo/event, stores digest, acknowledges under 10 seconds, queues reconciliation, no request-thread side effect.

Canonical security halt only for authenticated/verified anomaly: signed delivery-ID digest mismatch, identity contradiction, history tamper, credential misuse/unauthorized API success, scope/secret escape, independently confirmed compromise.

Endpoints only health, readiness, webhook. Queue is operational; duplicate converges; pure reads retry bounded; side-effect retry requires committed event/proven idempotency; webhook order untrusted.

Retention: delivery 30d, queue/projection 90d, logs 30d; no raw model/secrets/headers. Canonical RPO zero, DB RPO 24h, RTO target 4h; GitHub uncertainty stops.

## 21. Presentation

One non-authoritative check, sticky PR comment, control-issue status, weekly digest. Idempotent after canonical change. Between weekly reviews notify only human decision, authenticated security signal, or budget overrun/disabled authority. Digest Europe/Rome Monday 08:00, max weekly, omitted without change, never grants authority.

## 22. Security/supply chain

Short-lived tokens, secret store, rotation, immutable pins/digests, SBOM, dependency/container scanning, outbound allow-list, repo/SHA validation, no untrusted fork with write/secrets, webhook process never executes PR code. Invalid unsigned traffic does not halt; verified authenticated compromise does.

## 23. Verification

### 23.1 Offline

Unit/integration with fake GitHub/DB/actors proves canonical encoding/chains/reconstruction/idempotency/schema rejection; transition matrix; grant/expiry/revoke/recover/release; identity/scope; reservation/caps/calls; finding ID derivation; lease; PR idempotency; head invalidation; human PR outcome from every active PR state; current-clean versus human-override merge evidence; provider ambiguity; notifications; invalid-signature no-state-change; restart/replay; one create-only ref; no later App ref mutation; one PR before gates; same PR after fixes; grant expiry blocks dispatch; expired lease blocks repair; inconclusive stops; ambiguous calls halt; release enables later grant; no merge/self-approval; inactivity silent.

### 23.2 Disposable real-tool proofs before readiness

All architecture-closure proofs remain mandatory, including multi-writer CAS race; stale parent/ref; timeout reconciliation; replay after DB loss; reconstruction; history tamper; lease expiry; create-only ref; PR create/replay/mismatch; grant expiry at each dispatch; budget/call/lease gates; exact-head invalidation; human merge/close from each active PR state; clean-evidence equality versus override; inconclusive/provider ambiguity; deterministic finding IDs; release/sequential run; credential abuse denials; reviewer/implementer separation; fork/prompt injection; cost stops; provider duplicate-charge prevention; outage; kill switches; Actions non-authority; invalid unsigned traffic no halt; verified authenticated anomaly halt; inactivity/noise.

### 23.3 Repository/conformance

Implementation must pass repository Pytest/Ruff/status/canaries and deterministic service tests; no live/paid/production CI. Readiness freezes maintainer-owned vectors for every authority property. Implementation agents cannot weaken them.

## 24. Governance, rollout, readiness

### 24.1 Required `AGENTS.md` amendment

Separate PR explicitly amends manual/explicit-only dispatch rules and hard `run_ai_task`/`ai_jobs` invariant with the narrow 079 repository-development exception described in section 16. It continues to forbid auto selection/merge/priority/bypass/force-delete/settings/secrets/destructive/scope expansion/fallback/work after expiry/revocation/security/cost/integrity/human stop. Until merged, no live calls.

### 24.2 Rollout and proof order

1. Merge this documentary full spec under section 2.1; 079 stays `planned` and mechanisms remain unproven/unavailable.
2. Merge narrow governance amendment, dormant until readiness.
3. Build disposable/separate proof prototype with fake actors and zero paid calls; execute every architecture-closure proof before readiness.
4. Optional explicitly approved read-only JarvisOS shadow: no claim/ref/PR/workflow/provider writes.
5. Dated readiness records host/App/actors/rulesets/adapters/prices/caps/proofs/vectors/owners/rollback and only then sets `ready`.
6. One bounded implementation PR after readiness.
7. Separate operational grant for one low-risk docs-only activation with human merge.
8. Broader use separately approved after first-run evidence.

The sequencing exception affects only steps 1 and 3 ordering. No implementation skeleton enters JarvisOS while `planned`.

### 24.3 Kill switches and readiness evidence

Canonical halt, App suspension, key/secret/provider revocation, service/queue stop, caps zero, dispatch workflow disable, human recovery. Rollback never force-pushes or erases.

Readiness proves merged dependencies/architecture/full spec/governance; all mandatory proofs; exact permissions/rulesets/wrapper/IDs; execution exception; abuse denials; ref/PR lifecycle; grant/lease/budget; head drift and human-outcome reconciliation; provider ambiguity/finding IDs/release; host/DB/secrets/adapters/pricing/caps/gates/vectors/owners/first slice; no unresolved P0/P1. Only readiness PR sets `ready`.

## 25. Compatibility

No product SQLite migration. Product execution/budget/Hermes/MemoryStore/BLUECAD/events do not become authority. Hosted DB rebuildable. Bootstrap new protected control branch explicitly; no chat/old PR/ref imported. Existing work needs exact grant/reconciliation and normally fresh branch. Review remains manual until governance/readiness. Authority versions require additive migration proof. No force-push migration.

## 26. Likely implementation scope

After readiness: `services/devloop/`, pinned service manifest/container, fake fixtures, secret-free deployment docs, normal `STATUS.md` transition, CI only for offline tests. Not in implementation: `AGENTS.md` amendment, live settings/App/rulesets/secrets, credentials/account data, product runtime, Hermes/MCP/MemoryStore/BLUECAD/process kernel/078. Dependencies pinned/justified/scanned/service-limited; no agent framework.

## 27. Non-goals

No automatic next-spec selection; simultaneous fronts/branches/actors/PRs; autonomous merge/approval/release/deploy/priority/governance/settings; force-delete/history rewrite/protected-test mutation; arbitrary shell; provider fallback/bidding/swarm; unbounded loops; untrusted fork execution; replacement of runtime 059b/Hermes/Actions; raw model/secret canonical storage; outage availability guarantee; or 078/other frozen work.

## 28. Definition result

Complete when this one-document PR remains `planned`; records section 2.1 sequencing honestly; freezes architecture/state/auth/expiry/branch/PR/dispatch/lease/head/human outcomes/provider/finding IDs/permissions/cost/tests/rollout; preserves mandatory proof gates; keeps execution-spine conflict blocked pending governance; asserts no unproven mechanism as working; changes no runtime/workflow/App/provider/secret/ruleset/dependency/setting; passes exact-head gates and review; and stops for maintainer merge.

Merge does not authorize governance, proofs against live JarvisOS, readiness, implementation, provider calls, or automated merge.
