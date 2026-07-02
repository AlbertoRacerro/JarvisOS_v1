# 004 — Tiered PR review: DeepSeek iteration loop, frontier review only pre-merge

Status: ready
Depends on: none (pure CI/workflow infra; no backend or frontend code)

## Goal

Every push to a PR is reviewed by a cheap external model (DeepSeek) that drives
the fix iteration loop with the implementing agent. The existing Claude (frontier)
review no longer runs on every push: it runs once, on the stabilized diff, when
the cheap tier reports no remaining MAJOR/CRITICAL findings (or when the
maintainer requests it explicitly). Frontier review cost per PR drops from N
rounds to ~1.

## Why

Two Claude review rounds on one PR consumed ~40% of the maintainer's daily
frontier budget. This is ADR-057 applied to the development loop itself: cheap
external as workhorse, frontier as final gate. Review authority is unchanged
(see `AGENTS.md` "Review authority"): the cheap tier's verdict is a trigger,
never an approval.

## Scope

In scope:
- A new workflow `.github/workflows/deepseek-review.yml` triggered on
  `pull_request` (`opened`, `synchronize`, `ready_for_review`), skipping drafts,
  with per-PR concurrency (mirror the existing `claude-review.yml` structure).
- The workflow calls the DeepSeek chat-completions API directly (curl or a small
  Python script in `scripts/`; no new SDK dependency) with a **scoped pack**:
  the PR diff, the referenced spec file (`docs/specs/NNN-*.md`, resolved from
  branch name/PR title/body), and the "Hard invariants" section of `AGENTS.md`.
  Not the whole repo.
- Review instructions to DeepSeek mirror the Claude prompt's substance rules:
  invariant violations → CRITICAL, spec conformance → MAJOR, correctness bugs
  with concrete failure scenario, missing/weak required tests. No style nits.
- Output: one sticky PR comment (updated in place, like the Claude review) with
  verdict `NEEDS_CHANGES` or `NO_FURTHER_CHANGES`, findings labeled
  CRITICAL/MAJOR/MINOR. If `NEEDS_CHANGES`, end with the same
  `@codex please fix ...` line the Claude workflow uses.
- **Round limit: 3.** The workflow counts its own previous sticky-comment
  revisions (or a round counter embedded in the comment). After round 3, post
  "ROUND LIMIT REACHED — maintainer decision needed" and stop mentioning @codex.
  Remaining MINOR findings are listed for the maintainer, not sent back to the
  agent.
- Gate the existing `claude-review.yml` so it no longer runs on every
  `synchronize`. Trigger it via a PR label (e.g. `frontier-review`): the
  DeepSeek workflow applies the label when its verdict is `NO_FURTHER_CHANGES`;
  the maintainer can also apply it manually at any time to force a frontier
  review. Remove the label on subsequent pushes so a stale approval cannot
  trigger frontier review of a changed diff.
- Secret: `DEEPSEEK_API_KEY` read from GitHub Actions secrets. The workflow must
  fail with a clear message (not silently skip) if the secret is missing.
- Fail-open on infrastructure errors: if the DeepSeek API call fails (network,
  5xx, malformed response), post a comment saying the cheap tier failed and that
  the maintainer can apply the `frontier-review` label manually. Do not block
  the PR.

Out of scope (binding non-goals):
- No changes to merge authority, branch protection, or auto-merge. The DeepSeek
  verdict never approves, merges, or dismisses reviews.
- No changes to backend/frontend code, the AI gateway, provider modules, or the
  in-app cost registry. This slice is repo CI infra only.
- No new Python dependencies in `backend/requirements*.txt`; a script under
  `scripts/` may use only the standard library.
- No secrets in logs: never echo the API key or full request headers; do not
  dump raw API responses to the workflow log beyond the extracted review text.
- No prompt-engineering iteration loops in this slice: one prompt, one call per
  push (plus at most one retry on transient failure).

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `.github/workflows/deepseek-review.yml` (new)
- `.github/workflows/claude-review.yml` (trigger change only: label-gated)
- `scripts/deepseek_review.py` (new, stdlib-only) — or inline curl if simpler

Note: if the execution environment cannot push workflow-file changes (GitHub
`workflow` scope restriction on the agent's token), stop and report per the
standard conflict rule; do not work around it.

## Design constraints

- Mirror the existing `claude-review.yml` conventions: sticky comment, per-PR
  concurrency group, draft skip, explicit `permissions` block (needs
  `pull-requests: write` and, for labeling, `issues: write`).
- The DeepSeek prompt must state that its review is advisory and that it must
  never claim approval/merge authority — same framing as the Claude prompt.
- The label name and round limit must be defined once (workflow env vars), not
  scattered.
- Model: `deepseek-chat` (current V4 endpoint); pin the model name in one env
  var so it is hand-editable.

## Acceptance criteria

1. Opening or pushing to a non-draft PR triggers the DeepSeek workflow and
   produces/updates exactly one sticky review comment with a verdict and
   labeled findings.
2. `claude-review.yml` does not run on `opened`/`synchronize` anymore; it runs
   when the `frontier-review` label is applied.
3. A `NO_FURTHER_CHANGES` DeepSeek verdict applies the `frontier-review` label;
   a subsequent push removes it.
4. After 3 DeepSeek rounds on the same PR, the comment states the round limit
   was reached and stops mentioning @codex.
5. A missing `DEEPSEEK_API_KEY` fails the workflow with an explicit message; a
   DeepSeek API error posts the fail-open comment instead of blocking.
6. No API key or raw auth header appears in any workflow log line.

## Required tests

CI workflows cannot run in the backend pytest suite. Required verification
instead:
- `python -m json.tool` / `yamllint`-equivalent validity: workflows parse
  (GitHub rejects invalid YAML on push — a dry parse locally is enough).
- If `scripts/deepseek_review.py` is created: unit-testable pure functions
  (pack assembly, spec-file resolution from branch name, round counting from
  comment body) get stdlib `unittest` or pytest tests under `backend/tests/`
  only if trivially importable without new deps; otherwise a `--self-test` flag
  on the script executed in the workflow. State in the summary which option was
  taken and why.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status updated,
summary written. First real PR after merge is the live smoke test: maintainer
observes one full DeepSeek round on it before trusting the label gate.
