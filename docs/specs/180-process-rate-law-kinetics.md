# 180 — Process rate-law kinetics in DWSIM reactors

State: **accepted and ready**. Written under the maintainer directive of 2026-10-04 (post-170: spec 180 first, then 172) and reviewed against the current Process compiler and real DWSIM 10.2.9 probes on 2026-10-05. It builds on the merged [PBR engineering architecture record](../implementation/pbr-engineering-architecture-2026-10-02.md) §9 row 180 and §10.3, merged 158 (Process draft compiler), 168 (mixed-engine solve) and 170 (reactor-owned inspector pattern).

- **Hard dependencies:** 158 and 169 (STATUS row 180). 168 and 170 are merged and are relied on as current code, not as new dependencies.
- **Place in the roadmap:** the conventional-chemistry kinetics slice. It lets an operator give a DWSIM reactor a typed, reviewable rate law and see it evaluated by DWSIM, without free-text scripts.

## Fresh evidence

Surveys and probes (paths under `/home/thera/jarvis-control/work/`):

- `out/wpbr/a180.report.md` (survey at `8a1ef2f6`) and `out/w180/a180b.report.md` (delta at `ac569829`, after 168 and 170).
- `evidence/pbr/pDWSIM2` and `evidence/pbr/pDWSIM3` (real DWSIM 10.2.9 PythonScript kinetics), read back independently in `out/w180/p3.report.md`.
- `out/w180/coord_ref.md`: coordinator's independent references (constant density and variable volumetric flow).
- `evidence/pbr/pDWSIM4`: energy-mode and reaction-heat matrix in `q1a_raw.json` and `q1b_raw.json`; `q3_summary.json` independently checks a non-neutral temperature factor in isothermal CSTR and PFR. Variable-temperature PFR and robustness probes remain open.

Facts that shape the contract:

1. **No reaction editor exists.** `set_reactions` is absent from `frontend/src`. The PFR inspector only assigns existing reactions, and its empty state says "Define kinetic reactions under Thermo" (`ProcessDraftEditor.tsx:1044`). The only supported kinetics is native DWSIM Arrhenius power law on the PFR.
2. **DWSIM PythonScript kinetics works numerically on CSTR and PFR.** Script scope concentrations are kmol/m³ (the first evaluation saw `R1 = 6.34013 = C₀`); `r` is the base-reactant consumption rate in kmol/(m³·h); `T` is K and `P` is Pa; `import math` and `Amounts['<compound name>']` work (CSTR scope dumped; PFR source identical). Monod, Haldane and product-inhibited Monod agree with the coordinator's variable-volumetric-flow reference within 4.3e-5 relative on X and with constant-density hand values within 0.73 %. The constant-density gap is liquid density change, not a unit or sign error.
3. **Script failures are silent on the CSTR.** An exception, a missing `r`, a syntax error or a negative rate returns `ok=true`, `calculated=true` and the unreacted feed as product. DWSIM catches the exception and uses `r = Double.MinValue`; the message never reaches the MCP client. PFR failures surface as generic solver errors, except a negative rate, which returned `ok=true` after 252 s and ignored `timeout_s=30`.
4. **DWSIM per-reaction outputs are wrong under script kinetics.** CSTR `Extent`, `Rate` and reaction `Heat` are low by a factor V (the Python branch stores a per-volume rate where the Expression branch stores mol/s); the PFR `Reaction Extent` is low by 1000. Composition and conversion are correct.
5. **The CSTR needs an energy stream in every mode**, and its absence appears only at solve time (`R: No energy stream associated with the reactor.`).
6. **Generated IronPython is not sandboxed.** The script runs with CLR access and could write `/tmp` in the probe. Safety comes only from Jarvis authoring the text from closed templates.
7. **Mixed-solve light pass skips the native patch.** `mixed_runtime._light` builds segments through `plan()`/save/`read_back` without `_patch_native_xml`, so a reactor with reactions inside a 168 DWSIM segment cannot pass the light-pass comparison (devctx `L20261004221522-a45b`).
8. **The native patch writes one `<Reaction>` per assigning PFR** with the draft reaction id, so a reaction shared by two reactors would be written twice with one id.
9. **Determinism.** Ten PythonScript solves over two loads are bit-identical for CSTR and PFR. A CSTR solve takes about 0.02–0.1 s warm; a PFR solve about 0.15–0.6 s.

## Decision

**Kinetics belongs to the reactor.** An operator selects a PFR or CSTR and defines its reactions in the reactor's Kinetics tab: stoichiometry, a typed rate law with units, validity, provenance, and the DWSIM compilation state. Jarvis compiles each typed rate law from a closed template table to DWSIM PythonScript kinetics. DWSIM evaluates it. Jarvis verifies the solved result independently and refuses any result it cannot verify. Thermo stays property package and compounds.

Rulings:

1. **One kinetics authority.** The draft's `reactions` dictionary remains the only definition store. A reaction is authored, edited, assigned and removed only through a reactor's Kinetics tab or the equivalent agent action. A reaction assigned to two reactors is one definition, shown as shared in both inspectors; the compiler writes one native copy per reactor with distinct deterministic ids (fact 8).
2. **Closed rate-law forms** (all rates in kmol/(m³·h), base-reactant consumption basis, S = substrate concentration, clamped at zero):
   - `power_law_arrhenius`: today's native DWSIM Arrhenius power law (A, E, orders), unchanged.
   - `monod`: r = V_max · S / (K_S + S).
   - `haldane` (Andrews): r = V_max · S / (K_S + S + S²/K_I).
   - Optional **inhibition terms** on `monod` and `haldane`, at most three: non-competitive, factor K_i/(K_i + I); competitive, K_S → K_S·(1 + I/K_i). I is the concentration of a named reaction participant, clamped at zero.
   - Optional **temperature factor** on `monod` and `haldane`: exp(−(E_a/R)(1/T − 1/T_ref)). pDWSIM4 Q3 matched independent fixed-factor controls in isothermal CSTR and PFR at T ≠ T_ref. For PFR, this option is supported only in Isothermic mode; a variable-temperature axial profile remains unsupported. CSTR uses its uniform outlet temperature.

   The substrate is the base reactant. Inhibitors must be reaction participants, because only participants are present in the script scope. Reverse reactions, equilibrium, catalytic (per-mass) bases and user-written expressions are not offered.
3. **Liquid phase only for script kinetics.** Rate-law reactions use `ReactionPhase = Liquid`. A solved reactor outlet with a vapour fraction above 1e-9 fails with `KINETICS_TWO_PHASE_UNSUPPORTED`, because the concentration basis is then ambiguous.
4. **Energy modes.** CSTR script kinetics: Isothermic and OutletTemperature. CSTR Adiabatic is refused: pDWSIM4 Q1b measured a roughly 190 kW enthalpy residual with zero reported duty. PFR script kinetics: Isothermic and OutletTemperature; Adiabatic may be admitted after the temperature-factor and variable-temperature verification probes, because pDWSIM4 Q1b showed stream enthalpy closure within 0.001 kW for the tested PFR case. HeatExchange and NonIsothermalNonAdiabatic remain unsupported until proven. `power_law_arrhenius` reactions keep today's PFR modes.
5. **Reaction heat.** `ReactionHeat` stays 0, as today. Isothermal and specified-outlet-temperature reactor duty is checked against the inlet and outlet stream enthalpies. DWSIM's per-reaction Extent, Rate and Heat are never shown for rate-law reactions (fact 4); Jarvis derives its own values from stream flows. A PFR OutletTemperature result may differ from the requested value: pDWSIM4 Q1b consistently returned 338.05 K for 338.15 K requested.
6. **No silent results.** Every solved rate-law reactor passes a Jarvis verification after DWSIM returns (capability 5). A failed verification makes the run fail with a typed code and no current results for that reactor.
7. **Separate from 169 biology.** Reactor kinetics forms live in Process (`process_stack/kinetics.py`). 169's growth forms are biological factors for model cards and stay unchanged; `FORM_VERSION` is not bumped. 169's `kinetics_explanation()` text is updated to point at the reactor Kinetics tab.
8. **Verifiable reaction set.** A reactor using a new typed rate law has exactly one assigned reaction in this slice. The same reaction may be shared by multiple reactors. Legacy PFRs with multiple Arrhenius reactions remain supported. A larger typed reaction set requires a later contract for coupled rates, independently identifiable extents and a multicomponent PFR reference; silently reporting one rate or deriving individual extents from net stream flows is not acceptable.

## Accepted capability

### 1. Draft model

`KineticReaction` gains an optional `rate_law` (discriminated on `form`; `extra="forbid"` everywhere):

- **Absent:** today's Arrhenius reaction. `A_forward` and `E_forward` remain required. Stored documents load unchanged.
- **Present:** `A_forward`, `E_forward` and `orders` are forbidden. `phase` must be `Liquid`.
  - `monod {substrate, v_max, k_s, inhibitions[], temperature?}`
  - `haldane {substrate, v_max, k_s, k_i, inhibitions[], temperature?}`
  - `inhibitions[]`: at most 3 of `{kind: "noncompetitive" | "competitive", inhibitor, k_i}`; inhibitors distinct and different from the substrate.
  - `temperature`: `{activation_energy, reference_temperature}`.

Each reaction also gains:

- `provenance {kind: "literature" | "measurement" | "operator_estimate" | "synthetic", citation?, note?}`. Required for rate-law reactions; a literature kind requires a citation of at most 300 characters. Legacy Arrhenius reactions show "Provenance not recorded".
- `validity {temperature_min?, temperature_max?, substrate_max?}`, all optional typed quantities.

New quantity kinds:

- `reaction_rate`: SI mol/(m³·s); display kmol/(m³·h), mol/(m³·s), mol/(L·h).
- `molar_concentration` gains the display unit kmol/m³ (= mol/L).
- `molar_energy`: J/mol, kJ/mol.

Parameter domains: `v_max ≥ 0`; `k_s > 0`; `k_i > 0`; `activation_energy ≥ 0`; `reference_temperature > 0` K; every value finite. Nothing has a default. The registry projection publishes the form table (symbols, kinds, domains, equation trees) so the frontend draws its fields from it.

`SetReactions` and `SetUnitParams.reactions` stay as they are. One new DraftOp, `set_reactor_reaction {unit, reaction_id, reaction | null}`, upserts or deletes one reaction and assigns or unassigns it on that reactor in one revision (CAS, undo, stale like every DraftOp). Deleting a reaction still assigned to another reactor only unassigns it here.

### 2. CSTR unit

A registry unit `CSTR` (`dwsim_type` from the regenerated 158 manifest, native `Reactor_CSTR`, MCP result type `RCT_CSTR`), owner `dwsim`, `culture_rule = "refuse"`:

- one material inlet, outlets per the regenerated manifest, energy stream required by DWSIM;
- modes per ruling 4; parameters `volume` (> 0, required) and `outlet_temperature` in that mode;
- added to the culture list (`culture.py:437`), the manifest generator (`NATIVE_ALIASES` `RCT_CSTR`, modes, ports) and the palette. The dead `CSTR` entry in `TAG_PREFIX` becomes live.

A CSTR without an energy stream is a blocker before Run: `REACTOR_ENERGY_STREAM_MISSING`. PFR energy-stream validation follows the existing mode-specific rule; a valid legacy PFR without an energy stream must remain valid.

### 3. Compiler

- **Templates.** One fixed template per form and option. The generator takes only the form id, validated finite parameters in DWSIM units and compound names from the declared set. Numbers are rendered deterministically. Compounds are read as `Amounts['<name>']`, with names checked against the declared compound list and escaped or rejected so they cannot alter generated code. The template clamps concentrations at zero and assigns `r` once. Parameter ranges and evaluation guards must ensure that the rate remains finite and non-negative over the supported concentration and temperature domain, including multiplication and exponential overflow; a merely finite input float is insufficient. Invalid or out-of-domain inputs fail before DWSIM execution.
- **Native shape.** Per reactor and reaction: `ReactionKinetics = PythonScript`, `ScriptTitle = jarvis-rate-<tag>-<reaction_id>`, and one `ScriptItem` (`Linked = false`, IronPython) with the generated text. Native reaction ids are `<reaction_id>` when the reaction belongs to one reactor (keeping legacy cases byte-identical) and `<reaction_id>__<tag>` per reactor when shared.
- **One build path.** The full and the 168 light pass use the same patched build (patch, reload, re-assign reaction set). This repairs fact 7 for PFR, CSTR and DistillationColumn segments.
- **Read-back** parses the reaction set, kinetics fields and script text from the reloaded case and compares the script text byte for byte with a fresh render. A difference fails the run with `materialization_mismatch`.
- **Determinism.** Compiling the same draft twice gives identical bytes. Scripts carry no timestamps or revision numbers.
- **Never re-emitted:** scripts from imported or native cases. The compiler writes only Jarvis-generated scripts.

### 4. Validation before Run (`source: "jarvis"`)

| Code | Severity | Condition |
|---|---|---|
| `REACTION_SET_MISSING` | blocker | A PFR or CSTR has no assigned reaction (extended to CSTR). |
| `REACTOR_ENERGY_STREAM_MISSING` | blocker | A CSTR has no energy stream, or a PFR mode requires one under the existing rule. |
| `KINETICS_PARAMETER_MISSING` | blocker | A required rate-law parameter is absent; the finding names it. |
| `KINETICS_PARAMETER_DOMAIN` | blocker | A parameter is outside its domain. |
| `KINETICS_SUBSTRATE_INVALID` | blocker | The substrate is not the base reactant, or an inhibitor is not a participant. |
| `KINETICS_MODE_UNSUPPORTED` | blocker | The reactor mode is refused for rate-law reactions (ruling 4). |
| `KINETICS_TEMPERATURE_PROFILE_UNSUPPORTED` | blocker | A PFR with a temperature factor is not Isothermic. |
| `KINETICS_PROVENANCE_MISSING` | blocker | A rate-law reaction has no provenance, or a literature kind has no citation. |
| `KINETICS_COMPOUND_UNDECLARED` | blocker | A participant is not declared in Thermo. |
| `KINETICS_REACTION_SET_UNSUPPORTED` | blocker | A reactor with a new typed rate law has more than one assigned reaction. |
| `KINETICS_PARAMETER_UNVERIFIED` | info | Provenance kind is `operator_estimate` or `synthetic`. |

Apply-time refusals (unknown form, extra field, non-finite number, bad id) stay DraftOp errors with a named field, as today.

### 5. Verification after DWSIM solves

For each reactor with rate-law reactions, Jarvis reads the inlet and outlet streams and:

- **CSTR balance.** For each compound, the outlet molar flow equals the inlet plus Σ (ν/|ν_base|)·r_j(C_out, T_out)·V, because `r_j` is defined as base-reactant consumption and a base coefficient need not equal −1. Concentration uses the outlet compound flow and outlet liquid volumetric flow. Relative tolerance 1e-3 on the base reactant; failure → `KINETICS_VERIFICATION_FAILED`. This catches every silent CSTR failure in fact 3.
- **PFR reference.** For the single typed reaction, Jarvis integrates its stoichiometric flow vector along reactor volume with an independent ODE solver, taking Q linearly between the measured inlet and outlet volumetric flows as a function of reaction progress. Conversion within 2e-3 relative of DWSIM; failure → `KINETICS_VERIFICATION_FAILED`.
- `KINETICS_TWO_PHASE_UNSUPPORTED` (ruling 3).
- `KINETICS_OUTSIDE_VALIDITY` (warning): reactor temperature or inlet substrate concentration outside the declared validity.
- A PFR solve exceeding the bounded MCP client call timeout terminates the MCP subprocess and reports `JARVIS_SOLVE_TIMEOUT`; DWSIM's own `timeout_s` is not relied on (fact 3).

The verification code is a pure function with unit tests on synthetic stream data, including the probe's silent-failure shapes.

### 6. Results

Per reactor, grouped `Results · DWSIM` with a `Verified by Jarvis` chip:

- conversion of each reactant, outlet concentrations, residence time V/Q_out, duty and outlet temperature;
- for the single typed reaction: rate at outlet conditions (CSTR) or inlet and outlet rate (PFR), and extent derived from normalized stoichiometric flow change in kmol/h;
- the verification residual and tolerance;
- findings in plain words.

DWSIM's Extent, Rate and Heat per reaction are not shown for rate-law reactions.

### 7. Fingerprints and staleness

Rate-law fields, provenance and validity enter `expected()` and the 168 fingerprint, plus `KINETICS_VERSION = "180.1"` **only when a rate-law reaction exists**. Editing a rate law, an inhibition term or a temperature factor stales results; editing provenance or validity also stales (they change findings). Layout edits do not. Drafts without rate-law reactions keep their `expected()` and fingerprints byte-identical (golden test on the 158 PFR fixture).

### 8. Operator UI (mandatory)

**Reactor inspector.** Selecting a PFR or CSTR opens a tabbed inspector (the 170 pattern, keyboard `tablist`): **Setup** (the current generic inputs, mode, volume, energy), **Kinetics**, and **Results**.

**Kinetics tab:**

- A list of the reactor's reactions, each a card showing the equation (rendered from a typed tree through the existing allowlisted MathML renderer), the rate-law type, the base reactant, a shared-with note when assigned elsewhere, and its findings.
- **Add reaction** and **Edit**: name; stoichiometry rows (declared compound + coefficient); base reactant; rate-law type (`Power law (Arrhenius)`, `Monod`, `Haldane / Andrews`); typed parameters with unit selectors and inline domain errors; inhibition terms; optional temperature factor; validity; provenance with citation.
- **Assign existing** reaction from the draft, and **Remove** (unassign; delete when unassigned everywhere, with confirmation).
- An explanation paragraph per form in plain words (what V_max, K_S, K_I mean, the clamp, the base-reactant convention).
- **DWSIM compilation state:** "Evaluated by DWSIM · authored by Jarvis", the script title, a read-only generated-script preview (collapsed), and whether the last run compiled and verified it.
- **Unsupported conditions** listed explicitly: vapour phase, refused modes, reverse reactions, free-text expressions.

**Thermo** keeps property package and compounds. Its hint changes to "Reactions are defined on each reactor (select a PFR or CSTR)."

**Layout.** Readable at 1280 and 1440 CSS px with no horizontal overflow and no raw JSON.

### 9. Agent (166 vocabulary)

- `add_unit` / `insert_unit_after` / `connect` work for the CSTR through the registry.
- New action `set_reaction {unit, reaction_id, reaction}` with the typed reaction above. It is confirm tier and maps to one `set_reactor_reaction` DraftOp. Wired in the action models, `_process_ops`, the summary, the brief tail example, the Hermes MCP schema, the thread guard's op list and the frontend presentation.
- The brief lists each reactor's reactions (form, base reactant, verification status of the last run) within the 6000-character cap, tested with 35 objects and 12 reactions.
- The agent never edits provenance kinds to `literature` without a citation and never runs the flowsheet; Run stays operator-initiated.
- The explanation "Monod … DWSIM reactor rate laws arrive with 180" is replaced, with its test.

## Required evidence

**1. Backend tests.**

- Template golden texts per form and option; property test with adversarial compound names and parameter values (only whitelisted tokens and characters); `repr` edge values (5e-324, 1.7976931348623157e308, −0.0, 0.1).
- Model and DraftOp: refusals, upsert/delete/assign, CAS, undo, stale; shared reaction compiles to two native ids.
- Validation table rows each triggered and cleared.
- Verification function on synthetic data: pass, silent-failure shape (X ≈ 0 with positive rate), wrong-unit shape, two-phase shape.
- Fingerprint golden: legacy PFR draft byte-identical; rate-law edits stale.
- Mixed light pass with a reactor in a DWSIM segment (fact 7).
- 166: action, tier, brief cap.

**2. Independent reference.** `scripts/qualification/180/reference.py` computes the acceptance values without importing product code: constant-density closed forms and the variable-Q integration of `out/w180/coord_ref.md`.

**3. Exact-head real DWSIM 10.2.9** (`scripts/qualification/180/real_dwsim_acceptance.py`, in-process API, isolated data root, evidence JSON with head SHA and MCP sha256). Setup: Water 70 / EO 30 wt %, 1 kg/s, 328.15 K, 200 kPa, NRTL, V = 2 m³, `EO + H2O → EG`.

| Case | Reactor | Rate law | Reference X (variable Q) |
|---|---|---|---|
| A1 | CSTR | Monod V_max 5, K_S 2 | 0.28531 |
| A2 | CSTR, PFR | Monod K_S 1e-9 | 0.40789 |
| A3 | CSTR, PFR | Haldane K_I 10 | from reference.py |
| A4 | PFR | Monod | 0.29793 |
| A5 | CSTR, PFR | Monod + non-competitive EG, K_i 4 | from reference.py |
| A6 | CSTR, PFR | Monod + temperature factor, T ≠ T_ref | from reference.py; pDWSIM4 Q3 control |
| A7 | CSTR, PFR | Monod + competitive EG, K_i 4 | from reference.py |

- Acceptance: ≤ 2e-4 relative on X against the variable-Q reference and ≤ 1.5 % against the constant-density reference; Jarvis verification passes.
- Two CSTRs in series sharing one reaction; a mixed draft (Jarvis SpecifiedSeparator + CSTR) solves through 168.
- Determinism: compile twice identical; three solves identical.
- Legacy Arrhenius PFR fixture unchanged.
- Refusals: missing energy stream and refused mode are blocked before any DWSIM call.

**4. Exact-head real Chromium at 1280 and 1440 CSS px** (local Gemma for Sidecar steps).

1. Add a CSTR from the palette, connect feed, product and energy; see `REACTOR_ENERGY_STREAM_MISSING` clear.
2. Kinetics tab: add Monod (A1 values) with synthetic provenance; see the rendered equation, units, explanation and compilation state; enter K_S = 0 and see the inline error.
3. Run; Results show conversion matching A1 and the `Verified by Jarvis` chip.
4. Edit V_max; results go stale; Run again.
5. Switch the reaction to Haldane; add a non-competitive EG inhibition; Run.
6. PFR: assign the same reaction; see "shared with"; Run.
7. Sidecar: "use Monod kinetics with Vmax 5 and Ks 2 on the CSTR" yields an Apply card that creates the next revision; "why is the conversion low?" is answered with no Apply card.
8. Thermo shows only package and compounds plus the new hint.
9. Inspect the screenshots. No raw JSON or ids are visible.

A browser-proof plan `.github/browser-proof/plans/180-rate-law-kinetics.json` is checked in.

## Boundaries / non-goals

- **Out of scope:** free-text expressions or scripts; reverse and equilibrium reactions; heterogeneous or per-catalyst-mass bases; vapour or two-phase rate laws; reaction heat under script kinetics (ruling 5); refused energy modes (ruling 4); biomass, growth, light or culture in reactors (167/170); Gibbs, conversion and equilibrium reactors; dynamic reactors (172); parameter fitting.
- **Unchanged:** 169 forms and `FORM_VERSION`; 168 numerics and limits, apart from the shared build path; frozen 145 contracts; legacy Arrhenius cases byte-identical.
- **Never done:** executing or re-emitting scripts that Jarvis did not generate; showing DWSIM's script-kinetics Extent, Rate or Heat; shipping literature parameter values as defaults.
- **No SQL migration.** The draft `schema_version` stays 1, and old documents load unchanged.
