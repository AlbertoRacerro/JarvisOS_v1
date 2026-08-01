# 079 — AUTONOMOUS-DEVELOPMENT-LOOP-0: minimal scheduled continuation

Status: implementation contract. `docs/specs/STATUS.md` is authoritative.

Depends on: 022

## 1. Acceptance criterion

When one already-authorized implementation session stops, repository work resumes without a new maintainer message, on the same pull-request branch, for the same specification, and from the exact current head.

V0 satisfies this criterion with one GitHub Actions workflow scheduled once per day. It reuses the installed `anthropics/claude-code-action@v1` integration and the existing `CLAUDE_CODE_OAUTH_TOKEN`. It adds no provider account, credential, repository, GitHub App, service, database, queue, control branch, claim, or lease.

## 2. Minimum-necessary test

### Test del minimo necessario
Acceptance criterion of the specification:
An interrupted implementation session resumes on the same branch and specification without a new maintainer message.

Does this work satisfy it?                   yes
Can the criterion be met without it?         no — a future trigger must observe the interrupted front and invoke the existing agent integration.
Can it be met with less infrastructure?      no — one daily workflow, one standard-library script, existing GitHub state, and the existing Claude action are the minimum mechanism.

Binding consequence: do not build the earlier GitHub App, webhook service, database, queue, `jarvis-control` branch, compare-and-swap authority ledger, claim/lease system, ruleset laboratory, token-revocation programme, or sandbox repository for 079 v0. The already merged CAS experiments remain historical evidence, not an implementation dependency.

## 3. Scope

079 owns only scheduled continuation of one existing implementation pull request:

1. enumerate open pull requests;
2. read `docs/specs/STATUS.md` from each exact pull-request head;
3. find exactly one same-repository, non-draft pull request whose own head registry contains exactly one `in_review` row linked to that pull-request number;
4. verify base `master`, an unprotected head branch, a valid exact head, specification binding, and ancestry from the prior continuation checkpoint;
5. in `SHADOW`, report the exact action without invoking Claude or mutating GitHub;
6. in `EXECUTE_NO_MERGE`, invoke the existing Claude Code Action on that exact head;
7. treat Claude's working-tree result as untrusted input;
8. validate paths and run deterministic gates in a separate write-authority job;
9. push only a non-forced same-branch commit when the remote head still equals the planned head;
10. record one idempotent checkpoint marker in the pull-request conversation.

079 does not select a new specification, create a pull request, perform review, classify findings, request fixes or re-review, or merge.

## 4. Separate specification 080

Implementer/reviewer separation and the finding → correction → re-review cycle belong exclusively to spec 080 `AUTONOMOUS-REVIEW-REPAIR-0`.

080 remains independently removable and `planned`. No 080 behavior may be added to the 079 workflow.

## 5. Workflow and modes

Implementation path: `.github/workflows/daily-development-continuation.yml`.

Triggers:

```yaml
on:
  schedule:
    - cron: "17 4 * * *"
  workflow_dispatch:
```

Concurrency:

```yaml
concurrency:
  group: jarvis-development-continuation
  cancel-in-progress: false
```

Repository variable `JARVISOS_CONTINUATION_MODE` has a closed vocabulary:

- `OFF`: default when absent; no API discovery beyond workflow checkout, no Claude invocation, no mutation;
- `SHADOW`: reconstruct and report the eligible exact-head action; no Claude invocation and no mutation;
- `EXECUTE_NO_MERGE`: run the bounded continuation path; never merge.

Any other value fails closed. Tests never enter a live provider path.

## 6. Existing credential boundary

The workflow reuses `CLAUDE_CODE_OAUTH_TOKEN`, already named by `.github/workflows/claude-review.yml`.

GitHub does not expose secret values through repository APIs. The plan job checks only non-empty presence without printing or exporting the value. Actual validity or expiry is exercised only when the maintainer changes the mode to `EXECUTE_NO_MERGE`; a rejected authentication attempt fails the workflow before any push.

No new credential is introduced. `GITHUB_TOKEN` is used only for GitHub API reads, the isolated validation job's non-forced branch push, and the checkpoint comment.

## 7. Authority separation inside the workflow

### 7.1 Plan job

The plan job has read-only repository and pull-request permissions. It reconstructs the sole active front from current GitHub facts and exports the exact plan.

### 7.2 Claude generation job

The Claude job:

- has `contents: read` only;
- checks out the exact planned SHA with persisted credentials disabled;
- uses `anthropics/claude-code-action@v1` and the existing OAuth secret;
- receives the exact specification, pull request, branch, input head, and control constraints;
- may modify only the local working tree;
- cannot push, comment, label, merge, dispatch another model, or own a write token;
- exports a bounded binary Git patch as an artifact.

A local Claude commit is harmless: the exported artifact is always a patch relative to the planned exact head. The remote head is reread and must remain unchanged after Claude exits.

### 7.3 Validation and push job

Only the separate validation job receives `contents: write`. It does not receive the Claude OAuth secret. It:

1. checks out the planned exact head;
2. applies the untrusted patch;
3. rejects protected or sensitive paths;
4. runs deterministic gates before any push;
5. rereads the remote branch head;
6. commits and performs a normal non-forced push only when the remote head still equals the planned head;
7. records the input/output checkpoint marker.

A push made with `GITHUB_TOKEN` is not assumed to trigger CI, so this job runs the complete deterministic gate set itself.

## 8. Discovery and authority

Implementation script: `scripts/daily_development_continuation.py`, standard library only.

The script lists all open pull requests with bounded pagination. For each non-draft pull request it reads `docs/specs/STATUS.md` from the exact head SHA, not from `master`.

An eligible front requires:

- exactly one active registry row in that head;
- status exactly `in_review`;
- exactly one implementation PR number, equal to the pull request being inspected;
- same base and head repository;
- base branch `master`;
- head branch not `master` or `main`;
- valid 40-character lowercase hexadecimal base and head SHAs;
- the same three-digit specification identifier in the registry and PR title, body, or branch.

Zero eligible fronts is an honest no-op. More than one eligible front, an `in_progress` row without a durable PR, multiple active rows, incomplete pagination, a fork, or any mismatch fails closed.

## 9. Checkpoint and idempotency

The marker is:

```text
<!-- jarvis-continuation:v1 spec=<spec> pr=<number> input=<sha> output=<sha> result=<changed|no_change> -->
```

The current head must descend from the last output checkpoint, or from the PR base when no marker exists.

- A `no_change` marker whose output equals the current head makes that head terminal and prevents another invocation.
- A `changed` marker must name the exact current head as output; that output becomes the next checkpoint.
- Two markers with the same input and different outputs/results are an integrity error.
- A marker claiming an output not observed as the current head is an integrity error.

No separate ledger or mutable label is used.

## 10. Protected paths and patch limits

The generated patch is rejected if it changes:

- `.github/**`;
- `AGENTS.md`;
- `CODEOWNERS`;
- `scripts/daily_development_continuation.py`;
- `backend/tests/test_daily_development_continuation.py`;
- environment, secret, token, credential, or key paths.

`docs/specs/STATUS.md` may change only the active specification row. No registry row may be added or removed by scheduled continuation.

V0 limits the patch to 20 files and 200,000 bytes.

## 11. Deterministic gates before push

For a non-empty patch, the validation job runs:

1. spec-registry self-test and live registry validation;
2. cheap-review and manual-review offline self-tests;
3. dependency installation from existing requirement files;
4. Ruff over backend code, tests, and repository control scripts including the 079 script;
5. full backend Pytest;
6. frontend `npm ci` and production build when a frontend file changed;
7. `git diff --check`;
8. exact remote-head reread.

Any failure produces zero push and zero checkpoint marker.

## 12. Offline tests

`backend/tests/test_daily_development_continuation.py` uses fake GitHub readers and no network or provider.

Required coverage includes OFF, SHADOW, secret-presence enforcement, exact PR-head registry discovery, zero-front no-op, draft/fork/base/spec/ancestry failures, multiple-front rejection, checkpoint idempotency, conflicting-marker rejection, protected paths, file-count limits, active-row-only STATUS changes, and static workflow authority checks.

## 13. Acceptance proof

Acceptance is established in layers:

1. offline deterministic tests prove discovery, exact-head binding, idempotency, authority separation, and fail-closed paths;
2. normal PR CI proves the implementation and complete repository remain green;
3. after merge, an Actions run in `SHADOW` proves GitHub-hosted discovery without provider execution or mutation;
4. the first real eligible run in `EXECUTE_NO_MERGE` proves cross-session continuation using the existing credential. Authentication failure is a credential obstacle, not a reason to build new infrastructure.

Default `OFF` means merge alone invokes no provider and incurs no spend.

## 14. Non-goals

- review, finding management, repair, or re-review;
- merge or auto-merge;
- automatic selection or authorization of a new specification;
- continuation before an implementation PR exists;
- parallel fronts, forks, or multiple repositories;
- App, webhook service, daemon, database, queue, control branch, claim, or lease;
- paid-provider tests or synthetic work created only to exercise the workflow;
- changes to JarvisOS runtime, Hermes, backend APIs, frontend product behavior, repository settings, secrets, rulesets, or branch protection.

## 15. Rollback

Delete one workflow, one script, and one focused test. No application state, schema, account, credential, or external service must be migrated.

## 16. Definition of done

- workflow, script, and focused tests merged;
- 079 exact-head PR CI green;
- all current review findings resolved;
- mode defaults to `OFF`;
- no new credential, account, repository, state store, dependency, or runtime service;
- 079 recorded as `merged` after integration;
- 080 remains separate and `planned`;
- a real `SHADOW` run is observed without provider execution or mutation.