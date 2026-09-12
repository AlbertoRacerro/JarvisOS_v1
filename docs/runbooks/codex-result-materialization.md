# Codex result materialization

This runbook closes the gap between a Codex Cloud task-local commit and the authoritative GitHub PR branch without giving the Codex sandbox repository credentials.

## Operating rule

Remote GitHub state is authoritative. A Codex summary or task-local commit is advisory until the existing PR branch advances.

For bounded single-profile implementation or repair tasks, request Codex to push to the existing PR branch when its environment supports that safely. If `git remote`/push is unavailable, Codex must export an exact delivery payload in its final PR comment instead of reporting only a local commit.

The final comment must contain both markers exactly once:

```text
<!-- jarvis-codex-result-delivery:v1 -->
<!-- jarvis-cloud-delivery:v1 -->
```

followed by the existing cloud-delivery v1 JSON metadata fence and exact unified diff fence. The payload must satisfy `scripts/cloud_delivery_bridge.py`: same-repository open PR, exact current head as `base_sha`, non-default `target_ref`, sorted unique safe `changed_paths`, admitted validation profile, exact SHA-256 of the diff bytes, no protected/control/secret paths, and the bridge's bounded size/path limits.

Recommended Codex task instruction:

```text
Work only on the existing PR branch and accepted scope. Push the finished commit to that branch if the environment provides a safe configured remote. Never push master, force-push, merge, delete branches, or modify secrets/credentials.

Before editing, record the exact checkout HEAD as BASE_SHA. If push is unavailable, do not stop at a local commit. In your final PR response export a machine-applicable fallback:
1. include exactly once `<!-- jarvis-codex-result-delivery:v1 -->`;
2. include exactly once `<!-- jarvis-cloud-delivery:v1 -->`;
3. emit the complete cloud-delivery v1 JSON metadata bound to this PR, BASE_SHA and existing PR head branch;
4. generate an exact `git diff --binary --no-renames BASE_SHA..HEAD` for only the changed files, keep changed_paths sorted, compute patch_sha256 from the exact emitted diff bytes, and place those exact bytes in the diff fence;
5. choose only the admitted fixed validation profile (`backend`, `frontend`, or `docs`).
A task-local commit without either a remote branch advance or this exact payload is incomplete delivery.
```

## Automatic path

When a newly created PR comment carrying the Codex-specific marker is authored either by the repository OWNER or by the exact GitHub actor `chatgpt-codex-connector[bot]`, `.github/workflows/codex-result-delivery.yml` binds the immutable comment ID and full-body SHA-256, then dispatches the existing `cloud-delivery-bridge.yml` on trusted `master`.

The dispatcher itself cannot apply code. The downstream bridge re-fetches the comment, checks the exact body digest, binds it to the open same-repository PR and exact remote head, parses the untrusted patch, rejects stale/unsafe/control paths, runs the fixed validation profile, and only then performs the existing guarded CAS push. CI/review/proof remain authoritative after materialization.

## Boundaries

- No Codex GitHub token or repository credential is exposed.
- No push to `master`, automerge, force-push, branch deletion, or direct merge authority.
- Only newly created PR comments from the OWNER or exact allowlisted `chatgpt-codex-connector[bot]` actor, carrying both explicit markers, can auto-dispatch. No wildcard bot trust exists.
- Existing manual `jarvis-cloud-delivery:v1` payloads do not auto-dispatch unless the Codex-specific marker is also present.
- The fallback is intentionally bounded to one bridge validation profile and current bridge size/path limits. Mixed frontend/backend or oversized work must be split into sequential bounded tasks after each remote head advance, or materialized builder-native.
- If Codex cannot produce a valid payload, builders immediately reconstruct/materialize from canonical remote truth rather than waiting on the sandbox artifact.

## Why not loosen the sandbox

The supported GitHub Action path for running Codex directly in a repository checkout requires a separate provider API key. JarvisOS keeps the zero-extra-cost default and avoids adding a high-value model credential to GitHub Actions merely to solve transport. The trusted-controller pattern gives Codex a durable output channel while preserving credential isolation and the existing post-write CI/review boundaries.
