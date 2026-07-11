# BlueRev Engineering Knowledge Validation Model v2

## Meaning of technical and industrial validity

A knowledge unit is **formally valid** when its equations, logic, units and limiting cases are correct under the assumptions stated in the unit.

This does not prove that the same unit is accurate for BlueRev. A general equation may be correct while its coefficients, geometry, boundary conditions or biological assumptions are wrong for a floating marine photobioreactor.

## Four independent validation axes

### 1. Formal validity

Question: is the method internally correct?

Evidence can include dimensional consistency, conservation-law residuals, analytical derivation, independent numerical reproduction and correct limiting behavior.

### 2. Evidence maturity

Question: how strong and independent is the support?

A lecture, a preprint, a standard and a replicated experiment do not carry the same evidential weight. Multiple files from one course are not counted as independent confirmation.

### 3. BlueRev transfer validity

Question: does the knowledge apply to BlueRev's real geometry, species, salinity, materials, weather, fouling, sensors and operating modes?

General methods may still require BlueRev parameterization, design adaptation or an experiment.

### 4. Industrial validity

Question: can the method support a real product or operating decision at acceptable reliability, maintainability, cost and organizational complexity?

A method can be mathematically correct and still fail industrially because sensors drift, computation is too slow, marine maintenance dominates the benefit, equipment cannot be cleaned or replaced, or implementation cost exceeds the economic gain.

## Decision statuses

- `reference_safe`: safe as scoped general engineering reference.
- `design_candidate`: useful for design exploration with explicit caveats.
- `experiment_required`: must be tested before it drives a BlueRev design decision.
- `deployment_candidate`: has sufficient BlueRev and pilot evidence to be considered for implementation.
- `blocked`: has an unresolved technical or evidential problem.

`reference_safe` never means `ready to deploy`.

## Examples

- Darcy-Weisbach is established engineering knowledge; BlueRev still needs roughness, fouling and regime data for its real tubes.
- Economic MPC can be mathematically sound and simulation-supported while remaining unvalidated on BlueRev hardware, biology and economics.
- A standard-backed automation architecture does not prove that one specific Smart Joint interface is complete or cost-effective.
- A reduced-order FEM model may reproduce its parent simulation but remain unsafe for maintenance decisions until loads, sensing and uncertainty are validated.
