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
- **Verification states** are per value: `candidate`, `source_verified`, `expert_reviewed`. `qualified` is reserved for a later 102-ledger link and cannot be set in 169.
- The library ships **forms and empty set templates only**. No literature value is shipped or adopted without source evidence (record §10.2).

Alternatives rejected:

- **QSDsan as the form library:** a 950 MB dependency stack, and its forms are wastewater-calibrated. It is used only as a cited reference.
- **User-typed equations:** not Tier 1–2 (record §5.3). A dimension-checked custom-expression form is a later spec.
- **Reusing the `parameters` table as the set store:** this would need a set aggregate and per-value verification, and would break the table's single-value lifecycle semantics.

## Accepted capability

1. **Form library (`bio_models.forms`, version-pinned).** Families and forms:
   - **light response** f_I(I): Monod/Tamiya, Haldane/Andrews, Steele, Eilers–Peeters (static);
   - **light attenuation** Ī(I₀, X, path): depth-averaged Beer–Lambert slab (107 parity). The cylindrical form belongs to 170;
   - **temperature** f_T(T): isothermal, CTMI (Rosso/Bernard–Rémond), Arrhenius;
   - **nutrient** f_S: Monod per nutrient, Droop quota (declares the quota state it requires; usable once 170 carries the quota);
   - **nutrient combination**: multiplicative, Liebig minimum;
   - **losses**: first-order decay, maintenance respiration with distinct light and dark rates;
   - **stoichiometry**: elemental biomass formula (C, H, O, N, P with ash fraction) giving yields of O₂ produced and CO₂, N and P consumed per kg of biomass, with elemental closure.

   O₂-inhibition and pH factors belong to 175 and are not in 169. Each form declares `applies_to`. For example, nutrient Monod reads "nutrient-limitation factor of a bioreactor growth model; not a reaction rate law in a DWSIM reactor (see 180)".
2. **Growth model composition (`model card`).** A model card is a document in the same owner. It holds:
   - μ_max;
   - one form per selected family (light, temperature, nutrients with combination rule, losses);
   - a stoichiometry form;
   - a reference to one parameter-set revision.

   It defines μ = μ_max · f_I · f_T · f_S − losses, with each factor's form id and version pinned. A pure evaluator returns μ and the per-factor breakdown with units. It refuses when any required value is missing or out of its symbol's valid range, naming the symbol. No silent defaults.
3. **Parameter sets.**
   - **Value records.** Each value carries:
     - a value and unit, checked for dimensional compatibility with the symbol's unit;
     - an optional exact `basis_ref` to a `literature_entry` (or `literature_source` plus locator) in the same workspace;
     - species/strain, conditions text and the validity range;
     - a verification state, with the actor and time of the last state change.
   - **Editing.** Duplicating a set and editing values create new revisions through CAS. Editing a value resets its state to `candidate`. A value without `basis_ref` displays as "operator assumption".
   - **`source_verified`.** Requires an explicit operator action. The action resolves `basis_ref` to an existing literature record and records that record's content digest and the operator. If the entry has a numeric value and unit, it must match the stored value after unit conversion within 1e-6 relative; otherwise the action is refused with both values shown. If the entry has no numeric value, the operator must confirm the shown locator (page, table, figure) in the action.
   - **`expert_reviewed`.** Requires `source_verified`, a reviewer name and a note.
   - **Staleness.** If the cited literature entry later changes digest, the value displays "source changed since verification" and its state drops to `candidate` in the next revision created by any edit. The stored history is never rewritten.
   - **Templates.** Shipped templates (e.g. "N. gaditana T1 — empty") contain symbols and units only.
4. **Operator UI.**
   - A **Biology model library** panel reachable from the Process stage toolbar ("Biology models…"), designed to be embedded by 170's PBR Biology tab.
   - **Form cards.** Each card shows the MathML equation, symbol table with units and ranges, `applies_to`, version, and reference citations (e.g. QSDsan PM², 107).
   - **Model-card builder.** A factor picker per family.
   - **Parameter table.** Shows symbol, value and unit (unit-selectable), a range bar with off-range warning, source link, verification badge and the actions Verify / Review / Duplicate set / Edit. Revision history is visible.
   - **Evaluation preview.** For one operating point (I, T, S), shows μ and the factor breakdown as a table.
   - Readable at 1280 and 1440 CSS px. Keyboard reachable. No raw JSON in the normal view.
5. **Agent explanation (166 integration).** The Process surface brief's known-limits section derives its kinetics explanation from form metadata. Asked to "add Monod kinetics to PFR-1", the agent explains that Monod is a nutrient-limitation factor of a bioreactor growth model (form `nutrient.monod`), that DWSIM reactor rate laws arrive with 180, and that PBR units arrive with 170. No action is proposed. Agents cannot edit or verify parameter sets in 169.

## Boundaries / non-goals

- No PBR unit, culture state integration, dynamic simulation, profiles or charts (170–173). No O₂ or pH factors (175). No DWSIM rate laws (180).
- No shipped literature values, no automatic verification, no `qualified` state, no change to 102/106 contracts, 107 behavior, frozen 145 contracts or SQL migrations.
- FMU-neutral boundary (record §4.4): forms are pure functions over typed, unit-bearing inputs.

## Required evidence

- Focused backend tests:
  - per form: analytic limits (e.g. Monod → 1 as S → ∞ and half at S = K; Haldane maximum at √(K·K_i); CTMI zero at T_min and T_max and one at T_opt; Beer–Lambert → I₀ as X → 0), monotonicity and range refusal;
  - stoichiometry elemental closure;
  - 107 parity for Monod, Haldane, CTMI and depth-averaged slab against `pbr_evaluator` with identical inputs;
  - model-card evaluation, breakdown and refusals;
  - set CAS, revisions, duplicate and edit-resets-state;
  - verification: resolve, value-match refusal with both values, locator confirmation, digest recording, source-changed display;
  - `expert_reviewed` preconditions and `qualified` refusal;
  - unit compatibility refusal;
  - brief explanation text derived from form metadata.
- Frontend build and node contract tests for the library panel, form card MathML, parameter table badges and actions.
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
