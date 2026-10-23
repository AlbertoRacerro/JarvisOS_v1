# C1 source reconstruction and capability audit

Date: 2026-10-23. Scope: the two tubular AlgaePARC systems in [spec 212](../specs/212-bluerev-c1-tubular-replication.md). This is the entry evidence for the first BlueRev C1–C9 case, not a claim of scientific replication.

## Source custody

- Primary S01: [de Vree et al. 2015](https://doi.org/10.1186/s13068-015-0400-2), open access CC BY 4.0; publisher HTML and the local 12-page PDF were checked. Local PDF SHA-256: `ad655f38eb0bbcc542df19cba5e73078600a0f6d8f606b684c5501309525b6b1`. The data below are from its Table 1, Table 3 and *Outdoor pilot-scale photobioreactors* methods.
- S22: [Bosma et al. 2014](https://doi.org/10.1016/j.algal.2014.10.006), publisher text inaccessible in this environment. Chapter 2 of [de Vree's Wageningen dissertation](https://edepot.wur.nl/387236), locally archived as `s35.pdf`, reproduces the design paper's text and is used as **secondary access** for the 46 mm inner/50 mm outer diameter, tube pitch, panel spacing and stripper design. These geometry details need a direct S22 source check before being called independently verified.
- Manual: local 31-page *Manuale fotobioreattori* (18 October 2026), pages 1–3 and 25. The path named in the roadmap directive with `(1)` is absent on this host; the available `Manuale_fotobioreattori.pdf` is 31 pages. It selects C1 and cites S01/S22. The paper, not the manual's summary, owns the numerical observation.
- A local KNMI hourly 2013 archive (`weather/knmi_2013_hourly_275_260.txt`, SHA-256 `e70bb6199912e3e19af9173a1e9a5761ea2b4c3a5f385b1c78028f96a6f452c0`) has global radiation and air temperature from Deelen/De Bilt. It is an external weather surrogate, not AlgaePARC culture temperature or a split DNI/DHI series; it cannot supply the missing C1 operating and harvest trace.

## Inputs and observations

| Input or observation | Horizontal | Fence | State and source |
| --- | ---: | ---: | --- |
| Strain | CCAP 211/78 | CCAP 211/78 | Known, S01 methods |
| Tube ID / OD | 0.046 / 0.050 m | same | ID supported by S01 optical path and secondary S22 chapter; OD secondary only |
| Loop count × length | 3 × 80 m | 7 × 80 m | Known, S01 methods |
| Operated tube velocity | 0.45 m/s | 0.45 m/s | Known, S01 methods |
| Total working volume | 0.56 m³ | 1.06 m³ | Known, S01 Table 3 |
| Illuminated volume share | 73% | 71% | Reported, S01 Table 3; see residual below |
| Occupied ground area | 27.0 m² | 31.0 m² | Known, S01 Table 3, half dummy boundary included |
| Summer mean measured dilution | 0.25/day | 0.27/day | Known, S01 Table 1; different operations |
| Summer mean ground areal productivity | 12.1 g/m²/day | 19.4 g/m²/day | Known, S01 Table 1, July–August 2013, 36 days each |
| Summer mean volumetric productivity | 0.65 g/L/day | 0.57 g/L/day | Same source/window |
| Outdoor culture temperature | 20–30 °C | 20–30 °C | S01 outdoor methods give the maintained range, not the time series or exact values for either 36-day window |
| Time-aligned incident light, temperature, harvest and outages | — | — | Missing from available S01 tables; search for raw dataset remains open |
| CCAP 211/78 growth/extinction/temperature parameter set | — | — | Missing as a jointly sourced, independently verified card |
| Exact array/stripper/pump operating state during the 36 days | — | — | Incomplete; design dimensions do not establish as-operated performance |

## Arithmetic and source inconsistencies

The cylindrical tube volumes from the reported ID and lengths are `π·0.046²·240/4 = 0.3989 m³` and `π·0.046²·560/4 = 0.9307 m³`. S01's reported illuminated shares imply `0.73·0.56 = 0.4088 m³` and `0.71·1.06 = 0.7526 m³`. The horizontal difference is about 2.5% of calculated tube volume; the fence difference is about 19.1%. These are source-definition residuals, **not** numbers to silently correct with a fabricated tube count. The 80 m may include opaque connections or the illuminated share may use a different convention; the available methods do not resolve it.

S01 methods say volumetric productivity is calculated from ground areal productivity using reactor volume and ground area (Eq. 2), yet the published Table 1 means do not close under its Table 3 denominators. Multiplication gives horizontal `12.1·27 = 326.7 g/day` versus `0.65·560 = 364.0 g/day` (11.4% relative to the areal value), and fence `19.4·31 = 601.4 g/day` versus `0.57·1060 = 604.2 g/day` (0.5%). Both Table 1 averages report 36 days. Rounding alone cannot explain the horizontal gap. A table error, undocumented denominator or calculation convention remains unresolved; compare each published measure on its stated definition rather than forcing identity by changing an input.

S01 explicitly used separate circulation pumps, service bubble columns (0.15 and 0.31 m³), pH-controlled CO₂, active oxygen removal and temperature management. Its two systems also differed in footprint, working volume, illuminated share and dilution. The paper's output contrast cannot identify an orientation-only effect. Maximum-week outputs and photosynthetic efficiency values are separate targets, not substitutes for the 36-day means.

## Current capability map at master `16028ab9`

| Required effect | Existing owner | C1 limit |
| --- | --- | --- |
| Pinned strain/model parameters | 169 biological model cards, consumed by `process_stack/pbr_unit.py` | A source-verified CCAP 211/78 set is not bundled; candidate/assumed values cannot validate C1. |
| Cylindrical tube light and loop growth | 170 `PhotobioreactorT1`, 172 `dynamic_engine.py` | Well-mixed tube loop; no axial O₂ or full service-unit dynamics. A run needs a pinned card and complete inlet/environment. |
| Array shade/wall/diffuse PAR | 174 `optics_t2.py` | Requires pitch, axis, height, indices and a time-resolved DNI/DHI profile. Secondary S22 gives some design geometry, not a complete 2013 operating profile. |
| Sourced environment | 171 immutable imported profiles | No raw, time-aligned 2013 C1 site profile has been identified. A synthetic profile is only a model exercise. |
| Hydraulic screening | 107 evaluator and 170/172 PBR diagnostics | Straight smooth tube/declared pump efficiency; no measured C1 pump curve, bends, manifold or degasser pressure loss. |
| Thermal/carbon/O₂ inhibition and fouling | No qualified C1 owner | Tier 1 temperature is prescribed, carbon is nonlimiting, O₂ is reported without growth inhibition, and fouling/restarts are absent. 175 is planned but not ready. |
| Provenance and qualification | Existing 102/106 evaluation evidence and 169 card pins | A green run does not promote a model or observation into scientific qualification. |

## Quantitative C1 comparison at this checkpoint

The observation is the 36-day July–August 2013 mean, not a per-day trace. A comparable prediction is currently unavailable for either layout: a pinned C1-suitable model card and time-aligned 2013 light/temperature/harvest inputs have not been established. Thus the prediction and prediction-minus-observation discrepancy are **not computable**, rather than zero. The available geometric and published-output arithmetic is:

| Quantity | Horizontal | Fence | Interpretation |
| --- | ---: | ---: | --- |
| Tube cylinder volume, `πD²L/4` | 0.3989 m³ | 0.9307 m³ | `D=0.046 m`; `L=240/560 m` from S01 methods |
| Reported illuminated volume, share × total | 0.4088 m³ | 0.7526 m³ | S01 Table 3; cylinder-minus-reported is −0.0099/0.1781 m³ |
| Observed ground areal productivity | 12.1 g m⁻² d⁻¹ | 19.4 g m⁻² d⁻¹ | S01 Table 1; occupied ground area is 27/31 m² |
| Observed volumetric productivity | 0.65 g L⁻¹ d⁻¹ | 0.57 g L⁻¹ d⁻¹ | S01 Table 1; total working volume is 560/1060 L |
| Areal implied daily biomass, productivity × ground area | 326.7 g d⁻¹ | 601.4 g d⁻¹ | Observed-mean arithmetic, not a simulation |
| Volumetric implied daily biomass, productivity × total volume | 364.0 g d⁻¹ | 604.2 g d⁻¹ | Horizontal value is 11.4% above the areal implication; fence is 0.47% above |
| C1 model prediction / discrepancy | unavailable / not computable | unavailable / not computable | Missing source-matched forcing and parameter basis; no scientific agreement claim |

The **bounded conclusion is inconclusive** for model agreement and orientation causality. The observations themselves show higher ground areal productivity for the fence system and higher volumetric productivity for the horizontal system under different operated dilution rates and geometries. The unexplained denominator and illuminated-volume residuals above must remain visible in any later simulation comparison.

A further [2025 primary study of CCAP 211/78 kinetics](https://doi.org/10.1016/j.algal.2025.104196) is a candidate parameter source, but its fitted parameters and light law come from a different ProviAPT indoor geometry and conditions. Its publisher abstract and accessible search extract do not establish a complete T1 card or 2013 outdoor forcing. No value from it has been promoted into this C1 run.

## Bounded next experiment

The publisher page exposes no supplementary file in the checked article view, and a bounded repository search did not locate day-level C1 data; absence has not been proven. Search the original AlgaePARC campaign for day-level light, temperature, dilution and harvested biomass and primary CCAP 211/78 kinetics with matching growth conditions. No new physics is justified by this audit alone.

### Reproducible existing-model exercise

[`c1_proxy_optics.py`](../../scripts/qualification/212/c1_proxy_optics.py) runs the existing `optics_t2.v1` kernel on **one synthetic daylight condition**, while reproducing the S01 geometry and denominator arithmetic independently of the optical model. Run from `backend/` with `PYTHONPATH=. uv run --no-project --with numpy python ../scripts/qualification/212/c1_proxy_optics.py`. The script was run on 23 October 2026 with CPython 3.11.16 and NumPy supplied by `uv`; the JSON output includes the exact layout digests. [`test_212_c1_proxy_regression.py`](../../backend/tests/test_212_c1_proxy_regression.py) pins both layouts' source arithmetic, executed optical outputs and unsupported biomass prediction state.

Source inputs are the 46 mm inner diameter, 3/7 × 80 m loops, total volumes, illuminated shares, ground areas and two observed productivities listed above. The 50 mm outer diameter, 50 mm free tube clearance and 400 mm tube-bottom height have only the secondary S22 access described above. The **3-across × 1-layer horizontal and 1-across × 7-layer fence cross-sections are assumptions**, not established as-built tube arrays: loop count alone does not establish cross-section count. The 45° sun elevation, 90° sun azimuth, 700/100 µmol m⁻² s⁻¹ direct/diffuse PAR, north-south tube axis, 1.49/1.33 refractive indices and 0.2 ground albedo are all sensitivity assumptions. Pitch is 0.10 m, tube-centre height is 0.425 m. There is no 2013 weather, harvest schedule, CCAP 211/78 card, temperature trace or measured array azimuth in this exercise.

| Existing T2 output, one condition | Horizontal proxy | Fence proxy | Meaning |
| --- | ---: | ---: | --- |
| Intercepted PAR, µmol s⁻¹ m⁻¹ per tube | 50.3336 | 49.8004 | Model output under assumed condition |
| Transmitted PAR, same units | 46.4724 | 45.9893 | Model output; both below intercepted PAR |
| Equivalent thin-limit PAR, µmol m⁻² s⁻¹ | 1101.3223 | 1089.0296 | Model output; **not** a 36-day mean |
| Cylinder minus reported illuminated volume, m³ | −0.00994 | +0.17807 | S01 geometry/denominator residual, preserved |
| Volumetric minus areal implied biomass, g/day | +37.3 | +2.8 | S01 observation denominator residual, preserved |

The proxy produces a lower per-tube light field for the assumed fence cross-section at this one sun angle. It cannot predict biomass or explain the observed higher fence ground areal yield. Different arrays, azimuths, weather and operations could change that direction. No predicted ground areal or volumetric productivity is reported, so prediction-minus-S01 discrepancy remains **not computable** for both layouts. This is a qualified inconclusive C1 result, with the first discriminating measurement being time-aligned 2013 DNI/DHI, culture temperature, dilution/harvest and observed biomass, plus a primary-source CCAP 211/78 parameter card and verified as-built cross-sections. A model run with synthetic inputs must remain unqualified even if it converges.
