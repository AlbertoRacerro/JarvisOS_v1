# 205 — Relay observability: evidence

Spec: [205](../specs/205-relay-observability.md). Issues [#866](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/866), [#859](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/859) Phase A.

## Delivered

- `scripts/relay_observe.py` is the canonical read-only adapter. `snapshot()` classifies the owner from durable state only. Owner liveness comes from the kernel lock table (`/proc/locks`), which is read without taking the lock. `incidents()`, `digest_text()` and `alert_text()` produce Italian, bounded, scrubbed messages, and `observe_step()` handles edge-triggered alerts and the digest schedule. The `follow` terminal monitor reads incrementally, tolerates torn lines, redacts output and follows session handoffs.
- `relay_continuity.py watch` runs on the host, outside the sandbox that hides the webhook, and calls `observe_step()` on every poll. The digest defaults to 2 hours (range 1–4). Mission chain sessions are no longer reported as REPL failures. `Notifier.send_text()` reuses the existing URL validation, secret check, dedupe, rate limit and failure accounting. The old field-template digest is removed.
- `notify-test --digest` / `--alert` send the semantic formats on demand.
- Runbook: "Observability (spec 205)" in [relay-continuity-runbook.md](relay-continuity-runbook.md).

## Verification

- `backend/tests/test_relay_observe.py`, 17 tests. They cover classification of every state, the rule that a settled cycle is not verified delivery, corrupt state, the kernel lock table both faked and with a real held flock, digest content, links and secret scrubbing, alerts on transition, suppression of repeats and after a watcher restart with JSON-persisted state, re-announcement after clearing, the owner-down incident (also with roadmap mode on and nothing queued), finding the session of a first-turn attempt by its nonce, the prolonged-wait threshold, a blocked roadmap carrying the ledger question, Slack-down retry and failure reporting, `send_text` dedupe and no exceptions, merge parsing, torn JSONL, render redaction, session handoff in `follow` with the control root unmodified and no locks, and the interval bounds.
- The relay continuity suite with the new tests: 481 passed, 1 skipped. Ruff is clean, and `relay_observe.py` was added to the CI ruff gate.
- Live, read-only, inside the sandbox on 2026-10-22: `relay_observe.py status` and `digest` correctly reported roadmap cycle 4, task 1/1, as `running` on claude with the owner alive, and showed the current claim.
- Live terminal monitor, same day: `timeout 5 python3 scripts/relay_observe.py follow` attached to the running owner task (mission `m-20261022T051445Z-1bd5fa`, session `20261022-051514-515816`, the turn that produced this change). It found the session by its attempt nonce before the chain recorded it, then printed the header (`── missione … · compito 1/1 · running · claude`) and the Claude tool calls and results in order, each bounded to one line. It did not stall the owner and took no lock.
- Successor task, live, 2026-10-22T05:57Z: the next roadmap cycle (mission `m-20261022T055533Z-e4cec8`, cycle 5, session `20261022-055537-fb4f5f`) was auto-discovered by `relay_observe.py status` (`running`, task 1/1, owner alive) and followed with `timeout 8 python3 scripts/relay_observe.py follow`. The monitor printed the new mission header (`── missione m-20261022T055533Z-e4cec8 · compito 1/1 · running · claude`), the session/turn line and that turn's Claude tool calls, results and assistant messages in order, each bounded to one line. It exited cleanly (status 0) and the owner turn continued. This completes the live part of acceptance 3.

## Host Slack delivery (acceptance 2)

Run on the trusted WSL host, outside the sandbox, on 2026-10-22 by the maintainer's direct host session (mandate `L20261022085842-e05d`). The code was `impl/205-relay-observability` rebased onto master `260ed2a6` (head `eb11544b`); `scripts/`, `backend/` and `.github/` are byte-identical to the reviewed head `aa74de6d`. The working directory was the main checkout, so the commands read the live owner state.

- Webhook file `~/.config/jarvis/slack_webhook_url`: present, mode `600`, owner `thera`; its directory is mode `700`. Its content was not read or printed.
- The owner had been stopped gracefully just before (`relay_continuity.py stop`, 08:57:36Z) with roadmap mode paused at cycle 6.
- `08:59:36Z` `notify-test --digest`: printed `sent`, exit 0. `sent` means the webhook POST returned HTTP 2xx with no redirect (`post_webhook` returns no error class). Delivered text:

  ```
  *JarvisOS — aggiornamento delle 22/10 10:59*
  *In corso:* roadmap in pausa.
    motivo: il coordinatore ha chiesto una decisione (RELAY_STATUS blocked)
    perché: roadmap autonoma attiva (ciclo 6) per far avanzare lo sviluppo di JarvisOS/BlueRev senza supervisione continua.
  *Fatto dall'ultimo aggiornamento:*
    • nessun risultato nuovo registrato.
    ultimo turno (blocked): No authorized independent work remains: spec 205/PR #869 (Slack link markup shown here as plain `#869`) needs the maintainer's host-only Slack proof before it can merge, […]
      – git ls-remote: master 260ed2a6, impl/205-relay-observability aa74de6d, impl/165-bluecad-print-handoff 3a3d47ad
      – gh pr view 869: OPEN at aa74de6d, no new comments
      – STATUS non-merged: 062 blocked, 165 in_review, 205 ready, 206 ready (dep 205)
  *Prossimo:* Maintainer: spec 205 acceptance 2 host step (notify-test --digest/--alert, record the output, enable jarvisos-relay-watch.service)
  *Serve intervento:* roadmap in pausa: il coordinatore ha chiesto una decisione (RELAY_STATUS blocked)
  ```

- `08:59:37Z` `notify-test --alert`: printed `sent`, exit 0. Delivered text:

  ```
  :red_circle: *JarvisOS — serve intervento* (22/10 10:59)
  prova di allerta (nessun incidente reale): questo è il formato degli avvisi urgenti.
  La domanda è registrata nel ledger (`devctx.py recover`).
  ```

What this proves: Slack's incoming-webhook endpoint accepted both semantic messages. What it does not prove: the session had no Slack read access, so it did not independently confirm that the messages appear in the channel. The digest links the PR as `issues/869`, which GitHub redirects to the pull request.
