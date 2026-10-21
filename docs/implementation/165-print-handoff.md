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

## Host proof (pending)

The required host proof — real `explorer.exe` on the WSL qualification host —
cannot run inside the provider sandbox. On the host, outside the sandbox, from
this branch:

```
cd backend && .venv/bin/python ../scripts/165-print-handoff-host-proof.py /mnt/c/Users/<you>/JarvisOS-print
```

Expected: `open-in-slicer 200` with outcome `handed_to_windows`, and Windows
opening the file with the `.3mf` default program. Record which program opened
it and whether it shows millimetre size and one object per part. Maintainer
confirmation in Bambu Studio is welcome but not a merge gate.
