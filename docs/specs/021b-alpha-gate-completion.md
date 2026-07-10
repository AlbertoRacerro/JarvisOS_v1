# 021b — ALPHA-GATE completion: real-tool proof + recoverable data root

Status: ready. `docs/specs/STATUS.md` is authoritative.

Depends on: 021, 038, 044.

## Goal

Close the remaining alpha-readiness gap without expanding runtime authority:

1. prove that the existing BLUECAD entry point can execute the real CAD → mesh →
   static-FEM path with pinned tools, no live AI provider, complete artifacts, and
   linked evidence;
2. provide a deterministic local backup/restore path for the minimum canonical
   JarvisOS data root, including path rebasing when restored elsewhere.

These are independent failure domains and MUST be implemented as two sequential,
independently reviewable PRs under the same spec:

- **021b-A — strict real-tool alpha proof**;
- **021b-B — atomic backup/restore with relocation verification**.

Do not combine both implementation slices into one PR.

## Runtime facts frozen by this spec

The implementation must preserve the current merged behavior rather than inventing
parallel contracts:

- `create_bluecad_candidate(...)` is the real BLUECAD entry point.
- Candidate build artifacts use roles `bluecad_spec`, `bluecad_report`,
  `bluecad_manifest`, and optionally `bluecad_glb`.
- Mesh and FEM JSON reports are registered as `bluecad_sim_report`; they are
  distinguished by filename/source reference and by linked evidence kind.
- Evidence kinds are `validation_v0`, `mesh_quality_v0`, and `fem_static_v0`.
- Mesh/FEM evidence must carry `candidate_id`, `attempt_id`, `source_run_id`, and
  `report_artifact_id`.
- A valid geometry candidate remains `valid` even when the advisory simulation
  stage fails.
- `simulation_runs.status == "completed"` means the advisory stage reached a
  terminal recorded result; mesh/FEM truth remains in `output_payload` verdicts.
- `simulation_runs.status == "failed"` is reserved for simulation-stage
  persistence failure in the current runtime.
- The default tool registry keeps Gmsh and CalculiX disabled. A normal CI skip is
  not evidence that the alpha proof passed.
- Canonical data currently spans the SQLite database plus `workspaces/` and
  `artifacts/`. `logs/` is operational output and is not required for minimum
  restore acceptance.
- The database stores root-bound absolute paths, including `artifacts.stored_path`,
  runner-job paths, and BLUECAD geometry paths inside simulation payloads.

## Authority and safety boundaries

- No live AI provider call.
- The scripted BLUECAD adapter is allowed only through caller-injected bindings
  with `requires_network=False`.
- No automatic candidate promotion or decision creation.
- No request-controlled tool-registry path.
- Tool-registry override, if added, must be server/operator-owned configuration.
- Gmsh and CalculiX remain subprocess integrations behind the existing registry,
  hash validation, minimal environment, timeout, and license boundary.
- Restore never overwrites a non-empty target by default.
- A partial, interrupted, unverifiable, or concurrently mutated snapshot must not
  be represented as complete.

# 021b-A — strict real-tool alpha proof

## Problem

`test_real_solver_marker_documents_full_chain` already exercises the merged loop,
but it skips when the kernel or registry-enabled tools are absent. That is useful
for ordinary CI compatibility, but a skipped test cannot close the alpha gate.
The default registry is also machine-specific and disabled, so proof execution
needs an explicit operator-owned registry without editing the checked-in config.

## Required implementation

### 1. Operator-owned registry selection

Add one server-side registry-path override with this precedence:

1. explicit function argument already accepted by registry/adapter functions;
2. environment variable `JARVISOS_BLUECAD_TOOL_REGISTRY`;
3. existing checked-in `configs/bluecad_tools.yaml`.

Requirements:

- blank values are rejected or treated as absent consistently;
- request payloads and model output cannot set the path;
- every registry load, resolve, health check, mesh call, and FEM call uses the
  same resolved path;
- existing explicit `registry_path=` tests remain authoritative and unchanged in
  meaning;
- no binary is downloaded or trusted by JarvisOS at runtime.

### 2. Strict proof mode

Strengthen or replace the existing real-solver integration test with a dedicated
manual proof command, for example:

```text
cd backend
python -m pytest -q tests/bluecad/test_alpha_real_tools.py \
  --require-bluecad-real-tools
```

Exact filename/option spelling may differ, but the following semantics are binding:

- ordinary CI may skip the test when real tools are unavailable;
- strict mode must convert missing `build123d`, disabled tools, missing binaries,
  hash mismatch, failed health check, or unsupported registry configuration into
  a test failure, never a skip;
- the command must exit nonzero unless the full proof passes;
- the proof must use a temporary `JARVISOS_DATA_ROOT` and must not touch the
  operator's normal data root;
- no network provider adapter may be constructed or called.

### 3. Full-chain assertions

Using one deterministic single-tube fixture and a valid static AnalysisSpec, run
`create_bluecad_candidate(...)` twice with equivalent inputs and assert:

- both candidates are `valid`;
- each has exactly one successful BLUECAD attempt;
- validation verdict is `pass`;
- Gmsh returned zero and created a non-empty `mesh.inp` with nodes, volume
  elements, and all required physical groups;
- CalculiX returned zero, reports the registry version pin rather than `fake`, and
  produces finite non-negative displacement and von-Mises maxima;
- each simulation run is terminal with `status == "completed"`,
  `mesh_verdict == "pass"`, and `fem_verdict == "pass"`;
- each candidate has `validation_v0`, `mesh_quality_v0`, and `fem_static_v0`
  evidence linked to its candidate/attempt identity;
- mesh/FEM evidence has non-null source-run and report-artifact links;
- registered `bluecad_spec`, `bluecad_report`, `bluecad_manifest`, `bluecad_glb`,
  and both `bluecad_sim_report` rows point to existing files whose SHA-256 matches
  the database value;
- the two canonical manifest files have the same SHA-256;
- the proof records the resolved Gmsh and CalculiX entrypoints, version pins, and
  binary SHA-256 values in test output or a bounded proof JSON artifact.

A candidate becoming `valid` is insufficient by itself. Any mesh, FEM, evidence,
artifact, digest, or real-tool assertion failure fails strict proof mode.

### 4. Documentation

Add a short operator runbook covering:

- preparing an external registry with exact entrypoints and hashes;
- running registry health checks;
- invoking ordinary skip-capable tests versus strict proof mode;
- interpreting failure versus skip;
- the fact that this proves integration/determinism, not FEM accuracy.

## Required 021b-A tests

At minimum:

1. registry env override is used when no explicit argument is supplied;
2. explicit argument wins over the env override;
3. request/model-shaped data cannot select a registry;
4. ordinary mode skips when tools are unavailable;
5. strict mode fails rather than skips when tools are unavailable;
6. strict full-chain proof with real tools and two-run manifest equality;
7. offline adapter assertion: zero network/provider path;
8. existing registry hash-mismatch and license-boundary tests remain green.

## 021b-A non-goals

- No analytic FEM accuracy claim; spec 024 owns that.
- No checked-in machine-specific binary path or hash.
- No long-lived golden manifest digest; spec 056 owns the canary.
- No automatic installation of GPL tools in the application runtime.
- No default enabling of Gmsh or CalculiX.
- No change to candidate promotion semantics.

# 021b-B — atomic backup/restore with relocation verification

## Problem

A raw copy of the live SQLite file is unsafe under WAL, and copying only the
artifact directory is incomplete. Restoring to another root without rewriting
absolute paths creates a database that appears populated but cannot open its
artifacts, runner files, or BLUECAD simulation geometry.

## Required CLI

Add one plain-Python CLI under `scripts/` with three explicit operations:

```text
python scripts/jarvisos_data_root.py snapshot ...
python scripts/jarvisos_data_root.py verify ...
python scripts/jarvisos_data_root.py restore ...
```

Exact command/file naming may differ, but all behavior below is binding.

### Snapshot creation

- Source root defaults through current JarvisOS settings but may be supplied
  explicitly by the operator.
- Destination must be outside the source data root.
- Create into a sibling temporary directory such as `.partial-<snapshot-id>`.
- Hold one source SQLite connection open for the operation.
- Create the database image with `sqlite3.Connection.backup(...)`; never copy the
  live database file, WAL, or SHM directly.
- Copy `workspaces/` and `artifacts/` without following symlinks.
- Reject any source symlink, path escape, unreadable file, duplicate relative
  path, unsupported special file, or destination nested inside source.
- Detect concurrent mutation by checking both:
  - SQLite `PRAGMA data_version` before and after file copying on the held source
    connection;
  - deterministic source file inventory before and after copying.
- If either changes, delete/leave only an explicitly incomplete partial directory
  and return nonzero.
- Run `PRAGMA integrity_check` on the snapshot database.
- Write `manifest.json` containing at least:
  - schema version and snapshot id;
  - UTC creation time;
  - source-root identity used for later rebasing;
  - database filename and current schema migration id;
  - table row counts;
  - every included relative path, byte size, and SHA-256;
  - excluded roots (`logs/` at minimum);
  - completion state.
- Write the completion marker last, then atomically rename the partial directory
  to its final snapshot name.
- Implement keep-last-N rotation only after a new snapshot is verified complete.
- Never delete partial/unverified snapshots as part of retention accounting.

### Snapshot verification

`verify` must return nonzero when:

- the completion marker or manifest is absent;
- the manifest schema is unsupported;
- a listed file is missing, extra where forbidden, wrong-sized, or hash-mismatched;
- SQLite integrity check fails;
- schema migration metadata or row counts differ from the manifest;
- any stored path escapes the snapshot's expected relative roots.

### Restore

- Restore into a new/empty target root by default.
- Existing non-empty targets require an explicit destructive flag; that flag must
  be separately tested and must never delete the source snapshot.
- Restore through a target sibling partial directory and atomically rename only
  after all checks pass.
- Copy the snapshot database, `workspaces/`, and `artifacts/`.
- Transactionally rebase every canonical root-bound path from the manifest's
  source root to the new target root.
- The minimum path-rebase allowlist is:
  - `artifacts.stored_path`;
  - `runner_jobs.script_path`;
  - `runner_jobs.working_dir`;
  - `runner_jobs.input_file` when non-null;
  - `runner_jobs.output_dir`;
  - BLUECAD `simulation_runs.parameter_payload.geometry.step_path`;
  - BLUECAD `simulation_runs.parameter_payload.geometry.manifest_path`.
- Inspect runner `command_json` and `environment_json` metadata. If they contain
  source-root absolute paths, either rebase documented path fields or fail restore;
  do not silently leave stale paths.
- After rebasing, scan canonical path columns/payloads for the old source-root
  prefix. Any remaining canonical occurrence fails restore.
- Re-run SQLite integrity and foreign-key checks.
- Point the application at the restored root in the test process, clear cached
  settings, and prove normal read paths can open every registered artifact.

## Required 021b-B tests

All backup tests run in normal offline CI and use temporary roots.

1. snapshot uses SQLite backup API and succeeds with WAL enabled;
2. database rows plus workspace/artifact files round-trip to a different root;
3. all registered artifact hashes match after restore;
4. BLUECAD geometry payload paths are rebased and readable;
5. runner script/working/input/output paths are rebased and pass existing path
   validators;
6. old source-root prefixes are absent from canonical path fields after restore;
7. SQLite integrity and foreign-key checks pass;
8. source file mutation during snapshot fails closed;
9. source database mutation during snapshot fails closed;
10. symlink/path-escape/special-file inputs fail closed;
11. interrupted partial snapshot is rejected by verify and restore;
12. corrupted database/file/manifest hash is rejected;
13. non-empty restore target is refused without explicit destructive approval;
14. keep-last-N removes only oldest complete verified snapshots;
15. snapshot destination inside the source root is rejected;
16. no source data, snapshot, or existing target is deleted on failed restore.

## 021b-B non-goals

- No cloud/off-site backup transport.
- No encryption/key-management system in this slice.
- No scheduler daemon, background service, or UI.
- No hot backup guarantee under continuous writes; the operation detects mutation
  and fails rather than claiming consistency.
- No generic database migration or portable export format.
- No backup of secrets outside the canonical data root.
- No claim of disaster recovery until a restore test passes.

## Files likely touched

021b-A may touch:

- `backend/app/modules/bluecad/registry.py`;
- `backend/app/modules/bluecad/mesh_adapter.py` and
  `backend/app/modules/bluecad/fem_adapter.py` only if registry-path propagation is
  currently incomplete;
- one dedicated real-tool test file and pytest option/fixture support;
- a BLUECAD alpha-proof runbook.

021b-B may touch:

- one new script under `scripts/`;
- focused backup/restore tests;
- a local backup/restore runbook.

`backend/app/modules/bluecad/loop.py`, provider policy, UI, schema, and production
routes should remain unchanged unless a concrete test proves a minimal change is
required.

## Acceptance criteria

Spec 021b is complete only when both implementation PRs are merged and:

1. strict real-tool mode cannot pass or skip without executing hash-verified Gmsh
   and CalculiX;
2. the real entry point produces complete linked artifacts/evidence twice with an
   identical canonical manifest digest;
3. no live provider/network path is used;
4. normal CI remains offline and deterministic;
5. snapshot creation is atomic, mutation-detecting, and SQLite-backup based;
6. restore to a different root rebases all canonical paths and opens every
   registered artifact;
7. corrupt, partial, concurrent, escaping, and destructive-default cases fail
   closed;
8. operator documentation distinguishes integration proof, FEM verification,
   determinism canary, backup creation, and proven restore.

## Definition of done

- 021b-A and 021b-B are separate reviewed implementation PRs.
- Focused tests and the complete backend suite pass for each slice.
- Ruff passes.
- No conformance tests are weakened or deleted.
- No live provider call, secret, machine-specific binary path, or snapshot data is
  committed.
- `docs/specs/STATUS.md` records both implementation PRs and marks 021b `merged`
  only after the second PR merges.
