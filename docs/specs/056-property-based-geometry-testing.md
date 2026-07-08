# 056 — BLUECAD property-based geometry testing + determinism canary

Status: ready (drafted 2026-07-08 after registry repair; implements quality
program item 056)
Depends on: 005 (CAD adapter MVP), 007 (tool registry / CI discipline), and
010 (candidate/attempt ledger fixtures are useful but not required for the
pure adapter tests). Does **not** depend on 021, 024, 038, or any solver.

## Goal

Add a permanent regression net for BLUECAD geometry that catches two classes of
failure the existing golden fixtures do not cover:

1. **Property-based geometry invariants**: generate many random but valid
   `GeometrySpec` inputs inside bounded engineering ranges and assert that the
   CAD adapter builds a valid artifact set with sane geometry metrics. A
   generated input labelled valid must not be accepted as a structured
   rejection: if it fails with `SPEC_INVALID`, `PORT_MISMATCH`, or any other
   structured validation error, the test fails. Intentionally invalid or
   adversarial specs belong to item 023. The property suite must never crash,
   hang, write outside its temp output root, or silently produce physically
   impossible manifest values.
2. **Manifest determinism canary**: rebuild a small checked-in golden fixture
   set and compare each `manifest_digest` to a checked-in expected digest. This
   is the dependency-drift alarm for build123d/OCP pins and builder changes.

The slice turns "the geometry kernel seems stable" into a measurable test
contract.

## Why

`PROGRAM_BACKLOG.md` item 056 names this as the quality-program slice for
random valid GeometrySpecs plus a determinism canary. The old registry slot 022
is now occupied by Codex PR autopush, so this spec owns the quality work under
056. The important distinction from 021 and 024:

- 021 runs one end-to-end alpha gate and compares two live manifests from the
  same process; it explicitly does **not** check a golden digest across
  dependency bumps.
- 024 verifies FEM physics against analytic benchmark cases; it is a fixed
  solver-verification ladder, not a GeometrySpec generator.
- 056 is CAD-kernel robustness and deterministic-manifest drift detection.

## Scope

In scope:

- Add `hypothesis` as a test dependency, pinned in the backend dependency set
  according to the repository's existing dependency discipline.
- Add property-based tests for valid bounded `GeometrySpec` JSON objects.
- Add a deterministic golden-fixture manifest canary.
- Keep all tests offline: no AI provider calls, no network, no gmsh, no ccx.
- Run under normal backend pytest unless the implementation proves the build123d
  runtime is too slow; in that case mark the property suite with a dedicated
  pytest marker and include it in CI explicitly.
- Keep generated CAD artifacts in pytest temp directories only.

Out of scope:

- No solver tests, mesh tests, FEM tolerances, or `AnalysisSpec` assertions.
- No L2 script execution or AST runner changes.
- No new part kinds or vocabulary promotion flow.
- No mutation of trusted builders by AI.
- No live provider calls and no use of the 010 repair loop.
- No broad refactor of builders, manifests, exports, or validation code unless a
  test exposes a real defect; if such a defect is found, stop and report rather
  than hiding it with weaker assertions.

## Files likely touched

Verify against actual code before starting; report conflicts instead of
guessing.

- `backend/requirements.txt` — add a pinned `hypothesis` test dependency if the
  repo has no separate dev/test requirements file. A repository split for dev
  dependencies is out of scope; follow current convention.
- `backend/pyproject.toml` — add pytest marker registration if a new marker is
  introduced; otherwise no change expected.
- `backend/tests/bluecad/test_geometry_property_invariants.py` (new) — property
  generator and invariants.
- `backend/tests/bluecad/test_manifest_determinism_canary.py` (new) — golden
  fixture digest canary.
- `backend/tests/bluecad/fixtures/property_geometry/` (new, optional) — small
  fixture specs only if needed for the canary. Do not commit generated STEP/STL/
  GLB files.
- `backend/tests/bluecad/fixtures/property_geometry_expected.json` or similar
  (new) — checked-in expected manifest digests for the canary.
- `.github/workflows/ci.yml` or existing backend CI workflow — only if necessary
  to ensure the new test marker runs in CI.

## Design constraints

- **Use the real CAD adapter path.** The property tests must call the same
  adapter/build entry point used by the existing BLUECAD tests. Do not re-create
  builder math in the test as a parallel implementation.
- **Generate valid specs, not arbitrary JSON.** Strategies must construct
  bounded valid `GeometrySpec` payloads using the actual supported part kinds
  and parameter names. Invalid/adversarial JSON belongs to item 023, not this
  slice.
- **Start bounded and cheap.** Use small example counts and deterministic
  settings so the suite is CI-stable. Suggested starting point: 25–50 examples
  per strategy, `deadline=None` if build123d variability makes wall-time
  deadlines noisy, and a fixed Hypothesis database behavior suitable for CI.
- **Prefer a phased generator.** Phase 1 may cover single-part specs and a small
  set of simple two-part connected assemblies. Do not try to generate a full
  reactor graph in the first implementation.
- **No physics claims.** Geometry invariants may assert manifest sanity and
  topological/port consistency; they must not claim structural, flow, light, or
  buoyancy correctness.
- **No snapshotting generated binary artifacts.** The canary snapshots digest
  expectations and small JSON fixtures only. STEP/STL/GLB output remains
  generated in temp directories.
- **Fail loudly on digest drift.** If the golden manifest digest changes, the
  test failure must print the old and new digest and the fixture name. The fix is
  a conscious PR that explains why the manifest changed, not automatic refresh.

## Generator contract

At minimum, implement strategies for:

1. **Single tube-run specs** with bounded `length`, `outer_d`, and `wall_t`.
2. **Simple tube assemblies** with two compatible ports and one connection, if
   the current `GeometrySpec` schema supports connections in the adapter path.
3. **At least one non-tube supported kind** discovered from the real builder
   registry. If the current code does not expose a stable registry, document the
   implemented kinds in the test module and keep the list intentionally small.

Boundaries:

- All dimensions are in millimetres.
- Values must stay comfortably away from singular geometry: no zero length,
  no zero wall, no wall thickness near or above radius, no tiny bend radii near
  kernel tolerance, no 10k-part cases.
- Recommended initial ranges:
  - `length`: 50–5000 mm
  - `outer_d`: 20–500 mm
  - `wall_t`: 1–25 mm, always `< outer_d / 4`
  - rotations/translations: bounded to ±10_000 mm and finite radians/degrees as
    required by the existing schema
- Generated IDs must be ASCII, short, unique, and deterministic under shrinking.

## Required invariants

For every generated valid spec that should build:

1. Build verdict is `pass` / candidate status equivalent is valid according to
   the called adapter path.
2. Manifest exists and is valid JSON.
3. `manifest_digest` exists, is stable across two builds of the same spec in two
   fresh temp output directories, and changes only when the manifest content
   actually changes.
4. Every part entry has:
   - finite positive `volume_mm3`,
   - finite bbox coordinates,
   - `bbox.min[axis] <= bbox.max[axis]` for every axis,
   - positive bbox envelope volume for non-degenerate solids,
   - `0 < volume_mm3 <= bbox_envelope_volume * tolerance_factor` where the
     tolerance factor is explicit and conservative enough for rotated/curved
     parts. If this invariant is too crude for a kind, narrow it by kind rather
     than deleting it globally.
5. Every resolved port has finite origin and direction values.
6. Port directions are non-zero and approximately unit-normalized if the manifest
   represents normalized directions. If the current manifest does not guarantee
   unit vectors, assert finite non-zero vectors and document why.
7. For connected assemblies, connected port origins are coincident within the
   existing adapter tolerance and opposing/compatible directions satisfy the
   existing connection semantics. Do not invent a new tolerance if the adapter
   already defines one.
8. No output path escapes the pytest temp output root.
9. Rebuilding the same spec twice produces the same digest and the same sorted
   manifest semantic content, excluding allowed run-specific fields if any are
   explicitly documented.

For generated specs that the strategy marks as valid but the adapter rejects,
the test should fail: that is either a generator bug or a real adapter/schema
bug. Do not silently filter after generation except through Hypothesis
assumptions that encode schema preconditions.

## Determinism canary contract

Add a checked-in fixture set with 3–5 small stable specs, for example:

- minimal single tube,
- one connected two-tube assembly if supported,
- one supported curved/bend-like part,
- one representative joint/manifold/float-style part if currently stable.

For each fixture:

1. Build it in a fresh temp output directory.
2. Read the produced manifest and `manifest_digest`.
3. Compare to checked-in expected digest metadata.
4. Assert output semantic content is deterministic across two immediate rebuilds.
5. On mismatch, fail with a message that says:
   - fixture name,
   - expected digest,
   - actual digest,
   - instruction to update the expected file only in a PR that explains the
     intentional geometry/manifest/dependency change.

The expected digest file must not include machine-local paths, timestamps, temp
paths, random seeds, or absolute artifact paths. If any such field appears in
manifest content, that is a determinism bug to fix or explicitly normalize in the
manifest code, not in the canary.

## Acceptance criteria

- `python -m pytest tests/bluecad/test_geometry_property_invariants.py -q` passes
  from `backend/`.
- `python -m pytest tests/bluecad/test_manifest_determinism_canary.py -q` passes
  from `backend/`.
- The normal backend test command still passes, or the PR documents why a new
  marker/job is required and proves that CI runs it.
- `python -m ruff check app tests` passes from `backend/`.
- No generated CAD binaries are committed.
- No live provider, network, gmsh, or ccx call is required.
- The implementation appends `## Implementation notes` to this spec, including:
  - exact generated part kinds covered,
  - Hypothesis example counts/settings,
  - canary fixtures and digest metadata path,
  - any invariants excluded by kind and why.

## Failure modes this spec must prevent

- A dependency bump changes manifest ordering/digests silently.
- A builder emits negative, NaN, infinite, or impossible volume/bbox values.
- A generated valid spec crashes build123d instead of returning a structured
  failure.
- Port transforms drift under rotation/translation.
- Tests accidentally become solver/integration tests and start depending on
  gmsh/ccx.
- Tests write outside temp directories or commit generated geometry artifacts.

## Non-goal handoff to other specs

- Invalid/adversarial payloads and resource-exhaustion probes belong to 023.
- Golden end-to-end pipeline execution belongs to 021.
- FEM analytic verification belongs to 024.
- L-prop proposed-builder promotion uses this slice as validation muscle later,
  but durable vocabulary extension itself belongs to 033.
