# Deep Research prompt — BlueRev microalgae modeling playbook

Copy the prompt below into a fresh Deep Research session.

---

You are conducting a rigorous engineering and scientific deep-research study for **BlueRev**, a proposed modular floating marine tubular photobioreactor platform. The initial biological target is **Nannochloropsis gaditana**, but evidence from closely related *Nannochloropsis* species may be used only when transferability is made explicit.

## Objective

Build a **decision-oriented modeling playbook** for designing the first credible dynamic BlueRev model. Do not produce an encyclopedic collection of formulas. Determine:

1. which biological, physicochemical and transport mechanisms need to be represented;
2. which model families are available for each mechanism;
3. when each family is appropriate or inappropriate;
4. which states, parameters, measurements and experiments are needed;
5. what minimum model should be built first;
6. what additional complexity should be introduced only after specific validation failures;
7. which open datasets, benchmark models and reproducible implementations can accelerate the work.

The result must help an engineer decide **what to model, how to identify it, how to validate it and when to escalate model fidelity**.

## BlueRev context

Assume the system may include:

- transparent replaceable marine tubes;
- modular Smart Joints containing pumping, gas exchange, nutrient dosing, sensing and sampling functions;
- semi-batch operation initially, with future continuous feed and bleed;
- outdoor solar forcing, day-night cycles and variable weather;
- marine salinity and possible evaporation/rain disturbances;
- recirculation through pumps and curved joints;
- CO2 addition and O2 removal;
- pH, dissolved oxygen and temperature sensing;
- continuous or periodic harvesting;
- progressive development from laboratory loop to protected-water pilot and later offshore modules;
- future digital-twin, MPC/EMPC and fleet-learning capabilities.

The first model must be useful for decisions about reactor geometry, circulation, gas transfer, nutrient strategy, sensor selection, control, harvesting, fouling management and experimental planning.

## Strict scope and evidence rules

Search primary scientific literature, authoritative reviews, standards where relevant, doctoral theses with substantial data, government/institutional reports, open datasets and mature open-source implementations. Prefer original model papers and experimental studies over secondary summaries.

Use English-language literature extensively even though the final report must be in Italian.

For every important claim:

- cite the exact source;
- identify species and strain;
- identify cultivation medium and salinity;
- identify temperature and light regime;
- identify reactor type and scale;
- distinguish laboratory, outdoor pilot and industrial evidence;
- state whether the evidence is directly applicable, partially transferable or only conceptually relevant to BlueRev.

Do not silently transfer parameters across species, strains, media, light regimes or reactor geometries.

Do not treat a model that fits one dataset as universally valid.

Do not rank models by mathematical sophistication. Rank them by decision usefulness, identifiability, data burden, extrapolation risk and computational cost.

Do not promote isolated numerical parameters into a reusable database unless their full basis, units, uncertainty and validity envelope are available.

Clearly label:

- established evidence;
- competing interpretations;
- emerging approaches;
- unresolved questions;
- missing data;
- inferred recommendations.

## Research questions

### A. Biological state representation

Determine which states are commonly and successfully used for *Nannochloropsis* and comparable industrial microalgae:

- total biomass;
- active or viable biomass;
- dead biomass/detritus;
- cell number and size distribution;
- chlorophyll/pigment state;
- internal nitrogen and phosphorus quotas;
- storage carbon, carbohydrate or lipid pools;
- product-quality states.

For each state, assess:

- what decision it supports;
- whether it is observable;
- how it is measured;
- whether it is structurally/practically identifiable;
- whether it is necessary in M0, M1, M2 or only future models.

### B. Growth and nutrient-model families

Compare at least:

- Monod-type external-substrate models;
- multi-substrate and inhibition variants;
- Droop/internal-quota models;
- luxury-uptake and storage models;
- Liebig minimum, multiplicative and other co-limitation formulations;
- variable-stoichiometry models;
- photoacclimation and variable-chlorophyll models;
- hybrid physics-data models;
- metabolic, flux-balance and dynamic-FBA approaches.

For each family provide:

- physical interpretation;
- assumptions;
- required states and parameters;
- typical experiments;
- strengths and known failure modes;
- extrapolation limits;
- computational burden;
- suitability for control-oriented, design-oriented and digital-twin use;
- specific evidence for *N. gaditana* or close species.

### C. Light, photosynthesis and photoinhibition

Research and compare:

- photosynthesis-irradiance formulations;
- light saturation and photoinhibition;
- photoacclimation and pigment dynamics;
- photosystem damage-repair models;
- spectral effects and PAR conversion;
- self-shading and optical-property variation;
- Beer-Lambert, two-flux, radiative-transfer and empirical attenuation models;
- flashing-light and light-dark-cycle models;
- Lagrangian light-history models under circulation;
- coupling between light, nutrient status and temperature.

Identify when a volume-averaged irradiance is adequate and when spatial or Lagrangian exposure history is required.

### D. Day-night metabolism and respiration

Determine how outdoor models represent:

- daytime photosynthesis;
- dark respiration;
- maintenance metabolism;
- endogenous decay;
- storage accumulation and overnight consumption;
- diel or circadian acclimation;
- stress recovery;
- net biomass loss.

Assess which mechanisms are necessary to predict 24-hour productivity and harvesting decisions.

### E. Temperature, salinity and stress

Compare suitable response formulations for:

- cardinal temperatures and optimum-based kinetics;
- asymmetric temperature response;
- acclimation;
- reversible and irreversible stress;
- separate effects on photosynthesis, uptake, respiration, death and repair;
- salinity and osmotic shock;
- interactions among temperature, light, salinity and nutrient limitation.

Explicitly explain why a single Arrhenius multiplier is often inadequate.

### F. Carbonate chemistry, pH and carbon uptake

Research:

- dissolved CO2/bicarbonate/carbonate representation;
- alkalinity and charge balance;
- equilibrium versus dynamic carbonate chemistry;
- biological uptake of CO2 and bicarbonate;
- carbon-concentrating mechanisms in *Nannochloropsis*;
- coupling to pH, gas transfer, light and nutrient state;
- pH inhibition and operational limits;
- suitable measurement and parameter-estimation methods.

### G. Oxygen dynamics

Determine how to model:

- photosynthetic oxygen production;
- dark consumption;
- gas-liquid transfer;
- supersaturation;
- bubble formation;
- local versus bulk dissolved oxygen;
- possible inhibition or oxidative stress;
- temperature and salinity effects.

Identify evidence relevant to tubular photobioreactors.

### H. Hydrodynamics, residence-time and cell exposure history

Compare:

- CSTR;
- plug flow;
- axial-dispersion models;
- tanks-in-series;
- compartment models;
- distributed-delay models;
- one-dimensional tubular models;
- CFD plus Lagrangian trajectories.

For each, state which BlueRev decisions justify the added complexity. Include recirculation, mixing, dead zones, gas-liquid regions and Smart Joint transitions.

### I. Shear, pumps and mixing

Research evidence for *Nannochloropsis* and similar robust microalgae regarding:

- pump type and repeated recirculation;
- energy-dissipation rate;
- local shear and extensional stress;
- bubble damage;
- aggregation or floc breakup;
- mixing time;
- productivity and viability effects.

Produce an experiment and model-selection workflow rather than a generic claim that more mixing is beneficial.

### J. Biofilm, wall growth and cleaning

Determine how to represent:

- attached algal/bacterial growth;
- non-biological deposits;
- optical-transmission loss;
- hydraulic and mass-transfer changes;
- detachment and recolonization;
- cleaning effectiveness and damage;
- slow-state models suitable for operational twins.

### K. Contamination and community dynamics

Review models and data for:

- competing algae;
- associated bacteria;
- mutualistic or harmful interactions;
- grazers and predators;
- viruses;
- invasion thresholds;
- washout and selective operating conditions;
- probability and consequences of culture collapse.

Classify what belongs in the first model, a risk model or only a future fleet model.

### L. Product composition

For future economic optimization, examine dynamic models of:

- lipids;
- pigments;
- PUFA or target products;
- carbon partitioning;
- nutrient-stress induction;
- trade-off between biomass productivity and product quality.

Do not force these states into the first model unless the evidence shows they affect an immediate BlueRev decision.

### M. Measurement models and soft sensing

Assess measurement principles, uncertainty, response time and calibration for:

- dry weight;
- optical density;
- cell counts;
- chlorophyll and fluorescence;
- Fv/Fm or related photosynthetic-efficiency metrics;
- nutrients;
- TIC/DIC/TOC;
- pH and alkalinity;
- dissolved and off-gas O2/CO2;
- viability;
- lipid/product composition.

Identify which states can be estimated using observers, EKF/UKF/MHE or hybrid soft sensors and what observability limitations remain.

### N. Parameter estimation, model discrimination and validation

Produce a rigorous workflow covering:

- structural identifiability;
- practical identifiability;
- parameter correlation;
- sensitivity analysis;
- priors and hierarchical fitting;
- sequential experiment design;
- model discrimination;
- uncertainty propagation;
- out-of-sample and cross-regime validation;
- falsification tests;
- validity-envelope detection;
- criteria for adding or removing states.

### O. Open data, benchmarks and implementations

Find and evaluate:

- open datasets for *Nannochloropsis* or comparable outdoor photobioreactors;
- dynamic weather-driven datasets;
- chemostat/turbidostat datasets;
- open-source model implementations;
- reproducible code repositories;
- benchmark control environments;
- digital-twin or state-estimation examples.

For every resource report license, completeness, data quality, missing metadata, reproducibility and BlueRev relevance.

## Required deliverables

### 1. Executive decision report

Provide the recommended modeling ladder:

- M0 diagnostic baseline;
- M1 physiology-aware model;
- M2 transport-aware model;
- M3 operational digital twin.

For each level specify states, inputs, outputs, equations/model families, parameters, measurements, decisions supported, limitations and promotion criteria.

### 2. Model-family selection matrix

Create a table with rows for mechanisms and columns for candidate model families. Include:

- when to use;
- when not to use;
- data burden;
- identifiability risk;
- computational burden;
- extrapolation risk;
- BlueRev relevance;
- evidence strength.

### 3. State and parameter dictionary

Create a proposed state/input/output/parameter dictionary with:

- symbol/name;
- physical meaning;
- units and basis;
- model level M0-M3;
- measurement method;
- expected uncertainty;
- species specificity;
- source;
- whether value must be identified experimentally.

Do not populate unsupported numerical values.

### 4. Minimal experimental programme

Provide a prioritized experimental plan including:

- objective;
- manipulated variables;
- measured variables;
- required sampling frequency;
- expected information gain;
- model hypotheses discriminated;
- cost and difficulty class;
- dependencies;
- stop/go criteria.

Separate experiments needed before M0, M1, M2 and field deployment.

### 5. Literature evidence map

Organize sources by mechanism, species/strain, reactor type, scale and evidence quality. Highlight contradictory results and likely reasons for disagreement.

### 6. Data and implementation inventory

List open datasets, code, repositories and benchmark environments with links, licenses and reproducibility assessment.

### 7. BlueRev risk register

List the highest-risk modeling assumptions, how they could produce wrong design/control decisions, warning signals and the cheapest discriminating test.

### 8. Playbook candidates

Generate concise candidate playbook entries, each containing:

- problem addressed;
- decision enabled;
- model choices;
- selection rules;
- workflow;
- failure modes;
- escalation trigger;
- BlueRev application;
- required evidence;
- source list;
- freshness and maturity.

Do not create formula-only entries.

## Expected conclusion format

End with:

1. the recommended first BlueRev model architecture;
2. the ten highest-priority unknowns;
3. the first five experiments;
4. the sensors required for the first instrumented loop;
5. the mechanisms deliberately omitted from M0 and why;
6. the exact evidence that would trigger escalation to M1 and M2;
7. a research backlog ordered by value of information;
8. a list of claims that remain too weak to save as canonical guidance.

The report must be technically skeptical, citation-rich and explicit about uncertainty. It must distinguish what is known for *Nannochloropsis gaditana*, what is inferred from related organisms and what is merely a promising research direction.

---