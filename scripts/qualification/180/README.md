# Spec 180 qualification

`reference.py` computes the acceptance conversions for cases A1-A7 without importing product code.
Run `python3 scripts/qualification/180/reference.py --json` for the machine-readable table
(`cases[].X_constant_density`, `cases[].X_variable_q`); the case table is `CASES` at the top of the file.
Variable-Q model: `Q = Q_in (1 - K_Q X)` with `K_Q` measured from DWSIM 10.2.9 (ideal liquid volume mixing).
