# 068 — HERMES-CONFIG-0: pinned, isolated, policy-verifiable Hermes profile

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 066, 067

## Problem

A repository `cli-config.yaml` is not a security boundary by itself.

Hermes can expose broad terminal, filesystem, browser, web, computer-use, cron,
messaging, delegation, auxiliary-model, fallback-model, and MCP capabilities.
Terminal deny patterns govern command strings; they do not prove filesystem
isolation. Main-model custom-provider configuration also does not prove that every
auxiliary or delegated model call uses the JarvisOS passthrough.

JarvisOS needs one versioned profile whose **effective runtime configuration** is
validated, fingerprinted, and fail-closed.

## Maintainer direction

- Pin Hermes by immutable version identity and fingerprint.
- Configure only the JarvisOS passthrough as model provider.
- Configure only the bounded JarvisOS MCP server for domain access.
- Keep Hermes' own workspace disposable.
- Prevent direct access to the JarvisOS repository and data root.
- Disable browser, web search, computer use, cron, proactive triggers, messaging,
  and unrelated MCP servers until separately specified.
- Keep personas/subagents advisory and economically bounded.
- Reuse the model-bench identity-probe pattern without making the benchmark repo a
  production dependency.

## Required future contract

### 1. Immutable identity

The full spec must select and record:

- upstream repository;
- immutable commit SHA or release tag resolved to a commit;
- source-tree or package fingerprint;
- license identity and notice obligations;
- Python/package lock identity;
- compatibility-test identity;
- approved upgrade and rollback procedure.

A moving branch, “latest”, repository size, or “production-grade” label is not an
identity or acceptance criterion.

### 2. Dedicated runtime home

Use a dedicated `HERMES_HOME` and workspace for JarvisOS operation.

The runtime home must not reuse a developer's general Hermes profile containing
provider OAuth sessions, API keys, unrelated MCP servers, skills, cron jobs, or
fallback configuration.

The committed profile contains no secret. Local passthrough/MCP credentials are
injected through a protected runtime overlay.

### 3. Model-call closure

The startup validator must prove that:

- the primary model provider is JarvisOS custom passthrough;
- every auxiliary model slot used by the pinned version resolves to the
  passthrough or is disabled;
- context compression, title/session helpers, approval helpers, subagents, and
  any other model-backed feature cannot select a direct provider;
- fallback provider/model lists are empty or contain only JarvisOS policy aliases
  through the same passthrough;
- subagent overrides cannot introduce a direct provider;
- no provider key, OAuth session, or provider-specific environment variable is
  visible to the Hermes process.

Any unresolved model path fails startup.

### 4. Tool allowlist

Start from an explicit allowlist, not the default broad tool catalog.

The initial profile may expose only:

- the JarvisOS MCP tools from spec 067;
- bounded delegation if required by the first dogfood;
- minimal non-authoritative planning/clarification tools proven necessary.

Terminal, filesystem, browser, web/search, computer use, cron, proactive,
messaging, code execution, tool gateway, and unrelated MCP tools are disabled by
default.

Terminal deny patterns may be retained only as supplemental defense-in-depth.

### 5. Host isolation

Use a dedicated OS identity, container, or equivalent mandatory access boundary
so the Hermes process:

- can access only its disposable workspace and required loopback endpoints;
- cannot read or write the JarvisOS repository;
- cannot read or write the JarvisOS data root;
- cannot follow symlinks, junctions, mount escapes, or alternate path forms into
  protected roots;
- cannot reach external provider endpoints directly;
- cannot inherit provider credentials or unrelated user secrets.

The full spec must choose the concrete Windows-first isolation mechanism and state
its residual risk. A prompt, system message, deny glob, or current working
directory is not sufficient.

### 6. MCP configuration

- Configure only the JarvisOS MCP server.
- Set `sampling.enabled: false`.
- Keep parallel tool calls disabled unless a specific read-only tool is later
  proven safe.
- Bound connection timeout, per-call timeout, lifetime, and reconnect behavior.
- Use loopback/stdio authentication consistent with spec 067.
- Do not place credentials in the committed YAML.

### 7. Delegation bounds

Freeze conservative defaults for the first profile:

- maximum spawn depth: one;
- nested orchestration: disabled;
- maximum concurrent children: explicitly bounded;
- maximum iterations per parent and child: explicitly bounded;
- child wall-clock timeout: explicitly bounded;
- maximum tool calls and model calls per job: explicitly bounded;
- per-job token/cost envelope supplied and enforced by JarvisOS;
- child model aliases restricted to passthrough-offered models;
- final child summaries remain advisory.

The exact numbers belong in the full spec and must be justified by dogfood
measurements. Hermes configuration is not the authoritative budget gate.

### 8. Scheduled and proactive work

Cron, heartbeat, proactive triggers, background polling, and auto-resume are
disabled.

Future scheduled work begins under a JarvisOS-owned policy/job record and invokes a
bounded Hermes session only after a separate spec defines scheduling, retries,
ownership, cancellation, and budget.

### 9. Effective-config preflight

A deterministic preflight must print or persist safe evidence for:

- Hermes identity and fingerprint;
- effective provider/base URL host;
- absence of direct-provider credentials;
- enabled tool names;
- MCP servers and sampling/parallel settings;
- delegation limits;
- cron/proactive state;
- workspace and protected-root access checks;
- direct external egress denial;
- config digest and policy version.

The preflight fails closed on unknown fields, unresolved environment overrides,
unexpected plugins, unexpected skills/toolsets, or identity mismatch.

## Required tests

The full spec must test:

- config precedence and environment override attacks;
- stale or altered Hermes source identity;
- unexpected provider OAuth/key material;
- auxiliary and subagent direct-provider bypass;
- fallback-provider bypass;
- default-tool leakage;
- terminal absolute-path, traversal, symlink, and junction access;
- JarvisOS repo/data-root read and write attempts;
- direct external-provider network attempts;
- browser/computer/cron/proactive disabled state;
- MCP sampling disabled;
- bounded delegation depth, concurrency, iterations, timeout, and cancellation;
- kill switch and rollback to a known-good pinned profile.

## Hard lines

- Hermes is an untrusted advisory orchestrator, not a policy or authority process.
- No direct provider credential, canonical database access, repository access,
  data-root access, promotion, sensitivity decision, route ownership, or budget
  override.
- No claim of sandboxing based only on YAML deny rules.
- No version drift without a new fingerprint and compatibility evidence.

## Non-goals

No runtime activation, provider integration, browser/computer use, autonomous
cron, remote deployment, plugin ecosystem enablement, general developer profile,
Hermes fork, vendoring, or modification of Hermes internals.

## Promotion evidence

Before this row may become `ready`, the full spec must:

1. select a concrete pinned Hermes identity;
2. select and test the host isolation mechanism;
3. enumerate every effective model and tool path in the pinned version;
4. define the committed profile plus secret-free runtime overlay;
5. include startup-preflight, bypass, and rollback tests;
6. bind to completed 066 and 067 compatibility contracts.
