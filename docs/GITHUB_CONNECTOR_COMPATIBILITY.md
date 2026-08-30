# GitHub connector compatibility policy

Status: canonical temporary operational supplement
Effective date: 2026-08-30
Scope: repository-development transport mechanics only

This document exists because the official OpenAI/ChatGPT GitHub connector currently has a deterministic Draft/Ready GraphQL regression. It does not change JarvisOS product/runtime authority, spec/readiness authority, merge criteria, review requirements, exact-SHA rules, provider policy, credentials, budgets, or security boundaries.

`AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`, and `docs/specs/STATUS.md` remain higher authority. This supplement only defines a connector-compatibility transport mode where those documents do not otherwise require GitHub draft state.

## 1. Incident and activation

Compatibility mode is ACTIVE while either condition holds:

1. upstream OpenAI connector bug `openai/codex#41433` remains open; or
2. the dedicated connector action `mark_pull_request_ready_for_review` fails with the known GraphQL schema-selection error involving `Repository.fullDatabaseId` / `headRepository.fullDatabaseId`.

The observed failure is connector-side response/query generation. GitHub's supported `markPullRequestReadyForReview` mutation itself remains valid. Do not treat this incident as repository corruption, permission failure, CI failure, or a reason to mutate product code.

## 2. New automated PRs while compatibility mode is active

Automated JarvisOS delivery MUST NOT create new draft pull requests while compatibility mode is active.

Normal flow becomes:

1. create/use the implementation or planning branch from an exact authorized base;
2. perform bounded candidate work and focused validation on the branch or proposal artifact;
3. once there is a coherent first head worth exposing as the active PR, re-read exact base/head and create the PR directly with `draft=false`;
4. continue ordinary repair commits on that PR when required;
5. every head mutation invalidates affected head-specific CI/review/evidence exactly as before;
6. merge remains forbidden until all canonical exact-head merge gates pass.

`draft=false` is transport metadata only. It does NOT mean semantic acceptance, readiness, approval, queue promotion, review completion, or merge authorization.

If a PR-triggered CI path is materially required before the branch is otherwise reviewable, the coordinator may still create the PR directly non-draft once scope and branch identity are stable enough to avoid misleading or duplicate fronts. No review request is implied unless explicitly made.

## 3. Existing draft PR recovery

For an already-open draft PR during compatibility mode:

- do not repeatedly retry the known-broken Draft -> Ready action;
- never use generic PR update as a fake Ready transition;
- never change product/runtime code merely to solve connector metadata failure;
- first preserve exact base/head and inspect comments, reviews, unresolved threads, and provenance.

If the draft has no material review/comment/thread provenance that would be lost operationally, the coordinator may close it and create a same-base, same-head, non-draft replacement PR. The replacement must link the superseded PR in its body or conversation, and the old PR remains historical provenance only.

If material review/thread provenance exists, prefer preserving the existing PR and require either a verified repaired dedicated connector action or an explicit maintainer/external authenticated GitHub transition. Do not silently discard unresolved review state merely to avoid one metadata limitation.

## 4. Exit from compatibility mode

Do NOT disable compatibility mode merely because time passed, a retry happened to differ, or an upstream issue was closed.

Return to normal draft-capable automation only after BOTH:

1. upstream evidence indicates the connector defect is fixed or the relevant incident is closed/resolved; and
2. one bounded live verification confirms `mark_pull_request_ready_for_review` actually changes a low-risk draft PR to `draft=false`, followed by an independent fresh PR read.

If Ready -> Draft is needed by a future workflow, verify that direction separately before relying on it.

After successful verification, remove or mark this supplement inactive in a bounded governance change. Do not leave stale compatibility rules indefinitely.

## 5. Invariants that do not change

Compatibility mode never weakens:

- one ChatGPT GitHub/shared-authority writer at a time;
- exact-SHA/CAS correctness;
- STATUS.md as sole live work-state registry;
- accepted spec/readiness requirements;
- semantic acceptance and independent review requirements;
- terminal frozen-head gates;
- no auto-merge;
- explicit exact-head merge and post-merge reconciliation;
- no implementation authority from `planned` state;
- no authority from Coordination Bus V2 messages or external review helpers.

The purpose is to remove a fragile connector-state transition from the critical path, not to weaken governance.
