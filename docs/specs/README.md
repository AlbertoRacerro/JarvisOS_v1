# Work-item specs

Each file `NNN-<slug>.md` is one implementation slice, sized for a single agent
session and a single reviewable diff. Specs are written by the maintainer (with
strategic-review support) and executed by AI coding agents.

The live status and roadmap are maintained only in [`STATUS.md`](STATUS.md).
Individual spec files define scope, acceptance criteria, tests, and non-goals;
legacy `Status:` lines inside those files are not authoritative.

## Execution workflow

1. Read [`STATUS.md`](STATUS.md). Pick a `ready` spec only after confirming all
   hard dependencies are `merged` and no active PR overlaps the same files or
   runtime boundary.
2. Read the selected spec fully, then create a branch: `spec/NNN-<slug>`.
3. Set the registry row to `in_progress` when implementation starts.
4. **Verify the "Files likely touched" list against the actual code before
   writing anything** — specs are written from docs-level knowledge and may be
   slightly stale. If reality conflicts with the spec, stop and report.
5. Implement within scope. Non-goals are binding.
6. Run the test gate in `AGENTS.md`.
7. Open one PR, set the registry row to `in_review`, add the PR number, and note
   deviations or discoveries in the PR summary or an `## Implementation notes`
   section in the spec when needed.
8. The merge owner changes the registry row to `merged` immediately after merge.

Review is human-controlled and supported by automated review. A spec is merged
only when its implementation PR is incorporated into `master`; model verdicts or
passing self-authored tests do not change status by themselves.

## Status values

- `planned`
- `blocked`
- `ready`
- `in_progress`
- `in_review`
- `merged`
- `cancelled`

Definitions and update rules live in [`STATUS.md`](STATUS.md). Do not recreate a
second live index in this file, the root README, strategy documents, chat
handoffs, or individual specs.
