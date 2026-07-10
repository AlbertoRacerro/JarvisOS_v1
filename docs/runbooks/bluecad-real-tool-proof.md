# BLUECAD strict real-tool proof

This runbook executes the 021b-A proof with the real Gmsh and CalculiX binaries.
It proves the integrated CAD → mesh → static-FEM → evidence path. It does **not**
prove FEM accuracy; analytic verification remains spec 024.

## Safety boundary

- Use an external operator-owned registry. Do not edit `configs/bluecad_tools.yaml`
  with machine-local paths or hashes.
- The registry must contain exact executable paths, version pins, SHA-256 hashes,
  provenance URLs, and health checks.
- The BLUECAD AI response is supplied by the caller-injected scripted offline
  adapter. No live provider or network route is used.
- Pytest creates an isolated temporary `JARVISOS_DATA_ROOT`; the normal operator
  data root is not touched.

## Prepare the registry

Locate the actual executables and calculate their hashes:

```bash
command -v gmsh
command -v ccx
sha256sum "$(command -v gmsh)" "$(command -v ccx)"
gmsh -version
```

Create a YAML file outside the repository using
`registry_version: bluecad_tool_registry_v0_1`. Enable only the tools being
proved. Gmsh and CalculiX must remain subprocess integrations with license
boundary `C`. Example fields for each tool:

```yaml
id: gmsh                 # or calculix
kind: mesher             # or fem_solver
integration_mode: subprocess
version_pin: "<exact version>"
enabled: true
entrypoint: "<absolute executable path>"
binary_sha256: "<64 hex characters>"
provenance_url: "<operator-recorded source>"
health_check: "<same executable path> <operator-owned health arguments>"
```

Gmsh may use `-version`. CalculiX 2.21 does not provide a reliable zero-exit
version-only command in every package build; use a minimal valid static deck in
the registry directory and set the health check to `<ccx-path> <deck-basename>`.
The dedicated GitHub workflow creates and solves such a tetrahedron deck.

## Check the registry

```bash
export JARVISOS_BLUECAD_TOOL_REGISTRY=/absolute/path/bluecad-tools.yaml
cd backend
python -m app.modules.bluecad.registry check
```

The command must report `hash=ok` and `health=ok` for both tools. A missing
binary, hash mismatch, invalid license boundary, or failing health check returns
nonzero.

## Ordinary versus strict execution

Ordinary development/CI remains skip-capable:

```bash
cd backend
python -m pytest -q tests/bluecad/test_alpha_real_tools.py
```

When tools are unavailable, this command records a pytest skip. A skip is not an
alpha proof.

Strict execution converts the same condition into failure:

```bash
cd backend
python -m pytest -q tests/bluecad/test_alpha_real_tools.py \
  --require-bluecad-real-tools
```

The command exits zero only after two equivalent real-tool runs complete with:

- valid geometry and one successful attempt each;
- non-empty Gmsh mesh with required BODY/BC/LOAD groups;
- successful native CalculiX FRD parsing and finite displacement/stress maxima;
- completed simulation rows with passing mesh/FEM verdicts;
- linked validation, mesh, and FEM evidence;
- registered artifact hashes matching the files;
- byte-identical canonical manifests;
- a bounded JSON proof containing the resolved entrypoints, versions, and binary
  hashes.

GitHub Actions runs the same strict command in
`.github/workflows/bluecad-real-tool-proof.yml` using an external registry built
from the runner's installed packages. The workflow also runs the complete offline
backend test suite and uploads bounded text diagnostics plus the final proof JSON.

## Determinism boundary

The canonical manifest excludes elapsed runtime. It retains STEP/STL/GLB hashes
and sizes as integrity evidence. Open Cascade writes the wall-clock export time
into the STEP `FILE_NAME` header, so BLUECAD normalizes only that header timestamp
to `1970-01-01T00:00:00` immediately after export. Geometry data, entity ordering,
and all other STEP content remain untouched. A missing or ambiguous header fails
as `EXPORT_ERROR` rather than silently weakening the manifest.

CalculiX input uses a relative mesh include path. This avoids its fixed input-line
limit without copying or duplicating the canonical mesh artifact.

## Interpreting failures

- **Skip without strict flag:** expected when tools are unavailable; not proof.
- **Registry failure:** fix the operator registry or tool installation. Do not
  weaken hash/license checks.
- **Mesh group failure:** inspect `mesh.geo`, `mesh.inp`, and `gmsh.log`; do not
  substitute fake groups.
- **Solver input failure:** inspect `analysis.inp` and `analysis.log`. Keep mesh
  includes relative; do not shorten the test data root to hide a line-length bug.
- **FRD parse failure:** preserve the real `.frd` artifact and fix the narrow
  public-format parser; do not make the real solver emit the fake fixture format.
- **Manifest mismatch:** compare artifact hashes first. Runtime duration is outside
  the manifest; STEP header time is normalized, while every geometry artifact hash
  remains binding integrity evidence.
- **Tier 3 failure:** the integration proof failed. Accuracy and tolerance tuning
  belongs to spec 024, but a failing result cannot be represented as green.
