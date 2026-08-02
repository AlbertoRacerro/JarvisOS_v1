# Spec 078 — full-specification scientific source evidence

**Authority:** scientific-evidence companion to `078-full-specification-2026-08-02.md`.

**Supersession:** this document supersedes the `PROPOSED` literature-gate state in §§5–6 of `078-pbr-modeling-source-evidence.md`. The earlier document remains the runtime/repository evidence register and historical planning record.

**Method:** bibliographic metadata and DOI targets were checked against publisher, PubMed, or journal records. Sources are used only for the narrow decisions stated below. No fitted biological parameter is copied into an operational profile by this specification.

## 1. Evidence rules

- Repository source and tests remain authority for current JarvisOS behavior.
- Primary scientific literature is authority for physical/model claims.
- A source supporting a model family does not make its fitted parameters transferable to another strain, reactor, temperature, salinity, acclimation state, or measurement basis.
- Missing target-specific evidence becomes a required profile parameter or a withheld claim, never an inferred default.
- Vendor-software agreement may corroborate workflow but is not physical validation.

## 2. Verified primary sources

### `SRC-078-01` — bounded optimum-shaped light response

Olivier Bernard and Barbara Rémond, “Validation of a simple model accounting for light and temperature effect on microalgal growth,” *Bioresource Technology*, volume 123, 2012, pages 520–527. DOI: https://doi.org/10.1016/j.biortech.2012.07.022

**Supports:** selection of the Bernard–Rémond optimum-shaped mathematical identity and its analytic light-response properties.

**Does not support:** universal parameters for *Nannochloropsis*, automatic parameter transfer, or omission of a calibration envelope.

### `SRC-078-02` — *Nannochloropsis gaditana* condition dependence

M. P. Gentile and H. W. Blanch, “Physiology and xanthophyll cycle activity of Nannochloropsis gaditana,” *Biotechnology and Bioengineering*, volume 75, issue 1, 2001, pages 1–12. DOI: https://doi.org/10.1002/bit.1158

**Supports:** irradiance, temperature, pH, dilution rate, acclimation, and pigment state materially affect observed physiology and growth; profile constants therefore require condition and strain provenance.

**Does not support:** treating the paper's reported optimum or growth rate as a default outside its experimental conditions.

### `SRC-078-03` — CO2 solubility in seawater

R. F. Weiss, “Carbon dioxide in water and seawater: the solubility of a non-ideal gas,” *Marine Chemistry*, volume 2, issue 3, 1974, pages 203–215. DOI: https://doi.org/10.1016/0304-4203(74)90015-2

**Supports:** dissolved CO2 equilibrium depends on temperature, salinity, and a declared gas-phase basis.

**Does not support:** automatic carbonate speciation, pH dynamics, or use of one fixed equilibrium concentration.

### `SRC-078-04` — oxygen solubility in seawater

H. E. Garcia and L. I. Gordon, “Oxygen solubility in seawater: Better fitting equations,” *Limnology and Oceanography*, volume 37, issue 6, 1992, pages 1307–1312. DOI: https://doi.org/10.4319/lo.1992.37.6.1307

**Supports:** oxygen equilibrium concentration is temperature- and salinity-dependent and must carry a declared calculation basis.

**Does not support:** treating oxygen saturation percent as an absolute concentration without the associated conditions.

### `SRC-078-05` — reactor-specific gas-transfer characterization

R. Reyna-Velarde, E. Cristiani-Urbina, D. J. Hernández-Melchor, F. Thalasso, and R. O. Cañizares-Villanueva, “Hydrodynamic and mass transfer characterization of a flat-panel airlift photobioreactor with high light path,” *Chemical Engineering and Processing: Process Intensification*, volume 49, issue 1, 2010, pages 97–103. DOI: https://doi.org/10.1016/j.cep.2009.11.014

**Supports:** volumetric mass-transfer coefficients depend on reactor configuration, hydrodynamics, gas velocity, and culture/system state.

**Does not support:** a universal `kLa` for tubular BlueRev geometry or automatic transfer of a correlation.

### `SRC-078-06` — local `kLa` variation during microalgal culture

Aastha Ojah, Laith S. Sabri, and Muthanna H. Aldahhan, “Local volumetric mass transfer coefficient estimation for Scenedesmus microalgae culture in a cylindrical airlift photobioreactor,” *Journal of Chemical Technology & Biotechnology*, volume 96, issue 3, 2021, pages 764–774. DOI: https://doi.org/10.1002/jctb.6590

**Supports:** measured/estimated `kLa` varies with location, gas velocity, optical density, gas holdup, and method; supplying a characterized value with provenance is scientifically safer than assuming a shared coefficient.

**Does not support:** direct use of its values for *Nannochloropsis* or a different reactor.

### `SRC-078-07` — oxygen and biomass composition are condition-specific

Sayam Raso, Bernard van Genugten, Marian Vermuë, and René H. Wijffels, “Effect of oxygen concentration on the growth of Nannochloropsis sp. at low light intensity,” *Journal of Applied Phycology*, volume 24, issue 4, 2012, pages 863–871. DOI: https://doi.org/10.1007/s10811-011-9706-z

**Supports:** dissolved oxygen can be a material operating variable, and elemental/biomass measurements are tied to stated cultivation conditions.

**Does not support:** a universal biomass carbon fraction, oxygen-inhibition law, or photosynthetic quotient for every *Nannochloropsis* profile.

### `SRC-078-08` — respiration and maintenance vary with state

Dongmei Zhang, Fei Yan, Zhongliang Sun, Qinghua Zhang, Shengzhang Xue, and Wei Cong, “On-line modeling intracellular carbon and energy metabolism of Nannochloropsis sp. in nitrogen-repletion and nitrogen-limitation cultures,” *Bioresource Technology*, volume 164, 2014, pages 86–92. DOI: https://doi.org/10.1016/j.biortech.2014.04.083

**Supports:** respiration/carbon loss and maintenance allocation vary with culture state, light limitation, biomass concentration, and nitrogen condition.

**Does not support:** one default respiration constant for all profiles or the nitrogen-limited model that 078 explicitly excludes.

### `SRC-078-09` — candidate independent tubular-PBR dataset

Tobias Weise, Claudia Grewe, and Michael Pfaff, “Experimental and Model-Based Analysis to Optimize Microalgal Biomass Productivity in a Pilot-Scale Tubular Photobioreactor,” *Frontiers in Bioengineering and Biotechnology*, volume 8, 2020, article 453. DOI: https://doi.org/10.3389/fbioe.2020.00453

**Supports:** a primary pilot-scale tubular-PBR dataset exists for *Nannochloropsis granulata*, with multiple batch cultivations and recorded light/temperature/productivity behavior suitable for a future independent benchmark extraction.

**Does not support:** calling the bounded 078 algebraic models validated before measured variables, time windows, exclusions, units, and parameter independence are versioned and matched.

### `SRC-078-10` — limits of absorption-only light attenuation in tubular PBRs

F. G. A. Fernández, F. G. Camacho, J. A. S. Pérez, J. M. F. Sevilla, and E. M. Grima, “A model for light distribution and average solar irradiance inside outdoor tubular photobioreactors for the microalgal mass culture,” *Biotechnology and Bioengineering*, volume 55, issue 5, 1997, pages 701–714. DOI: https://doi.org/10.1002/(SICI)1097-0290(19970905)55:5%3C701::AID-BIT1%3E3.0.CO;2-F

**Supports:** tubular-PBR average irradiance requires geometric/light-path treatment; an absorption-only Lambert–Beer representation omits scattering and wavelength-dependent attenuation and therefore must remain a bounded proxy.

**Does not support:** using the paper's empirical optical relation or fitted values for the BlueRev geometry, species, or operating state without a separate compatibility review.

## 3. Literature-gate closure matrix

| Gate | Closure for specification | Evidence | Residual implementation obligation |
|---|---|---|---|
| `LIT-01` | **Closed by bounded selection.** Adopt the Bernard–Rémond identity, but require source-bound `mu_max`, `alpha`, `I_opt`, and respiration parameters. | `SRC-078-01`, `SRC-078-02` | No operational profile until strain/condition calibration and envelope are recorded. |
| `LIT-02` | **Closed by claim restriction.** Use only the analytic one-dimensional path-average proxy and explicitly withhold resolved cylindrical-field accuracy. | `SRC-078-10` plus the analytic Beer–Lambert limiting oracle | No scattering, spectral, radial, direct/diffuse, or error-bound claim. |
| `LIT-03` | **Closed by external-equilibrium boundary.** Require CO2/O2 equilibrium concentrations with T, salinity, gas basis, source, and calculation provenance. | `SRC-078-03`, `SRC-078-04` | No automatic Henry/property/carbonate subsystem in 078. |
| `LIT-04` | **Closed by external-`kLa` boundary.** Require separate characterized `kla_co2` and `kla_o2`; prohibit a universal/shared coefficient and automatic correlation. | `SRC-078-05`, `SRC-078-06` | Each operational value must match reactor, phase, culture, method, and operating envelope. |
| `LIT-05` | **Closed by profile ownership.** Biomass carbon fraction and photosynthetic quotient are profile constants; no universal composition is asserted. | `SRC-078-07` | Missing carbon fraction or quotient produces `not_computable`. |
| `LIT-06` | **Closed by required sourced parameter.** Respiration is mandatory and condition-specific; no default is supplied. | `SRC-078-08`, `SRC-078-02` | Profile must record state, light, nutrient, and temperature context. |
| `LIT-07` | **Closed for specification, validation deferred.** Identify the Weise–Grewe–Pfaff pilot dataset as a candidate benchmark, without claiming validation. | `SRC-078-09` | Create a versioned extraction and independence audit in implementation slice 078-D. |

## 4. Decisions supported by literature but not numerically populated

The full specification intentionally contains no operational values for:

- `mu_max`;
- `alpha`;
- `I_opt`;
- respiration rate;
- biomass extinction coefficient;
- biomass carbon mass fraction;
- photosynthetic quotient;
- `kla_co2` or `kla_o2`;
- CO2 or O2 equilibrium concentration.

This is not missing work. It is the fail-closed consequence of heterogeneous strain, culture, reactor, temperature, salinity, acclimation, and measurement conditions across the literature.

A later operational profile must either:

1. bind a compatible primary experimental source and its validity envelope;
2. bind an approved BlueRev experiment with provenance and uncertainty; or
3. remain `verification_only`/`not_computable`.

## 5. Explicitly withheld claims

| Claim | Status | Reason |
|---|---|---|
| Bernard–Rémond is universally correct for *Nannochloropsis* | withheld | Model-family selection does not establish universal fit. |
| One parameter set transfers across strains or acclimation regimes | withheld | Contradicted by condition dependence in `SRC-078-02`. |
| The optical proxy is a resolved cylindrical light field | blocked | Scattering, geometry-resolved radiative transfer, and spectral effects are outside 078. |
| CO2 equilibrium can be computed without a gas/T/salinity basis | blocked | `SRC-078-03` requires those dependencies. |
| O2 percent saturation is an absolute state without T/salinity | blocked | `SRC-078-04` requires an equilibrium basis. |
| One `kLa` applies to CO2 and O2 or to every reactor | blocked | `SRC-078-05` and `SRC-078-06` show reactor/method/state dependence. |
| A universal biomass composition or photosynthetic quotient exists | withheld | Measurements are condition-specific and incomplete for a universal component. |
| 078 closes a full oxygen elemental balance | withheld | Water, nutrients, detailed composition, and photorespiration products are outside the boundary. |
| The pilot-scale dataset already validates 078 | blocked | A compatible independent extraction and parameter-separation audit do not yet exist. |
| New floating-point outputs are bit-identical across environments | blocked | `RT-37` and existing canary policy do not authorize that claim. |

## 6. Evidence acceptance invariant

> A bibliographic record may justify a model family, parameter, or validity envelope only for the claim and experimental conditions it actually supports. Citation presence is not semantic validation, and an operational profile cannot be created from a title, abstract, review, or incompatible fitted value alone.
