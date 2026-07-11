# 056 — BLUECAD property-based geometry testing + determinism canary

Status: ready after definition reconciliation
Depends on: 005 (CAD adapter MVP)

Contextual foundations, not hard dependencies: 007 supplies repository CI/tool
boundary discipline, while 010 supplies candidate-ledger fixtures that this pure
adapter slice does not call. This slice does **not** depend on 021, 024, 038, any
solver, any AI route, or the candidate repair loop.

## Goal

Add a permanent offline regression net for the BLUECAD CAD adapter that catches:

1. **Valid-domain robustness failures.** Generate bounded GeometrySpecs that are
   valid by construction and require every one to complete the real
   `build_geometry_spec` path with verdict `pass`. `SPEC_INVALID`,
   `PORT_MISMATCH`, `KERNEL_ERROR`, `EXPORT_ERROR`, `TIMEOUT`, a crash, a hang,
   or an empty artifact is a test failure. Invalid and adversarial payloads remain
   owned by 023.
2. **Semantic and full-manifest determinism drift.** Rebuild fixed and generated
   specs in fresh output roots, recompute each manifest digest from the canonical
   payload, and detect unexpected changes. Cross-platform semantic invariants and
   the canonical full-artifact digest canary are separate contracts; the latter
   runs only on an explicitly identified Linux profile.

The slice measures CAD-kernel robustness and repeatability. It does not add a new
builder, claim engineering physics, or certify generated geometry.

## Current runtime facts that bind this definition

- The public adapter entry point is `build_geometry_spec`; tests must not call
  builders or exporter internals as a substitute for the real path.
- A successful build exports `model.step`, `model.stl`, `model.glb`,
  `manifest.json`, and `validation_report.json`.
- The public `manifest_digest` covers the complete manifest payload, including
  STEP/STL/GLB hashes and the recorded build123d version. It is therefore a
  dependency and export-format canary, not a portable geometry-only digest.
- Manifest part volumes and bounding boxes are deterministic analytic metadata
  produced by the builders. Actual kernel validity/manifold evidence is exposed
  separately under `assembly.kernel_checks`. Tests must not misrepresent the
  analytic volume as a direct BREP-volume measurement.
- Assembly placement is currently planar: a frame direction determines a Z-axis
  rotation from its XY components. Phase 1 therefore generates only planar unit
  frame directions.
- The repository has `backend/requirements-dev.txt`; Hypothesis is a development
  dependency and must not be added to runtime `requirements.txt`.

## Scope

In scope:

- Add the exact development dependency `hypothesis==6.156.6` to
  `backend/requirements-dev.txt`.
- Add deterministic, bounded property tests for the three Phase 1 families below.
- Add same-environment repeatability tests through two fresh build roots.
- Add a checked-in full-manifest digest canary for one canonical Linux profile.
- Reuse existing BLUECAD fixtures where they already express the required cases.
- Add one small fixed float fixture if no stable non-tube fixture exists.
- Keep generated geometry in pytest temporary directories only.
- Run all tests offline with no provider, network, Gmsh, CalculiX, runner, or
  candidate-loop call.

Out of scope:

- Invalid/adversarial JSON, resource exhaustion, malicious paths, and crash fuzzing
  outside the valid domain; those belong to 023.
- New part kinds, builder refactors, vocabulary promotion, L2 scripts, AI repair,
  mesh/FEM, CFD, modal, thermal, or nonlinear analysis.
- A universal digest shared across operating systems, architectures, Python
  versions, OCCT wheels, or exporter versions.
- Snapshotting generated STEP/STL/GLB files in Git.
- Automatically regenerating expected digests.
- Treating analytic manifest volume/bbox metadata as independent BREP
  metrology.
- Broad random generation for bend, joint, manifold, anchor_mount, or
  harvest_module in Phase 1.

A property test exposing a real adapter defect may justify a narrow production
fix in the implementation PR. The test, minimized failing example, root cause,
and fix must remain visible; do not filter the example or weaken the invariant.

## Hypothesis profile and execution budget

The implementation must register one explicit profile named
`bluecad_property_ci` with:

```python
settings(
    derandomize=True,
    database=None,
    deadline=None,
    print_blob=True,
    suppress_health_check=[HealthCheck.too_slow],
)
```

Only `HealthCheck.too_slow` may be suppressed. Do not suppress filtering,
large-base-example, data-too-large, or function-scoped-fixture warnings to hide a
poor strategy.

Each test sets its own exact `max_examples`:

- single tube invariant test: 8 examples;
- compatible two-tube assembly invariant test: 6 examples;
- single float invariant test: 6 examples;
- repeatability test: 3 examples from each family, each built twice.

This is 38 full adapter builds before the fixed canary fixtures. The canary uses
four fixtures and builds each twice, for a maximum Phase 1 total of 46 full
builds. The implementation must record the observed wall time on the canonical CI
profile. The property module plus canary must complete within 240 seconds on
GitHub `ubuntu-24.04`; exceeding that is a blocker requiring an explicit
definition amendment, not silent example reduction or a disabled test.

Strategies must construct valid values directly. Broad `.filter()` calls and
post-generation rejection are forbidden. `assume()` is permitted only for a
small, documented relation that cannot be expressed compositionally and must not
trigger Hypothesis filtering health checks.

## Phase 1 generator contract

All generated IDs are short deterministic ASCII identifiers. All dimensions are
millimetres. Numeric dimensions are integers in Phase 1 to reduce irrelevant
floating-point shrinking noise.

### Family A — one `tube_run`

Generate:

- `outer_d`: integer 20–500;
- `wall_t`: integer 1–25 and strictly `< outer_d / 4`;
- `length`: integer 50–5000;
- optional frame origin: integer vector with each coordinate in
  `[-10_000, 10_000]`;
- optional frame direction selected from the four planar unit vectors
  `(±1, 0, 0)` and `(0, ±1, 0)`.

The strategy must build wall thickness conditionally from `outer_d`; it must not
sample an invalid wall and filter it later.

### Family B — two connected `tube_run` parts

Generate two tubes with:

- one shared `outer_d` and `wall_t` from Family A;
- independent integer lengths 50–2500;
- first-part optional planar frame from Family A;
- connection exactly `tube_a.port_b` → `tube_b.port_a`.

The second part is placed by the real assembly code. Do not add a competing frame
to the second part or reproduce placement math in the strategy.

### Family C — one `float`

Generate:

- `outer_d`: integer 50–500;
- `length`: integer 100–5000;
- `n_mounts`: integer 1–6;
- `pad_d`: integer 10 through `max(10, floor(outer_d / 2))`;
- optional planar frame from Family A.

This is the required non-tube family. Bend remains represented by fixed canary
fixtures but is intentionally excluded from random Phase 1 generation because
its valid kernel domain requires a separate geometric constraint amendment.

## Invariants for every generated build

Every generated spec is labelled valid and must satisfy all of the following:

1. `build_geometry_spec` returns verdict `pass`, no errors, a manifest object, and
   a validation report with verdict `pass`.
2. The five expected files exist, are regular files, are non-empty, and resolve
   beneath the pytest-owned build root. Symlink/path escape is forbidden.
3. `manifest.json` parses to the same object returned by the adapter.
4. `spec_id` equals the result spec ID and is identical for the same canonical
   input across fresh builds.
5. Recompute `manifest_digest` exactly by removing only the
   `manifest_digest` field and hashing the repository `canonical_json` encoding.
   The stored and recomputed values must match.
6. Every part has a finite positive analytic `volume_mm3`; finite bbox min/max;
   `min <= max` on every axis; and a strictly positive bbox envelope volume.
7. For the Phase 1 tube and float families, analytic volume must be no greater
   than bbox envelope volume times `1 + 1e-9`. This invariant is not generalized
   to excluded kinds.
8. Every `assembly.kernel_checks` entry reports `brep_valid is True` and
   `manifold is True`.
9. Every resolved port origin/direction value is finite. Direction norm must be
   within `1e-8` of one; no zero direction is accepted.
10. For Family B, connected port origins are componentwise coincident within the
    existing `assembly.ABS_TOL`, and directions are componentwise opposed within
    the same tolerance. Tests may import the existing tolerance constant but must
    not invent a second connection tolerance.
11. No manifest string contains the pytest temp-root path. No manifest field may
    introduce a wall-clock timestamp or absolute artifact path.
12. The generated output root contains no unexpected file outside the five
    adapter artifacts.

A strategy-valid spec rejected by schema or assembly is a failing example. The
implementation may correct the strategy only when it violated this frozen
contract; otherwise it must report and fix the adapter defect or stop.

## Generated repeatability contract

For three generated examples from each Phase 1 family:

1. Build the identical spec in two fresh sibling output roots.
2. Require identical canonical spec ID.
3. Require exact equality of the complete parsed manifests, including artifact
   hashes, tool metadata, and `manifest_digest`, within the same process and
   environment.
4. Require exact equality of STEP, STL, and GLB SHA-256 values recorded in both
   manifests.
5. Recompute both digests independently and require each to be valid.

Do not assert that every pair of different specs must have different digests;
that is not needed to prove determinism and turns this suite into a collision
claim.

## Canonical determinism canary

### Fixture set

Use exactly four checked-in JSON specs:

1. existing `minimal_single_tube.json`;
2. existing `chain_tube_bend_joint.json`;
3. existing `u_shape_two_bends.json`;
4. one new minimal single-float spec.

Do not commit generated CAD binaries. The expected metadata file stores only:

- schema version for the expected file;
- canonical profile ID;
- Python major/minor;
- operating system and architecture;
- resolved `build123d` version;
- resolved `cadquery-ocp` distribution version, or the exact installed
  distribution name if metadata uses another canonical name;
- fixture spec path;
- expected `spec_id`;
- expected full `manifest_digest`.

### Canonical profile

The full canary runs in a dedicated normal-CI job using:

- GitHub runner `ubuntu-24.04`;
- CPython 3.11;
- repository `requirements.txt` and `requirements-dev.txt`;
- environment marker `JARVISOS_BLUECAD_CANARY_PROFILE=ubuntu24-py311`.

The job must verify the expected profile metadata before comparing digests. A
Python/build123d/OCP/OS/architecture mismatch fails with a structured diagnostic;
it must not silently skip in canonical CI.

Developer runs outside that exact profile may run the portable property suite and
same-environment repeatability tests. The full checked-in digest canary must emit
an explicit skip explaining the profile mismatch. It must not compare a Linux
binary-artifact digest on an unsupported platform.

A transitive OCCT/OCP resolution change is intentionally visible: the profile or
digest comparison fails until a maintainer reviews the dependency change. 056
does not automatically add a new runtime OCP pin. Pinning a transitive runtime
dependency requires explicit compatibility evidence and a conscious dependency
change.

### Canary procedure

For each fixture:

1. Build twice in fresh temporary directories.
2. Apply all generated-build invariants relevant to that fixed kind.
3. Require the two complete manifests and all three artifact hashes to match.
4. Compare `spec_id` and full `manifest_digest` with the expected metadata.
5. On failure, report fixture name, profile mismatch if any, expected and actual
   spec ID/digest, build123d/OCP versions, and the three expected/actual artifact
   hashes where available.

There is no `--update`, auto-refresh, CI write-back, or fixture-regeneration
command in this slice. Expected metadata is edited only in a reviewed PR whose
body explains the intentional builder, exporter, kernel, or dependency change
and includes the previous and new values.

## Files expected in the implementation PR

Verify paths against `master` before implementation:

- `backend/requirements-dev.txt` — exact Hypothesis pin;
- `backend/pytest.ini` or `backend/pyproject.toml` only if profile registration
  requires configuration; reuse `bluecad_kernel`, do not add an unnecessary
  marker;
- `backend/tests/bluecad/test_geometry_property_invariants.py`;
- `backend/tests/bluecad/test_manifest_determinism_canary.py`;
- `backend/tests/bluecad/fixtures/property_geometry/minimal_float.json`;
- `backend/tests/bluecad/fixtures/property_geometry/expected.json`;
- `.github/workflows/ci.yml` — dedicated canonical canary job;
- this spec, with implementation notes appended;
- one implementation report under `reports/056-*`.

Production CAD files may change only if a minimized property failure proves a
real defect. Such files are not pre-authorized by this definition and must be
called out separately in the PR.

## Acceptance criteria

From `backend/`:

- `python -m pytest -q tests/bluecad/test_geometry_property_invariants.py` passes;
- portable property tests pass on developer platforms with build123d available;
- same-environment repeatability passes;
- canonical Linux digest canary passes in the dedicated job;
- normal backend pytest and Ruff remain green;
- canonical property + canary wall time is at most 240 seconds;
- no generated CAD binary is committed;
- no network/provider/Gmsh/CalculiX/AI/runner call occurs;
- no output escapes pytest temp roots;
- expected digest metadata contains no temp path, timestamp, secret, or generated
  binary content.

The implementation appends `## Implementation notes` to this spec with:

- exact Hypothesis version and profile settings;
- observed example/build counts and canonical wall time;
- fixture/profile metadata path;
- resolved build123d/OCP versions;
- covered and deliberately excluded kinds;
- any production defect found and its minimized reproducer;
- old/new canary values for every intentional baseline update.

## Stop conditions

Stop and amend the definition rather than weakening tests when:

- the 46-build bound cannot complete within 240 seconds on canonical CI;
- a Phase 1 family cannot be generated validly without broad filtering;
- full manifests are not repeatable in the same canonical environment after STEP
  timestamp normalization;
- an exporter embeds additional uncontrolled time, randomness, machine path, or
  process-order state;
- the actual OCP distribution cannot be identified reliably for profile binding;
- a builder's analytic bbox cannot conservatively contain its analytic volume for
  a covered Phase 1 kind;
- the required connected-port evidence is absent from the manifest;
- a valid minimized example crashes/hangs the kernel or writes outside its root;
- implementation would need new part kinds, schema mutation, a broad builder
  refactor, or solver/provider calls.

## Non-goal handoff

- Invalid/adversarial and resource-exhaustion probes → 023.
- End-to-end alpha execution and data recovery → 021/021b.
- FEM analytic verification → completed 024.
- Human-gated vocabulary extension → 033.
- Parametric user-facing variants → 006b.

## Implementation notes

- Development dependency: `hypothesis==6.156.6` in
  `backend/requirements-dev.txt` only.
- Loaded profile: `bluecad_property_ci` with `derandomize=True`, `database=None`,
  `deadline=None`, `print_blob=True`, and only `HealthCheck.too_slow` suppressed.
- Generated invariant coverage is 8 single-tube examples, 6 compatible two-tube
  assemblies, and 6 single-float examples: 20 full adapter builds.
- Generated repeatability coverage is 3 examples per family, each built twice: 18
  full adapter builds. Four fixed canary fixtures are each built twice: 8 builds.
  Total canonical bound: 46 full `build_geometry_spec` executions.
- The reviewed bootstrap run completed the property module and canary in 132.24
  seconds on the canonical runner, below the 240-second ceiling.
- Canonical metadata is stored at
  `backend/tests/bluecad/fixtures/property_geometry/expected.json`. It was moved
  beneath the dedicated subdirectory because the historical golden-fixture test
  treats every JSON file directly under `fixtures/` as a GeometrySpec.
- Canonical profile: Ubuntu 24.04, CPython 3.11, x86_64, build123d 0.11.1,
  `cadquery-ocp-novtk` 7.9.3.1.1.
- Random Phase 1 coverage includes `tube_run`, compatible connected `tube_run`
  assemblies, and `float`. Bend is represented by fixed canaries. Joint,
  manifold, anchor_mount, and harvest_module remain deliberately excluded from
  random generation under this definition.
- No production CAD defect was found and no production CAD file changed. The
  implementation exposed only a test-fixture discovery collision; the correction
  isolated canary metadata without weakening any invariant or changing a digest.
- This is the initial reviewed baseline, so every previous value was `TBD`. The
  accepted fixture bindings are:
  - `minimal_single_tube.json`: spec ID
    `sha256:bd04044e65c001b9911ce7adbc5e18b64618b0002f2fa25af5f34c1912a05050`,
    manifest digest
    `19b5f925b8d9fd2a3b837177958a68abf3256fba3d5bb44c31253603dd0729f4`;
  - `chain_tube_bend_joint.json`: spec ID
    `sha256:155ec1b90a0cbe47c6ce0821360f838504695057f8a1bc0b1cf9a67b2851367f`,
    manifest digest
    `88b0d778047f662d38fb4ee91440c05ae160bacc59e7c570c9a99dc22d3f87cd`;
  - `u_shape_two_bends.json`: spec ID
    `sha256:5178bfeb841266749e2df7bec3fa777a27a236d31e2e9b232ee6b8944869e14f`,
    manifest digest
    `73d951bb102e93d45392dc8defc3b580cdd932773b878f2a6aab5cc306e217db`;
  - `property_geometry/minimal_float.json`: spec ID
    `sha256:7631c98b0cb478cc1a879200a577ef140c63d887c484bfbf65efaff7951b51b9`,
    manifest digest
    `cd5ab4daca78410797c8e12451263eae7e31e17f175899c5712c3bc4eefa0230`.
