# Narrow post-merge STATUS reconciler

Status: activation-ready repository plumbing; no merge or roadmap authority.

This V3.2 throughput component creates a normal reviewable pull request for the single mechanical `docs/specs/STATUS.md` transition `in_review -> merged` after a qualifying merged implementation PR. It never pushes `master`, merges a PR, changes dependencies or queue order, infers a different spec state, edits another canonical surface, or bypasses branch protection/rulesets.

## Activation

Repository code is inert for implementation PRs until the Actions secret `JARVIS_RECONCILER_TOKEN` exists. The remaining human-controlled step is to install/provision a narrow GitHub App installation token or fine-grained repository token and store it under that exact secret name.

Minimum required repository permissions for that credential:

- Contents: read and write, solely to create/update the deterministic reconciliation branch;
- Pull requests: read and write, solely to inspect the merged implementation PR and create the reconciliation PR;
- Metadata: read as implied by GitHub.

Do **not** grant Administration, ruleset/branch-protection bypass, Actions write, Secrets write, or merge authority. The workflow's own `GITHUB_TOKEN` remains read-only; all mutation is explicit through the separately provisioned narrow credential.

## Fail-closed behavior

The workflow acts only on a merged PR whose base is `master` and whose body contains an exact `**Spec gate:** implementation NNN` declaration. It re-reads fresh `master`, requires exactly one matching STATUS row already associated with that implementation PR and still in `in_review`, and changes only that token to `merged`. Already-reconciled state is an idempotent no-op. Missing/ambiguous/moved state fails without semantic inference.

The branch name is deterministic from spec, merged PR and merge SHA. A retry reuses only identical branch content and refuses unexpected branch drift. The resulting PR uses the normal repository gates and remains subject to ordinary review/merge rules.
