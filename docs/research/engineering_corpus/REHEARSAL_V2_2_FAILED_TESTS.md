# v2.2 Rehearsal — Failed and Withheld Checks

## Non-cheating result

The strict rehearsal is intentionally **not green**.

- embedded record checks: 950 passed, 1 failed;
- independent content checks: 39 passed, 5 failed;
- independent reviewer gate: not run;
- full-corpus readiness: failed;
- canonical export: 37/150 records.

No tolerance was enlarged and no failed assertion was removed to obtain these numbers.

## Failed source-artifact checks

All five failures came from cell-level auditing of `Soluzione Excel Ese 02.xlsx`:

1. tube-side Reynolds number combines density from one stream with viscosity from another;
2. bubble-point residual closes at about 10 atm while the declared column pressure is 9 atm;
3. shell-side heat-transfer coefficient label omits area from `W/(m² K)`;
4. overall heat-transfer coefficient label omits area from `W/(m² K)`;
5. Antoine evaluation mixes `273` and `273.15` Kelvin-to-Celsius conversions.

Corrected canonical records use consistent stream properties, the actual target pressure, area-based coefficient units and `T_C = T_K - 273.15`. Rejected source fragments are not embedded in retrievable knowledge.

## Unresolved semantic check

`packed.overall_mass_transfer_coefficient` remains withheld because the units and bases of `K_y`, `k_y` and `k_x` are not explicit enough to prove dimensional consistency under the source convention.

## Withheld does not mean false

113 records remain QA-only because they lack sufficient review evidence, a required typed-contract check, explicit coefficient basis, or a genuinely independent domain review. They must not be promoted by weakening the gate.
