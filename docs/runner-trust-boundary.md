# Runner trust boundary

JarvisOS currently runs as a single-operator, loopback-first application. The
runner cleanup removes caller authority over executable source so the API can
later be exposed to additional product surfaces without inheriting an
unnecessary code-upload contract.

> JarvisOS runner execution is a trusted-code execution boundary, not a hostile-code sandbox. Static policy checks, digest verification, path confinement, a clean subprocess launch, output contracts, and timeouts reduce mistakes and preserve evidence for reviewed implementations. They do not safely contain malicious Python. Caller-controlled and automatically AI-generated Python therefore remain non-executable unless and until a separate OS-isolation specification is implemented and independently proven.

No runtime status, error code, API field, UI label, runbook, test name, or
implementation report may imply stronger isolation. The AST policy remains a
lint and defense-in-depth check over reviewed bundled code.

## Final invariant

> JarvisOS may execute exact reviewed Python that the server and maintainer already trust. It may not execute Python merely because a caller, model, route, old database row, AST checker, or successful previous run says that it is trusted.

A future feature that executes untrusted or automatically AI-generated code
requires a separate specification with real OS-level isolation, hostile-code
tests against that boundary, resource and network controls, and explicit
maintainer acceptance.

## Reopen triggers

Reopen measured runner-isolation work only when at least one condition becomes
real:

- JarvisOS listens on a non-loopback interface;
- a second user can reach the application;
- a remote agent can reach runner mutation or execution routes;
- Hermes or MCP receives runner execution authority;
- a genuinely non-bundled implementation must execute and git-based bundling is
  demonstrably inadequate.

The Origin check on mutating runner routes is a browser/CSRF guard. It is not
authentication: origin-less local clients remain valid, and a local process can
construct its own HTTP request.
