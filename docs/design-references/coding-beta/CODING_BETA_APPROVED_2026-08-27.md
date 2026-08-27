# Coding beta — approved visual and interaction reference — 2026-08-27

Status: maintainer-approved visual/product reference; not runtime implementation authority.

This file freezes the approved `Coding` workspace composition reached during the 2026-08-27 maintainer visual pass. It supplements `docs/product-direction/04-coding-and-self-development-contract.md`. `docs/specs/STATUS.md` remains the live implementation registry and must be reconciled to the maintainer release recorded separately for the post-100 hold.

## Shared Coding shell

Primary navigation remains exactly:

`Design | Memory | Development | Coding | Settings`

`Coding` owns exactly:

`Repository | Runtime`

The approved warm limestone / near-white operator shell is reused. Normal application typography follows the Inter / Inter Display direction already frozen by the maintainer, with regular/medium weights rather than heavy bold treatment. IBM Plex Mono is reserved for code, paths, hashes, ports and logs. Generic icons remain Phosphor-only where icons are needed.

## Repository

Final approved local HTML identity:

- `coding_repository_beta_mockup_v1.html`
- SHA-256: `56897ca83cb3adb1d0ac74041335b014631f1f819f7457ba86e210aaf65122a7`

Approved rendered reference identity:

- `coding_repository_beta_mockup_v1.png`
- SHA-256: `662ae1225ec0c471fad16814e6246052d38d199181595c6f326e77d53b724ea0`

The exact approved HTML is preserved beside this file as `coding-repository-beta-approved-2026-08-27.html`.

Approved composition and semantics:

- Repository represents GitHub remote/future software state, not the currently loaded local runtime;
- the top strip exposes repository identity, branch, exact/short SHA, remote-current status and working-tree cleanliness where truthfully available;
- the dominant active-development card renders the canonical software lifecycle as `Proposal -> Plan -> Implementation -> Tests -> Review -> Reconciliation -> Merge`;
- software changes remain isolated in a branch/worktree. Jarvis never directly mutates the currently executed code path;
- exact-head deterministic gates and an independent review remain first-class merge prerequisites when required by accepted authority;
- `Current work` summarizes only real or explicitly future development fronts without inventing implementation authorization;
- the `Repository architecture` surface is a semantic, navigable graph rather than a static image. Selecting a node scopes inspection/Jarvis context and may expose dependencies, files and tests without itself mutating code;
- Jarvis remains on the right with an explicit active context that may include exact master/PR/file/module/spec references;
- repository facts are read-only summaries of the selected remote state;
- a Brainstorm `Promote -> Coding` action becomes a Coding development proposal and still passes the Coding lifecycle before merge.

## Runtime

Final approved local HTML identity:

- `coding_runtime_beta_mockup_v1.html`
- SHA-256: `48e867be8d7c865abf9b5fe653cf47713bab146c5f81c48779ca725c9430bfee`

Approved rendered reference identity:

- `coding_runtime_beta_mockup_v1.png`
- SHA-256: `2d716f74baad8104653e91b4191451aa58c59372685c15db6c6295aa9cf1b0ca`

The exact approved HTML is preserved beside this file as `coding-runtime-beta-approved-2026-08-27.html`.

Runtime is explicitly distinct from Repository. It represents the JarvisOS instance actually loaded on the workstation.

Approved composition and semantics:

- the top surface exposes local runtime health, cleanliness and whether an approved remote target is newer;
- loaded runtime identity includes local SHA, approved remote target SHA, working-tree state, state-snapshot availability and rollback point where truthfully available;
- local services/health endpoints are inspectable individually;
- the safe update path is explicit: `Save state -> Fetch approved target -> Migration -> Build -> Smoke -> Restart -> Health / rollback`;
- remote code is never hot-swapped into the currently running process;
- dirty local changes block the normal update path and must be explained rather than silently overwritten;
- post-restart health failure arms/uses rollback according to later accepted runtime authority;
- runtime logs show essential local events and preserve access to full logs separately;
- Jarvis may inspect differences, prepare an update plan and explain blockers, but restart/deploy/update remains an explicit operator action under the accepted runtime policy;
- update preparation must never invent service health or successful gates that were not actually observed.

## Authority boundary

These references freeze approved visual composition and interaction intent only. They do not by themselves create Repository/Runtime backend capabilities, authorize new state stores or process supervisors, bypass spec/readiness, or grant Jarvis commit/deploy authority.

When an approved HTML artifact and an incorrectly rendered screenshot disagree, the approved HTML/composition contract is authoritative.
