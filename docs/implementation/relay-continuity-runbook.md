# Relay continuity supervisor: operational runbook (spec 195)

`scripts/relay_continuity.py` continues a Relay coordinator session chain after a failed turn, and sends sanitized Slack notices. It never modifies the repository, Relay's configuration, permissions or session journals. Durable state is under `~/jarvis-control/work/continuity/` (override it with `RELAY_CONTINUITY_DIR`).

## When to use it

Run the supervisor when you step away from an interactive Relay REPL session and want failures to be handled:

| Failure | What the supervisor does |
| --- | --- |
| Quota exhaustion | Switches Claude → Codex, then returns to Claude at a turn boundary once Claude's reset is confirmed. |
| DNS/API blips | Retries the same agent with bounded backoff. |
| Interrupted turns | Retries once, but only when no side effect is uncertain. |

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
| `effects_uncertain` | The failed turn was interrupted during a non-read-only operation (push, merge, PR comment, file write, subagent, script), or while a background job it launched (a worker lane, a queue) was still running. Background jobs are the commonest cause: check the lane with `devctx.py lanes`. Check whether it took effect with `git log`/`gh pr view`/`python3 scripts/devctx.py recover`. |
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
- **Restart safety.** Every launch writes an intent record with a nonce before Relay starts. If the supervisor dies, the Relay turn keeps running in its own session. On restart the supervisor waits for that process (it never relaunches it), then finds the session by nonce and classifies it.
- **Slack.** Messages use fixed templates with validated fields only. They never include transcripts, prompts, tool output, paths or secrets. The webhook is read from `~/.config/jarvis/slack_webhook_url`, which must be mode 600. Delivery failures are counted and retried once, and never interrupt supervision.

## Rollback

1. `python3 scripts/relay_continuity.py stop` (or kill the supervisor by exact PID; the running turn is unaffected), and stop `relay-watch`.
2. Restore the Relay REPL handoff order: `cp ~/jarvis-control/work/continuity/backup-20261018/relay-user-config.toml ~/.config/relay/config.toml`. Check it with `sha256sum` against `SHA256SUMS` in that directory.
3. Optionally remove `~/jarvis-control/work/continuity/`. Nothing else reads it.
4. The legacy autopilot is preserved in `~/jarvis-control/autopilot/retired-20261018/` (see its README). Moving the scripts back restores it.
