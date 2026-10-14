# 189 — Engineering Studio CAD as code: user-authored build123d geometry

State: **accepted and ready**. Written after spec 188 was delivered, as the 2026-10-13 directive asks ("then plan the custom CAD geometry … using the evidence from Stage 5"). The maintainer approved Option A on 2026-10-14 with revised initial limits (see "Maintainer decision"). Proposed against master `80ad932c`; readiness reviewed against master `21f454c5`. Architecture record: [Engineering Studio architecture](../implementation/engineering-studio-architecture-2026-10-13.md).

- **Hard dependencies:** 187, 188.

## Fresh evidence (master `80ad932c`, WSL2 qualification host, 2026-10-13)

Measured by running user source through `studio_runtime.run` with the real bubblewrap sandbox:

| Probe | Result |
|---|---|
| `import build123d` (0.11.1) at default limits | ok, 4.9 s for the whole run |
| build a `Box`, read its volume | ok, 3.4 s |
| build a cylinder, export STEP and STL to scratch | ok, 2.6 s; import 1.9 s; STEP 5.6 kB, STL 25 kB; peak RSS 489 MB |

A helical baffle probe on the same host and build123d 0.11.1 swept a 4 × 2 mm rectangular section along a four-turn, 18 mm radius helix (12 mm pitch, 48 mm height). A direct kernel run exported STEP (69,826 bytes), default-resolution STL (8,636,184 bytes) and GLB (3,277 bytes) in 3.89 s with 638,132 KiB peak RSS. The maintainer accepted this measurement as sufficient for V0; no further benchmarking precedes implementation. The sandboxed end-to-end run is acceptance evidence.

- **The kernel already runs in the sandbox.** No new dependency is needed: `build123d` is in `backend/requirements.txt` and the sandbox mounts the backend environment read-only.
- **Geometry cannot leave the sandbox today.** Only `result.json` crosses, capped at 64 KiB. Files are capped at 128 KiB each, scratch at 4 MiB, wall time at 15 s. A trivial cylinder already needs 25 kB of STL; a real part needs megabytes.
- **The BLUECAD viewer only shows typed parts.** `BluecadGlbViewer` renders a candidate's GLB. `bluecad/export.py` builds GLB, STEP and STL from spec part kinds through `builders.py`. No path accepts user geometry.
- **The 188 owners are reusable as they are:** draft, test report bound to hashes, immutable publication, revise, library, editor, runtime status and refusal, and the runner-job flow with Parameter bindings, stale and superseded flags.
- **Readiness re-check (master `21f454c5`).** `studio_runtime.runtime` still holds one fixed limit set (15 s wall, 12 s CPU, 1 GiB, 32 processes, 128 KiB per file, 4 MiB scratch) and binds `result.json` as a single pre-created file. The runner executes `studio_calc_v1` through `_run_studio_calc_job`, clamping the wall time to 15 s. The `geometry` category is listed as unavailable.

## Maintainer decision (2026-10-14)

Option A is approved: the artifact channel and a geometry profile, with these initial limits. They are engineering defaults, held in one table in the 187 owner, not permanent architectural limits.

| Limit | Geometry profile | Calculation profile (unchanged) |
|---|---|---|
| Wall time | 120 s | 15 s |
| CPU time (all threads) | 480 s | 12 s |
| Address space | 4 GiB | 1 GiB |
| Processes and threads | 32 | 32 |
| Any one file, including each artifact | 64 MiB | 128 KiB |
| Scratch (`/work` tmpfs) | 256 MiB | 4 MiB |
| Combined admitted artifacts | 128 MiB | — |

CPU time is four times the wall budget: the OCCT mesher may use several threads, and the wall time stays the binding limit. Filesystem, network, secret and process isolation are unchanged.

If a real workload exceeds a limit, the run fails and records which limit it hit and that limit's configured value. Raising a limit by operator authorization, without a source change, is a later slice.

## Contract

1. **Category.** Studio gains a second executable category, `geometry`: a Python function `build(...)` with declared, unit-bearing inputs that returns one build123d shape. The wizard, scaffold, editor, lifecycle and library are those of 188.
2. **Runtime profile.** The 187 owner gains a fixed, host-selected `geometry` profile with the limits above. Only geometry calls select it; user code and requests cannot select a profile or exceed its ceilings. The calculation profile is unchanged.
3. **Artifact channel.** For one run the host creates a private directory holding three empty regular files, `model.step`, `model.stl` and `model.glb`, and binds each file, not the directory, writable into the sandbox. The sandbox can write into those three files and cannot create, rename or link any other host entry. After `build` returns, sandbox-side worker code exports the shape into them. Once the sandbox process has exited, the host opens each name with no symlink following and verifies, from the file descriptor, a single-link regular file, a non-empty size within the per-file cap and the combined cap. It then copies the bytes to host-owned immutable storage, hashes the copied bytes and registers all three together. Any failed check fails the run and registers none. User code never selects a host path, and no file from the run directory is visible until all checks pass. The per-file bind is narrower than the writable directory first proposed: a writable directory would let a hostile script fill host disk with many capped files within the wall time.
4. **Untrusted output.** The exported bytes are treated as untrusted: the host never executes or imports them. STEP and STL are downloads; GLB is served only to the existing browser viewer with the fixed type, no content sniffing and the same origin and authorization rules as other artifacts. A malformed GLB may still exercise the browser parser; this is residual risk, not a validation claim.
5. **Shape facts.** Bounding box, volume, solid count and validity are computed in the sandbox by the worker and returned in the JSON result. Test passes when the build succeeds, the shape is a valid solid and optional declared bounds hold.
6. **Lineage.** Each generation is a run through the existing runner-job flow. Its artifacts are registered with their hashes and linked to the model version, source hash, contract hash and input bindings. Stale and superseded behave as in 188.
7. **Preview.** The Studio model workspace shows the run's GLB in the existing `BluecadGlbViewer`. User geometry has no part-kind semantics and no scene binding.
8. **Resource failures.** A run stopped by a limit is classified `limit` (or `timeout` for wall time) and names the limit: `wall_seconds`, `cpu_seconds`, `memory_bytes`, `file_bytes`, `scratch_bytes` or `artifact_bytes`, with the configured value. Test reports, run history and the GUI show it. Nothing is registered.
9. **No new part kinds.** Nothing is added to `builders.py`. Spec 033 is re-evaluated after this slice.

## Acceptance

1. **Golden workflow 2, real browser.** An operator, using the GUI only, creates a helical baffle with declared parameters, writes the build123d code, tests it, previews it, publishes it, generates it with one input bound to a project Parameter, and downloads STEP and STL. Lineage shows the version, source hash and inputs. Changing the Parameter flags the generation stale.
2. **Channel is closed by default.** Hostile cases cover an attempt to create an extra entry, replacing an artifact with a symlink, hard link, directory or special file, a missing (empty) artifact, per-file and aggregate oversize output, malformed GLB, and failed or timed-out export. Invalid sets get no registered or browser-visible artifact and fail with a stated reason. The host copies only after sandbox exit and verifies copied hashes.
3. **No host access.** The 187 hostile suite passes unchanged, and its host-access cases also pass under the geometry profile.
4. **Execution boundary.** Geometry cannot be generated with the runtime disabled or unavailable. A request cannot select the geometry profile for calculation code or exceed a profile ceiling.
5. **Resource failures are explicit.** Scripts that exceed the wall time, memory, a per-file cap and the combined cap each fail with the named limit and its configured value, and register nothing.
6. **Typed BLUECAD is unchanged.** Existing candidate build, export and scene-binding tests pass without edits. The 188 and 190 suites pass without edits.

## Required evidence

- Backend tests for criteria 2 to 6 with the real bubblewrap sandbox and build123d.
- A frontend test file gating the build for the geometry wizard, editor, test, preview and generation views.
- A real-browser proof of criterion 1 with screenshots on the exact head.
- Full backend suite in a clean environment, ruff, frontend build and the registry checks.

## Non-goals

- No BLUECAD candidate or assembly integration, and no FEM or CFD on user geometry.
- No FreeCAD exchange, no visual CAD, no Sidecar code proposals.
- No change to the `calculation` category limits.
- No resource-escalation UI, operator limit override or resource-calibration system, and no benchmarking campaign.
