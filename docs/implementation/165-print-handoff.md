# 165 — BLUECAD print handoff: implementation evidence

Spec: [165](../specs/165-bluecad-print-handoff.md). Implementation lane `k165`
(2026-10-15), recovered and rebased onto master `a5a7f9bd` on 2026-10-21 in
roadmap continuation cycle 3. The audit table migration was renumbered to
`0025_print_handoff_events`, because master had taken `0024` for spec 194.

## What changed

- `model.3mf` is the fourth BLUECAD export: `build123d.Mesher(unit=MM)`, one
  mesh object per `part_id` in sorted order (name and part number equal the
  part id), GLB tolerances (0.001 / 0.1 rad), meshed from in-memory shapes.
- Manifest `print_handoff` block: unit, object count, triangle count per
  object, tolerances and `mesh_digest` (SHA-256 over the canonical triangle
  soup, vertices rounded to 1e-6 mm, sorted).
- The only byte variance measured on lib3mf 2.5.0 is the random `p:UUID`
  values in `3D/3dmodel.model`. They are rewritten to deterministic UUIDv5
  values and zip timestamps are fixed. Two separate GUI builds on two fresh
  backends produced the same 10 674-byte file (SHA-256 `a672b8ac…`). The
  tests still anchor determinism on `mesh_digest`, as the spec requires.
- `bluecad_3mf` is registered, served as `model/3mf` and listed in the
  candidate aggregate exports. `lib3mf==2.5.0` is pinned.
- `GET …/bluecad/print-handoff/capability` and
  `POST …/bluecad/artifacts/{id}/open-in-slicer` behind three gates
  (`JARVISOS_PRINT_HANDOFF_ENABLED=1`, WSL, a `/mnt/<drive>/…`
  `JARVISOS_PRINT_HANDOFF_DIR`), each refused with a typed 409. The file is
  copied under a server-built name with its hash re-verified during the copy,
  replaced atomically, converted with `wslpath -w` (must match `^[A-Za-z]:\`
  and a forbidden-character check), and handed to
  `[/mnt/c/Windows/explorer.exe, <winpath>]` with `shell=False` and a 15 s
  timeout. A `PATH` fallback is accepted only if it resolves to
  `/mnt/<drive>/Windows/explorer.exe`. Every attempt writes a
  `print_handoff_events` row. The response says "handed to Windows", never
  "opened".
- GUI: the Export menu gains Download 3MF, and Open in slicer only when the
  backend reports the capability, labelled "The Windows default program for
  .3mf will open this file".

## Verification at the PR head

- `tests/bluecad/test_print_handoff_165.py`: 12 tests for acceptance 1–6
  (mm unit, one object per part, bbox within deflection, volume within 0.5 %,
  equal `mesh_digest`, manifest hash equals registered hash, `model/3mf`
  serving, all gates, foreign workspace, wrong type, hash mismatch, symlink,
  hard-link non-overwrite, wslpath result validation, filename charset fuzz,
  and the `shell=True` / `cmd.exe` grep gate).
- `tests/bluecad` and `tests/test_foundation_contracts.py`: 517 passed,
  22 skipped. Full backend suite: 4420 passed, 43 skipped; the only failure,
  the spec 028 CREATE-only digest, is resolved by reviewing the new table
  (`print_handoff_events` is a new table, not a new column on an old one;
  the digest of all other CREATE-only columns is unchanged). 17 errors in
  `test_devctx.py` / `test_coding_control_room_164.py` came from the sandbox
  ASCII locale and pass under `LANG=C.UTF-8`.
- ruff, architecture enforcement, frontend contract generation and the
  typecheck ratchet (301 ≤ 310) pass. `npm run build` passes.
- BLUECAD geometry canary: every pinned `manifest_digest` changes because
  each manifest now lists `model.3mf` and the `print_handoff` block. The four
  new digests are taken from the CI canonical-profile run; the fixtures'
  `spec_id`s and profile are unchanged, and the STL, STEP and GLB bytes of all
  four fixtures were checked byte-identical between master and this branch.
- CI core shard: `test_devctx.py` failed once it was rebalanced into a shard
  whose earlier tests leave an ASCII locale. `scripts/devctx.py` now decodes
  git output as UTF-8 and the test writes its fixtures as UTF-8 (verified
  with `LC_ALL=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0`).

## Real Chromium GUI proof

Playwright 1.55.0 with cached Chromium 1187 drove two fresh backends that
served the built `frontend/dist` same-origin (`VITE_API_BASE_URL=`), each on a
new `JARVISOS_DATA_ROOT` bootstrapped with `app.core.bootstrap`.

- Flag off: the GUI built the tube template, Download 3MF saved a valid zip;
  capability `print_handoff_disabled`; Open in slicer absent; the endpoint
  answered 409 `print_handoff_disabled`.
- Flag on: clicking Open in slicer showed
  `Handed to Windows: C:\Users\proof\JarvisOS-print\<cand8>-attempt1-a672b8ac.3mf`.
  The handoff copy had the downloaded file's SHA-256 and one
  `print_handoff_events` row with outcome `handed_to_windows` was written.

The provider sandbox hides `/mnt/c`, `wslpath` and WSL interop, so the
flag-on run replaced only the Windows boundary in a proof launcher outside the
repository: WSL detection, the drive-path pattern (to accept a scratch
directory), `wslpath` and the `explorer.exe` call. Each boundary call was
recorded: `["wslpath","-w",<path>]` and
`["/mnt/c/Windows/explorer.exe","C:\\…"]`, both with `shell=false`. Product
routes, copy, hashing and the audit row ran unmodified. Screenshots:
[flag on](evidence-165/flag-on-handed.png), [flag off](evidence-165/flag-off-menu.png).

## Host proof (WSL qualification host)

Run on 2026-10-22 on the trusted WSL host, outside jarvis-sandbox, by the maintainer's direct host session (mandate `L20261022085842-e05d`). Code: PR head `3a3d47ad7bab396bbab6cc34ee8a5ac4fba7ca6a`. The handoff module, the route and the proof script were reviewed before running. The environment was scrubbed (`env -i`, temporary `HOME`, only `PATH`, `LANG`, `WSL_INTEROP` and `WSL_DISTRO_NAME` kept), and `JARVISOS_DATA_ROOT` was a fresh temporary directory.

```
cd backend && env -i HOME=<tmp> PATH=... WSL_INTEROP=... WSL_DISTRO_NAME=... \
  ~/src/JarvisOS_v1/backend/.venv/bin/python ../scripts/165-print-handoff-host-proof.py /mnt/c/Users/thera/JarvisOS-print
```

- `09:07:03Z` capability `{'available': True, 'code': None}` (flag on, WSL, directory set).
- Tube template candidate `1bef7bdb-…` built. Its `bluecad_3mf` artifact `3c64bea3-…` was found among the exports.
- `09:07:08Z` `POST …/open-in-slicer` → `200`, event row `a122dd73-b273-40e0-b0ba-60c0ddfc0693`, outcome `handed_to_windows`, `handoff_path` `/mnt/c/Users/thera/JarvisOS-print/1bef7bdb-attempt1-a672b8ac.3mf`, `windows_path` `C:\Users\thera\JarvisOS-print\1bef7bdb-attempt1-a672b8ac.3mf`. The script exited 0.
- The handed-off file has `sha256 a672b8ac872f49a38dd3a1622d1df22cf72e39f1d2fe33a15ebe21bf022c96d0` (10674 bytes). This equals the registered artifact hash in the event row.
- Windows process table, read afterwards: `explorer` and `OpenWith` started at 11:07:08 local (09:07:08Z), together with `smartscreen`.

**Association: none.** `assoc .3mf` reports no association. The per-user `UserChoice` points to an AppX handler (`AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg`) that is no longer installed. No Bambu Studio, OrcaSlicer, PrusaSlicer, Cura or 3D Viewer is installed. Windows therefore showed its "choose an app" dialog (`OpenWith.exe`).

This meets the spec's required host evidence: `explorer.exe` starts on the handed-off path and the event row is written. **No slicer opened the file**, so mm size and one object per part were not confirmed in a slicer; the spec makes that conditional on an existing association and not a merge gate. Nothing was printed.

## Independent review (2026-10-22)

Codex, read-only, at exact head `11b7241824819d3a673bb07571d4e866ceedc2cd` against master `260ed2a6`. It reran `tests/bluecad/test_print_handoff_165.py` (12 passed), `tests/bluecad` (398 passed, 22 skipped), migration/189/foundation contracts (146 passed) and ruff. In fresh processes, the STL, STEP and GLB hashes of four canonical fixtures matched master byte for byte. It found no defect in the feature-off, off-WSL and unset-directory refusals, workspace scoping, artifact type and provenance checks, filename charset, fixed `explorer.exe` argv, `shell=False` or the additive migration.

**Finding (reported P1, dispositioned P2, not merge-blocking): handoff path TOCTOU.** `print_handoff.py` resolves the handoff directory once, then uses pathnames again. A process that can write the handoff directory or its parent could swap in a symlinked directory before the copy, or replace the copied file before Explorer opens it. Both interleavings were reproduced with Linux filesystem operations and a mocked Windows boundary. The audit row would then record the registered hash for bytes that Explorer did not open.

**Disposition.** The only writers of `/mnt/c/Users/thera/JarvisOS-print` and its ancestry are the same Windows/WSL user that runs the backend and launches Explorer. Agents in `jarvis-sandbox` cannot see `/mnt/c` at all (spec 201). Exploiting the race therefore needs a process that already holds the user's privileges, so no privilege boundary is crossed. It does not violate a spec 165 acceptance item. The hardening is tracked as a follow-up: descriptor-anchored, no-follow copy and replace, and a re-verified identity before launch. The audit wording stays "registered artifact handed to Windows", not "bytes opened by the slicer".
