# PD-04 — Coding and self-development contract

Status: future product direction; not implementation authority. Reconciled to PD-08 on 2026-08-27; where earlier revisions differed, the final semantics below are authoritative for this packet.

## Purpose

Define `Coding` as the JarvisOS software-development control room. The goal is not to embed a generic IDE clone. The goal is to make the remote repository/future software state, the currently running local JarvisOS build, Jarvis-assisted development proposals, deterministic gates/reviews/reconciliation, controlled self-update and eventually a safe integrated local terminal inspectable from inside JarvisOS.

The long-term intent is to formalize inside JarvisOS/Hermes the development pipeline that is currently coordinated externally through ChatGPT automations/builders, GitHub, CI and model reviews, without giving the frontend direct repository/shell/provider authority.

## Coding navigation

Normal peer tabs are exactly:

- `Repository`
- `Runtime`

Do not create a third peer `Jarvis Memory` tab. JarvisOS software knowledge is searchable and inspectable within Coding.

# Repository

Repository represents **remote/future JarvisOS state** and GitHub-backed development work. It must remain semantically distinct from the local Runtime actually being executed.

## Repository header/status

The operator should be able to understand truthful repository identity at a glance, including where available:

- repository identity;
- current/default branch;
- exact commit/head;
- remote-current/synchronization fact;
- working-tree/read-only local inspection fact only when actually observed by the owning backend;
- open PR/check/review state.

No fixture value such as a sample SHA or PR count may become production truth.

## Active development lifecycle

The dominant software-development lifecycle is:

`Proposal -> Plan -> Implementation -> Tests -> Independent Review -> Reconciliation -> Merge`

The UI may expose active item, branch/worktree, PR, exact head, gates and blockers, but each fact must come from real repository/process evidence.

Required principles:

- one exact repository/head identity at every stage;
- implementation occurs in an isolated branch/worktree, never by directly mutating currently executed JarvisOS code;
- deterministic gates remain authoritative for executable/testable facts;
- model/code-agent output remains proposal until policy/gates/user authority promotes it;
- reviews are evidence, not supernatural authority;
- stale review/check results are invalidated when the head changes;
- merge remains reversible through Git history and respects repository authority rules;
- credentials/secrets never enter prompts/logs/repository artifacts/frontend responses;
- the orchestrator must not silently broaden its own authority.

The current ChatGPT builder arrangement is a transitional external implementation pattern, not the permanent product abstraction.

## Current work

Repository may summarize current/next software-development fronts, but only from canonical queue/spec/PR state. It may not invent authorization merely because a future feature is visible in a mockup/reference.

## Repository Inspector

The normal general inspection surface is **Repository Inspector**, not a permanently pinned architecture graph and not a full VS Code clone.

It should progressively support safe search/inspection of real repository artifacts such as:

- Markdown and specs (`STATUS.md`, `README.md`, `AGENTS.md`, architecture/decision documents, etc.);
- source code;
- tests;
- config/workflows;
- architecture SVG/image artifacts;
- other explicitly allow-listed readable repository files.

Search may support literal/path/ID lookup first and later bounded semantic retrieval only when evidence-backed. Results preserve exact repository/ref/path/blob identity.

Type-specific preview behavior may include:

- Markdown `Rendered | Raw`;
- syntax-highlighted code/source/config;
- SVG/image bounded preview;
- relevant safe metadata/links;
- truthful unsupported/too-large state for unsafe or unsupported content.

A selected artifact exposes, where applicable:

- `Add to Jarvis context`;
- `Suggest modification`;
- `Open on GitHub ↗`.

### Suggest modification boundary

`Suggest modification` is **not** an editor save action.

The intended flow is:

`selected exact target/ref -> user instruction -> proposed diff/plan/reason/affected files -> discussion -> development proposal/plan -> isolated branch/worktree -> implementation -> tests -> review/reconciliation -> PR -> merge`

No direct save-to-production or live-code mutation is authorized by the button.

## Architecture artifacts

Architecture remains important, but it is not permanently visible on the default Repository screen.

Existing Markdown/SVG architecture artifacts are searchable/inspectable through Repository Inspector like other repository artifacts. Clicking a preview may expand/full-inspect it and add it to Jarvis context or start a modification proposal.

A future semantic architecture model may still be useful, but only after a separate authority/readiness proves need. If promoted, semantic architecture should distinguish stable node/edge identity, responsibility, interfaces/capabilities, typed dependencies, code paths, lifecycle/status and provenance from mere layout coordinates.

Moving a rendered box alone must never imply an architectural semantic change. A semantic architecture edit should produce impact analysis/development proposal before code mutation.

## Right-side Jarvis panel

Coding includes a persistent right-side Jarvis panel with explicit removable active context. Context may include exact PRs, specs, repository files/paths, architecture artifacts/modules or runtime identities.

Jarvis may support bounded actions such as:

- inspect/explain;
- compare selected artifacts/specs/code;
- prepare modification proposal/diff;
- plan an authorized implementation;
- create/use an isolated branch/worktree when later authorized;
- run/interpret permitted deterministic checks;
- summarize/reconcile genuine review findings;
- create a Brainstorm/Roadmap proposal when work is not yet authorized.

Selecting/browsing a repository artifact does not silently add it to Jarvis context.

# Runtime

Runtime represents the JarvisOS software **actually installed/running on the maintainer machine**. It is explicitly distinct from Repository/GitHub state.

## Local-vs-GitHub identity is the dominant first-screen concept

Runtime must independently establish and display:

- **local actually executed version/SHA** — visually green in the approved reference plus explicit text, never color-only;
- **latest/selected approved GitHub version/SHA** — orange when newer in the approved reference plus explicit text;
- local installation/worktree path where safely available;
- local branch and dirty/clean state;
- backend/frontend/runtime/service health;
- explicit alignment state such as `aligned`, `local behind`, `divergent`, `unknown`.

Never infer the local running SHA from GitHub latest. Remote latest and local executed truth are separate observations.

## Semantic divergence summary

When GitHub is ahead, Runtime should expose a concise evidence-backed `What GitHub added after the local version` summary.

Required semantics:

- exact ancestry/compare between local and remote selected SHAs;
- summary tied to real commits/files/specs;
- docs/reference-only versus runtime-affecting classification only where deterministically supportable;
- underlying commits/files remain inspectable;
- divergent/unrelated/unknown histories fail honestly rather than inventing a feature delta;
- LLM summary alone cannot be presented as repository fact.

This delta and identity hierarchy should receive more first-screen emphasis than update/migration phase details.

## Safe update and restart

A future operator action may prepare/update to an approved GitHub target, but never as `git pull && hope` or a hot swap into the currently executing process.

The safe contract preserves conceptually:

1. preserve needed runtime/user state;
2. fetch exact approved target;
3. refuse or explicitly reconcile unsafe dirty local modifications;
4. perform migrations/build steps deterministically;
5. smoke-check the candidate;
6. restart explicitly into the candidate;
7. verify post-restart health;
8. automatically roll back to the previous known-good version when startup/health fails.

The normal Runtime page keeps these safeguards compact until `Prepare update`/inspection is requested. Exact current/target SHAs, dirty state, state backup and rollback identity must remain inspectable.

# Future integrated terminal

The lower Runtime utility area may evolve into:

`Terminal | Logs`

The Terminal is intended to be **real**, not a mock. PowerShell is the default Windows shell on the maintainer workstation, with a replaceable PTY/process adapter for CI/platform portability.

Useful interactions include:

- persistent active session/cwd;
- terminal scrollback/history;
- stdin and `Ctrl+C`/interrupt;
- `Open terminal here` from a validated Repository Inspector/worktree/path;
- `Send output to Jarvis` as an explicit bounded context action;
- Jarvis-proposed command with `Insert in terminal` / copy;
- Logs retained as the adjacent tab.

## Terminal authority/security boundary

This feature is separate from self-update authority and must not weaken JarvisOS hard invariants.

- Frontend never receives direct shell/filesystem/process authority.
- PTY/session creation and all command I/O are mediated by a typed local backend service.
- The service is local-only/appropriately authenticated and cannot become a remote shell server.
- Working directory/path targets are backend-validated; protected credential/config/secret-store paths require denial/isolation under the accepted security spec.
- The child process uses a deliberately scrubbed/minimum environment and does not inherit provider API keys, repository tokens or credential-store secrets by default.
- Raw PTY bytes are not forwarded as an unrestricted frontend response. A backend-owned secret-safe display/isolation/redaction boundary runs before terminal output reaches the UI.
- If adequate target-OS secret isolation/redaction cannot be proven, arbitrary PTY streaming remains unavailable/deferred rather than weakening the repository no-secret frontend invariant.
- `Send output to Jarvis` has its own bounded secret/context/egress policy on top of the frontend display boundary.
- Jarvis command suggestions are proposals; they are not executed automatically by default.
- High-risk/destructive command classes require backend/policy classification and explicit operator confirmation where required.
- Terminal access never bypasses Git/spec/review/update boundaries for self-modification.
- CI uses fake/controlled adapters and does not require live Windows PowerShell.

A prompt-level denylist alone is not an adequate terminal security boundary.

# JarvisOS software knowledge inside Coding

Project `Memory` remains project-only. JarvisOS self-knowledge is exposed within Coding search/context.

Coding knowledge may combine exact provenance-linked material from:

- code;
- GitHub/PR/commit context;
- architecture artifacts/semantic architecture if later accepted;
- ADRs/decisions;
- accepted specifications;
- AGENTS/process invariants;
- known limitations/technical debt;
- lessons from failed/superseded approaches.

This knowledge should explain *why* the repository is designed as it is; it must not duplicate the repository itself or promote generated explanation into source authority.

## Self-improvement safety principle

Jarvis does not directly mutate the live running self and treat the result as authoritative.

The required conceptual pattern is:

`current Jarvis -> proposal -> plan -> isolated branch/worktree -> implementation -> tests -> independent review/deterministic checks -> reconciliation -> PR -> merge -> approved new version -> controlled update/restart`

Self-improvement is therefore versioned, testable, auditable and reversible.

Do not create a magical `Auto improve` mode that bypasses Development, Coding, policy or deterministic gates.

## Non-goals

This contract does not authorize:

- arbitrary shell/filesystem authority from the frontend;
- direct frontend GitHub/provider calls;
- direct repository mutation from Repository Inspector preview;
- automatic merge without repository policy/gates;
- live self-modification bypassing Git;
- hidden background code changes;
- a permanent default architecture graph that displaces Repository Inspector;
- a new provider/runtime/agent framework solely for this UI;
- weakening no-secret frontend-response policy to support terminal output;
- replacing existing accepted repository invariants before a real spec re-derives them.
