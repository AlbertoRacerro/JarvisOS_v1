# 020 — pipeline-doctor: deterministic review-pipeline watchdog

Status: ready
Depends on: 017, 019

## Goal

The review pipeline can fail in ways that look like success (green run, no
comment; approval verdict, no label; fix request posted, no actuation). A
scheduled, fully deterministic watchdog checks the pipeline's invariants and
makes every silent failure loud. No LLM calls: this is the part of the system
that must never be probabilistic.

## Why

Every failure mode observed live in 2026-07-06/07 — stale-script runs billed
for nothing, verdicts posted but mis-parsed, labels missing after approval,
@codex mentions that never produced commits — was invisible until a human
went looking. Each would have been a one-line alert under these checks.

## Scope

In scope:
- `scripts/pipeline_doctor.py` (stdlib only, same conventions as
  `scripts/cheap_review.py`: env-driven, `--self-test` flag, GITHUB_TOKEN).
- `.github/workflows/pipeline-doctor.yml`: `schedule` (cron, twice daily) +
  `workflow_dispatch` for manual runs.
- The doctor examines the last 48h (env-tunable `DOCTOR_WINDOW_HOURS`) of
  review activity and checks, for every open non-draft PR:
  1. **Run→comment integrity:** every completed `cheap-review.yml` /
     `senior-review.yml` run with conclusion `success` has the matching sticky
     comment (`cheap-review:deepseek` / `cheap-review:glm`) created or updated
     at/after the run's start time.
  2. **Approval→label integrity:** a cheap-tier `NO_FURTHER_CHANGES` on the
     PR's current head has the `frontier-review` label present OR a senior run
     that started afterwards; a senior `NO_FURTHER_CHANGES`/LGTM on the current
     head has `ready-for-merge` present.
  3. **Actuation liveness:** a `codex-fix-request` sticky comment older than
     `DOCTOR_STUCK_HOURS` (default 12) with no commit pushed to the PR branch
     after its last update -> "actuator stuck" finding.
  4. **Failed runs:** any review-workflow run with conclusion `failure` or
     `cancelled` in the window is listed with its error line
     (`gh run view --log-failed` equivalent via the API is NOT required; the
     run URL and conclusion are enough).
  5. **Stale-branch guard:** PR branches whose `.github/workflows/senior-review.yml`
     or `cheap-review.yml` differ from master's version -> warning (their
     label-triggered workflow YAML is outdated; the script itself is already
     pinned to master by spec 019 follow-up).
  6. **Round-limit strandings:** sticky comments showing the round limit
     reached, listed for the maintainer.
- Output: ONE sticky issue titled "Pipeline doctor report" (find by marker
  `<!-- pipeline-doctor -->` in the body, create with label `pipeline-alert`
  if missing, update in place otherwise). Body: one section per check, only
  violations listed, timestamp, and a final PASS/FAIL banner. The workflow
  exits non-zero when any check 1-3 fails (visible red run), zero otherwise.
- Maintainer setup note: create the `pipeline-alert` label (any color).

Out of scope (binding non-goals):
- No LLM/provider calls of any kind; GitHub API only.
- No remediation actions: the doctor never adds/removes labels, never
  comments on PRs, never re-triggers workflows, never mentions @codex. It
  reports; humans and the existing pipeline act.
- No changes to `scripts/cheap_review.py` or the review workflows.
- No new dependencies (stdlib only).

## Files likely touched

- `scripts/pipeline_doctor.py` (new)
- `.github/workflows/pipeline-doctor.yml` (new)

Note: if the execution environment cannot push workflow files (`workflow`
scope), stop and report per the standard conflict rule.

## Acceptance criteria

1. A senior/cheap run that succeeded without its sticky comment being
   created/updated is reported as a check-1 violation.
2. An approval verdict on the current head without its expected label (and,
   for cheap, without a subsequent senior run) is reported as a check-2
   violation.
3. A `codex-fix-request` comment older than the threshold with no later push
   on the branch is reported as "actuator stuck".
4. Failed/cancelled review runs in the window appear in the report with URLs.
5. The report is a single sticky issue updated in place; a healthy window
   produces a PASS banner and a green run.
6. `python scripts/pipeline_doctor.py --self-test` passes offline (pure
   helpers: window math, verdict extraction from comment bodies, marker
   matching, report assembly); ruff clean; workflow YAML parses.

## Residual risks

- GitHub API pagination/rate limits on busy windows: cap examined PRs/runs
  (env-tunable) and state truncation in the report rather than failing.
- The doctor shares the sticky-comment marker conventions with
  `cheap_review.py`; if those markers change, the doctor's parsers must
  change with them (single source of truth note added at both definition
  sites).
