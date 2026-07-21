# 052 — CAD-LINK-0: accepted process bindings to deterministic BLUECAD candidates

Status: ready for implementation after this definition is merged. `docs/specs/STATUS.md`
is authoritative.

Depends on: 005, 038, 050, 051, 071

## Goal

Connect accepted process-model Parameters to BLUECAD without adding an optimizer,
inverse solver, topology generator, second calculation engine, or model authority.

After this slice, an operator can:

1. select a valid BLUECAD candidate as a fixed-topology template;
2. provide an explicit bounded manifest that binds accepted, fresh Parameters to
   semantically compatible GeometrySpec fields;
3. preview the exact resolved GeometrySpec and all conversions with zero writes;
4. execute the exact preview to create a deterministic child candidate, reuse the
   existing build/validation path, and optionally reuse the existing advisory
   mesh/FEM stage;
5. inspect flowsheet lineage from source Parameters through the linked candidate,
   build attempt, artifacts, simulation, validation, and FEM evidence;
6. replace an upstream accepted Parameter and see the supported downstream chain
   become stale through the existing 051 mechanism, without automatic recompute or
   silent promotion.

The process model remains the source of calculation outputs. GeometrySpec remains
the source of CAD construction. Validation and solver evidence remain advisory.

## Runtime findings that constrain V0

### 1. `tube_count` is not a 047 model variable

`bluerev_geometry_hydraulics_v0` currently exposes `tube_length`,
`tube_inner_diameter`, and `tube_outer_diameter`; it has no hydraulic or geometric
`tube_count` input or output.

V0 therefore performs no tube-count binding or assertion. Counting `tube_run` CAD
parts would not prove hydraulic parallel-tube count, illuminated-path count, or
manifold outlet semantics. Tube-count support requires a later spec after a process
model defines the physical quantity, units, topology meaning, and validation rule.

### 2. GeometrySpec stores outer diameter and wall thickness

The current tube-compatible builders use `outer_d`/`out_d`/`port_d` plus wall
thickness; they do not store an independent `inner_d` field. The only derived V0
binding is:

```text
wall_t = (outer_d - inner_d) / 2
```

Both source values must be accepted, fresh, finite, positive, semantically correct,
and dimensionally compatible. The result must satisfy existing GeometrySpec wall
and port-compatibility checks. No expression language is introduced.

### 3. Process `tube_length` is aggregate; CAD has named straight segments

The process model's `tube_length` is total illuminated straight-tube centreline
length. A template can contain multiple named `tube_run` parts. Copying the total
into each part would multiply the physical length.

V0 therefore supports an explicit equal split over an ordered list of named
`tube_run.length` targets. It does not discover paths, subtract bend arc lengths,
include manifold branches, infer illumination, or change topology.

### 4. Existing AI-loop persistence cannot be reused blindly

The current candidate creator records `origin=ai`; attempts require a proposal
outcome; artifact notes currently identify the AI loop as producer. CAD-LINK must
not manufacture AI provenance.

Implementation may extract and reuse low-level deterministic build, validation,
artifact, and simulation helpers, but must add explicit non-AI candidate, attempt,
and artifact semantics.

### 5. Existing 051 traversal does not follow every provenance edge

051 follows dependency edges, not arbitrary provenance. Existing generic
candidate→attempt and candidate→current-artifact edges are provenance edges, so a
new source Parameter→candidate edge alone would not stale every linked artifact or
validation record.

V0 must add narrowly scoped dependency edges for process-linked build outputs as
defined below. It must not globally reinterpret all historical BLUECAD provenance
as dependency.

## Supported source semantics

Units alone are insufficient: any arbitrary Parameter measured in metres must not
be allowed to drive any arbitrary CAD length.

V0 accepts only these exact Parameter `name` values:

- `tube_length`;
- `tube_inner_diameter`;
- `tube_outer_diameter`.

A source Parameter may originate from `calc`, user entry, or another governed path,
but its exact name, accepted status, value, unit, workspace, source reference, and
freshness are snapshotted and validated.

No aliasing, fuzzy matching, display-label matching, symbol matching, or caller-
supplied semantic override is allowed.

## Supported target matrix

The normalized manifest must reject all source/target combinations outside this
closed matrix.

### `tube_length`

Allowed only through `split_total_length_equal` to:

- `tube_run.length`.

### `tube_outer_diameter`

Allowed through `copy` to tube-interface diameter fields:

- `tube_run.outer_d`;
- `bend.outer_d`;
- `joint.outer_d`;
- `manifold.out_d`;
- `harvest_module.port_d`.

It may not set `manifold.outer_d_main`, `harvest_module.outer_d`, float dimensions,
bend radius, spacing, socket length, or unrelated dimensions.

### Derived wall thickness

`wall_from_outer_inner` consumes exactly one `tube_outer_diameter` and one
`tube_inner_diameter`. It may write only:

- `tube_run.wall_t`;
- `bend.wall_t`;
- `joint.wall_t`;
- `manifold.out_wall_t`;
- `harvest_module.wall_t` only when the target port is part of the same declared
  tube interface and the resolved GeometrySpec passes existing validation.

The manifest must name every target explicitly. CAD-LINK does not auto-discover
connected parts or silently repair omitted interface fields; existing validation
must fail honestly when the operator provides an incomplete binding set.

## Authority and safety invariants

1. Only Parameter rows with `status=accepted` may drive execution.
2. Every source Parameter and optional source run must belong to the template's
   workspace.
3. Every source Parameter and the template candidate must be `fresh` under 051 at
   preview and again at execution.
4. Proposed, rejected, superseded, stale, missing, non-numeric, non-finite,
   semantically mismatched, or unit-mismatched values fail closed.
5. Preview is side-effect free.
6. Execution is bound to one canonical preview digest and revalidates the full
   source/template snapshot before any write.
7. No LLM or provider call occurs; preview and execute write zero `ai_jobs` rows.
8. No topology mutation occurs.
9. No calculation result, candidate, validation result, decision, or FEM result is
   promoted automatically.
10. A stale linked candidate remains inspectable immutable history; it is not
    overwritten, deleted, rebuilt, or silently marked current.
11. Existing GeometrySpec validation and deterministic build/export remain
    authoritative for CAD validity.
12. Existing mesh/FEM outputs remain advisory evidence and never rewrite source
    Parameters.
13. A deterministic CAD-LINK attempt is never represented as an AI proposal.

## API surface

Add two workspace-scoped endpoints under the selected template candidate:

```text
POST /workspaces/{workspace_id}/bluecad/candidates/{template_candidate_id}/cad-link/preview
POST /workspaces/{workspace_id}/bluecad/candidates/{template_candidate_id}/cad-link/execute
```

The template candidate must:

- exist in the workspace;
- have status `valid`;
- have a registered canonical GeometrySpec artifact whose stored SHA and recomputed
  canonical spec identity agree;
- be fresh;
- remain unchanged between preview and execute.

## Preview request

```json
{
  "source_simulation_run_id": "optional-run-id",
  "bindings": [],
  "analysis_spec": null
}
```

`analysis_spec` follows the existing 038 contract without geometry. It is optional
and receives geometry only from validated build artifacts during execution.

`source_simulation_run_id` is optional lineage context. When supplied, it must be a
workspace run that is provably upstream of every calc-origin source Parameter:

```text
simulation_run -> runner_job -> parameter.source_ref
```

Manual/user-origin Parameters need not share run provenance. A supplied run that
does not cover every calc-origin source fails rather than recording misleading
lineage.

## Binding manifest

The manifest is a strict list with at most 32 bindings and 128 total targets.
Unknown fields, nulls, booleans-as-numbers, duplicate sources where forbidden,
duplicate target identities, and oversized UTF-8 fail validation.

Every target uses stable semantic identity:

```json
{"part_id": "run_top", "param": "length"}
```

Array-index JSON paths are forbidden because part ordering is not an engineering
identity.

V0 supports exactly three operators.

### `copy`

Consumes exactly one `tube_outer_diameter` Parameter and writes the converted value
to one or more allowed diameter targets.

```json
{
  "operator": "copy",
  "source_parameter_ref": "parameter:<outer-id>",
  "targets": [
    {"part_id": "run_top", "param": "outer_d"},
    {"part_id": "left", "param": "out_d"}
  ]
}
```

### `wall_from_outer_inner`

Consumes exactly one outer and one inner diameter source and writes the derived wall
thickness to named allowed wall targets.

```json
{
  "operator": "wall_from_outer_inner",
  "outer_parameter_ref": "parameter:<outer-id>",
  "inner_parameter_ref": "parameter:<inner-id>",
  "targets": [
    {"part_id": "run_top", "param": "wall_t"},
    {"part_id": "left", "param": "out_wall_t"}
  ]
}
```

### `split_total_length_equal`

Consumes exactly one `tube_length` Parameter and writes an equal share to each
explicitly listed `tube_run.length` target.

```json
{
  "operator": "split_total_length_equal",
  "source_parameter_ref": "parameter:<length-id>",
  "targets": [
    {"part_id": "run_top", "param": "length"},
    {"part_id": "run_bottom", "param": "length"}
  ]
}
```

Targets are sorted canonically by `(part_id, param)` before allocation. Conversion
and division use decimal arithmetic from the exact stored numeric text. All but the
last canonical target receive the same decimal quotient at the chosen canonical
precision; the last receives the deterministic remainder. After conversion to
finite JSON numbers, the sum must equal the converted source within both:

- absolute error `<= 1e-6 mm`;
- relative error `<= 1e-12`.

The preview returns quotient, remainder, target ordering, and observed conservation
errors. Binary-float iteration order must not determine the result.

## Units and numeric parsing

V0 implements a closed conversion table, not a generic units package:

- `m` → `mm`;
- `mm` → `mm`.

The source `parameters.value` string is parsed through one strict decimal parser.
Accepted syntax is finite base-10 numeric text only. Whitespace-normalized but
otherwise equivalent text canonicalizes to one representation. Empty strings,
booleans, NaN, Infinity, locale commas, embedded units, expressions, and trailing
text fail.

No inferred unit, alias, offset conversion, compound-unit conversion, or unit-string
normalization is allowed.

## Preview response

Preview returns at least:

- canonical resolved GeometrySpec;
- resolved `spec_id` and canonical JSON digest;
- canonical normalized binding manifest and digest;
- exact source snapshot containing Parameter refs, names, values, units, statuses,
  origins, freshness states, and source refs;
- source snapshot digest;
- template candidate id, template artifact SHA, canonical template spec id, and
  digest;
- optional validated source simulation run id;
- deterministic per-binding conversion/derivation details;
- target ordering and length-conservation evidence;
- inherited GeometrySpec numeric fields not written by the manifest;
- factual non-authoritative warnings;
- canonical analysis contract digest when supplied;
- one `preview_digest` covering every execution-relevant field and version.

Inherited GeometrySpec values remain template values and are listed as such; they
are not represented as solved process outputs.

Preview performs no candidate, attempt, artifact, evidence, event, freshness, link,
filesystem-build, or `ai_jobs` write.

## Execute request and TOCTOU boundary

Execution receives the original request plus the exact `preview_digest`.

Before any write or build-directory creation, execution must reload and revalidate:

- template candidate status, freshness, artifact SHA, canonical spec id, and digest;
- every source Parameter name, exact numeric value, unit, status, origin, source
  reference, workspace, and freshness state;
- optional source simulation-run lineage;
- normalized manifest, resolved GeometrySpec, analysis contract, and all digests;
- the implementation contract/version identifiers included in the preview.

Any mismatch returns `409 cad_link_preview_stale` with zero candidate, attempt,
artifact, evidence, link, event, build-directory, or AI writes.

## Persistence and provenance

### Candidate semantics

Add `process_linked` to `CandidateOrigin` and `cad_link_failed` to the parked-reason
contract.

A successful or validation-failed execution creates one child candidate with:

- `origin=process_linked`;
- `parent_candidate_id=<template_candidate_id>`;
- no `proposal_ai_job_id`;
- `loop_config_json={}` as an explicit not-applicable legacy field; no provenance,
  analysis settings, or binding data is stored there;
- one deterministic attempt with `route_class=deterministic:cad_link`;
- `proposal_outcome=not_applicable`, added to the typed attempt contract;
- artifacts and validation report from the shared deterministic BLUECAD path.

A resolved spec that reaches build/validation but fails creates an inspectable
`parked(cad_link_failed)` child with its report and link provenance. Invalid input
or stale preview creates no child.

Artifact registration must accept an explicit producer/source description. CAD-LINK
artifacts must not carry the current "Generated by BLUECAD AI loop v0" note or any
other false AI claim.

### Additive link record

Add one additive persistence object, expected table `bluecad_cad_links`, with at
least:

- id;
- workspace_id;
- template_candidate_id;
- child_candidate_id, unique;
- optional source_simulation_run_id;
- canonical binding_manifest_json and digest;
- canonical source_snapshot_json and digest;
- template_spec_digest;
- analysis_contract_digest when supplied;
- preview_digest;
- resolved_spec_digest;
- created_at.

The source snapshot is immutable audit evidence, not a second mutable Parameter
store. Runtime reads continue to use canonical Parameter rows.

The implementation uses the next additive migration id. Candidate, attempt, link,
and final artifact/evidence references must be persisted coherently. An unexpected
persistence failure must never leave a candidate marked `valid` without its link
record; it must leave an honest parked/failed state or roll back the database unit
of work. Staged filesystem output receives best-effort cleanup and is never exposed
as a registered successful artifact without committed metadata.

## Flowsheet and stale-propagation integration

Extend the existing 050 graph builder, not a second graph engine.

For each CAD-link record, materialize:

- each source `parameter:<id>` → child `bluecad_candidate:<id>` as
  `geometry_binding`, edge class `dependency`;
- optional `simulation_run:<id>` → child candidate as `cad_link_source_run`, edge
  class `provenance`.

For `origin=process_linked` only, materialize the deterministic downstream build
chain as dependency edges:

- child candidate → deterministic attempt as `process_link_build`;
- child candidate and/or deterministic attempt → registered current build artifacts
  as `process_link_artifact`, using the existing canonical nodes and avoiding
  duplicate logical edges;
- existing report-artifact → validation-evidence dependency remains authoritative;
- existing candidate/attempt → simulation-run dependency remains authoritative for
  optional mesh/FEM;
- existing simulation-run/report-artifact → evidence dependencies remain
  authoritative.

Do not globally change historical AI candidate provenance edge classes. Do not add
a new flowsheet node kind solely for the link row.

Replacing any source Parameter must cause 051 to mark the child candidate and every
supported downstream attempt, artifact, simulation run, validation record, and FEM
record stale where a dependency path exists. Tests must assert each exact path and
must not claim staleness for nodes connected only by advisory provenance.

## Deterministic execution path

Implementation must reuse the existing:

- GeometrySpec canonicalization and validation;
- `build_geometry_spec` construction/export path;
- artifact hashing and registration;
- validation evidence mapping;
- optional 038 mesh/FEM stage.

A small extraction from the AI loop into a shared deterministic helper is allowed
only where needed to avoid duplicate build/simulation logic. Existing AI-loop
behavior and tests must remain unchanged. A second CAD builder, validation mapper,
artifact store, simulation engine, or evidence path is forbidden.

Same template spec digest + same canonical source snapshot + same canonical manifest
+ same analysis contract + same implementation version must produce the same
resolved GeometrySpec and same-environment artifact digests.

## Error contract

Required bounded reason codes include at least:

- `cad_link_template_not_found`;
- `cad_link_template_not_valid`;
- `cad_link_template_stale`;
- `cad_link_spec_artifact_invalid`;
- `cad_link_manifest_invalid`;
- `cad_link_source_not_found`;
- `cad_link_source_not_accepted`;
- `cad_link_source_stale`;
- `cad_link_source_semantic_mismatch`;
- `cad_link_source_not_numeric`;
- `cad_link_unit_unsupported`;
- `cad_link_target_invalid`;
- `cad_link_target_conflict`;
- `cad_link_source_run_mismatch`;
- `cad_link_preview_stale`;
- `cad_link_persistence_failed`.

Reject duplicate writes to one target, unknown parts, unsupported part/param pairs,
topology edits, invalid numeric domains, and payloads above declared bounds.

Expected response classes:

- `404` for absent workspace-scoped resources;
- `409` for stale template/source/preview or conflicting current state;
- `422` for malformed manifest, semantic mismatch, unsupported unit/operator/target,
  or invalid numeric domain;
- `500` with a safe bounded code for unexpected persistence/build infrastructure
  failure, never internal paths or SQL text.

## Files likely touched

Verify against current code before implementation and stop on conflict.

Expected bounded set:

- `backend/app/core/schema.py`;
- `backend/app/modules/bluecad/cad_link.py` (new service);
- `backend/app/modules/bluecad/models.py`;
- `backend/app/modules/bluecad/routes.py`;
- `backend/app/modules/bluecad/ledger.py`;
- `backend/app/modules/bluecad/loop.py` only for the smallest shared-helper
  extraction;
- `backend/app/modules/flowsheet/service.py`;
- `backend/tests/bluecad/test_cad_link.py` (new);
- focused flowsheet/freshness tests;
- `docs/specs/STATUS.md`.

No frontend file is in scope.

## Acceptance criteria

1. Preview with accepted fresh `tube_length`, `tube_inner_diameter`, and
   `tube_outer_diameter` returns a canonical resolved GeometrySpec, complete source
   snapshot, conversion evidence, inherited-field list, and preview digest with zero
   database/filesystem writes.
2. Sources with the wrong exact semantic name are rejected even when their units and
   numeric values are compatible.
3. `wall_from_outer_inner` computes `(outer-inner)/2`, rejects invalid dimensions,
   and passes existing wall/port validation when the complete binding set is valid.
4. `split_total_length_equal` writes only named `tube_run.length` fields and proves
   deterministic aggregate conservation and remainder handling.
5. No tube-count field, assertion, topology mutation, or implied parallel-flow
   semantics exists in V0.
6. Execute with the exact current preview creates one child candidate with
   `origin=process_linked`, a deterministic non-AI attempt, honest artifact metadata,
   correct parent/link record, and zero `ai_jobs` rows.
7. Repeating the same source snapshot and manifest yields identical resolved-spec
   and same-environment artifact digests while retaining separate immutable child
   history.
8. Any template/source/run/version/freshness/digest change between preview and
   execute returns `409 cad_link_preview_stale` before writes or directory creation.
9. Proposed, rejected, superseded, stale, cross-workspace, non-numeric, non-finite,
   unsupported-unit, semantic-mismatch, unknown-target, duplicate-target, and
   topology-edit cases fail closed with no candidate or artifact writes.
10. A validly resolved spec that fails existing validation creates an inspectable
    `parked(cad_link_failed)` child with report and link provenance.
11. Optional mesh/FEM reuses 038, records typed evidence, and cannot promote or
    rewrite process Parameters.
12. The 050 graph contains the scoped process-linked dependency chain. Replacing a
    source Parameter causes 051 to stale the candidate and every dependency-reachable
    build/simulation/evidence node with explainable paths, without reclassifying
    historical AI provenance.
13. Persistence failure cannot expose a valid unlinked candidate or a registered
    artifact with false/missing producer provenance.
14. Existing AI candidate creation, build, validation, simulation, artifact,
    flowsheet, and freshness behavior remains regression-green.
15. No frontend, optimizer, inverse solver, topology generator, generic unit engine,
    provider call, automatic recompute, or automatic promotion is added.

## Required tests

Offline tests must cover at least:

- preview happy path and zero-write assertion across relevant tables and filesystem;
- exact source-name allowlist and same-unit semantic mismatch;
- strict decimal parsing;
- wall derivation and invalid inner/outer combinations;
- equal aggregate-length split, canonical ordering, deterministic remainder, and
  conservation bounds;
- target allowlist across tube runs, bends, joints, manifold outlets, and harvest
  ports/walls;
- omitted interface-field validation failure without automatic repair;
- source authority/freshness/workspace/unit/numeric failures;
- unknown, duplicate, conflicting, and topology-edit targets;
- payload bounds;
- preview/execute TOCTOU rejection before writes/directories;
- successful deterministic child build, honest attempt/artifact provenance, and zero
  `ai_jobs` rows;
- validation-failed parked child;
- coherent persistence-failure behavior;
- identical resolved-spec/artifact digests for identical inputs;
- optional mesh/FEM evidence using existing offline fixtures/fakes;
- flowsheet dependency edges and exact 051 stale paths;
- proof that historical AI candidate edge semantics are unchanged;
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
assumption may be required by the offline suite.

## Non-goals

- No UI, slider panel, comparison surface, or workspace redesign; 006b and 058 own
  those surfaces.
- No tube-count semantics in V0.
- No topology synthesis, part creation/removal, connection editing, manifold outlet
  mutation, or automatic path discovery.
- No optimizer, target solver, inverse calculation, sensitivity sweep, or automatic
  scenario selection.
- No automatic recomputation after an upstream change.
- No automatic promotion of Parameters, candidates, decisions, or solver evidence.
- No general expression language or general-purpose unit-conversion framework.
- No new process formulas, embedded design defaults, or changes to 047–049 validity
  domains.
- No direct provider/model call and no AI repair of failed linked geometry.
- No broad BLUECAD ledger, artifact, flowsheet, or runner refactor.

## Definition of done

The spec is implemented as one reviewable slice, all acceptance criteria and offline
gates pass, `STATUS.md` points to the implementation PR while in review,
implementation notes disclose runtime conflicts, and the maintainer—not the
implementing agent—decides whether to merge.
