# 201 — Supervised Relay control plane

State: **ready** (live state in [`STATUS.md`](STATUS.md)). Maintainer mission [#840](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/840), ordered P0 on 2026-10-19. Depends on 195 and 197. Readiness was granted by the maintainer's 2026-10-20 approval of decisions D1–D3 (ledger directive `L20261020085928-0431`), recorded with the verified profile under [Readiness decision](#readiness-decision-2026-10-20).

## Outcome

After one-time setup, an operator can submit an ordinary, already-authorized JarvisOS maintenance or development mission through a supported terminal entrypoint and leave. One durable control-plane owner advances its remaining tasks, selects Claude or Codex when quota or transient failures require it, and reports real state. The operator decides strategic and scientific outcomes, spending, credentials, security and destructive risks; routine provider switching and shell diagnostics do not require operator action.

## Recovered starting point (2026-10-19)

- Relay v0.7.7's interactive `relay` shell owns `/use claude` turns. The existing `relay_continuity.py watch` only notifies; it never assumes ownership of that shell. The spec 195/197 `run --session` supervisor owns only a separately started chain, and its current state is held on `20261018-215555-4f193a/turn-006` for `effects_uncertain`. That hold and all worktrees remain intact.
- The Relay daemon and its hooks record events and snapshots, but do not launch a successor coordinator. PRs #833 and #839 are merged and solve incident reconciliation within a supervised chain, not transfer of an interactive REPL.
- Relay's REPL launched a fresh Claude turn with `--permission-mode auto` on this workstation; `git status` and `python3 scripts/devctx.py recover` both succeeded in turn `20261019-185815-bd0b4d/turn-001`. In `default` mode, an unlisted compound Bash command was denied without an interactive Relay approval prompt. Headless `relay run` uses `default` plus Relay's approval hook, as recorded in spec 195; its ability to execute real implementation work needs a separately proved bounded grant.
- An isolated headless Relay probe under `~/jarvis-control/work/relay-permission-probe-20261019` separated built-in safe commands from explicit grants. `git status --short` succeeded even with empty Relay allow patterns (`20261019-190701-442b4b`), so that call proves no grant. Unlisted `python3 -c "print(42)"` was refused with “This command requires approval” (`20261019-190623-536ceb`); a Relay `[claude.allow]` pattern did not change that result (`20261019-190722-f6a329`). The same Python command succeeded when the scratch project's Claude `settings.local.json` allowed it (`20261019-190758-f43885`). Bounded project rules are a viable candidate, but the exact implementation command surface and Relay hook interaction remain a readiness item.
- Setting `AGENT_RELAY_CLAUDE_PERMISSION_MODE=auto` for a scratch `relay run` still launched Claude in `default` and refused that Python call (`20261019-190958-a65cf9`). The environment variable does not turn the supported headless runner into the REPL's `auto` profile on this installed version.
- A local spec 196 keeper branch and worktree contain tmux keystroke injection. They are preserved as WIP, but that mechanism conflicts with the explicit #840 boundary and is not a candidate for this slice.
- The observed shell lacked `XDG_RUNTIME_DIR`, so a bare `systemctl --user` reported “No medium found.” With `XDG_RUNTIME_DIR=/run/user/1000`, the user manager showed `agent-relay.service` enabled and running since 2026-10-16. `loginctl` reported `Linger=no`; a tmux `relay-watch` was also running. Boot and user-session ownership still require actual workstation proof, but the user manager itself is available.

## Ownership direction

Make supervised task submission the canonical entrypoint for future unattended missions. The existing continuity supervisor remains the single execution owner and Relay remains the turn executor and journal owner. A submitted mission enters the supervisor through a supported CLI or a small operator front-end that calls it; it does not type into, attach to, or take over a live REPL. The entrypoint must make its ownership and limitations clear. An already-running REPL can hand off only at a proven quiescent turn boundary with an atomic ownership transition; otherwise it stays independent and the supervisor waits.

This direction reuses 195/197 classification, locks, side-effect reconciliation, provider limits and notifications. Add only the durable task/mission state needed to continue after successful turns. A model's statement that work remains is advisory; task completion and promotion use explicit operator directives or deterministic state. The supervisor must never select a new product goal from free-form model output.

## Acceptance boundary

1. A submitted mission is durable before the first provider launch. At most one coordinator owns it across process restart. An interrupted launch is adopted or held from observable evidence; it is not blindly repeated.
2. Claude quota or a provider transient is classified from raw turn evidence. Codex takes over when available under a **confirmed bounded execution profile**, preserving the remaining task and the 195/197 side-effect gate. A later Claude return follows current availability and the same authority limits.
3. Successful turns advance only the accepted queued work. A terminal prompt or a single success does not silently end a mission with remaining tasks. Waiting, held, complete and active states are distinct and visible.
4. No concurrent REPL and supervisor writers act on the same mission. No terminal keystroke injection, tmux self-drive, duplicate worktree/PR, direct master push, branch-protection change, blanket hold release, or authority widening through a fallback provider.
5. The current `effects_uncertain` hold and spec 196 WIP are preserved until exact evidence supports a separate reconciliation decision. Existing sessions and worktrees are never deleted or silently reset during setup.
6. The one-time workstation installation has an explicit start/restart owner and can be rolled back without losing task or Relay journals. Slack reports the owner, provider, remaining task, wait/reset or hold reason using sanitized fixed fields.
7. Real workstation acceptance exercises the supported user entrypoint, a forced Claude quota with safe Codex takeover in a distinct process, one effect per operation after restart, provider return, remaining-task continuation, and an ambiguous external effect that genuinely holds. Fake tests alone do not establish these facts.

## Readiness work

Before changing the product or service path, resolve and record: the exact task-submission and owner-transition protocol; a bounded headless Claude/Codex authorization profile verified with real tool calls; the actual host restart mechanism and `Linger=no` implications; and a non-destructive way to fault-inject quota and restart against isolated state. These are authority and environment boundaries, so a staged readiness decision is warranted. The coordinator chooses the smallest implementation that passes them; no general queue bus, REPL automation, new provider credentials or repository-administration authority is implied.

## Readiness findings (2026-10-19, workstation, real tool calls)

All probes ran in isolated scratch repositories under `~/jarvis-control/work/` (no remote, nothing pushed). Transcripts and settings are in `~/jarvis-control/work/evidence/201/`. Stray files that the probes created outside their scratch roots were removed.

### Headless Claude through `relay run`

- Relay launches Claude in `default` mode and honours the scratch project's `.claude/settings.local.json` (session `20261019-201929-374a91`).
- A bare `Write` allow rule let Claude write outside the project and outside `additionalDirectories` (`/home/thera/p201-outside.txt`). An unscoped `Edit`/`Write` grant is therefore unacceptable.
- With path-scoped rules (`Edit(/**)`, `Write(/**)` relative to the project, plus `//abs/**` for an extra root), writes inside both roots succeeded. A write to `$HOME` was refused as ungranted, a `~/.claude/**` deny was enforced, and a shell redirection outside the working directories was refused (`20261019-202029-3313c1`). `Bash(git commit:*)` matched `git commit -m`, but not `git -c … commit`, because rules match by literal prefix. `gh pr merge` under a deny rule and unlisted `curl` were both refused.
- An allowed interpreter is an escape hatch. With `Bash(python3:*)` allowed, `python3 -c "open('/home/thera/…','w')"` wrote outside every granted root. Permission rules are guardrails, not containment.
- With Claude's own `sandbox.enabled: true` (Linux bubblewrap), Bash was **not** confined in a headless `relay run`. The Python write outside the project still succeeded, and `git ls-remote` still required approval. `bwrap` is installed, but `socat` is not. This setting is not a usable boundary on this host as installed.

### Headless Codex

- Relay launches Codex with `-a never -s workspace-write`. The OS sandbox refuses writes outside the writable roots (earlier proof `L20261019191627-0fbf`).
- A project-scoped `.codex/config.toml` in a **trusted** project is honoured. `[sandbox_workspace_write] writable_roots` and `network_access = true` showed up in the session header (`workspace-write [workdir, /tmp, $TMPDIR, /tmp/p201-extra] (network access enabled)`). The extra-root write and `git ls-remote https://github.com/…` both succeeded. Without such a file, a Codex fallback could not write the sibling implementation worktrees under `~/src/worktrees/`, commit into the main checkout's `.git`, or reach GitHub. That makes a Codex takeover able to analyse but unable to deliver.

### OS boundary candidate

- Unprivileged `bwrap --ro-bind / / --bind <root> <root>` works on this host: a write inside the bound root succeeded and a write elsewhere failed with `Read-only file system`. A supervisor that wraps its own `relay run` invocation in such a namespace would give both providers one deterministic filesystem boundary that the model cannot negotiate. The interpreter escape above would then be contained. The coordinator session's auto-mode classifier refused to launch a Relay turn under `bwrap` (`[Auto-Mode Bypass]`). That attempt is not proven and needs explicit maintainer authorisation before any probe or use.

### Service lifecycle

- After the 2026-10-19 reboot, `agent-relay.service` (user unit) was active again. The tmux `relay-watch` notifier did **not** survive: there was no tmux server. A process held by tmux is therefore not a restart owner.
- The user manager needs `XDG_RUNTIME_DIR=/run/user/1000`, and `Linger=no`. Without lingering, user units run only while a user session exists. Under WSL, that is while the distribution is started by a login. The proposed owner is a `systemd --user` unit with `Restart=on-failure`. Starting it without an interactive login requires `loginctl enable-linger thera`, a host change reserved to the maintainer.

### Fault injection without touching real state

The supervisor already takes its control root and repository from `control_root()` and `repo_root()`. The spec 197 commissioning ran against an exact no-remote copy. Quota can be injected in a real distinct process by prepending a fixture directory to the supervisor's `PATH` only in the acceptance harness. That directory holds a `claude` shim that emits a recorded quota-limit stream and exits; Codex stays real, under the bounded profile. Restart is injected by killing the supervisor process group mid-turn and restarting the unit. No production state, credential or the held session `20261018-215555-4f193a` is used.

## Proposed protocol (for the readiness decision)

1. **Submission.** `relay_continuity.py submit --mission-file M` validates a mission and writes it atomically to `<control>/missions/<id>.json`, with a `mission_submitted` journal record, before anything launches. A mission has an id, its authority (directive ledger id), the repository, and an ordered list of explicit tasks. Free text is screened for secrets as `--task-file` is today. Only one mission is active; the others wait in FIFO order, visibly.
2. **Single owner.** A `serve` loop under the existing `supervisor.lock` (kernel flock, released on death) is the only executor. It reuses the spec 195/197 state, journal, pending-attempt adoption, side-effect gate, reconciliation, provider choice, limits and notifier unchanged. Each task launch records `mission`, `task` and the attempt nonce.
3. **Advancement.** A task completes only on a deterministic `success` turn outcome and its optional declared read-only check, such as `gh pr view N` state or file presence. A model's claim that work remains or is done is advisory. Success with tasks left launches the next task. The last task's success completes the mission. Wait, hold, active and complete are distinct states, shown by `status` and sent to Slack as fixed fields (owner, provider, mission, task index, reason, reset).
4. **REPL independence.** The supervisor never types into, attaches to or adopts a live REPL. `submit --continue-session S` binds a mission to an existing chain only when that chain's last turn is terminal and the spec 195 live-work check finds no running coordinator or worker for the repository. Otherwise it waits (`repl_active`/`live_work`). The `effects_uncertain` hold on `20261018-215555-4f193a` stays untouched.
5. **Execution profile.** It is applied by the supervisor and project files, not requested from the model. The profile is:
   - Codex: a project `.codex/config.toml` with the repository, `~/src/worktrees` and `~/jarvis-control/work` as writable roots, plus network.
   - Claude: project rules with path-scoped `Edit`/`Write` for the same roots and a bounded Bash list. That list covers git except push to `master` or force, `gh pr create|view|checks|list`, tests, build, lint and `devctx`. Denies cover `gh pr merge`, branch-protection or admin API calls, force pushes, and edits to `~/.claude`, `~/.codex`, `~/.relay` and credentials. Optionally, the `bwrap` wrapper above contains the interpreter escape.
   Merging, credentials and host changes stay with the maintainer.

## Readiness decision (2026-10-20)

The maintainer approved D1–D3 on 2026-10-20 with these boundaries. They are binding for the implementation slice.

- **D1, execution profile.** Approved: a bounded headless profile for Claude and Codex, made of scoped project permissions and verified OS-level bubblewrap isolation. The following are excluded: blanket filesystem access, global permission bypass, secret exposure, uncontrolled subprocess execution, direct pushes to `master` and any weakening of security. Supervised writes may be enabled only after the sandbox has been verified with real isolated Claude and Codex tool calls.
- **D2, restart owner.** Approved: one persistent control-plane owner as a `systemd --user` service, with safe restart, explicit ownership, journaling and rollback. The scoped user-service setup and `loginctl enable-linger` are authorized if they are demonstrably needed. Authentication is not bypassed, and no unrelated privileged change is made. WSL start after a Windows reboot needs separate verification.
- **D3, protocol.** Approved: the protocol proposed above is the implementation direction.

### Verified profile (real tool calls, 2026-10-20)

Probes ran in scratch repositories under `~/jarvis-control/work/evidence/201-sandbox/`, through `agent-relay run` wrapped in unprivileged `bwrap` (no remote, nothing pushed). The wrapper mounts `/` read-only and binds read-write only the mission roots, the repository's common Git directory and the providers' own state directories. It gives the run a private `/tmp`. It hides `/run/user` (user bus), `/run/WSL` (Windows interop) and secret configuration directories. It also unshares the PID, IPC and UTS namespaces and starts a new session.

- **Claude** (`20261020-090503-cba6f1`, launched in `default` mode with project rules). A `Write` inside the repository succeeded. An *allowed* `python3` writing to `$HOME` failed with `Read-only file system`, so the interpreter escape seen on 2026-10-19 is contained. The Slack webhook directory was empty inside the sandbox.
- **Codex** (`20261020-091617-d9b332`). With Codex's own `workspace-write` nested inside `bwrap`, writes were contained. That mode always mounts `.git` read-only, so Codex cannot commit in it. With `danger-full-access` *inside* `bwrap`, Codex committed in a linked worktree (`76465fe`), reached GitHub through `git ls-remote`, and its `$HOME` write failed with `Read-only file system`. The profile therefore uses `bwrap` as the single enforced filesystem boundary for both providers. Claude's project rules and a `gh` guard on `PATH` remain guardrails, not containment.
- **Installed workstation boundary (2026-10-20, maintainer directive `L20261020120919-38dd`).** The prototype's `--ro-bind / /` still let the run *read* personal files, so it was replaced by `jarvis-sandbox` (`~/.local/share/jarvisos-sandbox/`, outside every sandbox-writable root). It builds a fresh root: system toolchain read-only; the canonical checkout with its shared `.git`, the JarvisOS worktree roots and `~/jarvis-control` read-write; `.git/config`, `.git/hooks`, the checkout's `.claude/settings*.json` and `.agent-relay/permissions.toml` read-only; sandbox-only Claude/Codex/gh state; an allowlisted environment (`env -i`); user/PID/IPC/UTS/cgroup namespaces with `--die-with-parent`. Personal dotfiles, host `~/.claude`, `~/.config` secrets, unrelated repositories, `/mnt/*`, `/run/WSL`, `/run/user` and host `/tmp` are absent rather than read-only. Its suite (`selftest.py`, 46 checks: nested Python writes, nested user-namespace unmount attempts, PE execution through WSL interop, `sudo`, `systemd-run`, a detached `setsid` daemon reaped after exit, a linked-worktree commit) passed. It certifies the launcher's sha256. Bypass permissions are granted only while that hash matches. A real `bypassPermissions` Claude session inside the boundary then found all 16 sensitive paths absent. Writes outside the roots by nested Python and by the `Write` tool failed with `Read-only file system`. The same session committed in a linked worktree, ran pytest and a `vite` build, and reached GitHub. A Codex `relay run` turn (`danger-full-access` inside the boundary) committed, reached GitHub and was refused by `Read-only file system` outside the roots. The full backend suite ran inside the boundary at `0d6a68ae`: 4374 passed and 43 skipped. Headless `relay run` under `systemd-run --user` and an interactive session killed through a tmux disconnect both left no surviving process. Evidence: `~/jarvis-control/work/evidence/sandbox-bootstrap/`.
- **Escape routes.** `cmd.exe` and `powershell.exe` (WSL interop) failed and left no file on `C:`. `systemd-run --user` could not reach the bus.
- **Launch hang.** `codex exec` waits on an inherited open stdin, so the supervisor launches every run with `/dev/null` as stdin.
- **Fresh Codex reading.** Relay reads Codex quota only from Codex's own rollouts, so the reading goes stale on an idle host (13 h observed). A minimal read-only Codex turn refreshed it. Before the supervisor switches to Codex without a fresh reading, it runs one such probe instead of refusing the failover.

### Residual risks accepted for this slice

- GitHub authority inside the boundary is a fine-grained token restricted to this repository: Contents, Pull requests and Issues read-write; Actions, Checks and Statuses read-only; no Administration. The model can use it for anything those permissions allow in this repository, including exact-head merges, which the maintainer authorized on 2026-10-20. It cannot reach other repositories or repository administration. The broad host `gh` OAuth token never enters the boundary, and the suite fails if it does.
- Direct pushes to `master` are refused server-side by the active `master` ruleset, which requires status checks and has no bypass actors.
- Refs in the common Git directory are writable, which branch creation needs. `.git/config` and `.git/hooks` are bound read-only, so `push -u` and `gh pr checkout` cannot record tracking config.
- Content written inside the boundary is trusted by anything that later runs it outside: host services that execute project venvs, and host-side `git` whose worktree metadata the sandbox can rewrite. All agent and control-plane execution therefore goes through the launcher.
- The network namespace is shared, so GitHub, package registries, localhost JarvisOS services and the Windows host network are reachable.
- Claude and Codex login files are bind-mounted read-write, because each provider must authenticate.

### Host lifecycle

The `systemd --user` manager is running. Without lingering, though, user units stop when the last login session ends. The owner unit uses `KillMode=process`, so stopping or restarting the service never kills a running provider turn. The restarted supervisor adopts that turn through its pending-attempt record and waits for it. Linger is enabled only once it is demonstrated to be needed for running without a login session.

## Implementation evidence (2026-10-20, isolated workstation runs)

Real provider processes ran inside `jarvis-sandbox` against a no-remote copy of the repository with separate control roots. Only Claude's first launch was replaced by a recorded real quota stream on `PATH`. Evidence: `~/jarvis-control/work/evidence/201-live-20261020/RESULT.md`.

- **Takeover and advancement.** A real Claude quota led to a Codex takeover, and Codex completed both remaining tasks. Their path checks passed (`control2`).
- **Owner death.** The owner was killed with SIGKILL during a live Codex turn. The replacement waited (`repl_active`) and then adopted that attempt by nonce. One task completion was recorded, with no relaunch (`control3`).
- **Return to Claude.** After the quota, Codex did task 1. The owner was stopped at the task boundary and restarted after the 20-minute dwell. Claude then took task 2, continuing the Codex session (`control5`). A wait for Claude's own reset also returned to Claude (`control4`).
- **Ambiguous effect.** Claude was killed during a Bash call that had sent an external POST. The turn settled as `crash` with `curl POST` in flight and held `effects_uncertain`. The next task never launched (`control6`).
- **Live-work protection.** A stray process in the checkout held the mission rather than launching beside it. A stop request survived restart until `serve --clear-stop`.
- **Launcher independence.** The first run from a Claude shell exposed three defects. `CODEX_HOME` was inherited (unset), Relay read Claude limits only from `~/.claude`, and the quota probe was `--ephemeral`, so no Codex reading ever appeared. Together they left a Codex takeover unconfirmed and made a confirmed return impossible. The owner now pins both provider logins, links Relay's Claude credential path inside the sandbox home, and runs a non-ephemeral probe.

- **Cross-instance exclusion.** Each `jarvis-sandbox` instance unshares the PID namespace, so the owner's process-table scan could not see a REPL in another instance. `relay` now holds a shared coordinator lease (flock) for the lifetime of every coordinator invocation, and the owner waits while that lease is held. A lease taken in a nested PID namespace was seen from outside it and released on exit. The owner also pins the sandbox's `gh` login and git credential helper, which a session launched without them could not use.

Still to prove on the host: the `systemd --user` owner and its restart (installation is a host step, because the sandbox hides the user bus and host `~/.config`), and pushing, PR and merge through the scoped GitHub token, which is not yet mounted in the sandbox.
