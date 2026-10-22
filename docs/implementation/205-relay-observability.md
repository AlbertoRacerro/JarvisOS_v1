# 205 — Relay observability: evidence

Spec: [205](../specs/205-relay-observability.md). Issues [#866](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/866), [#859](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/859) Phase A.

## Delivered

- `scripts/relay_observe.py` is the canonical read-only adapter. `snapshot()` classifies the owner from durable state only. Owner liveness comes from the kernel lock table (`/proc/locks`), which is read without taking the lock. `incidents()`, `digest_text()` and `alert_text()` produce Italian, bounded, scrubbed messages, and `observe_step()` handles edge-triggered alerts and the digest schedule. The `follow` terminal monitor reads incrementally, tolerates torn lines, redacts output and follows session handoffs.
- `relay_continuity.py watch` runs on the host, outside the sandbox that hides the webhook, and calls `observe_step()` on every poll. The digest defaults to 2 hours (range 1–4). Mission chain sessions are no longer reported as REPL failures. `Notifier.send_text()` reuses the existing URL validation, secret check, dedupe, rate limit and failure accounting. The old field-template digest is removed.
- `notify-test --digest` / `--alert` send the semantic formats on demand.
- Runbook: "Observability (spec 205)" in [relay-continuity-runbook.md](relay-continuity-runbook.md).

## Verification

- `backend/tests/test_relay_observe.py`, 16 tests. They cover classification of every state, the rule that a settled cycle is not verified delivery, corrupt state, the kernel lock table both faked and with a real held flock, digest content, links and secret scrubbing, alerts on transition, suppression of repeats and after a watcher restart with JSON-persisted state, re-announcement after clearing, the owner-down incident, the prolonged-wait threshold, a blocked roadmap carrying the ledger question, Slack-down retry and failure reporting, `send_text` dedupe and no exceptions, merge parsing, torn JSONL, render redaction, session handoff in `follow` with the control root unmodified and no locks, and the interval bounds.
- The relay continuity suite with the new tests: 481 passed, 1 skipped. Ruff is clean, and `relay_observe.py` was added to the CI ruff gate.
- Live, read-only, inside the sandbox on 2026-10-22: `relay_observe.py status` and `digest` correctly reported roadmap cycle 4, task 1/1, as `running` on claude with the owner alive, and showed the current claim.

## Pending (maintainer host evidence)

The webhook is deliberately unreadable inside the sandbox, so the sandboxed coordinator cannot run the real Slack end-to-end delivery (acceptance 2). On the host, run `python3 scripts/relay_continuity.py notify-test --digest` and `notify-test --alert`, then enable `jarvisos-relay-watch.service` as described in the runbook. The command prints the delivered text without the URL; record it here. The live observation of a real owner task with the terminal monitor (acceptance 3) can run from any shell with `python3 scripts/relay_observe.py follow`.
