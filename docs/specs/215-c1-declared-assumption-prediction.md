# 215 — BlueRev C1 declared-assumption prediction with uncertainty band

Accepted outcome and readiness: maintainer [issue #905](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/905), scheduled after Design Phase 1 by the [#901 scheduling update](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/901#issuecomment-6364677846). It follows the qualified inconclusive spec 212 result and keeps all spec 212 boundaries unless relaxed below. The maintainer decided not to contact the authors or wait for raw AlgaePARC data. Live state is only in `STATUS.md`.

## Outcome

An engineer can rerun the C1 horizontal and fence AlgaePARC cases as an explicit **declared-assumption prediction**. The run produces predicted 36-day July–August 2013 mean ground areal and volumetric productivity bands for both layouts. The bands are set beside the S01 observations under both S01 denominator conventions, with the dominant uncertain inputs named. The result is a real model-vs-observation comparison, labelled *consistent under declared assumptions* or another spec 212 verdict. It is never *validated*.

## Contract

1. **Surrogate forcing.** Build July–August 2013 hourly forcing from the archived KNMI hourly record (global radiation and air temperature; SHA-256 recorded in the 212 audit). Use a documented, cited decomposition into direct/diffuse PAR and solar position for the site. Culture temperature stays within S01's reported 20–30 °C, through a simple bounded model or explicit scenarios. Import it through the existing environment-profile owner (spec 171), or an equivalent pinned input record. Label it *surrogate*, never AlgaePARC measured data.
2. **Biological card.** Assemble a parameter card for the S01 strain (Nannochloropsis sp. CCAP 211/78) from the best available primary literature, including the 2025 kinetics study. If a parameter has no source for that strain, use the closest justified relative and say so. Each value records source and location, original conditions and the reason it transfers. The card is marked *assumed / not qualified* and uses the existing spec 169 card form. C1 observations must not be used to fit it.
3. **Geometry and operation.** Use the S01 and secondary-S22 geometry and the S01 dilution rates (0.25 and 0.27 per day), with carbon non-limiting and O₂ removal active as in S01. Treat the unknown cross-sections (horizontal 3×1 and fence 1×7, plus plausible alternatives), array azimuth and illuminated-volume convention as explicit scenario parameters. Do not resolve the 212 source residuals silently.
4. **Prediction with uncertainty.** Run both layouts through the existing optics (174), PBR unit (170) and dynamic (172) owners. Cover the plausible ranges with a sensitivity analysis and a small, seeded Monte Carlo over the dominant uncertain inputs. Report each layout's predicted 36-day mean areal and volumetric productivity as median plus 5–95% band, under both S01 denominator conventions. Rank the inputs by their contribution to the spread.
5. **Verdict.** Use the spec 212 vocabulary: reproduced, partially reproduced, not determinable or discrepant. An observation inside the band is *consistent under declared assumptions*. Say whether the model reproduces the observed direction: fence higher per ground area, horizontal higher per volume. List capability gaps for later C cases (for example temperature or O₂ inhibition). Build new physics only if a gap blocks the comparison itself.
6. **Reproducibility.** Pin scripts, inputs, digests, seeds and versions as in the 212 proxy script and regression test. Rerunning the pinned inputs gives the same numbers.

## Acceptance and evidence

1. The implementation evidence document lists every forcing, card, geometry and operation input with its value or range, source, transfer argument and known/assumed/scenario state. Surrogate and assumed labels appear in the outputs too.
2. Offline tests cover the forcing construction (energy/PAR conversion, decomposition limits, solar-position sanity), card provenance completeness, and a deterministic regression of the pinned band summary for both layouts. Changed numerical owners also need unit and limiting-case tests.
3. A quantitative report gives observations, bands, both denominator conventions, the spread ranking, the direction check, the verdict and the gap list. It keeps the 212 residuals visible.
4. Ruff, the relevant backend tests and an exact-head semantic review of the science, provenance and claims all pass. If the setup is meant to be opened in the Design shell, a pinned input record is enough; browser proof is required only for a new operator-visible workflow.

## Boundaries

- No author contact, no new raw-data search as a gate, no calibration to the C1 target, no *validated* claim, no C2–C9 work, and no CFD/OpenFOAM or new optics fidelity.
- No new canonical model or evidence store. Reuse the 169/170/171/172/174 owners and the 212 qualification layout.
- Keep it in its own PRs, separate from Design Phase 2. Several coherent PRs may deliver this contract. Final acceptance requires the integrated band report.
