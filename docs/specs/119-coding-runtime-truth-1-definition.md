# 119 CODING-RUNTIME-TRUTH-1 — definition

Exact source master: `f5995dc187a1834ca0d52e5d8b3891b17fcd4e20`.

Authority: definition only. This document does not authorize runtime implementation and does not change the live `119` registry row from `planned`.

Governing authority:
- `AGENTS.md` and `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` for safety, exact-head evidence, lifecycle, and repository-development authority;
- `docs/specs/STATUS.md` for the live `119` row, dependency, and state;
- `docs/specs/README.md` and `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` for the active Coding-first lifecycle;
- merged `118 CODING-REPOSITORY-TRUTH-1` for authoritative remote repository/ref/SHA truth;
- merged `111 JARVIS-CONTEXT-ACTION-FOUNDATION-1` for READ/CONTEXT versus mutation authority.

## Problem

JarvisOS can now inspect remote repository truth through `118`, but that does not prove which code is actually running on a local installation. A branch name, remote default branch, packaged version string, copied path, or model statement cannot establish the executed worktree, commit, dirty state, build identity, process health, or whether the local runtime is aligned with the approved remote target.

Without a separate local-observer boundary, later Coding and Development features could confuse remote repository state with executed state, report stale code as current, compare the wrong ref, hide dirty/uncommitted changes, or grow observation into implicit update/restart authority.

## Definition boundary

`119` owns only read-only local runtime/worktree truth and deterministic alignment derivation against exact remote evidence owned by `118`.

The later full specification MUST define:

1. **Observed installation/worktree identity** — identify the concrete local code root or packaged runtime root actually associated with the observed JarvisOS service, without trusting arbitrary model/frontend paths.
2. **Executed code identity** — expose the strongest available immutable identity for the running build/process, including exact commit SHA when the runtime is a Git worktree and a typed `unknown` when that cannot be proven.
3. **Local ref and dirty evidence** — when applicable, observe branch/detached state plus tracked/untracked or otherwise accepted dirty-state evidence without modifying the worktree or index.
4. **Runtime/build identity** — distinguish configured application version from evidence about the code/build actually executing; define what build/process metadata can be proved and what remains unknown.
5. **Service/runtime health** — project bounded health evidence needed by the Coding lane without becoming a process supervisor, restart controller, deployment manager, or general host monitor.
6. **Approved remote target** — consume exact repository/ref/SHA evidence from `118` as the remote comparison target; do not create a second GitHub/repository-truth implementation.
7. **Deterministic alignment state** — derive only evidence-backed `aligned`, `local_behind`, `divergent`, or `unknown` states. Human-friendly labels must not outrun the evidence required for the state.
8. **Evidence-backed semantic delta** — define the smallest bounded local-versus-approved-remote delta projection needed to explain misalignment, reusing `118` repository truth rather than inventing another diff/index.
9. **Typed failures and uncertainty** — missing Git metadata, detached/invalid refs, inaccessible paths, absent executables, malformed VCS output, timeout, dirty ambiguity, unsupported packaging, remote truth unavailable/stale, and process/build identity uncertainty remain explicit rather than guessed.
10. **Observation-only enforcement** — no update, pull, fetch-as-mutation-to-worktree, checkout, reset, clean, stash, commit, install, build, restart, kill, service-control, or deployment action belongs to `119`.

## Trust-boundary invariants

The full specification MUST preserve these invariants:

- local filesystem/process/VCS observations are backend-owned and limited to configured/derived JarvisOS installation roots; arbitrary model/frontend filesystem paths are not observation authority;
- commands, if fresh code proves a subprocess is minimum-necessary, are fixed allowlisted read-only probes with explicit argv/cwd/environment/timeouts and no shell evaluation;
- repository files, branch names, environment values, VCS output, process metadata, and build metadata are untrusted data and are never executed or interpolated into shell commands;
- observation must not modify Git index/worktree/config, install dependencies, create commits/refs, invoke hooks, or change service/process state;
- exact local SHA evidence and exact remote SHA evidence are kept distinct; one may not be substituted for the other;
- `aligned` requires exact equality of the accepted local executed/worktree identity and approved remote target under the semantics frozen by the full spec;
- `local_behind` and `divergent` require concrete ancestry/delta evidence; inability to prove those relations yields `unknown`, not a guess from timestamps, versions, branch names, commit counts, or human text;
- dirty state cannot be hidden by an otherwise matching SHA; the full spec must state how dirty evidence affects alignment presentation and downstream safety;
- local observation is evidence/context only and grants no COMMIT/EXECUTE/update/restart authority;
- no telemetry may expose repository contents, secrets, arbitrary environment variables, user home paths beyond the accepted projection, or command output not required for the typed result.

## Fresh-code obligations for the full specification

The full-spec pass must inventory current owners before selecting implementation files or probes. At minimum it must revalidate:

- `backend/app/api/system.py`, which already exposes configured application version, environment, storage/database status, and AI gateway status but does not currently prove Git/worktree/executed-SHA identity;
- startup/bootstrap/path/config owners and the actual launch scripts used by the repository, to distinguish configured paths from the code root that is really executing;
- existing subprocess/process-runner safety owners, if any read-only VCS/process probe is proposed, before adding another execution seam;
- merged `118` service contracts for exact remote repository/ref/SHA/compare evidence;
- existing health endpoints and tests so `119` adds only missing runtime truth rather than a duplicate system-information API;
- current security/AE002 and logging/redaction gates relevant to filesystem, subprocess, environment, or provider access.

A new subprocess wrapper, filesystem crawler, process monitor, persistent store, remote transport, Git library, cache, daemon, or supervisor must identify the concrete insufficiency in current owners and pass the minimum-necessary test. None is presumed necessary by this definition.

## Questions the full specification must resolve from fresh code

1. What concrete local root corresponds to the running JarvisOS backend/frontend installation in supported development/production modes, and how is that root derived safely rather than supplied arbitrarily?
2. What is the smallest read-only mechanism that can prove local Git SHA/ref/dirty state where Git metadata exists, and what typed result applies to packaged/non-Git installations?
3. Is worktree HEAD sufficient evidence of **executed** code for the supported launch model, or must build/startup identity be captured separately to avoid claiming that a changed-on-disk checkout is what a long-running process loaded?
4. Which health/build/process fields are already authoritative in `/system/info`, and which additional fields are genuinely needed for Coding runtime truth?
5. How does `119` select the approved remote repository/ref target using `118`, and what happens when the remote ref moved after local observation?
6. What exact evidence distinguishes `aligned`, `local_behind`, `divergent`, and `unknown`; how is dirty state represented alongside those states?
7. What bounded semantic delta can be derived by reusing `118` compare/file truth without sending local repository content to another provider or creating a duplicate local index?
8. What timeouts, byte/count bounds, path restrictions, environment controls, and typed parse failures apply to every local observation primitive?
9. What telemetry proves an observation occurred while avoiding local path leakage, secrets, repository contents, and raw environment/process dumps?
10. Which deterministic tests prove observation-only behavior and prove that update/restart/worktree mutations are unreachable through the `119` surface?

## Acceptance criteria for future full spec/readiness

Before `119` can become `ready`, fresh exact-master planning evidence must prove all of the following:

1. each accepted local observation has one explicit backend owner and a fixed configured/derived JarvisOS scope;
2. local worktree identity, executed/build identity, branch/detached state, dirty evidence, and runtime health have explicit provenance and typed unknown semantics where proof is unavailable;
3. approved remote target truth is consumed from `118` with exact repository/ref/SHA provenance and no duplicate remote repository transport/index;
4. `aligned`, `local_behind`, `divergent`, and `unknown` are defined by deterministic evidence, including the treatment of dirty local state and moved/stale remote refs;
5. any subprocess/filesystem/process primitive is bounded, read-only, shell-free where applicable, timeout-controlled, output-bounded, and unable to escape configured/derived JarvisOS roots;
6. no accepted operation can update Git state, mutate files, install/build code, control processes/services, restart JarvisOS, deploy, merge, or otherwise change runtime/repository state;
7. supported non-Git/packaged/missing-metadata cases fail or degrade explicitly to typed uncertainty rather than fabricated alignment;
8. semantic delta explanation reuses exact evidence from `118` and does not create a second repository truth/index or treat model prose as state;
9. telemetry/logging exposes only bounded metadata required for audit/debug and excludes credentials, repository content, unrestricted environment/process data, and unnecessary local path detail;
10. deterministic tests cover at minimum matching SHA, dirty matching SHA, local ancestor/behind, divergent history, detached head, non-Git/missing metadata, stale/moved remote target, malformed/timeout probe, path/shell-injection attempts, bounded-output failure, and rejection/unreachability of update/restart/mutation operations.

## Non-goals

- Git fetch/pull/checkout/reset/clean/stash/commit/ref/config mutation or automatic synchronization.
- Package installation, build execution, self-update, deployment, restart, process kill/control, service manager, watchdog, or host orchestration.
- A second GitHub/repository provider, repository database/index, diff engine, or branch/PR/check/review owner already covered by `118`.
- Generic host inventory, arbitrary filesystem browser, arbitrary command runner, shell/PTY, remote execution, or IDE agent.
- Development pipeline lifecycle state owned by `120`, later coding actions owned by subsequent accepted slices, or Hermes release authority.
- Frontend-owned local filesystem/process access or model-controlled probing.

## Minimum-necessary test

Criterion: give the Coding lane one bounded, read-only, evidence-backed answer to “what JarvisOS code/runtime is actually local/running, and how does it relate to the approved remote target?”

This definition is necessary because `118` proves remote repository truth but cannot prove executed local state. It intentionally stops before choosing probe commands, process/build identifiers, endpoint/schema shape, or new dependencies; those choices require fresh-code full-spec derivation and separate readiness while `119` remains `planned`.