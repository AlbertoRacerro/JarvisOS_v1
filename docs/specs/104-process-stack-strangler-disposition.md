# 104 PROCESS-STACK-STRANGLER-1 — executed disposition

Input: the 103 role matrix and incumbent disposition in `docs/specs/103-process-upstream-bakeoff-evidence.md`.

## Switched to upstream owners

`backend/app/modules/process_stack/` holds the upstream owners new process work must use instead of new custom solver code. Evaluators implement the frozen 106 `EngineeringEvaluator` boundary: descriptor, truthful import-based availability, and typed results for success, refusal, deadline, mismatch and upstream crashes.

| Role | Owner | Boundary |
| --- | --- | --- |
| Pure-fluid properties (Water, CO2, N2, O2, Air) | CoolProp 8.0.0, `coolprop.pure_fluid_properties` | Single-phase only. States outside CoolProp's own `Tmin`/`Tmax`/`pmax` are refused as `outside_validity_domain`, because CoolProp returns extrapolated numbers there without raising (observed: water at 5000 K). |
| Pipe friction / pressure drop | fluids 1.3.1, `fluids.pipe_pressure_drop` | Clamond solution of Colebrook for turbulent flow and 64/Re for laminar flow. The transitional regime (2040 ≤ Re < 4000) and e/D > 0.05 are refused. Screening fidelity. |
| Internal convection | ht 1.2.0, `ht.internal_convection` | Gnielinski (3e3 ≤ Re ≤ 5e6, 0.5 ≤ Pr ≤ 2000) or Dittus-Boelter heating/cooling (Re ≥ 1e4, 0.6 ≤ Pr ≤ 160). Out-of-range inputs are refused. Screening fidelity. |
| ODE time integration | SUNDIALS CVODE via scikit-sundae 1.1.3, `integrate_ode` | Single time/state owner. Models supply only `rhs(t, y)`. Discrete actions are applied between integration segments, never by a second integrator. Solver failure returns `success=False` with the native message and no states. |

Inputs convert through the single Pint owner (`process_kernel.units`), so offset temperatures such as °C are handled. Unknown inputs or options are refused, not ignored. `available` and `converged` never mean qualified; no 102 qualification record is created here.

Tests pin the owners to the independently recorded 103 results. They cover CoolProp water density, fluids pressure drop and its −0.948% difference from the 047 Blasius incumbent, the Dittus-Boelter Nusselt number measured on both WSL2 and Windows, and the 48 h day/night CVODE endpoint. The four packages are pinned in `backend/requirements.txt`. The 103 Windows 11 smoke installed and ran all of them natively.

## Kept

The 047 process kernel is kept as the frozen screening fixture: `process_kernel/*` plus `runner/process_kernel_047.py` and `runner/process_kernel_registration.py`. Its exact bundle digests, nine-input result identity and registered model versions depend on current bytes, and no upstream owner reproduces that contract. The `flowsheet/*` modules remain the canonical repository graph and freshness owner; they are not a numerical solver.

## Deleted

Nothing. 103 found no generic custom solver whose deletion is safe: the only custom numerical path is the 047 profile executor, which is the identity-bearing incumbent above. Deleting it would invalidate supported registered model versions.

## Deferred on 103 evidence (no slot built now)

- **Recycle and separation flowsheets.** BioSTEAM first, Pyomo/IPOPT as fallback. On Windows, BioSTEAM's install failed and IPOPT was unavailable; add them only when 107/108 needs a real recycle case.
- **Other roles:** do-mpc control, FMPy co-simulation, OpenMDAO studies (108), IDA DAE, NeqSim.
