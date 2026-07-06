# 016 — RUNNER-EXT-1: scoped runner extension for BLUECAD L2

Status: implemented (pending review)
Depends on: 005 (BLUECAD CAD adapter MVP), 010 (BLUECAD AI loop v0). Blocks: 012 (BLUECAD L2 script execution).

## Goal

After this slice, the existing local Python runner can register and execute one
additional implementation kind, `bluecad_l2_v0`, for bounded BLUECAD L2
build123d scripts supplied as script text. The path preserves existing
`batch_growth_v0` behavior byte-for-byte while adding GeometrySpec v0 input
validation, CAD artifact output validation, script hashing, and stronger
LLM-script preflight policy for the new kind only.

## Why

BLUECAD L2 needs a narrow bridge between AI-proposed parametric CAD code and the
JarvisOS-owned execution/audit spine. The current runner already owns local
script storage, SHA checks, run directories, cleared subprocess environments,
logs, and artifact persistence, but it only supports the bundled
`batch_growth_v0` example and uses a textual denylist. This slice extends that
runner in the smallest possible way so future BLUECAD L2 work can execute
scripted CAD proposals without broadening tools, agents, providers, or frontend
surface area.

## Scope

In scope:
- Add `implementation_kind = "bluecad_l2_v0"` alongside the existing
  `batch_growth_v0` path.
- For `bluecad_l2_v0` registration only, accept caller-supplied Python script
  text, store it under the existing model implementation data-root location,
  compute SHA-256 with the existing artifact hash machinery, insert the script
  artifact, and link it from the model version as the existing runner does.
- Preserve `batch_growth_v0` registration semantics exactly: it still rejects
  arbitrary script text and still copies/uses the bundled batch-growth script.
- For `bluecad_l2_v0` job creation and execution, validate `input.json` as a
  GeometrySpec v0 payload accepted by the spec-005 schema/module.
- For `bluecad_l2_v0` successful output, require the spec-005 artifact set:
  `model.step`, `model.stl`, `model.glb`, `manifest.json`, plus `result.json`.
  `result.json` must declare these artifacts so existing run-artifact
  persistence records them with CAD-specific roles.
- Keep the existing textual denylist and add AST-based import allowlist checks
  for `bluecad_l2_v0` scripts before execution.
- Map every textual policy or AST allowlist failure for `bluecad_l2_v0` to
  error type/code `SANDBOX_VIOLATION`, and make that failure non-retryable for
  the owning BLUECAD candidate when consumed by later L2 orchestration.
- Add regression coverage proving `batch_growth_v0` externally observable
  behavior is byte-identical.

Out of scope (binding non-goals):
- No implementation of spec 012 orchestration, candidate repair logic, or any
  AI generation loop changes.
- No new provider calls and no AI execution path changes.
- No new tools/agents framework, MCP servers, background workers, streaming, or
  frontend work.
- No OS-level sandboxing, containers, job objects, seccomp, firejail, network
  namespaces, or dependency isolation in this slice.
- No generic arbitrary Python runner; `bluecad_l2_v0` is a BLUECAD-only kind
  with a fixed input/output contract.
- No schema redesign of existing runner/modeling/artifact tables beyond
  additive fields if reality proves they are required.
- No changes to `batch_growth_v0` output schema, input validation rules, route
  behavior, status strings, log format, artifact rows, or bundled script.

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `backend/app/modules/runner/models.py`
- `backend/app/modules/runner/service.py`
- `backend/app/modules/runner/safety.py`
- `backend/app/modules/runner/local_python.py` only if needed to thread the
  new kind without changing subprocess behavior
- `backend/app/core/schema.py` only if an additive runner/model version field is
  unavoidable
- `backend/tests/runner/test_*bluecad_l2*.py` (new)
- Existing runner tests for `batch_growth_v0` regression coverage

## Design constraints

- Honest isolation statement (verbatim):

  > current runner isolation is not OS-level sandboxing; it is scoped scripts,
  > input validation, textual+AST checks, and a cleared environment. It must
  > not be described as network-secure. Stronger isolation
  > (job objects/containers) is a future, separate decision.
- `batch_growth_v0` is the regression anchor. Its behavior must remain
  byte-identical from the perspective of API responses, DB rows, copied script
  bytes, SHA-256 values, input validation failures, successful result payloads,
  logs, artifact declarations, and error/status strings.
- The `bluecad_l2_v0` script source is an artifact, not executable mutable
  state. Job creation and execution must both continue to reject script bytes
  whose current SHA-256 differs from the stored artifact hash.
- All new runtime paths continue to use data-root helpers from
  `backend/app/core/paths.py`; runtime data must not be written into the repo.
- The existing path constraints remain in force: implementation scripts stay
  under `model_implementation_root(workspace_id)`, run files stay under
  `run_root(workspace_id, simulation_run_id)`, and declared artifacts are
  relative paths under the run output directory.
- Subprocess execution remains `shell=False`, timeout-bounded, stdout/stderr
  bounded, and launched with the current cleared environment behavior. Do not
  weaken the environment clearing or add ambient secrets.
- Policy checks are fail-closed: unparseable Python source, unknown import form,
  dynamic import, or any import outside the allowlist is a
  `SANDBOX_VIOLATION`.
- Keep the textual denylist for both implementation kinds unless preserving
  byte-identical `batch_growth_v0` requires leaving its exact call path
  untouched; in either case, `bluecad_l2_v0` must run both textual denylist and
  AST allowlist checks.
- AST import allowlist for `bluecad_l2_v0`:
  - third-party/project modules allowed: `build123d` only;
  - stdlib modules allowed: `collections`, `dataclasses`, `decimal`, `enum`,
    `functools`, `itertools`, `json`, `math`, `operator`, `pathlib`,
    `statistics`, `typing`;
  - submodules are allowed only under an allowed root when explicitly safe for
    that root (for example `typing` names and `collections.abc`); do not allow
    `importlib`, `os`, `sys`, `subprocess`, `socket`, `urllib`, `http`,
    `httpx`, `requests`, filesystem mutation helpers, environment access, or
    any secret-related module/name.
- AST checks must inspect both `import x` and `from x import y`. Relative
  imports, star imports, `__import__`, `importlib`, `eval`, `exec`, and dynamic
  code loading are rejected.
- Output contract for `bluecad_l2_v0` successful runs:
  - `result.json` exists, is a JSON object, and declares at least the roles
    `bluecad_step`, `bluecad_stl`, `bluecad_glb`, `bluecad_manifest`;
  - declared paths point to existing files under the run output directory;
  - required filenames are `model.step`, `model.stl`, `model.glb`, and
    `manifest.json` unless spec 005 established different exact names;
  - artifact size and path checks use existing runner validation;
  - the manifest/result payloads must not expose absolute paths outside the
    data root.
- Input contract for `bluecad_l2_v0` successful job creation:
  - input set is accepted by GeometrySpec v0 validation from spec 005;
  - invalid GeometrySpec payloads fail before a runner job is queued.
- `SANDBOX_VIOLATION` must be distinguishable from normal script runtime
  failure, validation failure, timeout, and artifact validation failure in
  runner responses/logs so spec 012 can park candidates without retrying.
- Do not duplicate BLUECAD schema validation logic if spec 005 exposes an
  importable validator; reuse it. If no reusable validator exists, stop and
  report the conflict rather than inventing a parallel schema.

## Acceptance criteria

1. `create_model_implementation(..., implementation_kind="bluecad_l2_v0", script_text=...)`
   stores the provided script bytes under the workspace model implementation
   data-root path, records a `python_script` artifact with the correct SHA-256,
   and links that artifact from the created model version.
2. `batch_growth_v0` registration still copies the bundled script and ignores or
   rejects caller script text exactly as before; a golden regression test proves
   the copied bytes, SHA-256, returned fields, and relevant DB rows match the
   pre-change baseline.
3. Creating a `bluecad_l2_v0` runner job with a valid GeometrySpec v0 queues a
   job and writes `input.json` in the existing run-root layout.
4. Creating a `bluecad_l2_v0` runner job with invalid GeometrySpec data fails
   before queueing a job and does not write run artifacts.
5. Running a safe `bluecad_l2_v0` script that imports only allowlisted modules
   and writes `model.step`, `model.stl`, `model.glb`, `manifest.json`, and
   `result.json` completes successfully and persists run artifacts with the
   expected BLUECAD roles and SHA-256 values.
6. A `bluecad_l2_v0` script containing forbidden textual markers, disallowed
   imports (`os`, `sys`, `subprocess`, `socket`, `requests`, `httpx`, `urllib`,
   `importlib`, etc.), relative imports, star imports, `__import__`, `eval`, or
   `exec` is rejected before subprocess execution with `SANDBOX_VIOLATION`.
7. A `bluecad_l2_v0` script whose current bytes differ from the stored artifact
   SHA is rejected at both job creation and execution, matching the existing
   tamper-check pattern.
8. A `bluecad_l2_v0` script that exits successfully but omits any required CAD
   artifact or declares an artifact outside the output directory is marked
   failed with a structured artifact/output validation error, not success.
9. Existing `batch_growth_v0` tests pass unchanged, and an added golden test
   demonstrates byte-identical behavior for successful run output and at least
   one representative validation/policy failure.
10. No test requires network access, live providers, a running Ollama instance,
    or OS-level sandbox features.

## Required tests

- Runner model registration tests:
  - `bluecad_l2_v0` stores caller script text as a hashed artifact;
  - `batch_growth_v0` golden registration behavior remains byte-identical.
- Runner job creation tests:
  - valid GeometrySpec v0 queues successfully;
  - invalid GeometrySpec fails before queueing.
- Runner execution tests:
  - safe allowlisted L2 script succeeds and registers STEP/STL/GLB/manifest
    artifacts via `result.json`;
  - missing required artifact fails;
  - artifact path escape fails using existing path validation.
- Policy tests for the AST allowlist:
  - allowed imports: `build123d`, `math`, `json`, and each explicitly listed
    stdlib module;
  - rejected imports/forms: `os`, `sys`, `subprocess`, `socket`, `requests`,
    `httpx`, `urllib`, `importlib`, relative import, star import,
    `__import__`, `eval`, `exec`.
- Tamper tests proving script SHA mismatch is rejected at job creation and at
  execution.
- `batch_growth_v0` regression tests covering successful run output and a
  representative existing failure path; compare exact response/status/error
  payloads and relevant persisted values, excluding nondeterministic ids and
  timestamps only.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.

## Implementation notes

- Status updated after implementing `bluecad_l2_v0` registration, job creation, execution output validation, script hashing/tamper checks, and AST import allowlist policy on the scoped runner path.
- Added additive `implementation_kind` fields on `model_versions` and `runner_jobs` so the existing `batch_growth_v0` path can dispatch without changing its externally observable behavior.
- Reused `backend/app/modules/bluecad/spec.py` GeometrySpec v0 validation for `bluecad_l2_v0` input validation; invalid specs fail before runner jobs are queued.
- Honest isolation statement (verbatim):

  > current runner isolation is not OS-level sandboxing; it is scoped scripts,
  > input validation, textual+AST checks, and a cleared environment. It must
  > not be described as network-secure. Stronger isolation
  > (job objects/containers) is a future, separate decision.

- No OS-level sandboxing, provider path, frontend, tools/agents, or `batch_growth_v0` output-schema changes were implemented.
