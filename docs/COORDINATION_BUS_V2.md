# JarvisOS Coordination Bus V2

Status: canonical repository-development coordination contract when present on exact `master`
Authorized by maintainer: 2026-08-30

This document defines a narrow, non-authoritative communication and pre-build bus for the interchangeable JarvisOS Roadmap Builder A/B/C/D schedulers. It exists so a scheduler that wakes while another scheduler owns the ChatGPT writer mutex can still spend its run producing useful bounded material for the next writer, without turning comments, candidate patches, checkpoints, or automation output into a second source of truth.

The invariant is:

> Coordination messages and candidate workpacks may reduce duplicated work. They never establish repository authority and are never self-applying.

`AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`, `docs/specs/STATUS.md`, accepted specs/readiness, exact Git state, and exact-head deterministic evidence retain their normal authority. This bus cannot override any of them.

## 1. Activation gate

The V2 bus is active only when this file exists on fresh exact `master`. A copy on a PR branch is planning evidence only.

The canonical transport is one dedicated open GitHub issue titled exactly:

`JarvisOS Coordination Bus V2`

The issue body must identify itself as non-authoritative and link this contract. Individual messages are append-only top-level issue comments. Do not repurpose an implementation/planning PR, `STATUS.md`, a spec file, automation title, Gmail, or the historical PR #432 checkpoint comments as the bus.

## 2. Primary objective: useful work during writer contention

A scheduler that sees another fresh A/B/C/D writer lease must not automatically waste the run if useful safe work is available.

After activation, the non-writer should use the run for the highest-value bounded pre-build work that does not mutate repository/shared authority. Useful work includes:

- source, ownership, dependency and exact-head inventory;
- accepted-spec/readiness analysis;
- acceptance-criterion mapping;
- threat-model or failure-mode analysis;
- focused test design and test-command derivation;
- CI/review/tooling diagnosis;
- connector-capability investigation;
- review checklists and semantic-risk analysis;
- implementation packets;
- for already implementation-authorized work, complete candidate code/document changes represented as a bounded unified diff or equivalent candidate patch;
- review or repair workpacks against an existing exact PR head;
- any other bounded material that lets the next writer review/revalidate/apply rather than rediscover or rewrite from zero.

Helpers prefer an explicit unexpired `REQUEST`. If no useful request exists, a helper may select the highest-value non-duplicative pre-build task visible from fresh canonical state, subject to the lifecycle boundary below.

## 3. Lifecycle boundary: READY code versus planned prework

The bus must never manufacture implementation authority.

### Implementation-authorized slice

If fresh canonical state proves the target slice is implementation-authorized under the normal lifecycle, a BUSY-blocked helper may prepare a `WORKPACK` or `CANDIDATE_PATCH` containing candidate implementation code. The candidate remains proposal-only and may not be written to a branch, PR, repository file, shared store, or product runtime by the helper.

### Planned / not implementation-authorized slice

If the target row is `planned`, backlog-only, missing accepted readiness, dependency-blocked, or otherwise not implementation-authorized, the helper may prepare only pre-implementation material such as:

- file/owner/dependency inventory;
- definition/spec/readiness inputs;
- acceptance criteria and non-goals;
- threat/failure-mode analysis;
- test plan;
- architecture alternatives;
- review checklist;
- implementation packet structure without product-code implementation.

It must not generate a product-code candidate patch for such a slice. `planned` remains non-implementable even through the bus.

## 4. Message envelope

Every operational comment starts with the exact marker:

`<!-- JARVIS_COORD_V2 -->`

and contains these fields:

```text
message_id: <globally unique producer-generated id>
request_id: <request id or NONE>
producer: <A|B|C|D|SUPERVISOR>
target: <A|B|C|D|WRITER|ANY_HELPER>
kind: <REQUEST|RESULT|FINDING|INFO|WORKPACK|CANDIDATE_PATCH|CANCEL>
created_at_utc: <UTC ISO-8601>
expires_at_utc: <UTC ISO-8601>
master_sha: <40-char SHA or NONE>
pr: <number or NONE>
pr_head_sha: <40-char SHA or NONE>
authority: NONE
payload: <bounded text>
```

For `REQUEST`, `request_id` equals `message_id`. A response to a request repeats that request's `request_id`.

Default TTL is 2 hours. A shorter TTL should be used for fast-moving PR/CI/tooling state. A workpack may use a longer TTL only when its claims are explicitly exact-SHA bound; no message may claim indefinite freshness.

## 5. WORKPACK and CANDIDATE_PATCH payload

A useful pre-build artifact should contain enough information for a later writer to validate it without rediscovering the entire task. Where applicable, include:

```text
workpack_id: <id>
candidate_kind: <patch|implementation_packet|review_packet|test_plan|research>
base_master_sha: <40-char SHA>
target_pr: <number or NONE>
target_pr_head_sha: <40-char SHA or NONE>
scope: <bounded purpose>
allowed_paths: <paths or NONE>
authority_context_read: <canonical files/spec/readiness consulted>
assumptions: <bounded list>
acceptance_mapping: <criterion -> proposed evidence/change>
proposed_changes: <summary>
candidate_diff: <unified diff when practical, or NONE>
tests_to_run: <commands/checks>
risks_or_open_questions: <bounded list>
revalidation_required: YES
```

A `CANDIDATE_PATCH` should normally include a directly inspectable unified diff when the candidate is small enough. If the candidate would make the comment unwieldy, split it into independently useful path-bounded workpacks rather than dumping a huge patch. Keep a single bus comment comfortably below GitHub comment limits; as an operating target, keep candidate patch text below roughly 45–50k characters.

A candidate patch may contain only repository material that is safe to place in the repository's public coordination issue. Never include secrets, credentials, tokens, private user data, sensitive provider material, private generated data, or binary content.

## 6. Authority and freshness rules

Every bus artifact is advisory and untrusted for mutation purposes, including a syntactically valid patch or passing-test claim.

A consumer must never infer from a message that:

- a spec is ready/implementing/merged;
- a dependency is satisfied;
- a PR is accepted, mergeable, approved, or merge-authorized;
- a workflow/check remains green;
- a branch/head remains current;
- a scheduler owns the writer lock;
- Codex budget/quota is available or consumed;
- a queue item is next;
- a finding is closed;
- a maintainer decision has been canonized;
- a candidate patch is correct, current, accepted, or authorized to apply.

Before any GitHub/shared-authority mutation, the current writer reconstructs all relevant authority from fresh canonical sources and exact Git/PR state. If `master_sha`, `base_master_sha`, or `pr_head_sha` differs from the relevant current SHA, head-sensitive conclusions are stale. A stale workpack may be used as a search/design hint, but its code must be re-derived or intentionally rebased and re-reviewed before use.

Bus messages must not contain fields named `owner`, `phase`, `queue_state`, `spec_status`, `merge_authority`, `current_truth`, or equivalent shadow-state claims.

## 7. Mutex exception and BUSY-helper algorithm

Appending one valid `JARVIS_COORD_V2` comment to the dedicated bus issue is a narrow exception to the global ChatGPT writer mutex because the comment has `authority: NONE` and cannot itself mutate repository/shared authority.

Therefore a scheduler that sees another fresh A/B/C/D `[BUSY ...]` marker should, when useful wall-clock budget remains:

1. perform fresh read-only repository/tool inspection;
2. inspect recent unexpired V2 requests/workpacks to avoid duplicate effort;
3. prefer one useful open `REQUEST` targeted to `ANY_HELPER` or that scheduler;
4. otherwise choose the highest-value non-duplicative pre-build task permitted by current canonical readiness/lifecycle authority;
5. if implementation is already authorized, prepare a bounded implementation/review/repair workpack or candidate patch; otherwise remain planning/readiness/research-only;
6. perform any read-only validation possible in the available environment and record exactly what was and was not run;
7. append at most one consolidated `RESULT`, `FINDING`, `INFO`, `WORKPACK`, or `CANDIDATE_PATCH` V2 message;
8. exit without changing code, branches, PR state/body, reviews, labels, `STATUS.md`, specs/readiness, workflows/settings, automation prompts/titles, merge state, or any other shared authority.

The exception does not permit updating/deleting existing bus comments. Messages are append-only.

A BUSY-blocked helper does not acquire another scheduler title, does not claim a lane, and does not launch external implementation workers that would create budget/authority ambiguity. Its output is the bus workpack itself.

The current writer may append `REQUEST`, `CANCEL`, result, or workpack messages while holding the writer lease, but bus traffic never substitutes for the lease itself.

## 8. Next-writer consumption rule

A scheduler that successfully acquires the writer lease should inspect relevant unexpired V2 workpacks before starting equivalent analysis or implementation from zero.

For each relevant candidate it may use, the writer must:

1. re-read fresh exact `master`, `STATUS.md`, selected spec/readiness, target PR/head and affected authority;
2. verify that implementation remains authorized and that dependencies/scope still hold;
3. compare the candidate's base/head to current exact SHAs;
4. semantically review the proposed diff or workpack rather than trusting the producer's conclusion;
5. re-run or reproduce the focused tests/checks needed for the current head;
6. adjust/rebase/rederive the candidate if stale or partially invalid;
7. apply only the smallest still-valid candidate through the normal writer mutation path and exact-head/CAS guards;
8. invalidate old evidence normally after any resulting head mutation.

The writer should prefer reuse when it saves work without reducing confidence. It should reject or redo a workpack when fresh state makes that safer or cheaper.

No `consumed`, `claimed`, `accepted`, or similar authoritative bus state is required. The issue remains an append-only advisory log.

## 9. Request stealing and deduplication

An explicit request is eligible only when:

- its TTL has not expired;
- it is not followed by a valid `CANCEL` for the same `request_id`;
- there is no already-published adequate response/workpack for the same request unless independent duplicate evidence was requested;
- required exact SHA bindings still match or the request explicitly asks for fresh re-resolution;
- the work is bounded enough to produce a useful artifact in the current run.

If another adequate workpack already exists, a helper should choose a disjoint unresolved subproblem rather than reproduce it. If two helpers race and both publish, the writer may independently evaluate either or both; neither gains authority.

Do not create a second coordination registry to mark requests claimed/completed.

## 10. Safety and content restrictions

Never place secrets, credentials, tokens, private user data, provider-sensitive material, huge logs, or binary artifacts in the public coordination issue.

Do not use the bus for:

- GitHub writes other than the single append-only V2 comment itself during the mutex exception;
- implementation authority for a planned/not-ready slice;
- direct branch or PR mutation by a BUSY-blocked helper;
- merge/approval/review decisions;
- queue/spec/readiness state;
- budget accounting;
- persistent lane ownership;
- scheduler lease/lock state;
- user notifications;
- runtime/product authority;
- self-approval or self-application of candidate patches.

P0/security/secret/data-loss matters follow the normal maintainer-interruption path and must not be dumped into the bus.

## 11. Historical V1 checkpoints

PR #432 comments `5463341236`, `5463358988`, and `5463359860` remain historical provenance only. They must never be updated, consumed as current coordination state, or used as the V2 transport.

V2 deliberately removes the V1 failure modes: mutable checkpoint state, `owner/phase/next_action` shadow authority, PR-local lifetime, implicit freshness, and coupling between useful helper work and the writer mutex.

## 12. Enforcement target

`128 ARCHITECTURE-ENFORCEMENT-GATE-1` must treat the authority boundary in this contract as an enforcement target: tooling may consume V2 messages/workpacks only as advisory inputs and must fail closed if a coordination artifact or candidate patch is ever treated as queue, readiness, semantic-acceptance, approval, merge, persistence, self-application, or source-of-truth authority.
