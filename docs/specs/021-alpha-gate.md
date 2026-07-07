# 021 — ALPHA-GATE: executable pipeline gate + data-root backup/restore

Status: ready (drafted 2026-07-07 from expert kernel; expert review
resolutions written same day — see final section; slice A implement after
038+044 merge, slice B implementable now)
Depends on: slice A depends on 038 (SIM-WIRE) AND 044 (EVIDENCE-BRIDGE-1),
both merged. Slice B depends on nothing and is implementable immediately.

## Goal

After this slice, two independent things exist:

(A) One CI-runnable test session (or single script) that exercises the real
BLUECAD pipeline end to end — fixture brief → 010 loop → build → validate →
mesh → solve → artifacts — against real `gmsh`/`ccx` binaries, asserting
`valid`, the expected artifact rows and files, `evidence_records` rows for
mesh and FEM outcomes, and manifest-digest determinism across two runs. This
turns "alpha raggiunta" from an opinion into a green check.

(B) One CLI entry point that takes a consistent snapshot of the data root
(SQLite backup via the `sqlite3` backup API + a copy of the artifacts
directory), rotates old snapshots keep-last-N, and — critically — an
automated per-commit test that proves a snapshot can be restored: row counts
and artifact digests in the restored root match the originals.

These two deliverables are independent implementation slices with different
dependencies (see kernel decision 1/7) and may land as separate PRs.

## Why

`docs/strategy/JARVISOS_BETA_PROGRAM.md` Phase A names this pair as the item
that closes the physical loop: "the loop that already builds + validates
geometry must also simulate and record, deterministically" (038), and 021 is
the next row, depending on 038. The same document's "What beta means" gate
section states beta requires "the alpha gate green ... and a backup restore
proven at least once." `docs/strategy/PROGRAM_BACKLOG.md`'s Horizon 2 row 021
("Alpha-gate demo as executable CI test + data-root backup job") and its
Quality program row 021 ("Executable alpha gate ... turns 'alpha raggiunta'
from an opinion into a green check; doubles as backup-tested demo") both name
this pair as the alpha-credibility differentiator. Slice B has no dependency
on 038/044 and closes real data-loss risk (a live SQLite file has never had a
tested backup path) independently of when slice A's dependencies land.

## Scope

In scope:

**Slice A — executable alpha gate:**
- One pytest test (preferred, to reuse existing fixtures/markers/skip
  patterns) or one script under `scripts/`, invoking the real loop entry
  `create_bluecad_candidate` (`backend/app/modules/bluecad/loop.py`) with:
  - a checked-in fixture brief (plain string; no live provider call — see
    Design constraints for the offline mechanism),
  - a caller-supplied fixture `AnalysisSpec` (minus `geometry`, per 038
    Review resolution 1) set on `BluecadLoopConfig.analysis_spec`,
  - `force_external_allowed=True` and a scripted fake adapter injected via
    `adapters=`/`bindings=`, exactly as 010's own tests already do.
- Assembling the full `AnalysisSpec.geometry` block from the candidate's own
  registered build artifacts (STEP + manifest paths), as 038 wires it — this
  spec's test only supplies the non-geometry fields (`material`, `bcs`,
  `loads`, `mesh`, `pass_criteria`) and lets the loop fill `geometry`.
- Assertions listed under kernel decision 4 below.
- Wiring as a separate, manually-triggered CI job requiring both
  `bluecad_gmsh` and `bluecad_ccx` real-tool markers (024's pattern) — see
  Design constraints for the actual current CI state, which this spec must
  extend, not assume.

**Slice B — data-root backup + proven restore:**
- One CLI script under `scripts/` that snapshots the data root: a SQLite
  backup via the `sqlite3` backup API (`sqlite3.Connection.backup(...)`, not
  a raw file copy of a live DB) plus a copy of the artifacts directory, into
  a timestamped snapshot directory, then prunes to keep-last-N (default 7,
  configurable via a CLI flag or env var).
- One automated test in the normal per-commit suite that builds a small
  fixture data root (a temp SQLite DB with known rows + a small artifacts
  tree), runs the backup function, restores the snapshot into a different
  temp root, points the storage layer at the restored root, and asserts row
  counts and artifact file digests match the originals.
- Prose documentation (in this spec and/or the script's own docstring/`--help`)
  of a suggested invocation cadence (cron on Linux / Task Scheduler on
  Windows) — no scheduler daemon is built.

Out of scope (binding non-goals):
- No cloud/offsite backup destination — local filesystem only.
- No scheduler daemon; invocation is manual/documented-cron only.
- No UI for either slice.
- No golden-digest determinism canary across dependency bumps (that is
  backlog item 022 — this gate's own determinism check is narrower: same
  process, two consecutive runs, no golden file checked in).
- No property-based tests (backlog item 022).
- No new orchestration layer, job queue, or background worker.
- No changes to `loop.py`, `mesh_adapter.py`, `fem_adapter.py`, or any
  adapter — this gate only calls existing entry points with fixture data.
- No gate variant that skips mesh/solve/evidence assertions "while 038/044
  aren't merged" — slice A is either fully red (038/044 missing, or the real
  pipeline fails) or fully green; a partial/soft-fallback gate is forbidden
  (kernel decision 7, `AGENTS.md` invariant 9).

## Files likely touched

Verify against actual code before starting; report conflicts instead of
guessing.

- `backend/tests/bluecad/test_alpha_gate.py` (new) — slice A, marked
  `@pytest.mark.bluecad_gmsh` and `@pytest.mark.bluecad_ccx`.
- `backend/tests/bluecad/fixtures/` — a fixture brief text file and a fixture
  `AnalysisSpec` JSON (minus `geometry`) referencing `tube1.port_a` /
  `tube1.port_b` (see Design constraints) — reuse `minimal_single_tube.json`
  as the scripted fake adapter's response rather than adding new geometry.
- `scripts/bluecad_alpha_gate.py` (new, only if the implementer chooses the
  script form over a pure pytest session — see Open questions in 024, same
  choice applies here).
- `scripts/data_root_backup.py` (new) — slice B CLI entry point, following
  the plain-Python-script-run-directly convention already used by every file
  under `scripts/` (e.g. `scripts/router_policy_canonical_digest.py`,
  `scripts/cheap_review.py`) — no new CLI framework dependency.
- `backend/tests/test_data_root_backup_restore.py` or
  `backend/tests/core/test_data_root_backup_restore.py` (new) — slice B
  restore-proof test, offline, per-commit.
- `backend/app/core/paths.py` — read-only reference for `JarvisPaths`
  (`data_root`, `database_file`, `artifacts_dir`); no changes expected unless
  the restore test needs a way to point the storage layer at an alternate
  root, in which case verify whether `JARVISOS_DATA_ROOT`/`get_settings()`
  overriding (already used by `backend/tests/conftest.py` for test isolation)
  is sufficient — do not add new path-resolution logic if the existing
  env-var override already covers it.
- `.github/workflows/` — new, separate, manually-triggered workflow (or a
  new job in an existing one) for slice A; slice B's restore test runs in the
  existing `backend` job in `.github/workflows/ci.yml` (no new workflow
  needed for B, since it must run in the normal per-commit gate).

## Design constraints

- **Kernel decision 1 (two independent slices).** Slice A and slice B may be
  implemented and merged as separate PRs in either order; slice B has no
  code dependency on slice A or on 038/044.
- **Kernel decision 2 (fixture AnalysisSpec, real geometry, verified port
  labels).** Per 038 Review resolution 1, the opt-in mechanism is a
  caller-supplied `analysis_spec` field on `BluecadLoopConfig` (presence =
  opt-in). This spec's fixture `AnalysisSpec` must reference port labels the
  fixture geometry actually produces. Verified against the real code path
  (not the `.expected.json` test-comparison fixture, which has no ports
  block): `backend/app/modules/bluecad/export.py`'s `_manifest()` writes
  `manifest["resolved_ports"][part_id][port_name]` from each `BuiltPart`'s
  `ports` dict (`backend/app/modules/bluecad/models.py`'s `PortFrame`).
  `backend/tests/bluecad/fixtures/minimal_single_tube.json` has one part,
  `part_id: "tube1"`, `kind: "tube_run"`. `tube_run`'s builder
  (`backend/app/modules/bluecad/builders.py`, the `ports={...}` block for the
  tube case) emits exactly two ports named `port_a` and `port_b`
  (`PortFrame((0,0,0), (-1,0,0), outer_d, wall_t)` and
  `PortFrame((length,0,0), (1,0,0), outer_d, wall_t)`). Therefore the correct
  fixture port labels are **`tube1.port_a`** (fixed end) and **`tube1.port_b`**
  (loaded end) — not `fixed_end`/`tip_end` as used illustratively in 024's
  draft cases, which describe a *different*, not-yet-built benchmark
  geometry, not `minimal_single_tube`. The gate's `AnalysisSpec` fixture
  should use `bcs = [{"port_label": "tube1.port_a", "kind": "fixed"}]` and
  `loads = [{"port_label": "tube1.port_b", "type": "force_total", "force":
  [0, F, 0]}]` (or an equivalent single BC + single load), with `material`,
  `mesh.target_size`, and `pass_criteria` values the implementer picks to be
  cheap/fast for a gate (not a verification battery — no tolerance claims
  needed here, unlike 024).
- **Kernel decision 3 (AI determinism — reuse 010's existing offline
  mechanism, do not invent a new one).** Verified against
  `backend/tests/bluecad/test_loop_stage2.py` and
  `backend/app/modules/bluecad/ledger.py`: 010's own tests make the loop's
  proposal step deterministic/offline via `ScriptedFakeBluecadAdapter`
  (`backend/app/modules/bluecad/ledger.py:276-310`), an `AIProviderAdapter`
  implementation whose `complete()` pops a scripted response off a
  caller-supplied list and returns it as an `AIResponse`, with
  `provider_id = "scaleway"`. It is injected into `create_bluecad_candidate`
  via its `adapters={"scaleway": adapter}` and `bindings=...` keyword
  arguments (`bindings` built as
  `{route: ProviderBinding(route, "scaleway", "scripted", False, 4000) for
  route in [...]}`), together with `force_external_allowed=True` to bypass
  the budget-blocked fail-closed gate in tests. This is the exact, only
  mechanism to reuse — the gate's fixture brief is answered by a
  `ScriptedFakeBluecadAdapter([<minimal_single_tube.json spec text>])` so
  attempt 1 always proposes a valid, known GeometrySpec. Inventing a second
  injection mechanism (e.g. monkeypatching `run_ai_task` directly, or a new
  fake-provider class) is forbidden. No live provider is called at any point
  (`AGENTS.md` test-gate rule: tests never call live providers).
- **Kernel decision 4 (gate assertions, minimum set, verified artifact
  kinds).** Verified against `backend/app/modules/bluecad/loop.py`'s
  `_build_and_register` (roles: `bluecad_spec`, `bluecad_report`,
  `bluecad_manifest`, `bluecad_glb`) and 038's design (mesh/FEM report
  artifacts registered the same way `_build_and_register` already does for
  the validation report). The gate must assert, at minimum:
  1. The candidate reaches `status == "valid"`.
  2. Artifact rows for spec, manifest, validation report, and GLB (the
     existing 010 roles) exist and their files are present on disk at
     `stored_path`.
  3. The STEP file (`model.step`, written by `export.py`'s `_export_shapes`)
     is present on disk — verify at implementation whether 010 already
     registers a `bluecad_step`-role artifact for it or whether the STEP is
     only reachable via the manifest's `artifacts["model.step"]` entry
     alongside the registered manifest artifact; assert whichever is
     actually true, do not assume a `bluecad_step` role exists without
     checking `ledger.py`/`loop.py`.
  4. The mesh `.inp` file (`mesh.inp`, written by `mesh_adapter.py`) and the
     solver result summary (FEM report/result artifact, per 038's wiring)
     are present on disk, each via a registered `artifacts` row (mesh report
     and FEM report roles — exact role names are 038's to define; this gate
     asserts whatever 038 actually registers, verified at implementation
     time, not invented here).
  5. `evidence_records` rows exist for both the mesh and FEM outcomes, with
     `candidate_id` and `attempt_id` populated (via 044's
     `record_mesh_quality_evidence` / `record_fem_static_evidence` hooks, as
     wired by 038).
  6. Determinism: the gate runs the full pipeline twice (two fresh
     candidates from the same fixture brief + AnalysisSpec + scripted
     adapter) and asserts the two runs' manifest `manifest_digest` values
     (from each run's own `manifest.json`) are equal. No golden digest is
     checked into the repo for this comparison — the two live runs are
     compared against each other only. A checked-in golden-digest canary is
     explicitly out of scope (backlog item 022).
- **Kernel decision 5 (backup mechanism, hard requirement).** The SQLite
  half of the snapshot must use the `sqlite3` backup API
  (`sqlite3.Connection.backup(target_connection)`, available since Python
  3.7) against the live database connection, producing a consistent
  point-in-time copy even if the source DB is open elsewhere. A plain
  `shutil.copy`/file-copy of the live `.db` file is explicitly forbidden (can
  copy a half-written page during a concurrent write) — this is a hard
  dependency the implementer must not substitute with a "simpler" fallback.
  The artifacts directory (no live-write consistency concern for static
  files) may be copied with a straightforward recursive copy
  (`shutil.copytree` or equivalent). Rotation: keep the last N snapshot
  directories by creation time, prune older ones; N defaults to 7,
  overridable via a CLI flag (and/or env var, implementer's choice, but
  document whichever is chosen).
- **Kernel decision 6 (restore proof — a green restore, not "a file
  exists").** The per-commit test must NOT merely assert that a backup file
  was written. It must: (a) build a small fixture data root (a fresh SQLite
  DB via `initialize_database()` or equivalent, seeded with a few known rows
  in at least one existing table plus at least one small file registered
  under a fixture artifacts directory), (b) run the backup function against
  it, (c) restore the resulting snapshot into a separate temp directory, (d)
  point the storage/paths layer at the restored root (via the same
  `JARVISOS_DATA_ROOT`-style override `backend/tests/conftest.py` already
  uses for test isolation — verify and reuse, do not invent a second
  override mechanism), (e) assert row counts in the restored DB match the
  original, and (f) assert artifact file digests (sha256) in the restored
  artifacts directory match the originals byte-for-byte.
- **Kernel decision 7 (hard dependency — no soft fallback).** Slice A cannot
  be implemented, let alone merged, until both 038 and 044 are merged:
  `create_bluecad_candidate` has no `analysis_spec`/simulate opt-in today
  (verified: `BluecadLoopConfig` in `backend/app/modules/bluecad/models.py`
  currently has only `max_attempts_per_tier`, `tier_ladder`,
  `max_output_tokens`, `per_call_timeout_s` — no `analysis_spec` field), and
  `backend/app/modules/bluecad/evidence.py` does not exist yet (verified:
  no such file in the tree; `evidence_records` is absent from
  `backend/app/core/schema.py`). Writing a temporary stand-in sim stage or
  evidence writer "until 038/044 land," or a gate variant that only asserts
  build+validate (skipping mesh/solve/evidence) while claiming to be the
  alpha gate, is explicitly forbidden — the correct state before 038/044
  merge is "slice A not yet implementable," not a partial green gate. Slice
  B has no such dependency and may be implemented now, independent of slice
  A's timeline.
- **CI wiring — verify current state, do not assume 024 already wired
  anything.** Verified against `.github/workflows/`: the repo has exactly
  four workflows today — `ci.yml` (the per-commit `pytest -q` + `ruff` +
  license-boundary gate job, `ubuntu-latest`, no real gmsh/ccx installation
  step), `claude-review.yml`, `senior-review.yml`, `cheap-review.yml` (all
  PR-review automation, unrelated to test execution). **No workflow today
  installs or runs real gmsh/CalculiX, and no `bluecad_gmsh`/`bluecad_ccx`
  marker-selected job exists anywhere in `.github/workflows/`** — despite
  024's spec describing this as a pattern to match, 024 itself has not been
  implemented/merged yet (its own Open Questions section says the CI wiring
  "were not enumerated in this draft"). This spec's slice A must therefore
  create the first such job from scratch (real gmsh + CalculiX installation
  steps, `workflow_dispatch` trigger for manual invocation, `pytest -m
  "bluecad_gmsh and bluecad_ccx" backend/tests/bluecad/test_alpha_gate.py`),
  not merely "match 024's pattern" as if it already exists in CI — if 024
  lands first with its own new workflow job, slice A should reuse that same
  job/workflow file rather than creating a second one; verify at
  implementation time which spec's PR lands first. Slice B's restore test
  has no marker requirement and must run inside the existing `backend` job
  in `ci.yml` (the normal per-commit gate) — no new workflow file needed for
  slice B.
- Reuse existing patterns: `ScriptedFakeBluecadAdapter` (010), the
  `bluecad_gmsh`/`bluecad_ccx` marker-skip behavior via `TOOL_DISABLED`
  (008/009), `open_sqlite_connection()` (`backend/app/core/database.py`), and
  the plain-script convention under `scripts/` — no new dependency, no new
  ORM, no new CLI framework.

## Acceptance criteria

**Slice A:**
1. The gate test/script invokes `create_bluecad_candidate` with a checked-in
   fixture brief, a `ScriptedFakeBluecadAdapter` response equal to
   `minimal_single_tube.json`'s spec text, and a fixture `analysis_spec` on
   `BluecadLoopConfig` referencing `tube1.port_a`/`tube1.port_b` (or the
   correct labels re-verified at implementation time if 038 changes the
   manifest-to-AnalysisSpec wiring).
2. The candidate reaches `status == "valid"`.
3. Spec, manifest, validation-report, and GLB artifact rows exist with files
   present on disk; the STEP file's presence is asserted via whichever
   mechanism 010/038 actually registers it (verify, do not assume a role
   name).
4. Mesh `.inp` and FEM result-summary artifacts exist on disk, each via a
   registered `artifacts` row.
5. `evidence_records` rows exist for both the mesh and FEM outcomes with
   `candidate_id`/`attempt_id` populated.
6. Running the pipeline twice (fresh candidates, same fixture inputs)
   produces two manifest digests that are equal to each other; no golden
   digest is checked into the repo.
7. The gate is marked with both `@pytest.mark.bluecad_gmsh` and
   `@pytest.mark.bluecad_ccx` and skips cleanly (existing `TOOL_DISABLED`
   path) when either real tool is not registry-enabled.
8. The gate is wired into a separate, manually-triggered CI job (new or
   shared with 024's job if that lands first) — verified against the actual
   workflow files at implementation time — and is NOT added to `ci.yml`'s
   per-commit `backend` job.
9. Existing 010/008/009/038/044 tests pass unmodified.

**Slice B:**
10. `scripts/data_root_backup.py` (or the implementer's chosen path) backs up
    a live SQLite database using the `sqlite3` backup API (grep/behavior
    check: no `shutil.copy`/raw file read of the live `.db` path) plus a copy
    of the artifacts directory, into a timestamped snapshot directory.
11. Rotation keeps the last N snapshots (default 7, configurable) and prunes
    older ones.
12. An automated per-commit test builds a fixture data root, backs it up,
    restores into a temp root, points the storage layer at the restored
    root, and asserts row counts and artifact sha256 digests match the
    originals — "a backup file exists" alone is NOT sufficient to pass this
    criterion.
13. The restore test runs in the normal per-commit gate (`ci.yml`'s existing
    `backend` job), offline, no real binaries required.
14. Invocation (a suggested cron/Task Scheduler entry) is documented in
    prose; no scheduler daemon code is added.

## Required tests

- `backend/tests/bluecad/test_alpha_gate.py` (slice A): the full
  brief→build→validate→mesh→solve→artifacts→evidence gate described above,
  marked `@pytest.mark.bluecad_gmsh` + `@pytest.mark.bluecad_ccx`, skipping
  cleanly when either tool is registry-disabled; the two-run determinism
  check as a second test or a second phase of the same test.
- `backend/tests/test_data_root_backup_restore.py` (slice B): fixture data
  root construction, backup, restore into a temp root, row-count and
  artifact-digest equality assertions — fully offline, runs in the normal
  suite.
- Both slices: no test calls a live provider, network, or running Ollama
  instance, per `AGENTS.md`.

## Definition of done

Test gate green (see `AGENTS.md`) for slice B in the normal per-commit suite
(slice A's marker-gated gate test is exempt from the per-commit gate by
design, matching 024's pattern), acceptance criteria met, spec status
updated, summary written.

## Open questions / verify at implementation

- **Whether 010 already registers a `bluecad_step`-role artifact for
  `model.step`.** Not verified in this drafting pass beyond confirming
  `_build_and_register` registers `bluecad_spec`, `bluecad_report`,
  `bluecad_manifest`, `bluecad_glb` roles — no `bluecad_step` role was found
  in `loop.py` at drafting time. If the STEP file is only reachable via the
  manifest's own `artifacts["model.step"]` entry (not a separate `artifacts`
  table row), the gate's acceptance criterion 3 must assert presence via
  that path instead — the implementer must re-verify and adjust rather than
  assume a role name that may not exist.
- **Exact mesh/FEM report artifact role names 038 registers.** This spec was
  drafted before 038 exists in the tree; the gate's assertions in kernel
  decision 4 (items 4-5) must be re-verified against 038's actual merged
  code, not this spec's description, at slice A implementation time.
- **Which job/workflow file owns the `bluecad_gmsh`+`bluecad_ccx` CI
  installation steps if 024 and 021 slice A are implemented close together.**
  Whichever lands first should create the job; the second should extend it
  rather than duplicating a real-gmsh/real-ccx install step in two separate
  workflow files. Flag the actual landing order in the implementation
  summary.
- **Fixture `AnalysisSpec` numeric values (material constants,
  `mesh.target_size`, `pass_criteria`).** Left to the implementer to choose
  values that are cheap/fast for a gate — this is not a verification battery
  (024 owns tolerance/analytic-accuracy judgment); the gate only needs the
  solve to complete and produce a `pass` or a typed, non-crashing outcome for
  the mesh/FEM steps, per 038's failure-semantics design (a sim failure never
  blocks the candidate's own `valid` status, and the gate should still assert
  evidence rows exist even if the chosen loads happen to fail Tier 3 pass
  criteria — confirm at implementation time whether the gate requires a sim
  `pass` verdict specifically or merely a recorded, non-crashing evidence row
  regardless of sim verdict; kernel decision 4 as given requires evidence
  rows to exist, not that the sim `pass`, so a sim `fail`/`error` with
  correctly recorded evidence should still satisfy the gate — but this
  reading should be confirmed against the maintainer's intent before
  implementation, since "asserting the outcome" in the goal statement could
  also be read as requiring an end-to-end `pass`).
- **CLI flag/env-var naming for slice B's keep-last-N rotation count and
  snapshot destination path.** Left to the implementer; follow the plain
  `argparse`-or-simpler convention already used by scripts in `scripts/`
  (verify: most existing scripts under `scripts/` do not use `argparse` at
  all — check `router_policy_*.py` and `cheap_review.py` for the actual
  convention before choosing one for `data_root_backup.py`).

## Review resolutions (2026-07-07, expert review)

1. **The gate requires an end-to-end sim `pass`, not merely recorded
   evidence.** The corresponding open question above is resolved in the
   stricter direction: "alpha gate green" means the known-good fixture
   passes the whole physical loop — mesh verdict `pass` AND FEM verdict
   `pass` — in addition to the evidence-row assertions of kernel decision 4.
   Choose the fixture's loads/`pass_criteria` so a healthy pipeline passes
   (generous criteria or none; 024 owns accuracy judgment, the gate owns
   "the chain works"). A gate that goes green on a recorded `fail`/`error`
   evidence row would prove plumbing, not the loop's health. The
   recorded-failure path is still covered elsewhere: 038's own unit tests
   assert it; the gate does not need to.
2. All other Open questions stay open by design (verify at implementation),
   including the pytest-vs-script form and the CI-job ownership handshake
   with 024. The drafter's verification that no real-solver CI job exists
   today — correcting the kernel's "match 024's existing pattern"
   assumption — is accepted and binding: whichever of 021-A/024 lands first
   creates the job, the other extends it.
