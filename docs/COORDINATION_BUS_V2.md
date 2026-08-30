# JarvisOS Coordination Bus V2

Status: canonical repository-development coordination contract when present on exact `master`
Authorized by maintainer: 2026-08-30

This document defines a narrow, non-authoritative communication bus for the interchangeable JarvisOS Roadmap Builder A/B/C/D schedulers. It exists to let a current writer delegate or receive useful read-only work without turning comments, checkpoints, or automation output into a second source of truth.

The invariant is:

> Coordination messages may point to evidence or request work. They never establish repository authority.

`AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`, `docs/specs/STATUS.md`, accepted specs/readiness, exact Git state, and exact-head deterministic evidence retain their normal authority. This bus cannot override any of them.

## 1. Activation gate

The V2 bus is active only when this file exists on fresh exact `master`. A copy on a PR branch is planning evidence only.

The canonical transport is one dedicated open GitHub issue titled exactly:

`JarvisOS Coordination Bus V2`

The issue body must identify itself as non-authoritative and link this contract. Individual messages are append-only top-level issue comments. Do not repurpose an implementation/planning PR, `STATUS.md`, a spec file, automation title, Gmail, or the historical PR #432 checkpoint comments as the bus.

## 2. What the bus is for

Allowed uses are bounded coordination that materially reduces latency or duplicated work, especially while another scheduler holds the ChatGPT writer mutex:

- a writer publishes a read-only investigation, audit, comparison, connector-capability lookup, CI diagnosis, review-evidence check, ownership inventory, or other bounded request;
- a non-writer scheduler discovers an unexpired request and performs only the read-only work authorized by that request;
- a helper publishes a result/finding for the writer to independently revalidate;
- a scheduler publishes a material tooling observation that another writer would otherwise rediscover, provided it is exact-head/freshness bound where applicable.

The bus is not required for ordinary work. Do not create messages that add no evidence, risk reduction, or useful handoff.

## 3. Message envelope

Every operational comment starts with the exact marker:

`<!-- JARVIS_COORD_V2 -->`

and contains these fields:

```text
message_id: <globally unique producer-generated id>
request_id: <request id or NONE>
producer: <A|B|C|D|SUPERVISOR>
target: <A|B|C|D|WRITER|ANY_HELPER>
kind: <REQUEST|RESULT|FINDING|INFO|CANCEL>
created_at_utc: <UTC ISO-8601>
expires_at_utc: <UTC ISO-8601>
master_sha: <40-char SHA or NONE>
pr: <number or NONE>
pr_head_sha: <40-char SHA or NONE>
authority: NONE
payload: <bounded text>
```

For `REQUEST`, `request_id` equals `message_id`. A `RESULT`, `FINDING`, or `CANCEL` answering a request repeats that request's `request_id`.

Default TTL is 2 hours. A shorter TTL should be used for fast-moving PR/CI/tooling state. No message may claim indefinite freshness.

## 4. Authority and freshness rules

A bus message is always advisory and untrusted for mutation purposes.

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
- a maintainer decision has been canonized.

Before any GitHub/shared-authority mutation, the current writer must reconstruct all relevant authority from fresh canonical sources and exact Git/PR state. If a message contains `master_sha` or `pr_head_sha` and the relevant current SHA differs, the message is stale for head-sensitive conclusions. A stale result may be used only as a search hint and must be re-derived.

Bus messages must not contain fields named `owner`, `phase`, `queue_state`, `spec_status`, `merge_authority`, `current_truth`, or equivalent shadow-state claims.

## 5. Mutex exception

Appending one valid `JARVIS_COORD_V2` comment to the dedicated bus issue is a narrow exception to the global ChatGPT writer mutex because the comment has `authority: NONE` and cannot mutate repository/shared authority.

Therefore a scheduler that sees another fresh A/B/C/D `[BUSY ...]` marker may still:

1. perform read-only repository/tool inspection;
2. consume at most one useful unexpired `REQUEST` targeted to `ANY_HELPER` or to that scheduler;
3. append one bounded `RESULT`, `FINDING`, or `INFO` V2 message;
4. exit without changing code, branches, PR state/body, reviews, labels, `STATUS.md`, specs/readiness, workflows/settings, automation prompts/titles, merge state, or any other shared authority.

The exception does not permit updating/deleting existing bus comments. Messages are append-only.

The current writer may append `REQUEST`, `CANCEL`, or result messages while holding the writer lease, but bus traffic never substitutes for the lease itself.

## 6. Request stealing and deduplication

Helpers prefer explicit open requests over unsolicited audits. A request is eligible only when:

- its TTL has not expired;
- it is not followed by a valid `CANCEL` for the same `request_id`;
- there is no already-published adequate `RESULT` for the same request unless the request explicitly asks for independent duplicate evidence;
- required exact SHA bindings still match or the request explicitly asks for fresh re-resolution;
- the work is read-only and bounded enough to finish in the current run.

If two helpers race and both publish results, the writer may use either or both as advisory evidence; neither result gains authority. Do not create a second coordination registry to mark requests claimed/completed.

## 7. Safety and content restrictions

Never place secrets, credentials, tokens, private user data, large logs, generated patches, binary artifacts, or provider-sensitive material in the public coordination issue.

Do not use the bus for:

- GitHub writes other than the single append-only V2 comment itself;
- implementation delegation to GLM/Claude/Codex;
- code or document patches;
- merge/approval/review decisions;
- queue/spec/readiness state;
- budget accounting;
- persistent lane ownership;
- scheduler lease/lock state;
- user notifications;
- runtime/product authority.

P0/security/secret/data-loss matters follow the normal maintainer-interruption path and must not be dumped into the bus.

## 8. Historical V1 checkpoints

PR #432 comments `5463341236`, `5463358988`, and `5463359860` remain historical provenance only. They must never be updated, consumed as current coordination state, or used as the V2 transport.

V2 deliberately removes the V1 failure modes: mutable checkpoint state, `owner/phase/next_action` shadow authority, PR-local lifetime, implicit freshness, and coupling between audit communication and the writer mutex.

## 9. Enforcement target

`128 ARCHITECTURE-ENFORCEMENT-GATE-1` must treat the authority boundary in this contract as an enforcement target: tooling may consume V2 messages only as advisory inputs and must fail closed if a coordination artifact is ever treated as queue, readiness, semantic-acceptance, approval, merge, persistence, or source-of-truth authority.
