# 201 — Supervised Relay control plane

State: **planned**. Maintainer mission [#840](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/840), ordered P0 on 2026-10-19. Depends on 195 and 197. This document records the outcome and the ownership direction; it does not grant implementation authority until a separate readiness decision resolves the authority and workstation proof boundaries below.

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

## Decisions requested from the maintainer

- **D1 (security):** approve the bounded headless execution profile in protocol item 5: Codex project config plus scoped Claude rules. State whether the supervisor may also wrap its Relay launches in `bwrap`. That is recommended, because Claude rules alone do not contain an allowed interpreter.
- **D2 (host):** approve `loginctl enable-linger thera` and a `jarvis-control-plane` user unit as the restart owner, or name another start owner.
- **D3:** approve this protocol as the readiness for an implementation slice (`ready`). The real-workstation acceptance in boundary item 7 then runs under the approved profile.
