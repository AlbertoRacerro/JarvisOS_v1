# 051 — FLOWSHEET-RECALC: deterministic freshness invalidation

Status: implementation-ready full specification. `docs/specs/STATUS.md` is authoritative.

Depends on: 050

Related merged foundations: 001, 040, 043, 047, 048, 049, 071

## Goal

When an operator explicitly accepts a new Parameter as the replacement for one
previously accepted Parameter, atomically:

1. supersede the old accepted Parameter;
2. accept the new proposed Parameter;
3. derive the affected downstream closure from the merged 050 graph;
4. persist deterministic freshness-invalidations with inspectable dependency paths;
5. leave historical execution, validation, evidence, and promotion states unchanged.

051 makes stale engineering consequences visible and explainable. It does not rerun a
model, rebuild geometry, invoke a solver, choose a replacement value, promote an output,
or claim that a stale historical result failed when it originally succeeded.

## Binding principles

### Execution state and freshness state are different

A successful SimulationRun remains `succeeded`; a completed RunnerJob remains
completed; a generated Artifact remains registered; a Decision remains accepted.

051 adds a separate freshness overlay:

- `fresh`: no accepted upstream replacement has invalidated the record;
- `stale`: at least one accepted upstream replacement has invalidated the record.

Freshness must never overwrite historical status fields. A stale successful run means
"successfully computed from superseded input", not "execution failed".

### Replacement is explicit authority

V0 never guesses that two Parameters represent the same engineering variable from
name, symbol, unit, notes, source, value, or semantic similarity.

A proposed Parameter may declare exactly one `supersedes_parameter_id`. Only the
explicit replacement-promotion operation activates supersession and stale propagation.
Creating another Parameter with the same name or unit does not invalidate anything.

### No automatic recomputation

051 marks and explains. It does not:

- create a SimulationRun or RunnerJob;
- call `calc_v0`, BLUECAD, Gmsh, CalculiX, CFD, a provider, a model, or Ollama;
- select new bindings;
- create replacement artifacts, evidence, decisions, or Parameters;
- clear stale state;
- promote, reject, archive, or delete any downstream record.

A later reviewed workflow may use the stale overlay to propose recomputation, but the
operator remains the authority.

## V0 trigger boundary

051 supports Parameter replacement only.

The trigger is a proposed Parameter carrying:

```text
supersedes_parameter_id = <accepted same-workspace Parameter ID>
```

The replacement may originate from the user or an AI proposal. Calculation-originated
Parameter proposals do not receive a supersession field in V0 and cannot automatically
replace an accepted input.

Assumption, Requirement, Decision, model-version, GeometrySpec, material, evidence, and
artifact replacement semantics are deferred. Their records may become stale when they
are downstream of a replaced Parameter, but they cannot trigger 051 in V0.

## Proposal contract

Add the optional field below to user/AI Parameter proposal and read contracts:

| Field | Type | Meaning |
| --- | --- | --- |
| `supersedes_parameter_id` | non-empty string or null | explicit accepted Parameter replaced by this proposal |

Rules at proposal creation:

1. the field is rejected for non-Parameter records;
2. the referenced Parameter must exist in the same workspace;
3. the referenced record must currently have record status `accepted`;
4. the proposal and referenced Parameter must use the exact same unit string;
5. the proposed replacement must contain a non-empty value;
6. a Parameter cannot supersede itself;
7. creation performs no status transition and no stale marking;
8. multiple alternative proposed replacements may reference the same accepted Parameter;
9. all conditions are revalidated at promotion because authority may change after proposal creation.

Exact unit equality is deliberate. V0 performs no unit conversion and does not accept a
dimensionally equivalent replacement under another unit string.

The explicit link is the variable-identity authority. Name and symbol may be corrected
without breaking replacement semantics and are therefore not required to match.

## Promotion authority

### Existing generic promotion

The existing generic endpoint remains valid for ordinary proposals:

```http
POST /memory/{record_kind}/{record_id}/promote
```

If a proposed Parameter has `supersedes_parameter_id`, generic promotion must fail with
stable reason:

```text
parameter_replacement_promotion_required
```

This prevents acceptance without stale propagation.

### Explicit replacement promotion

Add:

```http
POST /memory/parameter/{record_id}/promote-replacement
```

The request has no model-chosen payload. `record_id` identifies the proposed replacement
and its persisted `supersedes_parameter_id` identifies the old accepted Parameter.

Success response:

```json
{
  "accepted_parameter": {
    "id": "<new-id>",
    "status": "accepted",
    "supersedes_parameter_id": "<old-id>"
  },
  "superseded_parameter": {
    "id": "<old-id>",
    "status": "superseded"
  },
  "invalidation": {
    "id": "<invalidation-id>",
    "source_ref": "parameter:<old-id>",
    "replacement_ref": "parameter:<new-id>",
    "affected_count": 0,
    "graph_digest": "sha256:<digest>",
    "created_at": "<timestamp>"
  }
}
```

The response does not expose Parameter values.

## Atomic replacement transaction

Use one SQLite connection and one immediate write transaction.

Before changing either Parameter status:

1. verify workspace and proposal state;
2. revalidate the superseded Parameter as same-workspace and `accepted`;
3. verify exact unit equality and non-empty replacement value;
4. reject if another replacement has already been accepted for the old Parameter;
5. build the supported 050 graph from the same connection without opening another
   snapshot or performing writes;
6. verify graph, path, and invalidation bounds;
7. derive all freshness paths and rows in memory.

Only after all checks succeed:

1. update old Parameter status to `superseded` and `updated_at`;
2. update new Parameter status to `accepted`, set `promoted_at`, and update `updated_at`;
3. insert one invalidation batch;
4. insert all freshness marks;
5. emit one bounded replacement/invalidation event;
6. commit once.

Any failure rolls back statuses, marks, and event together. There is no state in which the
old Parameter is superseded but its known descendants were not marked.

Use `BEGIN IMMEDIATE` or the repository-equivalent write-lock discipline so two
alternative proposals cannot both replace the same accepted Parameter.

## Idempotency and races

A successful replacement is idempotent by replacement Parameter ID.

Replaying the explicit endpoint after success returns the existing accepted/superseded
records and the original invalidation batch without adding marks or events.

Required uniqueness:

- one invalidation batch per replacement Parameter;
- one accepted replacement per superseded Parameter;
- one freshness mark per `(invalidation_id, record_ref)`.

If two alternative proposals race, exactly one succeeds. The loser receives stable
`parameter_already_replaced`; it remains proposed and creates no stale state.

An inconsistent partial legacy state fails closed with
`parameter_replacement_state_inconsistent`; it is never repaired silently.

## Graph source and transaction reuse

051 reuses the merged 050 extraction rules and canonical node identity. It must not create
a second dependency resolver.

Refactor 050 only as needed to expose one internal, side-effect-free function that builds
the graph from a caller-supplied SQLite connection. The public 050 endpoints and response
contract remain unchanged.

The graph used for invalidation is the pre-replacement graph from the same transaction.
Its canonical digest is stored in the invalidation batch.

Canonical graph digest input:

```text
sorted node refs
+
sorted tuples of upstream_ref, downstream_ref, relation, edge_class,
    sorted authorities, sorted source_fields
+
sorted unresolved-reference diagnostics
```

Serialize with the repository canonical JSON rules and prefix the SHA-256 value with
`sha256:`.

## Freshness traversal

### Edge selection

Traverse:

1. every 050 edge with `edge_class = dependency`;
2. the exact provenance bridge relation `executed_by`.

`executed_by` is included only because calc-produced Parameters use
`runner_job:<id>` source references. Without the run-to-job bridge, an accepted input
could invalidate its SimulationRun while leaving derived Parameter outputs incorrectly
fresh.

No other provenance relation is traversed in V0. Context, proposal, promotion, parent,
and review provenance do not imply engineering invalidation.

### Source and targets

The traversal source is:

```text
parameter:<superseded_parameter_id>
```

The source Parameter itself is not marked stale because its canonical record state becomes
`superseded`.

Every other reachable 050 node is eligible for a freshness mark, regardless of kind. This
keeps the rule generic while preserving 050's workspace and reference authority.

The accepted replacement Parameter is excluded even if malformed legacy lineage makes it
reachable.

### Deterministic path

For every affected node, store one canonical shortest path from the superseded Parameter.

Use breadth-first traversal with:

- adjacency sorted by downstream canonical ref, relation, and edge class;
- shortest number of traversed edges;
- lexicographically smallest complete canonical-ref sequence when equal-length paths exist;
- the source and target both included in the stored path.

Example:

```json
[
  "parameter:<old-id>",
  "simulation_run:<run-id>",
  "runner_job:<job-id>",
  "parameter:<derived-output-id>"
]
```

Cycles are handled with a visited set. Each target is marked once per invalidation. A cycle
does not cause an infinite walk or duplicate mark.

### Bounds

Use the existing 050 graph node/edge bounds. Add:

```text
MAX_FRESHNESS_PATH_NODES = 100
MAX_FRESHNESS_MARKS_PER_INVALIDATION = 1000
```

A required path longer than its bound or an affected closure larger than its bound fails
before status changes. Paths and affected records are never silently truncated.

Stable reasons:

- `freshness_path_limit_exceeded`;
- `freshness_mark_limit_exceeded`;
- existing 050 graph-limit reasons when graph construction exceeds its bounds.

## Incomplete-lineage handling

051 propagates only over resolved supported 050 edges and does not invent missing nodes.

Before commit, fail with `freshness_lineage_incomplete` when an unresolved 050 diagnostic:

- is owned by a node in the affected closure; or
- names the superseded Parameter canonical ref as its bounded raw reference.

The response includes only the diagnostic count and bounded source-field identifiers, not
raw engineering values or arbitrary payloads.

Unrelated diagnostics outside the affected closure do not block the replacement. Their
count is stored in the invalidation batch for audit.

A cyclic affected subgraph is conservatively invalidated and recorded; it does not block
replacement when all references are resolved and bounds are respected.

## Persistence contract

Use the next available migration ID at implementation time; do not reserve a numeric ID in
this definition.

### Parameter supersession link

Add nullable:

```text
parameters.supersedes_parameter_id TEXT
```

It references `parameters.id`. Existing rows remain null.

### Invalidation batches

Add `freshness_invalidations` with at least:

| Column | Contract |
| --- | --- |
| `id` | opaque primary key |
| `workspace_id` | same workspace as both Parameters |
| `superseded_parameter_id` | old accepted Parameter |
| `replacement_parameter_id` | newly accepted Parameter |
| `source_graph_digest` | canonical pre-replacement 050 graph digest |
| `affected_count` | exact number of inserted marks |
| `unresolved_diagnostic_count` | total diagnostics observed in source graph |
| `cycle_count` | affected dependency-cycle count observed by 050 |
| `created_at` | transaction timestamp |

Required uniqueness:

- `(workspace_id, superseded_parameter_id)`;
- `(workspace_id, replacement_parameter_id)`.

### Freshness marks

Add `freshness_marks` with at least:

| Column | Contract |
| --- | --- |
| `id` | opaque primary key |
| `workspace_id` | target workspace |
| `invalidation_id` | owning invalidation batch |
| `record_ref` | canonical 050 target identity |
| `record_kind` | canonical kind copied for bounded querying |
| `record_id` | canonical ID copied for bounded querying |
| `reason_code` | exact `upstream_parameter_superseded` in V0 |
| `path_json` | canonical shortest path array |
| `path_digest` | SHA-256 of canonical path JSON, prefixed `sha256:` |
| `created_at` | batch timestamp |

Required uniqueness:

```text
(invalidation_id, record_ref)
```

The generic target is intentionally not a database foreign key. 050 owns canonical
workspace-safe resolution for heterogeneous record kinds. A mark is immutable evidence of
the state at invalidation time even if a later lifecycle archives the target.

Add indexes for:

- workspace plus record ref;
- invalidation ID plus record ref;
- workspace plus superseded/replacement Parameter IDs.

## Freshness semantics

A record is currently:

- `fresh` when no `freshness_marks` row exists for its canonical ref;
- `stale` when one or more marks exist.

V0 does not clear or mutate a mark. Recomputed outputs are new records/runs and are fresh
unless a later accepted replacement invalidates them. Historical stale records remain
stale relative to their superseded inputs.

Revalidation, mark clearing, equivalence proofs, and "fresh again" semantics require a
separate reviewed contract. Deleting a mark manually is forbidden.

## Read endpoints

### Node freshness

Add:

```http
GET /workspaces/{workspace_id}/flowsheet/nodes/{node_ref}/freshness
```

Use the shared 050 resolver first, preserving the same malformed, absent, and
cross-workspace behavior.

Response:

```json
{
  "record_ref": "simulation_run:<id>",
  "state": "stale",
  "invalidation_count": 1,
  "latest_invalidation": {
    "id": "<id>",
    "source_ref": "parameter:<old-id>",
    "replacement_ref": "parameter:<new-id>",
    "reason_code": "upstream_parameter_superseded",
    "path": ["parameter:<old-id>", "simulation_run:<id>"],
    "path_digest": "sha256:<digest>",
    "created_at": "<timestamp>"
  }
}
```

For a fresh record, `invalidation_count = 0` and `latest_invalidation = null`.

When several invalidations affect one record, latest means descending `created_at`, then
invalidation ID as deterministic tie-break. The count is exact; no cause list is silently
truncated.

### Invalidation detail

Add:

```http
GET /workspaces/{workspace_id}/flowsheet/invalidations/{invalidation_id}
```

Return batch metadata and all marks sorted by `record_ref`. The batch is bounded by the
write-time mark limit, so pagination is unnecessary in V0.

The endpoint returns no Parameter values, run inputs/outputs, artifact paths, prompts,
logs, metrics JSON, decision text, or record bodies.

Missing and cross-workspace invalidations share one not-found response.

## Event contract

On successful first execution, emit exactly one event:

```text
ParameterReplacementAccepted
```

Bounded payload:

- replacement Parameter ID;
- superseded Parameter ID;
- invalidation ID;
- affected count;
- graph digest;
- cycle and unresolved-diagnostic counts.

Do not emit one event per stale record. Do not include old/new values, notes, statements,
paths, raw references, or payloads in the event.

Idempotent replay emits no second event.

## Stable error contract

Use bounded domain errors, mapped without SQL, path, or cross-workspace existence leakage:

- `parameter_replacement_promotion_required`;
- `parameter_replacement_not_configured`;
- `parameter_replacement_not_found`;
- `parameter_replacement_cross_workspace`;
- `parameter_replacement_source_not_accepted`;
- `parameter_replacement_unit_mismatch`;
- `parameter_replacement_value_missing`;
- `parameter_already_replaced`;
- `parameter_replacement_state_inconsistent`;
- `freshness_lineage_incomplete`;
- `freshness_path_limit_exceeded`;
- `freshness_mark_limit_exceeded`;
- existing 050 reference, node, graph, and diagnostics limit reasons.

Validation or lineage errors produce no status, mark, or event change.

## Required implementation shape

One bounded implementation PR may change only what is needed for:

- the next available additive schema migration and indexes;
- Parameter proposal/read fields;
- MemoryStore replacement promotion transaction and response models;
- the minimal 050 internal connection-reuse seam;
- freshness read models/service/routes under the existing flowsheet module;
- focused backend tests;
- canonical 051 lifecycle update.

No frontend is required. Later navigator/project-view work may render freshness through the
read endpoints.

## Required tests

### Proposal and authority

1. user-origin and AI-origin proposed Parameters may explicitly reference one accepted
   same-workspace Parameter;
2. non-Parameter proposals reject the field;
3. cross-workspace, missing, self, non-accepted, wrong-unit, and empty-value replacements
   fail;
4. matching names without the explicit ID create no replacement semantics;
5. multiple alternatives may remain proposed;
6. generic promotion rejects a configured replacement before any state change;
7. calculation-originated proposals cannot silently configure replacement.

### Atomic promotion

8. successful replacement atomically sets old `superseded`, new `accepted`, one batch, all
   marks, and one event;
9. injected failure before commit leaves both statuses, marks, and event counts unchanged;
10. replay returns the original result and creates no duplicate row/event;
11. racing alternatives result in exactly one accepted successor;
12. zero descendants still produces a successful zero-mark invalidation batch.

### Traversal and explanations

13. Parameter to SimulationRun dependency produces a stale run with the exact path;
14. run to Artifact, Decision, and Evidence descendants are marked;
15. the exact `executed_by` bridge reaches calc-produced Parameter outputs;
16. context/proposal/promotion provenance edges do not propagate freshness;
17. equal-length alternatives select the lexicographically smallest complete path;
18. cycles terminate, mark each target once, and report the affected cycle count;
19. the accepted replacement and superseded source are not marked stale;
20. changing insertion order does not change paths, graph digest, affected set, or response
   serialization.

### Lineage and bounds

21. unresolved diagnostics owned by affected nodes fail before status changes;
22. a diagnostic directly naming the superseded Parameter fails closed;
23. unrelated diagnostics are counted but do not block;
24. graph, path, and mark limits return bounded errors and no partial state.

### Read isolation and minimization

25. fresh and stale node freshness responses use the shared 050 resolver;
26. cross-workspace IDs are indistinguishable from absent IDs;
27. invalidation detail returns the complete bounded mark set in deterministic order;
28. responses contain no values, raw payloads, record bodies, paths, metrics, prompts,
   logs, or secret data;
29. read endpoints create no row, event, file, run, or background task.

### Compatibility

30. ordinary proposal promotion without `supersedes_parameter_id` is unchanged;
31. legacy Parameter rows with null supersession remain readable;
32. existing 050 graph and node responses remain byte-equivalent for unchanged fixtures;
33. database initialization and upgrade from the prior migration are additive and
   idempotent;
34. full backend suite, registry gate, BLUECAD canary, and strict real-tool proof pass
   without provider/model/local-runtime activation.

## Non-goals

051 does not implement:

- automatic semantic matching of Parameters;
- replacement triggers for assumptions, requirements, decisions, models, geometry, or
  evidence;
- unit conversion;
- mutation of historical execution or validation status;
- automatic recomputation, scheduling, retries, background workers, or notifications;
- automatic binding of the replacement into a new scenario;
- stale-state clearing or revalidation;
- frontend badges, graph visualization, or project navigation;
- provider, model, Hermes, Ollama, CAD, mesh, FEM, CFD, or optimization execution;
- deletion, archival, promotion, or rejection of downstream records.

## Acceptance outcome

After 051, JarvisOS can answer, deterministically and from persisted evidence:

- which accepted Parameter replaced which prior accepted Parameter;
- which supported records became stale;
- the exact canonical dependency path explaining each stale record;
- which graph snapshot produced the invalidation;
- whether a record is currently fresh or stale.

It still does not decide or execute the recomputation.
