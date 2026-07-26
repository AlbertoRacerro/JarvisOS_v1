# Runner trusted-code boundary

JarvisOS currently operates as a single-user, loopback-bound application. The
runner cleanup removes executable-source authority from request contracts so the
same API can later be exposed to additional product surfaces without silently
turning caller data into executable code. It does not create or claim a hostile-code
sandbox.

## Binding security statement

> JarvisOS runner execution is a trusted-code execution boundary, not a hostile-code sandbox. Static policy checks, digest verification, path confinement, a clean subprocess launch, output contracts, and timeouts reduce mistakes and preserve evidence for reviewed implementations. They do not safely contain malicious Python. Caller-controlled and automatically AI-generated Python therefore remain non-executable unless and until a separate OS-isolation specification is implemented and independently proven.

No runtime status, error code, API field, UI label, runbook, test name, or
implementation report may imply stronger isolation. The AST policy remains a
lint and defense-in-depth check for reviewed bundled code; it is not execution
authority.

## Final invariant

> JarvisOS may execute exact reviewed Python that the server and maintainer already trust. It may not execute Python merely because a caller, model, route, old database row, AST checker, or successful previous run says that it is trusted.

## Reopen triggers

Create a new measured runner-isolation specification only when at least one of
these conditions becomes real:

- JarvisOS listens on a non-loopback interface;
- a second user can reach the application;
- a remote agent can reach runner mutation or execution routes;
- Hermes or MCP receives runner execution authority;
- a genuinely non-bundled implementation must execute and git-based bundling is inadequate.

Until a trigger exists, broad container, VM, signing-root, interpreter-audit, or
hostile-code-sandbox work is out of scope.
