# 044 — Runner hardening boundary after CALC-1

Status: draft
Depends on: 043 (`calc_v0` runner kind)

## Goal

Record the security boundary left deliberately open after CALC-1 and define the
next hardening slice without expanding PR #52's runtime surface.

`calc_v0` is useful as a narrow engineering-calculation runner, but it must not
be described as a secure arbitrary-Python sandbox. The current protection model
is policy-based: script SHA binding, input/output shape validation, textual and
AST checks, a cleared subprocess environment, bounded stdout/stderr/output size,
and timeout-bounded synchronous execution. That is not equivalent to OS-level
isolation.

## Current boundary

The merged CALC-1 path should be treated as acceptable for small, local,
reviewable calculation scripts under the fixed `calc_v0` contract:

- read `input.json`;
- write `result.json`;
- import only the approved stdlib roots;
- produce finite numeric outputs with explicit units;
- create only proposed parameter records through the runner service, never from
  inside the subprocess.

The current AST policy is a deterministic guardrail, not a complete security
boundary. It reduces attack surface but does not make CPython safe for arbitrary
untrusted code.

## Binding non-goals for CALC-1

These remain out of scope for the merged CALC-1 implementation:

- no generic arbitrary Python runner;
- no network-secure sandbox claim;
- no seccomp, container, chroot, Windows job object, or per-run low-privilege OS
  account;
- no memory quota beyond process timeout/output-size limits;
- no CPU quota beyond the existing timeout;
- no package expansion such as numpy/scipy;
- no background execution or long-running jobs.

## Required future hardening slice

A future runner-hardening implementation should add at least one real operating
system isolation mechanism before JarvisOS treats local Python execution as
safe for broader untrusted scripts.

Candidate minimum acceptance criteria:

1. Each run executes in an isolated working directory that is not reused between
   jobs.
2. The subprocess runs with no inherited secrets and with an explicit allowlist
   of environment variables.
3. The subprocess cannot read or write outside the run directory by normal file
   paths.
4. The subprocess has deterministic timeout handling and bounded output capture.
5. Resource exhaustion is tested: timeout loop, large stdout/stderr, oversized
   `result.json`, and excessive artifact size.
6. The implementation documentation states exactly which threat model is covered
   and which attacks remain out of scope.

Platform-specific options to evaluate:

- Linux: container, user namespace, chroot-like jail, seccomp profile, or a
  dedicated low-privilege user plus filesystem permissions.
- Windows: job object, restricted token, low-integrity process, and ACL-limited
  run directory.
- Cross-platform fallback: keep `calc_v0` policy-only and label it explicitly as
  advisory/local-trusted until an OS-specific isolation path is available.

## Review checklist for future PRs

Before accepting any broader runner feature, verify:

- the actual subprocess command and environment, not only docs;
- path traversal and symlink behavior;
- retry/concurrency behavior if two callers attempt to run the same job;
- failure semantics for partial artifacts and parameter proposals;
- deterministic error codes for policy, timeout, validation, and execution
  failures;
- tests that prove blocked behavior, not just happy-path JSON validity.
