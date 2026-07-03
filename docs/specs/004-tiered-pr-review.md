# 004 — Tiered PR review: cheap-tier iteration loop, frontier review only pre-merge

Status: implemented (pending review)
Depends on: none (pure CI/workflow infra; no backend or frontend code)

## Goal

Every push to a PR is reviewed by a cheap external model that drives the fix
iteration loop with the implementing agent. The cheap tier is **provider-agnostic
and configured by env var**; this slice ships support for two candidates —
GLM 5.2 (Zhipu) and DeepSeek V4 — and an A/B evaluation to pick which becomes the
default workhorse. The existing Claude (frontier) review no longer runs on every
push: it runs once, on the stabilized diff, when the cheap tier reports no
remaining MAJOR/CRITICAL findings (or when the maintainer requests it explicitly).
Frontier review cost per PR drops from N rounds to ~1.

## Why

Two Claude review rounds on one PR consumed ~40% of the maintainer's daily
frontier budget. This is ADR-057 applied to the development loop itself: cheap
external as workhorse, frontier as final gate. Review authority is unchanged
(see `AGENTS.md` "Review authority"): the cheap tier's verdict is a trigger,
never an approval. The model choice is settled by measured evidence (which cheap
model missed fewer of the findings Opus later raised), not by reputation — so the
workflow must support swapping the provider via config, and the initial rollout
runs both candidates on the same PRs to compare.

## Scope

In scope:
- A new workflow `.github/workflows/cheap-review.yml` triggered on
  `pull_request` (`opened`, `synchronize`, `ready_for_review`), skipping drafts,
  with per-PR concurrency (mirror the existing `claude-review.yml` structure).
- The workflow calls an **OpenAI-compatible chat-completions endpoint** (curl or
  a small Python script in `scripts/`; no new SDK dependency) with a **scoped
  pack**: the PR diff, the referenced spec file (`docs/specs/NNN-*.md`, resolved
  from branch name/PR title/body), and the "Hard invariants" section of
  `AGENTS.md`. Not the whole repo.
- **Provider is config-driven, not hardcoded.** Three env vars own it:
  `CHEAP_REVIEW_BASE_URL`, `CHEAP_REVIEW_MODEL`, and a secret
  `CHEAP_REVIEW_API_KEY`. Both GLM 5.2 and DeepSeek V4 expose OpenAI-compatible
  endpoints, so the same script serves either by changing these three values.
- **A/B evaluation mode:** the workflow supports running both candidates on the
  same PR via a matrix over a `providers` list (each entry = base_url + model +
  key secret name), posting one sticky comment per provider (distinct comment
  markers so they update independently). Default config after evaluation is a
  single provider; the matrix is how the first PRs are compared. Which of the two
  models is the eventual default is decided by the maintainer from the evaluation
  (see Acceptance), not fixed in this spec.
- Review instructions mirror the Claude prompt's substance rules:
  invariant violations → CRITICAL, spec conformance → MAJOR, correctness bugs
  with concrete failure scenario, missing/weak required tests. No style nits.
  The prompt is provider-neutral (no model-specific wording).
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
  cheap-review workflow applies the label when its verdict is
  `NO_FURTHER_CHANGES` (in A/B mode, only when *all* configured providers agree
  on `NO_FURTHER_CHANGES`); the maintainer can also apply it manually at any time
  to force a frontier review. Remove the label on subsequent pushes so a stale
  approval cannot trigger frontier review of a changed diff.
- Secret(s): each provider's API key is read from GitHub Actions secrets (e.g.
  `GLM_API_KEY`, `DEEPSEEK_API_KEY`). The workflow must fail with a clear message
  (not silently skip) if a configured provider's secret is missing.
- Fail-open on infrastructure errors: if a provider API call fails (network,
  5xx, malformed response), post a comment saying that provider's cheap tier
  failed and that the maintainer can apply the `frontier-review` label manually.
  Do not block the PR. In A/B mode, one provider failing does not suppress the
  other's comment.

Out of scope (binding non-goals):
- No changes to merge authority, branch protection, or auto-merge. The cheap-tier
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

- `.github/workflows/cheap-review.yml` (new)
- `.github/workflows/claude-review.yml` (trigger change only: label-gated)
- `scripts/cheap_review.py` (new, stdlib-only) — or inline curl if simpler

Note: if the execution environment cannot push workflow-file changes (GitHub
`workflow` scope restriction on the agent's token), stop and report per the
standard conflict rule; do not work around it.

## Design constraints

- Mirror the existing `claude-review.yml` conventions: sticky comment, per-PR
  concurrency group, draft skip, explicit `permissions` block (needs
  `pull-requests: write` and, for labeling, `issues: write`).
- The review prompt must state that its review is advisory and that it must
  never claim approval/merge authority — same framing as the Claude prompt.
- The label name and round limit must be defined once (workflow env vars), not
  scattered.
- Model/endpoint config lives in one place (matrix + env vars), hand-editable.
  Both candidates speak the OpenAI chat-completions shape; do not fork the script
  per provider. Model IDs and base URLs must be confirmed against each provider's
  current docs at implementation time (see maintainer note below), not hardcoded
  from memory.

## Acceptance criteria

1. Opening or pushing to a non-draft PR triggers the cheap-review workflow and
   produces/updates one sticky review comment **per configured provider** with a
   verdict and labeled findings.
2. `claude-review.yml` does not run on `opened`/`synchronize` anymore; it runs
   when the `frontier-review` label is applied.
3. `NO_FURTHER_CHANGES` from all configured providers applies the
   `frontier-review` label; a subsequent push removes it.
4. After 3 rounds on the same PR, each provider's comment states the round limit
   was reached and stops mentioning @codex.
5. A missing API key for a configured provider fails the workflow with an
   explicit message; a provider API error posts the fail-open comment instead of
   blocking.
6. No API key or raw auth header appears in any workflow log line.
7. **A/B evaluation (one-time, recorded in the PR discussion, not a code
   artifact):** GLM 5.2 and DeepSeek V4 both run on the first real Codex spec PR;
   the maintainer compares each cheap-tier finding set against what the frontier
   review then raises as CRITICAL/MAJOR, and records which model missed fewer.
   The chosen model becomes the single default provider in a follow-up config
   commit. This criterion is satisfied by the evaluation being *possible and run*
   (both comments present on one PR), not by a particular winner.

## Required tests

CI workflows cannot run in the backend pytest suite. Required verification
instead:
- `python -m json.tool` / `yamllint`-equivalent validity: workflows parse
  (GitHub rejects invalid YAML on push — a dry parse locally is enough).
- If `scripts/cheap_review.py` is created: unit-testable pure functions
  (pack assembly, spec-file resolution from branch name, round counting from
  comment body) get stdlib `unittest` or pytest tests under `backend/tests/`
  only if trivially importable without new deps; otherwise a `--self-test` flag
  on the script executed in the workflow. State in the summary which option was
  taken and why.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status updated,
summary written. First real PR after merge is the live smoke test: maintainer
observes one full cheap-tier round on it before trusting the label gate.

## Maintainer setup note (not implemented by the agent)

Secrets and provider endpoints are configured by the maintainer, not the coding
agent. Preferred access path is a single **EU-data-residency** gateway so both
candidates share one OpenAI-compatible base URL and (optionally) one key:

- **EUrouter** (`eurouter.ai`) — EU servers, zero retention, GDPR DPA; exposes
  GLM and DeepSeek V4 behind one OpenAI-compatible key. One `CHEAP_REVIEW_*`
  config, two `CHEAP_REVIEW_MODEL` values in the A/B matrix.
- **Nebius Token Factory** (`studio.nebius.com`, Amsterdam HQ, EU datacenters) —
  hosts both DeepSeek and GLM with an OpenAI-compatible API; alternative if
  EUrouter lacks the exact model revision wanted.
- Direct Z.ai / DeepSeek APIs work too but route to China (no EU residency) — use
  only if the EU gateways lack the model. Redaction rules still forbid sending
  workspace/project context to any external endpoint regardless of jurisdiction.

Confirm current model IDs and base URLs from the chosen provider's docs at
implementation time; do not hardcode them from this note.

## Implementation notes

Implemented directly by the maintainer with Fable (not via a Codex slice), since
it is CI infra the maintainer operates. Deviations from the spec, by maintainer
decision:

- **Single provider, not A/B.** The maintainer chose the **DeepSeek V4 direct
  API** (`https://api.deepseek.com`, model `deepseek-chat`) as the sole cheap
  tier, for cost — the EU-gateway and GLM/DeepSeek A/B were dropped. The script
  (`scripts/cheap_review.py`) stays provider-agnostic: `CHEAP_REVIEW_PROVIDER`,
  `CHEAP_REVIEW_BASE_URL`, `CHEAP_REVIEW_MODEL`, `CHEAP_REVIEW_API_KEY`. Adding
  GLM later = a second workflow env block or matrix entry, no code change. The
  A/B acceptance criterion (7) is therefore deferred, not met.
- Label re-trigger handled by remove-then-add on every run, so each approved push
  re-fires the frontier review's `labeled` event.
- Files: `scripts/cheap_review.py` (stdlib only), `.github/workflows/cheap-review.yml`
  (new), `.github/workflows/claude-review.yml` (trigger -> `labeled`, gated on the
  `frontier-review` label).
- Verification: `ast.parse` + ruff clean on the script; both workflow YAMLs parse.
  No pytest added — the script's GitHub/DeepSeek calls need live tokens; the pure
  helpers (spec resolution, invariant extraction, round parsing) are simple enough
  that a live first-PR smoke is the intended check.

Maintainer to do before first run: create the `DEEPSEEK_API_KEY` repo secret and
the `frontier-review` label (any color). First real PR is the live smoke test.

Hardening pass (2026-07-03, frontier review of this slice) — behavior deltas:

- Verdict parsing tolerates markdown decoration/preamble; a missing verdict line
  is treated as NEEDS_CHANGES and noted in the comment.
- GitHub API writes and comment listing are status-checked (fail loud instead of
  silently green); provider fail-open still posts the comment but exits non-zero
  so the failure is visible in the checks list.
- The `frontier-review` label is removed at the start of every run (before any
  step can fail), and only added back on an untruncated, within-limit
  NO_FURTHER_CHANGES. Truncated-diff reviews never auto-apply the label.
- Past the round limit the review still runs (cheap) and posts findings for the
  maintainer, without @codex mentions and without the label — previously the
  limit banner overwrote the last findings.
- One retry on transient provider errors (as this spec allowed); spec-number
  resolution is word-bounded and prefers explicit `spec-NNN` references; the
  prompt pack now includes the AGENTS.md Repo map / Conventions / What NOT to do
  sections it already told the model to enforce.
- `--self-test` flag (offline, pure helpers) added and run as a workflow step.
- Diff cap is env-tunable via `CHEAP_REVIEW_DIFF_CAP` (default unchanged, 60k).
