# 169 — Biological model cards

State: **ready**. This spec combines definition, contract and readiness under the maintainer directive of 2026-10-02 (continue the planned PBR roadmap in dependency order, with the [PBR engineering architecture record](../implementation/pbr-engineering-architecture-2026-10-02.md) and the ranked engineering inventory as joint authority). Dependencies are 102, 106 and 107. It owns the reviewed library of biological model forms and the revisioned, source-traceable parameter sets that 170 (PBR unit) and 180 (rate-law kinetics) consume. It adds no unit and no simulation.

## Fresh evidence (master `da7dd02a`)

Code survey: `out/wpbr/a169.report.md`.

1. **107 hard-codes its forms.** `bluerev.pbr_day_night` implements:
   - a half-sine PAR attenuated by depth-sampled Beer–Lambert;
   - Monod or Haldane light response;
   - cardinal (CTMI) or isothermal temperature;
   - Monod or replete nitrogen;
   - first-order loss.

   Every coefficient is required and has no default, and a `basis_ref` must be present. Its envelopes are `unqualified`, and its ledger uses synthetic fixture provenance (`pbr_evaluator.py`; `scripts/qualification/107/pbr_day_night.v2.ledger.json`).
2. **`basis_ref` is presence-checked, not resolved.** `Quantity.basis_ref` is a generic `SourceRef` (`authority_owner`, `object_type`, `object_id`, workspace, revision or digest). Nothing verifies that it resolves to a literature value (`refs.py`; `pbr_evaluator.py`).
3. **Literature exists.** Spec 114 stores `literature_sources` and `literature_entries`. Entries are claims or data with a numeric or text value, unit, status, locator and context (`literature_schema.py`; `literature_service.py`).
4. **States differ.** 102's `QualificationStatus` (`unqualified … qualified`) is an evaluator/evidence qualification. The record's per-value verification states (`candidate → source_verified → expert_reviewed → qualified`) are a different concept and must stay distinct.
5. **Revisions.** The SQL `parameters` table (0016 lifecycle) stores single project parameters. It has no set aggregate, no immutable per-edit history and no per-value verification. The 155 draft has a proven JSON revision and CAS pattern.
6. **Frontend.** No KaTeX, MathJax or math plugin is installed. Engineering Studies has panel, badge and disclosure patterns, but no model-card UI.
7. **Reference forms (record §4.4).** QSDsan PM² (NCSA) restates:
   - depth-averaged Beer–Lambert;
   - Eilers–Peeters light with photoadaptation;
   - Droop and Monod nutrient factors combined by minimum (Liebig);
   - Arrhenius temperature;
   - maintenance and dark respiration.

   Equations are reference material. No code is copied, and its defaults are not evidence for *N. gaditana*.

## Decision

**Model forms are reviewed Jarvis code with declarative cards. Parameter sets are revisioned data owned by a new narrow `bio_models` owner. Verification is an explicit, recorded human act against a resolvable source.**

- A **form** is a pure, versioned Python function with a declarative card: id, version, family, equation as presentation MathML, symbol table (symbol, meaning, unit, valid range), required states and inputs, and an `applies_to` statement. The card and the function live together and are tested together. Native MathML (supported by the product's Chromium target) renders equations, so no new dependency is added.
- A **parameter set** is a revisioned JSON document under the workspace data root, using the same revision, digest and CAS discipline as the 155 draft. No SQL migration is added. 102 qualification and the 0016 project parameters are not redefined.
- **Per-value states** are `candidate`, `source_verified` and `expert_reviewed`. They are parameter provenance and review states, **never** 102 qualification states, and they promote no model or evaluator. 169 has no per-value `qualified` state; any later qualification is a 102-ledger record over a model scope.
- The library ships **forms and empty set templates only**. No literature value is shipped or adopted without source evidence (record §10.2).

Alternatives rejected:

- **QSDsan as the form library:** a 950 MB dependency stack, and its forms are wastewater-calibrated. It is used only as a cited reference.
- **User-typed equations:** not Tier 1–2 (record §5.3). A dimension-checked custom-expression form is a later spec.
- **Reusing the `parameters` table as the set store:** this would need a set aggregate and per-value verification, and would break the table's single-value lifecycle semantics.

## Accepted capability

1. **Form library (`bio_models.forms`, version-pinned).** These equations are normative. Inputs carry units, and every parameter has a domain; violating a domain refuses evaluation with the symbol named. I is PAR in µmol m⁻² s⁻¹, T is in K, and nutrient concentrations are in kg m⁻³.
   - **Light response f_I(I), I ≥ 0, dimensionless in [0, 1]:**
     - `light.monod` (Monod/Tamiya, same equation): f = I/(K_I + I), with K_I > 0.
     - `light.haldane` (Haldane/Andrews): f = I/(K_I + I + I²/K_i), with K_I, K_i > 0. Its maximum is at I = √(K_I·K_i).
     - `light.steele`: f = (I/I_opt)·exp(1 − I/I_opt), with I_opt > 0. It is 0 at I = 0 and 1 at I = I_opt.
     - `light.eilers_peeters_steady`: the steady-state curve of the Eilers–Peeters model, not its dynamic photoinhibition model. With x = I/I_opt, f = (2 + β)·x/(x² + β·x + 1), with I_opt > 0 and β ≥ 0. It is 1 at x = 1.
   - **Slab optics** (profile I(z) = I₀·exp(−k_X·X·z), z ∈ [0, L], with k_X ≥ 0 [m² kg⁻¹], X ≥ 0 [kg m⁻³], L > 0 [m], τ = k_X·X·L):
     - `optics.slab_mean_irradiance`: Ī = I₀·(1 − e^(−τ))/τ, and Ī → I₀ as τ → 0.
     - `optics.slab_response_average`: ⟨f_I⟩ = (1/L)·∫₀ᴸ f_I(I(z)) dz, evaluated by 8-point Gauss–Legendre exactly as 107 does. This is the **107 parity form**. Applying f_I to Ī is a different, generally larger quantity, and 169 never presents it as 107-equivalent. The cylindrical geometry belongs to 170.
   - **Temperature f_T(T), dimensionless:**
     - `temperature.isothermal`: f = 1.
     - `temperature.ctmi` (Rosso cardinal model with inflexion, as used by Bernard–Rémond): with T_min < T_opt < T_max,
       f = (T − T_max)(T − T_min)² / {(T_opt − T_min)[(T_opt − T_min)(T − T_opt) − (T_opt − T_max)(T_opt + T_min − 2T)]}
       for T_min < T < T_max, and 0 otherwise.
     - `temperature.arrhenius_ref`: f = exp[−(E_a/R)(1/T − 1/T_ref)], with E_a ≥ 0 [J mol⁻¹] and T_ref > 0. Here μ_max is defined at T_ref.
   - **Nutrients.** Each nutrient j first yields its own factor f_j ∈ [0, 1]:
     - `nutrient.monod`: f_j = S_j/(K_j + S_j), with K_j > 0 and S_j ≥ 0.
     - `nutrient.droop`: f_j = max(0, 1 − Q_min,j/Q_j), with Q in kg of element per kg of dry biomass and 0 < Q_min,j. It is 0 for Q_j ≤ Q_min,j. It needs the quota as an input; in 169 the quota is an evaluation input, and 170 carries it as state.
     - Combination, applied to the per-nutrient factors: `combine.multiplicative` f_S = Π f_j, or `combine.liebig` f_S = min_j f_j.
   - **Losses** are specific biomass-loss rates r [h⁻¹], subtracted from μ. They are not substrate maintenance demand.
     - `loss.first_order`: r = k_d.
     - `loss.light_dark`: r = m_L when I₀ > I_dark, and m_D otherwise. I_dark is a parameter.
   - **Stoichiometry** (`stoich.photoautotrophic`):
     - Biomass is ash-free dry biomass CH_aO_bN_cP_d per C-mol, with an ash mass fraction w_ash of total dry biomass.
     - Carbon source is CO₂. The N source is selectable: NH₃ or HNO₃ (neutral species). P is supplied as H₃PO₄, with H₂O and O₂ as the remaining species.
     - The five coefficients follow uniquely from the C, H, O, N and P balances.
     - Yields are reported per kg of **total** dry biomass (scaled by 1 − w_ash): kg O₂ produced, kg CO₂, kg N and kg P consumed. Elemental closure is tested.
   - O₂-inhibition and pH factors belong to 175. Each form declares `applies_to`. For example, `nutrient.monod` reads "nutrient-limitation factor of a bioreactor growth model; not a reaction rate law in a DWSIM reactor (see 180)".
2. **Growth model composition (`model card`).** A model card is a document in the same owner. It holds:
   - μ_max;
   - one form per selected family (light, temperature, nutrients with combination rule, losses);
   - a stoichiometry form;
   - a reference to one parameter-set revision.

   It defines μ_net = μ_max · ⟨f_I⟩ · f_T · f_S − r, where ⟨f_I⟩ comes from a slab optics form wrapped around the chosen light response. Each factor's form id and version are pinned. A pure evaluator returns μ and the per-factor breakdown with units. It refuses when any required value is missing or out of its symbol's valid range, naming the symbol. No silent defaults.
3. **Storage.** Parameter sets and model cards are separate aggregates. Each is one revisioned JSON document under the workspace data root, at a location owned by `core/paths.py` (`bio_models/sets/<id>`, `bio_models/cards/<id>`). Every write — value edit, duplicate, verification, review — is one atomic CAS revision of its own aggregate (expected revision, digest, parent, actor, time), following the 155 draft discipline. Verification history lives inside the set's revisions. A 409 conflict reloads in the UI.
4. **Parameter sets.**
   - **Value records.** Each value carries:
     - a value and unit, checked for dimensional compatibility with the symbol's unit;
     - an optional exact `basis_ref` to a `literature_entry` (or `literature_source` plus locator) in the same workspace;
     - species/strain, conditions text and the validity range;
     - a verification state, with the actor and time of the last state change.
   - **Editing.** Duplicating a set and editing values create new revisions through CAS. Editing a value resets its state to `candidate`. A value without `basis_ref` displays as "operator assumption".
   - **`source_verified`.** Requires an explicit operator action, which resolves `basis_ref` to an existing literature source or entry.
     - Literature records have no revision or digest of their own. The action therefore records a **snapshot digest**: SHA-256 of canonical JSON of the source metadata, the entry fields (value, unit, text, locator kind and range, context) and the backing artifact's SHA-256. When there is no backing artifact, that member is `null` and the badge says "no backing document".
     - If the entry has a numeric value and unit, both values are converted to SI and must satisfy |v − v_src| ≤ 1e-6·max(|v|, |v_src|) + 1e-12. Otherwise the action is refused with both values shown.
     - If the entry has no numeric value, the operator must confirm the shown locator in the action. Supported locator kinds are page, line and section; tables and figures are written as section text, e.g. "Table 2".
   - **`expert_reviewed`.** Requires `source_verified`, a reviewer name and a note.
   - **Staleness.** If the recomputed snapshot digest of the cited record later differs, the value displays "source changed since verification" and its state drops to `candidate` in the next revision created by any edit. The stored history is never rewritten.
   - **Templates.** Shipped templates (e.g. "N. gaditana T1 — empty") contain symbols and units only.
5. **Operator UI.**
   - A **Biology model library** panel reachable from the Process stage toolbar ("Biology models…"), designed to be embedded by 170's PBR Biology tab.
   - **Form cards.** Each card shows the equation rendered from a typed, allowlisted MathML element tree (never raw HTML insertion), symbol table with units and ranges, `applies_to`, version, and reference citations (e.g. QSDsan PM², 107).
   - **Model-card builder.** A factor picker per family.
   - **Parameter table.** Shows symbol, value and unit (unit-selectable), a range bar with off-range warning, source link, verification badge and the actions Verify / Review / Duplicate set / Edit. Revision history is visible.
   - **Evaluation preview.** For one operating point (I, T, S), shows μ and the factor breakdown as a table.
   - Readable at 1280 and 1440 CSS px. Keyboard reachable. No raw JSON in the normal view.
6. **Agent explanation (166 integration).** `bio_models` exposes `kinetics_explanation()`, derived from form `applies_to` metadata. The 166 Process surface brief replaces its static kinetics limit text with the output of that seam. Asked to "add Monod kinetics to PFR-1", the agent explains that Monod is a nutrient-limitation factor of a bioreactor growth model (form `nutrient.monod`), that DWSIM reactor rate laws arrive with 180, and that PBR units arrive with 170. No action is proposed. Agents cannot edit or verify parameter sets in 169.

## Boundaries / non-goals

- No PBR unit, culture state integration, dynamic simulation, profiles or charts (170–173). No O₂ or pH factors (175). No DWSIM rate laws (180).
- No shipped literature values, no automatic verification, no `qualified` state, no change to 102/106 contracts, 107 behavior, frozen 145 contracts or SQL migrations.
- FMU-neutral boundary (record §4.4): forms are pure functions over typed, unit-bearing inputs.

## Required evidence

- Focused backend tests:
  - per form: the analytic limits stated above (Monod ½ at I = K_I; Haldane maximum at √(K_I·K_i); Steele and Eilers–Peeters 1 at I_opt; CTMI 0 at T_min and T_max and 1 at T_opt; Arrhenius 1 at T_ref; Droop 0 at Q_min; Ī → I₀ as τ → 0), monotonicity where defined, and domain refusal;
  - stoichiometry elemental closure and uniqueness for both N sources;
  - 107 parity within 1e-12 for Monod/Haldane × `optics.slab_response_average`, CTMI and Monod N against `pbr_evaluator` with identical inputs;
  - a test showing f_I(Ī) ≠ ⟨f_I⟩ for a nonlinear response;
  - model-card evaluation, breakdown and refusals;
  - set CAS, revisions, duplicate and edit-resets-state;
  - verification: resolve, value-match refusal with both values, zero and near-zero matching, locator confirmation, snapshot digest recording without an artifact, and source-changed display;
  - `expert_reviewed` preconditions, and the absence of any qualification side effect;
  - unit compatibility refusal;
  - the 166 brief's kinetics text derived through `kinetics_explanation()` (a deterministic contract test).
- Frontend build and node contract tests for the library panel, the allowlisted MathML renderer, parameter table badges and actions.
- A checked-in 169 browser-proof plan under `.github/browser-proof/plans/`.
- Exact-head **real Chromium** acceptance at 1280 and 1440 CSS px:
  - open Biology models from Process and view the Haldane card's equation and symbols;
  - build a model card (Haldane + CTMI + Monod N + Liebig + first-order loss);
  - duplicate the empty template and enter μ_max with a literature entry created in the workspace;
  - Verify (match), then attempt Verify with a mismatched value (refused, both values visible);
  - Review;
  - edit a verified value: it resets to candidate and creates a new revision;
  - evaluation preview shows the breakdown;
  - Sidecar (local Gemma) on Process: "add Monod kinetics to PFR-1" gets the explanation and no change.
- Screenshots inspected; no raw JSON visible.
