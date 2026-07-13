# 067 — JARVIS-MCP-0: bounded domain tools without authority bypass

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 005, 010, 040, 042, 043, 044, 059a

## Problem

Hermes needs domain operations, but direct access to the JarvisOS repository,
SQLite database, data root, service internals, or runner directories would create
a second authority path and destroy sensitivity/provenance continuity.

MCP is the integration boundary, not a shortcut around existing services.

## Maintainer direction

Expose a first bounded JarvisOS MCP server consumed by Hermes. The initial tool
families are:

1. read a context-pack preview;
2. search canonical records;
3. propose a record through MemoryStore;
4. run a bounded `calc_v0` job;
5. create a BLUECAD candidate proposal;
6. inspect a BLUECAD candidate;
7. query typed evidence.

All mutations remain proposals or bounded jobs under existing service and
promotion gates. No MCP tool promotes, accepts, overwrites, deletes, relabels,
lowers sensitivity, selects a provider, or authorizes egress.

## Initial tool contract

The full spec must freeze exact names and schemas. The intended semantic surface
is:

- `jarvis_context_preview`
- `jarvis_search_records`
- `jarvis_propose_record`
- `jarvis_run_calc_v0`
- `jarvis_bluecad_create_candidate`
- `jarvis_bluecad_inspect_candidate`
- `jarvis_query_evidence`

Names are provisional until the full spec proves that they do not collide with
other configured MCP servers.

### Common requirements

Every tool must have:

- a bounded JSON input schema with no arbitrary SQL, shell, path, URL, Python, or
  service-method field;
- explicit workspace and actor/session scope;
- deterministic pagination, ordering, and maximum result size for reads;
- a timeout and cancellation outcome;
- a stable result envelope with status, safe reason code, object IDs, digests,
  provenance, and truncation state;
- an audit event with tool name, actor/session, workspace, input digest, output
  digest, latency, status, and safe reason code;
- no raw secret or withheld content in logs;
- service-layer invocation only.

### Read tools

- Return only records the existing service and sensitivity policy permit.
- Preserve record status, provenance, and source identity.
- Never represent retrieval snippets or summaries as canonical truth.
- Context preview must retain included/withheld manifests and must not expose
  withheld content.
- Search must not become a general database query language.

### Mutation and execution tools

- `jarvis_propose_record` must call MemoryStore proposal creation and return a
  proposal ID; it cannot promote or update an accepted record in place.
- `jarvis_run_calc_v0` must use the existing bounded runner contract, unit-bearing
  outputs, artifact limits, and proposal behavior; it cannot accept arbitrary
  code through this MCP slice.
- `jarvis_bluecad_create_candidate` must create only a candidate/proposal through
  the existing BLUECAD service boundary.
- Candidate inspection is read-only.
- Tool success proves only that the service accepted the operation; it does not
  prove the engineering result correct.

## Provenance capsule

Every result that may later enter a model request must include a server-owned
opaque `context_capsule_id` or equivalent verifiable reference.

The server-side capsule record binds at least:

- workspace;
- actor/session;
- tool and tool-call ID;
- canonical input and output digests;
- source record/artifact/evidence references;
- effective sensitivity and policy version;
- creation and expiry;
- truncation/withholding metadata.

The Hermes-visible result may include safe structured metadata, but the
passthrough must reload the capsule before trusting it for egress. Hermes never
receives a signing key.

## Transport and authentication

The first server must use either:

- stdio launched inside the hardened Hermes isolation boundary; or
- authenticated loopback-only Streamable HTTP.

The full spec must choose one primary transport and prove lifecycle, reconnect,
timeout, and shutdown behavior for the pinned Hermes version.

Remote/public binding is out of scope. Credentials are supplied outside committed
configuration and grant only the enumerated MCP capabilities.

## Hermes-specific hardening requirements

- Set MCP `sampling.enabled: false` for the JarvisOS server.
- Keep server-initiated model sampling disabled until a separate spec proves that
  it also traverses `run_ai_task`, budget, egress, and ledger policy.
- Keep parallel tool calls disabled by default.
- A tool may opt into concurrency only after idempotency, transaction, resource,
  and budget tests prove safety.
- Disable elicitation-driven authority changes; any future confirmation remains a
  JarvisOS-owned UI/policy event.

## Required tests

The full spec must include deterministic tests for:

- schema bounds and unknown fields;
- cross-workspace access;
- arbitrary SQL/path/URL/code injection;
- direct repository/data-root access attempts;
- service-layer bypass attempts;
- withheld sensitivity content;
- forged, stale, altered, expired, and cross-workspace capsules;
- pagination and output truncation;
- timeout/cancellation;
- duplicate proposal requests;
- `calc_v0` resource and artifact limits;
- BLUECAD candidate creation without promotion;
- no MCP sampling;
- no parallel mutation by default;
- safe audit metadata;
- zero provider calls from all MCP tools.

## Hard lines

- No direct SQLite connection, repository filesystem read, data-root traversal,
  or internal object mutation from the MCP adapter.
- No promotion, acceptance, deletion, sensitivity downgrade, provider route,
  budget override, confirmation, or egress authority.
- No canonical engineering truth stored in Hermes memory or skills.
- No arbitrary shell, Python, browser, or external-network tool hidden behind an
  MCP domain name.

## Non-goals

No generic CRUD MCP server, raw filesystem server, SQL tool, public remote MCP,
MCP sampling, browser/search proxy, provider tool, promotion UI, autonomous
workflow engine, or replacement of existing HTTP/service contracts.

## Promotion evidence

Before this row may become `ready`, the full spec must:

1. map every tool to an existing service entry point and identify any minimal
   missing service helper;
2. freeze exact input/output schemas and limits;
3. choose and threat-model the transport/authentication boundary;
4. define the provenance capsule store and passthrough verification;
5. include deterministic no-provider and no-promotion tests;
6. bind compatibility to the same pinned Hermes identity as specs 066 and 068.
