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

The supervisor never replays the failed turn's prompt. A continuation always uses a fixed recovery prompt that requires `devctx.py recover` and carries a deterministic effects record of the failed turn.

Each tool call in the failed turn's raw output is paired with its result and classified as `read_only`, `local_write`, `external` (push, PR/merge/comment, non-GET network, notifications, remote triggers), `background` (detached processes) or `unknown`. Subagents, MCP tools and unparsed shell count as `unknown`.

Automatic continuation is refused, and the chain enters a **manual hold** with an alert, when any of these hold:

- any non-`read_only` call has no paired result (it was in flight at interruption, so whether it took effect is unknown). A background launch (a `run_in_background` tool, a detached `&`/`nohup` command) counts as in flight until its completion notification is seen, because its result is only the launch acknowledgement. A subagent's calls settle only when the subagent itself finished;
- **live work**: before any automatic continuation, and before handing a successful chain a new task, the supervisor checks what is actually running. It looks at this user's live processes whose working directory is the repository or one of its worktrees, and at running docker/podman containers. Such work holds (`live_work`) when it started inside the chain's window, which opens at the chain's first session or the latest maintainer release, whichever is later. A multiplexer pane's program and a container with exec sessions also hold however old they are, because an `exec` starts new work without a new start time. They stop holding only when a release acknowledged that exact identity: pid, start time and argv digest, or container id, start and exec sessions. A release records the identities live at that moment. Bare interactive shells reading a terminal, multiplexer servers, the supervisor and its own ancestors are skipped. Inspection fails closed: an unreadable process table, a failed worktree listing, a container daemon that is reachable but cannot be listed or inspected, or an undatable container counts as live; an unreachable daemon means no containers only when no container shim (`containerd-shim*`, `conmon`) is running, because live restore keeps containers alive without their daemon. Detached work (`&`, tmux/screen, nohup, daemons, containers) outlives the call that launched it, and no shell classifier can recognize every way to start it, so this check is the backstop for detachment across calls, notifications and turns. A task notification closes only tool-managed backgrounding, never a command that detached itself. Only process names are logged, never arguments;
- the output has unparseable lines;
- the outcome is `crash` and the repository fingerprint changed during the attempt;
- the attempt journal shows a launched attempt whose outcome cannot be established. This includes an attempt that left no identifiable Relay session even when the repository looks unchanged, because remote effects such as a merge or a PR comment leave no local trace. It also includes a journal launch that the state does not account for. A session is identified only by its own first attempt-marker line, and only when exactly one session carries it.

The repository fingerprint covers refs, worktrees, the main checkout's status and HEAD. Only `release` leaves a hold. A release waives only the review it answers: the released turn is not re-gated, and an `auth`/`unknown` hold is retried once on the same agent. Cooldowns, failover confirmation and every bound still apply.

Command classification accounts for execution-capable arguments. Examples are `env`/`timeout`/`nohup` wrappers, `awk` `system()` and pipes, `sed` `e`/`w`, `find -fprint`, attached `curl -XPOST`/`-d` and `gh api -f` forms, and `$(...)` inside unquoted heredocs. Anything not recognized is `unknown`.

Terminal evidence: only the last top-level terminal decides (subagent results never do). Claude success requires `is_error` exactly `false` with `terminal_reason` `completed`. Without a terminal event, an authentication diagnostic in Relay's stderr or run JSON yields `auth`, which is held, never a retryable crash.

Completed `local_write`/`external`/`background` calls with results are listed in the recovery prompt as already done and must not be repeated. Their effects are inspectable through Git, GitHub and `devctx` recover.

### Continuation policy

- **Preferred and fallback.** Claude is the preferred coordinator and Codex is the only fallback; no other agent is ever selected. Per-agent model and permission settings stay exactly as Relay's existing configuration defines them. The supervisor passes no permission, sandbox or model flags.
- **Permission pinning.** It pins the digest of the authority-bearing settings in `.agent-relay/permissions.toml` on first run, including the file's absence, and holds if the digest changes. Creating the file later is a change. Releasing a `permissions_changed` hold re-pins the reviewed settings.
- **Approval gates.** A failover turn never has more authority than the turn it replaces. It cannot approve, merge or bypass a gate the original could not.
- **Headless authority is narrower than the REPL's.** Relay applies the configured `permissions.toml` backend modes (`bypassPermissions`, Codex sandbox and approval policy) only in its interactive REPL. Headless `run` starts Claude with `--permission-mode default` plus Relay's approval hook, so unapproved tool calls are refused. Codex runs with Relay's headless default, which allows workspace writes. The supervisor does not change this. Making headless continuations match REPL authority (for example through Relay's `[agent.allow]` patterns) is a maintainer authority decision outside this spec.
- **`quota`.** The agent goes into a persistent cooldown and the chain switches to the other agent unless that agent is itself cooling down or a fresh limits reading shows it out of quota. A missing, failed, stale or implausible reading is not evidence either way: the agent is tried, and its own run decides (amended 2026-10-22, see below). The cooldown ends at the provider-reported reset: a fresh `limits` reading with a future `resets_at`, else the provider's own message, else a recheck interval labelled estimated that doubles for each further estimated quota failure of that agent up to `recheck_cap` (4 h) and resets on its success. A cooldown is recorded once per failed turn, so a restart that re-decides the same turn neither extends it nor backs it off. Readings with an `as_of` older than the freshness bound, or a `resets_at` in the past, are refreshed and otherwise discarded. A reset is accepted only if it is no more than 8 days ahead.
- **Spend cap outliving its reset.** A second spend-cap failure on the same agent (a distinct turn, with no success in between) is a `spend_limit`, even when it prints a session reset. So is a single spend-cap turn whose printed reset is already behind the turn's end. The 2026-09-24 corpus shows Claude repeating the cap after its printed reset passed.
- **`spend_limit`.** As `quota`, but the cooldown never expires by time. Spend caps do not appear in the `limits` usage windows, so only `release` ends it.
- **Stale printed resets.** A time-only reset less than 6 hours behind the turn's end is a stale message, not tomorrow's reset. It falls back to a short recheck.
- **`transient`.** Retry the same agent with bounded exponential backoff and no switch.
- **`crash`.** One same-agent retry, subject to the side-effect gate, then hold.
- **`auth`, `unknown`.** Hold with an alert. These never cause a switch.
- **Same-agent retries.** `transient` and `crash` retries never switch provider, even when Claude is preferred and available.
- **Return to Claude.** Only at a turn boundary, after Claude's cooldown has passed and a minimum dwell since the last switch has elapsed. The dwell and the switch budget bound only a voluntary return from a working Codex. They never keep the chain on an agent whose last turn ran out of quota.
- **Both agents unavailable.** Wait until the earliest validated reset or estimate, recheck, and keep waiting with bounded waits without busy looping. Only spend caps, which have no reset, hold `no_provider_available`.
- **Circuit breaker.** Bounded consecutive failures and a maximum total attempts per run. Exceeding either bound opens the circuit: hold plus alert. Quota failures do not count as consecutive failures, because their cooldowns and backoff already bound them. Switches per window are bounded too. Over that budget, a voluntary return to Claude is skipped and the working agent continues, but a switch away from an exhausted agent always goes ahead. Together these prevent infinite loops and oscillation.
- **Execution-driven failover (amendment, 2026-10-22 maintainer directive `L20261022204106-22ab`).** A provider's real run result is the authority on whether it can work. `limits` readings are optional scheduling information. A fresh reading that shows exhaustion with a plausible reset defers an agent to that reset. Nothing requires a confirming reading, and no extra quota-probe turn is launched to obtain one. Missing or wrong usage statistics never need maintainer intervention. The side-effect gate, spec 197 reconciliation (still Codex read-only only), single-instance lock and live-work checks are unchanged.
- **Turns per invocation.** Each invocation runs at most the configured number of turns, default 1. After a `success` the chain goes **idle** (awaiting the maintainer) rather than inventing new work. The maintainer may opt into a bounded autonomous turn count.

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
