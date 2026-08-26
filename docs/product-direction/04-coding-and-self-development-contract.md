# PD-04 — Coding and self-development contract

Status: future product direction; not implementation authority.

## Purpose

Define `Coding` as the JarvisOS software-development control room. The goal is not to embed a generic IDE clone. The goal is to make the repository, the currently running local JarvisOS build, Jarvis-assisted implementation, automated review/reconciliation, and controlled self-update inspectable from inside JarvisOS.

The long-term intent is to formalize inside JarvisOS/Hermes the development pipeline that is currently coordinated externally through ChatGPT automations/builders, GitHub, CI and model reviews.

## Coding navigation

Normal peer tabs are exactly:

- `Repository`
- `Runtime`

Do not create a third peer `Jarvis Memory` tab. JarvisOS software knowledge is searchable and inspectable within Coding.

# Repository

Repository represents remote/future JarvisOS state and GitHub-backed development work.

## Repository header/status

The operator should be able to understand at a glance:

- repository identity;
- current/default branch;
- exact commit/head;
- GitHub connectivity;
- CI/check status;
- open PR count;
- Hermes/development orchestrator state when available.

Example composition only:

`JarvisOS_v1   master · a82f31c   CI ✓   2 PR open   Hermes ● running`

## Repository browser

The workspace should support, progressively:

- repository tree;
- branch selection/inspection;
- file view with syntax highlighting;
- repository search;
- selected-line context;
- diff view;
- commit/file history where useful;
- PR list and PR detail;
- CI/check/review status;
- architecture view.

This does not require reproducing all features of VS Code/GitHub.

## PR state as a first-class inspectable object

For an open PR, the UI should make the development pipeline state readable in one place. Conceptually expose:

- implementation state;
- deterministic tests/CI;
- Codex review status when used;
- Claude/other independent review status when used;
- reconciliation/fix state;
- Hermes orchestration state;
- merge readiness/blocker;
- last activity time.

A PR must remain tied to the exact remote head. Never imply review/CI applies to a moved head without revalidation.

## Formalized autonomous development pipeline

The intended future pipeline is a persistent state machine, not a loose chat convention:

`Proposal -> Plan -> Implementation -> Tests -> Independent Review -> Reconciliation -> Merge`

Hermes may orchestrate this pipeline 24/7, but each stage must be inspectable and auditable.

Required principles:

- one exact repository/head identity at every stage;
- deterministic gates remain authoritative for executable/testable facts;
- model/code-agent output remains untrusted proposal until gates/policy promote it;
- reviews are evidence, not supernatural authority;
- stale review/check results are invalidated when the head changes;
- merge remains reversible through Git history and must respect repository authority rules;
- credentials/secrets never enter prompts/logs/repository artifacts;
- the orchestrator must not silently broaden its own authority.

The current ChatGPT builder automation arrangement is a transitional external implementation pattern, not a permanent product abstraction.

## Right-side Jarvis panel

Coding includes a persistent right-side Jarvis panel. Jarvis receives the selected repository context (file/lines/PR/diff/architecture item) and may support actions such as:

- inspect/explain;
- plan;
- propose implementation;
- implement on an isolated branch/worktree when later authorized;
- run/interpret deterministic checks;
- summarize review findings;
- reconcile genuine findings;
- create a Brainstorm/Roadmap proposal when the requested work is not yet authorized.

The UI should make the scope/context Jarvis is acting on explicit.

# Editable architecture view

The future Repository workspace should support a semantic block-and-edge architecture view as a shared language between maintainer and Jarvis.

This is not merely a generated diagram image.

A block should be able to represent at least conceptually:

- stable ID;
- name;
- responsibility;
- interfaces/capabilities;
- dependencies/edges;
- code paths/implementation references;
- lifecycle/status.

An edge represents a typed relationship/dependency, not just a line drawn on a canvas.

The maintainer should eventually be able to add/remove/move/edit blocks and connections. Jarvis should interpret the semantic change and explain the resulting implementation impact before proposing code changes.

Example intended interaction:

1. maintainer inserts a `Deterministic Validation` gate between orchestration and merge;
2. Jarvis interprets the graph change as an architectural requirement;
3. Jarvis identifies affected orchestrator/state/CI boundaries;
4. Jarvis proposes a development item/spec rather than silently mutating code.

The graph must be versioned/provenanced if it becomes authoritative. A rendered position change alone must not imply architectural semantic change.

# Runtime

Runtime represents the JarvisOS software actually installed/running on the maintainer machine.

It must distinguish local current truth from GitHub truth.

Conceptually expose:

- local installation/worktree path;
- running version/commit;
- local branch;
- GitHub/default-branch latest commit;
- clean/dirty working-tree state;
- backend/frontend/runtime health;
- update availability.

A mismatch such as `running commit != GitHub master` must be explicit.

## Update to GitHub master and restart

The intended operator action is a clear command similar to:

`Update to GitHub master & restart`

This action must never be a blind `git pull && hope` flow.

Before execution show/verify at least conceptually:

- exact current commit;
- exact target commit;
- working-tree clean/dirty status;
- target CI/review/policy eligibility;
- required database/schema migration change if known;
- restart impact.

The future safe update pipeline should be designed around:

1. preserve needed runtime/user state;
2. fetch exact approved target;
3. refuse or explicitly reconcile unsafe local modifications;
4. perform migrations/build steps deterministically;
5. smoke/health check the new version;
6. restart into the new version;
7. verify health;
8. automatically roll back to the previous known-good version when the new runtime cannot start/validate.

Exact implementation is future-spec work. This contract requires safe, inspectable, reversible semantics.

# JarvisOS software knowledge inside Coding

Project `Memory` remains project-only. JarvisOS self-knowledge is exposed within Coding search/context.

Coding search should eventually be able to search across:

- code;
- GitHub/PR/commit context;
- semantic architecture;
- architecture decisions;
- implementation contracts;
- known limitations/technical debt;
- coding/repository invariants;
- lessons from failed/superseded approaches.

This knowledge should explain *why* the repository is designed as it is; it must not duplicate the repository itself.

Conceptual filters may include:

`All | Code | GitHub | Architecture | Decisions | Knowledge`

## Self-improvement safety principle

Jarvis does not directly mutate the live running self and treat the result as authoritative.

The required conceptual pattern is:

`current Jarvis -> proposal -> isolated branch/worktree -> implementation -> tests -> review/reconciliation -> merge -> approved new version -> controlled update/restart`

Self-improvement is therefore versioned, testable, auditable and reversible.

Do not create a separate magical `Auto improve` mode that bypasses Development, Coding, policy or deterministic gates.

## Non-goals

This contract does not authorize:

- arbitrary shell/filesystem authority from the frontend;
- direct frontend GitHub/provider calls;
- automatic merge without repository policy/gates;
- live self-modification bypassing Git;
- hidden background code changes;
- a new provider/runtime/agent framework solely for this UI;
- replacing existing accepted repository invariants before a real spec re-derives them.
