# 052 — CAD-LINK-0: accepted process bindings to deterministic BLUECAD candidates

Status: ready for implementation after this definition is merged. `docs/specs/STATUS.md`
is authoritative.

Depends on: 005, 038, 050, 051, 071

## Goal

Connect the accepted, caller-editable process-model state to BLUECAD without adding
an optimizer, inverse solver, second calculation engine, or model authority.

After this slice, an operator can:

1. select a valid BLUECAD candidate as a fixed-topology template;
2. provide an explicit bounded binding manifest from accepted, fresh Parameter
   records to named GeometrySpec parameters;
3. preview the fully resolved GeometrySpec and all deterministic conversions with
   zero writes;
4. execute the exact preview to create a deterministic child candidate, run the
   existing build/validation path, and optionally run the existing advisory
   mesh/FEM stage;
5. inspect flowsheet lineage from the source Parameters through the child candidate,
   artifacts, validation, and FEM evidence;
6. replace an upstream accepted Parameter and see the linked CAD/evidence chain
   become stale through the existing 051 mechanism, without automatic recompute or
   silent promotion.

The process model remains the source of calculation outputs. GeometrySpec remains
the source of CAD construction. Solver evidence remains advisory.

## Runtime findings that constrain V0

This spec resolves concrete mismatches in the merged runtime rather than assuming
that the process and CAD schemas already align.

### 1. The process model does not produce `tube_count`

`bluerev_geometry_hydraulics_v0` currently accepts `tube_length`,
`tube_inner_diameter`, and `tube_outer_diameter`, but it has no `tube_count`
input or output.

Therefore V0 must not claim that 047 calculates tube count. A tube-count Parameter
may be supplied only as an independently accepted, unitless integer topology
assertion. It may verify the selected template but may not create or remove parts,
connections, ports, or manifold outlets.

### 2. GeometrySpec stores outer diameter and wall thickness

The current tube and bend builders use `outer_d` and `wall_t`; they do not store
an independent `inner_d` field. The only allowed V0 derived binding is:

```text
wall_t = (outer_d - inner_d) / 2
```

Both source values must be accepted, fresh, finite, positive, and dimensionally
compatible. The result must satisfy the existing GeometrySpec wall constraint.
No other free-form expression language is introduced.

### 3. Process `tube_length` is aggregate; CAD has named segments

The process model's `tube_length` is total illuminated tube centreline length.
A template can contain multiple `tube_run` parts. Copying the total length into
every part would silently multiply the physical length.

V0 therefore supports an explicit `split_total_length_equal` operator over an
ordered set of named `tube_run.length` targets. After unit conversion, the sum of
the written target lengths must equal the source total within the deterministic
numeric tolerance defined below.

No implicit target discovery, proportional split, topology generation, bend-length
subtraction, or path inference is allowed.

### 4. Existing AI-loop persistence cannot be reused blindly

The current candidate creator records `origin=ai`, and its artifact notes state that
the AI loop generated the result. CAD-LINK must not write false provenance.
Implementation may share low-level build, validation, artifact, and simulation
helpers, but it needs an explicit deterministic candidate origin and link record.

## Authority and safety invariants

1. Only Parameter records with `status=accepted` may drive execution.
2. Every source Parameter must belong to the same workspace as the template.
3. Every source Parameter must be `fresh` under the 051 overlay at preview and
   again at execution.
4. Proposed, rejected, superseded, stale, non-numeric, non-finite, or unit-mismatched
   values fail closed.
5. Preview is side-effect free.
6. Execution is digest-bound to one preview and revalidates the source snapshot to
   prevent time-of-check/time-of-use drift.
7. No LLM or provider call occurs; the flow writes zero `ai_jobs` rows.
8. No topology mutation occurs.
9. No calculation result, CAD result, validation result, or FEM result is promoted
   automatically.
10. A stale linked candidate remains inspectable history; it is not overwritten,
    deleted, rebuilt, or silently marked current.
11. Existing GeometrySpec validation and deterministic build/export remain
    authoritative for CAD validity.
12. Existing mesh/FEM outputs remain advisory evidence and never rewrite upstream
    Parameters.

## API surface

Add two workspace-scoped endpoints under the selected template candidate:

```text
POST /workspaces/{workspace_id}/bluecad/candidates/{template_candidate_id}/cad-link/preview
POST /workspaces/{workspace_id}/bluecad/candidates/{template_candidate_id}/cad-link/execute
```

The template candidate must exist in the workspace, have status `valid`, have a
registered canonical GeometrySpec artifact, and not itself be stale.

### Preview request

The request contains:

```json
{
  "source_simulation_run_id": "optional-run-id",
  "bindings": [],
  "analysis_spec": null
}
```

`source_simulation_run_id` is optional lineage context. When supplied, it must
belong to the workspace and be the run provenance of every calc-origin Parameter
used by the manifest; otherwise preview fails rather than recording a misleading
run link.

`analysis_spec` follows the existing 038 analysis contract without geometry. It is
optional and receives geometry only from the validated build artifacts during
execution.

### Binding manifest

The manifest is a bounded list with at most 32 bindings and 128 total targets.
Each target uses stable semantic identity:

```json
{"part_id": "run_top", "param": "length"}
```

Array-index JSON paths are forbidden because part ordering is not an engineering
identity.

V0 supports exactly these operators.

#### `copy`

Copies one source Parameter to one or more explicitly named numeric GeometrySpec
parameters using an allowed exact unit conversion.

```json
{
  "operator": "copy",
  "source_parameter_refs": ["parameter:<id>"],
  "targets": [{"part_id": "run_top", "param": "outer_d"}]
}
```

#### `wall_from_outer_inner`

Consumes exactly two source Parameters, explicitly labelled `outer` and `inner`,
and writes the derived wall thickness to named `wall_t` targets.

```json
{
  "operator": "wall_from_outer_inner",
  "outer_parameter_ref": "parameter:<outer-id>",
  "inner_parameter_ref": "parameter:<inner-id>",
  "targets": [{"part_id": "run_top", "param": "wall_t"}]
}
```

#### `split_total_length_equal`

Consumes one total-length Parameter and writes an equal share to each explicitly
listed `tube_run.length` target. The target list must contain at least one item.

```json
{
  "operator": "split_total_length_equal",
  "source_parameter_refs": ["parameter:<length-id>"],
  "targets": [
    {"part_id": "run_top", "param": "length"},
    {"part_id": "run_bottom", "param": "length"}
  ]
}
```

The canonical result must preserve the converted aggregate length. The absolute
sum error must be no greater than `1e-9 mm` after deterministic decimal arithmetic
and canonical serialization.

#### `assert_part_count`

Consumes one accepted unitless integer Parameter and verifies the selected template
contains exactly that number of parts of the declared supported kind. V0 supports
only `part_kind=tube_run`.

```json
{
  "operator": "assert_part_count",
  "source_parameter_refs": ["parameter:<count-id>"],
  "part_kind": "tube_run"
}
```

This operator never edits GeometrySpec.

### Unit conversions

V0 implements a closed conversion table, not a generic units package:

- `m` to `mm` and `mm` to `mm` for GeometrySpec lengths and diameters;
- `1` to integer assertion for `assert_part_count`.

No inferred unit, alias, offset conversion, compound-unit conversion, or
unit-string normalization is allowed. Unsupported units return a structured
validation error.

### Preview response

Preview returns at least:

- canonical resolved GeometrySpec;
- resolved `spec_id` and canonical JSON digest;
- canonical normalized binding manifest and manifest digest;
- exact source snapshot containing Parameter refs, accepted values, units,
  statuses, freshness states, and source refs;
- source snapshot digest;
- template candidate and template spec digests;
- source simulation run id when valid and supplied;
- deterministic per-binding conversion details;
- topology assertions and their results;
- unresolved GeometrySpec numeric DOF not written by the manifest;
- warnings that are factual and non-authoritative;
- one `preview_digest` covering all execution-relevant fields.

Unresolved GeometrySpec values are inherited transparently from the template and
listed; they are not represented as solved process-model outputs.

Preview performs no candidate, attempt, artifact, evidence, event, freshness,
link, or `ai_jobs` write.

### Execute request

Execution receives the original request plus the exact `preview_digest`.

Before any write, execution must reload and revalidate:

- template candidate and canonical spec digest;
- every Parameter value, unit, status, source reference, and freshness state;
- optional source simulation run provenance;
- manifest normalization and resolved-spec digest.

Any mismatch returns `409 cad_link_preview_stale` with zero candidate, attempt,
artifact, evidence, link, or AI writes.

## Persistence and provenance

### Candidate semantics

Add `process_linked` to `CandidateOrigin`.

A successful or validation-failed execution creates one child candidate with:

- `origin=process_linked`;
- `parent_candidate_id=<template_candidate_id>`;
- no `proposal_ai_job_id`;
- one deterministic attempt identified as a local CAD-link build, not an AI
  proposal;
- artifacts and validation report from the existing BLUECAD build path.

Add `cad_link_failed` to the parked-reason contract. A resolved spec that reaches
the build/validation path but fails validation creates an inspectable parked child
with its report and provenance. Invalid input or stale preview creates no child.

Do not store CAD-link provenance in free-form notes or overload
`loop_config_json` as a second schema.

### Additive link record

Add one additive persistence object, expected table name `bluecad_cad_links`, with
at least:

- id;
- workspace_id;
- template_candidate_id;
- child_candidate_id, unique after execution;
- optional source_simulation_run_id;
- canonical binding_manifest_json and digest;
- canonical source_snapshot_json and digest;
- preview_digest;
- resolved_spec_digest;
- created_at.

The implementation must use the next additive migration id and follow the existing
schema migration discipline. No existing row is rewritten to manufacture lineage.

### Flowsheet integration

Extend the existing 050 graph builder, not a second graph engine.

For each CAD-link record, materialize:

- each source `parameter:<id>` → child `bluecad_candidate:<id>` as relation
  `geometry_binding`, edge class `dependency`;
- optional `simulation_run:<id>` → child candidate as relation
  `cad_link_source_run`, edge class `provenance`.

The existing candidate→artifact, candidate/attempt→evidence, and simulation/evidence
edges remain authoritative. Do not add a new flowsheet node kind solely for the
link record in V0.

Because the source-Parameter edges are dependencies, existing 051 propagation must
mark the linked candidate and all supported downstream artifacts/evidence stale
when a source Parameter is replaced. Tests must assert the explainable path.

## Deterministic execution path

Implementation must reuse the existing:

- GeometrySpec canonicalization and schema validation;
- `build_geometry_spec` construction/export path;
- artifact registration rules;
- validation evidence mapping;
- optional 038 mesh/FEM stage.

A small extraction from the AI loop into a shared deterministic helper is allowed
only where needed to avoid duplicated build/simulation logic. It must preserve the
existing AI-loop behavior and tests. A second CAD builder or simulation engine is
forbidden.

Same template spec digest + same canonical source snapshot + same canonical
manifest + same analysis contract must produce the same resolved GeometrySpec and
same-environment artifact digests.

## Error contract

Use structured, bounded errors. Required codes include at least:

- `cad_link_template_not_found`;
- `cad_link_template_not_valid`;
- `cad_link_template_stale`;
- `cad_link_spec_artifact_invalid`;
- `cad_link_manifest_invalid`;
- `cad_link_source_not_found`;
- `cad_link_source_not_accepted`;
- `cad_link_source_stale`;
- `cad_link_source_not_numeric`;
- `cad_link_unit_unsupported`;
- `cad_link_target_invalid`;
- `cad_link_target_conflict`;
- `cad_link_topology_mismatch`;
- `cad_link_source_run_mismatch`;
- `cad_link_preview_stale`.

Reject duplicate writes to the same target, duplicate target identities, unknown
parts, unsupported params, topology-field edits, boolean-as-number values,
non-finite values, and payloads above the declared bounds.

Expected response classes:

- `404` for absent workspace-scoped resources;
- `409` for stale template/source/preview or conflicting current state;
- `422` for malformed manifest, unsupported unit/operator/target, invalid numeric
  domain, or topology assertion failure.

No internal path, SQL text, secret, or unbounded stored payload is returned.

## Files likely touched

Verify these against current code before implementation; stop on conflict rather
than guessing.

Expected bounded set:

- `backend/app/core/schema.py`;
- `backend/app/modules/bluecad/cad_link.py` (new service);
- `backend/app/modules/bluecad/models.py`;
- `backend/app/modules/bluecad/routes.py`;
- `backend/app/modules/bluecad/ledger.py`;
- `backend/app/modules/bluecad/loop.py` only for the smallest shared-helper
  extraction required by deterministic build/simulation reuse;
- `backend/app/modules/flowsheet/service.py`;
- `backend/tests/bluecad/test_cad_link.py` (new);
- focused flowsheet/freshness tests;
- `docs/specs/STATUS.md`.

No frontend file is in scope.

## Acceptance criteria

1. Previewing a valid template with accepted fresh diameter and aggregate-length
   Parameters returns a canonical resolved GeometrySpec, complete source snapshot,
   conversions, inherited DOF list, and preview digest with zero database writes.
2. `wall_from_outer_inner` computes `(outer-inner)/2`, rejects invalid dimensions,
   and produces a GeometrySpec that passes the existing wall checks when the inputs
   are valid.
3. `split_total_length_equal` writes only the named tube runs and preserves total
   converted length within the specified tolerance.
4. `assert_part_count` verifies a unitless accepted integer and never mutates
   topology.
5. Execute with the exact current preview creates one child candidate with
   `origin=process_linked`, correct parent, deterministic attempt/artifacts/report,
   and zero `ai_jobs` rows.
6. Repeating the same source snapshot and manifest yields an identical resolved
   spec digest and same-environment artifact digests while preserving immutable
   history as separate child candidates.
7. Any source/template change, replacement, stale mark, status change, or digest
   mismatch between preview and execute returns `409 cad_link_preview_stale` before
   writes.
8. Proposed, rejected, superseded, stale, cross-workspace, non-numeric, non-finite,
   unsupported-unit, unknown-target, duplicate-target, and topology-mismatch cases
   fail closed with no candidate or artifact writes.
9. A validly resolved GeometrySpec that fails existing validation creates an
   inspectable `parked(cad_link_failed)` child with report and provenance rather
   than returning an unhandled server error.
10. Optional mesh/FEM execution reuses 038, records typed evidence, and cannot
    promote or rewrite process Parameters.
11. The 050 graph contains source Parameter→child candidate dependency edges and
    the existing downstream evidence chain. Replacing a source Parameter causes
    051 to mark the child and supported downstream nodes stale with an explainable
    path.
12. Existing AI candidate creation, build, validation, simulation, artifact, and
    flowsheet behavior remains regression-green.
13. No frontend, optimizer, inverse solver, topology generator, generic unit engine,
    provider call, automatic recompute, or automatic promotion is added.

## Required tests

Offline tests must cover at least:

- preview happy path and zero-write assertion across all relevant tables;
- wall derivation and invalid inner/outer combinations;
- equal aggregate-length split and numeric conservation;
- topology-count pass/fail and no topology mutation;
- all source authority/freshness/workspace/unit/numeric failures;
- unknown, duplicate, conflicting, and topology-edit targets;
- payload bounds;
- preview/execute TOCTOU rejection with zero writes;
- successful deterministic child build and zero `ai_jobs` rows;
- validation-failed parked child;
- identical resolved spec/artifact digests for identical inputs;
- optional mesh/FEM evidence using existing offline fixtures/fakes;
- flowsheet source edges and 051 stale propagation path;
- regression coverage for existing AI-loop candidate creation.

Required gate:

```text
cd backend
python -m pytest -q
python -m ruff check app tests
cd ..
python scripts/check_spec_status.py --self-test
```

No live provider, Ollama, Gmsh, CalculiX, network, or Windows-specific data-root
assumption may be required by the offline test suite.

## Non-goals

- No UI, slider panel, comparison surface, or workspace redesign; 006b and 058 own
  those surfaces.
- No dynamic topology synthesis, part creation/removal, connection editing, manifold
  outlet mutation, or automatic tube-count selection.
- No optimizer, target solver, inverse calculation, sensitivity sweep, or automatic
  scenario selection.
- No automatic recomputation after an upstream change.
- No automatic promotion of Parameters, candidates, decisions, or solver evidence.
- No general expression language or general-purpose unit-conversion framework.
- No new process formulas, embedded design defaults, or changes to 047–049 validity
  domains.
- No direct provider/model call and no AI repair of a failed linked geometry.
- No broad BLUECAD ledger, artifact, flowsheet, or runner refactor.

## Definition of done

The full spec is implemented as one reviewable slice, all acceptance criteria and
required offline gates pass, `STATUS.md` points to the implementation PR while in
review, implementation notes disclose any runtime conflict, and the maintainer—not
the implementing agent—decides whether to merge.
