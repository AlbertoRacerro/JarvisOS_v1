# 167 — Process culture streams

State: **ready**. This spec combines definition, contract and readiness under the maintainer directive of 2026-10-02 (continue the planned PBR roadmap in dependency order after 166, with the merged [PBR engineering architecture record](../implementation/pbr-engineering-architecture-2026-10-02.md) and the ranked engineering inventory as joint authority). Dependencies are 155, 158, 162 and 166. It is the first slice of the record's order of value (167 → 168 → 169 → 170). It gives Process streams a Jarvis-owned biological culture state and makes every unit's computational owner explicit, without adding any Jarvis-native unit or any biology inside DWSIM.

## Fresh evidence (master `a40eb9b0`, 166 head `b95c762d`)

Code survey: `out/wpbr/a167.report.md`.

1. **No document model class.** The draft is a JSON document (`schema_version: 1`) in which units and streams share `objects` (`draft.py` `empty_document`). A feed is a `MaterialStream` without `source`; its `spec` carries pressure, one flow basis, one thermal basis and a mass or mole composition over the closed list of 21 compounds (`draft_models.py`).
2. **Closed op set with CAS.** `DraftOp` is a closed discriminated union (`add_unit` … `set_thermo`); patches carry an expected revision. Results are current while the layout-free process fingerprint matches. `move`, `set_route` and `set_orientation` are the only layout ops.
3. **Registry.** `UNIT_REGISTRY` declares the 11 DWSIM unit types, their ports and parameter specs. Nothing declares a computational owner, and the UI has no owner badge.
4. **Quantities.** `QUANTITY_UNITS` is closed and has no concentration, molar concentration, salinity or pH kind.
5. **Results.** After a successful solve the compiler reads every material stream and stores `outcome["streams"][tag]`. The inspector shows these under `Results · DWSIM`. No topological evaluation order is exposed; cycles require a DWSIM `Recycle`.
6. **Fingerprints.** The DWSIM materialization fingerprint hashes the normalized materialization (`expected()`), which a read-back must reproduce. Adding Jarvis-only fields there would make read-back comparison fail.
7. **Contracts.** `frontend/src/api/processDraft.ts` is hand-maintained; `generate_frontend_contracts.py` does not cover the Process draft. Spec 145 freezes `Quantity` and `MaterialStateRef` but not a process schema, so this is Process-domain state owned by the 155 draft.
8. **107.** `bluerev.pbr_day_night` carries biomass, dissolved nitrogen and dissolved O₂ in kg/m³. It has no phosphorus, DIC, pH or salinity.

Superseded for mixed-engine culture recycles by [168](168-process-mixed-engine-solve.md): Recycle uses `culture_rule: "tear"`, and `CULTURE_RECYCLE_UNSUPPORTED` is retired for consumed cross-engine tears.

## Decision

**The culture extension is Process-draft state owned by Jarvis and propagated by Jarvis after the DWSIM solve. DWSIM never sees it.**

- Unit ownership is a **registry property** (`owner: "dwsim"` for the existing 11 types), not a per-document field. Old revisions therefore need no upgrade, and 168 adds `jarvis_bio` types to the same registry.
- Culture is specified on **feeds** only. Every other stream's culture is computed. In 167 no unit transforms biology: DWSIM-owned units only carry the culture through declared pass-through rules, and units without a rule refuse it.
- The internal propagation basis is **mass-specific** (per kg of stream). Mass balances therefore close regardless of density changes across heaters or pumps. Volumetric display values are converted using the DWSIM-reported mass density of each stream.

Alternatives rejected:

- **A Biomass compound in DWSIM:** DWSIM 10.2.9 has none, and MCP cannot add one (record P7). A pseudo-compound would put biology inside a thermodynamic package.
- **A culture field on every stream as editable state:** computed streams would then hold a second authority over values that the propagation owns.
- **Iterating culture around recycle loops in 167:** convergence and tear residual reporting belong to the 168 mixed-engine loop. 167 refuses culture on a cycle rather than reporting a value it did not converge.

## Accepted capability

1. **Unit ownership.**
   - Each `UNIT_REGISTRY` entry declares `owner` (`dwsim` for all 11 existing types) and a `culture_rule` (below). The registry read API returns both.
   - Canvas nodes and the unit inspector show an owner badge ("DWSIM"). Stream results remain labelled `Results · DWSIM`; culture results are labelled `Culture · Jarvis`.
   - The 166 Process surface brief lists the owner of the selected unit and the culture rule. Agents can explain ownership, but cannot change it.
2. **Culture schema (`stream.spec.culture`, feeds only).** All fields are optional, but a feed with a `culture` section must give biomass and salinity. Fields, quantity kinds and accepted display units:
   - biomass X: `mass_concentration` — kg/m³, g/L, mg/L;
   - dissolved nitrogen (as N) and dissolved phosphorus (as P): `mass_concentration`;
   - dissolved O₂: `mass_concentration`;
   - DIC: `molar_concentration` — mol/m³, mmol/L;
   - pH: `ph`, a bounded scalar in [0, 14] that is never unit-converted or flow-averaged;
   - salinity: `salinity` — g/kg (absolute salinity).

   The new quantity kinds are added to `QUANTITY_UNITS` with explicit SI storage (kg/m³, mol/m³, g/kg, pH) and reviewed conversion factors. Values are stored as `{si, value, unit}`, as for existing quantities. Tier-2/3 fields from the record (intracellular N quota, lipid marker) are out of scope.

   An omitted optional field (N, P, O₂, DIC, pH) means **unknown**, not zero. It propagates as `null` with the reason "not specified on feed <tag>". An explicit 0 is a value.
3. **Operations.**
   - A new `set_stream_culture` DraftOp (feed tag plus the full culture section or `null` to clear) joins the closed op union. It is a meaning op: it stales results and goes through CAS, revisions, undo and restore like every other op.
   - Culture is part of a **culture-inclusive result fingerprint**, which is the fingerprint used for staleness. That fingerprint includes the culture schema and propagation versions. Culture is not part of the DWSIM materialization (`expected()`), its read-back comparison, or its materialization fingerprint. Tests must prove both: a culture-only edit stales results, and the DWSIM materialization fingerprint and read-back are unchanged.
   - Documents and revisions without culture load unchanged.
4. **Validation findings (162 style, `source: "jarvis"`).**
   - Blocker `CULTURE_CARRIER_NOT_AQUEOUS`: a culture feed whose declared compounds lack Water, or whose Water **mass** fraction is below 0.5. A mole-basis composition is converted to mass fractions for this check.
   - Warning `CULTURE_CARRIER_IMPURE`: Water mass fraction below 0.95. Both thresholds are screening bounds, not scientific limits.
   - Blocker `CULTURE_FEED_NOT_LIQUID`: a culture feed specified with a vapor fraction above 0.
   - Blocker `CULTURE_FIELD_REQUIRED` for missing biomass or salinity, and `CULTURE_VALUE_OUT_OF_RANGE` for negative concentrations, pH outside [0, 14], or salinity above 300 g/kg (a plausibility bound, not an operating range).
   - Blocker `CULTURE_UNIT_UNSUPPORTED`: a culture-carrying stream reaches a unit whose `culture_rule` is `refuse` (Flash, DistillationColumn, PFR). The finding names the unit and explains that biology cannot pass through DWSIM VLE or reactors, and that Jarvis-native units arrive with 168/170.
   - Blocker `CULTURE_RECYCLE_UNSUPPORTED`: a culture-carrying stream lies on a cycle. Converged culture recycles arrive with 168.
   - Warning `CULTURE_MIXED_WITH_UNSPECIFIED`: a Mixer combines culture and non-culture inlets. The non-culture inlet contributes zero biomass, nutrients, O₂ and DIC and zero salinity, and this assumption is stated in the warning.
   - A flowsheet without culture produces no culture findings and behaves exactly as before.
5. **Propagation (`jarvis_culture_propagation`, version 1).** This runs only after a successful DWSIM solve, in topological order over the acyclic culture-carrying subgraph, using DWSIM-reported mass flows and densities.
   - Internal basis is per kg of the **total** DWSIM stream: biomass, N, P and O₂ in kg/kg; DIC in mol/kg; salinity in g/kg. pH is a non-conserved scalar. Feed volumetric inputs are converted with the feed's own DWSIM density; computed volumetric display values use each stream's own density.
   - Density source: the raw DWSIM stream result's `phases[name="Mixture"].density_kg_m3`. It must be finite and positive; otherwise that stream's culture result fails visibly. No fallback density is used, and volumetric values inherit the record's seawater-as-water approximation, which the fidelity label states.
   - **Liquid-only eligibility.** A culture-carrying stream whose solved vapor fraction is above 1e-6 (for example after a Heater, Cooler or Valve) gets no culture values. Its culture result fails with post-run finding `CULTURE_PHASE_NOT_LIQUID` naming the stream and the upstream unit, and everything downstream of it is marked failed. Suspended biomass and dissolved species are never attributed to a vapor phase.
   - Pass-through (Heater, Cooler, Pump, Valve, and each side of a HeatExchanger independently): mass-specific values are copied unchanged.
   - Splitter: every outlet copies the inlet's mass-specific values.
   - Mixer: mass-flow-weighted average of mass-specific values for biomass, N, P, O₂, DIC and salinity. A field that is `null` on any culture inlet is `null` on the outlet. Non-positive total inlet mass flow fails the outlet's culture result.
   - pH: pass-through and Splitter copy it. A Mixer output copies a pH only when all inlets are culture inlets that agree within 0.01. The result labels it "screening placeholder; mixed pH requires carbonate speciation (175)". Otherwise pH is `null` with that reason. pH is never averaged.
   - Recycle: refused (finding above).
   - Each culture result records its owner, propagation version, mass-specific values, volumetric display values with the density used, and its fidelity label "screening — pass-through, no reaction or gas transfer". It also records per-unit balance residuals for each conserved field with a value: biomass, N, P, O₂ and salt (inlets minus outlets, kg/s), and DIC (mol/s). A residual passes when |in − out| ≤ 1e-9·max(in, out) + floor, with a floor of 1e-12 kg/s or 1e-12 mol/s. A failing residual marks the result failed rather than showing it.
   - Dissolved O₂ is carried without solubility or degassing changes; the result shows a supersaturation caveat for heated streams. This is the record's explicit assumption until 175.
   - Missing DWSIM density for a culture stream fails that stream's culture result visibly. No fallback density is used.
   - Results are stored with the run outcome under `culture[tag]` and become stale with the run.
6. **Operator UI (Process editor).**
   - The feed inspector gains a "Culture medium" section with an explicit "This feed carries a culture" toggle, unit-selectable inputs, and inline validation.
   - Computed stream inspectors show a read-only `Culture · Jarvis` section after Run, with the fidelity label and the pH reason when null. The canvas marks culture-carrying streams subtly (style, not a new color system).
   - Findings are listed and selectable as in 162.
   - Readable at 1280 and 1440 CSS px without horizontal overflow. No raw JSON in the normal view.
7. **Agent actions (166 vocabulary).** `set_value` admits single culture fields on feed streams (confirm tier, with units validated as above). The executor reads the current culture section, replaces that one field, and emits a full-section `set_stream_culture`, so the other fields are preserved. Setting an optional field to `null` makes it unknown. Clearing the whole section, or creating one on a feed without culture, requires biomass and salinity in the same action. The Process surface brief lists the selected feed's culture values and the refusal rules. Asked to put culture through a Flash or PFR, the agent explains the refusal and makes no change.

## Boundaries / non-goals

- No Jarvis-native unit, no mixed-engine loop, no biological reaction, growth, gas transfer, carbonate speciation, thermal effect or seawater property package (168/170/175).
- No change to DWSIM materialization, the closed compound list, property packages or the frozen 145 contracts.
- No new authority: computed culture is never editable. The 166 executor remains the only agent mutation path.
- FMU-neutral boundary (record §4.4): culture values stay a typed, unit-bearing mapping that a future adapter can export.

## Required evidence

- Focused backend tests:
  - schema and unit conversion per field, including pH bounds and the non-convertible pH;
  - `set_stream_culture` CAS, undo/restore, staleness, and an unchanged DWSIM materialization fingerprint for culture-only edits;
  - old-revision loading without culture;
  - every validation finding;
  - every pass-through rule, Splitter copy, Mixer weighting and pH agreement/placeholder/null;
  - mass ↔ mass-specific conversion at different densities, mole-basis Water checks, unknown-field propagation, zero-flow Mixer, missing/zero/non-finite density, and vapor or two-phase refusal;
  - each refusal (Flash, DistillationColumn, PFR, cycle);
  - balance residuals per field in their units (including O₂ and DIC);
  - registry owner exposure;
  - 166 `set_value` on culture fields and the brief contents.
- Frontend build and node contract tests for the Culture medium section, `Culture · Jarvis` results and owner badges.
- Exact-head **real DWSIM 10.2.9** run: a culture feed (Water carrier, biomass 1 g/L, N, P, DIC, pH 8.1, salinity 35 g/kg) and a water make-up feed → Mixer → Pump → Heater → Splitter → two products. Culture mass balances close per unit, and the pH is null after mixing with the make-up stream. A second case with a culture inlet to a Flash is refused before solve.
- Exact-head **real Chromium** acceptance at 1280 and 1440 CSS px:
  - configure the culture feed in the inspector;
  - Run, then inspect `Culture · Jarvis` on a product;
  - edit a culture value and confirm results are stale;
  - see the owner badges;
  - see the Flash refusal finding and select it;
  - in the Sidecar (local Gemma), "set the biomass of the culture feed to 1.5 g/L" yields an Apply card, and applying it creates the next revision.
- Screenshots inspected; no raw JSON visible.
