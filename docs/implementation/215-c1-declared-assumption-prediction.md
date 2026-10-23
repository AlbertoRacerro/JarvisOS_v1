# Spec 215 C1 declared-assumption prediction — inputs, band and verdict

Status: pinned inputs, an assumed screening card, a central run and the
declared-assumption uncertainty band with a spec 212 verdict (below). The
exact-head semantic review changed predicted productivity from harvest-only to
net production (harvest plus inventory change) and reran the pinned band; the
verdict did not change. Every prediction uses surrogate
forcing and an assumed / not qualified card; nothing is *validated*. The
qualified-inconclusive [spec 212](212-c1-source-and-capability-audit.md)
residuals stay visible.

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
Those fields let the 172/T2 path use the same solar location and PAR
conversion as the CSV construction without relying on mutable workspace site
state. The hourly child is not itself accepted by T2: the 174 owner evaluates
the sun at interval midpoints and refuses profiles coarser than 15 minutes.
`pin_t2_profile` therefore creates a second immutable child that holds each
hourly mean over its four 15-minute intervals. No sub-hourly weather is
invented; the hourly beam-normal and diffuse irradiance are unchanged, and only
the T2 sun geometry moves to 15-minute midpoints. Near sunrise and sunset a
held DNI value can fall on a sub-interval with the sun below the horizon; that
small beam loss is part of the declared surrogate construction. The parent digest preserves the exact CSV import lineage. Both
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

### Declared culture-temperature and run-window matrix

[`run_matrix.py`](../../scripts/qualification/215/run_matrix.py) combines the
three pinned 36-day forcing windows with constant **assumed** culture
temperatures of 20, 25 and 30 °C, giving nine input cases per layout. S01
reports only that culture was maintained in the 20–30 °C range, so these are
screening scenarios, not reconstructed culture temperatures. Each case starts
one hour before its first KNMI end stamp and ends at its last end stamp,
covering exactly 864 hourly intervals. The script pins the forcing digest and
labels the inputs as surrogate scenarios; it makes no biomass prediction.

The existing 172 dynamic scenario uses `temperature_source=unit_mean` with the
PBR unit's `temperature_mean` set to 293.15, 298.15 or 303.15 K and its
temperature amplitude set to zero. The KNMI `air_temperature` channel remains
station weather only. The 30 °C case approaches the assumed biological card's
30.03 °C fitted maximum and is intentionally a high-sensitivity case; it is
not a claim that C1 culture was held at 30 °C. Offline tests check the dynamic
scenario accepts this source, all cases are exactly 36 days, and no case uses
air temperature as culture temperature.

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

The 169/170 card still needs uncertainty treatment for transferred nutrient,
composition, light, extinction and loss parameters. N quota and oxygen yield derive from the selected
stoichiometry. The 2025 paper's two-flux optical coefficients
and optimum light response cannot be inserted into the 170 cylindrical
Beer–Lambert/Monod fields without a declared model-form approximation.
[`card_candidates.py`](../../scripts/qualification/215/card_candidates.py) now
pins the exact same-strain conversions that can be made without that
approximation, with source locator, original conditions and candidate state.
It explicitly lists the 2025 optimum irradiance and maintenance loss as
nontransferable to the current 170 Monod/first-order symbols, and names every
missing 170 parameter. This audit is not itself a stored 169 card. The assumed
card below pins a central screening choice, but no biomass prediction has run.

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
complete assumed card must still choose and record the candidate transfers
and propagate their dominant uncertainty.

### Cross-strain nitrate half-saturation candidate

The primary [Sánchez-Bayo et al. (2020), *Molecules* 25, 2834](https://doi.org/10.3390/molecules25122834)
full-text XML was checked at [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7356364/fullTextXML),
SHA-256 `dc7c14c7d409c03fc1711609d74c997b852654e0b0afe4ee6b1ff3fba3c21463`.
Table 2 reports `K_S = 4 ± 2 mg NO₃⁻ L⁻¹` for *N. gaditana* SAG 2.99;
Section 3.5 Eq. 2 uses a nitrate-limited Monod growth law. The original
conditions were 25 °C freshwater Guillard F/2 batch mini-photobioreactors
under 12:12 h light:dark operation, with 134 mg NO₃⁻ L⁻¹ initially. This is
neither the C1 strain nor its marine outdoor operating environment.

The 167/170 culture field is **total dissolved N as N** in kg m⁻³. Multiplying
the reported nitrate-ion concentration by `14.0067 / 62.0049` and by `0.001`
converts the central candidate to `0.0009036 kg N m⁻³`; the source's ±2 mg/L
corresponds to `0.0004518–0.0013554 kg N m⁻³`. These are a transferred
screening range, not a C1 uncertainty interval. The assumed card selects
`HNO3` as its assumed N source, but the generic inlet does not verify nitrate
speciation. An independent [*N. gaditana* nitrate-uptake study](https://doi.org/10.3389/fmars.2020.00077)
observed growth continuing after extracellular nitrate depletion, so the
simple extracellular Monod factor is also a model-form limitation. The
conversion and provenance are pinned in `card_candidates.py`; no biomass
prediction is claimed by this checkpoint.

### Cross-strain biomass-composition candidates

The primary [Sánchez-Bayo et al. (2021), *Applied Sciences* 11,
4337](https://doi.org/10.3390/app11104337) [author PDF](https://burjcdigital.urjc.es/server/api/core/bitstreams/0f40ec97-4b97-4429-a1e9-083d4614e107/content),
SHA-256 `3cc0c135f7b686577ef980c26e969270a9d84a05e89675ce12aafce3d9cfaea6`,
reports an elemental assay of harvested *N. gaditana* supplied by AlgaEnergy
in Section 2.1, Table 1. The culture conditions for that biomass are not
specified. It is **not** CCAP 211/78 or a C1 sample. The table gives C 48.7,
H 7.1, O 36.5, N 6.80 and S 0.90 wt%; P 6.43 mg/g; and ash 4.5 wt%.
The CHONS numbers sum to 100%, so the 169 ash-free CHONP formula uses their
atomic ratios to carbon, with ash entered separately. P is converted from
mg/g to 0.643 wt% before its atomic ratio is taken. The source does not
resolve how much P is organic versus inorganic. The 169 formula has no S term,
so its 0.90 wt% sulfur remains an explicit model-form residual.

[`card_candidates.py`](../../scripts/qualification/215/card_candidates.py)
pins these conversions as `a`, `b`, `c`, `d` and `w_ash`, all marked
**cross-strain candidates** with the source locator and transfer caveat.
This closes the symbol inventory for a T1 card but does not make a source-
verified or qualified card: composition, optics, nutrient response and loss
still need declared transfer uncertainty before any C1 biomass run. No C1
observation was used to select these values.

[`assumed_card.py`](../../scripts/qualification/215/assumed_card.py) now creates
one pinned **candidate** parameter set and card through the existing 169 owner
in a caller-supplied isolated workspace. Its central screening choices are the
same-strain 2025 `mu_max` and cardinal temperatures, cross-strain Lima `K_I`,
`k_d` and annular `k_X=200 m² kg⁻¹`, cross-strain Sánchez-Bayo nitrate `K_j_0`
and biomass composition. The selected N source is assumed HNO₃; the inlet
does not establish speciation. Each stored parameter retains original source
conditions and its transfer caveat, while the returned manifest pins DOI and
audited source digest. The 169 values remain `candidate`, because the cited
papers are not registered and independently verified as 169 literature records
in that workspace. The card is **assumed / not qualified**, not a measured C1
model. The 200–380 m² kg⁻¹ extinction, nitrate and other transfer ranges still
need sensitivity coverage before the final band report. A focused offline test
confirms that the card resolves through 170 and that no symbol is promoted.

## Declared geometry and operation matrix

[`scenario_inputs.py`](../../scripts/qualification/215/scenario_inputs.py)
pins S01's layout, dilution, ground area, working volume and observed outputs
without changing the spec 212 source audit. Its 24 scenarios vary the two
**assumed** representative cross-sections per layout, three **unmeasured**
array azimuths (0°, 45°, 90°), and two illuminated-volume conventions. The
3×1 horizontal and 1×7 fence cross-sections reproduce the spec 212 proxy;
1×3 and 2×3 are alternative optical modules, not claimed as-built arrays.
The fence alternative was first declared as 2×4; the 174 T2 owner refuses a
representative module with more tubes than the unit's seven loops, so it is
now 2×3 (two adjacent three-high planes). This change was made before any band
run and not chosen from C1 observations.

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

## Central declared-assumption run

[`central_run.py`](../../scripts/qualification/215/central_run.py) is the first
run of both layouts through the real owners. It uses the assumed 169 card, the
15-minute surrogate profile (171), T2 optics (174) and the PBR unit (170) in a
172 pumped culture loop: pump → PBR → dark holdup tank → harvest splitter → feed
mixer. The PBR holds the calculated tube-cylinder volume; the tank holds the
rest of S01's working volume. The feed is set to S01's dilution of the working
volume. Productivity is the net biomass produced over the window — harvested
biomass plus the change in loop inventory — divided by ground area or working
volume as S01 reports it. Counting harvest alone would let the assumed initial
inventory wash out into the prediction, or hold growth back in it; the
harvest-only value is kept beside it as `harvest_only_areal_g_m2_day`.

The central choices are the median-PAR window, 25 °C, 0° azimuth, the 3×1 and
1×7 cross-sections, 1.0 kg m⁻³ initial biomass and a nutrient-replete
0.5 kg N m⁻³ feed. `CENTRAL` and `STATES` in the script record each value and
its known/assumed/scenario state. None was chosen from the C1 observations.

| Layout | Predicted areal (g m⁻² d⁻¹) | Observed areal | Predicted volumetric (g L⁻¹ d⁻¹) | Observed volumetric | Minimum PBR N (kg m⁻³) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Horizontal | 14.11 | 12.1 | 0.680 | 0.65 | 0.304 |
| Fence | 29.55 | 19.4 | 0.864 | 0.57 | 0.268 |

The full 36-day run took about 85 s for both layouts, with a relative biomass
balance residual below 10⁻¹². Nitrogen stays about 300 times above the
transferred nitrate half-saturation, so the replete-feed assumption holds in
this run. Repeated runs agree only to about 10⁻¹² relative, and card and
snapshot digests carry workspace-local identifiers. `summary_digest` therefore
hashes the output without run-local identifiers or the round-off-level balance
residual, with floats rounded to nine significant digits. Two independent fresh
runs gave the summary digest
`16cd2450156b2876e67e8e9fd4965b03a42dfecd3a5e4178e9f864881523819f`; the 15-minute
profile digest was
`sha256:bd3ab32a914ea2c23939e093a993795233b341748f1c518ba60d19b7685bf709`.

This is **one central point, not a band or a verdict**. At this point the fence
is higher per ground area, as observed, but not lower per volume. The fence
module has 0.93 m³ of tube volume against S01's 0.75 m³ illuminated volume, and
its central prediction is sensitive to the assumed stacked 1×7 module and
`k_X`. The sensitivity analysis and seeded Monte Carlo must cover these before
any spec 212 verdict is stated. A focused offline test runs a 2-day truncation
of both layouts. It checks the labels, the volume and dilution mapping, the
net-production and denominator identities, nitrogen sufficiency and the biomass
balance.

## Declared-assumption uncertainty band

[`band.py`](../../scripts/qualification/215/band.py) runs the central case,
a one-at-a-time (OAT) sweep and a 64-draw Monte Carlo with seed 215. Each case
is a full 36-day run of both layouts through the same 169/170/171/172/174 path
as the central run, in its own temporary data root. Overrides enter only
through `run_central(..., overrides=...)`: card symbols go through a new 169
card revision whose manifest records each replacement, and geometry and
operation values go through the PBR and tank parameters. With no overrides
the central case reproduces summary digest `16cd2450156b…819f` exactly.

| Input | OAT levels around central | Monte Carlo law | State |
| --- | --- | --- | --- |
| Forcing window | low / high 36-day PAR (central median) | choice of three | scenario; KNMI surrogate |
| Culture temperature | 20, 30 °C (central 25) | uniform 20–30 °C | assumed constant inside S01's maintained range |
| Array azimuth | 45°, 90° (central 0°) | choice 0/45/90° | scenario; not reported |
| Optical module | alternative 1×3 / 2×3 (central 3×1 / 1×7) | choice | assumed, not as-built |
| Illuminated volume | S01 reported share (central tube cylinder) | choice | S01 convention vs calculated; mapped to an equivalent tube length |
| `k_X` | 380 m² kg⁻¹ (central 200) | uniform 200–380 | cross-strain fitted bounds (Lima 2022) |
| `K_I` | 7.64, 30.56 µmol m⁻² s⁻¹ | log-uniform ×½–×2 | **assumed** factor-2 screening range; no source interval |
| `k_d` | 0.0023, 0.0092 h⁻¹ | log-uniform ×½–×2 | **assumed** factor-2 screening range; no source interval |
| `mu_max` | ±20 % of 2.50 d⁻¹ | uniform ±20 % | **assumed** screening range around the same-strain value |
| Initial biomass | 0.5, 2.0 kg m⁻³ | log-uniform | assumed; no aligned initial state |
| Nitrate `K_S` as N | 0.00045, 0.00136 kg m⁻³ | uniform | cross-strain 4 ± 2 mg NO₃⁻ L⁻¹ converted |

No range was chosen from, or adjusted after seeing, the C1 observations.
`band_results.json` pins every case's draw, per-layout outputs and run summary
digest. The band summary digest is
`a8106aff909b051eabdd5937a9b561bc14dbec72fd21e67ff8c950996ef2e881`
(floats at six significant digits). The full sweep took about 10 minutes
with 22 parallel workers. Nitrogen never fell below 0.21 kg N m⁻³ in any case,
so the replete-feed assumption held throughout, and every biomass balance
closed below 10⁻⁹ relative.

### Bands against S01 observations

Both S01 denominator conventions are compared on their own definitions: ground
areal productivity, and volumetric productivity over the working volume. They
do not close against each other in S01 (horizontal +37.3 g d⁻¹, fence
+2.8 g d⁻¹), so neither is derived from the other here.

| Layout, convention | Observed | Central | MC median | MC 5–95 % | Observed quantile in MC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Horizontal, g m⁻² d⁻¹ | 12.1 | 14.11 | 7.42 | 0.81–13.14 | 0.91 |
| Horizontal, g L⁻¹ d⁻¹ | 0.65 | 0.680 | 0.358 | 0.039–0.634 | 0.97 |
| Fence, g m⁻² d⁻¹ | 19.4 | 29.55 | 13.36 | 1.87–22.61 | 0.77 |
| Fence, g L⁻¹ d⁻¹ | 0.57 | 0.864 | 0.391 | 0.055–0.661 | 0.77 |

The bands are wide: the 5th percentile is near zero net production. Being
inside such a band is weak evidence. Three of the four observations lie inside
their 5–95 % band, in its upper part. Horizontal volumetric productivity lies
just above it, at the 97th percentile of the draws. With 64 draws the 5th and
95th percentiles are themselves uncertain by a few percentile points, so this
boundary placement is not sharp. The central run sits above
the Monte Carlo median because 25 °C is close to the card's 24.5 °C optimum,
while the sampled ranges mostly move growth down.

### Spread ranking

OAT range (maximum minus minimum over central and levels), fence areal in
g m⁻² d⁻¹; horizontal and volumetric rankings have the same top five.

| Rank | Input | Fence areal OAT range | Horizontal areal OAT range |
| ---: | --- | ---: | ---: |
| 1 | Culture temperature | 29.8 | 14.3 |
| 2 | `k_X` | 14.0 | 6.7 |
| 3 | `K_I` | 13.3 | 6.4 |
| 4 | `mu_max` | 13.0 | 6.4 |
| 5 | `k_d` | 12.3 | 6.4 |
| 6 | Illuminated volume basis | 6.2 | 0.40 |
| 7 | Forcing window | 2.9 | 1.4 |
| 8–11 | Optical module, azimuth, initial biomass, nitrate `K_S` | ≤ 1.6 | ≤ 0.23 |

Temperature dominates through the card's CTMI cardinal temperatures: the
same-strain `T_max` of 30.03 °C makes growth nearly stop at a constant 30 °C,
where loss exceeds growth and net production is slightly negative (fence
−0.24 g m⁻² d⁻¹; harvest alone would show a spurious +0.71 from washing out
the initial inventory). That reflects the transferred `T_max`, which lies
above the 2025 study's training range, together with the constant-temperature
scenario. It is not evidence about the C1 culture. The four biological
parameters come next and are each about as strong. The illuminated-volume
convention matters for the fence (its tube cylinder is 0.18 m³ larger than the
reported illuminated volume) and hardly for the horizontal layout. Weather
window, azimuth, optical module, initial biomass and nutrient half-saturation
are minor.

### Direction check

| Measure | Observed | Central | Share of Monte Carlo draws with fence higher |
| --- | --- | --- | ---: |
| Ground areal | fence higher | fence higher | 100 % |
| Volumetric (working volume) | horizontal higher | fence higher | 53 % |

The model reproduces the observed areal direction in every draw. The observed
volumetric direction is not reproduced at the centre, and the draws split
about evenly, so the volumetric direction is not determinable under the
declared assumptions. It depends mainly on the illuminated-volume convention
and on biology shared by both layouts.

### Verdict

**Partially reproduced, consistent under declared assumptions for three of four
measures.** The horizontal areal, fence areal and fence volumetric observations
lie inside the predicted 5–95 % bands, and the areal direction is reproduced.
Horizontal volumetric productivity lies just above its band, and the
volumetric direction is not determinable. The bands are wide enough that this
consistency constrains the model only weakly. It is **not** validation: the
forcing is surrogate KNMI Deelen weather, the card is assumed / not qualified,
and the spec 212 denominator and illuminated-volume residuals remain
unresolved.

### Capability gaps for later C cases

1. **Culture temperature.** No measured culture-temperature trace exists, and
   the CTMI card with transferred `T_max = 30.03 °C` turns the top of S01's
   range into a growth cliff. A diurnal culture-temperature model or a
   measured trace, and a same-strain high-temperature response, are needed.
2. **Strain-specific light and loss.** `K_I` and `k_d` are cross-strain
   transfers with assumed factor-2 ranges. The same-strain 2025 light law has
   an optimum (`I_opt`), which the 170 Monod form cannot represent; a
   photoinhibition form would be needed to use it.
3. **Optical attenuation.** `k_X` varies with geometry and aggregation, and
   its 200–380 m² kg⁻¹ span is the second-largest spread.
4. **Oxygen inhibition.** S01 removes O₂ actively, but the card has no O₂
   inhibition, so the model cannot test that operating choice.
5. **Illuminated-volume convention.** S01's reported illuminated share and
   the tube geometry differ by 0.18 m³ for the fence; resolving it would narrow
   the fence volumetric comparison.
6. **Campaign dates and module geometry.** The 36-day window and the
   as-built cross-sections are unknown. Both are minor here, but they stay
   declared scenarios.

None of these gaps blocked the comparison, so no new physics was added.

Reproduce from `backend/`:

    PYTHONPATH=. python ../scripts/qualification/215/band.py --workers 22 \
        --out ../scripts/qualification/215/band_results.json

[`test_215_band.py`](../../backend/tests/test_215_band.py) checks the seeded
plan against the declared ranges, the illuminated-volume mapping, the module
tube-count limit and, offline, that the pinned results reproduce the central
digest and the band summary digest.
