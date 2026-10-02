# 170 — Photobioreactor unit, Tier 1

State: **draft for review**. This spec combines definition and contract under the maintainer directive of 2026-10-02 (continue the planned PBR roadmap in dependency order). Readiness follows resolution of the branch-selection and 168 interface checks. It builds on the merged [PBR engineering architecture record](../implementation/pbr-engineering-architecture-2026-10-02.md) §5, §6, §7 and §9 row 170, and the ranked engineering inventory, which are joint authority.

- **Hard dependencies:** 168 (mixed-engine solve, Jarvis unit callables) and 169 (model cards). 167 culture streams are merged.
- **168 coordination:** this spec relies on the Jarvis-unit interface fixed by coordinator ruling in the 168 implementation (evaluator registry, stream density, declared generation terms, unit object and run context, per-Run cache, Jarvis time in the wall budget). The 170 implementation starts only after 168 merges with that interface.
- **Place in the roadmap:** the fourth slice of the record's order of value (167 → 168 → 169 → 170). It delivers the first operator-visible photobioreactor in the flowsheet.

It adds one Jarvis-owned unit, `PhotobioreactorT1`, that grows culture at a periodic steady state with true cylindrical light, driven by a pinned 169 model card. It runs inside the 168 mixed solve.

## Fresh evidence (master `8a1ef2f6`, 168 in implementation)

Code survey and prototypes: `out/wpbr/a170.report.md` (scratch in `/tmp/a170`).

1. **107 is a finite initial-value run, not a periodic steady state.** `bluerev.pbr_day_night` v2 integrates a batch with a daily semi-continuous harvest (`pbr_evaluator.py`). Continuous dilution D = Q/V and a 24-hour periodic steady state are new physics here.
2. **The record's Q2 light numbers are partly a probe artifact.**
   - `probe_q2_light.py:cylinder_collimated` gives every point on a chord one depth. It is not an area integral. The true collimated cylinder (beam normal to the axis) is −0.3 % to +39 % against the 107 slab, not "at most 18 %".
   - The probe's isotropic case is an in-plane 2-D proxy (+2.7 % to +162 %). A full 3-D isotropic field (Bickley–Naylor Ki₂) gives +5 % to +118 %.
   - The record's conclusion stands: tube geometry dominates and belongs in Tier 1. The numbers are restated here and supersede record §10.1 Q2.
3. **Washout trap.** With an inlet of zero biomass, the trivial state X = 0 is always a periodic fixed point. In the prototype, Newton on the 24-hour map converged to it even where a productive branch exists (HRT 3 and 5 d). The thin-culture growth rate Λ (below) decides the branch only for a monotone light response. For the 107 Monod fixture, Λ = 0.01529 h⁻¹, a critical HRT of 2.73 d. Haldane, Steele and Eilers–Peeters can instead have a productive branch even when Λ ≤ D because biomass shading relieves photoinhibition; this Tier 1 solver refuses those forms until branch selection is proven.
4. **Cost.** One 24-hour map takes 4–14 ms (slab to cylinder). A Newton periodic-steady solve from a warm start takes 0.1–0.5 s. The first call in a process pays about 3.9 s of cold imports (CoolProp, fluids, scikit-sundae).
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
| Light & environment | `temperature_mean` | temperature | — |
| Light & environment | `temperature_amplitude` | temperature_difference | ≥ 0 |

**Derived quantities:**

- liquid volume V = n·(π/4)·D²·L;
- Q = ṁ_in/ρ_in in m³/s, D_s = Q/V in s⁻¹, D_h = 3600 D_s in h⁻¹ for the hourly ODE, and HRT = 1/D_s in seconds (displayed in days);
- Reynolds number;
- pressure drop: the 104 stack's straight smooth pipe × `baffle_friction_multiplier`;
- circulation pumping power = ΔP·u·(π/4)·D²·n/η, with η = stored `pump_efficiency` percent/100 (the existing `percent` quantity kind stores 50 for 50 %, not 0.5).

The baffle multiplier is an unqualified screening factor. It scales only ΔP and power.

**Model pin.** A document field `unit.model = {card_id, card_revision, card_digest}` holds the model pin. It is not a ParamSpec quantity. The new DraftOp `set_unit_model` sets or clears it with CAS, undo and staleness exactly like other DraftOps. Any other unit type refuses it.

### 2. Model card resolution (169 consumer)

`bio_models.resolve_growth_model(workspace_id, card_id, revision, digest)` returns resolved callables and values in the units pinned by 169. The PBR evaluator converts them at its hourly ODE boundary. It refuses (typed `PBR_MODEL_CARD_*` findings) when:

- the pin's digest or revision does not match the stored card, or the card's set revision or digest does not match;
- the card's `form_versions` differ from the current forms;
- a required symbol is missing.

**Supported card factors:**

| Factor | Supported forms |
|---|---|
| Light | `light.monod` |
| Temperature | `temperature.isothermal`, `temperature.ctmi`, `temperature.arrhenius_ref` |
| Nutrients | `nutrient.monod` only. Index 0 is bound to dissolved **nitrogen** (167 field `nitrogen`). Further indices are refused in T1. |
| Nutrient combination | `combine.multiplicative`, `combine.liebig` (identical with T1's single nitrogen factor) |
| Loss | `loss.first_order`, `loss.light_dark` |
| Stoichiometry | `stoich.photoautotrophic` is **required**. It provides the N quota q (kg N per kg total dry biomass) and the O₂ yield Y_O2 (kg O₂ per kg). |

**Refused:**

- `nutrient.droop`, which needs a quota state, with `PBR_MODEL_CARD_FORM_UNSUPPORTED`;
- `light.haldane`, `light.steele` and `light.eilers_peeters_steady`, whose shading-dependent productive branches cannot be selected by the Tier 1 thin-culture washout rule;
- a card without stoichiometry.

**Optics.** The card's optics factor is superseded by the unit geometry. The unit always averages the response over the cylinder (capability 3), and a card that names `optics.slab_*` gets the caveat "card optics replaced by unit geometry (cylinder)". The card's `k_X` (m² kg⁻¹) is the extinction coefficient.

**Parameter states.** Values in state `candidate` raise `PBR_PARAMETER_UNVERIFIED` (info), listing the symbols. They are never blocked and never promoted.

**Run record.** The run stores the card id, revision and digest, the set id, revision and digest, and the form versions.

### 3. Cylindrical light (`optics.cylinder_beam_diffuse_response_average`)

This is a new 169 form card at `FORM_VERSION 1.0.0`. It has typed MathML and a symbol table: D, k_X, X, I₀, f_d. It shares the 169 form tests.

**Setup.** An infinite circular cylinder of radius R = D/2 with extinction κ = k_X·X. Use polar coordinates (r, φ) over the cross-section.

**Beam.** I_b(p) = (1 − f_d)·I₀·exp(−κ·s_b(p)). Here s_b(p) = y + √(R² − x²) is the path from the entry point, with the beam travelling along +y normal to the axis.

**Diffuse.** I_d(p) = f_d·I₀·S₃(p), where:

- S₃(p) = (1/2π)·∮ Ki₂(κ·s_θ(p)) dθ;
- s_θ(p) = p·u + √((p·u)² + R² − |p|²);
- Ki₂(a) = ∫₀^{π/2} cos φ·exp(−a/cos φ) dφ, the Bickley–Naylor function.

**Response.** ⟨f_I⟩ = (1/πR²)·∬ f_I(I_b + I_d) dA. The response is averaged over the area; it is never f_I of the mean irradiance (169 parity rule).

**Numerics** (code constants under `MODEL_VERSION`):

- polar quadrature: 16 Gauss–Legendre radial nodes × 48 uniform azimuth nodes;
- S₃ uses 64 directions;
- Ki₂ comes from a log-spaced table built at import from a fixed 400-point Gauss–Legendre rule. Its relative error is ≤ 5e-5, with the asymptote √(π/2a)·e^(−a) above a = 316.

All tables are deterministic constants. κ·s is clamped before `exp`, and nothing divides by τ.

**Required properties** (tests, capability 9):

- **Thin limit:** ⟨f_I⟩ → f_I(I₀).
- **Linear response, thick limit:**
  - beam: 4/(πτ) with τ = κD;
  - 3-D diffuse: 1/τ.
- **Linear-response beam** equals the 1-D chord integral (1/πR²)·∫(1 − e^(−κc(x)))/κ dx to 1e-6.
- **Accuracy:** 16×48 is within 1e-4 of a 96×256 reference on a grid of (X, I₀, f_d).

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

N and O₂ are clipped at 0 inside the rates exactly as 107 does.

The inlet volumetric values are the inlet's 167 mass-specific values × ρ_in. Biomass, dissolved N and dissolved O₂ must each be specified and finite on the PBR inlet; 167 permits N and O₂ to be unknown, but T1 refuses an unknown value instead of assuming zero. An explicit zero remains valid. P, DIC and salinity are not consumed in T1. They pass through, with the caveat "carbon and phosphorus assumed non-limiting".

**Map.** Φ₂₄(y₀) integrates 24 h with `integrate_ode` (CVODE BDF). Tolerances are rtol 1e-10 and atol 1e-12. Augmented integral states give the daily means and the degassed O₂.

**Periodic steady state.** This is y* = Φ₂₄(y*). For each state i:

- residual: |Φ₂₄(y)_i − y_i| ≤ 1e-7·max(|y_i|, 1e-6 kg m⁻³);
- Newton with a forward-difference Jacobian, step 1e-4·max(|y_i|, 1e-4);
- at most 20 Newton steps, with step halving on a residual increase;
- the solve fails as `PBR_PERIODIC_STEADY_FAILED` when the iterations are exhausted.

**Branch rule.** This rule applies to the supported monotone Monod light response. It must not be used for photoinhibitory forms.

- Λ = (1/24)∫₀²⁴ [μ_g(t; thin limit ⟨f_I⟩ = f_I(I₀(t)), N = N_in) − k_d(t)] dt.
- **If X_in = 0 and Λ ≤ D_h:** the result is the washout state. X = 0, and N and O₂ come from the map with X ≡ 0. The status is `washout`, with the warning `PBR_WASHOUT`. This is a valid result, not a failure.
- **If X_in = 0 and Λ > D_h:**
  - Seed from X₀ = 0.05 kg m⁻³ × (Λ − D_h)/Λ, then integrate 10 days before Newton.
  - A converged state with mean X̄ < 1e-6 kg m⁻³ is rejected, and Newton restarts from a seed 4× larger, at most 3 times.
  - Then the solve fails with `PBR_PERIODIC_STEADY_FAILED` ("productive branch not found").
- **If X_in > 0:** seed from X_in after a 10-day integration. The positive solution is unique.

Λ, D_h, HRT and the branch are always reported with explicit units.

**Initialization and cache.** Each evaluation derives its Newton seed from its current inlet and model pin using the branch rule above. It does not read a previous outer iteration's state. Identical unit and inlet inputs may use 168's per-Run cache; the result therefore does not depend on iteration order.

**Outlet.** The outlet is the flow-weighted daily mean:

- X̄, N̄ and Ō₂ in kg m⁻³, converted to mass-specific values with ρ_in;
- carrier mass flow, pressure, composition and pH equal the inlet's;
- temperature equals the inlet's (ruling 1).

The carrier excludes biomass mass, as in 167/168.

**Declared generation** (168 interface (c)), in kg/s over the daily mean. Rates r̄_X and kLa_h·mean(O₂ − O₂sat) are kg m⁻³ h⁻¹, so conversion to seconds is explicit:

- biomass: V·r̄_X/3600;
- dissolved N: −q·V·r̄_X/3600;
- dissolved O₂: V·[Y_O2·r̄_X − kLa_h·mean(O₂ − O₂sat)]/3600. The degassed O₂ is reported separately.

The per-unit residual closes as in − out + generation to 167's rule. A whole-graph balance includes the generation terms.

**Limits.**

- Zero inlet flow (Q = 0) refuses with `PBR_NO_THROUGHFLOW` (a unit failure, which makes the 168 run `segment_failed`).
- HRT outside [0.1, 100] d raises `PBR_HRT_OUT_OF_RANGE` (warning).
- An inlet vapor fraction above 1e-6 fails, following the 167 liquid-only rule.
- **Wall time:** each evaluation is capped at 5 s. Eager module imports happen at server startup; any import inside a Run counts against the 168 wall budget. A typed `wall_budget` unit failure feeds the 168 budget rule.

**106 evaluator.** It has `backend_kind="dynamic_simulator"`, `fidelity="reduced_order"`, and an `unqualified` envelope. Its `qualification_record_ref` points to a new synthetic-unqualified ledger. It can also be called headless with scalar outputs (X̄, productivity, Λ, HRT, ΔP, power), but it is not added to Engineering Studies in 170.

**Unit result** (`reported`), each value with its unit:

- branch;
- Newton iterations and map residual;
- Λ (h⁻¹), D_h (h⁻¹) and HRT (d);
- X̄ and net volumetric biomass productivity 24·D_h·(X̄ − X_in) (kg m⁻³ d⁻¹); this may be negative when decay exceeds growth;
- net biomass production rate 24·V·r̄_X (kg/d), equal to 86,400·Q·(X̄ − X_in); outlet biomass throughput is separately labelled if shown;
- minimum and mean N;
- maximum and mean O₂, and the maximum O₂ saturation ratio;
- degassed O₂;
- Re, ΔP and pumping power;
- the balance residuals.

It also carries the fidelity label "T1 · unqualified · periodic steady state, cylinder light, no energy balance", the caveats, and the card pin.

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
| `PBR_REQUIRES_NITROGEN` | blocker | Dissolved N is absent or unknown on the PBR inlet. Explicit zero is valid. |
| `PBR_REQUIRES_OXYGEN` | blocker | Dissolved O₂ is absent or unknown on the PBR inlet. Explicit zero is valid. |
| `PBR_REQUIRES_MODEL_CARD` | blocker | The unit has no model pin. |
| `PBR_MODEL_CARD_UNAVAILABLE` | blocker | The pin does not resolve, or its digest or form versions differ. |
| `PBR_MODEL_CARD_FORM_UNSUPPORTED` | blocker | The card uses a refused form. |
| `PBR_PARAMETER_UNVERIFIED` | info | The card's set has `candidate` values. |
| `PBR_HRT_OUT_OF_RANGE` | warning | HRT outside [0.1, 100] d. Before a run it uses the feed's ṁ/ρ, where ρ is the 167 density basis of the culture feed. |
| `PBR_TEMPERATURE_DECLARED_DIFFERS` | info | \|T_mean − T_inlet\| > 5 K (ruling 1). |
| `PBR_WASHOUT` | warning | Emitted after a run. |

168's findings apply unchanged. A PBR on a consumed tear's cycle is a normal 168 mixed loop.

### 7. Fingerprints and staleness

The 168 layout-free fingerprint gains:

- the PBR parameters;
- the model pin (card id, revision and digest);
- the resolved set digest;
- `jarvis.pbr_unit_t1` and `pbr_unit.v1`.

Editing a PBR parameter or re-pinning the card stales results. Layout edits do not. A newer card revision does **not** silently change a unit; the inspector shows "newer card revision available". Single-owner and 168-only drafts keep their fingerprints byte-identical.

### 8. Operator UI and agent actions

**Palette and canvas.**

- The palette's "Jarvis units" group gains "Photobioreactor (T1)".
- The canvas and inspector owner badges come from the registry `owner`. No "DWSIM" string is hard-coded anywhere.

**PBR inspector.** It has tabs: Overview, Geometry, Biology, Operation and Light & environment, and Results. They are keyboard-accessible with `role="tablist"`.

- **Overview:** the owner, fidelity, derived V/Q/HRT and the last run status.
- **Geometry, Operation, Light & environment:** typed QuantityInputs with units and inline domain validation. The amplitude uses °C/K difference units.
- **Biology:** an embeddable **model card picker** built from `listBioCards` and `listBioSets`. It shows each card's factors with their equations through the existing allowlisted MathML renderer, the set's verification chips, and the pin's revision. Pinning applies `set_unit_model`. A "newer revision available" notice offers to re-pin.
- **Results:** branch, Λ vs D, HRT, X̄, productivity, N/O₂ means and extremes, hydraulics, balance residuals, and Newton/map residuals. Grouped under `Results · Jarvis`, they carry the fidelity label and the caveats.
- The outlet stream shows `Culture · Jarvis`.

**Layout.** The editor is readable at 1280 and 1440 CSS px with no horizontal overflow and no raw JSON in the normal view.

**Agent (166 vocabulary).**

- `add_unit`, `insert_unit_after` and `connect` work for the PBR through the registry.
- `set_value` on PBR parameters is confirm tier, with units validated.
- A new action `set_unit_model {unit, card}` resolves a card by id or exact name to its current revision and digest. It is confirm tier and maps to one `set_unit_model` DraftOp. It is wired in the action models, `_process_ops`, the brief, the Hermes MCP schema, the thread guard's op list and the frontend presentation.
- The agent never edits or verifies sets (169 non-goal), and Run stays operator-initiated.
- **Brief.** The Process brief is registry-derived: unit owners, the PBR card name and verification summary, and the last run's branch, HRT, Λ, residual and status. It stays within the 6000-character cap, and a test asserts it with 35 objects. The static text "Jarvis-native units arrive with 168/170" and 169's "PBR units arrive with 170" are replaced, together with the tests that assert them.

### 9. Required evidence

**1. Backend tests.**

- **Cylinder properties** (capability 3): thin and thick limits, the chord integral, the Ki₂ table, quadrature convergence and the golden Q2 table.
- **107 parity:** v2 outputs bitwise on all 107 fixtures; `test_bluerev_pbr_107.py` and `test_bio_models_forms.py` unchanged and passing.
- **Periodic steady state:**
  - balances close ≤ 1e-8 relative;
  - the map residual is within tolerance;
  - the washout rule on the 107 fixture with X_in = 0 at HRT 2, 3, 5 and 8 d: washout at or below the 2.73 d critical HRT, the productive branch above it, and never the trivial state on the productive side;
  - X_in > 0 gives a unique positive state;
  - D_s ↔ D_h, kLa_s ↔ kLa_h, photoperiod seconds ↔ hours, hourly generation ↔ kg/s, and hourly productivity ↔ kg/day conversions close against an independent steady mass-balance calculation;
  - with X_in > 0, net productivity is based on X̄ − X_in while outlet biomass throughput remains a distinct quantity;
  - D → 0 with a long run approaches the 107 time average within a stated band;
  - determinism over two runs and cold/warm processes;
  - typed refusals mirror 107's matrix.
- **Model card resolution:** pins, mismatches, unsupported forms, a missing stoichiometry factor and the nutrient index binding.
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
  - Per-unit and whole-graph balances close: biomass with the PBR generation, total N, and O₂ with the degassed O₂.
  - Two runs agree to 1e-9 relative.
  - The whole Run is under 90 s, with per-phase wall times recorded.
- **Washout.** Once through (feed → PBR → product) with X_in = 0 at an HRT below critical, the run completes with `PBR_WASHOUT` and zero outlet biomass.
- **Staleness.** Editing a PBR parameter or re-pinning the card stales the results. A layout move does not.

**4. Exact-head real Chromium at 1280 and 1440 CSS px** (local Gemma for the Sidecar steps).

1. Add the PBR from the palette, connect it, and pick a card in Biology, seeing the verification chips.
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
  - 168's numerics and limits;
  - 169's `FORM_VERSION`;
  - the Heater `temperature_change` storage.
- **Never done:**
  - biology inside DWSIM;
  - shipping literature parameter values as defaults (169 rule);
  - promoting parameter verification states.
- **No SQL migration.** The draft `schema_version` stays 1, and old documents load unchanged.
