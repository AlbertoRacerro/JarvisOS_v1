# 021 — Codex PR autopush without automerge

Status: ready
Depends on: 017 (Autonomous three-tier review), 019 (Senior review hardening)

## Goal

Allow Codex-generated fixes to be pushed automatically to the existing pull
request branch after a reviewer/fix-request asks Codex to make changes, while
preserving the existing human merge boundary.

The intended operating model is:

- reviewers and maintainers can ask Codex to fix a PR;
- Codex may push commits to the PR branch;
- CI and automated review run after the push;
- if Codex goes out of scope, the next review round asks Codex to correct or
  revert;
- only a human maintainer merges.

This spec intentionally removes the manual "apply changes / update branch" step
as a safety boundary. That click does not add meaningful safety if the resulting
branch is reviewed only afterward. Safety must come from post-push CI/review and
the no-automerge rule, not from manual branch application friction.

## Root causes addressed

- **Task-local Codex commits are not branch evidence.** Codex Cloud can report
  that it committed a patch inside its task workspace, while the GitHub PR
  branch remains unchanged. The maintainer may then believe a fix exists when
  `origin/<branch>` still points to the old head.
- **Manual branch update is friction, not review.** The maintainer often cannot
  inspect the Codex patch before clicking "apply/update branch"; the real review
  happens after the branch changes.
- **Review loop stalls on non-materialized fixes.** Automated reviewers may ask
  Codex for fixes, Codex may complete them, but the PR remains stale until a
  human performs a mechanical update step.
- **Wrong authority signal.** Codex summaries are advisory. The authoritative
  state is the GitHub remote branch head, CI, and subsequent review output.

## Scope

This spec covers a future autopush capability for Codex-generated PR fixes.

The future implementation may add:

- a GitHub workflow that reacts to authorized Codex/fix-request events;
- a small script that validates the target PR branch and performs the push or
  verifies that Codex-native auto-apply has already pushed;
- comments that report the final remote branch head SHA;
- tests for branch targeting, no-automerge behavior, and blocked high-risk
  operations.

The policy is deliberately permissive for ordinary code/docs/test/spec changes.
Codex is allowed to make imperfect or out-of-scope commits on PR branches. Those
are handled by CI, review, additional Codex fixes, or human-requested revert.

## Hard boundaries

The future implementation must preserve these boundaries:

1. Codex or its actuator must never push to `master`.
2. Codex or its actuator must never merge a PR.
3. Codex or its actuator must never force-push.
4. Codex or its actuator must never delete branches.
5. Codex or its actuator must not modify `.github/workflows/**` unless the
   maintainer explicitly requests that class of change in a separate PR.
6. Codex or its actuator must not modify `.env*`, secret, token, credential, or
   key files unless the maintainer explicitly requests that class of change in a
   separate PR.

These are not general-purpose enterprise security controls. They only protect
the final integration boundary and the mechanisms that judge Codex's own work.

## Non-goals

- No automerge.
- No push to `master`.
- No force-push.
- No branch deletion.
- No default workflow self-modification.
- No default secrets/env/credential file modification.
- No heavy pre-push semantic gate for ordinary source, docs, tests, or specs.
- No attempt to prevent all bad Codex patches before they reach the PR branch.
  Bad patches are expected to be caught by CI and review after the push.
- No requirement that Codex patches be perfect before materialization.
- No replacement for CI, cheap review, senior review, or human merge authority.
- No implementation in this spec-only PR.

## Desired operating model

A reviewer or maintainer posts a bounded fix request, for example:

```text
@codex fix the review findings on this existing PR branch.

You may push commits to this PR branch.
Do not open a new PR.
Do not merge.
Do not push to master.
Do not force-push.
Do not modify .github/workflows/** or secret/env files.

After applying the fix, the GitHub PR branch must contain the new commit.
A task-local Codex commit or summary is not sufficient.
Comment the final remote branch head SHA.
````

After Codex completes:

1. the PR branch head on GitHub advances;
2. CI and review workflows run on the new head;
3. the PR conversation records the pushed SHA and changed files;
4. if the change is bad or out of scope, review asks Codex to correct or revert;
5. the maintainer merges only after the branch state and reviews are acceptable.

## Implementation options

### Option A — Codex-native auto-apply

If Codex Cloud / GitHub integration supports automatic application of completed
task changes to the existing PR branch, prefer this path.

The implementation should document:

* the required Codex/GitHub setting;
* the permission needed for Codex to push to PR branches;
* how to verify that the remote PR branch head advanced;
* what comment or status is emitted when auto-apply fails.

### Option B — JarvisOS GitHub actuator

If Codex-native auto-apply is unavailable or unreliable, add a small actuator.

The actuator may:

* react to PR comments or Codex completion signals;
* resolve the target PR branch;
* refuse protected/default branches;
* perform the push or apply a Codex-provided patch;
* run lightweight verification;
* comment final branch head SHA and changed files.

The actuator must still obey the hard boundaries above.

## Acceptance criteria

1. A future implementation documents whether Codex-native auto-apply is
   supported for this repository. If it is supported, the exact setting/flow is
   documented.
2. If Codex-native auto-apply is not sufficient, a future implementation provides
   a bounded actuator that can push Codex fixes to existing PR branches.
3. The autopush path refuses to push to `master`.
4. The autopush path refuses to merge.
5. The autopush path refuses force-push.
6. The autopush path refuses branch deletion.
7. The autopush path refuses `.github/workflows/**` changes unless the
   maintainer explicitly requests workflow modification in a separate PR.
8. The autopush path refuses `.env*`, secret, token, credential, or key file
   changes unless the maintainer explicitly requests that class of change in a
   separate PR.
9. Ordinary source, docs, tests, and spec files are not blocked by default.
10. After a successful autopush, the PR branch remote head visibly advances on
    GitHub.
11. After a successful autopush, the bot comments the final remote branch head
    SHA and changed files.
12. If Codex reports a task-local commit that is not present on the remote PR
    branch, the system reports that as non-materialized work rather than treating
    it as complete.
13. CI and automated review remain the authority for whether the pushed change is
    acceptable.
14. Human merge authority is unchanged.

## Required tests for future implementation

A future implementation must include deterministic tests for:

* refusing `master` as target branch;
* refusing force-push mode;
* refusing branch deletion;
* refusing workflow file changes by default;
* refusing env/secret/token/key files by default;
* allowing ordinary source/docs/tests/spec changes;
* reporting a final remote branch head SHA after successful push;
* detecting a Codex summary/commit reference that is not present on the remote
  PR branch;
* ensuring no code path performs merge.

## Notes for implementation PR

This spec intentionally favors operational autonomy over conservative pre-push
blocking. The correct failure handling is:

* let Codex push to the PR branch;
* let CI/review inspect the result;
* ask Codex to correct or revert if it went out of scope;
* never merge automatically.

Do not expand this into a general agent sandbox or enterprise policy system.
The first implementation should be the smallest working autopush path that
removes the manual "update branch" step while preserving the hard boundaries.
