# Spec 207 implementation

The executor uses the shared request spool and host-only policy/state/key. Requests are consumed without following symlinks, validated, executed serially and receipted with canonical JSON and an Ed25519 SSH signature. The durable done set republishes deleted receipts without re-execution; restart recovery preserves completed receipts and marks unfinished actions interrupted. Oversized and symlinked requests receive signed refusals. Policy reloads before each request and unknown operations or unsafe policy permissions fail closed.

Installation checks GitHub's `sha...master` comparison (`ahead` or `identical`), downloads the commit tarball, rejects absolute/traversing paths and links/devices, extracts only `scripts/` into a staged release and atomically flips `current`. Executor and watcher units use that release under `python3 -I`; their imports resolve siblings by explicit installed file paths. The watcher reads the repository from its working directory. The executor has privilege/resource limits and restarts on release-update exit 75.

Default control permits the watcher and mission owner, watcher template installation, and the spec 165 Windows handoff directory. Screenshot Chromium and registered benchmarks run through the sandbox launcher with plain argv and subprocess working directories. `release.install` stays refused until the host policy explicitly sets `trust_master: true`; once enabled it checks master ancestry, installs, restarts an active watcher, publishes the receipt and exits for executor restart. A failed watcher restart produces a failed receipt but still switches the executor to the installed release.

Supervisor contracts accept `host_receipt` with a known operation and optional full commit SHA; only verified `ok` receipts satisfy it. A settled blocked coordinator's final reply may contain `HOSTOPS-WAIT: <32hex>` markers. Roadmap saves those IDs and resumes only after every receipt verifies, regardless of outcome. Unmarked blocked pauses and explicit `roadmap start --authority` retain their behavior. The observer reports `hostops_down` in Italian when an old pending request and missing/stale heartbeat coincide (both thresholds two minutes).

## Verification so far

Offline tests use temporary homes, fake host commands/webhooks and real `ssh-keygen` Ed25519 signatures. They cover request validation/time/size/symlink boundaries, policy refusals, replay/republication, recovery, cancellation, forgery by edit/rename/foreign key, Slack filtering, operation refusals, sandbox argv, release extraction/master checks, copied release imports under `-I`, completion contracts, roadmap resumption and observer incidents. Final validation from `backend/`:

```bash
/home/thera/src/JarvisOS_v1/backend/.venv/bin/python -m pytest -q tests/test_host_ops.py tests/test_relay_observe.py tests/test_relay_continuity.py
/home/thera/src/JarvisOS_v1/backend/.venv/bin/python -m ruff check tests/test_host_ops.py tests/test_relay_observe.py tests/test_relay_continuity.py ../scripts/host_ops.py ../scripts/relay_continuity.py ../scripts/relay_observe.py
```

Result: **573 passed, 1 skipped** (existing opt-in real Codex CLI test), one dependency deprecation warning; Ruff passed. `git diff --check` passed. The absolute interpreter path resolves the requested shared virtualenv; the supplied relative path does not resolve when invoked from this worktree's `backend/`.

Real host acceptance is **pending**: no services, credentials, WSL, webhook, GitHub or host installation were accessed by the constrained worker. Acceptance 3–5 require the coordinator/maintainer host session after merge. No receipt IDs or host proof are claimed here.

## Host installation (maintainer, once)

From a trusted host shell in the merged repository, substitute the actual merged master SHA:

```bash
python3 scripts/host_ops.py install --sha <merged master sha> --with-watch
python3 -I ~/.local/share/jarvisos-hostops/current/scripts/host_ops.py health
```

Without `--with-watch`, installation writes the watcher unit but does not start it. The executor is enabled and restarted. Existing host policy and signing keys are preserved. Host-only policy: `~/.config/jarvisos-hostops/policy.json`; retain owner-only write permission. Verify the configured Chromium binary and registered benchmark interpreter exist on this host.

From the sandbox, collect and verify host acceptance receipts:

```bash
python3 scripts/host_ops.py request service.install --args '{"template":"jarvisos-relay-watch"}' --wait 90
python3 scripts/host_ops.py request slack.deliver --args '{"text":"Spec 207: verifica host completata"}' --wait 30
python3 scripts/host_ops.py request wsl.probe --wait 60
python3 scripts/host_ops.py request service.status --args '{"unit":"jarvisos-mission-owner.service"}' --wait 30
python3 scripts/host_ops.py request service.status --args '{"unit":"unapproved.service"}' --wait 30
python3 scripts/host_ops.py verify <receipt-id> --op service.status
```

Record receipt IDs, outcomes and the edited-receipt rejection here during host proof. `verify` returns zero only for a verified `ok` receipt. At final handoff, start the persistent owner through `service.control` and observe its first roadmap cycle with `relay_observe.py status`; record the real result.

Rollback (host shell; preserve audit state):

```bash
systemctl --user disable --now jarvisos-hostops jarvisos-relay-watch
rm ~/.config/systemd/user/jarvisos-hostops.service ~/.config/systemd/user/jarvisos-relay-watch.service
systemctl --user daemon-reload
```

Keep `~/.local/share/jarvisos-hostops/state` and `~/jarvis-control/work/hostops/` for audit. To return to a previous code release, rerun `install --sha <previous master sha> --with-watch` from trusted host code. Rollback is documented here and has not been executed by the constrained worker.
