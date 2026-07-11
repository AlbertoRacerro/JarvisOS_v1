# Spec 056 — BLUECAD property-based geometry testing and determinism canary

## Outcome

Implementation PR: #88.

The slice adds a bounded offline regression net around the public
`build_geometry_spec` entry point. It does not modify production CAD builders,
GeometrySpec schema, runtime dependencies, provider routes, solver adapters, or
frontend code.

## Implemented surface

- exact development pin `hypothesis==6.156.6`;
- deterministic Hypothesis profile `bluecad_property_ci`;
- valid-by-construction strategies for one `tube_run`, two compatible connected
  `tube_run` parts, and one `float`;
- shared invariant harness over the real adapter path and fresh temporary roots;
- same-environment full-manifest and STEP/STL/GLB hash repeatability;
- four-fixture canonical Linux digest canary;
- dedicated `ubuntu-24.04` / Python 3.11 CI job with a 240-second hard ceiling;
- checked-in profile and digest metadata under
  `backend/tests/bluecad/fixtures/property_geometry/expected.json`.

## Bounded execution

The canonical suite performs exactly:

- 20 generated invariant builds;
- 18 generated repeatability builds;
- 8 fixed canary builds;
- 46 full adapter builds total.

The reviewed bootstrap run completed in 132.24 seconds, below the 240-second
limit.

## Canonical profile

- profile ID: `ubuntu24-py311`;
- operating system: Linux on GitHub `ubuntu-24.04`;
- architecture: `x86_64`;
- Python: 3.11;
- build123d: 0.11.1;
- OCP distribution: `cadquery-ocp-novtk`;
- OCP version: 7.9.3.1.1.

## Initial canary baseline

| Fixture | Spec ID | Manifest digest |
| --- | --- | --- |
| `minimal_single_tube.json` | `sha256:bd04044e65c001b9911ce7adbc5e18b64618b0002f2fa25af5f34c1912a05050` | `19b5f925b8d9fd2a3b837177958a68abf3256fba3d5bb44c31253603dd0729f4` |
| `chain_tube_bend_joint.json` | `sha256:155ec1b90a0cbe47c6ce0821360f838504695057f8a1bc0b1cf9a67b2851367f` | `88b0d778047f662d38fb4ee91440c05ae160bacc59e7c570c9a99dc22d3f87cd` |
| `u_shape_two_bends.json` | `sha256:5178bfeb841266749e2df7bec3fa777a27a236d31e2e9b232ee6b8944869e14f` | `73d951bb102e93d45392dc8defc3b580cdd932773b878f2a6aab5cc306e217db` |
| `property_geometry/minimal_float.json` | `sha256:7631c98b0cb478cc1a879200a577ef140c63d887c484bfbf65efaff7951b51b9` | `cd5ab4daca78410797c8e12451263eae7e31e17f175899c5712c3bc4eefa0230` |

All previous values were `TBD`; this PR establishes the first reviewed baseline.
There is no automatic baseline update command or CI write-back.

## Failures found during implementation

No production CAD defect was found.

The initial metadata location
`backend/tests/bluecad/fixtures/property_geometry_expected.json` collided with a
historical golden test that treats every JSON file directly under `fixtures/` as
a GeometrySpec and derives a paired `.expected.json` path. This caused two
backend-suite failures even though the property suite and canonical canary were
valid. The metadata was moved to
`fixtures/property_geometry/expected.json`, outside that discovery root. No
invariant, example count, timeout, digest, or CAD output changed.

Temporary Ruff and Pytest diagnostic collection added during root-cause analysis
was removed before final review. The normal backend CI command remains
`python -m pytest -q`.

## Deliberate exclusions

Random Phase 1 generation does not cover bend, joint, manifold, anchor_mount, or
harvest_module. Bend remains present through fixed canary fixtures. Invalid and
adversarial payloads remain assigned to spec 023.

## Authority and non-goals

The suite detects robustness and determinism regressions; it does not certify
engineering correctness. It makes no provider, network, Gmsh, CalculiX, AI,
runner, or candidate-loop call and commits no generated CAD binary.
