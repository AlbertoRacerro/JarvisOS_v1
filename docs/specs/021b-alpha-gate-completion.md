# 021b — ALPHA-GATE completion: executable pipeline + proven backup/restore

Status: planned; this file preserves the historical 021 scope for later
reconciliation. `docs/specs/STATUS.md` is authoritative and this document is
not implementation authority while the row remains `planned`.

Depends on: 021, 038, 044.

## Why this document exists

The original `021-alpha-gate.md` combined two deliverables that are independent
from the server-owned provider-execution hardening now assigned to spec 021:

1. a real-tool, end-to-end BLUECAD alpha proof;
2. a tested data-root backup and restore path.

That historical scope remains valuable, but it must be reconciled against the
merged SIM-WIRE and evidence-bridge runtime before implementation. Moving it to
021b prevents the provider gate from being misrepresented as proof that the
whole engineering pipeline and recovery path are complete.

## Intended goal

After a future implementation of 021b:

- one explicitly marked CI/manual test runs the real BLUECAD path from a
  deterministic fixture brief through build, validation, mesh, static FEM,
  artifacts, and evidence;
- the run proves deterministic manifest output across two equivalent
  executions;
- one local CLI creates a consistent data-root snapshot using the SQLite
  backup API plus artifact-tree copying;
- one normal offline test restores that snapshot into a separate root and
  proves database row counts and artifact digests match.

## Slice A — executable BLUECAD alpha proof

Intended scope:

- call the real `create_bluecad_candidate` entry point;
- inject the existing scripted fake BLUECAD adapter with explicit
  `requires_network=False` bindings;
- supply a validated `analysis_spec` without caller-owned geometry;
- let the merged loop populate geometry from the candidate's registered STEP
  and manifest artifacts;
- run registered real `gmsh` and `ccx` binaries through their existing tool
  boundaries;
- assert the candidate is valid;
- assert required spec, manifest, validation, GLB, mesh, FEM, and evidence
  records/files exist;
- assert mesh and FEM evidence are linked to candidate and attempt identity;
- run twice and compare each generated manifest digest;
- use explicit real-tool pytest markers and a separately triggered CI job.

The future reconciled spec must inspect the merged 038 implementation before
freezing exact artifact roles, simulation-run terminal states, and marker
names. It must not invent roles that the runtime does not create.

## Slice B — data-root backup and restore proof

Intended scope:

- a plain Python CLI under `scripts/`;
- consistent SQLite snapshot through `sqlite3.Connection.backup(...)`, never a
  raw copy of a live database file;
- artifact-directory copy into the same timestamped snapshot;
- configurable keep-last-N rotation with a conservative default;
- restore into a separate target root;
- an offline per-commit test that:
  - creates known database rows and artifact files;
  - snapshots them;
  - restores them into another root;
  - points the storage layer at the restored root;
  - compares expected row counts;
  - compares artifact content digests;
- documented manual/cron/Task Scheduler invocation;
- no scheduler daemon.

## Binding non-goals

- No live AI provider call.
- No cloud or off-site backup destination.
- No automatic promotion.
- No generic workflow/orchestration platform.
- No UI.
- No silent skip of mesh, FEM, evidence, or restore assertions.
- No claim that a skipped real-tool job is a green alpha proof.
- No checked-in long-lived golden manifest digest; same-process two-run
  determinism is the intended narrow check. Spec 056 owns the separate
  determinism canary.
- No broad FEM accuracy claim; analytic verification remains spec 024.

## Preconditions before drafting to `ready`

1. Spec 021 is merged.
2. `STATUS.md` records 038 and 044 as merged.
3. The current `loop.py`, mesh adapter, FEM adapter, ledger, artifact roles,
   evidence writers, and simulation-run lifecycle are re-read from `master`.
4. Existing real-tool markers and CI capabilities are verified from workflow
   code rather than assumed.
5. The storage/path override used by tests is verified against current
   `JARVISOS_DATA_ROOT` behavior.
6. The scope is split into independently reviewable implementation PRs if the
   real-tool proof and backup/restore changes do not share code.

## Draft acceptance questions

The future full spec must answer:

- Which exact artifact rows identify mesh and FEM outputs after merged 038?
- What constitutes terminal success for `simulation_runs`?
- Are mesh/FEM failures advisory to candidate validity but fatal to the alpha
  proof test?
- Which runner/tool registry checks prove real binaries, not stubs, executed?
- Which workflow event runs the real-tool test, and how is a missing runner
  represented without producing a false green?
- Which database tables and artifact roots form the minimum restore
  acceptance set?
- How are partial or interrupted snapshots prevented from being treated as
  complete?

## Current status

This is preserved planning evidence only. Do not dispatch Codex or another
implementation agent until the row is promoted from `planned` through the
normal kernel/full-spec review process.
