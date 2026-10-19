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
   - `gh pr create`: `gh pr list --head`. Only an open PR counts, since a merged one may be an older PR from a reused branch name.
   - `Edit`/`Write`: the file content.
   A command is probed only when its single effectful step is the probed operation. The agent's working directory persists across calls, so `HEAD`, the upstream and the current branch are resolved only in an absolute directory the command itself names (`cd /abs`, `git -C /abs`). A named local branch is the same in every worktree. Tags and other non-branch refs, and `gh pr merge` without an explicit PR, are not probed.
3. **Bounded read-only diagnostic run.** For what the probes cannot settle, the supervisor runs a diagnosis with `codex exec --sandbox read-only` (see Enforced read-only below), not through Relay's headless runner, which cannot select a sandbox. The prompt carries a nonce, the operations by tool-call id, and a sanitized evidence bundle the supervisor collected read-only: worktrees, status, branches with upstream tracking, recent commits, remote heads, recent PRs and worker lanes. The transcript goes to `<control>/diagnostics/<nonce>/turns/turn-001/` in Relay's turn layout, so the spec 195 classifier reads it unchanged. It never becomes a Relay session or the chain head. There are at most `reconcile_attempts` (2) runs per turn, each bounded by `reconcile_timeout` (45 min), after which its process group is terminated.
3a. **Durable provider wait.** Codex runs a diagnosis when it is not cooling down, has no pending retry, and no fresh limits reading shows it out of quota. An unconfirmed (stale or missing) reading does not block it: Relay refreshes Codex's reading only when Codex runs, so on an idle host the reading stays stale indefinitely (found commissioning on the workstation, 2026-10-19). A diagnosis lost to quota uses no attempt, takes its cooldown from Codex's own message, and is bounded by the provider-failure limit. Otherwise the supervisor waits in the `waiting` phase and launches nothing:
   - until Codex's reliable reset (a fresh limits reading, or the provider's own message), when one is known;
   - otherwise for a bounded `recheck` (30 min).
   The wait sleeps in interruptible chunks against the clock, with no busy polling. It is persisted (`waiting_since`, `wake_at`) and bounded by `max_wait` (8 days) in total across restarts, after which it holds `wait_exceeded`. A diagnosis that ends in Codex quota records Codex's cooldown and is retried after the reset. One that ends in a transient outage is retried after exponential backoff. Neither uses up a diagnostic attempt; these provider-lost runs are bounded separately (`reconcile_provider_failures`, 6). A Codex spend cap with no reset (`no_provider_available`) and a Codex authentication failure (`auth_failure`) hold, because raising spend and renewing credentials are the operator's decisions. A failed turn's own quota is recorded as that agent's cooldown when reconciliation starts.
4. **Deterministic promotion.** A diagnosis counts only when all of the following hold:
   - the run is a `success`;
   - every tool call it made classifies `read_only` under the spec 195 classifier;
   - the repository fingerprint is unchanged;
   - its reply ends in exactly one well-formed `RECONCILE-VERDICT` line for its own nonce.
   These checks remain as defence in depth behind the sandbox. If it made any other call, or changed the repository, the diagnosis is void and the chain holds with `reconcile_failed`. A model verdict of `completed` is admitted: it only prevents a repeat. A model verdict of `not_started` is admitted only for local operations. For `external` and `unknown` operations it becomes `unresolved`, because a duplicate merge, comment or remote trigger cannot be taken back. A `running` verdict waits `reconcile_poll` and is re-diagnosed within the attempt bound.
5. **Result.**
   - Every operation `completed` or `not_started`: an auditable `reconcile` journal record (per operation: verdict, evidence, source), a control-ledger decision, a `reconciled` notice, and continuation. The recovery prompt lists each operation with its verdict.
   - Otherwise a hold with an explicit reason: `reconcile_unresolved`, `reconcile_insufficient_permissions`, `reconcile_failed`, `reconcile_no_sandbox`, `live_work`, `wait_exceeded`, `no_provider_available` or `auth_failure`.
   These are gate holds: `release` waives the gate exactly as for `effects_uncertain`.

### Safety and restart

- The diagnostic's intent (nonce, agent, operations, fingerprint) is written to `state.reconcile.diag` and the attempt journal before launch, and its transcript directory is created by nonce exactly once. On restart, a live diagnostic is waited for and adopted: by pid plus start time, or, if the supervisor died before recording the pid, by finding the process whose `-o` path names the nonce. A dead one is read from its nonce directory. If its transcript cannot be found, the hold is `attempt_unresolved`: without a transcript nothing shows it stayed read-only. A second diagnostic is never launched while one is unsettled. The spec 195 single-instance lock still applies.
- An existing `effects_uncertain` hold is re-examined on the next `run` of the held chain's own head session, for exactly the held turn. If the chain has moved, the hold stays and is marked not re-examinable. Re-examining a hold that remains unchanged is neither re-announced nor counted as a new failure. No other hold reason is ever cleared automatically, and holds reached by reconciliation are not re-examined.
- The state additions (`reconcile`, `diagnostics`) are optional, so state written by spec 195 still loads. Malformed additions are `state_corrupt`.
- `run --no-reconcile` restores the spec 195 behaviour. `Supervisor(reconcile=False)` is the library default, so spec 195 tests keep their exact semantics.

### Enforced read-only (before execution)

The diagnosis runs as:

`codex exec --sandbox read-only --ignore-user-config --ignore-rules --ephemeral --json --color never -c approval_policy="never" -c mcp_servers={} -C <repo> -o <dir>/last-message.txt -`

- **The sandbox.** `--sandbox read-only` is Codex's own operating-system sandbox. On Linux, every command the model runs gets read-only mounts and no network. Verified with Codex 0.163: a write anywhere, `/tmp` included, fails with `Read-only file system`, and outbound connections fail.
- **Approvals.** `approval_policy="never"` means nothing is escalated out of the sandbox.
- **What is not loaded.** `--ignore-user-config` drops user MCP servers (which run outside the sandbox), profiles, hooks and sandbox overrides; authentication still loads. `-c mcp_servers={}` also drops any project MCP servers. `--ignore-rules` drops execpolicy allow rules.
- **No authority-widening flags.** None are passed: no `--dangerously-*`, `--full-auto`, `--approve-for-me` or `--add-dir`.
- **Preflight canary.** Before every diagnosis the supervisor checks that this host's Codex has the required flags. It then runs `codex sandbox -c sandbox_mode="read-only"` with a script that must read the repository and must fail to create a canary file. If the canary appears, the read fails, Codex is missing, or the check errors, no diagnosis runs and the chain holds with `reconcile_no_sandbox`. Nothing falls back to an unsandboxed run.
- **Claude.** Claude is never the diagnostic agent: Relay's headless Claude can carry `[agent.allow]` grants, and there is no equivalent verified sandbox.

### Residual limits

- **The Codex process itself is not sandboxed.** The sandbox confines the commands the model runs. File edits through Codex's own patch tool are refused by the read-only policy inside the Codex process, not by the kernel. The model API connection, and Codex's own web search if the service enables it, are outside the sandbox; both are reads. The post-run checks (any `file_change` or non-read-only call, any repository change) still void such a run.
- **The canary is one check.** It runs `codex sandbox`, which uses the same sandbox implementation as `codex exec` but is a separate invocation. Network isolation was verified on the reference host, not by the per-run canary.
- **No network inside.** Remote state comes from the supervisor's own probes and evidence bundle.
- **Wait across reboots.** A wait survives a supervisor restart, but only a running supervisor wakes up. The runbook gives a systemd user unit so that a reboot restarts it.

### Authority

Probes and evidence collection use only reads, with the operator's existing git/gh configuration. `git fetch` is excluded because it moves local refs. The diagnosis uses the operator's existing Codex login and has strictly less authority than Relay's headless Codex. A refusal inside the sandbox is reported (`insufficient_permissions`) and holds, never worked around. A diagnosis grants no authority, and the continuation's authority is exactly spec 195's: it still runs through Relay's unchanged headless runner.

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
- Codex quota during reconciliation: the supervisor waits for the reported reset and then diagnoses once. A diagnosis lost to quota is retried after the reset without using an attempt. A restart during the wait resumes it without a duplicate. Unconfirmed availability is rechecked in bounded waits, then held. Spend cap and authentication failures hold.
- No diagnosis runs without a verified read-only sandbox. The launch command enforces the sandbox flags. The preflight refuses a sandbox that lets a write through, and the real-host test passes against Codex 0.163.
- Insufficient permissions from a probe or the diagnosis hold with `reconcile_insufficient_permissions`.
- A diagnosis that writes, or that changes the fingerprint, is void (`reconcile_failed`). Malformed verdicts are retried within the bound, then held.
- An existing `effects_uncertain` hold is re-examined only for its exact turn. Other holds are untouched.
- The spec 195 suite passes unchanged, and probes and evidence are read-only and secret-filtered.

Workstation verification is in the runbook section "Incident reconciliation (spec 197)".
