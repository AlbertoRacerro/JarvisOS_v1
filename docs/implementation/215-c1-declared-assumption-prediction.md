# Spec 215 C1 prediction — forcing checkpoint

Status: input preparation only. **No biomass prediction or C1 verdict has been run.**
The full 36-day band report still requires a sourced, assumed CCAP 211/78 model
card, scenario geometry and dynamic runs. This checkpoint does not change the
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

The CSV columns map to the existing environment profile importer as `ghi`,
`dni`, `dhi`, `par`, `air_temperature` with units W m⁻², W m⁻², W m⁻²,
µmol m⁻² s⁻¹ and °C respectively, 60-minute resolution and `end` stamps.
An imported profile must retain a site snapshot for T2 solar position and
explicitly label its surrogate origin. For T2 optics, the consuming dynamic
scenario must explicitly set `par_from_ghi_factor=2.0565`; the CSV importer
does not copy this conversion into its profile provenance. The committed file is a pinned input,
not a claim that the C1 systems received this weather.

Regenerate with the raw archive using the command in the script module docstring.
The focused offline test checks the committed digest, complete hourly coverage,
PAR conversion, solar-position sanity and GHI = DHI + DNI·cos(zenith) closure.

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

The existing 169/170 card still needs a source-backed or explicitly assumed
`K_I`, biomass extinction `k_X`, N half-saturation `K_j_0`, N quota,
stoichiometry and oxygen yield. The 2025 paper's two-flux optical coefficients
and optimum light response cannot be inserted into the 170 cylindrical
Beer–Lambert/Monod fields without a declared model-form approximation.
No complete card has been created and no biomass prediction has been run.
