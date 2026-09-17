# Area C file-audit durable progress

This is a temporary Area-C audit-progress shard for issue #656 while the canonical machine-scannable ledger remains in `C-engineering-bluecad-process.md`. Every row here is backed by an actual fresh-master content read and must be folded into that canonical ledger before `MAPPING_STATUS: COMPLETE`.

Fresh-tree baseline: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

| path | status | one-line role/reason |
|---|---|---|
| `backend/app/modules/runner/examples/batch_growth.py` | READ | Deterministic runner demonstration implementing bounded exponential biomass growth, finite/nonnegative inputs, a <=10,000-step grid, CSV timeseries artifact and schema-v1 result; explicitly not qualified PBR biology authority. |
| `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_v0.py` | READ | Reviewed 047 M0 geometry/hydraulics executable: strict nine-input unit envelope, finite/domain checks, OD>=ID, tube/inventory geometry, Reynolds, qualified Darcy friction regimes, pressure/head and pump-power outputs with fail-closed correlation limits. |
| `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_v0.contract.json` | READ | Schema-v1 forward input contract freezing the nine 047 geometry, operating, fluid-property, loss and pump-efficiency variables with units and numeric domains. |
| `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_semantic_v0.contract.json` | READ | Schema-v3 semantic 047 contract adding model-family/tube-run applicability, physical dimensions/property groups and explicit caller-owned versus part-owned engineering semantics. |
| `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_process_kernel_v1.py` | READ | Thin exact-process-kernel executable boundary: requires the exact EXPECTED_UNITS key set, finite numeric values and exact units, rejects extra fields, delegates to execute_047_process_kernel, maps kernel failures deterministically, and emits canonical finite JSON. |
| `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_process_kernel_v1.contract.json` | READ | Schema-v2 forward contract for the exact 047 process-kernel profile, freezing nine required variables with physical dimensions, units, categories and numeric domains. |
| `backend/app/modules/runner/examples/bluerev_biomass_nutrients_harvest_v0.py` | READ | M0 biomass/nutrient/harvest screening executable: validates strict units/domains and evidence bindings, computes biomass inventory/productivity, elemental incorporation and stock dosing, gas-equivalent benchmarks, side-stream harvest/filter sizing, mass-balance closure, and pump-electricity-only partial economics with explicit exclusions. |
| `backend/app/modules/runner/examples/bluerev_biomass_nutrients_harvest_v0.contract.json` | READ | Schema-v1 forward contract freezing 20 required plus optional product-price variables, including physical fractions, annual/daily time bounds, harvest recovery, filtration basis and explicit M0 productivity/gas-rate semantics. |

UNACCOUNTED_FILES: >0

Next: fold these rows into the canonical explicit ledger, continue remaining runner examples/contracts/tests, then fresh-tree set-difference across all Area C owned paths.