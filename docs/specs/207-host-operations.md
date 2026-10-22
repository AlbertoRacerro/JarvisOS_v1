# 207 — Host operations: typed, policy-bound host actions with signed receipts

State: **ready** (live state in [`STATUS.md`](STATUS.md)). Maintainer directive `L20261022085842-e05d` §3 ("Host Operations capability"), confirmed by the AUTONOMY BOOTSTRAP mandate of 2026-10-22. Depends on 201 (the `jarvis-sandbox` boundary), 204 (deterministic task contracts) and 205 (watcher, notifier).

## Outcome

Autonomous development no longer stops at the workstation boundary for routine host work. An agent inside `jarvis-sandbox` submits a structured request for one operation from a closed, typed catalogue. A trusted executor on the host checks it against a host-only policy, performs it and writes a receipt signed with a host-only key. Any agent, the mission owner or a later reviewer can verify that receipt, but nobody inside the sandbox can forge or alter one. Deterministic checks consume the verified receipt, not an agent's statement.

The maintainer authorizes host privileges once, by installing the executor and its policy from a host shell. Afterwards the routine operations below run without human intervention. Anything outside the policy is refused and stays refused until the maintainer edits the policy on the host.

## Trust layout

| What | Where | Sandbox access |
| --- | --- | --- |
| Request spool, published receipts, outbox, heartbeat | `~/jarvis-control/work/hostops/` | read-write |
| Executor code (release per master commit), host state (done set, in-flight marker, journal, unit backups) | `~/.local/share/jarvisos-hostops/` | absent |
| Policy, Ed25519 signing key | `~/.config/jarvisos-hostops/` (mode 700) | absent (the sandbox has its own `~/.config`) |
| Published public key (`allowed_signers`) | `~/.local/share/jarvisos/hostops/` | read-only |
| Slack webhook | `~/.config/jarvis/slack_webhook_url` | absent |

- The executor runs from an installed release, never from a checkout an agent can write. `install --sha` runs from a host shell only. It accepts only a commit that GitHub reports on `master`, downloads the `scripts/` tree of that commit from GitHub and writes it under `releases/<sha>/`, then flips `current` atomically. The release is stdlib-only and runs under `python3 -I`.
- The host-side Slack watcher (spec 205) moves into the same release. Its unit runs `current/scripts/relay_continuity.py watch` with the main checkout only as working directory (read for state), so an agent edit to `scripts/` in the checkout no longer reaches a host process.
- Receipts are canonical JSON plus an SSH signature (`ssh-keygen -Y sign`, namespace `jarvisos-hostops-receipt`). A receipt is valid only if it verifies against the published key and names the request id of its file name. Deleting a receipt from the spool cannot erase it: the host keeps the signed copy in its done set and republishes it when the same id is requested again.

## Requests and execution

- Request: `{schema, id (32 hex), op, args, sha (optional, 40 hex), requested_at, requester}`, at most 64 KiB, no other fields. It is read without following symlinks and consumed (removed from the spool) before execution.
- Replay protection and idempotency: a request older than 1 hour, or more than 5 minutes in the future, is refused. An id already in the done set is never executed again; its receipt is republished.
- One request at a time, oldest first. Every request ends in exactly one receipt with outcome `ok`, `failed`, `refused`, `cancelled`, `interrupted` or `timeout`. A request that was in flight when the executor stopped is receipted `interrupted` on restart and is never re-run.
- Cancellation: `host_ops.py cancel ID` writes a cancel marker. A pending request is receipted `cancelled`. A running `bench.run` is stopped through its systemd scope.
- Timeouts on every host command. The executor unit has `NoNewPrivileges`, memory, task and CPU limits. Benchmarks run in their own systemd scope with policy limits.
- Policy changes take effect on the next request. A policy that enables an operation this release does not know, or that is group/world-writable or owned by someone else, disables every operation (fail closed) and is reported in the heartbeat.

## Operation catalogue (this slice)

Each operation validates its own arguments. Free text never reaches a shell. No operation accepts a command line, a path outside its fixed roots or a URL outside its fixed pattern.

| Operation | Does | Default policy |
| --- | --- | --- |
| `slack.deliver` | Posts a bounded, scrubbed message (no Slack markup except links to this repository's issues/PRs) through the protected webhook; records HTTP status and the text hash. Proves webhook acceptance, not channel visibility. | on, 6/hour |
| `service.status` | `systemctl --user show` for an allowlisted unit. | watcher, owner, executor, `agent-relay` |
| `service.control` | `start`/`stop`/`restart` of an allowlisted unit and waits for the target state. | watcher, owner |
| `service.install` | Writes an allowlisted unit from a template in the release, backs up a differing unit, `daemon-reload`, `enable --now`. | watcher |
| `wsl.probe` | WSL kernel, interop registration, `cmd.exe /c ver`, handoff directory reachability. | on |
| `wsl.handoff` | Copies a file from the spool outbox (regular, no symlink, size and extension limits, matching sha256) to the policy's Windows directory, optionally opens it with `explorer.exe` (argv only, no shell) and lists the Windows processes it started. | on, `.3mf .stl .step .glb .png .pdf` |
| `browser.screenshot` | Headless Chromium inside `jarvis-sandbox` on `http://127.0.0.1:<port>/…`, fixed viewports and colour schemes; the PNG and its hash are in the receipt. | on |
| `http.smoke` | GET of a policy-named loopback target, expected status. | backend health |
| `bench.run` | A policy-registered argv, run inside `jarvis-sandbox` in a systemd scope with memory/CPU/task/time limits, only on a clean worktree whose HEAD equals the request's `sha`. | relay-observe tests |
| `release.install` | Installs a newer master commit as the executor/watcher release and restarts both. | **off** (`trust_master: false`) |

Commands that already work inside the sandbox (tests, builds, Playwright, local benchmarks, loopback HTTP) need no host operation. `browser.screenshot`, `http.smoke` and `bench.run` exist so that host-witnessed evidence is available when a contract requires it.

`release.install` is the one operation that changes which code runs with host privileges. It is off by default: code changes to the host release need the maintainer to run `install --sha` on the host, or to set `trust_master: true` in the policy after deciding that merged master code is trusted at host level. A request while it is off is receipted `refused` with that reason.

## Supervisor integration

- `host_ops.py request OP --args JSON [--sha SHA] --wait N` returns the verified receipt (exit 0 only for `ok`). It is what an agent uses inside a turn.
- `host_ops.py verify ID [--op] [--sha]` is the deterministic check.
- Spec 204 gains a `host_receipt` completion check (`{"kind": "host_receipt", "op": …, "sha": …}`). It is satisfied only by a verified `ok` receipt for that operation and commit.
- When a coordinator turn ends `blocked` with `HOSTOPS-WAIT: <id>` and roadmap mode pauses as `coordinator_blocked`, the owner resumes roadmap mode by itself once that request has a verified receipt (any outcome; the next cycle reads it). Other blocked pauses are unchanged.
- The spec 205 observer reports `hostops_down` when requests wait in the spool and the executor heartbeat is older than 2 minutes.

## Out of scope

- Arbitrary commands, shells, scripts or interpreters on the host; root or `sudo`; system (non-user) units.
- Running candidate (unmerged) code with host privileges. Pre-merge host evidence comes from typed operations or from `bench.run`, which executes inside the sandbox.
- Credentials beyond the existing webhook; new network egress; Windows-side installs; printing; changes to the sandbox launcher or its certified hash.
- Installing scientific solvers, CAD backends or product work.

## Acceptance

Two gates. `install` accepts only a commit already on GitHub master, so no unmerged code ever reaches the host. The merge gate is therefore items 1–2 plus an independent security review. The activation gate (items 3–5) runs on the installed release right after merge and is recorded in the implementation document. STATUS shows `merged` only when both gates are met. Until then the row stays `in_review` and names the pending activation.

1. Tests (offline, temporary home, faked `systemctl`/`wslpath`/webhook, real `ssh-keygen` signing) cover: request validation (schema, extra fields, id, sha, age, future, size, symlinked request file); replay and idempotency (same id never executes twice, deleted receipt republished); in-flight recovery (`interrupted`, not re-run); cancellation before start; every operation's refusal paths (unknown args, units, templates, extensions, sha mismatch, symlinked outbox file, non-loopback URL, unregistered benchmark, dirty or wrong-head worktree, `release.install` off); policy fail-closed (unknown op, bad mode); receipt forgery (edited receipt, receipt renamed to another id, signature from another key) all rejected by `verify`; Slack text filter; and the `host_receipt` check and roadmap auto-resume in `relay_continuity`.
2. `install` refuses inside the sandbox and refuses a commit not on GitHub master; the release contains `scripts/` of that commit only; units reference the release, not the checkout.
3. Real host end to end, recorded in `docs/implementation/207-host-operations.md` with receipt ids: from inside the sandbox, `service.install` of the watcher, `slack.deliver`, `wsl.probe` and `service.status` of the owner return verified `ok` receipts; a request outside the policy returns a verified `refused` receipt; a hand-edited receipt fails `verify`.
4. Supervisor continuation, real: the persistent owner is started through `service.control` from the sandbox at the final handoff, and its first roadmap cycle is observed running (`relay_observe.py status`).
5. Rollback documented and tried: `systemctl --user disable --now jarvisos-hostops jarvisos-relay-watch`, remove the units, keep `~/.local/share/jarvisos-hostops/state` and the spool for audit.
