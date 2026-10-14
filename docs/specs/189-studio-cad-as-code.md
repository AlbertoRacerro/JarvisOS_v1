# 189 — Engineering Studio CAD as code: user-authored build123d geometry

State: **proposed, not ready**. One maintainer decision is open (see "Decision requested"). Written after spec 188 was delivered, as the 2026-10-13 directive asks ("then plan the custom CAD geometry … using the evidence from Stage 5"). Reviewed against master `80ad932c`. Architecture record: [Engineering Studio architecture](../implementation/engineering-studio-architecture-2026-10-13.md).

- **Hard dependencies:** 187, 188.

## Fresh evidence (master `80ad932c`, WSL2 qualification host, 2026-10-13)

Measured by running user source through `studio_runtime.run` with the real bubblewrap sandbox:

| Probe | Result |
|---|---|
| `import build123d` (0.11.1) at default limits | ok, 4.9 s for the whole run |
| build a `Box`, read its volume | ok, 3.4 s |
| build a cylinder, export STEP and STL to scratch | ok, 2.6 s; import 1.9 s; STEP 5.6 kB, STL 25 kB; peak RSS 489 MB |

A helical baffle probe on the same host and build123d 0.11.1 swept a 4 × 2 mm rectangular section along a four-turn, 18 mm radius helix (12 mm pitch, 48 mm height). A direct kernel run exported STEP (69,826 bytes), default-resolution STL (8,636,184 bytes) and GLB (3,277 bytes) in 3.89 s with 638,132 KiB peak RSS. This sizes the proposed profile; the sandboxed end-to-end run remains acceptance evidence, not a claim of this probe.

- **The kernel already runs in the sandbox.** No new dependency is needed: `build123d` is in `backend/requirements.txt` and the sandbox mounts the backend environment read-only.
- **Geometry cannot leave the sandbox.** Only `result.json` crosses, capped at 64 KiB. Files are capped at 128 KiB each, scratch at 4 MiB, wall time at 15 s. A trivial cylinder already needs 25 kB of STL; a real part needs megabytes.
- **The BLUECAD viewer only shows typed parts.** `BluecadGlbViewer` renders a candidate's GLB. `bluecad/export.py` builds GLB, STEP and STL from spec part kinds through `builders.py`. No path accepts user geometry.
- **The 188 owners are reusable as they are:** draft, test report bound to hashes, immutable publication, revise, library, editor, runtime status and refusal.

## Proposed decision

1. **Category.** Studio gains a second executable category, `geometry`: a Python function `build(...)` with declared, unit-bearing inputs that returns one build123d shape. The wizard, scaffold, editor, lifecycle and library are those of 188.
2. **Runtime profile.** The 187 owner gains a fixed, host-selected `geometry` profile: 30 s wall, 24 s CPU, 1 GiB memory, 32 processes, 16 MiB per file and 64 MiB scratch. Only geometry calls select it; the existing calculation limits are unchanged. The baffle probe above fits with margin. Host artifact admission has a separate 32 MiB combined cap.
3. **Artifact channel.** The host creates a unique empty output directory for one run and binds only that directory writable into the sandbox. After `build` returns, sandbox-side worker code exports the shape to fixed names there: `model.step`, `model.stl`, `model.glb`. Once the sandbox process exits, the host requires exactly those three entries; it opens each with no symlink following, verifies a single-link regular file and the per-file and combined size caps from file descriptors, copies bytes to host-owned immutable storage, hashes the copied bytes and registers all three together. Any extra, missing, linked, special or oversized entry fails the run and registers none. User code never selects a host path. No files from the writable directory become visible until all checks pass.
4. **Untrusted output.** The exported bytes are treated as untrusted: the host never executes or imports them. STEP and STL are downloads; GLB is served only to the existing browser viewer with the fixed type, no content sniffing and the same origin and authorization rules as other BLUECAD artifacts. A malformed GLB may still exercise the browser parser; this is residual risk, not a validation claim.
5. **Host-computed facts.** Bounding box, volume, solid count and validity are computed in the sandbox by the worker and returned in the JSON result. Test passes when the build succeeds, the shape is a valid solid and optional declared bounds hold.
6. **Lineage.** Each generation is a run through the existing runner-job flow. Its artifacts are registered with their hashes and linked to the model version, source hash, contract hash and input bindings. Stale and superseded behave as in 188.
7. **Preview.** The Studio model workspace shows the run's GLB in the existing `BluecadGlbViewer`. User geometry has no part-kind semantics and no scene binding.
8. **No new part kinds.** Nothing is added to `builders.py`. Spec 033 is re-evaluated after this slice.

## Decision requested from the maintainer

Items 2 and 3 change the 187 boundary: user-produced files would leave the sandbox through a writable bound directory, and one profile would run longer with larger files. The proposed controls bound that exposure but cannot make CAD file parsing risk disappear. The directive asks for security-boundary changes to be escalated, so this spec is not marked ready.

| Option | Consequence |
|---|---|
| **A. Approve the artifact channel and the geometry profile (recommended)** | Golden workflow 2 is reachable with the existing kernel and viewer. Residual risk: crafted STEP, STL or GLB bytes reach the browser viewer and the operator's CAD tools, as with any downloaded file |
| B. Keep the boundary; return a mesh inside the JSON result | Not viable beyond toy parts: 64 KiB holds a few hundred triangles, and STEP cannot be returned |
| C. Build on the host from a declarative description | Removes the sandbox change but is no longer user-authored build123d, which the directive names as P1 |

## Acceptance (once ready)

1. **Golden workflow 2, real browser.** An operator, using the GUI only, creates a helical baffle with declared parameters, writes the build123d code, tests it, previews it, publishes it, generates it with one input bound to a project Parameter, and downloads STEP and STL. Lineage shows the version, source hash and inputs. Changing the Parameter flags the generation stale.
2. **Channel is closed by default.** Hostile cases cover an extra or missing name, symlink, hard link, directory or special file in place of an artifact, per-file and aggregate oversize output, malformed GLB, and failed or timed-out export. Invalid sets get no registered or browser-visible artifact and fail with a stated reason. The host copies only after sandbox exit and verifies copied hashes.
3. **No host access.** The 187 hostile suite passes unchanged under the geometry profile.
4. **Execution boundary.** Geometry cannot be generated with the runtime disabled or unavailable.
5. **Typed BLUECAD is unchanged.** Existing candidate build, export and scene-binding tests pass without edits.

## Non-goals

- No BLUECAD candidate or assembly integration, and no FEM or CFD on user geometry.
- No FreeCAD exchange, no visual CAD, no Sidecar code proposals.
- No change to the `calculation` category limits.
