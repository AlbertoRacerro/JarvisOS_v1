# 052 — CAD-LINK-0: 047 M0 cylinder proxy to deterministic BLUECAD

Status: ready for implementation after this definition is merged. `docs/specs/STATUS.md`
is authoritative.

Depends on: 005, 038, 050, 051, 071

## Goal

Turn one successful, parameter-backed `bluerev_geometry_hydraulics_v0` run into a
deterministic BLUECAD candidate that represents the **same M0 cylindrical tube
approximation** used by spec 047.

After this slice, an operator can:

1. select a successful 047 scenario run whose three geometry inputs are bound to
   accepted, fresh Parameters;
2. preview the exact one-part GeometrySpec and all transformations with zero writes;
3. execute the exact preview to create one deterministic `tube_run` candidate,
   reuse existing build/validation, and optionally reuse the advisory mesh/FEM stage;
4. inspect lineage from the three source Parameters through the 047 run, linked CAD
   candidate, build artifacts, validation, and optional FEM evidence;
5. replace an upstream accepted Parameter and see the supported downstream chain
   become stale through existing 050/051 behavior, without automatic recompute or
   promotion.

The process model remains authoritative for the M0 calculation. GeometrySpec remains
a deterministic representation of that approximation. Validation and FEM remain
advisory.

## Why V0 is deliberately a one-tube proxy

### 047 is an M0 cylinder approximation

Spec 047 defines `tube_length` as the illuminated tube centreline length used by an
M0 cylinder approximation. Its volume, area, transit time, pressure drop, and pump
power use that one aggregate length directly.

A full BLUECAD reactor may contain straight runs, bends, joints, manifolds, harvest
modules, branches, and multiple paths. Mapping the aggregate 047 length only into
straight `tube_run` parts would add bend/component lengths implicitly and make CAD
volume, wetted length, transit time, and pressure-loss basis disagree with the model.

V0 therefore generates exactly one `tube_run` and zero connections. That solid is
the direct CAD equivalent of the 047 cylindrical approximation.

### Full-reactor linking is deferred, not approximated silently

A later topology-aware process/CAD slice may link a full reactor only after a
reviewed model defines at least:

- hydraulic path identity;
- parallel-path or tube-count semantics;
- allocation of aggregate length among straight runs, bends, manifolds, joints, and
  modules;
- illuminated versus dark path contributions;
- component-specific hydraulic and volume conventions;
- validation of topology against the calculation basis.

Until those quantities exist, 052 must not claim that a full reactor “draws itself”
from 047.

### `tube_count` is absent from 047

047 has no `tube_count` input or output. Counting CAD parts would not prove hydraulic
parallel-tube count, illuminated-path count, or manifold outlet semantics. V0 has no
tube-count field, assertion, inference, or topology mutation.

## Exact model/run authority

The source run is mandatory and must satisfy all of the following:

- `simulation_runs.status = succeeded`;
- exactly one associated `runner_jobs` row with `status = succeeded`;
- model version `implementation_kind = calc_v0`;
- model version is the server-registered bundled 047 identity, verified by the
  current accepted version label, script artifact SHA-256, and input-contract
  SHA-256; matching a caller-provided label alone is insufficient;
- the run is fresh under 051;
- its input payload passed the existing 047 exact-name, exact-unit, and domain
  checks;
- `tube_length`, `tube_inner_diameter`, and `tube_outer_diameter` each carry a
  non-empty `source_parameter_id` in the run input payload;
- those three IDs are distinct only when the canonical design uses distinct records;
  accidental reuse under incompatible names fails;
- the referenced Parameters belong to the same workspace, are `accepted`, are fresh,
  and still contain the exact value and unit executed by the run.

Temporary/manual scenario values without `source_parameter_id` are valid for 071
exploration but are not eligible to create canonical CAD lineage in 052.

The remaining six 047 inputs may be parameter-backed or temporary; they are recorded
in the run but do not drive the GeometrySpec.

## Fixed transformation contract

Transformation version:

```text
bluerev_047_m0_tube_proxy_v0_1
```

The transformation consumes only the exact run inputs:

- `tube_length`, unit `m`;
- `tube_inner_diameter`, unit `mm`;
- `tube_outer_diameter`, unit `mm`.

It computes:

```text
length_mm = tube_length * 1000
outer_d_mm = tube_outer_diameter
wall_t_mm = (tube_outer_diameter - tube_inner_diameter) / 2
```

The resolved GeometrySpec before canonical `spec_id` stamping is exactly:

```json
{
  "spec_version": "bluecad_geometry_spec_v0_1",
  "name": "bluerev_047_m0_tube_proxy",
  "parts": [
    {
      "part_id": "illuminated_tube_proxy",
      "kind": "tube_run",
      "params": {
        "outer_d": "<outer_d_mm>",
        "wall_t": "<wall_t_mm>",
        "length": "<length_mm>"
      }
    }
  ],
  "connections": []
}
```

The angle-bracket values above are finite JSON numbers, not strings, in the runtime
payload. No frame or `declared` block is added.

No caller-controlled manifest, part ID, part kind, target path, formula, expression,
name, connection, or topology field exists in V0.

## Numeric and dimensional rules

Use one strict decimal parser over the exact JSON numeric values preserved in the
successful run input payload. Booleans, NaN, Infinity, locale commas, embedded units,
expressions, and trailing text fail closed.

Allowed unit transformations are only:

- `m` → `mm` by exact factor `1000`;
- `mm` → `mm` identity.

The implementation must verify:

- `tube_length > 0`;
- `tube_inner_diameter > 0`;
- `tube_outer_diameter > tube_inner_diameter` for a non-zero wall;
- `wall_t_mm * 2 < outer_d_mm`;
- all transformed values are finite and representable by the existing GeometrySpec
  canonicalization path.

Decimal arithmetic is used for conversion and wall derivation before conversion to
finite JSON numbers. Preview returns decimal canonical text and final JSON numeric
values. The reconstructed inner diameter:

```text
outer_d_mm - 2 * wall_t_mm
```

must match the executed `tube_inner_diameter` within both:

- absolute error `<= 1e-9 mm`;
- relative error `<= 1e-12`.

## Cross-model reconciliation

A successful preview must prove that the resolved GeometrySpec reproduces the 047
M0 geometry basis, not merely that it is schema-valid.

Using deterministic analytic formulas over the resolved spec, preview reports:

```text
CAD_inner_diameter_mm = outer_d - 2 * wall_t
CAD_liquid_volume_m3 = pi * (CAD_inner_diameter_mm / 1000)^2 / 4 * (length / 1000)
CAD_external_area_m2 = pi * (outer_d / 1000) * (length / 1000)
```

These must match the successful run outputs:

- `tube_liquid_volume`;
- `external_illuminated_area_proxy`;

within the same tight tolerances used by the 047 verification tests or tighter
implementation-defined deterministic tolerances recorded in the response.

The preview also reconciles:

- GeometrySpec length against run `tube_length`;
- GeometrySpec inner and outer diameters against run inputs;
- manifest/build analytic volume when available against the same annular-wall solid
  convention, while clearly distinguishing solid material volume from liquid volume.

A mismatch fails preview with no writes. JSON validity or a passing CAD validator is
not proof of process-model equivalence.

## Authority and safety invariants

1. Only the three accepted, fresh source Parameters actually executed by the same
   successful 047 run drive geometry.
2. Preview is side-effect free, including no build-directory creation.
3. Execute is bound to one canonical preview digest and revalidates the entire run,
   model identity, parameter snapshot, and transformation version before writes.
4. No LLM or provider call occurs; preview and execute write zero `ai_jobs` rows.
5. No topology choice or mutation occurs.
6. No record, candidate, validation result, decision, or FEM result is promoted
   automatically.
7. A stale linked candidate remains inspectable immutable history; it is not
   overwritten, deleted, rebuilt, or silently marked current.
8. Existing GeometrySpec validation and deterministic build/export remain
   authoritative for CAD validity.
9. Existing mesh/FEM output remains advisory and never rewrites source Parameters or
   process outputs.
10. A deterministic CAD-LINK attempt is never represented as an AI proposal.
11. Reconciliation failure blocks execution even if GeometrySpec validation would
    otherwise pass.

## API surface

Add two endpoints:

```text
POST /workspaces/{workspace_id}/bluecad/cad-link/047/preview
POST /workspaces/{workspace_id}/bluecad/cad-link/047/execute
```

### Preview request

```json
{
  "source_simulation_run_id": "<required-run-id>",
  "analysis_spec": null
}
```

`analysis_spec` is optional and follows the existing 038 contract without geometry.
No other fields are accepted.

### Preview response

Preview returns at least:

- workspace and source simulation-run ID;
- source runner-job ID;
- model-version ID, version label, implementation kind, script SHA-256, and
  input-contract SHA-256;
- run and runner statuses;
- source snapshot for the three geometry Parameters, including refs, exact names,
  executed values, current canonical values, units, status, origin, freshness, and
  source refs;
- transformation version;
- converted/derived decimal values;
- canonical resolved GeometrySpec and `spec_id`;
- canonical resolved-spec digest;
- cross-model reconciliation values, tolerances, and pass/fail results;
- canonical analysis-contract digest when supplied;
- implementation/schema version identifiers;
- one `preview_digest` over every execution-relevant field.

Preview performs zero database, filesystem, artifact, event, candidate, attempt,
evidence, freshness, link, or AI writes.

## Execute request and TOCTOU boundary

Execute receives the same request plus the exact `preview_digest`.

Before any database write or directory creation, execute must reload and revalidate:

- workspace and source run;
- run and runner status;
- bundled 047 model identity and hashes;
- run freshness;
- exact input payload and three `source_parameter_id` bindings;
- current source Parameter values, units, statuses, origins, source refs, and
  freshness;
- transformation, schema, canonical spec, reconciliation, analysis contract, and
  all digests.

Any mismatch returns `409 cad_link_preview_stale` with zero writes and zero directory
creation.

## Idempotency and concurrency

The canonical `preview_digest` is the idempotency identity for execute.

- the link table has a uniqueness constraint on `(workspace_id, preview_digest)`;
- the first execute owns candidate creation for that digest;
- a repeated or concurrent execute returns the existing linked candidate and
  `replayed=true` after verifying the stored digests;
- no duplicate candidate, attempt, artifact, evidence, simulation, or AI row is
  created for the same preview;
- an inconsistent existing row fails closed with
  `cad_link_persistence_inconsistent`.

## Candidate, attempt, and artifact semantics

Add `process_linked` to `CandidateOrigin` and `cad_link_failed` to the parked-reason
contract.

A first successful execute creates one candidate with:

- `origin=process_linked`;
- `parent_candidate_id=NULL`;
- deterministic brief identifying the 047 M0 proxy and source run without embedding
  source values;
- `loop_config_json={}` as an explicit not-applicable legacy field; readers branch on
  `origin` and do not interpret it as AI-loop configuration;
- no `proposal_ai_job_id`.

Create one attempt with:

- `route_class=deterministic:cad_link:047`;
- `proposal_outcome=not_applicable`, added to the typed attempt contract;
- build outcome, validation verdict, and artifact references populated through the
  shared deterministic path;
- no prompt version or AI-provider metadata.

A resolved GeometrySpec that reaches build/validation but fails creates an
inspectable `parked(cad_link_failed)` candidate with report and link provenance.
Invalid source/run state or failed reconciliation creates no candidate.

Artifact registration must accept an explicit producer description. CAD-LINK
artifacts must not carry the current "Generated by BLUECAD AI loop v0" note or any
false AI claim.

## Additive persistence

Add one table, expected name `bluecad_cad_links`, with at least:

- id;
- workspace_id;
- source_simulation_run_id;
- source_runner_job_id;
- child_candidate_id, unique;
- transformation_version;
- canonical source_snapshot_json and digest;
- source_model_identity_json and digest;
- analysis_contract_digest when supplied;
- preview_digest;
- resolved_spec_digest;
- reconciliation_json and digest;
- created_at;
- unique `(workspace_id, preview_digest)`.

The snapshot is immutable audit evidence, not a second mutable Parameter store.
Runtime authority remains in canonical run, model, Parameter, candidate, artifact,
and evidence rows.

Use the next additive migration ID. Candidate, attempt, link, and final artifact/
evidence references must be persisted coherently. An unexpected persistence failure
must never leave a candidate marked `valid` without its link record. It must leave an
honest parked/failed state or roll back the database unit of work. Staged filesystem
output receives best-effort cleanup and is never exposed as a successful registered
artifact without committed metadata.

## Flowsheet and stale-propagation integration

Extend the existing 050 graph builder, not a second graph engine.

Existing 050 already derives dependency edges from the three parameter-backed run
inputs to the source simulation run. Add:

- source 047 `simulation_run:<id>` → child `bluecad_candidate:<id>` as
  `m0_geometry_link`, edge class `dependency`;
- for `origin=process_linked`, child candidate → deterministic attempt as
  `process_link_build`, edge class `dependency`;
- for `origin=process_linked`, child candidate → each current registered candidate
  artifact, including GLB, as `process_link_artifact`, edge class `dependency`;
- preserve existing attempt→artifact, candidate/attempt→simulation-run,
  report-artifact→evidence, and simulation-run→evidence dependency edges.

Do not globally change historical AI candidate provenance edge classes. Do not add a
new flowsheet node kind solely for the link row.

Replacing one of the three accepted source Parameters must allow 051 to mark stale,
with exact explainable paths:

```text
parameter -> source 047 simulation_run -> process-linked candidate
          -> deterministic attempt/artifact/optional analysis run/evidence
```

Tests must assert each supported dependency path and must not claim staleness for
nodes connected only through advisory provenance.

## Deterministic execution path

Reuse the existing:

- GeometrySpec canonicalization and validation;
- `build_geometry_spec` construction/export;
- artifact hashing and registration;
- validation evidence mapping;
- optional 038 mesh/FEM stage.

A small extraction from the AI loop into a shared deterministic helper is allowed
only to avoid duplicate build/simulation logic. Existing AI-loop behavior and tests
must remain unchanged. A second CAD builder, validation mapper, artifact store,
simulation engine, or evidence path is forbidden.

Same source-run/model/parameter snapshot + same transformation version + same
analysis contract + same implementation version must produce the same resolved
GeometrySpec and same-environment artifact digests.

## Error contract

Required bounded codes include at least:

- `cad_link_run_not_found`;
- `cad_link_run_not_succeeded`;
- `cad_link_run_stale`;
- `cad_link_runner_job_invalid`;
- `cad_link_model_identity_mismatch`;
- `cad_link_parameter_binding_missing`;
- `cad_link_parameter_not_found`;
- `cad_link_parameter_not_accepted`;
- `cad_link_parameter_stale`;
- `cad_link_parameter_snapshot_mismatch`;
- `cad_link_numeric_invalid`;
- `cad_link_unit_unsupported`;
- `cad_link_geometry_invalid`;
- `cad_link_reconciliation_failed`;
- `cad_link_preview_stale`;
- `cad_link_persistence_inconsistent`;
- `cad_link_persistence_failed`.

Expected response classes:

- `404` for absent workspace-scoped resources;
- `409` for stale/changed run, Parameter, preview, or inconsistent idempotency state;
- `422` for ineligible run/model/binding, unsupported units, invalid geometry domain,
  or reconciliation failure;
- `500` with a safe bounded code for unexpected infrastructure failure, never
  internal paths, source values, SQL text, or secrets.

## Files likely touched

Verify against current code before implementation and stop on conflict.

Expected bounded set:

- `backend/app/core/schema.py`;
- `backend/app/modules/bluecad/cad_link.py` (new);
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

1. Preview accepts only a fresh successful bundled-047 `calc_v0` run with successful
   runner job and parameter-backed geometry inputs.
2. Temporary/manual geometry bindings, wrong model identity, failed/stale runs, or
   changed source Parameters are rejected with zero writes.
3. The resolved spec contains exactly one `tube_run`, fixed part/name identity, zero
   connections, and no caller-controlled topology or manifest.
4. Length, outer diameter, and derived wall thickness reproduce the executed 047
   inputs within declared tolerances.
5. Deterministic reconciliation proves liquid volume and external-area proxy agree
   with the successful 047 outputs; disagreement blocks execution.
6. Preview has zero database/filesystem side effects and returns a digest covering
   run, model hashes, source snapshot, transformation, spec, reconciliation, and
   analysis contract.
7. Execute rechecks the exact preview before any write or directory creation.
8. First execute creates one `process_linked` candidate, one deterministic non-AI
   attempt, honest artifact metadata, one link record, and zero `ai_jobs` rows.
9. Repeated/concurrent execute for the same preview is idempotent and creates no
   duplicate rows or artifacts.
10. A GeometrySpec validation failure creates an inspectable
    `parked(cad_link_failed)` candidate with report and provenance.
11. Optional mesh/FEM reuses 038, records typed evidence, and cannot promote or
    rewrite process Parameters or outputs.
12. Replacing one source Parameter stales the source run and every dependency-
    reachable linked CAD/build/simulation/evidence node with explainable paths.
13. Historical AI candidate edge semantics and AI-loop behavior remain unchanged.
14. Persistence failure cannot expose a valid unlinked candidate or a successful
    registered artifact with false/missing producer provenance.
15. No full-reactor topology claim, tube-count semantics, UI, optimizer, inverse
    solver, generic units engine, provider call, automatic recompute, or automatic
    promotion is added.

## Required tests

Offline tests must cover at least:

- successful 047 run fixture with all three parameter-backed geometry inputs;
- failed, queued, running, timed-out, and stale run rejection;
- wrong model version/label/script hash/input-contract hash;
- missing, temporary, cross-workspace, non-accepted, stale, or changed source
  Parameters;
- exact fixed GeometrySpec shape and canonical digest;
- strict decimal conversion and wall derivation edge cases;
- liquid-volume and external-area reconciliation pass/fail;
- preview zero-write and zero-directory assertion;
- preview/execute TOCTOU rejection before writes;
- successful child build, honest candidate/attempt/artifact provenance, and zero
  `ai_jobs` rows;
- idempotent replay and concurrent execute race;
- validation-failed parked child;
- coherent persistence-failure behavior;
- identical resolved-spec/artifact digests for identical previews;
- optional mesh/FEM evidence using existing offline fixtures/fakes;
- exact flowsheet dependency and 051 stale paths;
- proof that historical AI provenance edges are unchanged;
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

- No full-reactor or multi-part process-to-CAD mapping.
- No tube-count or parallel-path semantics.
- No caller-defined binding manifest or expression language.
- No topology synthesis, connection editing, or path discovery.
- No UI, slider panel, comparison surface, or workspace redesign.
- No optimizer, target solver, inverse calculation, sensitivity sweep, or automatic
  scenario selection.
- No automatic recomputation after an upstream change.
- No automatic promotion of Parameters, candidates, decisions, or solver evidence.
- No general-purpose unit-conversion framework.
- No new process formulas, embedded design defaults, or change to 047 validity
  domains.
- No direct provider/model call or AI repair of failed linked geometry.
- No broad BLUECAD ledger, artifact, flowsheet, or runner refactor.

## Definition of done

The spec is implemented as one reviewable slice, all acceptance criteria and offline
gates pass, `STATUS.md` points to the implementation PR while in review,
implementation notes disclose runtime conflicts, and the maintainer—not the
implementing agent—decides whether to merge.
