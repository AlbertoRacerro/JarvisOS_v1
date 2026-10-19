# Relay continuity supervisor: operational runbook (spec 195)

`scripts/relay_continuity.py` continues a Relay coordinator session chain after a failed turn, and sends sanitized Slack notices. It never modifies the repository, Relay's configuration, permissions or session journals. Durable state is under `~/jarvis-control/work/continuity/` (override it with `RELAY_CONTINUITY_DIR`).

## When to use it

Run the supervisor when you step away from an interactive Relay REPL session and want failures to be handled:

| Failure | What the supervisor does |
| --- | --- |
| Quota exhaustion | Switches Claude → Codex, then returns to Claude at a turn boundary once Claude's reset is confirmed. |
| DNS/API blips | Retries the same agent with bounded backoff. |
| Interrupted turns | Retries once, but only when no side effect is uncertain. |
| Uncertain side effects | Settles them from read-only evidence first (spec 197): waits for running work, probes Git/GitHub/files, runs a bounded read-only Codex diagnosis, and continues only when every operation is proven `completed` or `not_started`. |

After a successful turn the chain goes **idle** and waits for you. The supervisor never invents new work.

**Only one coordinator at a time.** The supervisor refuses to launch while a Relay REPL (or another `relay run`) is live in the same repository, or while the legacy autopilot scripts run. Close the REPL first, and start the supervisor outside it (for example in tmux).

## Commands

```bash
cd ~/src/JarvisOS_v1
S=$(ls -t .agent-relay/sessions | head -1)        # the session to supervise (normally the REPL's)

# Supervise: continue the chain if its last turn failed; exit idle on success.
tmux new -d -s relay-continuity "python3 scripts/relay_continuity.py run --session $S"

# Hand the chain a new maintainer task (runs on the preferred available agent):
python3 scripts/relay_continuity.py run --session $S --task-file /path/to/task.md

python3 scripts/relay_continuity.py status        # phase, head session, cooldowns, hold, counters
python3 scripts/relay_continuity.py stop          # graceful: exits at the next safe point, never kills a turn
python3 scripts/relay_continuity.py classify .agent-relay/sessions/$S/turns/turn-004   # one turn's outcome

# Notify-only monitor: REPL turn failures, master merges, a periodic digest. Safe alongside a REPL.
tmux new -d -s relay-watch "python3 scripts/relay_continuity.py watch --digest-hours 6"
python3 scripts/relay_continuity.py notify-test
```

Exit codes:

| Code | Meaning |
| --- | --- |
| 0 | Idle or stopped |
| 3 | Another supervisor, the legacy autopilot or a lock blocks the start |
| 4 | Held |
| 2 | Refused input (a secret pattern in a task or note) |

## Holds

A hold means automatic continuation was refused and needs your review. Slack shows `JarvisOS continuity HOLD` with a reason.

| Reason | Meaning and what to check |
| --- | --- |
| `reconcile_unresolved` | Spec 197 could not settle an operation from evidence. This is a genuine ambiguity, for example a PR comment that only a model says was not posted. `attempts.jsonl` has a `"event": "reconcile"` record with the verdict, evidence and source for each operation. |
| `reconcile_insufficient_permissions` | A check needed to settle an operation was refused: `gh`/`git ls-remote` authentication, Claude headless approval, or the Codex sandbox network. It was reported, not worked around. Fix the access or settle the operation by hand, then `release`. |
| `reconcile_failed` | The diagnostic run made a non-read-only call, changed the repository, or gave no valid verdict within two attempts. Its findings were discarded. Check what it did in its session (listed in `status` → `reconcile` / `diagnostics`). |
| `effects_uncertain` | Without reconciliation (`--no-reconcile`), or for a truncated turn after a repository change: the failed turn was interrupted during a non-read-only operation (push, merge, PR comment, file write, subagent, script), or while a background job it launched (a worker lane, a queue) was still running. Background jobs are the commonest cause: check the lane with `devctx.py lanes`. Check whether it took effect with `git log`/`gh pr view`/`python3 scripts/devctx.py recover`. |
| `reconcile_no_sandbox` | No diagnosis ran, because this host cannot prove Codex's read-only sandbox works: Codex is not installed or is too old, or its sandbox let a canary write through or could not run a command. The log names the cause. Install or upgrade Codex (`codex --version`, 0.163 verified), then `release` and run. |
| `live_work` | Something launched in this chain is still running in the repository or a worktree, or in a container: a dev server, a background test run, a worker lane, `docker compose up -d`, a program in a tmux pane. The log names the processes (names only). Continuing could overlap it. Let it finish or stop it, or confirm it is meant to keep running. A release acknowledges exactly what is live at that moment (a pane that later `exec`s something new, or a new `docker exec`, holds again). A failing check (`process table unreadable`, `docker check failed`) holds until it is repaired. |
| `output_unparseable` | The turn transcript is corrupt or torn. |
| `output_missing` | The turn left no output of its own: Relay's "No response captured" turns keep a copy of the previous turn's output, and the agent may still have worked. Check `git log`, `gh pr list`, `devctx.py recover` for what it did. |
| `attempt_unresolved` | A launched attempt left no identifiable Relay session, even if the repository looks unchanged (a merge or a PR comment leaves no local trace). Or a restart could not find it, or the journal records a launch the state does not account for. Establish what happened, then use `release --drop-pending`. |
| `auth_failure`, `unknown_failure` | Log in again, or fix the configuration (for example an invalid model). These never switch provider. |
| `crash_repeated`, `circuit_*` | Bounded retries, switches or attempts were exhausted. |
| `no_provider_available`, `wait_exceeded` | Both agents are capped without a known reset, or the wait exceeded 8 days. |
| `permissions_changed` | The authority-bearing parts of `.agent-relay/permissions.toml` changed. |
| `repl_active` | A live REPL or `relay run` exists on the repository. |
| `state_corrupt` | The state file is unreadable. Inspect it, then move it aside to reset. |

After review:

```bash
python3 scripts/relay_continuity.py release --note "push landed on origin; safe to continue"
#   --clear-cooldown claude|codex  also clears a provider cooldown (e.g. a spend cap you raised)
#   --drop-pending                 forgets an unresolved launched attempt
python3 scripts/relay_continuity.py run --session $S
```

A release is recorded in the attempt journal and the control ledger. Every hold names the turn it is about (`status` shows `hold.turn`). A release acknowledges exactly that turn: a later turn on the same session (for example, one you ran by hand in the REPL) is gated afresh. If one turn holds for two reasons in sequence (say `auth_failure`, then `effects_uncertain`), each release adds to the acknowledgement for that turn. A release waives only the review it answers: the released turn is not re-gated, and an `auth_failure`/`unknown_failure` turn is retried once on the same agent. Provider cooldowns, failover confirmation and circuit bounds still apply, and a new failure is gated again. Releasing `permissions_changed` accepts the new settings as the pinned authority.

## Behaviour notes

- **Failover needs evidence.** The supervisor switches to the other agent only when a fresh `limits` reading shows that agent has room. Without one, it waits for the failed agent's own reset. Transient and crash retries never switch agent.
- **Provider resets.** Reset times come from `agent-relay --json limits --refresh` when the reading is fresh and plausible. Otherwise they come from the provider's own message ("resets 4:20pm (Europe/Rome)", "try again at 11:38 PM"). If neither is usable, the supervisor rechecks after 30 minutes. A Claude "monthly spend limit" message that prints a session reset is treated as a session quota. A spend cap without a reset needs `release --clear-cooldown`.
- **Headless authority is narrower than the REPL's.** Relay applies `permissions.toml` backend modes only in the REPL. Headless continuations run Claude in `--permission-mode default` with Relay's approval hook, so tool calls that need approval are refused, and the agent will report itself blocked. Codex runs with Relay's headless default, which allows workspace writes. The supervisor never widens this.
- **Claude REPL permissions.** On this workstation, `.agent-relay/permissions.toml` selects the REPL launch mode. Keep `[claude.backend].mode = "auto"` for bounded Claude approval and do not set `bypassPermissions` in `.claude/settings.local.json`. That local file allows only `Bash(git status)` and `Bash(python3 scripts/devctx.py recover)` as recovery fallbacks. Relay v0.7.7 runs Claude with `-p`; a `default` mode request outside those rules was denied without an interactive approval prompt in the 2026-10-19 live check. Inspect a fresh turn's `system/init.permissionMode` and its tool results before assuming a mode change worked. The notify-only watcher alerts once per completed REPL turn if the effective mode is `dontAsk`.
- **Restart safety.** Every launch writes an intent record with a nonce before Relay starts. If the supervisor dies, the Relay turn keeps running in its own session. On restart the supervisor waits for that process (it never relaunches it), then finds the session by nonce and classifies it.
- **Slack.** Messages use fixed templates with validated fields only. They never include transcripts, prompts, tool output, paths or secrets. The webhook is read from `~/.config/jarvis/slack_webhook_url`, which must be mode 600. Delivery failures are counted and retried once, and never interrupt supervision.

## Rollback

1. `python3 scripts/relay_continuity.py stop` (or kill the supervisor by exact PID; the running turn is unaffected), and stop `relay-watch`.
2. Restore the Relay REPL handoff order: `cp ~/jarvis-control/work/continuity/backup-20261018/relay-user-config.toml ~/.config/relay/config.toml`. Check it with `sha256sum` against `SHA256SUMS` in that directory.
3. Optionally remove `~/jarvis-control/work/continuity/`. Nothing else reads it.
4. The legacy autopilot is preserved in `~/jarvis-control/autopilot/retired-20261018/` (see its README). Moving the scripts back restores it.

## Incident reconciliation (spec 197)

`run` reconciles uncertain operations before holding (pass `--no-reconcile` for the spec 195 behaviour):

1. **Running work.** Work of the chain still running in a checkout or container (a worker lane, a `nohup` job) is waited for, polled every 5 min, for at most 3 h. It is never relaunched.
2. **Probes.** The supervisor reads Git and GitHub itself:
   - one-branch `git push`: is the remote at the local commit?
   - `gh pr merge <n>`: is the PR merged or still open?
   - `gh pr create`: is there an open PR for the head?
   - `Edit`/`Write`: is the change in the file?
3. **Diagnosis in a read-only sandbox.** For anything else (a subagent, a script, a PR comment), Codex investigates under `codex exec --sandbox read-only`. The operating system makes every file read-only and cuts the network, and user config, rules and MCP servers are not loaded. Before each run, a canary check proves on this host that the sandbox blocks a write. If it does not, no diagnosis runs (`reconcile_no_sandbox`). The diagnosis gets the operations and a sanitized evidence bundle (worktrees, branches, remote heads, PRs, worker lanes), and must answer with a `RECONCILE-VERDICT` line. There are at most two runs of up to 45 min each.
4. **Codex out of quota: it waits.** The supervisor sleeps until Codex's reported reset (from `agent-relay limits`, or Codex's own message), or rechecks every 30 min when no reliable reset is known. A stale or missing Codex reading is not a reason to wait: Relay refreshes it only when Codex runs, so the diagnosis is simply tried, and a try lost to quota costs no attempt. Then it continues by itself. The wait survives restarts and is bounded to 8 days. A diagnosis cut off by quota or a network outage is retried and does not use up an attempt. A Codex spend cap with no reset, or a Codex login failure, holds: those are the operator's.
5. **Promotion is deterministic.** A model can mark an operation `completed`, or a local operation `not_started`. It can never establish that a push, merge, comment or other external effect did not happen. Any recorded write attempt or repository change still voids a diagnosis.
6. **Result.** If everything is settled, the chain continues (for example, Claude quota → Codex) and the recovery prompt lists each operation as COMPLETED (do not repeat) or NOT STARTED. Otherwise it holds with a `reconcile_*` reason. Every outcome is in `attempts.jsonl` (`"event": "reconcile"`) and in the control ledger. Diagnosis transcripts are under `~/jarvis-control/work/continuity/diagnostics/<nonce>/`.

A supervisor killed during a diagnosis adopts it on restart: it waits for the same process (found by pid or by its nonce), then reads its transcript. It never launches a second diagnosis. If the transcript cannot be found, it holds with `attempt_unresolved`.

### Apply and verify on the workstation (Ubuntu/WSL)

Until the PR is merged, run the new script from a separate worktree. The supervisor finds the main repository, its Relay sessions and its state from the current directory, not from the script's location.

```bash
cd ~/src/JarvisOS_v1
python3 scripts/relay_continuity.py stop; tmux kill-session -t relay-continuity 2>/dev/null   # never kills a turn
git fetch origin claude/nice-turing-uzv5ja
git worktree add ~/src/jarvis-197 origin/claude/nice-turing-uzv5ja    # after merge: plain `git pull` instead
RC="python3 $HOME/src/jarvis-197/scripts/relay_continuity.py"         # after merge: python3 scripts/relay_continuity.py

# 1. Offline proof, plus this machine's real Codex sandbox (with the backend's Python environment):
codex --version                         # 0.163.0 verified; the preflight checks the flags itself
(cd ~/src/jarvis-197/backend && RELAY_CONTINUITY_CODEX=$(command -v codex) python -m pytest -q tests/test_relay_continuity.py)
#    expect "... passed" with 0 skipped: test_real_codex_read_only_sandbox_blocks_writes ran on this host

# 2. Inspect the held incident (read-only):
$RC status                              # expect phase "held", hold.reason "effects_uncertain", hold.turn ".../turn-006"
S=$($RC status | python3 -c 'import json,sys; print(json.load(sys.stdin)["head_session"])')
$RC classify .agent-relay/sessions/$S/turns/turn-006 | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["outcome"], d["in_flight"])'

# 3. Recover it, unattended: no release needed. If Codex is out of quota the supervisor waits for its reset.
tmux new -d -s relay-continuity "$RC run --session $S; echo exit=\$?; sleep infinity"
tmux attach -t relay-continuity         # "re-examining held turn", "diagnostic run 1/2 on codex", or
                                        # "waiting for codex to run the diagnosis; next check ...", then "uncertain operations settled"

# 4. Verify what happened:
$RC status                              # reconcile record (waiting_since / wake_at while waiting); then the chain advances
grep '"event": "reconcile' ~/jarvis-control/work/continuity/attempts.jsonl | tail -2
ls ~/jarvis-control/work/continuity/diagnostics/               # one directory per diagnosis run
python3 scripts/devctx.py recover       # ledger: "reconciled turn ... from evidence" or the hold reason
```

Expected results:
- **Settled.** Codex continues the chain with the reconciled list in its prompt. Exit 0 once it is idle.
- **`reconcile_*` hold.** Exit 4, with a Slack HOLD. The journal record names the operation, its verdict, the evidence and the source. This is a real decision for the maintainer (an unprovable external effect, a refused check, a missing sandbox): settle it, then `$RC release --note "..."` and run again.

**Surviving reboots (optional).** A wait survives a supervisor restart, but something must start the supervisor again after a reboot. With systemd enabled in WSL (`/etc/wsl.conf`: `[boot] systemd=true`) and `loginctl enable-linger $USER`, create `~/.config/systemd/user/relay-continuity.service`:

```ini
[Service]
WorkingDirectory=%h/src/JarvisOS_v1
ExecStart=/usr/bin/python3 %h/src/JarvisOS_v1/scripts/relay_continuity.py run --session SESSION_ID
Restart=on-failure
RestartPreventExitStatus=3 4
RestartSec=300
[Install]
WantedBy=default.target
```

Enable it with `systemctl --user enable --now relay-continuity`. Exit 4 (held) and exit 3 (lock busy) are not restarted. Once the PR is merged, `ExecStart` points at the main checkout.

Headless authority of the continuation is unchanged: it runs through Relay's runner exactly as in spec 195. Remove the worktree after merge: `git worktree remove ~/src/jarvis-197`.
