# 022/128 Codex result-delivery authority amendment — 2026-09-13

Status: maintainer-authorized control-plane repair

This amendment closes the remaining spec-022 materialization gap while preserving spec-128's architecture ratchet. It is explicit authority for one narrowly bounded repository-development path, not a general relaxation of AE004.

## Authorized authority

Exactly one workflow trigger is admitted as an AE004 accepted owner:

`/.github/workflows/codex-result-delivery.yml::on.issue_comment`

Its sole authority is to bind one newly-created pull-request comment to immutable metadata and dispatch the already-trusted `cloud-delivery-bridge.yml` on `master`. The dispatcher itself has no `contents: write` permission and cannot apply a patch, commit, push, merge, delete a branch, alter status/readiness, or modify product/domain state.

A comment is eligible only when all of the following hold:

- it belongs to an existing pull request;
- event action is `created`;
- author is the repository `OWNER`, or the exact `chatgpt-codex-connector[bot]` login with GitHub user type `Bot`;
- `<!-- jarvis-codex-result-delivery:v1 -->` occurs exactly once;
- `<!-- jarvis-cloud-delivery:v1 -->` occurs exactly once;
- the complete comment body is bound by SHA-256 and comment ID before downstream dispatch.

The downstream cloud-delivery bridge remains the only repository-write authority in this path. It must re-fetch the immutable comment, verify its digest, require an open same-repository PR and exact current PR head, parse the payload as untrusted data, enforce safe changed paths and a fixed validation profile, apply the patch against the exact base, rerun validation, revalidate CAS, then guarded-push only the existing non-default PR branch.

## Preserved hard boundaries

This authority grants no push to `master`, automerge, force-push, branch deletion, credential exposure to Codex, direct GitHub token in the Codex sandbox, workflow/control-path mutation through the payload, secret/env/key mutation, Coordination Bus V2 authority, readiness/STATUS authority, or product/domain commit authority.

`JARVIS_COORD_V2`, `WORKPACK`, and `CANDIDATE_PATCH` remain non-authoritative proposal material. The AE004 exception does not suppress the separate V2-to-mutation check. Any other automatic `issue_comment` workflow remains a failing AE004 finding unless separately and explicitly authorized by a future maintainer architecture amendment.

## Failure semantics

A Codex task-local commit, summary, or claimed test result is not delivery evidence. A delegated Codex implementation/repair is durable only when either the existing remote PR branch advances, or Codex emits the exact machine-applicable result payload described in the runbook and the trusted bridge materializes it. Invalid, stale, oversized, mixed-profile, unsafe-path, malformed, duplicate-marker, unauthorized-actor, or failed-validation payloads fail closed.

No automatic retry may weaken admission. Builders may immediately fall back to builder-native materialization from canonical remote truth.

## Evidence required

Acceptance requires deterministic tests proving actor/marker/event admission, immutable digest binding, exact AE004 exception identity, continued rejection of a second `issue_comment` workflow, continued rejection of V2-to-mutation even inside the admitted workflow, and unchanged cloud-delivery CAS/path/profile boundaries. CI/review remain authoritative after any materialized Codex change; human/maintainer merge authority is unchanged.
