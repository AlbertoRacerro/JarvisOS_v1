# 067 — JARVIS-MCP-0: disabled read-only domain-tool boundary

Status: planned compatibility/domain-tool draft, not implementation-ready.
`docs/specs/STATUS.md` is authoritative. This contract must not become `ready` until
one pinned Hermes/MCP identity, captured name/schema/reconnect fixtures, and all four
read-service mappings are accepted.

Depends on: 005, 010, 040, 042, 043, 044, 059a

Durable decision: ADR-060

## Goal

Implement a disabled-by-default, transport-abstract MCP boundary exposing four bounded
read-only JarvisOS domain tools. It must not expose SQLite, repository/data-root paths,
provider adapters, credentials, arbitrary code, filesystem/network operations,
promotion, mutation, sensitivity downgrade, routing, budget, or final-state authority.

All 067 tools make zero AI/provider calls. MCP is a strict adapter over owning JarvisOS
services, not a second domain implementation.

## V0 tool catalog

The only implementable and advertiseable v0 tools are:

1. `jarvis_context_preview`;
2. `jarvis_search_records`;
3. `jarvis_bluecad_inspect_candidate`;
4. `jarvis_query_evidence`.

The following previously proposed mutation/execution names are **not part of 067 v0**
and must not appear in `tools/list`, schemas, runtime dispatch, or capability grants:

- `jarvis_propose_record`;
- `jarvis_run_calc_v0`;
- `jarvis_bluecad_create_candidate`.

They require one or more future numbered specs after pinned fixtures prove stable
server-verifiable tool-call identity through reconnects and each owning service passes
an independent idempotency/compatibility review. No model-visible `operation_key` can
serve as mutation authority.

## Why this remains a compatibility draft

Before implementation, captured fixtures from the same immutable Hermes identity used
by 066 must prove:

- exact MCP protocol/version and Streamable HTTP behavior;
- authentication/session metadata supported by the pinned client;
- exact canonical server tool names;
- exact client/model-visible effective names, including any server-name prefixing;
- input/output schema bytes and canonical digests;
- tool-call/result IDs;
- read-call retry and reconnect behavior;
- whether structured content and text fallback are both required.

If those facts cannot be proven without patching Hermes or broadening authority, amend
the design. Do not grant filesystem/database access as a workaround.

## Disabled implementation versus 068 activation

067 may be implemented before 068 only as a disabled, transport-abstract server
contract exercised through captured local fixture harnesses.

Implementation rules:

- activation state defaults to `disabled`;
- importing, migrating, testing, or starting ordinary JarvisOS binds no production MCP
  listener;
- bind address, port, socket family, private-network identity, and production credential
  source are injectable only through a server-owned activation interface;
- ordinary settings, environment drift, MCP requests, tool arguments, and model content
  cannot activate or select transport;
- fixture tests may use in-process or same-namespace loopback only as test plumbing;
- passing loopback tests is not production isolation evidence;
- no wildcard, LAN-general, public, forwarded-remote, or reverse-proxied exposure is
  enabled by 067.

After 066 and 067 are merged, 068 selects and proves the actual Windows-first private
transport/isolation, injects scoped credentials, configures the pinned runtime, and
activates the endpoint. A separate VM cannot reach a host service through its own
`127.0.0.1`; 068 owns real addressing and firewall policy.

## Protocol subset

Advertise only fixture-proven methods/capabilities. Intended v0:

- `initialize` / `notifications/initialized`;
- `ping`;
- `tools/list`;
- `tools/call` for the four read-only tools;
- bounded cancellation only if the pinned client preserves honest semantics.

Unavailable:

- resources/subscriptions;
- prompts;
- server-initiated sampling or model calls;
- roots/filesystem exposure;
- elicitation that changes authority;
- logging streams containing domain content;
- mutation/execution tools;
- unrelated MCP server proxying.

Sampling is disabled. Any server-initiated model request fails tests and later 068
activation.

## Authentication and session contract

067 defines verification semantics but does not generate or inject a production runtime
credential. 068 owns that operation.

The future credential is:

- distinct in audience from provider credentials and the 066 model credential;
- generated outside committed configuration;
- stored as a verifier or secret reference;
- rotatable/revocable;
- absent from logs, errors, fixtures, and safe diagnostics.

Every accepted session binds server-verifiably to:

- pinned Hermes profile/client identity;
- active JarvisOS-issued flow grant;
- workspace/operator;
- read-only capability subset;
- canonical/effective catalog version and digest;
- protocol/compatibility identity;
- expiry/revocation/terminal state;
- server-owned read-call/concurrency/wall-time limits.

Workspace, actor, flow, sensitivity, provider, route, budget, and status authority are
never ordinary tool arguments.

## Canonical/effective tool identity

Captured fixtures define a mapping for each tool:

```text
canonical_server_name
  -> exact Hermes/client-visible effective name
  -> exact input schema digest
  -> exact output schema digest
  -> compatibility version
```

067 dispatches only by the canonical server catalog. 066 validates only the exact
effective names/schemas proven for the pinned build. Unknown, transformed-with-drift,
widened, or client-mutated names/schemas fail closed.

Tool discovery is not execution permission. Every call rechecks session, flow,
workspace, catalog, scope, resource limits, and current source policy.

## Common strict input rules

All tool models use strict types and reject unknown fields, booleans where numbers are
expected, NaN/Infinity, duplicate identifiers, invalid nulls, and oversized UTF-8.

No schema contains fields that provide or behave as:

- SQL/table/column/FTS syntax;
- path/filename/directory/glob;
- URL/host/endpoint/network;
- command/shell/Python/script/code/expression/environment;
- provider/model/route/token/budget/credentials/headers;
- workspace/actor/flow/session authority;
- sensitivity labels or derivative authority;
- promote/accept/reject/archive/delete/update/execute controls;
- arbitrary metadata/kwargs.

Search text remains literal data. Cross-workspace object IDs fail.

## Read sensitivity boundary

Local MCP transport is not authority to reveal sensitive project content to Hermes.
V0 returns only:

- current S0/S1 source content under the granted read capability;
- a current approved effective-S0/S1 derivative exactly covering the selected source;
- bounded withheld metadata for everything else.

Raw S2/S3/S4, unknown, stale, malformed, cross-workspace, and deterministic
secret-bearing content is withheld. Raw S2/S3 access requires a future numbered spec
proving 068 isolation, a qualified local-only model path, operator-controlled
capability, retention/cleanup, and no external-reuse bypass. S4/secrets remain forbidden.

Selection, source-state resolution, derivative validation, serialization, and manifest
construction occur in one coherent read transaction.

## Result envelope and provenance capsule

Every call returns one strict bounded structured envelope containing:

- schema/catalog/compatibility version;
- stable status and reason code;
- server operation and session/flow correlation IDs;
- tool-specific bounded data;
- truncation, dropped, and withheld counts;
- opaque context-capsule ID and digest when content may enter a model turn;
- effective sensitivity and policy version;
- expiry.

A capsule binds:

- flow/session/profile/tool/call identity;
- canonical and effective tool identity;
- canonical input/output digests;
- included source/object references and current digests;
- derivative identity where used;
- included/withheld/dropped/truncated manifest;
- effective sensitivity and deterministic floor evidence;
- policy/catalog/compatibility versions;
- creation, expiry, revocation, and stale state.

When a result later enters 066, JarvisOS reloads and revalidates the capsule, visible
content digest, current source/object state, derivative validity, and sensitivity. A
capsule is provenance evidence, not provider-call or mutation authority.

No credential, path, SQL, arbitrary stack trace, provider metadata, file/report body,
or 062 note enters results, events, status, or logs.

## Safe per-call audit evidence

Every `tools/call` invocation, including denied, failed, cancelled, replayed, and
successful reads, appends exactly one safe audit/operation record. This audit is metadata
evidence and is not a domain mutation or second content store.

Required fields include:

- server operation/audit ID and timestamp;
- opaque profile, session, flow, workspace, and actor references;
- canonical and effective tool names;
- catalog, schema, compatibility, sensitivity-policy, and capability versions;
- canonical input digest, never the literal query or arguments body;
- output-envelope digest or explicit no-output marker;
- capsule ID/digest when one exists;
- status and stable reason code;
- authentication, authorization, dispatch, replay/recompute, and cancellation class;
- latency and bounded resource counters;
- included, withheld, dropped, and truncated item counts;
- source/object count and sensitivity summary without content bodies;
- reference to an original operation for exact replay, never a copied body.

Rules:

- append the audit record even when authentication, session, catalog, scope, or
  sensitivity validation denies the call, using only identities safely known at that
  point;
- one invocation produces one audit row; replay does not duplicate the original audit
  row and instead appends a new invocation row referencing it;
- audit writes occur outside domain tables and cannot alter records, evidence, BLUECAD,
  flow, grade, route, budget, or sensitivity state;
- audit records contain no literal search query, input/output body, record title/snippet,
  file content, credential, path, SQL, stack trace, 062 note, or provider metadata;
- audit failure is explicit and fail-closed according to an implementation-time policy;
  a successful domain read cannot be silently reported as fully audited if its required
  audit evidence was not durably written;
- retention and access are bounded local policy, while canonical source/capsule digests
  remain sufficient to investigate the operation without retaining content.

`tools/list`, initialize, ping, authentication failures, and protocol errors use separate
safe transport/audit events where useful, but they never masquerade as successful
`tools/call` audit rows.

## Tool 1 — `jarvis_context_preview`

Reuse current context selectors and 059a coherent snapshot/derivative logic through one
thin owning-service helper. Bounded inputs may select canonical record kinds/statuses,
IDs, literal query, item count, and character budget. Workspace/sensitivity/route fields
are server-owned.

Return a bounded deterministic sequence of S0/S1 blocks plus included, withheld,
dropped, and truncation manifests with capsule evidence. Raw S2+ never appears.

## Tool 2 — `jarvis_search_records`

Reuse owning modeling/evidence selectors through one minimal literal-search,
connection-aware pagination helper. Search is escaped/literal rather than caller FTS or
SQL. An opaque cursor binds workspace, filters, ordering, catalog version, and final
key.

Return bounded record metadata, S0/S1 title/snippet or withheld marker, stable ordering,
counts, next cursor, and capsule evidence.

## Tool 3 — `jarvis_bluecad_inspect_candidate`

Reuse BLUECAD ledger/evidence/artifact metadata read services. Return bounded candidate,
attempt, validation/evidence, and registered artifact metadata without stored paths,
artifact/report bodies, execution, retry, archive, promotion, or state mutation.

Existing candidate status and promotion decision IDs are descriptive only.

## Tool 4 — `jarvis_query_evidence`

Reuse typed evidence selectors through a bounded literal-filter/keyset helper. Return
existing evidence identity, kind, verdict, parsed typed metrics, source/candidate/run
references, artifact digest/type/status metadata, timestamps, withheld state, and
capsule evidence.

The tool cannot create or alter verdicts, metrics, evidence rows, or artifacts.

## Read-call idempotency, reconnect, and concurrency

Read calls are side-effect-free but still resource-bounded.

Rules:

- captured fixtures must measure whether reconnect reuses or changes JSON-RPC IDs;
- a duplicate exact read may be recomputed only from one coherent current snapshot and
  still counts against server resource limits, or replayed if a bounded cache is proven
  necessary;
- changed request content is a distinct read and never inherits prior authority;
- no call holds a database transaction across network/model activity;
- read concurrency remains disabled or strictly bounded until snapshot/resource tests
  pass;
- server hard timeouts are defined per tool at implementation time;
- cancellation before dispatch prevents work;
- disconnect causes no background retry or polling worker;
- every invocation, including replay/recompute, receives its own safe audit record.

Because v0 has no mutations, reconnect cannot create a domain object, job, candidate,
or accepted state.

## Replay and retention

Prefer deterministic recomputation for reads. If the pinned client requires exact
response replay, retain only the minimum bounded S0/S1 envelope required by the exact
session/flow/request identity, expiring at the earlier of flow expiry or one hour.

Replay content remains restricted operational data and never enters `ai_jobs`, 061/062,
normal logs/events/status, or long-lived analytics. Cleanup removes only replay bodies,
never canonical domain, capsule, safe audit, or attempt evidence.

No raw S2/S3/S4/unknown/secret replay is permitted in v0. No universal 24-hour cache is
accepted.

## Persistence and migration discipline

No numeric migration ID is frozen. Implementation-time additive persistence may include:

- disabled activation state/config version;
- scoped MCP client verifiers;
- read-only sessions;
- catalog/compatibility identity;
- bounded read operation/replay metadata where fixtures require it;
- context capsules;
- safe per-call audit records and indexes.

Domain data remains in owning services. MCP adapters contain no domain SQL or filesystem
traversal. Migration is additive/idempotent and preserves existing APIs. Database
migration or ordinary startup never binds or activates a production MCP endpoint.

## Required tests

### Pinned protocol and catalog

- immutable Hermes/MCP identity and captured protocol fixtures;
- exact canonical-to-effective names and schema digests;
- supported methods/content forms match fixtures;
- unknown methods/capabilities/tools/schemas fail;
- sampling/resources/prompts/mutation tools remain absent;
- reconnect/request-ID behavior is measured, not assumed.

### Disabled transport contract

- fresh/upgrade state is disabled;
- importing/starting ordinary JarvisOS binds no production MCP listener;
- ordinary settings, environment overrides, client requests, and model content cannot
  activate or select bind address;
- local fixture harnesses exercise the complete protocol without claiming isolation;
- authentication/session/catalog/cross-flow failures occur before domain reads;
- merging 067 cannot install, launch, bind production transport, inject runtime
  credentials, or activate Hermes.

### Authority and injection

- every input is strict and bounded;
- SQL/path/URL/command/code/provider/route/budget, status-authority, and mutation-control
  fields fail;
- bounded read-only status filters are accepted only where an advertised tool schema
  explicitly defines them, and they cannot change any stored status;
- malicious strings remain literal;
- cross-workspace/session/flow references fail;
- no tool calls `run_ai_task`, provider adapters, external network, promotion,
  mutation, archive, delete, or sensitivity downgrade.

### Read sensitivity and capsules

- only the four v0 tools are advertised;
- S0/S1/current approved derivatives return under scope;
- raw S2/S3/S4/unknown/secrets are withheld;
- source/derivative resolution and serialization use one coherent snapshot;
- included/withheld/dropped manifests are complete;
- visible output digest matches the capsule;
- altered, expired, revoked, stale, cross-flow, cross-workspace, or source-drifted
  capsules fail when reused through 066;
- read permission never becomes egress permission.

### Per-call audit

- every successful, denied, failed, cancelled, replayed, and recomputed `tools/call`
  invocation appends exactly one safe audit row;
- authentication and pre-dispatch denials use only safely resolved identities;
- audit rows bind tool/session/flow, input/output digests, status/reason, latency,
  resource and inclusion/withholding counts, and capsule evidence where present;
- literal queries, arguments, results, titles/snippets, paths, credentials, SQL, notes,
  and stack traces never enter audit rows;
- replay appends a new invocation audit referencing the original operation;
- audit failure cannot be silently reported as complete audit success;
- audit writes mutate no domain, flow, grade, route, budget, or sensitivity authority.

### Tool behavior

- context preview bounds/order/counts are deterministic;
- literal search cannot inject SQL/FTS and cursor tampering fails;
- BLUECAD inspection leaks no paths/bodies and mutates nothing;
- evidence query returns existing typed evidence only and cannot change verdicts;
- timeout/cancellation/disconnect creates no background work or domain mutation.

### Privacy/regression

- replay/capsule content stays out of safe logs/events/status/061/062;
- audit metadata contains no domain content or secrets;
- cleanup preserves canonical records, capsules, audit, and attempt evidence as required
  by bounded retention policy;
- migration remains provisional until implementation;
- existing modeling, BLUECAD, evidence, 059a/059b/061/062, and direct APIs remain green;
- CI uses no live provider, production Hermes process, or uncontrolled MCP server.

Run full backend tests, Ruff, status-registry self-test, relevant frontend regressions,
and BLUECAD real-tool proof.

## 068 activation obligations

After 066/067 implementations merge, 068 must prove before activation:

- actual Windows-first private transport and firewall/isolation;
- only the approved pinned runtime can connect;
- production credentials are secret-free in committed config and scoped correctly;
- effective tool list contains exactly the allowed read-only v0 names/schemas;
- all unrelated MCP servers, sampling, resources, prompts, and mutation tools are off;
- direct provider/model/network, repository, data-root, and unrelated secret access fail;
- kill switch/revocation returns the endpoint to disabled.

These are activation tests, not prerequisites for compiling/reviewing disabled 067 code.

## Non-goals

No mutation/execution tool, MemoryStore proposal tool, calc runner tool, BLUECAD create
tool, generic CRUD/SQL/filesystem server, arbitrary Python/shell, browser/search proxy,
provider tool, MCP sampling/resources/prompts marketplace, public/remote MCP, raw
artifact download, promotion/approval UI, autonomous workflow engine, Hermes
installation/activation, conversation memory, scheduled work, or replacement of
existing service/HTTP contracts.

## Promotion gates

Before `STATUS.md` may move 067 to `ready`:

1. One pinned Hermes/MCP identity and complete read-only fixture bundle are accepted.
2. Canonical/effective names, schemas, IDs, content form, and reconnect behavior are
   captured.
3. All four owning read-service mappings are rechecked against implementation-time
   `master` and require no direct MCP domain SQL.
4. 059a coherent sensitivity/derivative resolution remains stable.
5. 066's read-only tool-result/capsule consumer contract is stable or represented by
   accepted conditional fixtures; activation still waits for merged 066.
6. The implementation contract defaults disabled, is transport-abstract, advertises no
   mutations, and cannot bind/activate production transport by itself.
7. Safe per-call audit evidence and fail-closed audit behavior are accepted.
8. Migration ID is assigned from implementation-time `master`.
9. Exact-head CI and independent review have no unresolved blockers.

Even after implementation merge, 068 remains mandatory before any production binding,
Hermes installation/launch, runtime credential injection, or activation. Future
mutation/execution tools require new numbered specs and are not enabled by 067 status.
