# Spec 214 C1 parity in the Design shell

Date: 2026-10-23. Scope: [spec 214](../specs/214-design-phase1-skeleton.md) acceptance 3. Both [spec 212](../specs/212-bluerev-c1-tubular-replication.md) C1 layouts are rebuilt in the new shell and the same available capability is re-executed through existing owners. This is the 212 one-condition optical proxy. It is not a 2013 replication and it predicts no productivity.

## Reproduction

[`c1_shell_parity.py`](../../scripts/qualification/214/c1_shell_parity.py) uses an isolated temporary data root. It creates a Design project, opens a fresh version and activates it. In that version's Process draft, it places the horizontal and fence layouts as two `PhotobioreactorT1` units with T2 optics and typed quantities. The inputs come from the pinned 212 setup: 46 mm inner diameter, 3 or 7 loops of 80 m, the 3 × 1 and 1 × 7 representative modules, 0.10 m pitch, 0.425 m tube-centre height, refractive indices of 1.49 and 1.33, and a lower albedo of 0.2. It then opens each unit as a Plant component, reads the stored records back through the existing owners, and runs the Process T2 layout mapping (`dynamic_engine.t2_optics_for_unit`, extracted without behaviour change) and the `optics_t2.v1` kernel under the 212 condition.

Run it from `backend/` with `PYTHONPATH=. python ../scripts/qualification/214/c1_shell_parity.py`. The pinned output is [`c1_shell_parity.json`](../../scripts/qualification/214/c1_shell_parity.json). It was generated with CPython 3.12.3 and NumPy 2.3.5, and two runs were byte-identical. [`test_214_c1_shell_parity.py`](../../backend/tests/test_214_c1_shell_parity.py) pins the comparison.

## Comparison (tolerance: exact)

| Quantity | Horizontal | Fence |
| --- | --- | --- |
| 212 full input digest | `c38e2c85…` (same reference run) | same |
| Layout digest, shell vs 212 recorded setup | `299d44fa…` = `299d44fa…` | `bf9fefe9…` = `bf9fefe9…` |
| Model version | `optics_t2.v1` both | `optics_t2.v1` both |
| Tube cylinder volume from stored records, m³ | 0.398857, Δ = 0 | 0.930665, Δ = 0 |
| Intercepted PAR, µmol s⁻¹ m⁻¹ per tube | 50.3336, Δ = 0 | 49.8004, Δ = 0 |
| Transmitted PAR, µmol s⁻¹ m⁻¹ per tube | 46.4724, Δ = 0 | 45.9893, Δ = 0 |
| Equivalent PAR, µmol m⁻² s⁻¹ | 1101.3223, Δ = 0 | 1089.0296, Δ = 0 |
| Productivity prediction | none, unsupported | none, unsupported |

The "recorded 212 setup" uses the optical diameter that 212 used: the outer diameter, computed as the stored inner diameter plus two 2 mm walls (from the secondary S22 access). The Process model has no outer-diameter field.

## Owner differences found, not hidden

- **Optical diameter convention.** The existing Process T2 owner gives the kernel `tube_inner_diameter` (46 mm). The 212 proxy gave it the 50 mm outer diameter. Through the Process owner, intercepted PAR is 3.88 (horizontal) and 3.80 (fence) µmol s⁻¹ m⁻¹ lower, and equivalent PAR is 3.57 and 4.59 µmol m⁻² s⁻¹ higher. The kernel's wall/diameter convention needs a modelling decision before the two paths can be reconciled. Spec 214 does not change it.
- **Geometry.** The typed Process → BlueCad Deepen mapping applies to both units (46 mm inner diameter, 80 000 mm tube). The deterministic tube template allows at most 5 000 mm, so the handoff is refused with that reason, and no candidate is attached. One loop is not a straight tube. The 212 run had no CAD geometry.
- **Process run.** A periodic-steady or dynamic PBR run still needs a pinned CCAP 211/78 card and time-aligned 2013 DNI/DHI, temperature and harvest inputs. None has been established, so no run was executed. This is the same blocker as in 212.

## Scientific conclusion (unchanged)

The 212 conclusion holds: **qualified inconclusive** for model agreement and orientation causality. Prediction-minus-S01 discrepancy is still **not computable** for both layouts. The missing evidence is unchanged: time-aligned 2013 light, culture temperature, dilution/harvest and biomass data; a primary-source CCAP 211/78 parameter card; verified as-built cross-sections; and a direct S22 check of the outer diameter and spacing. The shell rebuild shows reproducibility of the declared proxy. It does not show scientific validity.
