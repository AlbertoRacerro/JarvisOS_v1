# 068 — HERMES-CONFIG-0: pinned isolated runtime activation and rollback

Status: planned full-spec draft, not implementation-ready. `docs/specs/STATUS.md` is
authoritative. This contract must not become `ready` until 066 and 067 implementations
are merged as disabled interfaces, one concrete Windows-first isolation mechanism is
accepted, and a pinned Hermes build passes the complete compatibility, session, and
bypass suite.

Depends on: 066, 067

Durable decision: ADR-060

## Goal

Install, configure, bind, launch, supervise, deactivate, and roll back one pinned Hermes
runtime without transferring JarvisOS authority or creating an uncontrolled second
conversation/memory system.

068 is the only slice allowed to transition the merged disabled 066 model boundary and
067 read-only MCP boundary into a production-reachable state. It owns:

- the protected runtime profile and disposable workspace;
- the JarvisOS-owned session gateway;
- actual private transport and runtime credential injection;
- effective-configuration and content-boundary preflight;
- process lifecycle and activation state;
- session-content retention/cleanup;
- kill switch and rollback.

Hermes remains an untrusted advisory orchestrator. JarvisOS retains:

- operator/workspace/flow/session authority;
- provider credentials and provider/network permission;
- 059a sensitivity and derivative authority;
- 059b packet, sanitization, confirmation, reservation, and audit authority;
- 061 flow state, continuation, budget, usage, accounting, and terminality authority;
- 062 human-grade authority;
- canonical records, proposals, promotion, BLUECAD, runner, and evidence authority;
- all production 066/067 activation state.

## Preconditions and sequencing

068 implementation may begin only after 066 and 067 are merged and stable in a disabled
state.

The merged prerequisites must prove:

- 066 text-only requests traverse `run_ai_task`, 059b, 061, and `ai_jobs`;
- 066 has no production listener, retry/replay bypass, or provider credential;
- 067 advertises exactly the accepted read-only S0/S1 tool catalog and no mutation tool;
- 067 has no production listener, provider call, domain SQL, path authority, or status
  mutation authority;
- both boundaries expose a server-owned activation interface that ordinary settings,
  environment drift, requests, models, and tools cannot invoke.

068 does not patch, fork, or vendor Hermes to bypass incompatible client behavior. Any
compatibility mismatch returns the relevant definition to planning.

## Immutable runtime identity

Select exactly one Hermes release/tag and resolve it to:

- upstream repository and distribution identity;
- immutable commit SHA;
- source-tree/package and executable/entry-point fingerprints;
- Python runtime and dependency-lock identity;
- license identity and required notices;
- accepted 066 fixture-bundle and compatibility-matrix digests;
- accepted 067 protocol/catalog/schema fixture digests;
- 068 profile, session-gateway, retention, and preflight-policy versions.

A moving branch, `latest`, unconstrained dependency, cached environment, version string
without fingerprints, or locally modified source fails closed.

Any upgrade creates a new candidate identity and passes the full 066/067/068 suite before
replacing the active identity. In-place drift is forbidden.

## Dedicated runtime home

Use a dedicated runtime OS identity, `HERMES_HOME`, configuration root, cache root, and
disposable workspace reserved for JarvisOS operation.

The runtime must not reuse a developer's general Hermes profile, OAuth sessions, API
keys, skills, MCP servers, cron state, history, plugins, fallback configuration, or
conversation cache.

Committed configuration contains no secret. Runtime overlays contain only opaque secret
references or process-injected values and are excluded from repository files, reports,
logs, diagnostics, and normal frontend state.

The disposable Hermes workspace:

- is not canonical memory, a backup, or an evaluation corpus;
- is inaccessible to unrelated host/guest identities;
- is excluded from cloud sync, desktop search indexing, backup, and telemetry unless a
  future accepted policy explicitly provides equivalent protection and deletion;
- cannot be imported automatically into later sessions, prompts, retrieval, training, or
  MemoryStore;
- may be destroyed or rolled back without deleting JarvisOS flows, attempts, grades,
  domain records, or evidence.

## JarvisOS-owned session gateway

The production profile is not a general-purpose Hermes CLI/profile. Only a trusted
JarvisOS operator action may create a production Hermes session.

The session gateway must:

- create and bind one server-owned 061 flow, workspace, operator, runtime profile, and
  session identity;
- issue the scoped 066/067 flow grants and runtime session capability;
- deliver operator input only through the accepted structured ingress;
- classify every initial and follow-up operator input using current JarvisOS sensitivity
  authority before it reaches Hermes;
- bind all model/tool calls, results, retries, lifecycle events, and final output to the
  same flow/session identity;
- revoke the session capability on expiry, terminal completion, cancellation, drift,
  kill switch, or operator stop.

Forbidden:

- direct interactive use of the production `HERMES_HOME` outside the gateway;
- starting the production entry point manually with inherited user credentials;
- attaching an unrelated client to an active session;
- resuming from a Hermes-native history ID without a current JarvisOS session/flow grant;
- importing arbitrary existing Hermes conversations into the production profile.

A developer may use a separate non-production Hermes profile, but it receives no 066/067
production credentials and is not covered by JarvisOS authority claims.

## Initial session-content boundary

V0 sends to Hermes only:

- current S0/S1 operator input;
- a current approved effective-S0/S1 derivative exactly covering a higher-sensitivity
  source;
- the read-only S0/S1 067 tool results and manifests;
- normalized model results already accepted through the 066/059b boundary.

Raw S2/S3/S4, unknown, stale, malformed, cross-workspace, and deterministic secret-
bearing input is withheld before Hermes ingress. S4 and secrets remain forbidden.

If operator input is above S1 and no approved current derivative exists, the gateway
returns a safe withheld/review-required outcome and does not start or continue a Hermes
turn with the raw body.

A future numbered sensitive-local amendment may allow raw S2/S3 only after proving:

- the accepted 068 isolation and content-retention controls;
- an entirely local-only qualified model path for the consuming turn and every helper;
- no external provider reuse, compression, summarization, fallback, or later replay of
  the raw material;
- operator-controlled capability and revocation;
- bounded protected retention and deletion;
- updated 066/067 provenance and egress tests.

Transport locality alone is not permission to expose sensitive content.

## Session content retention and deletion

Hermes may hold active-session content only in process memory and the protected disposable
workspace required by the pinned build.

V0 rules:

- no cross-session conversation history, automatic memory, semantic index, or persistent
  user profile is enabled;
- no prompt, response, tool-result body, or session transcript enters ordinary logs,
  activation records, safe events, crash reports, or preflight evidence;
- retain operational bodies only while the flow is active and for a bounded recovery
  window ending no later than one hour after terminal state or earlier flow/session
  expiry;
- kill switch, cancellation, profile drift, failed activation, and rollback trigger
  cleanup as soon as recovery is no longer valid;
- cleanup removes session bodies, caches, temporary files, local indexes, and native
  Hermes history while preserving only JarvisOS canonical digests, attempts, capsules,
  accounting, and safe lifecycle evidence;
- deletion is verified against the accepted runtime-home manifest and records a safe
  cleanup result/digest, not filenames or content;
- failed or incomplete cleanup leaves the runtime non-active and requires operator
  remediation before reactivation;
- rollback never copies old session content into the replacement profile.

If the pinned Hermes build cannot disable or reliably clean native history/cache within
this contract, activation fails and the definition must be amended rather than silently
retaining content.

## Windows-first isolation boundary

Before promotion, maintainers select and document one concrete Windows-first mandatory
isolation mechanism using a dedicated OS identity, VM/container boundary, or equivalent
access-control boundary proven by tests.

The chosen boundary ensures the Hermes process:

- can read/write only its dedicated runtime home and disposable workspace;
- cannot read, write, enumerate, map, or traverse the JarvisOS repository/data root;
- cannot escape through symlinks, junctions, alternate paths, mount mappings, network
  shares, inherited handles, or parent-directory access;
- cannot inherit provider credentials, browser sessions, SSH keys, unrelated API keys,
  or developer environment secrets;
- cannot reach external model/provider endpoints directly;
- can reach only approved private 066/067 endpoints and strictly required local OS
  services;
- cannot expose a listener to the public internet or general LAN.

A working directory, prompt, deny glob, terminal deny list, or committed YAML is not an
isolation boundary. Residual risk and unsupported Windows configurations are explicit.

## Private transport and endpoint binding

068 selects the actual address, namespace, firewall rules, and credential audience for
066 and 067.

Rules:

- same-namespace loopback is allowed only when the selected isolation design proves the
  intended shared namespace;
- a separate VM/guest uses proven host-only/private transport, never the guest's own
  `127.0.0.1` as an assumed host address;
- wildcard, public, LAN-general, forwarded-remote, and general reverse-proxy exposure are
  forbidden;
- 066 and 067 use distinct credential audiences and may use distinct endpoints;
- forwarded headers, source IP alone, and model-visible tokens cannot establish trust;
- only the pinned runtime identity and current scoped credential may connect;
- unrelated host/guest processes fail connection/authentication tests;
- endpoints remain disabled until the exact activation transaction succeeds.

Transport configuration is server-owned/versioned. Environment or profile fields may
select only an accepted 068 transport identity; they cannot introduce a new host, port,
socket, proxy, or credential source.

## Effective model configuration

The effective runtime configuration proves:

- the sole enabled model provider is 066;
- every primary, planner, compression, summarization, title, approval, auxiliary,
  delegated, vision, and helper model slot resolves to an allowed JarvisOS logical alias
  through 066 or is disabled;
- provider/model fallback lists are empty;
- Hermes-side model retries are `0`;
- no raw provider URL/model, OAuth session, API key, or provider-specific environment
  variable is visible;
- unknown model-backed features and dynamically discovered providers fail preflight.

The validator inspects final effective configuration after defaults, includes,
environment overlays, runtime discovery, and plugin loading.

## Effective tool configuration

Initial activation exposes only the merged 067 v0 catalog:

1. `jarvis_context_preview`;
2. `jarvis_search_records`;
3. `jarvis_bluecad_inspect_candidate`;
4. `jarvis_query_evidence`.

Bind exact canonical server names, Hermes-visible names, schema digests, catalog digest,
and compatibility version accepted by 067.

Unavailable in v0:

- terminal, shell, Python, code execution, filesystem, roots, arbitrary file tools;
- browser, web search, computer use, messaging, external network tools;
- cron, heartbeat, proactive triggers, background polling, auto-resume;
- MCP sampling, prompts, resources, subscriptions, elicitation, server-initiated model
  calls;
- unrelated MCP servers/tool gateways;
- MemoryStore proposal, calculation execution, BLUECAD creation, promotion, archive,
  delete, or other mutation tools.

Unknown, transformed-with-drift, widened, dynamically added, or schema-mismatched tools
fail preflight. Terminal deny patterns are defense in depth only; terminal remains absent.

## Delegation and agent bounds

Initial v0 disables Hermes delegation and sub-agent spawning:

- maximum spawn depth `0`;
- maximum child agents `0`;
- nested orchestration disabled;
- child model override unavailable.

A later numbered amendment may enable bounded advisory delegation only after measured
single-agent dogfood and explicit depth, concurrency, iteration, model/tool-call,
wall-time, cancellation, content, and 061 economic limits.

Hermes configuration is never the authoritative budget gate.

## Runtime credentials

Generate separate rotatable/revocable local credentials for 066 and 067 outside committed
configuration.

Required properties:

- distinct audience, verifier, and rotation identity;
- binding to pinned runtime/profile and current activation/session generation;
- bounded lifetime or explicit session generation;
- storage only in the accepted local secret facility;
- injection only into the isolated process at activation;
- no exposure in visible command lines, committed files, process diagnostics, ordinary
  logs, crash reports, preflight output, or UI state;
- revocation before termination during emergency shutdown where feasible;
- invalidation on profile, binary, configuration, isolation, or session drift.

A credential proves client identity only. 066/067 still require current flow/capability
grants.

## Effective-config preflight

Before every activation or restart, run a deterministic fail-closed preflight over the
exact candidate runtime.

Verify and record safe evidence for:

- immutable Hermes/Python/dependency/executable fingerprints;
- committed profile and protected overlay digests without secret values;
- session-gateway, ingress-sensitivity, retention, and cleanup policy versions;
- effective model-provider/logical-alias map;
- absence of provider credentials/provider-specific environment variables;
- enabled tools/MCP servers plus schema/catalog digests;
- sampling, resources, prompts, parallel calls, delegation, cron, proactive, history,
  memory, indexing, telemetry, and plugin states;
- actual endpoint identities and credential audiences;
- runtime-home/disposable-workspace identities and allowed manifest;
- repository/data-root read/write/traversal/symlink/junction probes;
- unrelated host/guest connection denial;
- direct external provider/network denial;
- production entry-point denial outside the session gateway;
- native history/cache cleanup capability and recovery-window limits;
- kill-switch and rollback target identity;
- 066, 067, 059a/b, 061, and activation-policy versions.

Unknown fields, unresolved overrides, unexpected skills/plugins/toolsets, fingerprint
mismatch, incomplete probes, stale evidence, enabled native history, or unproven cleanup
fail preflight.

Preflight evidence contains no secret, prompt/context body, 062 note, raw path beyond
approved safe identifiers, or arbitrary environment dump.

## Activation state machine

Persist one server-owned activation record with states:

- `disabled`;
- `preflight_passed`;
- `activating`;
- `active`;
- `draining`;
- `failed`.

Bind:

- runtime/profile/isolation/transport/session-policy identities and digests;
- 066/067 endpoint/policy versions;
- credential-generation references, never values;
- preflight digest/expiry;
- process identity/health;
- activation, heartbeat, drain, stop, cleanup, failure, rollback timestamps;
- operator action/idempotency identity;
- last known-good rollback target.

Only explicit trusted operator action may activate. Models, Hermes, MCP, provider
responses, ordinary AI tasks, environment changes, automatic startup, cron, and
background agents cannot activate/reactivate.

Activation transaction:

1. verify 066/067 remain disabled/version-compatible;
2. verify fresh exact preflight for the candidate identity;
3. claim activation idempotently;
4. create/rotate scoped credential generations;
5. inject protected runtime overlays;
6. start the isolated process under accepted identity with no session content;
7. enable private bindings only for that process identity;
8. run bounded authenticated health, gateway, cleanup, and negative-bypass probes;
9. transition to `active` only if every check passes;
10. otherwise revoke credentials, disable endpoints, terminate process, clean disposable
    content, record safe failure evidence, and remain non-active.

A partial activation never leaves an unauthenticated endpoint, live process with valid
credentials, or uncleared session content.

## Runtime supervision

The JarvisOS controller supervises process, gateway, transport, and cleanup lifecycle but
does not own AI/domain authority.

It may:

- verify process/session identity and bounded health;
- create/revoke session capabilities;
- revoke credentials and disable endpoints;
- request drain/termination;
- verify bounded content cleanup;
- record safe lifecycle evidence;
- invoke rollback.

It may not:

- call providers/adapters;
- consume 059b confirmation tickets;
- create/mutate canonical records;
- promote BLUECAD/evidence/proposals;
- change sensitivity, route, provider permission, budget, or grades;
- declare a 061 flow terminal because Hermes exits/disconnects;
- retain or reuse session bodies after expiry.

The 061 flow service remains terminality authority. `confirmation_required` stays
nonterminal after Hermes exits and resumes only through the direct operator surface.

V0 does not auto-restart after crash, preflight failure, credential revocation, cleanup
failure, or isolation drift. A new explicit operator action and fresh preflight are
required.

## Kill switch, drain, and rollback

Provide one trusted local kill switch that fail-safely:

1. prevents new sessions, grants, and 066/067 requests;
2. transitions activation to draining/failed;
3. revokes session and runtime credentials;
4. disables private bindings;
5. requests bounded graceful termination, then force-terminates if required;
6. cleans session bodies/caches when recovery is no longer valid;
7. preserves canonical 059b/061/`ai_jobs` evidence;
8. reports affected nonterminal flows honestly without fabricating cancellation;
9. records safe shutdown/cleanup evidence;
10. returns to `disabled` only after required cleanup or explicit remediation state.

Rollback selects a previously accepted immutable runtime/profile/isolation/session-policy
bundle. It uses fresh credentials and preflight, never copies old session content, and
leaves the system disabled on failure.

## Scheduled and proactive work

Cron, heartbeat-initiated tasks, proactive triggers, background polling, autonomous
resume, scheduled sessions, and scheduled activation are disabled.

Future scheduled work requires a JarvisOS-owned job/policy specification defining
ownership, retries, cancellation, confirmation, sensitivity, content retention, and 061
economics.

## Persistence and migration discipline

Use the next additive migration after merged 066/067; do not freeze its number now.

Persistence may include:

- accepted runtime/profile/isolation/transport/session-policy bundle metadata;
- safe preflight and cleanup evidence/digests;
- activation/session operation claims and state;
- credential-generation references;
- process/health/kill-switch/rollback metadata.

Store no credential values, prompt/context/result bodies, session transcripts, 062 notes,
provider secrets, arbitrary environment dumps, or copies of canonical domain data in
activation persistence.

Migration is additive/idempotent on fresh/immediate-predecessor databases. Upgrade never
starts Hermes, binds an endpoint, creates a session, or imports native history.

## Required tests

### Identity and configuration

- stale/altered/moving/modified runtime identities fail;
- dependency/profile/schema/session-policy digest drift fails;
- config precedence/environment override attacks fail;
- every model path resolves through 066 or is disabled;
- retries/fallbacks/provider credentials remain absent;
- only exact 067 tools/names/schemas enabled;
- unknown plugins/skills/tools/MCP/capabilities fail.

### Session ingress and retention

- production profile cannot be used directly outside the gateway;
- every session binds current operator/workspace/flow/profile capability;
- initial/follow-up S0/S1 input succeeds under scope;
- higher-sensitivity raw input is withheld before Hermes receives it;
- current approved S0/S1 derivative may be used with exact coverage/provenance;
- S4/secrets never enter runtime;
- native cross-session history, memory, indexing, sync, backup, and telemetry are absent;
- session bodies expire by flow/session expiry or one-hour post-terminal maximum;
- kill switch/cancel/drift/rollback cleanup is verified;
- cleanup failure blocks activation;
- old session content never enters new/rollback profile or future prompt.

### Isolation and transport

- Hermes cannot read/write/enumerate repository/data root;
- absolute paths, traversal, symlinks, junctions, alternate forms, shares, inherited
  handles, and mount escapes fail;
- unrelated host/guest/LAN processes cannot reach 066/067;
- direct external provider/model access fails;
- wildcard/public/LAN/proxy exposure fails;
- endpoint identities/audiences cannot be swapped;
- accepted loopback/private topology works only as specified.

### Credential safety

- credentials absent from committed config/logs/diagnostics/reports/UI/crash evidence;
- stale/wrong-audience/cross-profile/cross-session/revoked credentials fail;
- activation failure/kill switch revoke credentials;
- restart/rollback use fresh generations.

### Activation state machine

- only explicit trusted operator action activates;
- startup/environment/request/model/tool/cron cannot;
- duplicate activation is idempotent and concurrency has one winner;
- stale preflight/changed bundle/version fails;
- every partial-failure point returns endpoint/process/credentials/content to safe
  non-active state;
- active requires positive health/gateway/cleanup and negative-bypass probes;
- crash/drift/cleanup failure does not auto-restart.

### Flow and authority preservation

- all model calls traverse 066, 059b, 061, and `ai_jobs`;
- all MCP calls remain four read-only 067 tools with audit evidence;
- controller cannot consume confirmation or mutate route, sensitivity, budget, grade,
  records, evidence, or BLUECAD;
- Hermes exit cannot terminalize nonterminal 061 flow;
- confirmation remains resumable through direct operator surface;
- kill switch preserves canonical attempts/accounting and reports incomplete flows.

### Disabled capabilities

- terminal/filesystem/browser/web/computer/messaging/code tools absent;
- sampling/resources/prompts/elicitation/unrelated MCP absent;
- delegation/sub-agents disabled;
- cron/proactive/background/auto-resume disabled;
- mutation tools/direct provider access absent.

### Kill switch and rollback

- kill switch prevents new work before shutdown;
- credentials/endpoints revoked even if graceful stop fails;
- session cleanup follows bounded recovery policy;
- rollback requires fresh preflight/credentials and imports no history;
- failed rollback remains disabled;
- canonical domain/flow/attempt evidence is preserved.

Run full backend tests, applicable frontend/operator-control tests, Ruff,
status-registry self-test, 066/067 compatibility suites, and BLUECAD real-tool proof
without live provider calls in CI.

## Non-goals

No public/remote Hermes service, raw S2/S3 v0 session, browser/computer/search,
terminal/filesystem access, mutation MCP tools, autonomous cron/proactive operation,
automatic restart, cross-session Hermes memory, general developer profile, plugin
marketplace, provider integration inside Hermes, direct canonical database access,
Hermes fork/vendor patch, or replacement of JarvisOS policy/state/services.

## Promotion gates

Before `STATUS.md` may move 068 to `ready`:

1. 066 and 067 implementations are merged, disabled, and stable.
2. One immutable runtime/dependency identity is accepted.
3. One concrete Windows-first isolation mechanism/residual-risk statement is accepted.
4. Actual private transport/firewall topology is selected.
5. Complete effective model/tool/history/memory configuration is fail-closed.
6. Session gateway, S0/S1 ingress, withholding, retention, cleanup, and direct-profile
   denial are accepted.
7. Delegation, mutation, scheduling, browser, terminal, unrelated MCP, and raw S2/S3 are
   disabled initially.
8. Credential storage/injection/audience/session separation is accepted.
9. Activation partial-failure cleanup, supervision, kill switch, and rollback are
   accepted.
10. Migration ID is assigned from implementation-time `master`.
11. Exact-head CI and independent review have no unresolved blockers.
