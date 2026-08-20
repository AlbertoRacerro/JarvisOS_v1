MECHANICAL_WAVE_FEM_DISCOVERY_DELTA1
DATE=2026-08-20
BRANCH=audit/hermes-agent-2026-08-20
AUTHORITY=AUDIT_ONLY
FORMAT=AI_DENSE

SCOPE=BlueRev flexible marine structure; wave loads; hydrodynamics; global FEM; co-simulation; fatigue handoff.

1 PYHAMS/HAMS
- repo=NLRWindSystems/pyHAMS
- class=DIRECT
- license=Apache-2.0
- maturity=Beta; Python>=3.9; Fortran; Windows/Linux/macOS; wheels/CI/publish workflows.
- role=frequency-domain potential-flow BEM wrapper; write HAMS inputs; execute HAMS; read WAMIT-format added mass/damping/excitation.
- integration signal=strong packaging, simple numpy/meson/ninja deps, cross-platform.
- critical validation debt=test/test_cylinder.py contains regression truth arrays, but numerical assertions for added-mass/damping and excitation are commented out; current test mainly checks execution/readability/frequency grid. Packaging quality > scientific regression strength.
- verdict=strong DIRECT candidate for BlueRev hydrodynamic coefficients, but BlueCAD must add independent regression suite against analytic shapes + HAMS/Nemoh/Capytaine references before promotion.

2 CAPYTAINE/NEMOH LICENSING SPLIT
- Capytaine full package=GPLv3 => EXTERNAL, notwithstanding Apache-labelled/internal components.
- libDelhommeau internal Fortran component=Apache-2 candidate if isolated and license chain confirmed.
- Nemoh v2 lineage=Apache-2 candidate; deeper code-first comparison still pending.
- implication=do not accidentally import full Capytaine into proprietary runtime when only permissive hydrodynamic core is desired.

3 KRATOS STRUCTURAL MECHANICS
- repo=KratosMultiphysics/Kratos
- core license=permissive BSD-like 3-clause variant + advertising acknowledgement.
- StructuralMechanicsApplication same permissive family.
- capability observed={beam/truss/cable/shell/solid families; corotational beam; contact; dynamic/eigen/harmonic; adjoint/sensitivity; large test suite}.
- role candidate=global flexible structural FEM and local submodels; superior to building native BlueCAD FEM.
- PippoOS verdict=TAKE_SERIOUSLY; native BLUECAD should own model semantics/coupling/evidence, not FEM assembly/solvers.

4 KRATOS COSIMULATION + COSIMIO
- CoSimulationApplication license=permissive BSD-like + acknowledgement.
- CoSimIO license=same permissive family.
- architecture=detached standalone interprocess coupling library; explicitly no Kratos dependency; C++11; C/Python interfaces; sequential+MPI; memory exchange designed to avoid unnecessary copies.
- role candidate=numerical coupling bus across hydrodynamics/FEM/other solver processes.
- PippoOS verdict=TRY_BEFORE_BUILDING_CUSTOM_COUPLING_BUS.
- candidate future chain=wavespectra -> pyHAMS/HydroDyn/global hydro -> CoSimIO -> Kratos structural dynamics -> stress histories -> pyLife.
- caveat=frequency-domain BEM coefficients are not directly distributed time-dependent member loads; an explicit radiation/diffraction/state-space or load-reconstruction layer may be needed depending fidelity.

5 ARCHITECTURE UPDATE
CURRENT_FRONT_RUNNERS:
Hydro input={wavespectra DIRECT}
Potential-flow BEM={pyHAMS DIRECT strong candidate; Nemoh DIRECT candidate; Capytaine EXTERNAL oracle}
Structural FEM={Kratos DIRECT strong candidate}
Coupling={CoSimIO DIRECT strong candidate}
Fatigue={pyLife DIRECT strong candidate}
Mooring={MoorDyn v2 BSD-3; MoorPy BSD-3}

OPEN_DECISION_HIGH_PRIORITY:
- Is Kratos practical for flexible floating BlueRev global model with externally supplied hydrodynamic loads, including large rotations/member dynamics/contact at joints?
- Need compare MFEM/OpenSees/CalculiX/FEniCSx/SfePy or marine-specialized alternatives on structural nonlinear dynamics + joint/contact + license + Python integration + tests.
- Need material/joint taxonomy before fatigue backend finalization: welded/bolted/adhesive/polymer/composite each requires distinct local model.

6 VALIDATION PRINCIPLE
Any hydrodynamic/FEM backend must be promoted by BlueCAD evidence tests, not by README maturity:
- analytic canonical cases
- cross-solver agreement
- mesh/frequency/time-step convergence
- energy/reciprocity/conservation checks where applicable
- regression under exact input digest
- provenance of coefficients/material laws/load reconstruction.
