# 050 — FLOWSHEET-1: derived dependency and provenance graph

Status: implementation-ready full specification. `docs/specs/STATUS.md` is authoritative.

Depends on: 047, 048, 049

Related merged foundations: 040, 042, 043, 044, 071

## Goal

Expose one deterministic, workspace-scoped, inspectable graph derived from the records,
foreign keys, typed input bindings, and bounded provenance already stored by JarvisOS.

050 gives later work one shared answer to:

- what engineering, execution, CAD, and evidence records exist;
- which upstream records a downstream record depends on;
- which outputs feed later runs, decisions, artifacts, candidates, and evidence;
- which legacy references resolve to canonical `<kind>:<id>` identities;
- which references are malformed, dangling, unsupported, or cyclic.

050 does not create a recomputation engine, stale propagation, automatic binding,
automatic promotion, or a second engineering-record store.

## Maintainer direction

Implement the smallest read-only graph surface over current SQLite authority:

- no new table, migration, entity copy, graph database, cache, index, event, or materialized
  edge ledger;
- one workspace-consistent read snapshot per request;
- one shared canonical node resolver used by both graph extraction and direct inspection;
- exact allowlisted extraction from foreign keys, known payload shapes, and recognized
  `source_ref` grammars only;
- deterministic node, edge, diagnostic, and topological ordering;
- bounded fail-closed responses rather than silently incomplete graphs;
- no parsing of prose, notes, rationale, prompts, filenames, or arbitrary JSON keys;
- no local model, Ollama, provider, network, CAD, FEM, CFD, or background execution.

The legacy `entities` and `entity_links` tables are not used by 050. Populating them would
create a second mutable authority and is explicitly out of scope.

## Existing authority mapped by 050

050 reads only existing authoritative fields.

### Domain and model records

- `model_specs.id`, `workspace_id`;
- `model_versions.model_spec_id`, `implementation_artifact_id`;
- `assumptions.source_ref`, `source_ai_job_id`;
- `parameters.source_ref`, `source_ai_job_id`;
- `decisions.linked_run_id`, `source_ai_job_id`;
- `requirements` as inspectable isolated records when no typed dependency exists.

### Runner records

- `simulation_runs.model_version_id`;
- exact known shapes in `simulation_runs.input_payload`;
- `runner_jobs.simulation_run_id`;
- `run_artifacts.simulation_run_id`, `artifact_id`, `role`;
- calc-produced parameter `source_ref = "runner_job:<id>"`;
- generated artifact `source_ref = "simulation_run:<id>"`;
- implementation artifact `source_ref = "model_spec:<id>"`.

### AI context and proposal provenance

- workspace-scoped `source_ai_job_id` fields;
- `bluecad_attempts.proposal_ai_job_id`;
- `ai_jobs.context_sources_json` only for AI jobs already reached through a
  workspace-scoped record or BLUECAD attempt;
- context sources only when each manifest item has an allowlisted `type` and exact `id`.

`ai_jobs` has no direct workspace column. 050 must never expose an arbitrary AI job by
ID. An AI job is in scope only when a workspace-owned record or attempt references it.

### BLUECAD and evidence

- candidate parent, current artifact, and promoted-decision foreign keys;
- attempt candidate, proposal job, and artifact foreign keys;
- validation, mesh, and FEM evidence links to run, candidate, attempt, and report artifact;
- exact BLUECAD artifact source-reference forms already emitted by the loop.

## Canonical node identity

Every resolved node has exactly one identity:

```text
<kind>:<id>
```

Allowed canonical kinds:

- `model_spec`;
- `model_version`;
- `simulation_run`;
- `runner_job`;
- `artifact`;
- `assumption`;
- `parameter`;
- `decision`;
- `requirement`;
- `ai_job`;
- `bluecad_candidate`;
- `bluecad_attempt`;
- `evidence`.

The kind is lowercase ASCII and exact. The identifier is non-empty, contains no colon,
and is at most 256 characters. 050 does not require UUID syntax because existing and
future authoritative IDs may use another bounded opaque format.

`evidence_record` may be accepted as a legacy input alias and normalized to `evidence`.
No other alias is accepted in V0.

The graph response never creates synthetic nodes for unresolved references.

## Shared resolver contract

One internal resolver owns kind parsing, table mapping, workspace isolation, labels, and
bounded metadata. Both public endpoints use this same function.

Public direct inspection:

```http
GET /workspaces/{workspace_id}/flowsheet/nodes/{node_ref}
```

`node_ref` is one canonical `<kind>:<id>` path segment.

Resolution requirements:

- direct workspace tables require exact `workspace_id` equality;
- `bluecad_attempt` resolves through its candidate's workspace;
- `ai_job` resolves only when reachable from a workspace-owned assumption, parameter,
  decision, or BLUECAD attempt;
- missing and cross-workspace nodes share one `404 flowsheet_node_not_found` response so
  cross-workspace existence is not disclosed;
- malformed references return `400 flowsheet_ref_invalid`;
- resolver reads have no side effects.

## Node response

Each node contains:

```json
{
  "ref": "parameter:<id>",
  "kind": "parameter",
  "id": "<id>",
  "label": "Tube length",
  "status": "accepted",
  "origin": "calc",
  "created_at": "<stored timestamp or null>",
  "metadata": {}
}
```

Rules:

- `label` is deterministic and at most 120 Unicode code points;
- label sources are allowlisted fields such as title, name, version label, run label,
  filename, evidence kind, task kind, candidate ID prefix, or attempt number;
- assumption and requirement statements may be truncated for labels but are never
  returned in full;
- `status`, `origin`, and `created_at` are nullable when the table has no equivalent;
- metadata is an allowlisted shallow object only;
- no values, raw payloads, metrics JSON, notes, rationale, brief text, prompts, outputs,
  logs, paths, secret references, environment data, or arbitrary database columns are
  returned.

Allowed metadata examples:

- model version: `implementation_kind`;
- run: `run_label`;
- runner job: `implementation_kind`;
- artifact: `artifact_type`, `mime_type`;
- parameter: `unit`, `value_status`;
- AI job: `task_kind`;
- BLUECAD attempt: `attempt_no`, `route_class`, `validation_verdict`;
- evidence: `evidence_kind`, `verdict`.

## Graph endpoint

```http
GET /workspaces/{workspace_id}/flowsheet/graph
```

V0 returns the complete supported graph for one workspace. It has no filters, expansion
queries, pagination, saved layouts, or user-selected roots.

Response shape:

```json
{
  "workspace_id": "bluerev",
  "nodes": [],
  "edges": [],
  "topological_order": [],
  "is_acyclic": true,
  "diagnostics": {
    "unsupported_reference_count": 0,
    "malformed_reference_count": 0,
    "dangling_reference_count": 0,
    "cycle_count": 0,
    "manual_binding_count": 0,
    "unresolved_references": [],
    "cycles": []
  }
}
```

No generated timestamp appears, so identical database state yields byte-equivalent JSON
after framework serialization.

## Edge semantics

Every resolved edge is directed from upstream authority to downstream dependent:

```json
{
  "id": "sha256:<digest>",
  "upstream_ref": "parameter:<id>",
  "downstream_ref": "simulation_run:<id>",
  "relation": "bound_input",
  "edge_class": "dependency",
  "authorities": ["payload_binding"],
  "source_fields": ["simulation_runs.input_payload:tube_length"]
}
```

`downstream_ref` depends on or was produced from `upstream_ref`.

Edge IDs are SHA-256 digests of the canonical tuple:

```text
upstream_ref | downstream_ref | relation | edge_class
```

If the same logical edge is independently supported by multiple authoritative fields,
050 emits one edge and merges sorted unique `authorities` and `source_fields`.

Allowed edge classes:

- `dependency`: engineering or execution input/output lineage used for DAG analysis;
- `provenance`: creation, context, promotion, or lifecycle provenance not used to decide
  engineering recomputation order.

## Exact edge extraction

### Foreign-key and typed-column edges

050 emits the following when both endpoints resolve in the same workspace:

| Upstream | Downstream | Relation | Class | Authority |
| --- | --- | --- | --- | --- |
| model spec | model version | `has_version` | dependency | `foreign_key` |
| implementation artifact | model version | `implementation_artifact` | dependency | `foreign_key` |
| model version | simulation run | `configured_run` | dependency | `foreign_key` |
| simulation run | runner job | `executed_by` | provenance | `foreign_key` |
| simulation run | run artifact | `produced_artifact` | dependency | `foreign_key` |
| simulation run | linked decision | `informed_decision` | dependency | `foreign_key` |
| AI job | assumption/parameter/decision | `proposed_record` | provenance | `foreign_key` |
| parent candidate | child candidate | `parent_candidate` | dependency | `foreign_key` |
| candidate | attempt | `has_attempt` | provenance | `foreign_key` |
| AI job | BLUECAD attempt | `proposed_attempt` | provenance | `foreign_key` |
| candidate | current artifact | `current_candidate_artifact` | provenance | `foreign_key` |
| attempt | attempt artifact | `attempt_artifact` | dependency | `foreign_key` |
| candidate | promoted decision | `promoted_as` | provenance | `foreign_key` |
| simulation run | evidence | `supports_evidence` | dependency | `foreign_key` |
| candidate | evidence | `candidate_evidence` | provenance | `foreign_key` |
| attempt | evidence | `attempt_evidence` | provenance | `foreign_key` |
| report artifact | evidence | `reported_evidence` | dependency | `foreign_key` |

Artifact field and role names are preserved only in `source_fields`; they do not create
new relation names.

### Known simulation input payloads

050 parses only these exact shapes from valid JSON objects:

1. `calc_v0` binding items at the top level:

```json
{
  "variable_name": {
    "value": 1.0,
    "unit": "m",
    "source_parameter_id": "<id>"
  }
}
```

A verified same-workspace parameter emits:

```text
parameter -> simulation_run, relation=bound_input, class=dependency
```

The variable name is included only in the bounded `source_field`.

A top-level calc item without `source_parameter_id` increments
`manual_binding_count` and creates no synthetic source node.

2. batch-growth `input_artifact_ids`:

```json
{"input_artifact_ids": ["<artifact-id>"]}
```

Each verified artifact emits `artifact -> simulation_run`, relation `input_artifact`.

3. BLUECAD advisory run identity:

```json
{"candidate_id": "<id>", "attempt_id": "<id>"}
```

The candidate and attempt emit dependency edges to the simulation run only when the
attempt belongs to that candidate.

050 does not recursively scan payloads and does not interpret arbitrary keys ending in
`_id`.

`parameter_payload` and `output_payload` are not generic edge sources in 050. Their
current contents either duplicate authoritative input bindings or lack a stable shared
reference contract.

### AI context manifest

For an already in-scope AI job, `context_sources_json` is parsed only when it is a list of
objects containing:

- `type` in `decision`, `assumption`, `parameter`, `requirement`, or `evidence`;
- `id` as a non-empty string;
- optional `source`, which must equal `<type>:<id>` when present.

Each resolved item emits:

```text
context record -> ai_job, relation=context_for, class=provenance
```

Malformed manifest items produce bounded diagnostics and no edge.

### Simple source references

The following exact simple form is accepted:

```text
<canonical-kind>:<id>
```

Recognized simple source references on assumptions, parameters, and artifacts emit:

```text
resolved source -> owning record, relation=source_reference, class=dependency
```

### Legacy BLUECAD compound references

Recognized exact forms:

```text
bluecad_candidate:<candidate-id>:attempt:<positive-integer>
bluecad_candidate:<candidate-id>:attempt:<positive-integer>:sim:<run-id>
```

For the first form, 050 resolves the exact candidate plus attempt number and normalizes
the source to `bluecad_attempt:<attempt-id>`.

For the second form, 050 additionally verifies:

- the simulation run belongs to the same workspace;
- the run's exact BLUECAD advisory input payload identifies that candidate and attempt;
- the attempt number matches the referenced attempt.

The normalized primary source is `simulation_run:<run-id>`. Candidate and attempt
lineage is already represented by typed edges and is not duplicated through the raw
compound string.

No other colon-delimited grammar is accepted.

## Unresolved-reference diagnostics

A reference that cannot produce a resolved edge yields one bounded diagnostic:

```json
{
  "owner_ref": "artifact:<id>",
  "source_field": "artifacts.source_ref",
  "code": "dangling_reference",
  "raw_ref": "runner_job:<bounded-id>"
}
```

Allowed codes:

- `malformed_reference`;
- `unsupported_reference`;
- `dangling_reference`;
- `payload_invalid`;
- `payload_reference_invalid`;
- `context_manifest_invalid`.

`raw_ref` is omitted when not applicable and otherwise truncated to 256 Unicode code
points. Cross-workspace and nonexistent targets both use `dangling_reference` and do not
reveal whether another workspace contains the ID.

Diagnostics are sorted by owner, field, code, and raw reference.

## DAG and cycle contract

`dependency` edges define the 050 DAG projection. `provenance` edges are excluded from
topological ordering.

050 runs deterministic Kahn topological sorting with lexicographic canonical-ref tie
breaking.

- acyclic graph: `is_acyclic = true`, `topological_order` contains every node exactly
  once, including isolated nodes;
- cyclic dependency graph: `is_acyclic = false`, `topological_order = null`, and
  diagnostics contain bounded canonical cycle paths;
- cycles do not mutate, reject, supersede, or stale any record;
- 050 never claims a cyclic result is a DAG.

Cycle paths are canonicalized by rotating each directed path to its lexicographically
smallest node. Edge direction is never reversed. At most 20
cycles and at most 50 nodes per cycle are returned.

## Snapshot and determinism

Each graph request:

1. opens one SQLite connection;
2. verifies the workspace;
3. begins one read snapshot before loading any graph table;
4. performs no writes, events, temporary tables, or filesystem access;
5. constructs all nodes and edges in memory;
6. sorts nodes by `(kind, id)`;
7. sorts edges by `(upstream_ref, downstream_ref, relation, edge_class)`;
8. sorts and deduplicates authorities/source fields and diagnostics;
9. returns no wall-clock-derived field.

Two reads over unchanged database state must return equal response objects.

## Bounds and failure semantics

Constants:

```text
MAX_GRAPH_NODES = 1000
MAX_GRAPH_EDGES = 3000
MAX_GRAPH_DIAGNOSTICS = 200
MAX_REFERENCE_CHARS = 512
MAX_LABEL_CHARS = 120
```

050 never silently truncates nodes or edges. If a workspace exceeds a node or edge bound,
the graph endpoint returns:

```text
409 flowsheet_graph_limit_exceeded
```

with only the exceeded bound name and observed count. It returns no partial graph.

If unresolved diagnostics exceed their bound, the endpoint returns
`409 flowsheet_diagnostics_limit_exceeded`; it does not hide unresolved lineage.

Other errors:

- missing workspace: `404 flowsheet_workspace_not_found`;
- invalid direct node reference: `400 flowsheet_ref_invalid`;
- absent/out-of-scope direct node: `404 flowsheet_node_not_found`;
- invalid stored JSON contributes diagnostics; it does not crash the graph;
- unexpected database errors return a generic `500` without SQL or paths.

## Required endpoints and implementation shape

One bounded implementation PR may add only:

- `app/modules/flowsheet/models.py`;
- `app/modules/flowsheet/service.py`;
- `app/modules/flowsheet/routes.py`;
- router inclusion in `app/main.py`;
- focused backend tests;
- the canonical 050 lifecycle update.

No frontend change is required. The JSON route is the V0 inspectable surface; 035 and 055
own later navigation and product-view presentation.

No schema or migration is authorized.

## Required tests

### Resolver and workspace isolation

- every allowed kind resolves from a workspace-owned fixture;
- malformed kind, missing colon, empty ID, colon-bearing ID, and overlong reference fail;
- `evidence_record:<id>` normalizes to `evidence:<id>`;
- arbitrary AI jobs cannot be resolved without workspace-scoped reachability;
- cross-workspace IDs return the same not-found result as absent IDs;
- attempt resolution is scoped through candidate workspace;
- repeated resolution has no side effects.

### Foreign-key graph extraction

Construct fixtures covering model spec/version/artifact, simulation run/job/run artifact,
decision, AI-origin records, candidate/attempt/current artifacts/promotion, and evidence.
Assert every table-driven edge above and assert no undocumented edge.

### Payload bindings

- exact calc `source_parameter_id` creates one parameter-to-run edge;
- duplicate references coalesce and merge source fields;
- manual calc bindings create no node and increment the manual count;
- batch input artifact IDs create verified edges;
- BLUECAD candidate/attempt input creates edges only for matching ownership;
- invalid JSON and wrong known shapes produce diagnostics;
- arbitrary nested IDs and unknown `_id` keys never create edges;
- `parameter_payload` and `output_payload` are not recursively interpreted.

### Source-reference normalization

- simple canonical references resolve;
- model-spec, simulation-run, and runner-job source references resolve;
- both exact BLUECAD compound forms normalize as specified;
- wrong attempt number, mismatched run context, unsupported grammar, paths, URLs, and
  prose never create synthetic nodes;
- dangling/cross-workspace references are diagnosed without existence disclosure;
- duplicate FK plus source-ref support produces one merged edge.

### AI context provenance

- only AI jobs reached through workspace records or attempts enter the graph;
- exact context manifest entries create context edges;
- source/type/id mismatch is diagnosed;
- unknown context kinds, missing IDs, raw content, and malformed JSON create no edge;
- context bodies, prompts, outputs, and token-flow data never appear in responses.

### Determinism, bounds, and cycles

- unchanged state yields equal graph responses;
- node, edge, metadata, authority, field, diagnostic, and topological ordering is stable;
- no generated timestamp exists;
- an acyclic fixture returns a complete topological order;
- an injected source-reference cycle returns `is_acyclic = false` and canonical cycles;
- limits fail without returning a partial graph;
- graph and node reads leave counts and rows unchanged in all tables and create no event.

### Data minimization

Assert responses do not contain:

- parameter values;
- assumption/requirement full statements;
- decision text or rationale;
- artifact stored paths;
- candidate brief text;
- evidence metrics JSON;
- simulation inputs/outputs;
- AI prompt/context/output bodies;
- logs, environment, command metadata, secrets, or raw database payloads.

## Acceptance criteria

050 is complete when:

1. one shared resolver produces canonical workspace-safe nodes;
2. the graph is derived entirely from current authority in one read snapshot;
3. all exact FK, typed payload, context manifest, and supported source-reference edges are
   deterministic and tested;
4. malformed and dangling lineage is visible and bounded;
5. dependency cycles are reported honestly;
6. no graph state is stored and no record is changed;
7. the implementation adds no migration or recompute behavior;
8. full backend CI and existing BLUECAD proof remain green.

## Non-goals

050 does not authorize:

- recalculation, stale marking, invalidation, scheduling, or event-driven propagation;
- write endpoints for nodes or edges;
- graph editing, manual edge creation, or edge promotion;
- automatic parameter binding or value copying between models;
- automatic CAD generation from process outputs;
- automatic acceptance, rejection, supersession, or deletion;
- generic recursive JSON or natural-language relationship extraction;
- vector search, embeddings, LLM graph extraction, or model calls;
- graph database, NetworkX runtime dependency, cache, denormalized edge table, or use of
  legacy `entities`/`entity_links` as authority;
- frontend graph visualization, workspace navigator, or project dossier;
- stale propagation owned by 051;
- CAD linkage owned by 052;
- project navigation and view composition owned by 035 and 055.
