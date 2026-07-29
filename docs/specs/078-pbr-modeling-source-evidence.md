# Spec 078 — source evidence

Companion to `078-pbr-modeling-0.md`. Every material claim in that document traces to a row here.

## 1. Epistemic labels

078-local vocabulary. The repository has no pre-existing evidence-labelling enum; the nearest
existing tokens are the sensitivity classes `S0`–`S4` owned by 059a/059b, and the outcome tokens
`not_characterized` and `not_computable` used by 048. These labels are declared for 078 and are
not authoritative elsewhere.

| Label | Meaning |
|---|---|
| `RUNTIME_VERIFIED` | Read verbatim from merged runtime **source code** at a stated ref. |
| `TEST_VERIFIED` | Read verbatim from merged **test source** at a stated ref. |
| `REPO_DOCUMENTED` | Read verbatim from merged **repository documents** — STATUS.md, specification prose, readiness decisions. First-party, but not executable evidence. |
| `VENDOR_DOCUMENTED` | Stated by vendor documentation. Never sufficient for a physical claim. |
| `LITERATURE_SUPPORTED` | Supported by primary scientific literature located and read. |
| `INFERRED` | Derived by reasoning from verified facts; not directly observed. |
| `PROPOSED` | A candidate for a later decision; carries no evidential weight. |
| `UNKNOWN` | Not yet established. |
| `BLOCKED` | Cannot be established until a named obstacle is cleared. |

> **Deviation for maintainer review.** The task brief specified eight labels and did not include
> `REPO_DOCUMENTED`. It is added because the brief's set has no honest slot for first-party
> repository prose: such text is neither runtime, nor test, nor vendor, nor an inference. Reject it
> and these rows collapse to `INFERRED`, which would overstate their uncertainty, or to
> `RUNTIME_VERIFIED`, which would overstate their authority.

**Pinned verification baseline.** The facts cited by §2 of the kernel were re-read directly at
`132856f057c27d2800086912fa1cc926a72056eb` on 2026-07-29. No runtime code was executed and no provider call was made. Rows that still
carry a dagger (†) retain provenance about the original collection route, but every daggered row
used by kernel §2 was independently checked against the pinned source or test before this document
was committed.

## 2. Vendor manual corpus — `BLOCKED`

No vendor manual evidence is recorded, and none may be cited until this blocker is cleared.

The manual bundle prepared for this work did not arrive intact. Verified by file-type inspection
and byte count on the received copies:

| Declared filename | Received size | Actual content |
|---|---|---|
| `03_Chemical_Reaction_Engineering_Module_Users_Guide_6.4.pdf` | 88 B | a Windows URL shortcut |
| `05_Liquid_and_Gas_Properties_Module_Users_Guide_6.4.pdf` | 747 B | Markdown link notes |
| `01_SuperPro_Designer_User_Guide_v11.pdf` | 802 B | Markdown link notes |
| `01_Introduction_to_COMSOL_Multiphysics_6.4.pdf` | 1 476 839 B | genuine PDF, 122 pages |
| `manuals_manifest.csv` | 3 271 B | Markdown prose, not CSV |
| `03_Modeling_Language_Reference_Official.url` | 2 463 B | the CSV manifest |

The source archive is intact; the defect is in the attachment transfer. The COMSOL *Heat Transfer
Module* guide was not among the transferred files.

**Consequence.** Only *Introduction to COMSOL Multiphysics 6.4* was readable, and it was not
consulted for physics. Any earlier statement that the *Chemical Reaction Engineering* or *Liquid
and Gas Properties* guides were usable as evidence is withdrawn.

**To clear.** Re-supply each file individually; verify each by content type and SHA-256 before
citation; never identify a source by its filename. Then map only the pages answering §5, recording
chapter and exact page interval per row.

Clean-room constraint on any future row: vendor documentation may establish capabilities,
workflows, concepts, expected inputs and outputs, validation practice and useful abstractions
only. It may not contribute source code, proprietary implementation detail, interface assets,
textual description beyond minimal citation, or proprietary formats. Physics authority is public
literature. A vendor row is never labelled `RUNTIME_VERIFIED`.

## 3. Runtime evidence

Repository `AlbertoRacerro/JarvisOS_v1`, pinned baseline
`132856f057c27d2800086912fa1cc926a72056eb`, re-read 2026-07-29; see §1.

### 3.1 Kernel typing, units and identity

| ID | Path | Owner | Concept | Label | Implication | Further verification |
|---|---|---|---|---|---|---|
| `RT-01` | `process_kernel/units.py` † | 075 | `SEMANTIC_UNIT_REGISTRY_VERSION = "process_semantic_units_v1"`; eleven tokens `gDW, kgDW, mgN, gN, mgP, gP, gC, kgC, mLCO2, LCO2, EUR`; each definition carries `token, pint_unit, scale_to_si, physical_dimension, semantic_basis` | `RUNTIME_VERIFIED` | Any new PBR quantity is added here with a distinct `semantic_basis` | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-02` | `process_kernel/units.py` † | 075 | `normalize_magnitude` refuses conversion across `semantic_basis`; error `quantity_semantic_basis_mismatch` | `RUNTIME_VERIFIED` | Existing mechanism mitigating `F1`. It does **not** address `F3`, which concerns parameter naming | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-03` | `process_kernel/units.py` † | 075 | Closed fifteen-entry dimension whitelist; anything else raises `unit_dimension_unsupported`. The set contains `volumetric_flow`, `velocity` and `acceleration` but no molar or substance dimension, no photon-flux dimension, and no mass-per-time rate dimension | `RUNTIME_VERIFIED` | Gap `G9`; a photon-flux dimension is required for incident PAR, which changes the registry hash — decision `U2` | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-04` | `process_kernel/units.py` † | 075 | `UnitRegistry(autoconvert_offset_to_baseunit=True)`, `lru_cache`, closed `_PINT_UNIT_ALIASES`, `EUR = [currency]`; no prefix or suffix inference | `RUNTIME_VERIFIED` | Pint is in the live path, not merely declared; bind the kinetics schema to it | Confirm at pinned SHA |
| `RT-05` | `process_kernel/units.py`, `canonical.py` † | 075 | `semantic_registry_sha256()` = `canonical_sha256(payload)`, payload = version plus all definitions sorted by token; `canonical_sha256` is SHA-256 over `json.dumps(sort_keys=True, separators=(",",":"), allow_nan=False)` | `RUNTIME_VERIFIED` | Hashes the **unit vocabulary only**; a drift detector, not a model or source identity mechanism | Confirm at pinned SHA |
| `RT-06` | `process_kernel/components.py` † | 075 | `Component.scientific_molar_mass_authority` required whenever a molar mass is set; `ScreeningMassConstants.authority = "merged 048 rounded screening constants"` | `RUNTIME_VERIFIED` | The house pattern for per-datum provenance; the precedent `G8` requires for kinetic parameter sources | Confirm at pinned SHA |
| `RT-07` | `process_kernel/components.py` † | 075 | Catalogue holds `water`, `carbon_dioxide`, `oxygen`, `fixture_biomass`; none carries a molar mass or elemental fractions; runtime-closed `MappingProxyType`, no registration hook; `component_catalog_sha256()` exists but is not exported | `RUNTIME_VERIFIED` | Decision `U3`; promoting biomass to a real component changes this hash | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-08` | `process_kernel/streams.py` † | 075 | Composition is per-component **fractions** summing to 1.0 within 1e-12 over catalogue keys; no phase split; mass-versus-mole basis never stated in code | `RUNTIME_VERIFIED` | Gap `G4`; absolute concentrations cannot be expressed — decision `U1` | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |

### 3.2 Kernel execution and extension surface

| ID | Path | Owner | Concept | Label | Implication | Further verification |
|---|---|---|---|---|---|---|
| `RT-09` | `process_kernel/contracts.py` | 075 | `UnitOperation` is a `runtime_checkable` `Protocol` with `block_id`, four port maps, `caller_parameters`, `profile_constants`, `solve(...) -> BlockResult` | `RUNTIME_VERIFIED` | Read directly, not through a subagent. A PBR block is added by structural conformance; supports `A3` | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-10` | `process_kernel/contracts.py` | 075 | `caller_parameters` and `profile_constants` are distinct declared tuples | `RUNTIME_VERIFIED` | Rate-law coefficients are profile constants; operating conditions remain 071 caller bindings | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-11` | `process_kernel/flowsheet.py`, `core/topology.py` † | 075 | Kahn's algorithm with a min-heap on node id; `MAX_PROCESS_BLOCKS = 64`, `MAX_PROCESS_CONNECTIONS = 256`; cycles rejected as `topology_cycle` | `RUNTIME_VERIFIED` | Execution order is stable and lexicographic; recycle is structurally impossible | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-12` | `process_kernel/flowsheet.py` † | 075 | Single forward pass; no time variable, no state between calls, no iteration, no convergence loop, no tear stream; blocks are frozen dataclasses | `RUNTIME_VERIFIED` | Gap `G7`; decision `U4` | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-13` | `process_kernel/flowsheet.py` † | 075 | Scalar connection requires exact equality of `unit`, `physical_dimension` and `semantic_basis`, no conversion at connect time; every declared inlet must be driven | `RUNTIME_VERIFIED` | New PBR scalar ports must declare these three attributes consistently across producer and consumer | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-14` | `process_kernel/blocks.py` † | 075 | `Pipe` raises `correlation_not_qualified` in the transitional Reynolds band and above the correlation ceiling | `RUNTIME_VERIFIED` | House pattern for `F4` and decision `U7` | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-15` | `process_kernel/contracts.py` | 075 | `BlockResult.diagnostics` is a free-form `Mapping[str, object]` the executor does not validate | `RUNTIME_VERIFIED` | Balance residuals can be emitted without a kernel change | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-16` | `process_kernel/profile_047.py` † | 075 | Module-level `MODEL_ID` / `PROFILE_ID` / `ASSEMBLER_ID`; `flowsheet_profile_sha256()`, `profile_constants_sha256()`, `assembler_contract_sha256()`; `model_identity` is `PROFILE_ID` | `RUNTIME_VERIFIED` | Content-hash identity is the pattern a bundled PBR profile registry mirrors | Confirm at pinned SHA |
| `RT-17` | `process_kernel/` † | 075 | `registry.py` and `profile_048.py` return 404; dispatch is by direct import; `__init__.py` exports only `execute_047_process_kernel` and `EXPECTED_UNITS` from the profile module | `RUNTIME_VERIFIED` | Absence evidenced by 404, not by a listing. `A4` has no existing registry to extend | Confirm at pinned SHA |
| `RT-18` | `process_kernel/` † | 075 | No conservation residual was found in the files read (`units`, `streams`, `components`, `contracts`, `blocks`, `flowsheet`, `profile_047`, `errors`, `canonical`); `streams.py` raises `stream_flow_inconsistent` rather than reporting a residual | `INFERRED` | Gap `G6`. This is a negative over the files read, not an exhaustive directory search | Confirm by directory enumeration at pinned SHA |
| `RT-45` | `process_kernel/__init__.py` | 075 | Exports `MaterialStream`, `Component`, `COMPONENT_CATALOG`, `SCREENING_MASS_CONSTANTS_V0`, `MaterialPort`, `ScalarPort`, `UnitOperation`, `BlockResult`, `ProcessFlowsheet`, `Pipe`, `Pump`, `Fitting`, `Reservoir`, `ProcessKernelError`, `EXPECTED_UNITS`, `execute_047_process_kernel`, `SEMANTIC_UNITS`, `SEMANTIC_UNIT_REGISTRY_VERSION`, `normalize_magnitude`, `semantic_registry_sha256` | `RUNTIME_VERIFIED` | Read directly. Fixes the public surface 078 may rely on | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-46` | `process_kernel/flowsheet.py` † | 075 | The flowsheet requires its `profile_constants` mapping to equal exactly the union of all block-declared constant names, and each block's caller-parameter set to match exactly | `RUNTIME_VERIFIED` | A PBR profile must declare its constant set exhaustively and exactly | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |

### 3.3 Merged screening models 048 and 049

| ID | Path | Owner | Concept | Label | Implication | Further verification |
|---|---|---|---|---|---|---|
| `RT-19` | `runner/examples/bluerev_buoyancy_optical_screening_v0.py` † | 049 | `T_tube = T_clean · (1 − f_daily)^t_clean`; `τ = a · X · L`; `T_culture = exp(−τ)`; `T_combined = T_tube · T_culture`; all optical outputs dimensionless | `RUNTIME_VERIFIED` | Gap `G1`: the output is a transmittance ratio, not an irradiance | Confirm at pinned SHA |
| `RT-20` | same † | 049 | No radiometric unit among the required or optional units; diagnostics declare `spectral_PAR_not_evaluated`, `radial_light_field_not_evaluated`, `scattering_not_evaluated`, `center_light_not_claimed`, `light_growth_coupling_not_evaluated` | `RUNTIME_VERIFIED` | Gaps `G1` and `G2` confirmed from code. Scope: this is a statement about 049, not about the whole repository | Confirm at pinned SHA |
| `RT-21` | same † | 049 | Transmission evaluated at the end of the cleaning interval, the dirtiest instant; no cycle average; diagnostics label `discrete_daily_compounding_proxy` | `RUNTIME_VERIFIED` | Failure mode `F7` | Confirm at pinned SHA |
| `RT-22` | same † | 049 | Three of four optical outputs carry a literal `_proxy` suffix; `optical_model` is `beer_lambert_like_transmission_proxy` | `RUNTIME_VERIFIED` | 078 matches this register when naming screening-grade outputs | Confirm at pinned SHA |
| `RT-23` | `runner/examples/bluerev_biomass_nutrients_harvest_v0.py` † | 048 | `productivity = values["volumetric_productivity"]`; diagnostics declare `productivity_is_imposed_input` | `RUNTIME_VERIFIED` | Gap `G3` | Confirm at pinned SHA |
| `RT-24` | same † | 048 | `equivalent_dilution = productivity / culture_concentration`; its ratio to `mu_max` is emitted but not enforced by any invariant | `RUNTIME_VERIFIED` | `maximum_specific_growth_rate` annotates rather than constrains | Confirm at pinned SHA |
| `RT-25` | same † | 048 | `carbon_demand = production_g_d · biomass_carbon_fraction · 1000`; `co2_equivalent = carbon_demand · (44/12) / 1000`; `oxygen_equivalent = carbon_demand · (32/12) / 1000` | `RUNTIME_VERIFIED` | The biological demand side of the CO2 model already exists; `S2` supplies only the transfer side | Confirm at pinned SHA |
| `RT-26` | same † | 048 | `co2_gas_rate = volume_l · co2_specific_gas_rate` is a bare unit scaling never reconciled with `co2_equivalent`; diagnostics declare `gas_transfer_not_evaluated` and `gas_rate_semantics = instantaneous_pH_control_benchmark`; no Henry constant, transfer coefficient or dissolved concentration | `RUNTIME_VERIFIED` | Gap `G5`; the `S2` sufficiency comparison is the missing reconciliation | Confirm at pinned SHA |
| `RT-27` | same † | 048 | Only stoichiometric evolution equivalents; `oxygen_volume_reference = STP_22.414_L_per_mol`; no dissolved concentration | `RUNTIME_VERIFIED` | Gap `G4` for O2 | Confirm at pinned SHA |
| `RT-28` | same † | 048 | N, P and C demands are independent one-liners; the only balance check is a dry-mass harvest split | `RUNTIME_VERIFIED` | Gap `G6` | Confirm at pinned SHA |
| `RT-29` | 048 and 049 † | 048, 049 | 048 raises `mass_balance_invalid`; 049 raises `result_invariant_invalid` | `RUNTIME_VERIFIED` | Decision `U8` | Confirm at pinned SHA |
| `RT-30` | 048 and 049 † | 048, 049 | A single optional input gates a `not_computable` status carried in diagnostics with a `reason`, rather than failing the run | `RUNTIME_VERIFIED` | House pattern for any 078 output not computable from the supplied bindings | Confirm at pinned SHA |
| `RT-31` | 048 and 049 † | 048, 049 | Both expose `operating_biomass_concentration`; nothing makes them consistent | `RUNTIME_VERIFIED` | Motivates one authoritative biomass quantity | Confirm at pinned SHA |
| `RT-43` | `bluerev_buoyancy_optical_screening_v0.contract.json`, `bluerev_biomass_nutrients_harvest_v0.contract.json` | 048, 049 | Contracts are `{schema_version, evaluation_mode, variables[]}`; each variable carries `name`, `label`, `unit`, `required`, `category`, `description`, `domain` with `min`/`max`/`exclusive_min`/`exclusive_max`; observed categories `design`, `property`, `equipment`, `operating`, `model_parameter`; `evaluation_mode` is `forward` | `RUNTIME_VERIFIED` | Read directly. The schema types unit, domain and category but carries no parameter source — gap `G8` | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |

### 3.4 Verification machinery

| ID | Path | Owner | Concept | Label | Implication | Further verification |
|---|---|---|---|---|---|---|
| `RT-32` | `backend/tests/test_bluerev_geometry_hydraulics_v0.py` † | 047 | `pytest.approx(rel=1e-12, abs=1e-15)` against expected values; `rel=1e-15` for internal algebraic consistency; `rel=1e-12` for metamorphic scaling; `!= pytest.approx(...)` for required difference | `TEST_VERIFIED` | A tolerance class already exists; 078 reuses it | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-33` | same † | 047 | `script_sha256` compared against `hashlib.sha256(SCRIPT_PATH.read_bytes())`; repeated-run digests compared for equality | `TEST_VERIFIED` | Model-code identity is already hash-pinned | Confirm at pinned SHA |
| `RT-34` | `docs/specs/075-process-kernel-1.md`, `075-readiness-2026-07-27.md` † | 075 | Identity is specified as equality of normalized inputs, output keys and units, numeric values by `float.hex()`, diagnostics, canonical `result.json` bytes and result digest across canonical 047 fixtures | `REPO_DOCUMENTED` | The documented class is enforced by `RT-37`; it remains a same-runtime canonical-047 equivalence contract, not a cross-platform guarantee | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-35` | `backend/tests/bluecad/test_manifest_determinism_canary.py` † | 056 | Exact dict equality of manifest digests, skipped unless `JARVISOS_BLUECAD_CANARY_PROFILE=ubuntu24-py311`; the profile pins Python major/minor, `platform.system()`, `platform.machine()` and library versions | `TEST_VERIFIED` | The only house pattern under which an integrated PBR output could carry an exact digest claim | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |
| `RT-36` | `backend/tests/` † | — | pytest, Python 3.11, run from `backend/` as `python -m pytest -q`; bundled model tests live flat at `backend/tests/test_<model>.py` | `TEST_VERIFIED` | Where a future 078 model test belongs | Confirm at pinned SHA |
| `RT-37` | `backend/tests/test_process_kernel_075_identity.py` | 075 | `test_process_kernel_matches_canonical_047_bytes_and_float_hex` runs canonical turbulent and laminar cases, compares output units and every numeric value through `float.hex()`, then requires canonical bytes and SHA-256 to equal the legacy 047 result | `TEST_VERIFIED` | The exact 075 identity mechanism exists. It is a precedent limited to canonical 047 same-runtime equivalence; future 078 models inherit no exact claim without their own authoritative comparison contract | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |

### 3.5 Dependency surface

| ID | Path | Concept | Label | Implication | Further verification |
|---|---|---|---|---|---|
| `RT-38` | `backend/requirements.txt` | `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx`, `build123d`, `PyYAML`, `Pint`; no NumPy, SciPy, SUNDIALS, CasADi or Assimulo | `RUNTIME_VERIFIED` | No general scientific solver exists. This does **not** imply that any dynamic model needs a dependency — linear transfer and exponential growth have closed forms, and a bounded fixed-step integrator needs none. Only robust adaptive integration would | Verified at `132856f057c27d2800086912fa1cc926a72056eb` |

## 4. Repository documents

| ID | Source | Concept | Label | Implication |
|---|---|---|---|---|
| `RT-39` | `docs/specs/STATUS.md` @ `132856f057c27d2800086912fa1cc926a72056eb` | 074, 075 and 076 are `merged`; 077 is `ready`; `078-pbr-modeling-0.md` and the 078 registry row are absent | `REPO_DOCUMENTED` | 078 is free at the pinned baseline |
| `RT-40` | `docs/specs/STATUS.md`, two reads of the same path | An uncached read returned a materially older revision, indistinguishable from current by formatting alone; a cache-busted read returned current content | `INFERRED` | Cache-busting or SHA pinning is mandatory for every read; formatting fidelity is not freshness |
| `RT-41` | `docs/specs/STATUS.md`, `scripts/check_spec_status.py` † | Status vocabulary is `planned, blocked, ready, in_progress, in_review, merged, cancelled`; `planned` must carry no pull-request link; dependencies must resolve and be acyclic; pull-request bodies declare `**Spec gate:**` | `REPO_DOCUMENTED` | Constrains the 078 row and the definition pull request exactly |
| `RT-42` | `docs/specs/STATUS.md` | 043 CALC-1 is described as adding the narrow `calc_v0` runner contract with AST policy, unit-bearing JSON outputs, deterministic artifacts and parameter proposals | `REPO_DOCUMENTED` | Registry description, not code. The AST policy referenced in §8 of the kernel rests on this and must be verified against 043's implementation before it is load-bearing |
| `RT-44` | `docs/specs/STATUS.md` | 071 MODEL-SCENARIO-DOF-0 is described as exposing immutable value-free model input contracts, forward binding and degree-of-freedom preview, and parameter-backed or manual scenario bindings | `REPO_DOCUMENTED` | Registry description, not code. Verify against 071's implementation before relying on binding behaviour |
| `RT-47` | `docs/specs/STATUS.md`, priority section | The `## Current priority and drafting order` section is a ten-item numbered list; item 8 covers merged 075, merged 076 and ready 077 under `077-readiness-2026-07-28.md` | `REPO_DOCUMENTED` | Fixes the insertion point for the D4 priority amendment |
| `RT-48` | `docs/specs/STATUS.md`, successive reads | 077 was read first as `planned` and later as `ready` with a readiness decision dated 2026-07-28. The later reading is current; the earlier was the stale revision described in `RT-40` | `INFERRED` | Not a live registry change. It is the same caching defect, and it reinforces gate 2 in §14 of the kernel |

At pinned baseline `132856f057c27d2800086912fa1cc926a72056eb`, STATUS.md records all six dependencies as merged: 043 in PR #52,
047 in PR #143, 048 in PR #150, 049 in PR #153, 071 in PR #147 and 075 in PR #191. These links are
registry evidence only; the runtime facts above were verified against their source and test files.

## 5. Literature required, not yet obtained

No literature was located or read in this session. Every entry is `PROPOSED` — a category of
source that must be found, read and recorded before the corresponding claim may leave `PROPOSED`.
No citation is asserted, and none may be carried forward without verification.

| ID | Question it must answer | Blocks | Label |
|---|---|---|---|
| `LIT-01` | Which light-response relation is appropriate for *Nannochloropsis*, from strain-specific data stating acclimation history, temperature, salinity, photon-flux range, measured quantity and parameter uncertainty — including whether the appropriate form exhibits photoinhibition at all | Decision `U5`; the growth model in `S1` | `PROPOSED` |
| `LIT-02` | Validity and limitations of a one-dimensional path-averaged Beer-Lambert treatment for a cylindrical illuminated tube, and the error incurred against a resolved light field | Failure mode `F6`; the optical label in `S1` | `PROPOSED` |
| `LIT-03` | Henry's law constants for CO2 and O2 in seawater with temperature and salinity dependence, and the accepted form of the correction | Slice `S2` | `PROPOSED` |
| `LIT-04` | Reported ranges and measurement methods for the volumetric mass-transfer coefficient in tubular and airlift photobioreactors, and whether empirical or dimensional correlations are usable in place of a supplied value | Slice `S2`; the claim that supplying the coefficient externally is reasonable | `PROPOSED` |
| `LIT-05` | Carbon and oxygen composition of *Nannochloropsis* biomass, sufficient for the carbon and oxygen closure required in §11 of the kernel | Failure mode `F2`; gap `G6` | `PROPOSED` |
| `LIT-06` | Respiration and maintenance rates, including dark-period behaviour | Slices `S1` and `S3` | `PROPOSED` |
| `LIT-07` | Published photobioreactor datasets suitable as an independent benchmark for the integrated slice | Slice `S4` | `PROPOSED` |

## 6. Claims explicitly withheld

Recorded so they are not later mistaken for established results.

| Claim | Status | Reason |
|---|---|---|
| A named rate law is correct for *Nannochloropsis* | `PROPOSED` | `LIT-01` outstanding |
| The selected light response exhibits photoinhibition | `PROPOSED` | Part of decision `U5`; the kernel does not presuppose it |
| The path-averaged irradiance represents a cylindrical tube under direct and diffuse illumination | `BLOCKED` | Requires a resolved light field; out of scope |
| Any claim requiring scattering, spectral dependence or radiative transfer | `BLOCKED` | Out of scope by §5 of the kernel |
| Carbonate speciation, alkalinity or pH behaviour | `BLOCKED` | Out of scope by §5 of the kernel |
| Nitrogen balance closure | `BLOCKED` | No nitrogen state exists in `S1`–`S4`; arrives with the deferred quota model |
| Gas transfer introduces numerical stiffness | `UNKNOWN` | A linear transfer equation is not stiff; stiffness would arise only from coupling across separated timescales and must be demonstrated |
| Estimating the volumetric mass-transfer coefficient requires computational fluid dynamics | `UNKNOWN` | Empirical and dimensional correlations exist; `LIT-04` outstanding |
| Integrated outputs can be bit-identical across environments | `BLOCKED` | Contradicted by `RT-32` and `RT-35`; only the pinned-platform canary pattern permits an exact digest claim |
| The 075 bit-identical tier automatically applies to a future 078 model | `BLOCKED` | `RT-37` proves only canonical 047 same-runtime equivalence; a later full 078 specification must define its own authoritative comparison before making an exact claim |
| Vendor software agreement constitutes physical validation | `BLOCKED` | Excluded by §11 of the kernel |
