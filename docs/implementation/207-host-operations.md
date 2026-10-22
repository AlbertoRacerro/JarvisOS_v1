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

From a trusted host shell. Do **not** run `scripts/host_ops.py` from the checkout: the sandbox can write it. Fetch the installer from GitHub at the merged master commit instead (`SHA` = the full merge commit):

```bash
SHA=<full merged master sha>
d=$(mktemp -d) && gh api -H 'Accept: application/vnd.github.raw' \
  "repos/AlbertoRacerro/JarvisOS_v1/contents/scripts/host_ops.py?ref=$SHA" > "$d/host_ops.py" \
  && sha256sum "$d/host_ops.py" \
  && python3 -I "$d/host_ops.py" install --sha "$SHA" --with-watch \
  && python3 -I ~/.local/share/jarvisos-hostops/current/scripts/host_ops.py health
```

`install` verifies again that `SHA` is on GitHub master, then installs the whole `scripts/` tree of that commit as the release.

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

## Security review (merge gate)

Implementation by Codex (`8670dab5`). The coordinator (Claude) reviewed it against the spec 207 threat model: the agent controls everything it can write in `jarvis-sandbox`, including the spool, checkout, worktrees, control state and transcripts. A second Codex instance was asked for an independent adversarial review. OpenAI's safety classifier refused that request ("possible cybersecurity risk"), so it produced no report. Per directive `L20261020120919-38dd`, the refusal was not worked around.

Each item below gives the threat, then the conclusion.

- **Host code provenance.**
  - The executor and the watcher run `/usr/bin/python3 -I` on `~/.local/share/jarvisos-hostops/current/scripts/…`. That path is absent from the sandbox.
  - Sibling modules (`devctx`, `relay_observe`, `host_ops`) load from `Path(__file__).resolve().parent`, which is the release. `-I` drops cwd, `PYTHONPATH` and user site.
  - `install` and `release.install` accept only a commit GitHub reports on master.
  - Tarball extraction keeps only regular files and directories under `scripts/`. It rejects absolute paths, `..` and links.
- **Host git in the agent-writable checkout** (the watcher's `fetch`, `rev-parse` and `log`). `.git/config` and `.git/hooks` are read-only bind mounts in the sandbox, and `.git` cannot be renamed because it contains mount points. Hooks, fsmonitor, filters and includes are therefore all fixed by host-controlled config. No execution vector was found.
- **Receipt forgery and substitution.**
  - Signatures are made with the host-only key and checked against the published `allowed_signers`, which is a read-only mount in the sandbox. The receipt's `request_id` must equal its file name.
  - Tests cover an edited receipt, a receipt copied to another id and a signature by another key.
  - `host_receipt` and the `HOSTOPS-WAIT` resume use the same verification.
  - A `host_receipt` contract without `sha` accepts any earlier `ok` receipt for that operation, so contracts that need fresh evidence must name the commit.
- **Spool races.**
  - Every spool, outbox and screenshot access goes through no-follow, descriptor-anchored walks. A swapped directory makes the operation fail closed (DoS only).
  - Fixed in review: the screenshot temp file was unlinked by pathname. It is now unlinked through its verified descriptor.
- **Privilege surface.**
  - The operation catalogue is closed.
  - Units come only from templates.
  - The mission owner is start-only (`68ad55dd`), because stop or restart would kill a running provider turn.
  - `bench.run` and `browser.screenshot` execute inside `jarvis-sandbox`.
  - `release.install` is off unless the maintainer sets `trust_master`.
  - A policy that is unknown, wrong-owner or group/world-writable disables every operation.
- **Secrets.** The webhook URL is never put in a receipt, log or error class. Slack text is filtered: no markup except links to this repository's issues/PRs, and secret patterns rejected. Receipt output is scrubbed and bounded.

Residual risks, accepted:

- Slack messages through `slack.deliver` are agent-authored, filtered and capped at 6 per hour, and carry a `host-ops` header.
- An agent can deny service by deleting spool entries. The host keeps the signed done set and republishes receipts.

## Host activation acceptance (activation gate, 2026-10-22)

The maintainer installed release `46ee670ab2555e6f67f331c3b40d60e159e2f56d` from a host shell. At 12:45:21Z `jarvisos-hostops.service` and `jarvisos-relay-watch.service` were active and `health` reported healthy. Everything below ran **from inside `jarvis-sandbox`** against the real executor, and every receipt was checked with `host_ops.py verify` against the published key. Request logs are in `~/jarvis-control/work/evidence/207-host/` (`run.log`, `forgery.log`, `recovery.log`).

**Acceptance 3: authorized operations, verified `ok` receipts.**

| Request | Operation | Result |
| --- | --- | --- |
| `ae0c2641…` | `service.status` executor | active/running, enabled, 0 restarts |
| `dd201044…` | `service.status` watcher | active/running, enabled, 0 restarts |
| `b7085c22…` | `service.status` owner | inactive/dead, exit 0 (stopped by STOP) |
| `b38640e0…` | `wsl.probe` | WSL kernel, interop registered, `explorer.exe` present, Windows 10.0.26200, handoff dir `C:\Users\thera\JarvisOS-print` reachable |
| `83205526…` | `service.install` watcher | `changed: false`: the installed unit is byte-identical to the release template, which runs `current/scripts/relay_continuity.py` under `python3 -I`, not the checkout |

**Denied operations, verified `refused` receipts.** Nothing executed in any of these.

| Request | Attempt | Refusal |
| --- | --- | --- |
| `6340428b…` | `service.status ssh.service` | unit not allowed |
| `95ee3c93…` | `service.control` owner `stop` | not allowed (owner is start-only) |
| `f921aa7b…` | `service.control` executor `restart` | unit not allowed |
| `cd64fcdd…` | `release.install` | needs `trust_master` |
| `fc3c42ea…` | `http.smoke` with an external URL | target not in policy |

**Forgery, against real receipts.**

| Attempt | `verify` result |
| --- | --- |
| A refused receipt edited to `"outcome":"ok"` | rejected: signature does not verify |
| A genuine `ok` receipt copied under another id | rejected: receipt is for another request |
| An `ok` receipt re-signed with an agent-generated Ed25519 key (same comment and namespace) | rejected: signature does not verify |
| Appending to the published `allowed_signers` | `Read-only file system` |

The genuine receipt still verified, and the edited one verified again once restored.

**Recovery and replay, live.**

- An agent deleted the published receipt `ae0c2641…` and resubmitted a fresh, valid request with the same id. The executor republished the byte-identical signed receipt (`finished_at` 12:48:02Z unchanged) and did not execute it again.
- A request with a cancel marker written before it was picked up was receipted `cancelled before it started` (`7bbeab9f…`).
- A request dated 08:00Z was `refused` by replay protection (`38d508f5…`).
- In-flight `interrupted` recovery is covered by the offline suite only. Policy does not let an agent restart the executor, by design.

**Acceptance 5: rollback, rehearsed on the watcher.** `service.control` watcher `stop` (`1b6c7e09…`, inactive), then `start` (`042c9b60…`, active, new PID). The watch store kept updating (12:50:31Z) with 0 delivery failures. Dedupe and the digest schedule survived: no message was re-sent. The full executor rollback (`disable --now`, remove the units, keep state) is documented above. It needs a host shell and was not exercised, because disabling the executor is deliberately outside its own policy.

**Watcher, real delivery without test messages.**

- At start (12:45:22Z) the release-based watcher delivered the semantic digest and the real incident alert for the then-paused roadmap (`coordinator_blocked`). The maintainer had already confirmed visibility of spec 205 messages.
- It tracks master `46ee670a`.
- No `notify-test` was sent during activation.

**Acceptance 4: supervisor continuation.**

1. `roadmap start --authority L20261022122708-233d` at 12:51:03Z cleared `coordinator_blocked`.
2. The STOP marker of 08:57:35Z was removed per the runbook.
3. The owner was started from the sandbox through `service.control` (`start`, receipt verified `ok`, active, 12:51:09Z).
4. Within a second it submitted roadmap cycle 7 (`m-20261022T125110Z-1fae56`, authority `L20261022122708-233d`).
5. It then waited on the interactive coordinator's `coordinator.lease`, as spec 201 requires, without launching a turn.
6. Owner liveness was seen from the host side: `serve.lock` was rewritten by the owner, and the host watcher raised no `owner_down` with work pending. `relay_observe.py status` inside a *separate* sandbox instance reports `owner: false`, because `/proc/locks` there only shows locks of its own PID namespace. That is an observation limit of in-sandbox status, not an owner fault.
7. The first autonomous turn starts when the bootstrap session releases the lease.
