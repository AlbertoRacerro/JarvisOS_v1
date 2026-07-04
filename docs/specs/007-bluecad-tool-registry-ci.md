# 007 — BLUECAD tool registry, health checks, CI license-boundary gate

Status: ready (independent — can run in parallel with 005)
Depends on: none

## Goal

After this slice, external tools (gmsh, ccx, …) can only be invoked through a
schema-validated registry (`configs/bluecad_tools.yaml`) with exact version
pins and binary hashes; a CLI health check reports tool availability; and CI
enforces the license boundaries mechanically (no GPL imports in-process, no
`in_process` mode for boundary-C/D tools).

## Why

`BLUECAD_TOOLING_AND_LICENSING.md` boundary rules are hard invariants; this
slice turns them from prose into fail-closed machinery (registry) and CI
assertions. 008/009 subprocess adapters build on the runner functions here.
Also closes assumption A7's tracking half (each entry carries its license
verification date).

## Scope

In scope:
- `schemas/bluecad_tool_registry_v0_1.schema.json` per
  `BLUECAD_CORE_DESIGN.md` §1, plus field `license.verified_date`
  (ISO date the LICENSE was last checked against the pinned version).
- `configs/bluecad_tools.yaml` initial content: `build123d` (in_process,
  Apache-2.0) and placeholder-free entries for `gmsh` and `calculix` with
  `entrypoint: null` and `enabled: false` — enabling a subprocess tool
  requires filling `entrypoint`, `binary_sha256`, `provenance_url`.
- `backend/app/modules/bluecad/registry.py`:
  - `load_registry()` — schema-validate, reject duplicates/unknown fields.
  - `resolve_tool(tool_id)` — returns entry only if `enabled` and, for
    subprocess/container modes, verifies the binary file's SHA-256 against
    `binary_sha256` at resolve time; any mismatch → structured
    `TOOL_HASH_MISMATCH` error. Fail-closed: unknown id, disabled, or
    unhashed subprocess tool → error, never a fallback.
  - `run_tool(tool_id, args, cwd, timeout)` — the ONLY subprocess launcher
    for registry tools (list-args, `shell=False`, captured output, timeout,
    minimal env). 008/009 must use it.
- CLI: `python -m backend.app.modules.bluecad.registry check` — prints per
  tool: enabled, hash status, health-check command result; exit 0 only if
  all *enabled* tools pass.
- CI (`.github/workflows/ci.yml`, additive steps):
  - License-boundary grep: fail if `backend/app` or `frontend/src` contains
    `import gmsh`, `from gmsh`, `import FreeCAD`, `import calculix`
    (word-boundary regex; allowlist: none).
  - Registry consistency test (pytest, not grep): every entry with
    `license.boundary in {C, D}` has `integration_mode != in_process`;
    schema-validates the shipped yaml.

Out of scope (binding non-goals):
- No gmsh/ccx invocation logic (008/009); no downloading of binaries.
- No changes to the sandboxed runner.
- No generalization into a system-wide tool registry (module-scoped is
  deliberate; revisit post-alpha).

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `schemas/bluecad_tool_registry_v0_1.schema.json` (new)
- `configs/bluecad_tools.yaml` (new)
- `backend/app/modules/bluecad/registry.py` (new; if 005 has not created the
  module yet, create the package minimal — no conflict, report it)
- `backend/tests/bluecad/test_registry.py` (new)
- `.github/workflows/ci.yml` (additive steps only)

## Design constraints

- Registry paths may be absolute Windows paths locally; tests must use
  tmp-path fixture registries and fake executables (a tiny python script) —
  never the real yaml, never real binaries.
- `run_tool` env: pass a minimal explicit env (PATH + PYTHONIOENCODING),
  never the full parent env (secrets hygiene, AGENTS.md invariant 6).
- Hash verification reads the file at `entrypoint`; no caching across calls.
- CI grep step must be resistant to false positives in docs/comments: scope
  to `*.py` under `backend/app` and `*.ts*` under `frontend/src`.

## Acceptance criteria

1. Valid registry loads; duplicate ids, unknown fields, or bad spdx-less
   entries are rejected at load with structured errors.
2. `resolve_tool` on a disabled tool, unknown id, missing binary, or wrong
   hash → structured errors (four distinct codes), never a subprocess spawn.
3. `run_tool` executes a fixture fake tool with args/cwd/timeout and
   captures stdout/stderr; timeout kills and reports `TIMEOUT`.
4. Boundary consistency test fails if a fixture entry sets boundary C with
   `in_process` (negative test), passes on the shipped yaml.
5. CI workflow contains the grep step; a fixture-level test demonstrates the
   regex matches `import gmsh` and does not match `# gmsh is GPL` in a
   comment-only line... (regex matches the import statement form only).
6. `registry check` CLI exit codes: 0 all-enabled-pass, 1 otherwise, with a
   readable table.

## Required tests

- Offline pytest: schema validation, resolve/run paths incl. all negatives,
  hash mismatch simulation (modify fake binary after registering hash),
  boundary consistency, CLI exit codes. No network, no real tools.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.
