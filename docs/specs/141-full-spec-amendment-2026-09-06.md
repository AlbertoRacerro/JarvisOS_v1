# 141 LOCAL-WORKTREE-ACTUATOR-1 — bounded full-spec amendment — 2026-09-06

## Authority and scope

This document is a **full-spec refreeze amendment** for `docs/specs/141-local-worktree-actuator-1.md`. It exists only to reconcile three exact failure families discovered during readiness review. For the clauses below, this amendment replaces the conflicting text in the previously frozen full specification. Every other 141 full-spec requirement, non-goal, availability invariant, credential boundary, sensitive-path refusal, worker topology rule, audit requirement, and 125/126 separation remains frozen unchanged.

This amendment grants no implementation authority by itself. `docs/specs/STATUS.md` remains the sole live state authority; 141 may be implemented only after the readiness decision and matching `141: ready` registry transition are accepted on the same exact PR head.

## 1. Guarded push: exact expected-old-ref CAS without non-fast-forward authority

The earlier full-spec requirement for a plain ordinary `git push` is replaced because a pre-read followed by an ordinary push does not atomically prove that the remote still equals `expected_remote_head` at mutation time.

`push_branch(repository_id, worktree_id, branch, intended_local_commit, expected_remote_head)` remains the only push shape and is admitted only for an already-existing registered non-default/non-protected branch on the approved GitHub HTTPS remote. Remote branch creation remains outside 141.

The shared repository-delivery primitive MUST:

1. validate implementer capability, writer lock, repository/worktree/branch identity, complete sensitive-path delta, isolated Git configuration/remote/credential boundary, and exact local HEAD = `intended_local_commit` before network mutation;
2. read the target branch fresh and require exact equality with the caller-supplied 40-character `expected_remote_head`; an absent branch returns typed `REMOTE_BRANCH_ABSENT`, and a mismatch returns typed stale-head refusal, with no credentialed push;
3. prove `intended_local_commit` is a descendant of `expected_remote_head`; otherwise return typed `NON_FAST_FORWARD_REFUSED` before push;
4. perform only the exact target update using `--force-with-lease=<target-ref>:<expected_remote_head>` as a **fixed transport-level expected-old-ref equality guard**;
5. expose no generic force flag, no `+refspec`, no deletion refspec, no caller-controlled lease/ref, and no path that can intentionally admit a non-fast-forward update;
6. treat lease rejection as stale-CAS refusal and never retry automatically against a newly observed head;
7. declare `REMOTE_VERIFIED` only after a fresh remote reread equals `intended_local_commit` exactly.

The fixed lease is therefore not force-push authority: fast-forward ancestry is independently proven before invocation, the caller cannot weaken the lease, and any non-fast-forward update is structurally refused. Any implementation capable of rewriting branch history fails 141 acceptance.

The earlier frozen clauses that structurally forbade the literal `--force-with-lease` option and claimed an ordinary push alone closed the read→push race are superseded only to this extent. The prohibition on generic force, force-push semantics, default-branch writes, branch deletion, merge, and caller-selected Git arguments remains fully binding.

Required deterministic tests include: stale pre-read refusal; race `expected=A`, remote advances to `B`, intended commit `C` still fails because the lease expects `A`; intended commit not descending from expected refuses before push; no generic/caller-controlled force or lease surface exists; successful push is accepted only after exact remote-SHA reread.

## 2. Named validation profiles: no mutable-worktree code execution in 141 MVP

The earlier full-spec text allowing fixed named test profiles to execute repository/worktree code is replaced. Fixed argv, environment, cwd, timeout, and output caps are **not** an OS sandbox: mutable candidate code can execute through test imports, hooks, build scripts, package lifecycle behavior, or equivalent mechanisms and thereby escape reviewer/read-only, filesystem, credential, or subprocess boundaries.

Therefore 141 MVP MUST NOT execute, import, source, build, test, or otherwise run mutable repository/worktree content through its named-profile surface. A profile that would do so — including ordinary pytest, npm/build, repository script, import-hook, or equivalent candidate-code execution — returns typed `LOCAL_TEST_PROFILE_REQUIRES_ISOLATION` and launches no child process.

Named profiles may cover only bounded worker-owned validation operations whose executable and inputs are immutable/trusted worker assets and whose behavior cannot execute mutable worktree content. Reviewer role has the same refusal and cannot use a named profile to escape read-only authority.

Candidate-code tests remain available through separately governed cloud/CI, or through a future separately authorized isolation/process capability. This refusal does not create a global dependency on a local worker and does not absorb or redefine 126 LOCAL-TERMINAL-PTY-1.

Required deterministic tests include hostile worktree test/import-hook fixtures proving no child process launch, explicit typed refusal for mutable-code profiles, and reviewer/implementer parity on this execution boundary.

## 3. 079 compatibility owner: include the actual workflow push path without granting `.github/**` actuator writes

The earlier full-spec coexistence language is refined to match current runtime ownership. Spec 079 scheduled continuation retains its orchestration semantics, but its current commit/push shell owner in `.github/workflows/daily-development-continuation.yml` is part of the bounded **ChatGPT implementation compatibility surface** needed to adopt the shared repository-delivery safety primitive.

The 141 implementation PR may make only the minimum reviewed compatibility edit to that existing 079 workflow and its focused tests necessary to eliminate a divergent ordinary-push safety stack. This is repository-maintainer implementation authority, **not** an actuator/model capability or sensitive-path exception.

For every 141 worker/model request, `.github/**` remains server-owned sensitive control-plane material and is refused before write/stage/commit/push. Existing 022/079 lane-specific policy, OIDC/token ownership, candidate/marker semantics, and no-automerge boundaries remain unchanged except for consuming the shared deterministic Git-delivery primitive.

Required regression coverage must exercise the actual workflow commit/push owner and prove that factoring the shared primitive neither weakens 079 semantics nor leaves a second independent ordinary-push safety implementation.

## Refreeze result

With these three bounded replacements, the 141 full-spec and readiness contracts are no longer mutually exclusive: expected-head safety is atomic without granting history-rewrite authority; mutable worktree code is refused rather than falsely treated as sandboxed; and the real 079 push owner is included for compatibility while remaining inaccessible to the 141 actuator. No other scope or authority is broadened.