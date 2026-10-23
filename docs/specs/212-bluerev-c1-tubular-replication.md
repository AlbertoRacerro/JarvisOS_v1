# 212 — BlueRev C1 tubular layout scientific replication

State: **accepted and ready** under binding roadmap directive `L20261022122708-233d` (BlueRev C1–C9 scientific program). Dependencies 107, 170, 171, 172 and 174 are merged. This is the first bounded case of that program.

## Outcome

An engineer can reconstruct the published C1 horizontal and fence tubular configurations as traceable study inputs, run current capabilities as far as source data permit, and compare predictions quantitatively with the paper's summer observations. The conclusion must distinguish agreement, disagreement and **inconclusive** evidence. A successful simulation alone is never scientific validation.

## Primary evidence and reconstructed case

The canonical 31-page *Manuale fotobioreattori* (18 October 2026), pages 1–3 and 25, names C1 and cites [de Vree et al. (2015), DOI 10.1186/s13068-015-0400-2](https://doi.org/10.1186/s13068-015-0400-2) (S01) and [Bosma et al. (2014), DOI 10.1016/j.algal.2014.10.006](https://doi.org/10.1016/j.algal.2014.10.006) (S22). S01 full text was independently checked against the publisher and the local copy (SHA-256 `ad655f38eb0bbcc542df19cba5e73078600a0f6d8f606b684c5501309525b6b1`). S22 publisher full text was inaccessible here; chapter 2 of the [Wageningen dissertation](https://edepot.wur.nl/387236) is a secondary access path and must be labelled as such.

| Source quantity | Horizontal | Fence/vertical | Scope |
| --- | ---: | ---: | --- |
| Strain | Nannochloropsis sp. CCAP 211/78 | same | Same Netherlands site |
| Tube inner diameter | 0.046 m | 0.046 m | S01 Table 3 |
| Transparent loops | 3 × 80 m | 7 × 80 m | S01 methods |
| Tube liquid velocity | 0.45 m/s | 0.45 m/s | S01 methods |
| Total working volume | 0.56 m³ | 1.06 m³ | S01 Table 3; includes service volume |
| Occupied ground area | 27.0 m² | 31.0 m² | S01 Table 3; includes half the dummy boundary area |
| Illuminated volume fraction | 73% | 71% | S01 Table 3 |
| Summer mean ground areal productivity | 12.1 g/m²/day | 19.4 g/m²/day | S01 Table 1, July–August 2013, 36 days each |
| Summer mean volumetric productivity | 0.65 g/L/day | 0.57 g/L/day | Same 36-day comparison |

S01 reports different measured dilution rates for these means (0.25/day horizontal, 0.27/day vertical), service vessels and interruptions. Both systems were restarted three times during the wider campaign. The observed difference is **not** an isolated orientation effect, and the summer means are **not** year-round guarantees. Maximum-week values cannot replace the summer means. The table does not fix complete pump curves, as-built manifold geometry, time-aligned weather/harvest series or all strain-specific kinetic coefficients.

## Accepted boundaries

- Preserve every observation's time window, denominator, area convention, unit and source location. Keep observations separate from simulations and assumptions. Record exact model/code version, input digests, environment profile and run references.
- Audit current 107/170/172/174 process, dynamic and optics owners first. Reuse physically applicable models and evidence contracts. Add only a demonstrated missing capability required for C1. A new parameter needs a source or a labelled sensitivity assumption; fitting the C1 target cannot count as independent validation.
- Reconstruct layouts and distinguish illuminated tube volume from total working volume. Check geometry, volume and occupied-area arithmetic with units before biological runs. Do not infer exact service geometry, optical pitch, degasser performance or pump curve from aggregate values.
- Use sourced, time-aligned 2013 weather and operation if available. A labelled proxy or synthetic scenario may exercise a model but cannot claim to reproduce July–August 2013. Expose missing temperature, carbon/O2, fouling and service-unit effects instead of compensating with invented kinetics.
- Report predicted and observed ground areal and volumetric productivity, definitions, discrepancies and uncertainty/gaps where comparable. Compare layout direction only under compatible conditions. A qualified **inconclusive** result identifies the missing evidence and next discriminating measurement; never fabricate a match or confidence interval.

## Acceptance

1. A source inventory records S01 table/method locations, the S22 access limit, manual page references, and every input as known/assumed/missing with provenance. Geometry and denominator checks make unexplained residuals visible.
2. A capability audit maps each required effect to an existing owner or concrete gap. New numerical code, if genuinely needed, has conservation, unit and limiting-case tests plus a cumulative C1 regression case.
3. Both layouts execute through existing study/evaluation owners when inputs suffice. Runs are deterministic for pinned inputs and identify model, parameter basis, environment, layout and solver result. Unsupported cases fail with a reason.
4. A quantitative report puts S01 observations beside comparable predictions with units, 36-day summer scope and area conventions. Discrepancies are computed only where inputs and definitions match. Its bounded conclusion is agreement, disagreement or inconclusive, without claiming orientation causality from non-identical systems.
5. Relevant offline tests and exact-head semantic review verify transcription, arithmetic, provenance, model boundaries and report. Installed scientific runtime claims require real host evidence; an operator-visible workflow requires real-browser proof.

## Non-goals

C2–C9 replication, new dashboards, invented scientific parameters, calibration to C1 as validation, new canonical model/evidence stores, OpenFOAM/CFD or optical-field coupling, and an optimal-layout claim for another site or strain.
