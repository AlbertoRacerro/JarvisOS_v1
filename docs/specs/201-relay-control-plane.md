# 201 — Supervised Relay control plane

State: **planned**. Maintainer mission [#840](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/840), ordered P0 on 2026-10-19. Depends on 195 and 197. This document records the outcome and the ownership direction; it does not grant implementation authority until a separate readiness decision resolves the authority and workstation proof boundaries below.

## Outcome

After one-time setup, an operator can submit an ordinary, already-authorized JarvisOS maintenance or development mission through a supported terminal entrypoint and leave. One durable control-plane owner advances its remaining tasks, selects Claude or Codex when quota or transient failures require it, and reports real state. The operator decides strategic and scientific outcomes, spending, credentials, security and destructive risks; routine provider switching and shell diagnostics do not require operator action.

## Recovered starting point (2026-10-19)

- Relay v0.7.7's interactive `relay` shell owns `/use claude` turns. The existing `relay_continuity.py watch` only notifies; it never assumes ownership of that shell. The spec 195/197 `run --session` supervisor owns only a separately started chain, and its current state is held on `20261018-215555-4f193a/turn-006` for `effects_uncertain`. That hold and all worktrees remain intact.
- The Relay daemon and its hooks record events and snapshots, but do not launch a successor coordinator. PRs #833 and #839 are merged and solve incident reconciliation within a supervised chain, not transfer of an interactive REPL.
- Relay's REPL launched a fresh Claude turn with `--permission-mode auto` on this workstation; `git status` and `python3 scripts/devctx.py recover` both succeeded in turn `20261019-185815-bd0b4d/turn-001`. In `default` mode, an unlisted compound Bash command was denied without an interactive Relay approval prompt. Headless `relay run` uses `default` plus Relay's approval hook, as recorded in spec 195; its ability to execute real implementation work needs a separately proved bounded grant.
- An isolated headless Relay probe under `~/jarvis-control/work/relay-permission-probe-20261019` confirmed one narrow grant: `[claude.allow] patterns = ["Bash(git status)"]` let `git status` execute in a real `default` mode Claude turn (`20261019-190533-2a79b7`), while unlisted `python3 -c "print(42)"` was refused with “This command requires approval” (`20261019-190623-536ceb`). This proves the mechanism can be bounded, not that its current allowlist is sufficient for implementation.
- A local spec 196 keeper branch and worktree contain tmux keystroke injection. They are preserved as WIP, but that mechanism conflicts with the explicit #840 boundary and is not a candidate for this slice.
- The Linux user service bus was unavailable in the observed shell (`systemctl --user` reported “No medium found”). A tmux `relay-watch` was running. Restart and reboot ownership therefore require actual workstation proof, not a service-file assumption.

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

Before changing the product or service path, resolve and record: the exact task-submission and owner-transition protocol; a bounded headless Claude/Codex authorization profile verified with real tool calls; the actual host restart mechanism (including the unavailable user bus); and a non-destructive way to fault-inject quota and restart against isolated state. These are authority and environment boundaries, so a staged readiness decision is warranted. The coordinator chooses the smallest implementation that passes them; no general queue bus, REPL automation, new provider credentials or repository-administration authority is implied.
