# 047 review resolution — parameterization and degrees of freedom

Status: binding review resolution for implementation PR #143.

This resolution clarifies `docs/specs/047-bluerev-process-0.md`. It does not add a second model, solver, or UI implementation.

## Binding principle

Spec 047 fixes the **equations, units, variable meanings, validation domain, correlation ranges, diagnostics, and provenance contract**. It does not fix a BlueRev design.

The numerical values used by tests are regression fixtures only. They must never become:

- locked project values;
- hidden runtime defaults;
- automatically accepted MemoryStore records;
- initial UI values presented as design truth;
- AI-selected values without explicit proposal provenance and user promotion.

## Caller-authoritative variables

Every successful 047 run binds all nine model inputs explicitly:

| Input | Role | Unit |
| --- | --- | --- |
| `tube_length` | geometry | `m` |
| `tube_inner_diameter` | geometry / hydraulics | `mm` |
| `tube_outer_diameter` | geometry / illumination proxy | `mm` |
| `reservoir_liquid_volume` | inventory geometry | `L` |
| `target_liquid_velocity` | operating condition | `m/s` |
| `liquid_density` | physical property | `kg/m3` |
| `dynamic_viscosity` | physical property | `Pa*s` |
| `minor_loss_coefficient` | provisional correlation parameter | `1` |
| `pump_efficiency` | equipment performance assumption | `1` |

All nine are caller-authoritative, editable bindings. The current forward evaluator contains no numerical default for any of them.

Standard gravity and the qualified Reynolds/correlation boundaries are model constants, not design variables. Changing those requires a reviewed model revision rather than an ordinary project edit.

## Degrees-of-freedom semantics

The current 047 implementation is a deterministic **forward evaluation**, not an inverse solver or optimizer.

- structural input degrees of freedom before binding: `9`;
- bindings required for a runnable case: `9`;
- unresolved degrees of freedom after a valid run input is supplied: `0`;
- outputs are computed consequences and do not consume additional user choices;
- no equality target, optimization objective, equipment selection, or design constraint is solved in 047.

The future UI/chat/flowsheet surface must display, at minimum:

- total model input degrees of freedom;
- how many are currently bound;
- which variables remain unresolved;
- source and status of each binding (`accepted`, `proposed`, temporary scenario value, or missing);
- units and validation range;
- which outputs become stale when a binding changes.

For the current forward mode, a run is enabled only when all nine required bindings are present and valid. A future inverse/optimization mode may allow selected outputs or constraints to replace selected input bindings, but that requires a separate reviewed solver contract. It must not be inferred from this forward calculator.

## UI and AI authority

- The UI must allow project values to be changed without modifying Python source.
- Chat agents may propose one or more binding changes and scenario sets.
- AI proposals must show the previous value, proposed value, unit, reason, source, affected outputs, and resulting degree-of-freedom state.
- AI output does not overwrite accepted project values automatically.
- Scenario exploration must preserve each input set and result as reproducible evidence rather than mutating one opaque global state.

## Regression fixtures

The numerical case currently used in tests exists to prove equation implementation, unit wiring, deterministic output bytes, hydraulic-versus-illuminated diameter separation, transit-versus-turnover separation, pressure/power reconciliation, and correlation-domain failures.

Passing that fixture means the model reproduces a known calculation. It does not mean that fixture is the selected Mark-1 design.
