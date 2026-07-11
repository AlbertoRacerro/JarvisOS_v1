# Quality Gates

## Gate A — extraction

- source SHA-256 and exact location present;
- excerpt is short and traceable;
- equations are visually checked against the rendered source;
- no authority label is interpreted as truth.

## Gate B — structure

- atomicity test passes;
- primary and secondary record types are coherent;
- all symbols used by equations exist in the variable registry;
- assumptions and validity are nonempty for models/correlations;
- typed relations do not point to blank IDs.

## Gate C — engineering verification

- dimensions pass or the failure is recorded;
- numerical results are independently reproduced when sufficient data exist;
- governing equations pass residual/balance checks where possible;
- limiting cases and physical sanity are checked;
- empirical coefficients are bound to convention, units, range and source;
- unresolved ambiguity prevents `verified`.

## Gate D — benchmark promotion

- prompt can be separated from solution and gold;
- gold is independently reproduced, not copied blindly;
- deterministic grader covers all load-bearing outputs;
- alternative valid methods are accepted;
- contamination class and allowed context are explicit;
- at least one adversarial variant targets assumptions, units or model choice.

## Gate E — Jarvis capability promotion

- deterministic authority is identified;
- AI role is advisory where a mechanical check exists;
- failure modes have regression tests;
- tool/runtime requirements are explicit;
- no caller is added until the boundary tests pass.
