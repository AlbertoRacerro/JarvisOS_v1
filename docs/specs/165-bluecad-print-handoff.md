# 165 — BLUECAD print handoff: mm 3MF export and opt-in local "Open in slicer"

State: **accepted and ready**. Written and accepted under the 2026-10-15 maintainer queue directive "continue until all the queue is done" (STATUS row 165, `planned`). Reviewed against master `af053d31`. Research record: [163 Bambu integration research](../implementation/163-bambu-integration-research-2026-10-01.md).

- **Hard dependencies:** 163 (research only). No spec dependency is open. 189 is merged and is touched only through its registered artifacts.

## Fresh evidence (master `af053d31`)

- **Export today is STEP, STL and GLB, no 3MF.** `ARTIFACT_NAMES = ("model.step", "model.stl", "model.glb")` (`bluecad/export.py:15`). `_export_shapes` merges all parts into one compound before STEP and STL (`:46-51`), so per-part identity is lost there. GLB keeps part identity through scene-binding keys (`:68-100`).
- **Hashing.** The manifest records `sha256` and `bytes` for every name in `ARTIFACT_NAMES` (`export.py:161-162`, `sha256_file` `:220`) plus a `manifest_digest` (`:166`). STEP is made deterministic by `_normalize_step_header_timestamp` (`:104`).
- **Registration.** `register_export_artifacts` registers `model.stl` and `model.step` as `bluecad_stl` and `bluecad_step` (`ledger.py:241-262`). GLB is registered separately (`loop.py:1023`). The serve route maps types to MIME and a download name (`routes.py:38`, `:42-78`, `:227`). Paths are confined to the data root (`routes.py:63-69`).
- **Library availability, checked in `backend/.venv`.** `build123d` 0.11.1 imports with `Mesher`. `lib3mf` 2.5.0 imports. `Mesher(unit=Unit.MM)` reports `model_unit == MM`. `requirements.txt:5` pins `build123d==0.11.1` only. `lib3mf>=2.4.1` is a transitive requirement of build123d and is not pinned.
- **3MF bytes are not stable.** Two identical builds (two boxes, same tolerances, same part numbers) written with `Mesher.write` gave different SHA-256 values. Raw-byte hash determinism, as in 163, does not hold. The hash is still valid as a record of the registered file. The determinism test must compare canonical content instead.
- **189 user geometry.** The sandbox writes `model.step`, `model.stl`, `model.glb` (`studio/geometry.py:17`). They are registered as `studio_geometry`, with a hash re-verified on every serve (`studio/routes.py:104-121`). Their bytes are untrusted.
- **WSL detection exists.** `running_under_wsl()` reads `/proc/version` for "microsoft" (`scripts/jarvisos_launcher.py:549-553`). `windows_tool()` resolves `cmd.exe` under `/mnt/c/Windows/System32` (`:556-565`). `open_browser` runs `[cmd.exe, "/c", "start", "", url]` without a shell (`:665-667`). `wslpath -u` is run with argv (`:824`). The backend (`backend/app`) launches no Windows program today. It only reads `WSL_DISTRO_NAME` (`local_ai/runtime/llama_cpp.py:105`).
- **Settings pattern.** Opt-in flags are env-backed fields on `Settings`, default off (`core/config.py:53`, `studio_user_code_enabled`).

## Decision

1. **3MF artifact.** Add `model.3mf` as a fourth export of a BLUECAD build. Use `bd.Mesher(unit=Unit.MM)`. Add one object per `part_id`, in sorted order, with `part_number` = `part_id`. Use fixed tolerances (`linear_deflection=0.001`, `angular_deflection=0.1`, the GLB values) and record them in the manifest. Meshing is from the in-memory kernel shapes, never from re-read files.
2. **Register and serve.** Add `bluecad_3mf` to `EXPORT_ARTIFACT_ROLES` and `_EXPORT_MEDIA_TYPES` (`model/3mf`, `.3mf`). The manifest gains `model.3mf` `sha256` and `bytes`, and `print_handoff`: `{unit: "mm", object_count, objects: {part_id: triangle_count}, linear_deflection, angular_deflection, mesh_digest}`. `mesh_digest` is a SHA-256 over the canonical triangle soup of all objects (vertices rounded to 1e-6 mm, sorted). It is the determinism anchor, because file bytes vary.
3. **Pin lib3mf.** Add `lib3mf` to `requirements.txt` at the version tested (2.5.0), so the writer is not a floating transitive.
4. **189 geometry.** Out of scope for the first delivery. A 3MF for user geometry would be built on the host from the registered, hash-verified `model.stl`, as one object, with a strict bounded binary-STL parser and `lib3mf`. It must never parse the STEP bytes with OCC on the host and never run in the sandbox. This is recorded as a follow-up, not built here. 189 artifacts and routes are unchanged.
5. **Open in slicer.** `POST /workspaces/{workspace_id}/bluecad/artifacts/{artifact_id}/open-in-slicer`. Valid only for a `bluecad_3mf` artifact of that workspace, resolved by the existing `_bluecad_artifact_path` confinement and re-hashed against the registered sha256.
   - Gate 1: a new `Settings.print_handoff_enabled` from `JARVISOS_PRINT_HANDOFF_ENABLED == "1"`, default off. Gate 2: `running_under_wsl()` (moved to a small shared helper, launcher behaviour unchanged). Gate 3: a configured handoff directory `JARVISOS_PRINT_HANDOFF_DIR`, a Windows-reachable `/mnt/<drive>/...` path. If a gate fails, the answer is a typed 409 with a code (`print_handoff_disabled`, `print_handoff_not_wsl`, `print_handoff_dir_unset`). Nothing is copied or launched.
   - Copy the file to `<dir>/<candidate8>-attempt<N>-<sha8>.3mf`. The name is built only from server-held values, never request text. Refuse a symlink target and a path that resolves outside the directory.
   - Convert with `wslpath -w <path>` as an argv list. The result must match `^[A-Za-z]:\\` or the call fails closed.
   - Launch `[explorer.exe, <winpath>]` with `subprocess.run(argv, shell=False, timeout=15, capture_output=True)`. `explorer.exe` is resolved under `/mnt/c/Windows`, as `windows_tool` does. The argv holds exactly one variable item, the converted path.
   - Why `explorer.exe` and not `cmd.exe /c start`: `cmd.exe` re-parses its command line, so a quote or `&` in a path is an injection surface even without a shell on the Linux side. `explorer.exe <file>` opens the file through the association with no command parser. The filename charset above also excludes such characters.
   - `explorer.exe` often returns exit code 1 on success. Success is therefore "process started, no timeout", not the exit code. The result is reported as "handed to Windows", never as "opened".
6. **Record the handoff.** Append a `print_handoff_events` row (workspace, artifact id, sha256, handoff path, Windows path, time, outcome). The response returns the same. No other state changes. The table is created additively with its own `*_MIGRATION_RECORD`, following [028](028-additive-migration-discipline.md).
7. **GUI.** The BLUECAD candidate view gains Download 3MF (always, once built) and, only when the backend reports handoff available, "Open in slicer". The button states that the Windows default program for `.3mf` will open the file.
8. **No new authority.** No network, no printer, no credentials, no URL scheme, no slicer CLI, no Bambu metadata in the 3MF.

## Residual risk

The Windows file association runs whichever program the user set for `.3mf`. That is the user's local choice and is outside JarvisOS. Mitigations: opt-in flag, one fixed binary, one validated path, timeout, an audit row, a user-visible label. A hostile model file would reach the user's slicer. The 3MF is written by JarvisOS from validated geometry, so this does not widen what the user already opens by hand.

## Non-goals

Printer networking, Bambu access codes, cloud, slicing in JarvisOS, G-code, new part kinds, colour or material assignment, `bambu-connect://`, a slicer CLI, 3MF for 189 user geometry (follow-up above).

## Acceptance

1. A built candidate has `model.3mf`. Reloaded with `lib3mf`, the unit is millimeter, there is one object per part, object names equal `part_id`, and the bbox matches `manifest.assembly.bbox_mm` within the deflection tolerance. Volume matches `total_volume_mm3` within 0.5 %.
2. Two builds of one spec give equal `mesh_digest`. The test does not assert equal file bytes, and a comment records the measured byte variance.
3. The manifest `sha256` equals the registered artifact hash. The serve route returns `model/3mf`. Existing STL, STEP and GLB hashes and routes are unchanged.
4. Open endpoint, with `subprocess.run` and `wslpath` mocked: refused when the flag is off, off WSL, or the directory is unset. It refuses a non-`bluecad_3mf` artifact, a foreign workspace, a hash mismatch and a symlinked target. On success the argv is exactly `[explorer.exe, "C:\\..."]`, `shell` is false, and an event row is written.
5. A unit test fuzzes the filename inputs and asserts the Windows path never contains characters outside the fixed charset.
6. Existing BLUECAD export, candidate and 189 suites pass without edits, except the manifest-shape assertion that lists artifacts.

## Required evidence

- Backend tests for criteria 1 to 6. A grep gate: `shell=True` and `cmd.exe` are absent from the new module.
- Real-Chromium GUI proof against a candidate backend that serves `frontend/dist` same-origin (a Vite origin fails PATCH preflight), on a fresh `JARVISOS_DATA_ROOT` bootstrapped with `app.core.bootstrap`: build a candidate, download the 3MF, then with the flag on click "Open in slicer" and see the handoff row and path. Flag off: the button is absent and the endpoint answers 409.
- Host proof on the WSL qualification host with the flag on: `explorer.exe` starts on the handed-off path and the event row is written. If a `.3mf` association exists, record the program and version that opened the file, and confirm it shows mm size and one object per part. Maintainer confirmation in Bambu Studio is welcome. It is not a merge gate, because the association is outside JarvisOS.
