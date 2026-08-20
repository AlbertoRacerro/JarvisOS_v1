# BLUEREV PBR DISCOVERY DELTA2 — 2026-08-20
FORMAT=AI_FIRST; AUTHORITY=AUDIT_ONLY; IMPLEMENTATION_AUTHORIZED=NO; PREVIOUS={BLUEREV_PBR_DISCOVERY_2026-08-20.md,BLUEREV_PBR_DISCOVERY_CONTINUATION_2026-08-20.md}

## 0 DELTA
NEW={UAL2014 exact first-principles equation/parameter evidence+source inconsistencies; UAL 2022/2024 CFD->particle->light-history->dynamic photosynthesis framework; DTU 2026 fluxomic mechanistic model; dynamic radiative-property methodology; open pilot tubular Nannochloropsis benchmark}.
ARCH_IMPACT=HIGH: M1/M2/M3 ladder now has direct literature precedents and validation fixtures; light-history/mixing cannot be collapsed universally to mean irradiance.

## 1 UAL 2014 FIRST-PRINCIPLES TUBULAR PBR — EXACT MODEL EVIDENCE
SOURCE=Fernández et al./Acién/Guzmán UAL-CIESOL, "First Principles Model of a Tubular Photobioreactor for Microalgal Production", Ind Eng Chem Res 2014 53(27):11121-11136. Open-access web version inspected 2026-08-20.
ROLE=M2 distributed-1D/reference oracle.

### 1.1 Light field
Paper Eq1 average irradiance form:
`I_av(t,x) = [I0(t)*alpha/(Ka*Cb(t,x)*d_t,p)] * [1-exp(-Ka*Cb(t,x)*d_t,p)]`
where p={loop,column}; I0=horizontal solar irradiance; alpha=light-distribution factor; Ka=extinction coefficient; Cb=biomass; d_t,p=tube/column diameter.
Semantics: this is geometry/effective attenuation, not intrinsic spectral radiative transfer.

### 1.2 Model partition
BIOLOGY: photosynthesis modeled as nonlinear/hyperbolic light response multiplied/modified by pH, temperature, dissolved-O2 limitation/inhibition factors. Biological block reportedly has 18 characteristic parameters; 10 pH/O2/T parameters retained from lab-scale characterization; remaining calibrated.
SOLAR_RECEIVER/TUBE_LOOP: six mass balances (paper eq4,6,9,11,13,16) + heat balance eq25.
BUBBLE_COLUMN: five mass balances (eq5,8,10,12,14) + heat balances eq26,27.
VALIDATION=real outdoor pilot tubular PBR ~3.0 m3.
REPORTED_MEAN_ERRORS≈DO 3.43% and 10.81% at different positions; pH 1.56%; biomass 2.81%; temperatures 1.45%,1.27%,1.84%.

### 1.3 Parameter table extracted from web version
VALUES_AS_PRINTED; DO_NOT_IMPORT_WITHOUT_UNIT/SANITY_AUDIT:
- solar absorptivity a=0.5411
- A_t,c=0.1257 m2
- A_t,l=0.0055 m2
- a_c=0.0806 s-1
- b_c=0.7533
- a_l=0.0012 s-1
- b_l=0.8450
- A1=4.99e7
- A2=1.66e13
- B1=2.4098
- B2=533.009
- C0=0.996
- C1=6.2684
- C2=68.8062
- total inorganic carbon medium [CT]_m=8 mol/m3
- d_t,c=0.4 m
- d_t,l=0.084 m
- Ea1=4.27e4 [printed unit appears mol J^-1; likely dimensional/typographic issue]
- Ea2=7.71e4 [same warning]
- H_CO2=38.36 mol atm^-1 m^-3
- H_O2=1.07 mol atm^-1 m^-3
- h_ext=449.917 J s^-1 m^-2 °C^-1
- Ka=133.0324 m2/kg =0.1330324 m2/g
- Ki=173.9504 µE m^-2 s^-1
- K_CO2,c=K_CO2,l=0.91
- K_O2=0.7202 mol/m3
- L_c=3.2 m
- L_l=400 m
- m=0.0015
- n=0.9779
- [O2]_m=0.2812 mol/m3
- P_O2,max=4.37e-5 kg O2 kg^-1 s^-1
- respiration r=0.01
- U_inf=0.651 m/s
- U_gas=0.0186 m/s
- U_liq=0.0441 m/s
- fluid velocity V=1 m/s
- V_t,c=0.4021 m3
- V_t,l=2.2167 m3
- Vmol=20 L/mol
- Vext=20.3 L
- Y_o/x=0.9713 kg biomass/kg O2
- z=5.4333
- alpha_c=0.1052
- alpha_l=0.9725

### 1.4 Source inconsistencies / failure modes found
CRITICAL_NO_BLIND_IMPORT:
A) heat-transfer coefficients: prose/validation text reports `h_c=6.62`, `h_l=11.19`, but Table2 lists approximately `h_c=11.1886`, `h_l=6.6189`; possible c/l label swap.
B) molecular weights in table appear swapped: printed `M_CO2=32 g/mol`, `M_O2=44 g/mol`; physical values are CO2≈44.01, O2≈32.00. Treat table as typo until equation/source confirmed.
C) species label `[CO3^2-]` described as "bicarbonate" in table; CO3^2- is carbonate, HCO3- is bicarbonate. Terminology error.
D) printed `C_p = 1 kcal m^-3 °C^-1` is suspicious for water-like culture volumetric heat capacity (~10^3 kcal m^-3 °C^-1 order). Could be normalized/unit typo. Verify governing heat balance before use.
E) activation-energy units as rendered appear reversed/incorrect.
DECISION=paper is scientifically valuable but parameter ingestion requires dimensional-validation tests and cross-check against equations/source PDF.

## 2 UAL CFD -> PARTICLE TRACKING -> LIGHT HISTORY -> DYNAMIC PHOTOSYNTHESIS

### 2.1 2022 peer-reviewed tubular study
SOURCE=Fernández del Olmo / Acién / Fernández-Sevilla, "Productivity analysis in tubular photobioreactors using a dynamic photosynthesis model coupled to computational fluid dynamics particle tracking", Bioresource Technology 344 (2022) 126277; DOI 10.1016/j.biortech.2021.126277.
ROLE=M3 architecture/reference; DIRECT_REUSE_CODE=NOT_FOUND.
SYSTEM:
- tube diameters D={14,24,44,64,84} mm
- liquid velocities={0.4..1.0} m/s
- CFD cell/particle trajectories -> individual light histories I(t)
- dynamic photosynthesis model applied along trajectories
- uneven-sampling periodicity analyzed via Lomb-Scargle
- mixing/light-integration metric Gamma
FINDING=best reported mixing example approximately Gamma=0.199 for D=14 mm, v=1 m/s; larger tubes insufficient radial mixing; increasing v to 1m/s can add pumping cost without photosynthetic benefit.
KEY_VARIABLE=characteristic strain/frequency beta of light-dark exposure.
DECISION=light history is a real design variable; do not reduce all mixing effects to mean irradiance.

### 2.2 2024 design follow-up
SOURCE="Tubular photobioreactor design based on mixing intensity", Computers and Electronics in Agriculture 226 (2024) 109380; DOI 10.1016/j.compag.2024.109380.
COPYRIGHT=accessible SSRN copy states all rights reserved/no reuse without permission => RESEARCH_REFERENCE, not code source.
METHOD:
- CFD + light distribution -> I(t) for 50 tracked cells
- particle diameter=5 µm; density=1000 kg/m3
- same D={14,24,44,64,84}mm and v={0.4..1.0}m/s family
- dynamic photosynthesis -> Gamma mixing/integration factor
- generic-strain design example uses mu_max=0.075 h^-1, maintenance m=0.01 h^-1, alpha=200 µmol photons m^-2 s^-1
EXAMPLE_D14:
- perfect integration Gamma=1 -> predicted d_opt=0.0315 h^-1; productivity=182.5 g m^-3 h^-1
- mixing-intensity method -> d_opt=0.0125 h^-1; productivity=362.3 g m^-3 h^-1
IMPACT=perfect-light-integration assumption can materially distort optimum geometry/productivity.
IR_REQUIREMENT=M0/M1 mean-light assumption must be explicit and sensitivity-testable; M2/M3 should allow Gamma(mixing) correction or trajectory-resolved physiology.

### 2.3 Related raceway contrast
SOURCE=2021 Bioresource Technology 334:125226, "Analysis of productivity in raceway photobioreactor using CFD particle tracking coupled to dynamic photosynthesis model".
Reported raceway depth ~0.15m; velocities ~0.2-0.8m/s; Gamma≈0/perfect segregation in tested regime, implying increased velocity did not automatically create useful light integration.
USE=cross-geometry validation of Gamma concept.

### 2.4 Discovery consequence
GAP_REDEFINED: not "how to invent cell light-history modeling"; task is now reconstruct + audit the UAL/Brindley dynamic-photosynthesis chain and determine reproducible/open components.
NEXT={exact CFD solver/turbulence/particle settings; exact beta/Gamma equations; exact dynamic photosynthesis equations; Brindley2016 source/code; data availability/license}.

## 3 DTU 2026 FLUXOMIC MODEL — MECHANISTIC BIOLOGY CANDIDATE
SOURCE=Álvaro Pazo Vila; Niels H. Norsker; Krist V. Gernaey; Jakob K. Huusom (DTU PROSYS + ALGIECEL), "A fluxomic model of microalgae photoautotrophic growth for application in industrial photobioreactors", Algal Research 93 (Jan 2026) 104440; DOI 10.1016/j.algal.2025.104440.
PAPER_LICENSE=CC BY open access.
CODE_REPO=not found in GitHub searches as of audit.
DATA=paper data-availability statement says authors do not have permission to share underlying data.
MODEL:
- first-principles dynamic molecular-level model
- 10 ODEs
- photon capture
- photosynthetic electron transport
- photoinhibition
- thylakoid lumen/stroma pH regulation
- ATP/NADPH generation
- carbon fixation + photorespiration
- membrane O2/CO2 exchange
- macroscopic outputs include O2 production, carbon consumption, biomass growth
- literature-based parameterization; compared against multiple empirical sources; intended adaptable across species/industrial PBRs.
CLASS=CLEAN_ROOM_SCIENTIFIC_REFERENCE unless source code later appears with permissive license.
ROLE=M2-biological/mechanistic oracle candidate, not automatic implementation target.
DECISION=compare information/validation gain vs Nikolaou/Bernardi N.gaditana-specific lower-order dynamics and UAL/Brindley model before adopting 10-ODE complexity.

## 4 DYNAMIC RADIATIVE-PROPERTY MEASUREMENT METHODOLOGY
SOURCE=2022 open-access study "Assessment of Real-Time Radiative Properties and Productivity of Limnospira platensis in Tubular Photobioreactors" (species != Nannochloropsis).
VALUE=A+/S methodology reference for BlueRev experimental optical validation.
SYSTEM≈100L tubular PBR; 10 batch cultures; time-dependent radiative properties.
MEASURE/ESTIMATE={spectral absorption kappa_lambda, scattering sigma_lambda, phase function beta(theta,lambda)}.
LIGHT_SOLVER=Monte Carlo RTE; 19 tubes/connectors modeled independently.
COMPUTATION=ad-hoc MATLAB 2020a; parameter regression via GlobalSearch+fmincon; supplementary information exists.
DECISION=strong support for storing time/state-dependent intrinsic optical properties separately from effective reactor attenuation. Search code/supplement/license; species-specific values not transferable to N.gaditana.

## 5 OPEN PILOT TUBULAR NANN OCHLOROPSIS BENCHMARK
SOURCE=2020 Frontiers/PMC "Experimental and Model-Based Analysis to Optimize Microalgal Biomass Productivity in a Pilot-Scale Tubular Photobioreactor"; strain Nannochloropsis granulata.
OPEN_DATA=supplement includes original time series + reorganized dataset from 15 batch experiments.
LIGHT=incident ~19-836 µmol m^-2 s^-1; average ~337.
FITTED_MODEL_VALUES:
- mu_max=1.56 d^-1
- K_S,ph=1.89 [model-specific photon availability formulation; inspect units/equation before reuse]
- m_ph=0.346
- T_min=2.3°C
- T_opt=27.93°C
- T_max=32.59°C
VALIDATION=MAPE≈7.2%; optimization reported productivity gains order 35-39%; tested operation remained light-limited/no clear saturation.
CLASS=OPEN_SCIENTIFIC_DATA/reference; exact supplementary data license still to verify separately from article license.
ROLE=independent PE/model-validation benchmark for pipeline tooling even though species != N.gaditana.

## 6 UPDATED PBR IR REQUIREMENTS
Each light/growth parameter needs metadata:
`species,strain,physiological_state,nutrient_state,T,pH,salinity,spectrum,reactor_geometry,optical_depth,mixing_regime,measurement_or_fit,intrinsic_or_effective,source,uncertainty,validity_domain`.
Model assumption examples must be first-class:
`perfect_light_integration`, `mean_integral_irradiance_valid`, `uniform_biomass`, `fixed_carbon`, `no_dynamic_photoacclimation`, `fouling_absent`, `tube_orientation_static`.
Each assumption should have a promotion trigger.

## 7 UPDATED SEARCH PRIORITY
P0 reconstruct Brindley/UAL dynamic photosynthesis model: equations, beta,Gamma,code/data/license.
P0 extract UAL2014 Eq2 + mass balances and resolve source typos via PDF/other publications.
P0 audit UAL lumped model exact equations/parameters.
P0 inspect downloadable UAL virtual-lab packages/source/license.
P1 inspect 2022 radiative-property supplementary package + license; adapt experimental method, not values.
P1 locate N.gaditana raw spectra/cross-sections with state metadata.
P1 locate seawater carbonate+kLa+Nannochloropsis code/data.
P2 compare 2026 DTU fluxomic 10-ODE model vs N.gaditana-specific Nikolaou/Bernardi + UAL reduced dynamics using PIPPO_OS criterion.
