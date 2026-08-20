# BlueRev PBR discovery audit — 2026-08-20

Status: discovery/reference only; **not implementation authority**  
Branch purpose: preserve code-first findings without interfering with the active product implementation front.

## Operating rule

Discovery breadth and implementation priority are independent.

Every source is evaluated on two axes:

1. **reference value** — how much useful engineering/code evidence it contains;
2. **implementation timing** — whether it is needed for the first simplified BlueRev model or belongs to a later fidelity/validation layer.

A sophisticated S-grade project may remain future/reference-only. A simpler B/A-grade mechanism may be more appropriate for M0.

The first BlueRev photobioreactor model should make strong but explicit assumptions and remain small enough that its equations, parameter provenance and failure modes can be understood directly. Future Jarvis/Hermes-derived agents should then be able to replace assumptions incrementally through bounded model revisions.

## Current M0 direction

Initial intentionally simplified model:

- equivalent transparent tubular reactor geometry (`L`, `D`, `V`) rather than full serpentine CAD;
- constant incompressible liquid properties;
- 1-D steady hydraulics with Darcy-Weisbach and local-loss terms;
- simple biomass-dependent exponential light attenuation and average irradiance;
- homogeneous biomass state `X(t)`;
- simple light-response growth kinetics including photoinhibition;
- temperature modifier only if parameter evidence is good enough;
- nutrients, inorganic carbon and dissolved oxygen initially non-limiting unless initial experiments show that assumption is unacceptable;
- no dynamic fouling in M0; at most a static transmittance/cleanliness factor;
- no wave-motion coupling, CFD, MCRT, GEM or local structural fatigue in M0.

Every omitted mechanism should be represented as an explicit assumption/future replacement rather than hidden in code.

---

# Findings

## PBR-REF-01 — V-HAB algae/PBR subsystem

Source: `V-HAB/V-HAB`  
Origin: Institute of Astronautics, Technical University of Munich  
License: permissive custom/MIT-like terms with attribution/publication-citation requirements  
Evidence: CODE-FIRST  
Reference value: **A+/S**  
Timing: **M0 ARCHITECTURE REFERENCE**

### Code evidence

The algae subsystem is real and modular. It includes dedicated calculation modules for PAR, growth rate, growth medium, photosynthesis, CO2, O2, pH and temperature effects.

The PAR implementation uses a biomass-dependent hyperbolic attenuation coefficient and exponential irradiance decrease with depth. It computes positions corresponding to minimum, saturation and inhibition irradiance and partitions reactor volume into inhibited, saturated, linear-growth and dark zones. The light growth factor combines saturated-volume contribution with average light in the linear zone.

### BlueRev value

This is a strong architectural reference for a deliberately simplified M0: it shows how a model can remain interpretable while still representing both low-light limitation and excess-light inhibition.

Do not copy its Chlorella-specific parameters into Nannochloropsis gaditana.

---

## PBR-REF-02 — Jeremy Pruvost / Nantes tubular-PBR MCRT

Source: `JeremyPruvost/MCRT-for-tubular-photobioreactor`  
Origin: Nantes University / GEPEA-related research  
License: no reusable license found during audit  
Evidence: CODE-FIRST  
Reference value: **S**  
Timing: **FUTURE OPTICAL FIDELITY / ORACLE**

### Code evidence and defects

MATLAB Monte-Carlo ray-tracing code models direct/diffuse solar transfer in tubular photobioreactors with curved interfaces, reflection/refraction, scattering and absorption.

Static audit found a major direct-solar indexing defect: the main program packs `Nrays` as input 9 and solar zenith `theta_z` as input 10, while the collimated solver assigns both `theta_s` and `Nrays` from input 9. Direct-solar angle therefore uses the ray count and ignores the intended zenith angle. Additional concerns include MATLAB primary-function/file naming mismatch, geometry singularities for parallel sun/tube axes, and very heavy `disp` activity inside the ray loop.

Use as a scientific reference/oracle after defect correction/independent validation, not as trusted M0 production code.

---

## PBR-REF-03 — N. gaditana photophysiology papers

Sources: Nikolaou/Bernardi/Meneghesso/Morosinotto/Bezzo/Chachuat model family (2015, 2017)  
Evidence: paper/model equations; no directly reusable implementation located yet  
Reference value: **S**  
Timing: **M1/M2 BIOLOGY FIDELITY**

The 2015 work combines Han-style photoproduction/photoinhibition with qE/qI photoregulation and was calibrated/validated specifically on Nannochloropsis gaditana. The 2017 extension adds photoacclimation-state dependence.

Preferred long-term light-response biology reference. Continue searching author/lab repositories and supplementary materials before writing a clean implementation.

---

## PBR-REF-04 — SmartBioTech / CzechGlobe PBR-ControlScripts

Source: `SmartBioTech/PBR-ControlScripts`  
Origin: CzechGlobe Department of Adaptive Biotechnologies, Jan Červený  
License: **MIT**  
Evidence: CODE-FIRST  
Reference value: **A+/S**  
Timing: **EARLY EXPERIMENT / PARAMETER IDENTIFICATION**

### What the code really does

This is not a generic dashboard. The PSI Bioreactor Client scripts automate experimental characterization.

`O2-PIcurveMeasurement.js`:

- suspends bubbling and changes stirring during measurement;
- executes irradiance steps;
- records rapid dissolved-O2 histories;
- obtains linear regressions over the selected measurement fraction;
- derives O2 evolution and dark-respiration rates with R2 values;
- can synchronize measurements with turbidostat dilution and growth-stability state;
- cycles over multiple irradiance multipliers to produce a P-I curve.

`PP-GrowthOptimizer.js`:

- operates a quasi-continuous turbidostat using an external peristaltic pump;
- estimates doubling time from exponential regression of OD;
- rejects poor fits using an R2 threshold;
- evaluates stability using recent doubling-time mean, 95% confidence interval and temporal trend;
- only then advances the experiment to a new controlled parameter;
- can sweep light, temperature, gas-mixing settings, stirring, or OD range.

`LL-Luminostat.js` changes actinic light as a function of culture OD with a piecewise linear/exponential empirical relationship.

### BlueRev value

The high-value abstraction is not the exact PSI scripting API. It is a future BLUECAD/Jarvis workflow:

```text
model parameter / uncertainty
 -> generate bounded experiment
 -> actuate light / T / gas / dilution
 -> wait for quantitative stability
 -> measure P-I / growth response
 -> fit parameter + uncertainty
 -> attach evidence to ModelSpec/Parameter
 -> promote or reject replacement assumption
```

This is potentially more valuable near-term than importing a higher-fidelity simulator, because it creates a path from model assumptions to measured evidence.

---

## PBR-REF-05 — Pioreactor

Source: `Pioreactor/pioreactor`  
License: **MIT**  
Evidence: CODE-FIRST  
Reference value: **A+**  
Timing: **FUTURE EXPERIMENTAL DIGITAL TWIN / STATE ESTIMATION / CONTROL**

### Code evidence

The growth-rate job is production software, not a toy example. It consumes OD and dosing events, normalizes sensor channels, initializes a `CultureGrowthEKF` from warm-up data, estimates observation noise robustly from detrended log-OD residuals, and tracks hidden state containing log normalized OD, growth rate and growth-rate drift. It contains dedicated tests and is integrated with the experiment/event infrastructure.

Pioreactor also provides tested chemostat/turbidostat and LED automation patterns, calibration, messaging and experiment lifecycle machinery.

### BlueRev value

Do not use Pioreactor as the M0 physical growth model. Use it as a reference for the later measured-state side of the digital twin:

```text
raw sensors -> calibration -> filtered state estimate -> inferred growth rate
                                    |
model prediction -------------------+--> residual / parameter update / fault detection
```

Its treatment of dilution events and noisy OD measurements is especially useful for real commissioning.

---

## PBR-REF-06 — Phenobottle

Source: `HarveyBates/Phenobottle`  
Origin: University of Technology Sydney / published Algal Research platform  
Software license: **AGPL-3.0**  
Hardware/CAD license: **CC Attribution-ShareAlike** family  
Evidence: CODE-FIRST + peer-reviewed publication  
Reference value: **A+**  
Timing: **EXTERNAL/REFERENCE VALIDATION HARDWARE**

### Code/hardware evidence

Repository contains:

- host-side Python package for device communication/telemetry;
- microcontroller firmware;
- dedicated light, motor and temperature code;
- electronics;
- STEP and STL mechanical models.

The associated peer-reviewed paper reports an integrated OJIP chlorophyll-a fluorometer plus growth sensing and benchmarks the sensors against commercial instruments using Chlorella vulgaris.

### Disposition

Do not incorporate the AGPL software into proprietary JarvisOS/BLUECAD. It remains an excellent external/reference architecture for a low-cost physiology-validation rig. Hardware reuse needs separate ShareAlike/license review before commercial design adoption.

---

## PBR-REF-07 — Multiscale_Ulva

Source: `alexliberzonlab/Multiscale_Ulva` / related author fork  
Origin: published multi-scale macroalgae-farm model  
License: **no explicit repository license found in initial audit; re-check before reuse**  
Evidence: CODE/DATA STRUCTURE + publication-linked notebooks  
Reference value: **A**  
Timing: **FUTURE MULTI-REACTOR / FARM-SCALE COUPLING REFERENCE**

### Architecture

The model represents a sequence of algae cultivation reactors along a streamwise nutrient flow. Each reactor has four ODE states: environmental nutrient, reactor nutrient, internal algal nutrient and biomass. Upstream nutrient depletion is propagated into subsequent reactors. Model inputs include temperature, salinity, incident/average light, optical attenuation, nutrient uptake, internal quota, pump flow and dilution between reactors. The repo contains calibration/test notebooks and experimental/weather/light data linked to the published model.

### BlueRev value

Species and geometry are different, but the spatial coupling pattern is useful for a future BlueRev array:

```text
unit i state/output -> changed shared environment -> unit i+1
```

This is relevant if multiple BlueRev modules compete for nutrients/light/flow or are arranged in a common marine stream. It is not needed for the first single-device M0.

---

## PBR-REF-08 — AquaticEcoDynamics AED phytoplankton model

Current source: `AquaticEcoDynamics/libaed-water`  
Older monolith: `AquaticEcoDynamics/libaed2` is explicitly deprecated in favour of split libraries  
Origin: University of Western Australia Aquatic EcoDynamics group  
License: **GPL-3.0+**  
Evidence: CODE-FIRST  
Reference value: **A+/S as model/oracle**  
Timing: **FUTURE EXTERNAL/REFERENCE ECO-PHYSIOLOGY**

### Code evidence

`src/aed_phytoplankton.F90` is a mature phytoplankton biogeochemical module, not a placeholder. It supports multiple phytoplankton groups and state/diagnostic variables for carbon, internal N/P, light, temperature, salinity, nutrient uptake, respiration, mortality, excretion, chlorophyll-a, gross/net production and sedimentation. Parameter structures include alternative temperature and light models, light saturation/inhibition parameters, salinity tolerance and configurable internal N/P dynamics and uptake pools.

### BlueRev value

Potentially a strong independent external oracle for checking later nutrient/light/salinity formulations and for studying architecture of modular phytoplankton physiology. GPL means treat full code as EXTERNAL/reference for proprietary BLUECAD unless a clean separable boundary is deliberately used.

---

## PBR-REF-09 — Santhosh-dev-lab N. gaditana RL simulator

Source: `Santhosh-dev-lab/Research-Project`  
License: no license found in initial repository root  
Evidence: CODE-FIRST  
Reference value: **C / NEGATIVE REFERENCE with a few useful M0 motifs**  
Timing: **DO NOT IMPORT PHYSICS**

### Code evidence

The simulator has a superficially attractive M0/M1 structure: biomass, internal N quota, external nitrate, TAG, DIC and DO; Haldane light response; CTMI temperature modifier; Droop quota; average exponential light attenuation; gas transfer; carbonate/pH approximation; Gymnasium RL wrapper.

However, the actual code hard-codes many species/transfer/yield parameters without source provenance, uses a five-iteration multiplicative heuristic instead of a robust carbonate-equilibrium root solve, maps OD750 as a fixed linear multiple of biomass, uses simple empirical kLa and Henry-like expressions, and no relevant automated tests were found in the code search. Several comments explicitly identify approximations chosen for speed/training simplicity.

The architecture is useful as a checklist of candidate states, but it is not a trustworthy source of N. gaditana physics or parameters.

---

## PBR-REF-10 — N. gaditana genome-scale metabolic models

### TotalEnergies `Mgaditana-GEM`

- model `iMgadit23`;
- SBML/JSON/MAT/XLSX assets;
- photoautotrophic N. gaditana/Microchloropsis model;
- license **CC BY-NC 4.0**.

Disposition: research/reference/commercial-license-required; not direct proprietary integration.

### Published `iRJ1321`

A converted copy is discoverable in `zhanglab/psamm-model-collection`; this confirms another published N. gaditana GEM family. The model collection states it contains converted published models rather than original publications. Audit the original iRJ1321 model/license before considering use.

Timing: future metabolic feasibility/composition layer, not M0 dynamic PBR growth.

---

# Emerging architecture

The discovery phase increasingly suggests three separate concerns that should not be collapsed into one giant model.

## A. Predictive process model

M0 starts small:

```text
weather/light boundary
 -> simplified optical attenuation
 -> light-response growth
 -> biomass

pump/loop
 -> velocity / pressure loss / power
```

Later revisions add nutrient quota, carbonate chemistry, gas transfer, dynamic fouling, light-history and wave-driven orientation.

## B. Experimental characterization and state estimation

SmartBioTech + Phenobottle + Pioreactor suggest a powerful separate lane:

```text
experimental protocol
 -> controlled perturbation
 -> calibrated sensors
 -> filtered state/growth estimate
 -> fit + uncertainty
 -> compare against model
 -> evidence-bound parameter replacement
```

This lane can improve simple models instead of forcing theoretical fidelity before measurements exist.

## C. High-fidelity / independent oracles

Examples:

- Pruvost MCRT for tubular optical transfer;
- AED phytoplankton for aquatic biogeochemical formulations;
- N. gaditana photophysiology papers;
- GEMs for metabolic feasibility;
- CFD/structural tools in their respective domains.

Oracles do not need to be embedded in the main runtime to be valuable.

# Discovery priorities from here

1. Search author/lab repositories and supplementary code around the N. gaditana-specific Nikolaou/Bernardi/Meneghesso/Morosinotto/Bezzo/Chachuat models.
2. Audit experiment/photophysiology code from CzechGlobe and related PSI ecosystems beyond the current three scripts.
3. Search Wageningen, Almería, Nantes/GEPEA, Ifremer/INRIA and space-life-support groups for low-visibility PBR code/data.
4. Search for tubular-PBR cell-trajectory/light-dark-history code rather than only bulk radiative-transfer solvers.
5. Search seawater carbonate/gas-transfer implementations appropriate for closed tubular microalgal loops.
6. Search biofouling deposition/detachment implementations and calibration data; keep this future unless evidence shows M0 cannot ignore it.
7. Continue mechanical/wave/fatigue discovery separately; do not force it into the PBR M0.
