# 170 — Photobioreactor unit, Tier 1

State: **draft for review**. This spec combines definition and contract under the maintainer directive of 2026-10-02 (continue the planned PBR roadmap in dependency order). Readiness follows final scientific review on the merged 168 interface. It builds on the merged [PBR engineering architecture record](../implementation/pbr-engineering-architecture-2026-10-02.md) §5, §6, §7 and §9 row 170, and the ranked engineering inventory, which are joint authority.

- **Hard dependencies:** 168 (mixed-engine solve, Jarvis unit callables) and 169 (model cards). 167 culture streams are merged.
- **168 coordination:** this spec relies on the Jarvis-unit interface merged in PR #775 and verified on master `580d6e7d`: `JARVIS_EVALUATORS[type](unit, inlet, context) -> JarvisUnitEvaluation(outlets, result, culture_generation, culture_generation_units)`, with `context = JarvisUnitContext(inlet_density_kg_m3, deadline, cache, validation)`. A typed unit failure is an exception carrying `code` and `detail`; 168 turns it into `segment_failed` with the unit tag and code preserved. Non-failing findings (for example `PBR_WASHOUT`) travel in `result["findings"]`. 168's editor does not render unit-result findings, so 170 adds that rendering in the unit's `Results · Jarvis` group (capability 8). A consumed tear directly feeding a Jarvis unit supplies NaN density; validation invokes evaluators with `validation=True`. 170 adds one additive field, `culture_generation_allowance` (capability 4), which both 168 per-unit and whole-graph balances add to their tolerance. The 170 implementation records this merged interface SHA in its PR.
- **Place in the roadmap:** the fourth slice of the record's order of value (167 → 168 → 169 → 170). It delivers the first operator-visible photobioreactor in the flowsheet.

It adds one Jarvis-owned unit, `PhotobioreactorT1`, that grows culture at a periodic steady state with true cylindrical light, driven by a pinned 169 model card. It runs inside the 168 mixed solve.

## Fresh evidence (master `8a1ef2f6`, 168 in implementation)

Code survey and prototypes: `out/wpbr/a170.report.md` (scratch in `/tmp/a170`).

1. **107 is a finite initial-value run, not a periodic steady state.** `bluerev.pbr_day_night` v2 integrates a batch with a daily semi-continuous harvest (`pbr_evaluator.py`). Continuous dilution D = Q/V and a 24-hour periodic steady state are new physics here.
2. **The record's Q2 light numbers are partly a probe artifact.**
   - `probe_q2_light.py:cylinder_collimated` gives every point on a chord one depth. It is not an area integral. The true collimated cylinder (beam normal to the axis) is −0.3 % to +39 % against the 107 slab, not "at most 18 %".
   - The probe's isotropic case is an in-plane 2-D proxy (+2.7 % to +162 %). A full 3-D isotropic field (Bickley–Naylor Ki₂) gives +5 % to +118 %.
   - The record's conclusion stands: tube geometry dominates and belongs in Tier 1. The numbers are restated here and supersede record §10.1 Q2.
3. **Washout trap.** With an inlet of zero biomass, the trivial state X = 0 is always a periodic fixed point. In the prototype, Newton on the 24-hour map converged to it even where a productive branch exists (HRT 3 and 5 d). The thin-culture growth rate Λ (below) decides the branch only for a monotone light response. For the synthetic 107 parameters with **Monod** light and N_in = 0.05 kg m⁻³, Λ = 0.02361 h⁻¹, a critical HRT of 1.765 d. The previously quoted 0.01529 h⁻¹ and 2.73 d used Haldane light, which T1 refuses. Haldane, Steele and Eilers–Peeters can instead have a productive branch even when Λ ≤ D because biomass shading relieves photoinhibition; this Tier 1 solver refuses those forms until branch selection is proven.
4. **Cost.** The refined cylinder prototype at rtol 1e-11 takes about 50–90 ms per 24-hour map and 0.4–0.9 s per periodic solve. These are local prototype measurements, not a production wall-time guarantee. The first call in a process pays about 3.9 s of cold imports (CoolProp, fluids, scikit-sundae).
5. **107 v2 is pinned by evidence.** The 107 ledger, the 108/109/149 runtime evidence and `engineering_ui_operator_proof.mjs` pin `bluerev.pbr_day_night` / `pbr_day_night.v2`. `test_bio_models_forms.py` imports `_rhs` and `_cardinal_temperature` from `pbr_evaluator`.
6. **169 pins one `FORM_VERSION`.** Every stored card pins `FORM_VERSION = "1.0.0"`, and `evaluate_card` refuses a mismatch with 409. Bumping it would orphan every card.
7. **Gaps.**
   - There is no velocity, photon-flux, time, specific-rate or temperature-difference quantity kind. The `temperature` kind converts degC with an offset, so a 3 degC amplitude would be stored as 276.15 K.
   - The canvas owner badge is hard-coded "DWSIM".
   - `BiologyModelLibrary` has no embeddable picker.
   - The agent cannot set a non-quantity unit field.

## Decision

**`PhotobioreactorT1` is a Jarvis-native unit evaluated by a new 106 evaluator, `jarvis.pbr_unit_t1`. It solves a continuously diluted, well-mixed tube loop to its 24-hour periodic steady state. Light is true cylindrical Beer–Lambert under a beam normal to the tube axis plus 3-D isotropic diffuse light. Growth comes from a pinned 169 model card. 107 v2 stays byte-stable.**

Rulings on the survey's open questions:

1. **Outlet temperature** equals the inlet temperature. Tier 1 has no energy balance. Growth uses the declared culture temperature profile (mean and diel amplitude). The finding `PBR_TEMPERATURE_DECLARED_DIFFERS` (info) is raised when |T_mean − T_inlet| > 5 K. The caveat "no energy balance; outlet temperature equals inlet" is always shown.
2. **Light convention:** scalar irradiance. In the optically thin limit both the beam and the diffuse amplitude equal I₀(t). The diffuse field is full 3-D isotropic (Ki₂). Mapping horizontal GHI/DHI, sun elevation and tilt to these amplitudes belongs to 174. The unit labels itself "beam ⟂ axis + isotropic diffuse, scalar-irradiance convention".
3. **Branch rule** for an inlet with zero biomass: Λ versus D, defined in capability 4.
4. **Dilution** is derived from the inlet flow: Q = ṁ_in/ρ_in and D = Q/V. It is not an operator input.
5. **New evaluator id** `jarvis.pbr_unit_t1`, `MODEL_VERSION = "pbr_unit.v1"`. 107 v2 is not bumped.
6. **The agent may pin a model card** through a new confirm-tier action (capability 8).
7. **One `FORM_VERSION`.** The new optics form is added at `1.0.0`. Per-form versioning is a later 169 change.

Alternatives rejected:

- **Bumping 107 to v3 with a cylinder:** this invalidates frozen 107/108/149 evidence for no product gain.
- **Integrating from a seed until periodic:** this is too slow near the washout bifurcation (400 days not converged at HRT 5 d).
- **pvlib in Tier 1:** that is site and sun geometry, which belongs to 174 (record F07).
- **The 2-D in-plane isotropic proxy:** it is not a physical radiance field.

## Accepted capability

### 1. Registry unit and descriptors

`PhotobioreactorT1`, label "Photobioreactor (T1)":

- owner `jarvis_bio`, `culture_rule: "pbr"`;
- one material inlet and one material outlet;
- no energy ports;
- one mode, `periodic_steady`.

**New quantity kinds** (additive to the registry projection):

| Kind | SI | Display units |
|---|---|---|
| `velocity` | m/s | m/s |
| `photon_flux_density` | µmol m⁻² s⁻¹ | µmol/(m²·s) |
| `temperature_difference` | K | K, °C (no offset) |
| `time` | s | s, h, d |
| `specific_rate` | 1/s | 1/s, 1/h, 1/d |

`temperature_difference` converts without an offset. 170 does not change how the existing Heater `temperature_change` is stored. The latent offset hazard there is recorded as a finding for a later fix.

**Parameters.** Every parameter is required, and none has a default.

| Group | Key | Kind | Domain |
|---|---|---|---|
| Geometry | `tube_inner_diameter` | length | 0.005–0.5 m |
| Geometry | `tube_length` | length | > 0 |
| Geometry | `tube_count` | dimensionless | integer ≥ 1 |
| Operation | `liquid_velocity` | velocity | > 0 |
| Operation | `pump_efficiency` | percent | (0, 100] |
| Operation | `baffle_friction_multiplier` | dimensionless | ≥ 1 |
| Operation | `oxygen_kla` | specific_rate | ≥ 0 |
| Operation | `oxygen_saturation` | mass_concentration | > 0 |
| Light & environment | `peak_par` | photon_flux_density | ≥ 0 |
| Light & environment | `photoperiod` | time | (0, 24] h |
| Light & environment | `diffuse_fraction` | dimensionless | [0, 1] |
| Light & environment | `temperature_mean` | temperature | T_mean − ΔT > 0 K |
| Light & environment | `temperature_amplitude` | temperature_difference | ≥ 0, T_mean − ΔT > 0 K |

**Derived quantities:**

- liquid volume V = n·(π/4)·D²·L;
- Q = ṁ_in/ρ_in in m³/s, D_s = Q/V in s⁻¹, D_h = 3600 D_s in h⁻¹ for the hourly ODE, and HRT = 1/D_s in seconds (displayed in days);
- Reynolds number;
- pressure drop: the 104 stack's straight smooth pipe × `baffle_friction_multiplier`; this is a screening hydraulic estimate, not an outlet pressure calculation;
- circulation pumping power = ΔP·u·(π/4)·D²·n/η, with η = stored `pump_efficiency` percent/100 (the existing `percent` quantity kind stores 50 for 50 %, not 0.5).

These equations describe n parallel tubes of length L, each at velocity u. Hydraulic properties use the 107 CoolProp water basis at T_mean and 1 atm. A transitional Reynolds regime is a visible screening warning, not a unit failure. If Q ≥ u·n·πD²/4, warn that fresh feed is at least the circulation flow and the well-mixed loop assumption is outside its intended range.

The baffle multiplier is an unqualified screening factor. It scales only ΔP and power.

**Model pin.** A document field `unit.model = {card_id, card_revision, card_digest}` holds the model pin. It is not a ParamSpec quantity. The new DraftOp `set_unit_model` sets or clears it with CAS, undo and staleness exactly like other DraftOps. Any other unit type refuses it.

### 2. Model card resolution (169 consumer)

A new function, `bio_models.resolve_growth_model(workspace_id, card_id, revision, digest)` (169 ships only `evaluate_card`, which applies slab optics), returns resolved callables and values in the units pinned by 169. The PBR evaluator converts them at its hourly ODE boundary. It refuses (typed `PBR_MODEL_CARD_*` findings) when:

- the pin's digest or revision does not match the stored card, or the card's set revision or digest does not match;
- the card's `form_versions` differ from the current forms;
- a required symbol is missing. The extinction coefficient `k_X` (m² kg⁻¹) is required from the card's set even though the card's own optics factor is not used.

**Supported card factors:**

| Factor | Supported forms |
|---|---|
| Light | `light.monod` |
| Temperature | `temperature.isothermal`, `temperature.ctmi`, `temperature.arrhenius_ref` |
| Nutrients | `nutrient.monod` only. Index 0 is bound to dissolved **nitrogen** (167 field `nitrogen`). Further indices are refused in T1. |
| Nutrient combination | `combine.multiplicative`, `combine.liebig` (identical with T1's single nitrogen factor) |
| Loss | `loss.first_order`, `loss.light_dark` |
| Stoichiometry | `stoich.photoautotrophic` is **required**. It provides the N quota q (kg N per kg total dry biomass) and the O₂ yield Y_O2 (kg O₂ per kg). |

The card's `n_source` (`NH3` or `HNO3`) determines its oxygen yield and is pinned in the run. The 167 `nitrogen` culture field is total dissolved N as N and does not identify its chemical species. T1 treats that N as available under the card-selected source assumption; it cannot verify a source match. Validation and Results display `N source assumed: NH3/HNO3; inlet N speciation unverified`, and the fidelity caveat states that O₂ yield depends on this assumption. T1 does not infer a source from the generic inlet or silently convert it.

**Refused:**

- `nutrient.droop`, which needs a quota state, with `PBR_MODEL_CARD_FORM_UNSUPPORTED`;
- `light.haldane`, `light.steele` and `light.eilers_peeters_steady`, whose shading-dependent productive branches cannot be selected by the Tier 1 thin-culture washout rule;
- a card without stoichiometry.

**Optics.** The card's optics factor is superseded by the unit geometry. The unit always averages the response over the cylinder (capability 3), and a card that names `optics.slab_*` gets the caveat "card optics replaced by unit geometry (cylinder)". The card's `k_X` (m² kg⁻¹) is the extinction coefficient.

The cylinder form is a documented production kernel and reference target, not a selectable 169 card factor. `evaluate_card` continues to evaluate only its supported slab optics; a direct attempt to evaluate the cylinder form outside the PBR returns a clear typed 422 explaining that it is evaluated inside `PhotobioreactorT1`. Existing pinned slab cards receive the caveat above. The 169 model-library set editor gains a `k_X` parameter row and the PBR stoichiometry symbols, labelled as PBR inputs, so an operator can create a complete set and card through the UI. A missing symbol gives `PBR_MODEL_CARD_SYMBOL_MISSING`, listing the symbols and linking the Biology tab to the library; the picker has a "No model cards — Browse models…" empty state.

**Parameter states.** Values in state `candidate` raise `PBR_PARAMETER_UNVERIFIED` (info), listing the symbols. They are never blocked and never promoted.

**Run record.** The run stores the card id, revision and digest, the set id, revision and digest, the N-source assumption, and the form versions.

### 3. Cylindrical light (`optics.cylinder_beam_diffuse_response_average`)

This is a new 169 form card at `FORM_VERSION 1.0.0`. It has typed MathML and a symbol table: D, k_X, X, I₀, f_d. It shares the 169 form tests.

**Setup.** An infinite circular cylinder of radius R = D/2 with extinction κ = k_X·X. Use polar coordinates (r, φ) over the cross-section.

**Beam.** I_b(p) = (1 − f_d)·I₀·exp(−κ·s_b(p)). Here s_b(p) = y + √(R² − x²) is the path from the entry point, with the beam travelling along +y normal to the axis.

**Diffuse.** I_d(p) = f_d·I₀·S₃(p), where:

- S₃(p) = (1/2π)·∮ Ki₂(κ·s_θ(p)) dθ;
- s_θ(p) = p·u + √((p·u)² + R² − |p|²);
- Ki₂(a) = ∫₀^{π/2} cos φ·exp(−a/cos φ) dφ, the Bickley–Naylor function.

**Response.** ⟨f_I⟩ = (1/πR²)·∬ f_I(I_b + I_d) dA. The response is averaged over the area; it is never f_I of the mean irradiance (169 parity rule).

**Numerics** (fixed under `MODEL_VERSION`):

- The supported optical-depth domain is 0 ≤ τ = κD ≤ 1000. A larger τ produces `PBR_OPTICS_OUT_OF_RANGE` and no current outlet; the result never silently falls back to slab optics. The operator sees τ and this Tier-1 limit.
- The production ODE uses a fixed-rule, boundary-layer-aware area quadrature whose response is continuous, preferably C¹, in I₀ and κ. Nodes may move only through a smooth τ-dependent map; an adaptive rule that changes node counts inside the RHS is excluded. At τ = 0, use the analytic thin limit. Independent adaptive refinement is used for the reference only.
- The 3-D diffuse field uses a fixed directional rule and a smooth Ki₂ evaluation (a smooth interpolant or matched series/asymptotic pieces), checked against an independent integral reference. Large-argument asymptotics require enough correction terms to meet the stated accuracy; the leading √(π/2a)·e^(−a) term alone is insufficient at a = 316.
- On a declared grid spanning τ = 0 to 1000, irradiance, diffuse field and the final area-averaged light response agree with an independent, refined reference under |production − reference| ≤ 1e-4·|reference| + 1e-8·I₀. The reference method, convergence evidence and smoothness under small changes in I₀ and κ are recorded.

All constants and refinement rules are deterministic. Exponentials may underflow to zero at extreme optical path, but τ itself is never used as a divisor without its analytic zero limit.

**Required properties** (tests, capability 9):

- **Thin limit:** ⟨f_I⟩ → f_I(I₀).
- **Linear response, thick-limit trend** as τ increases within the supported range:
  - beam: 4/(πτ) with τ = κD;
  - 3-D diffuse: 1/τ.
- The thick-limit checks compare against the exact chord and angular integrals with stated tolerances; their asymptotic trends have O(1/τ) relative corrections and are not treated as exact at finite τ.
- **Linear-response beam** equals the 1-D chord integral (1/πR²)·∫(1 − e^(−κc(x)))/κ dx to 1e-6.
- **Accuracy:** the production response meets the independent reference criterion above, including high-τ boundary-layer cases rather than only a coarse-grid comparison.

### 4. Periodic steady state (`jarvis.pbr_unit_t1`)

**State and environment.** The state is y = (X, N, O₂) in kg m⁻³ inside the well-mixed loop. Time t is in hours. Registry `time` values are stored in seconds, so P_h = photoperiod_s/3600; registry `specific_rate` values are stored in s⁻¹, so kLa_h = 3600·oxygen_kla_s. The 169 μ_max and loss values are pinned in h⁻¹.

- **Surface PAR:** I₀(t) = peak_par·sin(π(t − t_rise)/P_h) during daylight, otherwise 0. Here t_rise = 12 − P_h/2. This is the 107 half-sine.
- **Temperature:** T(t) = T_mean + ΔT·sin(2π(t − 9)/24).
  - It applies at all hours. 107 applied it only in daylight, and this difference is documented.
  - The temperature factor matters only where growth is nonzero.

**Rates.** These are 107's equations with continuous dilution D_h (h⁻¹):

- μ_g = μ_max · ⟨f_I⟩(I₀(t), X) · f_T(T(t)) · C_N(f_N(N)). The 169 combination rule applies to nutrient factors only. T1 has one nitrogen factor, so `combine.multiplicative` and `combine.liebig` have the same value;
- r_X = (μ_g − k_d(t))·X, with k_d from the card's loss form (`light_dark` uses the light state of I₀(t));
- dX/dt = r_X + D_h·(X_in − X);
- dN/dt = −q·r_X + D_h·(N_in − N);
- dO₂/dt = Y_O2·r_X − kLa_h·(O₂ − O₂sat) + D_h·(O₂_in − O₂).

N is clipped at 0 only in its growth factor, as in 107; the oxygen transfer term uses the integrated O₂ state. This does not make a negative integrated state physical. Every accepted periodic trajectory must keep X, N and O₂ nonnegative within the numerical integration tolerance; a materially negative value fails with a typed `PBR_NONPHYSICAL_STATE` unit result. In particular, the allowed combination kLa = 0, O₂_in = 0 and dark biomass decay can drive the stated O₂ equation below zero; T1 refuses that trajectory rather than silently truncating oxygen or claiming oxygen-limited biology it does not model.

The inlet volumetric values are the inlet's 167 mass-specific values × ρ_in. Biomass, dissolved N and dissolved O₂ must each be specified and finite on the PBR inlet; 167 permits N and O₂ to be unknown, but T1 refuses an unknown value instead of assuming zero. An explicit zero remains valid. P, DIC and salinity are not consumed in T1. They pass through, with the caveat "carbon and phosphorus assumed externally supplied and non-limiting; elemental C/P balances are not modeled". pH passes through unchanged with the caveat "pH not modeled; photosynthetic DIC uptake would raise it". Two more equation conventions inherited from 107 are disclosed as caveats: "biomass loss returns its N quota to dissolved N and consumes O₂ at Y_O2" and "O₂ saturation is the declared constant, independent of temperature and salinity". The 169 stoichiometry card's phosphorus term is disclosed but is not applied as a Tier-1 phosphorus consumption or a claim of full elemental conservation.

In 168's `context.validation` mode the evaluator returns a carrier and culture pass-through with zero generation. It does not run the periodic solver or refuse absent culture values in the synthetic validation inlet; instant validation owns those findings. In Run mode a nonfinite `context.inlet_density_kg_m3` gives a typed `PBR_INLET_DENSITY_UNAVAILABLE` failure with the hint "place a Mixer or Heater between the Recycle and the PBR". A consumed tear immediately upstream of a PBR is therefore diagnosed rather than calculated with an invented density.

**Map.** Φ₂₄(y₀) integrates 24 h with `integrate_ode` (CVODE BDF) at rtol 1e-11 and atol 1e-14 kg m⁻³, fixed under `MODEL_VERSION`. Augmented quadrature states give the daily means of X, N, O₂ and r_X, and the signed net O₂ gas transfer. Positive transfer is degassing; negative transfer is oxygen absorption from the gas phase. Integration error, not the root solver, limits attainable periodicity: the survey measured map noise of about rtol relative. Every tolerance below keeps at least a 100× margin over rtol.

The fixed integration schedule splits at sunrise, sunset and any daylight I₀ = I_dark transition used by `loss.light_dark`; dense output samples (at least 20 per hour) prevent CVODE's internal 500-step limit from becoming an accidental scientific branch rule. `integrate_ode` does not expose `max_num_steps`. The Λ quadrature also splits at these light boundaries and at CTMI T_min/T_max crossings.

**Reduced periodic problem (normative).** The T1 equations have exact structure, and the solver uses it instead of a blind three-state Newton iteration:

- **N is slaved.** Z = N + qX obeys dZ/dt = D_h·(Z_in − Z) with Z_in = N_in + q·X_in. Its only periodic solution is Z ≡ Z_in. On the periodic orbit, N(t) = N_in + q·(X_in − X(t)). Every map evaluation therefore seeds N₀ = N_in + q·(X_in − X₀).
- **O₂ is linear and has no feedback.** T1 has no oxygen effect on growth. Given X(t), the O₂ equation is linear with decay rate kLa_h + D_h > 0. Its periodic solution is unique, and two integrations give it exactly: O₂(24) = α·O₂(0) + β, so O₂* = β/(1 − α).
- **X is a scalar periodic root.** Let F(X₀) = Φ₂₄,X(X₀) − X₀, with N slaved.

**Root finding (deterministic, fixed constants).**

- **Brackets.**
  - X_in > 0: the lower end is X_lo = 0, where F(0) > 0. The upper end is X_hi = X_in + N_in/q when q > 0; there N = 0 on the orbit, so F(X_hi) ≤ 0. When q = 0 and k_X > 0, start at max(2·X_in, 1e-3 kg m⁻³) and double until F < 0. Use at most 40 doublings, and never go beyond τ = 1000 (`PBR_OPTICS_OUT_OF_RANGE`). No sign change gives `PBR_NO_FINITE_PRODUCTIVE_STATE`.
  - q = 0 and k_X = 0 (no biomass feedback): N ≡ N_in, and the X equation is linear, dX/dt = (μ_g(t) − k_d(t) − D_h)·X + D_h·X_in, with growth independent of X. No bracket is used. With X_in > 0 and Λ < D_h (Λ as defined in the branch rule, exact here), X* = β/(1 − α) from two integrations, exactly as for O₂, followed by the normal certification. With X_in > 0 and Λ ≥ D_h the result is `PBR_NO_FINITE_PRODUCTIVE_STATE`. X_in = 0 follows the branch rule.
  - X_in = 0 and Λ > D_h: the lower end is the declared resolution X_res = 1e-6 kg m⁻³. F(X_res) must be > 0; otherwise the result is `PBR_BRANCH_UNRESOLVED`, reporting the bracket and the residual. The upper end is found as above.
  - If the physical upper bound X_hi ≤ X_res, refuse with `PBR_BRANCH_UNRESOLVED` before seeding X_res, because that seed would make N negative.
  - An endpoint where |F| meets the stopping rule below is the root.
- **Solve.** Use Brent's method. Stop when the bracket width is ≤ 1e-10·max(X, 1e-6 kg m⁻³) or |F| ≤ 1e-9·max(X, 1e-6 kg m⁻³). Use at most 80 map evaluations. Exhaustion gives `PBR_PERIODIC_STEADY_FAILED`, with the achieved bracket and residual.
- **Uniqueness.** With N slaved, X obeys a scalar 24-hour-periodic equation dX/dt = X·h(t, X), where h = μ_g − k_d − D_h + D_h·X_in/X. Under the supported forms, h is nonincreasing in X at every t (⟨f_I⟩ falls with X when k_X > 0, f_N falls with X when q > 0, and k_d does not depend on X). It is strictly decreasing on a set of hours of positive measure when q > 0 with N > 0 on daylight hours where f_T > 0, when k_X > 0 on such daylight hours with peak_par > 0, or when X_in > 0. Pointwise strictness is not claimed: at night ⟨f_I⟩ = 0. Two positive periodic solutions X₁ < X₂ would both need ∫₀²⁴ h dt = 0, which this rules out. The positive periodic solution is therefore unique and stable. The solver also checks that its evaluated points show exactly one sign change. Any other pattern gives `PBR_BRANCH_UNRESOLVED`.

**Certification.** From y* = (X*, N_in + q·(X_in − X*), O₂*), integrate the full three-state system once more. The root is accepted only if all of these hold:

- **Periodicity:** the X tolerance is 1e-9·max(X*, 1e-6 kg m⁻³), the N tolerance is 1e-9·max(Z_in, 1e-6 kg m⁻³), and the O₂ tolerance is 1e-9·max(|O₂*|, O₂sat). The N scale follows the exact conserved Z identity, so a valid N-limited X root is not spuriously refused;
- **Z identity:** |N(t) + q·X(t) − Z_in| ≤ 1e-9·max(Z_in, 1e-6 kg m⁻³) at the output samples;
- **Physical trajectory:** the trajectory is finite, and X, N, O₂ ≥ −1e-12 kg m⁻³. A violation gives `PBR_NONPHYSICAL_STATE`.

A failed periodicity or Z certification gives the typed `PBR_PERIODIC_STEADY_FAILED` result with each achieved residual and tolerance. Outlet means, generation and allowances all come from this same full-state certification integration with its quadrature states.

**Generation allowance (additive 168 interface).** For each field at the certified orbit, in − out + generation equals V times the daily mean of dy/dt: V·(y_i(24) − y_i(0))/86,400 kg/s. That is residual periodicity, not a modelling error. At long HRT, 168's 1e-9-relative per-unit rule is stricter than any attainable periodicity. The unit therefore declares an allowance with each generation term, in the same units: a_i = V·(|Φ₂₄(y*)_i − y*_i| + 1e-12 kg m⁻³)/86,400 kg/s. 168's per-unit and whole-graph culture balances add declared allowances to their tolerance, exactly as they add tear and native-Recycle allowances. Units that declare none (the separator) are unchanged. Generation always comes from the integrated rate quadratures and never from in − out, so the balance stays an independent check. The result reports each allowance next to its residual.

**Branch rule.** This rule applies to the supported monotone Monod light response. It must not be used for photoinhibitory forms.

- Λ = (1/24)∫₀²⁴ [μ_g(t; thin limit ⟨f_I⟩ = f_I(I₀(t)), N = N_in) − k_d(t)] dt.
- **If X_in = 0 and Λ ≤ D_h:** the result is the washout state when it is uniquely selected. X = 0, and N and O₂ come from the map with X ≡ 0. The status is `washout`, with the warning `PBR_WASHOUT`. This is a valid result, not a failure. The degenerate no-feedback equality case (q = k_X = 0 and Λ = D_h) is instead `PBR_BRANCH_UNRESOLVED`, because it has a continuum of positive periodic states.
- **If X_in = 0 and Λ > D_h:** find and certify the strictly positive fixed point of the 24-hour map. The zero fixed point is never accepted as the productive branch. The reported branch is `productive` only when a positive root is bracketed, the map residual closes, and the trajectory is physical. Near Λ = D_h, if a positive branch falls below the solver's declared resolution, return `PBR_BRANCH_UNRESOLVED` with the achieved bracket, residual and resolution; do not mislabel it washout or claim no root solely from a 1e-6 kg m⁻³ cutoff.
- **If X_in > 0:** find and certify the positive fixed point. With supported monotone Monod light and nutrient factors, a physically bounded root is unique when biomass growth has strict negative feedback. Do not assume existence if the card eliminates both nutrient and light feedback.

At a periodic state, Z = N + qX obeys dZ/dt = D_h·(N_in + qX_in − Z), so N(t) = N_in + q·(X_in − X(t)) on the periodic orbit. Use this identity to bound the search when q > 0 and to check the nutrient balance independently. The model permits q = 0 and k_X = 0; then growth is independent of biomass. With those values, Λ ≥ D_h and X_in > 0 gives no finite periodic root; Λ > D_h and X_in = 0 gives only the washout root, which is unstable and cannot be called productive. Report `PBR_NO_FINITE_PRODUCTIVE_STATE` with the card/parameter cause. At Λ = D_h with X_in = 0, the productive branch is degenerate rather than uniquely selected; report `PBR_BRANCH_UNRESOLVED`. Any other detected multiple positive roots or failure to certify uniqueness under the supported forms also returns `PBR_BRANCH_UNRESOLVED`, with diagnostics, rather than an arbitrary selected result. Both findings are unit failures and make the 168 run `segment_failed`.

Λ is computed by deterministic adaptive quadrature to 1e-10 relative, with an absolute floor of 1e-12 h⁻¹ because Λ may be zero or negative. If |Λ − D_h| ≤ 1e-8·D_h with X_in = 0, the branch is a numerical tie and the result is `PBR_BRANCH_UNRESOLVED`, never washout or productive. Λ, D_h, HRT and the branch are always reported with explicit units.

**Initialization and cache.** Each evaluation derives its brackets from its current inlet and model pin using the branch rule above. It does not read a previous outer iteration's state. Identical unit and inlet inputs may use 168's per-Run cache. Its key includes `MODEL_VERSION`, the resolved set digest, card pin, all SI parameters and the exact inlet state including density; the result therefore does not depend on iteration order.

**Outlet.** The outlet is the flow-weighted daily mean:

- X̄, N̄ and Ō₂ in kg m⁻³, converted to mass-specific values with ρ_in;
- carrier mass flow, pressure, composition and pH equal the inlet's;
- temperature equals the inlet's (ruling 1).

The carrier excludes biomass mass, as in 167/168.

**Declared generation** (168 interface (c)), in kg/s over the daily mean. Rates r̄_X and kLa_h·mean(O₂ − O₂sat) are kg m⁻³ h⁻¹, so conversion to seconds is explicit:

- biomass: V·r̄_X/3600;
- dissolved N: −q·V·r̄_X/3600;
- dissolved O₂: V·[Y_O2·r̄_X − kLa_h·mean(O₂ − O₂sat)]/3600. The signed net O₂ gas transfer is reported separately, with its direction.

The per-unit residual closes as in − out + generation to 167's rule. A whole-graph balance includes the generation terms.

**Limits.**

- Zero inlet flow (Q = 0) refuses with `PBR_NO_THROUGHFLOW` (a unit failure, which makes the 168 run `segment_failed`).
- HRT outside [0.1, 100] d raises `PBR_HRT_OUT_OF_RANGE` (warning).
- An inlet vapor fraction above 1e-6 fails, following the 167 liquid-only rule.
- A negative periodic state, missing finite productive root, or unresolved branch fails with the typed result above; none is published as a current culture outlet.
- **Wall time:** each evaluation is capped at min(5 s, `context.remaining_s()`). Eager module imports happen at server startup; any import inside a Run counts against the 168 wall budget. The evaluator raises `TimeoutError` when its deadline is reached; 168 records `JARVIS_UNIT_TIMEOUT`, and the outer run may end with reason `wall_budget`. The real mixed-loop evidence records PBR time per iteration.

**106 evaluator.** It has `backend_kind="dynamic_simulator"`, `fidelity="reduced_order"`, and an `unqualified` envelope. Its `qualification_record_ref` points to a new synthetic-unqualified ledger. It can also be called headless with scalar outputs (X̄, productivity, Λ, HRT, ΔP, power), but it is not added to Engineering Studies in 170.

**Unit result** (`reported`), each value with its unit:

- branch;
- map evaluations, final bracket and per-state periodicity residual;
- Λ (h⁻¹), D_h (h⁻¹) and HRT (d);
- X̄ and net volumetric biomass productivity 24·D_h·(X̄ − X_in) (kg m⁻³ d⁻¹); this may be negative when decay exceeds growth;
- net biomass production rate 24·V·r̄_X (kg/d), equal to 86,400·Q·(X̄ − X_in); outlet biomass throughput is separately labelled if shown;
- minimum and mean N;
- maximum and mean O₂, and the maximum O₂ saturation ratio;
- signed net O₂ gas transfer (degassing or absorption);
- Re, ΔP and pumping power;
- the balance residuals and declared generation allowances.

It also carries the fidelity label "T1 · unqualified · periodic steady state, cylinder light, no energy balance", the caveats, and the card pin. The visible caveats also state: "well-mixed (0-D) loop; no axial O₂ buildup along tubes, so maximum DO is a loop-mean value", "every tube receives full declared I₀; no array shading or wall losses (174)", and "Q is carrier volume; biomass volume is neglected". The maximum-O₂-saturation number is not presented as a degasser design maximum.

### 5. Shared growth core and 107 parity

- The 107 RHS pieces are extracted into a shared core that both `bluerev.pbr_day_night` v2 and `jarvis.pbr_unit_t1` call.
- v2 keeps `geometry = slab` and its harvest segments, and its outputs stay **bitwise identical** on the 107 fixtures.
- `_rhs` and `_cardinal_temperature` stay importable from `pbr_evaluator`.
- The unit never uses the slab. Slab mode is reachable only from v2 and the parity tests.
- The documented slab → cylinder change is recorded as a golden table: cylinder versus slab at the Q2 constants for beam, 3-D diffuse and 50/50, with the a170 values. It supersedes record §10.1 Q2. The record gets a one-line pointer in the 170 implementation PR.
- `MODEL_GAPS` gains "tube_light_geometry: resolved in jarvis.pbr_unit_t1".

### 6. Validation (instant, `source: "jarvis"`)

**New findings:**

| Code | Severity | Condition |
|---|---|---|
| `PBR_REQUIRES_CULTURE_INLET` | blocker | The inlet is not reached by culture. |
| `PBR_REQUIRES_BIOMASS` | blocker | Biomass is absent or unknown on the PBR inlet. Explicit zero is valid. |
| `PBR_REQUIRES_NITROGEN` | blocker | Dissolved N is absent or unknown on the PBR inlet. Explicit zero is valid. |
| `PBR_REQUIRES_OXYGEN` | blocker | Dissolved O₂ is absent or unknown on the PBR inlet. Explicit zero is valid. |
| `PBR_REQUIRES_MODEL_CARD` | blocker | The unit has no model pin. |
| `PBR_MODEL_CARD_UNAVAILABLE` | blocker | The pin does not resolve, or its digest or form versions differ. |
| `PBR_MODEL_CARD_FORM_UNSUPPORTED` | blocker | The card uses a refused form. |
| `PBR_MODEL_CARD_SYMBOL_MISSING` | blocker | The resolved set lacks a required PBR symbol; the finding lists the symbols. |
| `PBR_PARAMETER_UNVERIFIED` | info | The card's set has `candidate` values. |
| `PBR_HRT_OUT_OF_RANGE` | warning | HRT outside [0.1, 100] d. Before a run, it is evaluated only when the PBR inlet is a feed stream, using that feed's ṁ/ρ with ρ the 167 density basis. When the inlet comes from a unit or a recycle, the instant check is skipped and the finding comes from the solved inlet after Run. The finding labels which basis was used. |
| `PBR_TEMPERATURE_DECLARED_DIFFERS` | info | \|T_mean − T_inlet\| > 5 K (ruling 1). |
| `PBR_WASHOUT` | warning | Emitted after a run. |
| `PBR_NONPHYSICAL_STATE` | error | X, N or O₂ becomes materially negative or nonfinite on the periodic trajectory. |
| `PBR_NO_FINITE_PRODUCTIVE_STATE` | error | The supported equations lack a finite positive periodic root for the selected inputs/card. |
| `PBR_BRANCH_UNRESOLVED` | error | The branch lies below declared numerical resolution or a unique physical root cannot be certified. |
| `PBR_OPTICS_OUT_OF_RANGE` | error | The computed optical depth exceeds the supported Tier-1 range. |
| `PBR_PERIODIC_STEADY_FAILED` | error | The map, periodicity or conserved-state certification fails or exhausts the evaluation cap. |
| `PBR_NO_THROUGHFLOW` | error | The solved inlet has zero carrier flow. |
| `PBR_INLET_DENSITY_UNAVAILABLE` | error | The solved inlet has no finite DWSIM density; the message suggests a Mixer or Heater before the PBR. |
| `JARVIS_UNIT_TIMEOUT` | error | The PBR exceeds its own or the remaining 168 wall time; 168 owns this code. |

168's findings apply unchanged. A PBR on a consumed tear's cycle is a normal 168 mixed loop.

### 7. Fingerprints and staleness

The 168 layout-free fingerprint gains:

- the PBR parameters;
- the model pin (card id, revision and digest);
- the resolved set digest;
- `jarvis.pbr_unit_t1` and `pbr_unit.v1`.

Editing a PBR parameter or re-pinning the card stales results. Layout edits do not. A newer set or card does **not** silently change a pinned unit; the inspector names the newer compatible revision and offers an explicit re-pin. Single-owner and 168-only drafts keep their fingerprints byte-identical.

### 8. Operator UI and agent actions

**Palette and canvas.**

- The palette's "Jarvis units" group gains "Photobioreactor (T1)".
- The canvas and inspector owner badges come from the registry `owner`. No "DWSIM" string is hard-coded anywhere.

**PBR inspector.** It has tabs: Overview, Geometry, Biology, Operation and Light & environment, and Results. They are keyboard-accessible with `role="tablist"`.

- **Overview:** the owner, fidelity, derived V/Q/HRT and the last run status.
- **Geometry, Operation, Light & environment:** typed QuantityInputs with units and inline domain validation. The amplitude uses °C/K difference units.
- **Biology:** an embeddable **model card picker** built from `listBioCards` and `listBioSets`. It shows each card's factors with their equations through the existing allowlisted MathML renderer, the set's verification chips, the assumed N source and the pin's revision. Pinning applies `set_unit_model`. An empty picker links to the Biology model library, whose set editor exposes `k_X` and PBR stoichiometry symbols. A newer set revision or a newer compatible card is shown explicitly; no pinned digest changes silently.
- **Results:** branch, Λ vs D, HRT, X̄, productivity, N/O₂ means and extremes, hydraulics, balance residuals with allowances, and map residuals. Grouped under `Results · Jarvis`, they carry the fidelity label and the caveats. The unit's non-failing `result.findings` (for example `PBR_WASHOUT`, `PBR_HRT_OUT_OF_RANGE` after Run) are shown here as readable messages. A typed unit failure (for example `PBR_NONPHYSICAL_STATE`) is shown in 168's failed-segment message with its code meaning in plain words and an operator hint, such as raising `oxygen_kla` for night-time oxygen depletion.
- Every typed PBR exception includes its plain-language meaning and operator hint in the exception message itself, within 168's 600-character failure-message limit; the frontend does not depend on a hidden code lookup to explain it.
- The outlet stream shows `Culture · Jarvis`.

**Layout.** The editor is readable at 1280 and 1440 CSS px with no horizontal overflow and no raw JSON in the normal view.

**Agent (166 vocabulary).**

- `add_unit`, `insert_unit_after` and `connect` work for the PBR through the registry.
- `set_value` on PBR parameters is confirm tier, with units validated.
- A new action `set_unit_model {unit, card}` resolves a card by id or exact name to its current revision and digest; a name matching more than one card is refused with the matching ids shown. It is confirm tier and maps to one `set_unit_model` DraftOp. It is wired in the action models, `_process_ops`, the brief, the Hermes MCP schema, the thread guard's op list and the frontend presentation.
- The agent never edits or verifies sets (169 non-goal), and Run stays operator-initiated.
- **Brief.** The Process brief is registry-derived: unit owners, the PBR card name and verification summary, and the last run's branch, HRT, Λ, residual and status. It stays within the 6000-character cap, and a test asserts it with 35 objects. The static text "Jarvis-native units arrive with 168/170" and 169's "PBR units arrive with 170" are replaced, together with the tests that assert them.

### 9. Required evidence

**1. Backend tests.**

- **Cylinder properties** (capability 3): thin and thick limits, the chord integral, the Ki₂ table, quadrature convergence and the golden Q2 table.
- **107 parity:** v2 outputs bitwise on all 107 fixtures; `test_bluerev_pbr_107.py` and `test_bio_models_forms.py` unchanged and passing.
- **Periodic steady state:**
  - per-unit and whole-graph balances close under the 168 rule plus the declared allowance, and each allowance is itself bounded by the certified periodicity;
  - the map residual is within tolerance;
  - the Z identity holds on the orbit; the closed-form O₂* equals a brute-force full-map fixed point; the Brent and bracket constants give bit-identical results across two runs;
  - bracket refusals: q = 0 with k_X = 0, the doubling cap, τ beyond 1000, and a positive root below X_res;
  - long-HRT (100 d) and short-HRT (0.1 d) cases certify without relaxing any tolerance;
  - the Monod version of the synthetic 107 fixture with N_in = 0.05 kg m⁻³ and X_in = 0: washout at HRT 1.5 and 1.7 d, productive at 2, 3, 5 and 8 d, with a numerical tie probe around the 1.765 d critical HRT; never accept the trivial state on the productive side;
  - X_in > 0 gives a unique positive state when the supported growth feedback admits a finite root; the no-root case is separately refused;
  - D_s ↔ D_h, kLa_s ↔ kLa_h, photoperiod seconds ↔ hours, hourly generation ↔ kg/s, and hourly productivity ↔ kg/day conversions close against an independent steady mass-balance calculation;
  - with X_in > 0, net productivity is based on X̄ − X_in while outlet biomass throughput remains a distinct quantity;
  - D → 0 approaches a comparable 107 time average only in a zero-harvest 107 fixture; ordinary 107 v2 daily harvest is not a zero-dilution reference;
  - oxygen depletion, no finite productive root (q = k_X = 0), near-bifurcation unresolved branch and any detected multiple-root ambiguity yield typed failures without a current outlet;
  - determinism over two runs and cold/warm processes;
  - typed refusals mirror 107's matrix.
- **Model card resolution:** pins, mismatches, unsupported forms, a missing stoichiometry factor, the nutrient index binding, validation pass-through and typed missing-density refusal.
- **Culture input refusal:** missing or unknown dissolved N and O₂ each block before Run, while explicit zero values remain valid inputs.
- **The new quantity kinds,** including that `temperature_difference` has no offset.
- **DraftOp `set_unit_model`:** CAS, undo, stale and refusal on other unit types.
- **Fingerprint** includes and excludes the right items. Earlier drafts keep their golden fingerprints.
- **166:** both actions and the brief cap.

**2. Frontend.** The build passes. Node contract tests cover the palette entry, owner-driven badges, the tablist, the picker (no `dangerouslySetInnerHTML`) and the result groups. A browser-proof plan `.github/browser-proof/plans/170-pbr-unit.json` exists.

**3. Exact-head real DWSIM 10.2.9.**

- **Converging loop.** Topology: a culture medium feed and the recycle return enter Mixer → PBR → SpecifiedSeparator. The concentrate goes to a product. The clarified stream goes to Splitter → purge + return → Heater → Recycle → Mixer.
  - Card: a 169 card with a synthetic-unqualified set mirroring the 107 fixture values (labelled synthetic).
  - It converges within 168 limits.
  - Per-unit and whole-graph balances close: biomass with the PBR generation, total N, and O₂ with signed gas transfer.
  - Two runs agree to 1e-9 relative.
  - The whole Run is under 90 s, with per-phase wall times recorded.
- **Washout.** Once through (feed → PBR → product) with X_in = 0 at an HRT below critical, the run completes with `PBR_WASHOUT` and zero outlet biomass.
- **Staleness.** Editing a PBR parameter or re-pinning the card stales the results. A layout move does not.

**4. Exact-head real Chromium at 1280 and 1440 CSS px** (local Gemma for the Sidecar steps).

1. Create a complete synthetic parameter set and card through the Biology model library UI, including `k_X`, then add the PBR from the palette, connect it, and pick that card in Biology, seeing the verification chips.
2. Configure geometry, operation and light, and see an off-range warning.
3. Run, and inspect Results (branch, HRT, Λ, X̄, productivity, balances, hydraulics) and the outlet `Culture · Jarvis`.
4. Edit a parameter, see the results go stale, and Run again.
5. In the Sidecar: "add a photobioreactor after the heater" yields an Apply card. "why is the PBR washing out?" is answered from the brief with no Apply card. "use model card <name> for the PBR" yields an Apply card, and applying it creates the next revision.
6. Inspect the screenshots. No raw JSON is visible.

## Boundaries / non-goals

- **Out of scope:**
  - pvlib, site, profiles, sun geometry and tilt (171/174);
  - array shading, Fresnel walls and two-flux scattering (174);
  - an energy balance, a degasser, kLa correlations, pH/DIC/P consumption and O₂ inhibition (175);
  - dynamic scenarios and controllers (172);
  - a BLUECAD link, tube pitch and ground cover (176);
  - a dark volume;
  - Droop and quota states;
  - CFD (179);
  - Engineering Studies registration of the new evaluator.
- **Unchanged:**
  - `bluerev.pbr_day_night` v2 and its evidence;
  - the frozen 145 contracts;
  - 168's numerics and limits, apart from the additive `culture_generation_allowance` (capability 4);
  - 169's `FORM_VERSION`;
  - the Heater `temperature_change` storage.
- **Never done:**
  - biology inside DWSIM;
  - shipping literature parameter values as defaults (169 rule);
  - promoting parameter verification states.
- **No SQL migration.** The draft `schema_version` stays 1, and old documents load unchanged.
