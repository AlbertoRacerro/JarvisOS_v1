# Model calibration and optimal-experiment-design discovery — 2026-08-20

Status: audit/reference only; **not implementation authority**.

## Why this exists

The BlueRev modeling strategy intentionally starts with strong, explicit assumptions. A high-leverage future capability is therefore not merely a more complex simulator, but a workflow that can determine:

1. which uncertain parameters materially affect predictions;
2. which experiment would reduce that uncertainty most efficiently;
3. how to estimate parameters and uncertainty from measured data;
4. whether a more complex candidate model is statistically justified;
5. whether a proposed replacement assumption should be promoted into the engineering model.

This audit compares several external projects without sunk-cost or prestige bias.

---

## CAL-OED-01 — OMEGA/Imperial MAGNUS

Source: `omega-icl/magnus`  
Origin: Benoit Chachuat / OMEGA Research Group, Imperial College London  
Evidence: CODE-FIRST  
Reference value: **S**  
Implementation timing: **EARLY ORACLE / POSSIBLE BOUNDARY BACKEND; NOT FULL DIRECT INTEGRATION YET**

### What is actually implemented

MAGNUS is a C++/pybind11 framework built on the OMEGA stack:

- MC++ for expression DAGs, differentiation/evaluation and set arithmetic;
- CRONOS for dynamic-system integration and sensitivities;
- CANON for numerical optimization;
- MAGNUS classes for parameter estimation (`PAREST`), nested-sampling feasibility analysis, model-based design of experiments (`EXPDES`) and model discrimination.

The source is substantial: `parest.hpp`, `expdes.hpp`, `ffdoe.hpp`, feasibility/sampling modules and explicit Python bindings. The repository contains multiple families of C++ test/example programs for parameter estimation, experiment design, model discrimination and nested-sampling feasibility. It does not currently show a GitHub Actions CI directory, so the existence of test programs should not be confused with proof that every current commit is continuously regression-tested.

### Direct microalgae relevance discovered in code

`src/interface/bioreactor.py` is a complete parameter-estimation example for the published del Rio-Chanona et al. dynamic model of *Nannochloropsis oceanica* growth and lipid biosynthesis in a bubble-column photobioreactor.

The model states are:

- biomass `X`;
- nitrate `N`;
- internal nitrogen quota `q`;
- FAME quota `f`.

It uses incident irradiance as an experimental control and implements:

```text
I(z) = I0 exp[-(epsilon0 + epsilonX X) z]
mu(z) = mu_m I(z) / (kI + I(z) + I(z)^2/kI')
mu_bar = depth average of mu(z)
```

with Simpson/trapezoidal-style numerical averaging over the illuminated depth, then Droop-like internal-quota growth and nitrate uptake. Experimental outputs include biomass, nitrate, internal quota, FAME quota and chlorophyll-fluorescence Y(II).

The example defines two irradiance experiments (`I0 = 80` and `160 µmol m^-2 s^-1`), embeds their measured datasets and uncertainty/weight records, constructs two dynamic model instances in the computational DAG, defines 15 parameter bounds and runs maximum-likelihood parameter estimation through `ParEst`.

This is unusually close to the intended BlueRev M0→M1 progression and is much stronger evidence than a generic README claim.

### Licensing

There is no single conventional root license text; the root `LICENSE` instructs users to inspect per-file headers. Core files inspected in MAGNUS, MC++, CRONOS and CANON state that they are published under the **Eclipse Public License**.

Treat the OMEGA code family as **BOUNDARY / LICENSE-REVIEW REQUIRED**, not DIRECT, until exact EPL version, linking/distribution obligations and all relevant file/dependency licenses are mapped.

### Integration-cost problem

The default installation/build path is heavy. Current instructions require or discuss:

- BLAS/LAPACK, Boost, Armadillo;
- HSL MC13/MC21/MC33;
- SUNDIALS/CVODES and SuiteSparse;
- MC++, CRONOS, CANON;
- SNOPT;
- GAMS;
- Gurobi.

CANON's current default `makeoptions.mk` enables SNOPT, Gurobi and GAMS. IPOPT support exists but is commented out. CPLEX support is also present but disabled in that file.

Therefore the full stack is not currently a low-friction Jarvis dependency and would introduce solver licensing/deployment complexity.

### Disposition

Split the value:

- **PAREST / microalgae model reference:** very high value and potentially usable earlier through a narrow boundary or a clean reimplementation of equations from the cited publication;
- **full MAGNUS MBDoE stack:** S-grade oracle/research reference, but not justified as an immediate core dependency;
- **design principle:** BLUECAD should eventually support `model -> parameter uncertainty -> informative experiment -> evidence -> model update` regardless of which numerical backend wins.

---

## CAL-OED-02 — pyPESTO

Source: `ICB-DCM/pyPESTO`  
License: **BSD-3-Clause**  
Evidence: CODE-FIRST  
Reference value: **S for parameter estimation/UQ**  
Implementation timing: **STRONG DIRECT CANDIDATE FOR PARAMETER ESTIMATION; NOT A COMPLETE MBDoE REPLACEMENT**

### What the code provides

pyPESTO is a mature Python parameter-estimation framework with a large package/test surface. The architecture separates objective functions, optimization, profiling, sampling, ensembles, prediction, model selection, hierarchical data handling, PEtab integration and execution engines.

The core `Objective` abstraction accepts arbitrary callables for:

- scalar objective value;
- gradient;
- Hessian;
- residual vector;
- residual sensitivities.

This means a native BLUECAD ODE model does not need to be rewritten in SBML/AMICI merely to use basic pyPESTO optimization. Higher-performance simulator integrations remain optional.

Core install dependencies are ordinary Python scientific packages (`numpy`, `scipy`, `pandas`, `matplotlib`, `h5py`, etc.). AMICI, PEtab, IPOPT, NLopt, Fides, JAX, PyMC, emcee, dynesty, MPI and others are optional extras.

### BlueRev value

For an early `M0 calibration` capability, pyPESTO is more practical than the full MAGNUS stack:

```text
BLUECAD model(parameters, experiment)
 -> residuals against measured data
 -> pyPESTO multistart optimization
 -> confidence/profile/sampling analysis
 -> ParameterReplacementProposal
```

It is also permissively licensed and Python-native.

### Limitation relative to MAGNUS

pyPESTO is primarily parameter estimation and uncertainty quantification. It does not, by itself, provide the same integrated model-based optimal experimental campaign machinery represented by MAGNUS `EXPDES`.

Disposition: **DIRECT candidate for the calibration/UQ layer; keep MAGNUS as a stronger MBDoE/model-discrimination reference until a lower-friction winner is identified.**

---

## CAL-OED-03 — BoFire

Source: `experimental-design/bofire`  
Origin: industrial/academic experimental-design community including chemical/pharma practitioners  
License: **BSD-3-Clause**  
Evidence: CODE-FIRST  
Reference value: **S for constrained real-experiment design / Bayesian optimization**  
Implementation timing: **FUTURE DIRECT CANDIDATE FOR CLOSED-LOOP EXPERIMENT OPTIMIZATION**

### What the code really provides

BoFire has a broad strategy architecture for experimental design and Bayesian optimization, including explicit domain/input/output/constraint data models, surrogate-based strategies, random/factorial methods and a substantial `strategies/doe` implementation.

The DoE code directly implements multiple information/design criteria including:

- D-optimality;
- A-optimality;
- E/G/I/K criteria;
- space filling.

Its model-based objectives build design matrices from a specified formula and evaluate information criteria with Torch automatic differentiation for Jacobians/Hessians. The code also handles constrained domains and mixed experimental spaces elsewhere in the package.

The project is actively evolving; current 2026 issues/PRs include nonlinear-constraint unification, Hessian support and replacement of IPOPT by another optimizer. Treat its API as active rather than frozen.

### BlueRev value

BoFire is very attractive for the **outer experimental campaign**:

```text
choose T / irradiance / flow / CO2 / nutrient / residence-time experiment
 -> obey equipment and safety constraints
 -> run experiment
 -> update surrogate / observed objective
 -> choose next experiment
```

It may also become useful for design-space exploration and multi-objective optimization of BlueRev itself.

### Limitation relative to MAGNUS

Its current classical DoE objective works from an explicit regression/model matrix rather than natively taking a nonlinear dynamic ODE, propagating parameter sensitivities and constructing the mechanistic Fisher information matrix across a time-varying experimental trajectory.

Therefore BoFire should not be called a drop-in replacement for MAGNUS MBDoE. A useful future hybrid may be:

```text
BLUECAD mechanistic model + sensitivity backend
    -> information/uncertainty metrics
    -> BoFire constrained candidate/campaign optimization
```

Disposition: **DIRECT S-grade candidate for experimental-design/BO infrastructure, but not required for M0.**

---

## CAL-OED-04 — huckgroup/OED

Source: `huckgroup/OED`  
Evidence: CODE-FIRST  
License: **no root license found in audit**  
Reference value: **B-/C+**  
Implementation timing: **CLEAN-ROOM / CONCEPT REFERENCE ONLY**

### Positive evidence

Despite only a few stars, the repository contains real code for biochemical-system model compilation, measurements, sensitivity-based scoring and optimization of time-dependent experimental inputs. The iterative-design folder includes substantial modules for model construction, measurements, optimization operations, distributions and pulse-pattern experiment mutation.

This is a good example of why low-visibility repositories are worth searching.

### Negative evidence

The inspected optimization code is research-script quality rather than reusable infrastructure:

- broad wildcard imports;
- global/module coupling;
- many typos and weak naming/contracts;
- randomized mutation/recombination heuristics embedded directly in experiment operations;
- no root software license found;
- no obvious modern package/test/CI boundary from the repository structure.

Disposition: retain selected ideas about **time-dependent input pulse design and iterative experiment generation**, but do not integrate this code.

---

# Current winner map

| Need | Current best candidate | Why |
| --- | --- | --- |
| Fit M0/M1 parameters from experiments | **pyPESTO** | permissive, Python-native, generic callable objectives/residuals, mature UQ/optimization ecosystem |
| Scientific reference for dynamic mechanistic parameter estimation | **MAGNUS + its N. oceanica example** | unusually close to BlueRev biology and rigorous DAG/sensitivity framework |
| Full mechanistic model-based experimental design | **MAGNUS reference remains strongest found here** | integrated dynamic model/sensitivities/FIM/experiment design, but dependency/licensing cost is high |
| Constrained real-experiment / Bayesian optimization loop | **BoFire** | mature domain/constraint/strategy architecture, BSD, active industrial use |
| Low-visibility ideas for time-varying experimental forcing | **huckgroup/OED (concept only)** | real research implementation but weak packaging/licensing |
| Execute P-I / growth characterization protocols | **SmartBioTech PBR-ControlScripts** | direct automation of real PBR measurements and stability-gated campaigns |
| Filter noisy bioreactor observations / infer growth state | **Pioreactor patterns** | mature sensor/event/state-estimation pipeline |

# Architectural consequence for JarvisOS / BLUECAD

A future `AssumptionReductionLoop` should not depend on one monolithic scientific library. A better contract is:

```text
ModelSpec + Assumptions + Parameters + uncertainties
             |
             v
Sensitivity / identifiability analysis
             |
             +--> parameter calibration backend (pyPESTO first candidate)
             |
             +--> experiment-design backend (BoFire and/or future mechanistic MBDoE)
             |
             v
ExperimentSpec
  controls + bounds + safety + measurements + stopping criteria
             |
             v
Jarvis/Hermes execution orchestration
             |
             v
measured Evidence + calibrated parameter posterior/profile
             |
             v
ParameterReplacementProposal / AssumptionReplacementProposal
             |
      deterministic validation + user/policy promotion
```

This is a potentially differentiating BLUECAD capability: the AI should not merely tell the engineer that an assumption is weak; it should eventually be able to propose the cheapest informative experiment needed to remove it.

# Immediate implication

None of these packages is required to make BlueRev M0 run.

However, when the first experimental data become available, **pyPESTO is currently a better first integration candidate than importing full MAGNUS**. MAGNUS should remain near the front of the research/reference queue because its microalgae example and MBDoE implementation can inform the contracts and validate later higher-fidelity capability.
