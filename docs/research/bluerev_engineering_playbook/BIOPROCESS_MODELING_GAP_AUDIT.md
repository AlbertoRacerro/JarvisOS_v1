# BlueRev microalgae and industrial-biotechnology modeling gap audit

## Purpose

This audit defines what the BlueRev engineering playbook already knows about biological-process modeling and what must still be researched before building a credible dynamic model for an outdoor tubular marine photobioreactor using *Nannochloropsis gaditana*.

The playbook must retain model-selection knowledge, workflows, diagnostics, experiment-design logic and future research directions. It must not become a catalogue of isolated growth-rate equations or unqualified literature parameters.

## Current coverage

The current playbook already recognizes the need to couple:

- biomass growth and physiological state;
- light attenuation and light history;
- inorganic carbon, pH and alkalinity;
- gas-liquid CO2/O2 transfer;
- temperature and weather disturbances;
- nutrients, harvesting and dilution;
- hydrodynamics, residence-time distribution and mixing;
- fouling, contamination and soft sensing;
- model-fidelity escalation from simple dynamic balances to distributed or hybrid twins.

This is sufficient as a modeling agenda. It is not sufficient to select and parameterize a species-specific BlueRev model.

## Critical P0 gaps for the first dynamic model

### Biological state definition

Research must determine which states are necessary for the decisions BlueRev must support. Candidate states include:

- total, active and viable biomass;
- dead biomass or detritus;
- internal nitrogen and phosphorus quotas;
- chlorophyll or pigment state;
- storage carbon and lipid/product pools;
- cell number, size or population distribution.

The first model should use the smallest state vector that can explain measured transients and support control, harvesting and scale-up decisions.

### Growth-model family selection

The playbook needs an explicit comparison and decision workflow for:

- external-substrate Monod-type models;
- inhibition extensions;
- Droop/internal-quota models;
- photoacclimation and variable chlorophyll models;
- photosynthesis-irradiance models;
- dynamic photoinhibition and repair models;
- multi-nutrient and co-limitation formulations;
- hybrid physics-data models;
- metabolic or genome-scale models only when their additional complexity is decision-relevant.

The research objective is not to select the most sophisticated model. It is to identify the minimum model whose omitted mechanisms would otherwise change a BlueRev decision.

### Light, photoacclimation and photodamage

Required topics include:

- photosynthetically active radiation and spectral effects;
- self-shading and local irradiance distributions;
- photosynthesis-irradiance response;
- saturation and photoinhibition;
- pigment/chlorophyll acclimation;
- photosystem damage and repair;
- light-dark cycling and flashing-light effects;
- Lagrangian light history under recirculation;
- coupling between optical properties, biomass composition and fouling.

### Nutrient uptake and internal storage

Required topics include:

- external limitation versus internal quotas;
- nitrogen and phosphorus co-limitation;
- luxury uptake and storage;
- variable biomass stoichiometry;
- transition between growth and product/lipid accumulation;
- uptake-growth decoupling;
- nutrient pulses and starvation/recovery dynamics.

### Day-night physiology

The model must be able to represent, where evidence supports it:

- daytime photosynthesis;
- dark respiration and maintenance;
- storage accumulation and overnight consumption;
- net biomass loss;
- circadian or diel acclimation;
- dynamic composition and pigment changes.

Daily averaged growth rates are insufficient when control, gas transfer, stress or harvesting decisions depend on intraday transients.

### Temperature response

Temperature must not be inserted automatically as a simple Arrhenius multiplier. Research must compare:

- cardinal-temperature or optimum-based response functions;
- asymmetric responses around the optimum;
- separate temperature effects on photosynthesis, respiration, uptake, death and repair;
- thermal acclimation;
- reversible versus irreversible heat/cold damage;
- interactions with light, salinity and nutrient status.

### Inorganic carbon, pH and carbon-concentrating mechanisms

Required model-selection knowledge includes:

- dissolved CO2, bicarbonate and carbonate states;
- alkalinity and acid-base equilibria;
- equilibrium versus dynamic carbonate chemistry;
- biological uptake of CO2 and/or bicarbonate;
- carbon-concentrating mechanisms;
- gas transfer, degassing and biological consumption;
- pH inhibition and pH-dependent availability;
- coupling between carbon uptake, light and nitrogen state.

### Respiration, maintenance, death and recovery

The model must explicitly consider whether to include:

- maintenance metabolism;
- endogenous respiration;
- mortality, decay and lysis;
- lag phase and inoculum condition;
- stress-induced loss of viability;
- recovery after light, temperature, salinity or nutrient stress.

A growth-only model will generally overpredict outdoor productivity.

## P1 gaps for transfer from laboratory culture to BlueRev

### Salinity and osmotic stress

Research must cover optimum ranges, evaporation and rain transients, rapid osmotic shock, slower acclimation and interactions with temperature and nutrients.

### Oxygen production and supersaturation

The biological source term must be linked to local accumulation, gas transfer, bubble formation, possible inhibition or damage, temperature and light. A single bulk dissolved-oxygen measurement may not represent the most stressed region.

### Hydrodynamic history

The model-selection workflow must compare CSTR, plug flow, axial dispersion, tanks-in-series, compartment, distributed-delay, one-dimensional tubular and CFD/Lagrangian models. Cells experience histories of light, CO2, O2, temperature and shear, not only an average residence time.

### Mixing and shear damage

Required evidence includes effects of pumps, gas injection, local energy dissipation, recirculation frequency and shear on viability, aggregation, productivity and optical exposure.

### Biofilm and wall growth

The playbook must separate non-biological deposits from attached algal/bacterial growth and represent effects on transparency, hydraulics, mass transfer, detachment, recolonization and cleaning response.

### Contamination and community dynamics

Future outdoor models may require competition, associated bacteria, grazers, viruses, invasion thresholds, selective operating conditions and probability of culture loss.

### Strain specificity

Every reusable parameter or model claim must identify species, strain, medium, acclimation history, salinity, temperature, light regime and measurement method. Parameters from other *Nannochloropsis* species or strains cannot be transferred silently.

## Data and experiment-design gaps

The research must produce a minimum experimental programme covering, as justified by identifiability analysis:

- baseline batch growth;
- light-response and photoinhibition experiments;
- temperature-light interaction;
- nitrogen and phosphorus limitation;
- inorganic-carbon and pH response;
- salinity response;
- light-dark and dark-respiration tests;
- stress and recovery;
- chemostat or turbidostat experiments across dilution rates;
- pulse tests;
- gas-transfer characterization separated from biological kinetics;
- pump/shear and fouling tests where relevant.

It must also define measurement models and uncertainty for dry weight, optical density, cell count, chlorophyll/fluorescence, photosynthetic efficiency, nutrient concentrations, total/dissolved inorganic carbon, off-gas CO2/O2, dissolved oxygen, pH, alkalinity, product composition and viability.

Parameter estimation must address structural and practical identifiability, correlated parameters, priors, hierarchical fitting across experiments, uncertainty intervals, out-of-sample validation and criteria for rejecting unnecessary states.

## P2 future directions to retain

The playbook must preserve, without treating them as immediate requirements:

- dynamic carbon partitioning and product-quality models;
- flux-balance and dynamic-FBA approaches;
- genome-scale metabolic models;
- population-balance models for cell size, division and aggregation;
- evolutionary adaptation and phenotypic drift;
- community and microbiome models;
- physics-informed and hybrid state-space models;
- fleet-level hierarchical learning across BlueRev modules.

## Recommended first modeling ladder

### M0 — diagnostic baseline

A simple dynamic biomass model coupled to dilution, temperature, representative light, inorganic carbon and gas transfer. Its purpose is to expose data and structural gaps, not to become the final twin.

### M1 — physiology-aware model

Add internal nutrient quota, day-night storage/respiration, photoacclimation or photoinhibition where supported, dissolved oxygen, decay and a slow fouling state.

### M2 — transport-aware model

Add axial/compartment structure, residence-time or distributed-delay effects, and cell light-history representation when M1 cannot reproduce scale-dependent behavior.

### M3 — operational digital twin

Add state estimation, uncertainty, validity-envelope detection, parameter adaptation and economic/control interfaces only after the biological and transport submodels pass independent validation.

Escalation must be triggered by failed decision-relevant predictions, not by a preference for complexity.

## Research streams to execute later

1. *Nannochloropsis gaditana* strain-specific physiology and industrial cultivation.
2. Monod, Droop, quota, acclimation and hybrid model comparison.
3. Photosynthesis-irradiance, photoinhibition, repair and light-history models.
4. Nitrogen/phosphorus co-limitation, luxury uptake and variable stoichiometry.
5. Diel carbon storage, respiration and composition dynamics.
6. Temperature, salinity and pH response models.
7. Inorganic-carbon uptake, carbonate chemistry and carbon-concentrating mechanisms.
8. Oxygen production, supersaturation and inhibition.
9. Tubular-photobioreactor hydrodynamics and Lagrangian exposure histories.
10. Pump/shear sensitivity and recirculation damage.
11. Biofilm, fouling and cleaning dynamics.
12. Outdoor contamination, grazers and algal-bacterial interactions.
13. Species-specific parameter-estimation and model-discrimination protocols.
14. Measurement models, soft sensors and observability.
15. Open outdoor-PBR datasets, benchmarks and reproducible implementations.
16. Dynamic composition, lipid/product accumulation and quality models.

## Retention decision

This audit is part of the permanent playbook even before the research streams are completed. Missing evidence is represented as a research requirement, not as a reason to remove the direction. No unverified species-specific parameter is promoted into the canonical playbook.