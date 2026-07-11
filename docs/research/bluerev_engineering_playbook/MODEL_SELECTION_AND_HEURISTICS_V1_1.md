# Model Selection and Engineering Heuristics v1.1

## Objective

The playbook must teach **how to choose and apply engineering methods**, not store formulas that are already trivial to retrieve.

A canonical playbook records:

- when a method is appropriate;
- when its assumptions fail;
- alternatives to compare;
- decision rules and escalation triggers;
- workflow, checkpoints and stop conditions;
- diagnostics, failure modes and fallback;
- BlueRev applications and required evidence.

## Expansion

The external v1.1 package retains the 96 v1 playbooks and adds **228** model-selection, procedure-selection and engineering-heuristic playbooks, for **324 total**.

The new coverage includes:

- cross-cutting engineering judgment: units, conservation, limiting cases, dominant resistance, identifiability, observability and model-form error;
- interfacial transport: two-film, Higbie penetration, Danckwerts surface renewal, reactive-film and resolved alternatives;
- equilibrium-stage versus rate-based methods; HTU/NTU versus HETP versus rigorous models;
- steady versus dynamic, lumped versus distributed and 0D/1D/2D/3D model selection;
- thermodynamic-model, phase-equilibrium and property-method selection;
- batch/PFR/CSTR, ideal/nonideal reactor, kinetic and transport-limitation choices;
- rheology, turbulence, mixing, settling and hydraulic-transient model selection;
- numerical solvers, ODE/DAE, stiffness, event detection, discretization and continuation;
- PID/cascade/feedforward, MPC/EMPC/RTO, estimation and control-platform choices;
- instrumentation principle, calibration, sampling, redundancy and placement;
- digital-twin scope, authority, synchronization, ROM/surrogate and abstention choices;
- FEM/CFD element, turbulence, multiphase, FSI and V&V choices;
- offshore load, mooring, limit-state, inspection and deployment choices;
- reliability, safety, maintenance and OT-cyber method selection;
- economic, business-model, experiment, manufacturing and operations choices.

## Two-film example

The mass-transfer playbook does not store only an overall-coefficient equation. It asks whether the decision requires:

- an interpretable two-film resistance network;
- a fixed-contact-time penetration model;
- a surface-renewal age distribution;
- reactive-film/speciation coupling;
- separate coefficient and interfacial-area modelling;
- a bubble/drop population model or resolved multiphase CFD.

It requires compatible driving-force bases, time-scale analysis and a discriminating BlueRev experiment before scale-up.

## Retention rule

All valid playbooks are retained, including `future` and `fleet` directions. Maturity controls warnings and evidence requirements, not whether the capability is saved.

## Exclusions

The catalog still excludes as primary records:

- isolated standard formulas;
- definitions recoverable from authoritative references;
- exercise inputs and numerical answers;
- spreadsheet-cell results;
- unreviewed deployment or certification claims.

## Authority boundary

The catalog is ready for learning, design framing, alternative generation and experiment planning. Independent domain review, current-standard review and BlueRev prototype/field validation remain required before consequential use.
