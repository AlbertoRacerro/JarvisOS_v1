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
ccx -v
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
health_check: "<same executable path> -version"
```

For CalculiX, use the executable's supported version switch, commonly `-v`.

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
from the runner's installed packages.

## Interpreting failures

- **Skip without strict flag:** expected when tools are unavailable; not proof.
- **Registry failure:** fix the operator registry or tool installation. Do not
  weaken hash/license checks.
- **Mesh group failure:** inspect `mesh.geo`, `mesh.inp`, and `gmsh.log`; do not
  substitute fake groups.
- **FRD parse failure:** preserve the real `.frd` artifact and fix the narrow
  public-format parser; do not make the real solver emit the fake fixture format.
- **Manifest mismatch:** investigate semantic manifest drift. Runtime duration and
  binary serializer hashes are intentionally outside the canonical manifest.
- **Tier 3 failure:** the integration proof failed. Accuracy and tolerance tuning
  belongs to spec 024, but a failing result cannot be represented as green.
