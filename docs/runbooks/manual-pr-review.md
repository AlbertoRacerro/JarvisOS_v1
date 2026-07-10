# Manual external PR review

External model reviews are optional and run only after an explicit maintainer
action. Routine pull requests rely on deterministic CI plus maintainer review.

## Cheap or senior review

1. Open the repository **Actions** tab.
2. Select **Manual Cheap Review** or **Manual Senior Review**.
3. Choose the `master` branch.
4. Select **Run workflow** and enter the open pull request number.

The workflow checks out the requested PR head for its diff and referenced spec,
but replaces `AGENTS.md` and all executable reviewer scripts with the trusted
copies from `master` before accessing provider secrets.

The review posts one advisory PR comment. It does not:

- apply or remove `frontier-review`, `expert-review`, or `ready-for-merge`;
- trigger another review tier;
- mention or dispatch Codex;
- push commits or merge;
- make deterministic CI optional.

A newer push during the API call marks the resulting comment stale.

## Expert review

Apply the `expert-review` label manually to a non-draft PR. The Claude workflow
posts an advisory review only. It does not request an automated fix or apply a
readiness label.

## Cost boundary

No DeepSeek, GLM, or Claude review API call occurs merely because a PR is opened,
updated, or marked ready for review. Provider keys remain stored as repository
secrets but are read only during the corresponding explicit manual action.

`REVIEW_BOT_TOKEN` is no longer used by these workflows and may be removed from
repository Actions secrets after this policy change is merged.

## Merge authority

A clean model review is not an approval. Merge readiness requires:

1. the current PR head to pass deterministic required checks;
2. the spec and hard invariants to remain satisfied;
3. the human maintainer to decide to merge.
