# BlueRev seawater and Nannochloropsis foundations — 2026-08-20

Status: discovery/reference only; **not implementation authority**.

## Goal

BlueRev's biological working fluid is seawater-based. The first simplified model may hold fluid properties and carbonate availability fixed, but later fidelity should not invent marine-water thermodynamics or carbonate equilibria from ad-hoc correlations.

This audit separates:

- what M0 can reasonably freeze;
- what should become an M1/M2 backend;
- which packages can be incorporated directly versus used as external numerical oracles.

---

## SW-REF-01 — TEOS-10 GSW-Python

Source: `TEOS-10/GSW-Python`  
Origin: TEOS-10 / Gibbs SeaWater ecosystem  
Evidence: CODE/LICENSE-FIRST  
Reference value: **S scientific reference**  
Timing: **M1/M2 seawater physical properties**

### Value

GSW-Python exposes the TEOS-10 Gibbs SeaWater thermodynamic routines for seawater density, enthalpy/energy, freezing, geostrophic/stability quantities and related properties. The package includes generated/wrapped ufuncs and reference/check data rather than being a few hand-written correlations.

### Licensing caveat

The current `LICENSE.txt` allows use and redistribution in source/binary form **without modification** subject to conditions. That is materially narrower than MIT/BSD-style permission to modify.

Disposition:

- strong scientific dependency/oracle used unmodified;
- do not classify as ordinary DIRECT source code;
- pin exact package/version and keep it behind a property-service boundary if adopted;
- preserve a fallback simple constant-property implementation for M0/offline tests.

---

## SW-REF-02 — PyCO2SYS

Source: `mvdh7/PyCO2SYS`  
Origin: modern Python CO2SYS implementation maintained by marine-carbon researchers  
License: GPL-3  
Evidence: CODE/DOCUMENTATION-FIRST  
Reference value: **S carbonate-system oracle**  
Timing: **M1/M2 carbonate chemistry**  
Disposition: **EXTERNAL / boundary process if used in proprietary product**

PyCO2SYS solves the marine carbonate system from standard pairs of measurable carbonate parameters and supports modern equilibrium-constant choices and uncertainty/derivative workflows. It is extensively cross-validated against CO2SYS lineages.

For BlueRev it is a strong oracle for:

- pH;
- dissolved inorganic carbon species;
- alkalinity relationships;
- CO2/HCO3-/CO3-- availability;
- effects of temperature/salinity/pressure and equilibrium-constant selection.

Do not reproduce a home-made `pH = f(CO2)` proxy once this layer becomes relevant.

---

## SW-REF-03 — cbsyst

Source: `oscarbranson/cbsyst`  
Evidence: CODE-FIRST  
Package metadata: MIT  
Reference value: **A lightweight candidate**  
Timing: **possible M1/M2 permissive carbonate backend after validation**

### Code evidence

`cbsyst` contains direct carbon-system implementations plus tests for carbonate, boron and combined-system calculations. `cbsyst/carbon.py` handles multiple parameter combinations and uses numerical root solving rather than a single empirical pH proxy.

This is attractive because it is smaller and permissively presented compared with PyCO2SYS.

### Licensing hygiene caveat

The repository's `LICENCE.txt` is an MIT template that still contains placeholder text (`[year] [fullname]`) even though PyPI metadata declares MIT. Before commercial reuse, confirm licensing intent with repository/package metadata or author clarification and capture the exact released artifact/license.

### Required validation before use

Do not assume the smaller code is equivalent to CO2SYS. Build a differential test matrix against PyCO2SYS/CO2SYS reference outputs across BlueRev-relevant ranges of:

- salinity;
- temperature;
- total alkalinity;
- DIC/pCO2;
- pH;
- nutrient ranges if included;
- selected equilibrium-constant sets.

Only promote `cbsyst` if numerical differences are understood and bounded.

---

## SW-REF-04 — CO2SYS-MATLAB

Source: `jamesorr/CO2SYS-MATLAB`  
License: MIT according to current source metadata discovered in audit  
Evidence: source/documentation reference  
Reference value: **A+/S independent carbonate oracle**

This gives a useful second implementation lineage if PyCO2SYS's GPL boundary is undesirable for product execution. It may remain an independent validation oracle even if BLUECAD later adopts another Python implementation.

---

# Species-specific experimental references

## NANNO-EXP-01 — high-sensitivity O2 P-I measurements in N. gaditana

Paper: Vera-Vives, Michelberger, Morosinotto, Perin, *Assessment of photosynthetic activity in dense microalgae cultures using oxygen production*, Plant Physiology and Biochemistry 208 (2024) 108510.

Species: **Nannochloropsis gaditana CCAP 849/5**.

### Why it matters

The work directly characterizes P-I response and self-shading over culture density. Reported protocol details include:

- F/2 marine medium with 32 g/L sea salts;
- NaHCO3 supplementation to avoid carbon limitation during measurement;
- dark adaptation before measuring respiration;
- increasing irradiance steps with stabilization before extracting O2-production rate;
- measurements down to low cell concentrations to reduce shading bias;
- dense-culture measurements up to 100 million cells/mL;
- explicit comparison of light attenuation/self-shading and pigment-reduced strains.

For a representative dilute condition around 5 million cells/mL, the paper reports a light compensation point around 12 µmol photons m^-2 s^-1 and saturation around 163 µmol photons m^-2 s^-1, with uncertainty reported in the article. These are experimental reference values, **not universal M0 constants**.

The paper also estimates light distribution in dense cultures using measured transmittance plus Beer-Lambert attenuation, which is directly aligned with the simplified optical assumption proposed for M0.

### Data availability

A Zenodo record exists but associated files are embargoed until 2027-06-23. The article itself exposes supplementary material through the publisher. Record this now so Jarvis can re-check when the embargo lifts.

### BlueRev value

This is a strong candidate protocol/data source for validating:

- light-response curve shape;
- self-shading onset;
- optical attenuation;
- O2-based P-I characterization;
- later Pigment/Chl state models.

It also connects directly to the SmartBioTech automated O2 P-I workflow found independently.

---

## NANNO-MODEL-01 — 2025 outdoor growth-model comparison

Paper: *Comparing Growth Models to Describe Nannochloropsis Cultures Grown in Various Industrial Photobioreactors* (Bioengineering, 2025).

Evidence level: peer-reviewed comparative modeling; source code repository not located in the initial GitHub search.

### Important result for M0

Across ten closed outdoor Nannochloropsis cultures and multiple reactor configurations, the authors compared simple Monod-like, Haldane-like, exponential and more complex nutrient/quota formulations. In the reported comparison, the **Haldane-type light model coupled to simple self-shading performed best overall**, while the more complex Droop/nitrate model was less robust in the tested industrial data.

This does not prove that nutrients can always be ignored. It does provide independent evidence that starting BlueRev with:

```text
biomass
+ Beer-Lambert-like self-shading
+ Haldane-like light limitation/photoinhibition
```

is scientifically defensible as an M0 rather than merely a software shortcut.

### Consequence

M0 should not add internal nitrogen quota only because a more complex model sounds more sophisticated. Add it when:

- experimental residuals show a systematic nutrient-related error;
- operating conditions approach nutrient limitation;
- or the question being answered explicitly depends on biochemical composition/quotas.

---

# Current M0/M1 boundary

## M0 — keep explicit constants/assumptions

Reasonable initial assumptions to test:

- fixed salinity representative of operating seawater;
- fixed density/viscosity over the first narrow T/S operating range;
- inorganic carbon non-limiting if initial medium/operation supports that assumption;
- pH not dynamically solved;
- DO does not limit growth;
- Beer-Lambert-like biomass attenuation;
- Haldane-like light limitation/photoinhibition.

These are not hidden simplifications. Each should be an `Assumption` with source/rationale and an explicit replacement trigger.

## M1/M2 — planned replacements

```text
constant seawater properties
 -> TEOS-10/GSW property backend

carbon non-limiting / fixed pH
 -> carbonate-system state (validated cbsyst candidate and/or external CO2SYS oracle)
 -> CO2 gas-liquid transfer
 -> biological carbon uptake

simple light response
 -> N. gaditana fluorescence/photoregulation model
 -> measured P-I calibration

bulk light attenuation
 -> measured transmittance / improved radiative model
 -> eventual cell light-history/MCRT
```

# Recommended validation philosophy

When these fidelity layers are introduced, do not merely swap formulas. Require **differential evidence**:

1. run M0 and candidate M1 on the same experimental scenario;
2. compare against measured biomass/O2/pH/light data;
3. quantify whether the added state/parameter burden materially improves prediction;
4. retain M0 as a valid lower-fidelity mode if it remains adequate within a documented operating envelope.

This creates a real model hierarchy rather than an irreversible march toward maximum complexity.
