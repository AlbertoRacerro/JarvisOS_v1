# 141 LOCAL-WORKTREE-ACTUATOR-1

## Definition kernel

**Lifecycle:** definition only. This artifact does not make 141 implementation-ready; `docs/specs/STATUS.md` remains the sole live work-state authority. A separate full specification and readiness decision are mandatory before implementation.

**Fresh derivation basis:** exact `master` `129bf603969ee68e26d3f22fc37efcc139cebda9`, with repository-development authority from `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`, and the current registry.

## Problem

JarvisOS repository delivery can currently produce validated work that remains `LOCAL_ONLY` or becomes a `DELIVERY_FAILURE` when an ephemeral agent environment loses its checkout or cannot push its tested commit. The repository protocol explicitly distinguishes those states from `REMOTE_VERIFIED`; a local commit SHA or model claim is not durable delivery.

The missing owner is a small deterministic local actuator that can preserve an exact worktree and commit across model sessions and perform a tightly guarded ordinary branch push without exposing credentials or granting broad terminal, filesystem, merge, or desktop authority.

This is repository-development infrastructure only. It does not broaden JarvisOS product/runtime authority.

## Availability and worker-topology invariant

141 MUST be an optional execution plane, never a global availability dependency.

The full specification and readiness evidence must preserve all of these properties:

- JarvisOS supports zero, one, or multiple registered trusted local workers/hosts.
- A maintainer personal laptop is only an optional worker; it is never the required control-plane host and need not remain powered on continuously.
- Each worker exposes bounded identity, online/health state, registered repository/worktree identity, and supported capabilities.
- If one worker is offline, only operations that require that worker become typed `offline` / `unavailable`; worker absence must not be reported as success and must not become a global pipeline failure.
- With **zero local workers online**, GitHub connector/API work, GitHub-hosted Actions/CI, cloud semantic review, repository governance, and exact-head browser-proof workflows must remain usable whenever otherwise authorized.
- Stage 2 browser proof and later cloud-side work on 124/113/140 must not depend on a personal/local host being online.
- When multiple workers exist, a request may run only on an eligible registered worker for that repository/worktree/capability. A dirty or persistent worktree must never be silently migrated to another host.
- Worker disconnect/reconnect must preserve that host's durable local worktree/commit state. Before any guarded push after reconnect, remote truth and `expected_remote_head` must be revalidated.
- A future dedicated always-on machine may be enrolled as another worker without redesigning the authority protocol.

Worker installation, enrollment, startup, or host-local Git credential bootstrap is therefore a **LOCAL CAPABILITY ACTIVATION** concern only. Failure or absence of that activation must not block unrelated cloud/GitHub lanes.

## Minimum bounded owner to derive

A later accepted implementation may own only:

- a trusted local-user / loopback-only worker or bridge per registered host;
- a registry of trusted worker identity/health/capabilities plus explicitly allowed repositories and actuator-owned worktrees;
- exact-ref worktree create, attach, inspect, and identity verification;
- an `implementer` capability that may write only inside its assigned actuator worktree;
- a `reviewer` capability that is read-only;
- named, predeclared deterministic test profiles with bounded subprocess execution needed only by those profiles;
- bounded `git status`, `git diff`, local commit, and ordinary same-branch non-force push;
- push admission guarded by an explicit `expected_remote_head` compare-and-swap check;
- persistent worktree/commit identity that survives loss of the requesting model session and remains discoverable after host-service restart where practical;
- OS-owned Git authentication, initially through an existing local Git Credential Manager / GitHub CLI or an equivalently secret-safe owner, with raw credentials never returned to model/tool output;
- append-only audit evidence sufficient to reconstruct requesting principal/session, worker, repository/worktree, requested capability, exact SHA before/after, admission/refusal decision, exit/result status, and bounded result digests.

The full spec must reuse an existing JarvisOS audit/event/store owner where sufficient. It must not create a second durable state authority merely for convenience; a new store requires explicit minimum-necessary proof.

## Authority boundaries and hard refusals

141 MUST NOT create or acquire:

1. merge, auto-merge, default-branch write/push, force-push, or remote branch-deletion authority;
2. arbitrary shell, generic PTY, unrestricted command execution, or general process-supervisor authority;
3. arbitrary filesystem access outside registered repository/worktree roots;
4. self-update, restart, rollback, installer-update, or service-replacement authority;
5. browser, desktop, mouse, keyboard, screen-capture, or general computer-use authority;
6. provider credentials, provider dispatch, model-routing, budget, egress, promotion, database, service, or domain authority;
7. raw GitHub/Git credentials in model context, ordinary API responses, logs, audit payloads, test fixtures, or frontend state;
8. Hermes ownership of JarvisOS repository policy, credentials, capability admission, audit, or exact-head decisions.

`125 SAFE-SELF-UPDATE-1` and `126 LOCAL-TERMINAL-PTY-1` remain separately gated specifications and may not be absorbed, redefined, or implemented through 141.

## Git execution surface is part of the threat model

Calling an exact `git` subcommand is not by itself equivalent to bounded execution. Repository, worktree, local, global, and system Git configuration can cause child processes, URL rewrites, credential helpers, hooks, filters, proxies, or other behavior outside the apparent command.

The full spec MUST therefore freeze a fail-closed Git invocation model proving that actuator-owned operations cannot execute arbitrary repository-controlled helpers or redirect credentials/network traffic through unapproved Git configuration. At minimum it must explicitly resolve:

- repository/local `core.hooksPath` and commit hooks;
- executable or shell-form credential helpers and credential-source precedence;
- `url.*.insteadOf`, proxy, SSH-command, transport, and push-URL rewriting;
- clean/smudge/process filters or other checkout/worktree-triggered executable configuration relevant to the accepted worktree path;
- remote origin/push URL identity and allowed transport/host;
- subprocess environment inheritance and secret-bearing environment variables;
- whether system/global configuration is needed for the selected OS-owned credential path and, if so, how all unrelated executable configuration is excluded.

For the MVP, a narrower controlled HTTPS GitHub remote contract is preferred over supporting arbitrary Git transports. If this cannot be made deterministic without granting generic command or credential authority, the full spec must stop and re-derive the prerequisite rather than weaken this boundary.

## Filesystem and Windows path boundary

Lexical path-prefix checks are insufficient. The full spec must define canonical path identity and fail closed on path escape through symlinks, junctions, mount points, Windows reparse points, case/normalization ambiguities, or equivalent filesystem indirection. An implementer write must resolve to the assigned worktree; a reviewer write must always be refused.

The worktree itself must be bound to the expected repository identity, branch/ref, and Git common directory rather than trusted from a caller-supplied path string.

## Concurrency and exact-head boundary

The full spec must define one deterministic writer lease/lock for an actuator-owned worktree and branch so two model sessions cannot mutate the same working tree concurrently. Local serialization does not replace remote correctness: every push still requires a fresh remote-head read and `expected_remote_head` equality immediately before mutation.

After push, the actuator must re-read the remote branch SHA and report success only if it equals the intended local commit. A timeout, disconnect, or ambiguous push result is `unknown`/refused for retry until remote state is re-read; it is never blindly retried as a new effect.

## Failure modes the full spec must close

The next lifecycle artifacts must make at least these failures deterministic and testable:

- **Zero-worker graceful degradation:** no local worker is online; only local-worker-required capabilities become unavailable while GitHub/API, Actions/CI, cloud review, governance, and exact-head browser-proof lanes remain usable.
- **Single-worker outage:** one registered worker disconnects; requests requiring it receive a typed offline/unavailable result without poisoning unrelated workers or cloud lanes.
- **Wrong-worker migration:** a caller tries to continue a dirty/persistent worktree on a different host; the actuator refuses rather than silently recreating or moving state.
- **Reconnect staleness:** a worker returns after remote branch movement; any push requires fresh remote-head revalidation and stale CAS refuses.
- **Stale remote overwrite:** another writer advances the branch after the requester observed it; push is refused by CAS.
- **Protected/default-branch mutation:** branch identity is wrong, detached, default/protected, or caller-swapped; write/push is refused.
- **Force/destructive mutation:** any force, deletion, reset of remote authority, merge, or auto-merge request is structurally unavailable/refused.
- **Worktree escape:** write target resolves outside the assigned worktree through path traversal, symlink/junction/reparse indirection, or identity mismatch.
- **Reviewer escalation:** a reviewer or read-only session attempts file mutation, commit, test profile with writes outside allowed artifacts, or push.
- **Command smuggling:** a named test profile, Git hook/config/helper/filter, environment variable, remote URL rewrite, or caller-controlled argument causes unapproved command/process execution.
- **Credential disclosure/exfiltration:** secret material appears in output/log/audit/error/model context or Git is redirected to an unapproved credential consumer/remote.
- **Concurrent local writers:** two principals act on one worktree/branch without deterministic exclusion.
- **Dirty-state confusion:** pre-existing untracked/modified content or a mismatched HEAD is committed without an explicit accepted worktree state.
- **Session-loss work loss:** the requesting model disappears after creating validated work; the worktree and local commit remain discoverable and later guard-pushable by a newly authorized session.
- **Ambiguous push:** network/process interruption occurs after possible remote mutation; remote truth is re-read before any retry decision.
- **False delivery success:** local commit exists but remote SHA is not the intended commit; result is not reported as `REMOTE_VERIFIED`.
- **Audit gap:** a permitted or refused authority-bearing action cannot be reconstructed from durable audit evidence.

## Required full-spec derivation

A separate full-spec PR must re-inspect then-current master and freeze, at minimum:

- the exact module/process boundary and local IPC/API shape;
- worker registry/identity/health/capability representation and zero-worker behavior;
- repository/worktree registry ownership and persistence, preferring existing owners;
- principal/session and implementer-versus-reviewer capability representation;
- canonical path and Windows reparse-point handling;
- Git executable/config/environment isolation, remote identity, credential ownership, and allowed transport;
- named test-profile registry and exact argument/environment policy;
- worktree/branch concurrency lock semantics and crash recovery;
- dirty-state admission, commit author/message policy, and exact local commit identity;
- worker disconnect/reconnect semantics and prohibition on silent cross-host dirty-worktree migration;
- pre-push remote CAS, ambiguous-result handling, and post-push remote verification;
- audit schema/storage/redaction/retention using existing JarvisOS authority where sufficient;
- service startup/lifetime assumptions for optional Windows worker activation without granting self-update or arbitrary supervisor authority;
- exact deterministic offline tests using temporary repositories/bare remotes, with no live GitHub credential or provider call required in CI;
- proof that cloud/GitHub lanes and 142 browser proof remain independent of local-worker availability.

If any accepted behavior requires generic PTY, self-update, unrestricted filesystem/process authority, a new credential store, or a new durable state authority, the full spec must stop and derive that prerequisite separately.

## Readiness requirements

A separate readiness decision must freeze deterministic evidence for the accepted full spec. At minimum it must require negative and positive tests proving:

- zero workers online leaves non-local GitHub/API, CI, review, governance, and browser-proof capabilities available;
- worker-required operations return typed offline/unavailable when the selected worker is absent;
- a persistent dirty/worktree identity is not silently migrated across hosts;
- reconnect revalidates remote head before guarded push;
- stale `expected_remote_head` refuses push;
- default/wrong branch and force/destructive requests refuse;
- outside-worktree and reparse/symlink escape refuse;
- reviewer writes/commit/push refuse;
- repository-controlled Git config/hook/helper/URL behavior cannot escape the accepted command/credential/network boundary;
- raw credentials do not appear in responses, logs, audit, fixtures, or model-facing outputs;
- one durable local commit remains discoverable after simulated requester/session loss and is later guard-pushable by a newly authorized session;
- concurrent writer admission is deterministic;
- ambiguous push is resolved by remote re-read rather than blind retry;
- post-push remote SHA must equal the intended local commit before delivery is reported successful;
- all CI proof is offline against temporary local repositories/remotes, except a separately documented maintainer activation smoke if the final host credential path cannot be proven below the real OS layer.

## Definition exit criteria

This definition is complete when it establishes one independently removable, offline-tolerant local repository actuator owner, closes the authority boundary against generic terminal/filesystem/credential/merge/desktop expansion, records the Git-config and Windows-path execution hazards above, and leaves exact API/storage/credential/test contracts to the required full-spec and readiness stages.

No implementation, `ready` promotion, credential bootstrap, workstation installation, GitHub push, provider call, or product/runtime behavior change is authorized by this definition. Local worker installation/enrollment remains optional capability activation and is never a prerequisite for unrelated cloud/GitHub execution.