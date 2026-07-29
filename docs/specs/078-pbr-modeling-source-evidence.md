# Spec 078 — source evidence

Companion to `078-pbr-modeling-0.md`. Material claims in the planning kernel resolve to the rows
below. This file records evidence only; it does not authorize implementation.

## 1. Epistemic labels

| Label | Meaning |
|---|---|
| `RUNTIME_VERIFIED` | Read from merged runtime source at the pinned ref. |
| `TEST_VERIFIED` | Read from merged test source at the pinned ref. |
| `REPO_DOCUMENTED` | Read from merged repository prose such as `STATUS.md`, a spec, or a readiness decision. |
| `VENDOR_DOCUMENTED` | Stated by vendor documentation; never sufficient for a physical claim. |
| `LITERATURE_SUPPORTED` | Supported by located and read primary scientific literature. |
| `INFERRED` | Derived from verified facts rather than directly observed. |
| `PROPOSED` | Candidate decision with no evidential authority. |
| `UNKNOWN` | Not established. |
| `BLOCKED` | Cannot be established until a named obstacle is cleared. |

> **Maintainer decision at merge.** `REPO_DOCUMENTED` is a ninth label added to the eight-label
> brief because first-party repository prose is neither runtime, test, vendor evidence nor an
> inference. If rejected, these rows must be reclassified to `INFERRED`; they are not deleted.

**Pinned verification baseline:** `132856f057c27d2800086912fa1cc926a72056eb`, verified identical
to `master` before branch creation on 2026-07-29. SHA-pinned reads and explicit 404 responses were
used. Code and tests at that SHA override all earlier unpinned notes.

## 2. Vendor manual corpus — `BLOCKED`

No vendor-manual claim is used by the kernel. Three of four transferred PDFs were stubs below one
kilobyte or link notes whose filenames did not match their contents. The only genuine PDF was
*Introduction to COMSOL Multiphysics 6.4* (122 pages), and it was not used as physics authority.
The claimed Chemical Reaction Engineering and Liquid/Gas Properties guides were not usable.

To clear the blocker, re-supply each manual, verify content type and SHA-256, then map exact pages.
Vendor material may establish capabilities, workflows, inputs, outputs and validation practice;
physical claims require public scientific literature.

## 3. Runtime and test evidence

All paths are at the pinned baseline above.

### 3.1 Units, components and streams

| ID | Path | Verified fact | Label | 078 implication |
|---|---|---|---|---|
| `RT-01` | `backend/app/modules/process_kernel/units.py` | `process_semantic_units_v1` contains eleven exact semantic tokens: `gDW`, `kgDW`, `mgN`, `gN`, `mgP`, `gP`, `gC`, `kgC`, `mLCO2`, `LCO2`, `EUR`. | `RUNTIME_VERIFIED` | New PBR quantities require reviewed semantic-unit changes. |
| `RT-02` | same | `normalize_magnitude` rejects mismatched semantic bases with `quantity_semantic_basis_mismatch`. | `RUNTIME_VERIFIED` | Existing protection against physically compatible but semantically different units. |
| `RT-03` | same | Physical dimensions form a closed fifteen-entry set with no substance, photon-flux or mass-rate dimension. | `RUNTIME_VERIFIED` | Decision `U2` must precede any PAR or dissolved-species contract. |
| `RT-07` | `backend/app/modules/process_kernel/components.py` | Catalogue contains water, CO2, O2 and a formula-less fixture biomass pseudo-component. | `RUNTIME_VERIFIED` | Decision `U3`; no scientific biomass composition currently exists. |
| `RT-08` | `backend/app/modules/process_kernel/streams.py` | Composition is catalogue-keyed fractions summing to one within `1e-12`; no absolute concentration or phase split is represented. | `RUNTIME_VERIFIED` | Decision `U1`; dissolved CO2/O2 cannot be silently placed into the current composition field. |

### 3.2 Execution and extension surface

| ID | Path | Verified fact | Label | 078 implication |
|---|---|---|---|---|
| `RT-09` | `backend/app/modules/process_kernel/contracts.py` | `UnitOperation` is a `runtime_checkable Protocol`; blocks conform structurally. | `RUNTIME_VERIFIED` | A later additive block can reuse the protocol without a registry rewrite. |
| `RT-10` | same | Blocks declare separate `caller_parameters` and `profile_constants`. | `RUNTIME_VERIFIED` | Operating conditions remain bindings; scientific coefficients require immutable profile authority. |
| `RT-11` | `backend/app/modules/process_kernel/flowsheet.py`; `backend/app/core/topology.py` | Deterministic topological ordering; cycles fail as `topology_cycle`; limits are 64 blocks and 256 connections. | `RUNTIME_VERIFIED` | Recycle solving is outside the current kernel. |
| `RT-12` | `backend/app/modules/process_kernel/flowsheet.py` | `execute` performs one forward pass with no state, time loop, iteration, convergence or tear stream. | `RUNTIME_VERIFIED` | Decision `U4`; dynamics cannot be smuggled into existing semantics. |
| `RT-13` | same | Scalar connections require exact `unit`, `physical_dimension` and `semantic_basis`; all inlets need a driver. | `RUNTIME_VERIFIED` | Later PBR ports must declare exact compatible contracts. |
| `RT-14` | `backend/app/modules/process_kernel/blocks.py` | `Pipe` fails with `correlation_not_qualified` outside its qualified Reynolds envelope. | `RUNTIME_VERIFIED` | Precedent for fail-closed kinetic and transfer validity domains. |
| `RT-15` | `backend/app/modules/process_kernel/contracts.py` | `BlockResult.diagnostics` is a free-form mapping; executor validates output shape and finite scalar values, not diagnostic semantics. | `RUNTIME_VERIFIED` | A full spec must own diagnostic keys and invariant errors. |
| `RT-45` | `backend/app/modules/process_kernel/__init__.py` and package files | Public exports include streams, components, typed ports, block/result protocol, four blocks, flowsheet, 047 profile and semantic-unit helpers. | `RUNTIME_VERIFIED` | Confirms the exact 075 extension boundary. |
| `RT-46` | `backend/app/modules/process_kernel/flowsheet.py` | Execution requires exact block parameter sets and exact declared profile-constant sets. | `RUNTIME_VERIFIED` | A later profile cannot accept undeclared coefficients. |

### 3.3 Existing BlueRev models and binding boundary

| ID | Path | Verified fact | Label | 078 implication |
|---|---|---|---|---|
| `RT-42` | `docs/specs/STATUS.md`; `backend/app/modules/runner/safety.py` | 043 owns the narrow bundled `calc_v0` contract, AST policy and deterministic artifact boundary. | `REPO_DOCUMENTED` / `RUNTIME_VERIFIED` | 078 definition does not widen runner authority. |
| `RT-43` | `backend/app/modules/runner/examples/` | 047, 048, 049 and 072 have bundled Python implementations and sibling v1 forward input contracts with typed variables. | `RUNTIME_VERIFIED` | New identities must coexist with, not replace, these models. |
| `RT-44` | `backend/app/modules/runner/input_contracts.py`; `docs/specs/STATUS.md` | 071 provides immutable input contracts, binding preview, normalized input sets and forward degree-of-freedom inspection. | `RUNTIME_VERIFIED` / `REPO_DOCUMENTED` | Caller-controlled operating values remain under 071. |
| `RT-48A` | `backend/app/modules/runner/examples/bluerev_biomass_nutrients_harvest_v0.py` | 048 imposes volumetric productivity; reports biomass/nutrient/gas-equivalent/harvest/economic screening; diagnostics say gas transfer is not evaluated. | `RUNTIME_VERIFIED` | 078 must not describe 048 as kinetic or mass-transfer prediction. |
| `RT-49A` | `backend/app/modules/runner/examples/bluerev_buoyancy_optical_screening_v0.py` | 049 uses Beer-Lambert-like transmittance proxies and explicitly says light-growth coupling, spectral PAR, scattering and radial field are not evaluated. | `RUNTIME_VERIFIED` | 078 begins at the declared proxy boundary rather than rewriting 049. |

### 3.4 Verification classes and dependencies

| ID | Path | Verified fact | Label | 078 implication |
|---|---|---|---|---|
| `RT-32` | `backend/tests/test_bluerev_geometry_hydraulics_v0.py` | Algebraic model tests use explicit numerical tolerances and repeated-run determinism checks. | `TEST_VERIFIED` | Existing tolerance-test class. |
| `RT-34` | `docs/specs/075-process-kernel-1.md`; `docs/specs/075-readiness-2026-07-27.md` | 075 requires canonical 047 equality of keys, units, `float.hex()` values, diagnostics, bytes and SHA-256. | `REPO_DOCUMENTED` | Requirement is narrow and fixture-specific. |
| `RT-35` | `backend/tests/bluecad/test_manifest_determinism_canary.py` | Exact manifest digest canary runs only under pinned `ubuntu24-py311` profile metadata. | `TEST_VERIFIED` | Pinned-platform exactness, not cross-environment identity. |
| `RT-37` | `backend/tests/test_process_kernel_075_identity.py` | `test_process_kernel_matches_canonical_047_bytes_and_float_hex` enforces schema/status, diagnostics, keys, units, every numeric `float.hex()`, canonical bytes and SHA-256 against legacy 047 fixtures. | `TEST_VERIFIED` | Corrects the supplied false absence claim. It proves same-machine canonical 047 parity only; it is not a generic 078 verification tier. |
| `RT-38` | `backend/requirements.txt` | Runtime dependencies include FastAPI, Uvicorn, Pydantic, HTTPX, build123d, PyYAML and Pint; no NumPy, SciPy, SUNDIALS, CasADi or Assimulo. | `RUNTIME_VERIFIED` | No general scientific solver exists, but closed forms or a bounded fixed-step method may need no new dependency. |

These three verification classes are distinct: tolerance tests, same-machine canonical parity, and
pinned-platform exact-digest canaries. None establishes unconditional cross-environment identity.

## 4. Registry and planning evidence

| ID | Source | Verified fact | Label | Implication |
|---|---|---|---|---|
| `RT-39` | `docs/specs/STATUS.md` and explicit path reads at the baseline | No 078 row existed and both target 078 files returned 404; no open 078 PR or branch was found before branch creation. | `REPO_DOCUMENTED` | 078 was free. |
| `RT-47` | `docs/specs/STATUS.md` priority section | Baseline items 8–10 covered 075/076/077, then 069, then residual backlog. This PR proposes inserted item 9 and renumbers the old 9–10. | `REPO_DOCUMENTED` | Merge explicitly approves the priority amendment. |
| `RT-48` | `docs/specs/STATUS.md` | 043 is merged in #52; 047 in #143; 048 in #150; 049 in #153; 071 in #147; 075 in #191; 077 is `ready` with no Implementation PR. | `REPO_DOCUMENTED` | All 078 hard dependencies are merged at the pinned baseline; live state remains owned by `STATUS.md`. |

## 5. Literature required, not yet obtained

No scientific literature was searched or read for this definition. The identifiers below are
source categories to locate, not citations.

| ID | Required evidence | Label |
|---|---|---|
| `LIT-01` | Strain-specific *Nannochloropsis* light-response data, acclimation, temperature, salinity, photon-flux range and parameter uncertainty. | `PROPOSED` |
| `LIT-02` | Validity/error of a one-dimensional path-averaged Beer-Lambert treatment for tubular PBRs. | `PROPOSED` |
| `LIT-03` | CO2/O2 Henry constants in seawater with temperature and salinity correction. | `PROPOSED` |
| `LIT-04` | Measured `kLa` ranges/methods and usable correlations for tubular or airlift PBRs. | `PROPOSED` |
| `LIT-05` | Biomass carbon/oxygen composition for mass-balance closure. | `PROPOSED` |
| `LIT-06` | Respiration and maintenance rates, including dark periods. | `PROPOSED` |
| `LIT-07` | Published integrated-PBR benchmark or experimental dataset. | `PROPOSED` |

## 6. Claims explicitly withheld

- No rate law is claimed correct for *Nannochloropsis*.
- No photoinhibition assumption is accepted before `LIT-01`.
- No scattering, spectral, radial-field, carbonate, alkalinity, pH or nitrogen-quota claim is made.
- Gas-transfer stiffness and CFD necessity are `UNKNOWN`, not assumptions.
- Vendor agreement is not physical validation.
- Cross-environment bit identity and a generic 078 bit-identical tier are not established.
