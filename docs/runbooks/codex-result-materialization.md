# Codex result materialization

Remote GitHub state is authoritative. A Codex task-local commit or summary is advisory until the existing pull-request branch advances.

For bounded implementation/repair work, ask Codex to push to the existing PR branch when its environment safely exposes that branch. If no safe Git remote exists, Codex must export a complete machine-applicable fallback in its final PR comment rather than stop at a local commit.

The fallback comment must contain exactly once:

```text
<!-- jarvis-codex-result-delivery:v1 -->
<!-- jarvis-cloud-delivery:v1 -->
```

followed by the existing cloud-delivery v1 JSON metadata and the exact unified diff. Metadata must bind the existing PR number, the pre-edit exact PR head as `base_sha`, the existing non-default `target_ref`, sorted unique `changed_paths`, an admitted fixed validation profile, and the SHA-256 of the exact emitted diff bytes.

Recommended Codex task instruction:

```text
Work only on the existing PR branch and accepted scope. Push the finished commit to that branch if the environment provides a safe configured remote. Never push master, force-push, merge, delete branches, or modify secrets/credentials.

Before editing, record the exact checkout HEAD as BASE_SHA. If push is unavailable, do not stop at a local commit. In your final PR response export a machine-applicable fallback:
1. include exactly once `<!-- jarvis-codex-result-delivery:v1 -->`;
2. include exactly once `<!-- jarvis-cloud-delivery:v1 -->`;
3. emit the complete cloud-delivery v1 JSON metadata bound to this PR, BASE_SHA and existing PR head branch;
4. generate the exact diff for BASE_SHA..HEAD, keep changed_paths sorted, compute patch_sha256 from the exact emitted diff bytes, and emit those exact bytes in the diff fence;
5. choose only an admitted fixed validation profile.
A task-local commit without either remote branch advancement or this exact payload is incomplete delivery.
```

## Automatic transport

The sole admitted automatic `issue_comment` authority is `.github/workflows/codex-result-delivery.yml`, under the explicit 2026-09-13 022/128 amendment. It accepts only a newly-created PR comment from the repository OWNER or exact `chatgpt-codex-connector[bot]` actor with GitHub type `Bot`, and only when both result markers are present. The local dispatcher then verifies exact marker multiplicity and binds the immutable comment ID plus complete-body SHA-256.

The dispatcher has read-only repository permissions plus `actions: write`; it cannot modify contents. Its only privileged action is dispatching `cloud-delivery-bridge.yml` on trusted `master` with the bound PR/comment/digest inputs.

The cloud-delivery bridge re-fetches the comment, checks the body digest, binds the payload to an open same-repository PR and exact current remote head, rejects unsafe/control/secret paths and stale heads, runs the fixed validation profile, and only then performs its existing guarded CAS push. CI/review/proof remain authoritative afterward.

## Boundaries and fallback

No GitHub credential is exposed to Codex. No push to `master`, automerge, force-push, branch deletion, workflow/control-file mutation through the payload, or secret/env/key mutation is admitted. Coordination Bus V2 markers remain non-authoritative and cannot use this exception.

If Codex cannot produce a valid payload, or the dispatcher/bridge refuses it, builders immediately reconstruct/materialize from canonical remote truth. They must not spend later scheduler turns waiting for an inaccessible sandbox commit.
