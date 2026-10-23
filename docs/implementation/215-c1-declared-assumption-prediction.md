# Spec 215 C1 prediction — forcing checkpoint

Status: input preparation only. **No biomass prediction or C1 verdict has been run.**
The full 36-day band report still requires a sourced, assumed CCAP 211/78 model
card, dynamic runs and uncertainty analysis. This checkpoint does not change the
qualified-inconclusive result of [spec 212](212-c1-source-and-capability-audit.md).

## Pinned surrogate forcing

[`knmi_surrogate.py`](../../scripts/qualification/215/knmi_surrogate.py) converts
the archived KNMI hourly text into the committed
[`knmi_2013_deelen_surrogate.csv`](../../scripts/qualification/215/knmi_2013_deelen_surrogate.csv).
The raw input is the spec 212 local archive
`weather/knmi_2013_hourly_275_260.txt`, SHA-256
`e70bb6199912e3e19af9173a1e9a5761ea2b4c3a5f385b1c78028f96a6f452c0`.
The derived CSV SHA-256 is
`4e5c40c22639c21b562d4ce017e44bc96646fc8a16dea08c49187ce79264c584`.
It covers all 1,488 hourly intervals in July–August 2013 so a later C1 run can
declare its exact 36-day window. The S01 paper does not report those exact dates.

| Input or operation | Value and state | Source and transfer limit |
| --- | --- | --- |
| Station | KNMI 275 Deelen, 52.056° N, 5.873° E, 48.20 m; **surrogate** | KNMI file header. Nearby weather, not an AlgaePARC site measurement. |
| Hour | KNMI `HH` 1–24 is the end of a UTC hourly interval; **known** | KNMI file header. Midpoint, 30 minutes before the end, is used for sun position. |
| Broadband GHI | `Q × 10,000 / 3,600` W m⁻²; **measured at surrogate station** | KNMI `Q` is J cm⁻² per hour. |
| Air temperature | `T / 10` °C; **measured at surrogate station** | KNMI `T` is 0.1 °C. It is not culture temperature. |
| Solar position | pvlib SPA, station coordinates at interval midpoint; **modelled** | [pvlib solar position documentation](https://pvlib-python.readthedocs.io/en/stable/reference/solarposition.html). Station position stands in for the nearby C1 site. |
| Direct/diffuse split | pvlib Erbs hourly GHI decomposition; **estimated** | [pvlib Erbs documentation](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.irradiance.erbs.html), based on Erbs, Klein and Duffie (1982). No measured DNI/DHI were supplied. Low-sun estimates are especially uncertain. |
| Broadband-to-PAR | `0.45 × 4.57 = 2.0565` µmol J⁻¹; **screening assumption** | Existing [spec 171](../specs/171-environment-profiles.md) convention; the actual 2013 spectral PAR fraction is unknown. The same factor is applied to direct and diffuse broadband energy when T2 optics consumes them. |
| Culture temperature | **scenario pending** | S01 gives only a maintained 20–30 °C range. The KNMI air series must not be treated as culture temperature; a bounded scenario must be declared in the integrated run. |

[`environment_mapping.json`](../../scripts/qualification/215/environment_mapping.json)
is the exact mapping accepted by the existing environment-profile CSV importer.
It maps `ghi`, `dni`, `dhi`, `par` and `air_temperature`, converts the CSV's °C
to the profile's K, and retains the 60-minute `end` stamps. The importer
records the CSV SHA-256 and mapping in immutable profile provenance. An offline
test imports the committed CSV through that owner and reads back all 1,488
hours. No site or production workspace is changed by this checkpoint.

[`profile_handoff.py`](../../scripts/qualification/215/profile_handoff.py)
imports through the 171 owner, then creates an immutable child profile with
the KNMI Deelen site snapshot and `factor_umol_per_j=2.0565` in provenance.
Those fields let the existing 172/T2 handoff use the same solar location and
PAR conversion as the CSV construction without relying on mutable workspace
site state. The parent digest preserves the exact CSV import lineage. Both
profiles remain labelled **surrogate KNMI Deelen**, not AlgaePARC weather.
Imported `air_temperature` is weather only. Culture temperature remains a
separate 20–30 °C scenario; a future dynamic scenario must use a declared
culture-temperature source. This pinned input is not a claim that C1 received
this weather.

Regenerate with the raw archive using the command in the script module docstring.
The focused offline test checks the committed digest, complete hourly coverage,
PAR conversion, solar-position sanity and GHI = DHI + DNI·cos(zenith) closure.

### Declared 36-day forcing windows

S01 reports 36 days in July–August but does not identify the calendar dates.
[`forcing_windows.py`](../../scripts/qualification/215/forcing_windows.py)
examines every 36-day start in the pinned 62-day surrogate and chooses the
minimum, median and maximum integrated PAR windows. This is a deterministic
forcing sensitivity axis, **not** a reconstruction of the S01 campaign dates.
The digest check prevents selecting windows from a changed CSV silently.

| Scenario | First/last hourly end stamp (UTC) | Integrated surrogate PAR (mol m⁻²) |
| --- | --- | ---: |
| Low | 2013-07-26 01:00 / 2013-08-31 00:00 | 1173.438900 |
| Median | 2013-07-14 01:00 / 2013-08-19 00:00 | 1303.738740 |
| High | 2013-07-06 01:00 / 2013-08-11 00:00 | 1431.838125 |

Each window contains 864 complete hourly intervals. The low and high dose
differ by about 22% of the low dose. Later biomass runs must retain window
identity and must not label any selected window as the observed 36 days.

## CCAP 211/78 primary-source card audit

The open-access primary study by [Ihadjadene et al. (2025), *Algal Research*
90, 104196](https://doi.org/10.1016/j.algal.2025.104196) was read from the
[University of Antwerp author copy](https://repository.uantwerpen.be/docman/irua/f651d2motoMd7).
The PDF SHA-256 for this audit is
`30346040253415e5d477b255ba3876ec266034f11d60edc1e0b48273df41b9db`.
Its Table 5 reports the following fitted values for **Nannochloropsis sp.
CCAP 211/78**. The study trained its model on a lab-scale ProviAPT flat-panel
system (20 mm light path), not the AlgaePARC outdoor tubular systems. These
are **candidate assumed inputs, not source-verified 169 values or C1-calibrated
parameters**. The source study's validation applies to its own independent
lab-scale batches, not to this C1 transfer.

| Symbol | Primary value | Original meaning and C1 transfer |
| --- | --- | --- |
| μ_max | 2.50 d⁻¹ (= 0.10417 h⁻¹) | Table 5 maximum specific growth rate; candidate for the 169/170 `mu_max` field, with outdoor-transfer uncertainty. |
| r_s | 0.08 d⁻¹ (= 0.003333 h⁻¹) | Table 5 maintenance loss in the paper's net-light law (Eq. 8); candidate for 169 `loss.first_order`/170 `k_d`, but the law's placement of loss must be checked before substitution. |
| I_opt | 112.70 µmol m⁻² s⁻¹ | Table 5 optimum of the paper's photoinhibiting light law (Eq. 8); **not** the Monod half-saturation `K_I` used by 170. |
| T_min, T_opt, T_max | 6.27, 24.50, 30.03 °C (= 279.42, 297.65, 303.18 K) | Table 5 CTMI card candidates. The 20–30 °C C1 operation approaches the fitted upper limit; this parameter family deserves sensitivity coverage. |
| pH_min, pH_opt, pH_max | 4.08, 7.80, 11.30 | Table 5; the current 170 T1 model has no pH factor. S01's controlled pH near 7.5 is therefore a disclosed model gap, not a silently applied multiplier. |

Table 5 also lists same-strain literature estimates of μ_max 0.84 and 2.48
d⁻¹, loss 0.05 and 0.10 d⁻¹, I_opt about 150 and 100 µmol m⁻² s⁻¹, and
T_opt 22.63 and 25 °C. Those rows are **secondary quotations** in this paper;
their cited primary studies must be checked before any value is used as a
source-backed uncertainty bound. The paper's Table 1 gives a training
temperature range of 20.94–25.44 °C; the fitted 30.03 °C upper cardinal
temperature lies outside it.

The existing 169/170 card still needs N half-saturation `K_j_0`, N quota,
stoichiometry and oxygen yield, as well as uncertainty treatment for transferred
light, extinction and loss parameters. The 2025 paper's two-flux optical coefficients
and optimum light response cannot be inserted into the 170 cylindrical
Beer–Lambert/Monod fields without a declared model-form approximation.
[`card_candidates.py`](../../scripts/qualification/215/card_candidates.py) now
pins the exact same-strain conversions that can be made without that
approximation, with source locator, original conditions and candidate state.
It explicitly lists the 2025 optimum irradiance and maintenance loss as
nontransferable to the current 170 Monod/first-order symbols, and names every
missing 170 parameter. This is an incomplete audit record, not a stored 169
card. No complete card has been created and no biomass prediction has been run.

### Cross-strain, model-form-compatible candidates

The primary [Lima et al. (2022), *Applied Sciences* 12, 5776](https://doi.org/10.3390/app12125776)
author PDF was audited at [the University of Palermo repository](https://iris.unipa.it/retrieve/ed061932-1c36-409f-a9c1-c80257e1204f/Lima_ApplSci_2022.pdf),
SHA-256 `7b75969c6ffa680a6a29d5ddeb98c4161c0529fe4b1162975dba4b1ddff38b89`.
It studies *N. gaditana*, **not** CCAP 211/78, in 25 °C laboratory batch
reactors under artificial light. Its equations match three current 170 forms,
so the following are **cross-strain candidates**, not C1 measurements or a
qualified card:

| 170 symbol | Source value and location | Transfer limit |
| --- | --- | --- |
| `K_I` | 15.28 µmol m⁻² s⁻¹, Eq. 10 and Table 2; Monod half-saturation from a 4 mm quasi-isoactinic reactor | Same Monod form, but species, spectrum and outdoor tubular light distribution differ. Do not substitute the 2025 same-strain `I_opt` for this parameter. |
| `k_d` | 0.0046 h⁻¹, Eq. 5 and Table 2; first-order loss fitted to batch trajectories | Same loss placement as 170, but fitted for a different species and batch rather than diluted outdoor operation. Do not substitute the 2025 `r_s` without an equation audit. |
| `k_X` | 0.20 m² g⁻¹ annular and 0.38 m² g⁻¹ flat, Eq. 1 and Table 2; 200–380 m² kg⁻¹ after exact unit conversion | Eq. 1 uses natural-exponential Beer–Lambert attenuation, as 170 does. The paper attributes the geometry difference partly to aggregation; use these as scenario bounds, not a statistical confidence interval. |

[`card_candidates.py`](../../scripts/qualification/215/card_candidates.py)
pins the source, original conditions, conversions and cross-strain state. A
complete assumed card must still justify nutrient and biomass-composition
inputs and propagate the dominant transferred-parameter uncertainty.

## Declared geometry and operation matrix

[`scenario_inputs.py`](../../scripts/qualification/215/scenario_inputs.py)
pins S01's layout, dilution, ground area, working volume and observed outputs
without changing the spec 212 source audit. Its 24 scenarios vary the two
**assumed** representative cross-sections per layout, three **unmeasured**
array azimuths (0°, 45°, 90°), and two illuminated-volume conventions. The
3×1 horizontal and 1×7 fence cross-sections reproduce the spec 212 proxy;
1×3 and 2×4 are alternative optical modules, not claimed as-built arrays.
The latter fence alternative contains eight representative tubes, deliberately
showing that an optical module is not a claim about the seven physical loops.

| Layout | Source geometry/operation | Reported illuminated / tube-cylinder volume | S01 observed mass implied by areal / volumetric means |
| --- | --- | ---: | ---: |
| Horizontal | 3×80 m loops; 0.56 m³ working; 27 m² ground; 0.25 d⁻¹ dilution | 0.4088 / 0.39886 m³ | 326.7 / 364.0 g d⁻¹ |
| Fence | 7×80 m loops; 1.06 m³ working; 31 m² ground; 0.27 d⁻¹ dilution | 0.7526 / 0.93067 m³ | 601.4 / 604.2 g d⁻¹ |

The horizontal S01 output means imply daily masses differing by 37.3 g; the
fence means differ by 2.8 g. The fence illuminated-volume definitions differ
by 0.17807 m³. These residuals are retained as separate comparison bases, not
``corrected`` with an invented tube count or observation. The outer diameter
(0.050 m), 0.100 m pitch and 0.425 m tube-centre height come from secondary
S22 access as documented in spec 212. S01 says pH-controlled carbon supply,
active O₂ removal, and 20–30 °C culture temperature, but supplies no aligned
operating trace. The matrix therefore records those limits without generating
unobserved temperature or O₂ data. A later dynamic run must declare its
temperature scenario and map the selected volume basis into the existing PBR
owner explicitly.
