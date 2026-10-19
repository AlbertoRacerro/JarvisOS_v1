# 197 — Relay incident reconciliation

State: **ready**. Combined definition, full contract and readiness, authorized by the maintainer's 2026-10-19 directive: routine diagnostics, maintenance and recovery of ordinary recoverable continuity holds are software responsibilities, not operator work. It amends the spec 195 side-effect gate and leaves every other spec 195 contract unchanged. It does not overlap the proposed spec 196 (REPL keeper): it adds no terminal control of any kind.

## Problem

Spec 195 holds the chain (`effects_uncertain`) as soon as the failed turn shows a non-read-only operation without a settled result, and only a maintainer `release` resumes it. On 2026-10-18 session `20261018-215555-4f193a`, turn-006 ended in Claude quota exhaustion. The supervisor classified it `quota` but held with `effects_uncertain` instead of failing over to Codex. Most such holds are settled by reading evidence that already exists: whether the remote branch has the pushed commit, whether the PR is merged, whether the edit is in the file, whether the background worker is still running. Asking the maintainer to do that reading is routine maintenance pushed onto the operator.

## Outcome

1. An uncertain operation is classified from evidence as `completed`, `running`, `not_started` or genuinely `unresolved`. A needed check that is refused is reported as `insufficient_permissions`.
2. When every uncertain operation is settled, the chain continues under the unchanged spec 195 policy, including Claude-to-Codex failover. Completed operations are reported to the successor as done and are never replayed. Operations that did not start are named as such.
3. Running work is waited for (adopted), never duplicated.
4. A genuinely unresolved or irreversible ambiguity still holds for the maintainer.

## Mechanism

Reconciliation runs only where spec 195 would hold with `effects_uncertain` for recorded in-flight operations, with a terminal event or an unchanged repository fingerprint. The truncated-stream-with-changed-repository case still holds directly, because unrecorded writes cannot be enumerated.

1. **Await running work.** The spec 195 live-work check is polled. Work of the chain still running in a checkout or container is waited for, never relaunched, within `reconcile_wait` (3 h, counted from the start of reconciliation across restarts). Past the bound, or on a failed inspection, the hold is `live_work`.
2. **Deterministic probes.** The supervisor itself runs read-only checks:
   - `git push` of one branch: `rev-parse`, `ls-remote`, `merge-base --is-ancestor`. If the remote is at the local commit, the push is `completed`. If the remote is absent or behind, it is `not_started` (a push is idempotent). A forced, multi-ref or dynamic push is not probed.
   - `gh pr merge`: `gh pr view`. `MERGED` is `completed`; `OPEN` is `not_started`, unless `--auto` was used.
   - `gh pr create`: `gh pr list --head`.
   - `Edit`/`Write`: the file content.
   A command is probed only when its single effectful step is the probed operation.
3. **Bounded diagnostic run.** For what the probes cannot settle, the supervisor dispatches a read-only diagnostic through Relay's headless runner (`run --continue <head> -n 1`). Codex runs it when a fresh limits reading confirms room. Otherwise the failed agent runs it, unless that agent is out of quota or cooling down. The prompt carries a nonce, the operations by tool-call id, and a sanitized evidence bundle the supervisor collected read-only: worktrees, status, branches with upstream tracking, recent commits, remote heads, recent PRs and worker lanes. The diagnostic session never becomes the chain head. There are at most `reconcile_attempts` (2) runs per turn, each bounded by `reconcile_timeout` (45 min), after which its process group is terminated.
4. **Deterministic promotion.** A diagnosis counts only when all of the following hold:
   - the run is a `success`;
   - every tool call it made classifies `read_only` under the spec 195 classifier;
   - the repository fingerprint is unchanged;
   - its reply ends in exactly one well-formed `RECONCILE-VERDICT` line for its own nonce.
   If it made any other call, or changed the repository, the diagnosis is void and the chain holds with `reconcile_failed`. A model verdict of `completed` is admitted: it only prevents a repeat. A model verdict of `not_started` is admitted only for local operations. For `external` and `unknown` operations it becomes `unresolved`, because a duplicate merge, comment or remote trigger cannot be taken back. A `running` verdict waits `reconcile_poll` and is re-diagnosed within the attempt bound.
5. **Result.**
   - Every operation `completed` or `not_started`: an auditable `reconcile` journal record (per operation: verdict, evidence, source), a control-ledger decision, a `reconciled` notice, and continuation. The recovery prompt lists each operation with its verdict.
   - Otherwise a hold with an explicit reason: `reconcile_unresolved`, `reconcile_insufficient_permissions`, `reconcile_failed`, `live_work`, or `effects_uncertain` when no provider can run a diagnosis.
   These are gate holds: `release` waives the gate exactly as for `effects_uncertain`.

### Safety and restart

- The diagnostic's intent (nonce, agent, operations, fingerprint) is written to `state.reconcile.diag` and the attempt journal before launch. On restart, a live diagnostic (pid plus start time) is waited for and adopted, and a dead one is located by nonce. If its session cannot be identified, the hold is `attempt_unresolved`: without a transcript nothing shows it stayed read-only. A second diagnostic is never launched while one is unsettled. The spec 195 single-instance lock still applies.
- An existing `effects_uncertain` hold is re-examined on the next `run`, for exactly the held turn. If the chain has moved, the hold stays. No other hold reason is ever cleared automatically, and holds reached by reconciliation are not re-examined.
- The state additions (`reconcile`, `diagnostics`) are optional, so state written by spec 195 still loads. Malformed additions are `state_corrupt`.
- `run --no-reconcile` restores the spec 195 behaviour. `Supervisor(reconcile=False)` is the library default, so spec 195 tests keep their exact semantics.

### Authority

Probes and evidence collection use only reads, with the operator's existing git/gh configuration. `git fetch` is excluded because it moves local refs. The diagnostic runs with Relay's unchanged headless authority:
- Claude headless uses `--permission-mode default` and Relay's approval hook, so commands that need approval are refused.
- Codex uses Relay's headless sandbox, which may block network.
The supervisor passes no permission, sandbox or model flags and never works around a refusal. A refusal is reported (`insufficient_permissions`) and holds. A diagnosis grants no authority, and the continuation's authority is exactly spec 195's.

## Non-goals

- No terminal keystroke injection, REPL control or tmux driving (spec 196 territory).
- No blanket hold release, no new credentials, no permission, sandbox or security-check change, and no Relay modification.
- No automatic resolution of external effects from model judgement alone.
- No repair actions: reconciliation only reads. Doing the work remains the continuation's job under its normal authority.

## Acceptance (offline, injected Relay, probes, clock and process table)

- Claude quota with a probe-settled push hands off to Codex; the push is listed as completed.
- An interrupted completed operation is settled by a Codex diagnosis and not repeated.
- A running background worker is awaited; nothing launches while it runs; past the bound it holds.
- An unstarted merge (PR open) is resumed and named as not started.
- An ambiguous external effect (a PR comment) stays held even when the model says `not_started`.
- A supervisor restart during a diagnosis adopts it (no duplicate). A lost diagnosis holds. One past its time bound is terminated.
- Insufficient permissions from a probe or the diagnosis hold with `reconcile_insufficient_permissions`.
- A diagnosis that writes, or that changes the fingerprint, is void (`reconcile_failed`). Malformed verdicts are retried within the bound, then held.
- An existing `effects_uncertain` hold is re-examined only for its exact turn. Other holds are untouched.
- The spec 195 suite passes unchanged, and probes and evidence are read-only and secret-filtered.

Workstation verification is in the runbook section "Incident reconciliation (spec 197)".
