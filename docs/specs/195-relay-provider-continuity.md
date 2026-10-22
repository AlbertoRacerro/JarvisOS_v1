# 195 — Relay provider continuity and Slack outbound monitoring

State: **ready**. Combined definition, full contract and readiness, authorized by the maintainer's 2026-10-18 approval (control ledger directive `L20261018073626-2e9f`). It follows the 2026-10-15 directive that made provider continuity and Slack monitoring the next mission after 193/194. Phase 3, inbound Slack commands, is explicitly deferred.

## Problem

Coordinator work runs as Agent Relay sessions driven by Claude Code or Codex. When a turn ends because of a provider quota, a DNS/API outage or a crash, nothing continues the work: the maintainer has to notice and type "continue", and must pick the provider by hand. The 2026-10-17/18 survey found the following.

- **Relay's turn status is not evidence.** In the current session, turn 1 (Codex usage limit), turn 4 (no result captured) and turn 6 (Claude `EAI_AGAIN`) are all recorded as `completed`. Across 34 historical sessions, 17 Codex usage-limit turns, 17 Claude monthly-spend-limit turns, more than 30 Claude session-limit turns and 13 `EAI_AGAIN` turns were all recorded as `completed`.
- **Relay's error text misleads in both directions.** In a 2026-10-18 probe, a Codex turn that finished successfully (`turn.completed`) was reported as `agent_error` / "couldn't reach the service". Relay had read unrelated stderr lines: an MCP auth warning and a model-list refresh timeout.
- **Native capabilities, verified by probe and by reading the bundled Relay v0.7.7 modules.**
  - `agent-relay --json limits [--refresh]` returns provider-reported usage windows with `resets_at` and `as_of`. Readings can be stale: a Codex `resets_at` was already in the past.
  - `agent-relay --json run <agent> --continue <sid> -t <task> -n <k> -y` runs headless turns. It creates a new session per invocation, linked to its parent only inside the turn prompt, and returns structured JSON.
  - `handoff plan` ranks successors from the REPL user config `~/.config/relay/config.toml` `[handoff] order`. The daemon's `~/.relay/config.toml` `fallback_chain` is never read for selection. `--limited` records a flat estimated cooldown.
  - The daemon's handoff engine only writes a snapshot and a desktop notification on a hook-reported rate limit. It never launches an agent.
- **The legacy autopilot** (`~/jarvis-control/autopilot`, not running) detects quota by regex, assumes a hardcoded 04:35 reset and a hardcoded `k145` worktree, and drives only Claude. Its watchdog posts to an existing Slack incoming webhook.

## Outcome

1. A failed coordinator turn is classified deterministically from raw evidence.
2. Recoverable failures continue automatically on the right provider, at the right time, through Relay's own headless runner.
3. Continuation never silently duplicates a non-idempotent operation and never grants authority the interrupted turn did not have.
4. The maintainer receives sanitized, deduplicated Slack notifications of significant events.

## Architecture decision

Relay stays the session, transcript and execution owner. It is invoked and read, never modified. Native pieces are reused where the probe showed them to be reliable:

- `limits` is the provider-reported reset-time source.
- `run --continue` is the turn executor.
- The REPL `[handoff] order` is the configured preference.

A small supervisor adds only what Relay does not do reliably: raw-evidence classification, the side-effect gate, durable retry/cooldown policy, and outbound notification.

One standard-library-only module, `scripts/relay_continuity.py`, has these subcommands:

| Subcommand | Behaviour |
| --- | --- |
| `classify <turn-dir>` | Prints the deterministic outcome of one Relay turn. Read-only. |
| `run --session <sid>` | Supervises continuation of one Relay session chain until it is idle, held, stopped or done. |
| `status` | Shows durable state: current head session, provider cooldowns, attempt history, hold reason and circuit state. |
| `stop` | Writes a stop request. The supervisor exits gracefully at the next safe point and never kills a running turn. |
| `release` | Clears a manual hold after maintainer review, recording who released it and why. |
| `notify-test` | Sends one fixed test message through the outbound channel. |
| `watch` | Notify-only monitor of maintainer-driven REPL sessions and integration events. Never acts on a session. |

Durable state is a versioned JSON document plus an append-only attempt journal under `~/jarvis-control/work/continuity/`, outside the repository. Every switch, hold and release is also written to the spec 154 control ledger, so `devctx.py recover` shows it.

### Turn classification (closed set)

Classification reads `output.jsonl` first. It uses `stderr.log` and Relay's run JSON only when no terminal event exists. Relay's `status`/`run_error`/`stop_reason` never decide success.

| Outcome | Evidence |
| --- | --- |
| `success` | Claude `result` event with `is_error=false`. Codex `turn.completed` with no later `error`/`turn.failed`. |
| `quota` | Claude `is_error` + `api_error_status=429` + session/weekly limit text. Codex `error`/`turn.failed` usage-limit text. Carries a provider-message reset time when present. |
| `spend_limit` | A spend/credit cap with no printed reset. Raising spend is a maintainer decision. A spend-cap message that also prints a timed session reset (Claude's "monthly spend limit · your session limit resets 4pm") is a `quota` with that reset: the corpus shows work resuming after it. |
| `transient` | DNS/connection failures (`EAI_AGAIN`, unreachable API server), HTTP 5xx, overloaded/529. |
| `auth` | HTTP 401/403, login-required or expired-credential text. |
| `crash` | No terminal event (missing, empty or truncated output). A turn with no output of its own (missing, empty, or a byte-identical copy of the previous turn's output, which Relay leaves when it captures nothing) has no evidence and is always held as `output_missing`. Only a truncated stream with recorded events gets the crash retry. |
| `unknown` | Any other error terminal. |

### Side-effect gate (duplicate-execution safety)

Amended 2026-10-23 by maintainer directives `L20261022213650-31c7` and `L20261022220755-8248` (minimal controller). The earlier gate held for any interrupted non-read-only operation, scanned the process table and containers for "live work", and depended on a read-only Codex diagnosis (spec 197). On 2026-10-22 that kept mission `m-20261022T181241Z-3c9f97` waiting more than two hours for Codex's reset, with Claude available, over three interrupted local commands (uvicorn, `npm run preview`, a capture script). The gate now holds only where repeating an operation could not be undone.

The supervisor never replays the failed turn's prompt. A continuation always uses a fixed recovery prompt that requires `devctx.py recover` and carries a deterministic effects record of the failed turn.

Each tool call in the failed turn's raw output is paired with its result and classified as `read_only`, `local_write`, `external` (push, PR/merge/comment, non-GET network, notifications, remote triggers), `background` (detached processes) or `unknown`. MCP tools count as `external`, since their servers may be remote.

- **Process ownership.** The supervisor is a child subreaper (`PR_SET_CHILD_SUBREAPER`). Everything a turn starts stays its descendant, including what it detached with `&`, `nohup`, `setsid` or a double fork. When the turn ends, every descendant still running gets SIGTERM, then SIGKILL after a short grace period. An operation that was in flight is therefore *interrupted*, never still running when the next turn starts. `run` and `serve` refuse to start when the kernel refuses the subreaper role. This was verified on the workstation inside `jarvis-sandbox`, where no container runtime exists. A turn that ran under an earlier owner (before a restart) is not this process's to stop. Its successor is told that survivors are possible, and to check them before starting a server or worker again.
- **Interrupted local operations** (`local_write`, `background`, `unknown`, including scripts and subagents) do not hold. They are listed to the successor as `INTERRUPTED`. The successor inspects their effects before repeating them, and repeats them only when that is safe. If one may already have had an external effect that it cannot verify and that must not happen twice, it records a blocker and ends with `RELAY_STATUS blocked`, which holds the mission. Accepted residual risk (maintainer, `L20261022220755-8248`): an arbitrary script can have effects that are not immediately observable.
- **Interrupted external operations** are settled only by the spec 197 deterministic read-only probes: the push of one branch, `gh pr merge`, `gh pr create`. A `completed` or `not_started` verdict is reported to the successor. Any other external operation, or a probe that fails, holds `effects_uncertain`. This also applies to a detached external job left by a *successful* turn.
- **No evidence.** Unparseable output (`output_unparseable`), a turn with no output of its own (`output_missing`), and an attempt that left no identifiable Relay session or a journal launch the state does not account for (`attempt_unresolved`) still hold. Nothing then shows what the turn did. A session is identified only by its own first attempt-marker line, and only when exactly one session carries it.

A crash after the repository fingerprint changed no longer holds: the local changes are the successor's to inspect. Only `release` leaves a hold, and a release waives only the gate review it answers. Holds that the earlier controller raised and this policy no longer raises (`live_work`, `reconcile_*`, `auth_failure`, `unknown_failure`, `crash_repeated`, `circuit_attempts`/`_switches`/`_transient`, `repl_active`, `task_report_unverified`, and `effects_uncertain`) are decided again on the next run of the held chain's own head session, for exactly the held turn. If the chain has moved, the hold stays and is marked not re-examinable.

Command classification accounts for execution-capable arguments. Examples are `env`/`timeout`/`nohup` wrappers, `awk` `system()` and pipes, `sed` `e`/`w`, `find -fprint`, attached `curl -XPOST`/`-d` and `gh api -f` forms, and `$(...)` inside unquoted heredocs. Anything not recognized is `unknown`.

Terminal evidence: only the last top-level terminal decides (subagent results never do). Claude success requires `is_error` exactly `false` with `terminal_reason` `completed`. Without a terminal event, an authentication diagnostic in Relay's stderr or run JSON yields `auth`, never a retryable crash.

Completed `local_write`/`external`/`background` calls with results are listed in the recovery prompt as already done and must not be repeated. Their effects are inspectable through Git, GitHub and `devctx` recover.

### Continuation policy

Amended 2026-10-23 (same directives): the controller automates the maintainer's manual procedure. When a provider runs out, the other continues. When both are out, it waits for the earliest reset and resumes.

- **Agents.** Claude and Codex only. Per-agent model and permission settings stay exactly as Relay's configuration and the spec 201 profile define them.
- **Choice.** A chain starts on Claude, the preferred agent. Every new mission, and so every roadmap cycle, starts on Claude. It then stays on whichever agent is working, and switches only when that agent cannot run. There is no voluntary return, dwell time or switch budget.
- **Permission pinning and approval gates** are unchanged. A failover turn never has more authority than the turn it replaces.
- **Provider failures make only that provider unavailable**, through a persistent per-agent cooldown. The other agent continues at once when it can run:
  - `quota`: until the provider-reported reset. That is a fresh `limits` reading with a plausible future `resets_at`, else the provider's own message, else an estimate that starts at `recheck` (30 min), doubles for each further estimated failure of that agent up to `recheck_cap` (4 h), and resets on its success. Readings are optional scheduling information: a missing, stale or implausible reading is no evidence either way. The agent is tried, and its own run decides (execution-driven failover, directive `L20261022204106-22ab`).
  - `transient`: a short backoff for that agent, starting at `transient_base` (60 s), doubling, capped at `transient_cap` (30 min).
  - `auth`: the estimated backoff, with a notification. Renewing a login is the maintainer's action. Until then the other agent works.
  - `spend_limit`: no expiry by time; only `release --clear-cooldown` ends it. A spend cap that outlives its printed session reset, or repeats on a distinct turn with no success in between, is a `spend_limit`. A time-only printed reset less than 6 hours behind the turn's end is stale and falls back to the estimate.
  - A cooldown is recorded once per failed turn, so a restart that decides the same turn again neither extends it nor backs it off.
- **`crash`, `unknown`.** Retried on the same agent, with no cooldown.
- **Both agents unavailable.** Sleep until the earliest cooldown ends, at most `recheck` at a time, in interruptible chunks with no busy loop. Then take whichever agent is usable. Only caps with no reset (both spend-limited) hold `no_provider_available`. A wait longer than `max_wait` (8 days) holds `wait_exceeded`.
- **Circuit breaker.** One bound only: `max_consecutive_failures` (8) consecutive launched turns ending in `crash` or `unknown` hold `circuit_failures`. Provider failures are bounded by their cooldowns and `max_wait`.
- **Another coordinator.** A live REPL, which holds the coordinator lease or sits in this process table, or a legacy autopilot, makes the supervisor wait without a hold. Nothing is launched, and the same decision is taken once the other coordinator has gone.
- **Turns per invocation.** Each invocation runs at most the configured number of turns, default 1. After a `success` with no queued task, the chain goes **idle**.

### Process safety

- **Single instance.** Exclusive `flock` on the state directory, plus a refusal to start when legacy autopilot processes or another live supervisor exist.
- **Atomic, validated state.** Writes go to a temp file, then fsync, then rename. A corrupt, unknown-version or structurally incomplete state file (any missing or mistyped field) causes a hold, never a reset or a silent repair from defaults.
- **Restart safety.** Each launch first writes an intent record with a unique attempt nonce, embedded in the recovery prompt. On restart, a launched attempt without an outcome is resolved as follows: if its Relay process is still alive (pid plus start time), the supervisor waits for it. Otherwise it locates the Relay session by nonce and classifies it. If neither is possible, it holds.
- **Graceful shutdown.** SIGTERM/SIGINT and `stop` finish or leave the running turn intact and record the state; they never kill an agent.

### Slack outbound (Phase 2)

- Fixed message templates per event type. Every field passes an allowlist validator before rendering, and there are no free-text fields. Allowed fields:
  - event type, agent, outcome class, action;
  - Relay session id, attempt count;
  - ISO timestamps and reset source;
  - spec id, PR number, short or full SHA;
  - hold/stop reason enum, counts.
- Raw transcripts, prompts, tool output, stderr, paths, environment, file contents and secrets are never accepted. A value failing its validator drops the message, and the drop is logged locally.
- The webhook URL is read from `~/.config/jarvis/slack_webhook_url` (mode 0600) at send time. It is never logged, printed, persisted elsewhere or included in exception text.
- Events: provider switched, provider exhausted, all agents exhausted, manual hold, circuit open, unrecoverable failure, supervisor started/stopped, turn completed (idle), master advanced (merged PR number and SHA), failure observed in an unsupervised REPL session (notify-only), plus a periodic digest.
- Deduplication keys are persisted. There are a per-hour rate limit and a digest interval.
- Delivery failures are caught, counted and retried at most once later. They never raise into the supervisor.

## File boundaries

- **New:** `scripts/relay_continuity.py`; tests `backend/tests/test_relay_continuity.py`; trimmed and sanitized real-turn fixtures under `backend/tests/fixtures/relay_continuity/`; this spec; a runbook section in `docs/implementation/relay-continuity-runbook.md`.
- **Architecture enforcement:** one `accepted_owner` AE002 entry in `configs/architecture_enforcement.json` for `scripts/relay_continuity.py::post_webhook`, the only external dispatch. It is bound to a strictly validated `https://hooks.slack.com/services/` URL, with redirects rejected and proxies disabled.
- **Unchanged:**
  - Relay binary and session format;
  - product backend/frontend/schema;
  - `scripts/devctx.py`, imported read-only for ledger append and secret patterns;
  - governance documents, apart from STATUS rows.
- **Local configuration, outside Git, backed up before change:** `~/.config/relay/config.toml` `[handoff] order = ["claude", "codex"]`. The backup is under `~/jarvis-control/work/continuity/backup-20261018/`.

## Ownership

The Opus Frontier Coordinator owns the architecture, the implementation integration, acceptance and merge. Codex performs the independent review of the final head. Gemini performs a bounded read-only audit of classifier results over the historical turn corpus. Worker output is reviewed by the coordinator and is never auto-promoted.

## Acceptance criteria and required evidence

Deterministic offline tests run with injected clock, Relay runner, limits reader, process table and HTTP sender, and no network. They cover:

1. Real recorded failures from fixtures: Codex usage limit, Claude `EAI_AGAIN`, Claude session limit with reset time, Claude monthly spend limit, missing output, and false `completed` status. Also the Relay-misreported Codex success and Claude invalid-model 404 (expected: `unknown`, hold).
2. Restart during failover (intent written, supervisor killed, Relay still running or finished), stale or past reset timestamps, unavailable fallback provider, concurrent supervisor start, repeated crash loop (circuit opens), transient backoff bound, and oscillation bound.
3. Ambiguous side effects:
   - an in-flight `git push`, `gh pr merge`, Write or subagent call → hold;
   - live work in a checkout or a container started inside the chain's window → `live_work` hold; work older than the latest release → no hold;
   - completed effects listed in the recovery prompt;
   - **a test proving that no Relay invocation is issued** for any held attempt, including after restart.
4. Interrupted state writes: a crash between temp write and rename leaves the previous state valid; a corrupt state file holds.
5. Slack: webhook failure (exception, timeout, HTTP 500) never propagates; dedupe and rate limit; allowlist rejection of free text and of secret-pattern values; the webhook URL is absent from every log, exception and state file.
6. Manual stop/resume and hold/release.
7. Classifier corpus check: every historical turn in this workstation's Relay sessions classifies without error, and the counts by class are recorded as evidence.
8. Fault injection on this workstation against real Relay with a scratch repository and a cheap model:
   - a real success;
   - a forced provider error;
   - a supervisor kill during a running turn followed by restart adoption;
   - a forced side-effect hold with no relaunch;
   - one real Slack notification and digest through the existing webhook.

A full clean-environment backend suite runs at the exact head, plus CI. Independent Codex review of the final head finds no unresolved blocking finding.

### Amended acceptance (2026-10-23, minimal controller)

Offline tests cover:
- process ownership against real detached processes (`setsid`, `nohup`, double fork) and escalation to SIGKILL;
- local interrupted operations continuing on the available agent with the `INTERRUPTED` record;
- unsettled external operations, MCP calls and detached external jobs holding, and probe-settled ones continuing;
- provider-scoped cooldowns for quota/transient/auth, failover and waits;
- the single failure circuit; waiting rather than holding beside a live REPL;
- re-decision of the earlier controller's holds, and abandonment of its pending diagnosis;
- a replay of the 2026-10-22 incident state.

Workstation evidence: a dry replay of the preserved mission on a copy of its store, and a `serve --once` run inside `jarvis-sandbox` with a fake `agent-relay` that left detached processes. Claude ran out of quota, its processes were stopped, and Codex started at once, found no survivor and completed the checked task.

## Rollback

1. `relay_continuity.py stop` (or kill the supervisor by exact PID; the running turn is unaffected).
2. Restore `~/.config/relay/config.toml` from the backup and verify the SHA-256 checksums.
3. Delete or keep `~/jarvis-control/work/continuity/state`. It is never read by anything else.
4. The legacy autopilot scripts stay in place until this spec is accepted. They are then moved to a dated `retired-*` directory with a README, and restoring them is a move back.

No repository data, Relay session or product state is modified by the supervisor.

## Non-goals and boundaries

- No Phase 3: no inbound Slack commands, bot tokens, Socket Mode, listening ports or remote control.
- No new credentials, no spending changes, and no attempt to raise or work around provider limits.
- No modification of the Relay binary, its hooks, `permissions.toml` or its session journals.
- No terminal keystroke automation.
- No agents other than Claude and Codex.
- No change to approval, review or merge authority.
