# 205 — Relay observability: semantic Slack digest, incident alerts, terminal monitor

State: **ready** (live state in [`STATUS.md`](STATUS.md)). Maintainer [issue #866](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/866) and [issue #859](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/859) Phase A, ordered first by the binding 2026-10-22 directive `L20261022051213-c458` after spec 204. Depends on 195, 201, 203 and 204.

## Outcome

The maintainer can walk away and still learn, in short plain Italian, what the spec 201 owner is doing, why, what was delivered and with what evidence, what comes next and whether intervention is needed. Actionable incidents arrive promptly instead of waiting for the digest. A terminal viewer follows the active owner's mission and session chain live, read-only.

One canonical read-only adapter derives a semantic snapshot from the authoritative owner state: mission definitions and stores, the missions journal, `roadmap.json`, `STOP`, the owner lock and the latest Relay turn state. It classifies the owner as `running`, `queued`, `checkpointed` (task pending after a turn), `verified_complete`, `held`, `paused`, `waiting` (provider/CI reset), `idle` (verified no pending work), `stopped` or `unknown`. It never infers liveness from GitHub activity. The Slack digest, the alerts and the terminal monitor all use it, and later JarvisOS Coding (Phase B) can too.

## Design constraints

- Delivery runs in the existing host-side `relay_continuity.py watch` loop, outside the sandbox. The Slack webhook stays outside the provider sandbox, where agents run with `bypassPermissions`. The watcher only reads owner state and writes only its own `watch/` store. It never takes `coordinator.lease` or `serve.lock`, writes owner or mission state, or calls a provider. Because the watcher is a separate process, it can also report that the owner stopped while work is pending.
- The existing notifier stays in use: `hooks.slack.com`-only URL validation, no proxies or redirects, rate limit, dedupe, a single retry and error classes that never include the URL. Free text comes only from agent-written turn `next_step`/summary and mission task text. It is bounded, stripped of control characters and links and rejected if `devctx.find_secret` matches. Issue/PR links are generated only for this repository.
- Digest default interval: 2 hours, adjustable from 1 to 4 (`watch --digest-hours`). Alerts are edge-triggered on state transitions, deduplicated durably in the watch store across restarts, and never block or slow supervision when Slack is down. Webhook delivery failures are counted and reported in the next delivered message.
- No new daemon, scheduler, database, provider cost or secret handling. The terminal monitor is `python3 scripts/relay_observe.py follow`. It tails `output.jsonl` incrementally, tolerates torn final lines, redacts secrets, follows session handoffs and exits on Ctrl-C without touching any lock.

## Acceptance

1. Deterministic tests cover classification (running vs checkpointed vs verified complete, held, paused, waiting, idle, stopped, unknown). They show that alerts fire on detectable transitions and are suppressed when repeated, that dedupe survives a watcher restart, that a failing sender never raises into the loop, and that the digest answers what, why, delivered, next and problem in a few lines with issue/PR links.
2. A real end-to-end delivery to the existing webhook covers one semantic digest and one incident alert, with message samples recorded without secrets. The webhook is deliberately unreadable inside the sandbox, so this step runs on the host (`relay_continuity.py notify-test --digest` / `--alert`) and is recorded as pending maintainer host evidence until done.
3. Terminal monitor: tests for fragmented JSONL, secret redaction, session handoff and read-only/no-lock behaviour, plus a live observation of a real owner task.
4. Operator docs cover the interval control, the test commands and the host watcher unit, including the owner-failure alert. Exact-head CI, merge and `STATUS.md` reconciliation follow the normal rules.

Phase B (JarvisOS Coding integration) and Phase C (H2O/Qwen evaluation) of #859 remain separate subsequent work.
