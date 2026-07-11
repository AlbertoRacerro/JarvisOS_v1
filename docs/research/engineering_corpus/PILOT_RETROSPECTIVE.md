# Pilot Retrospective

## What v1 handled well

- forced explicit assumptions, validity and units;
- separated exercise, equation, solution and failure-mode records;
- made benchmark and Jarvis capability opportunities visible;
- represented the confirmed PIC numerical error instead of silently accepting the official answer.

## What failed structurally

The 14 logged gaps are not cosmetic. The largest issue is that a source can make several claims with different verdicts. In PIC Ex4 the profile and bottom concentration are correct, while the printed average rate is wrong. A single record-wide `verification_status` cannot express that safely.

The code examples exposed two additional needs: empirical correlations require a binding to their exact convention and coefficient source; executable artifacts require environment and run evidence.

## Decision

Promote **template v2** before full-corpus mapping. Do not expand v1 beyond the pilot. V2 treats source statements as claims, attaches checks to individual claims, supports multiple record types, and records benchmark visibility and artifact execution explicitly.

## Pilot correctness findings

- Planar reaction-diffusion bottom concentration independently reproduced: `0.03947710 M`.
- Correct average consumption rate: `5.810872146e-05 mol/(m^3 s)`; official printed value `2.90e-09` is low by about `20037x`.
- Spherical oxygen center concentration: `0.00314815 kg/m^3`; maximum viable radius `1.6267 mm`.
- FTCS pure-diffusion limit and centered-advection instability represented as separate claims.
- OTR/OUR and critical-kLa equations passed dimensional and algebraic checks.
- Python adsorption artifact has a runtime blocker plus correlation/provenance failures.
- MATLAB PSA artifact defines a 5% threshold but does not use it as an event; reproduced event time is approximately `58.7921 min`.
