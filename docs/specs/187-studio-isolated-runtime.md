# 187 — Engineering Studio isolated Python runtime

State: **accepted and ready**. Written under the maintainer directive of 2026-10-13 ("Engineering Studio / BlueRev R&D workstation", §27 Execution safety). Reviewed against master `c1e8f516`. Architecture record: [Engineering Studio architecture](../implementation/engineering-studio-architecture-2026-10-13.md).

- **Hard dependency:** none.
- **Risk tier:** 2 (security boundary). An independent adversarial peer review of the exact head is required before merge.

## Fresh evidence (master `c1e8f516`)

- **Runner boundary.** `docs/runner-trust-boundary.md` states that the runner is a trusted-code boundary, not a sandbox, and that caller-controlled Python stays non-executable until a separate OS-isolation specification is implemented and independently proven. `runner/guarded_service.py` (`_require_exact_bundled`) enforces it.
- **Reopen trigger.** "A genuinely non-bundled implementation must execute and git-based bundling is demonstrably inadequate." The 2026-10-13 directive makes that real: engineering users author models in the product, with no repository change.
- **No OS isolation in the runner.** `runner/local_python.py` launches a clean subprocess with a timeout and path confinement. It sets no resource limits, blocks no network and has no filesystem jail. The AST policy is lint.
- **Precedent.** `relay_gateway/sandbox.py` already runs agent CLIs under bubblewrap. On the normal WSL2 host, bubblewrap 0.9 ran the backend interpreter with network, PID and `/tmp` unshared and imported `numpy` and `build123d`.

## Decision

1. **One owner.** A new `studio_runtime` backend module is the only path that executes user-authored Python. The runner's bundled-only boundary does not change. `bluecad_l2_v0` stays disabled.
2. **Mechanism.** Each execution is one short-lived bubblewrap sandbox around the backend interpreter:
   - all namespaces unshared, including network and PID;
   - environment cleared, then a fixed minimal environment;
   - the system and the Python environment mounted read-only;
   - one per-run scratch directory as the only writable path; it is removed afterwards;
   - no mount of the data root, the repository, the home directory or Windows drives;
   - the sandbox dies with its parent.
3. **Limits.** Every run has a wall-clock timeout that kills the whole sandbox, plus CPU-time, address-space, process-count and file-size limits, and caps on captured stdout, stderr and result bytes. Defaults are fixed in code. A caller may lower them and may not raise them above the module maximum.
4. **Typed channel.** The host passes one JSON request and reads one JSON result file. It validates the result (size, JSON, finite numbers) before anything else uses it. The backend process never imports, compiles or executes user source. Parsing with `ast.parse` for documentation is allowed.
5. **Fail closed.** If bubblewrap is missing, or the start-up self-probe fails, the runtime reports `unavailable` with a reason and refuses to execute. There is no fallback to an unisolated subprocess. Native Windows is `unavailable` in this slice.
6. **Off by default.** Execution is refused unless the operator has set `JARVISOS_STUDIO_USER_CODE_ENABLED=1` (read through `core/config.py`). The status route reports enabled, available, mechanism and reason.
7. **Explicit action.** Only an explicit mutating request executes code. Saving, listing, documentation and status never execute it.
8. **Record.** Each run returns the source SHA-256, the limits applied, the mechanism, duration, exit classification (`ok`, `error`, `timeout`, `limit`, `invalid_result`, `unavailable`, `disabled`) and truncated logs.
9. **Trust-boundary document.** `docs/runner-trust-boundary.md` gains a section that describes this runtime as the separate isolation boundary, lists what it does and does not contain, and keeps the runner invariant intact.

## Acceptance

Each item is proven by a test that runs a real bubblewrap sandbox on the qualification host. A hostile test that is skipped on that host counts as a failure.

1. **Network.** A script that opens a TCP connection to a public address, and to a listener that the test starts on host loopback, fails in both cases.
2. **Filesystem read.** A script cannot read a canary file placed in the data root, in the repository or in the home directory.
3. **Filesystem write.** A script cannot create or modify a file outside its scratch directory. The Python environment is read-only. The scratch directory does not exist after the run.
4. **Environment.** A secret set in the backend environment is not visible to the script.
5. **Processes.** A script cannot see or signal a host process.
6. **Timeout.** An infinite loop is killed at the wall-clock limit and classified `timeout`. No sandbox process survives.
7. **Memory.** An allocation above the address-space limit is classified `limit` or `error`. The backend stays alive.
8. **Fork bomb.** Process creation beyond the limit fails. The run ends within the timeout and leaves no process.
9. **Output flood.** Oversized stdout and an oversized result are truncated or rejected at the caps.
10. **Result validation.** A malformed result, a non-finite number, or a missing result is classified `invalid_result`.
11. **Scientific stack.** A script imports `numpy`, `scipy` and `pint` and returns a computed value.
12. **Fail closed.** With bubblewrap made unavailable the runtime reports `unavailable` and executes nothing. With the setting off it reports `disabled` and executes nothing.
13. **Backend isolation.** No code path in the backend process executes user source: a test asserts that the module reaches user source only through the sandbox launcher.

## Required evidence

- The hostile-code suite above, executed on the WSL2 qualification host, with pass, fail and skip counts recorded.
- CI: the suite runs in CI when the runner allows unprivileged user namespaces. If it cannot, the CI job states that explicitly and the qualification-host run is the evidence.
- Full backend suite, ruff and the registry checks.
- An independent adversarial review that tries to escape the sandbox on the exact head.

## Non-goals

- No multi-tenant or internet-facing hardening, no custom seccomp filter, no cgroup controller.
- No native Windows isolation. A Job Object tier is parked.
- No automatic execution of AI-generated code. The Sidecar gains no execution authority.
- No change to runner registration, to bundled implementations or to BLUECAD typed parts.
- No hardware control.
