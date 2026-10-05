import { useEffect, useState } from "react";
import type { DraftObject, DraftOp, DraftReaction, DraftRun, Finding, ResultsState } from "../../api/processDraft";
import type { MathNode } from "../../api/bioModels";
import { MathTree } from "./BiologyModelLibrary";
import "./ReactorKinetics.css";

type Quantity = { value: number; unit: string };
type Inhibition = { kind: "noncompetitive" | "competitive"; inhibitor: string; k_i: Quantity };
type RateLaw = { form: "monod" | "haldane"; substrate: string; v_max: Quantity; k_s: Quantity; k_i?: Quantity;
  inhibitions: Inhibition[]; temperature?: { activation_energy: Quantity; reference_temperature: Quantity } };
type Provenance = { kind: "literature" | "measurement" | "operator_estimate" | "synthetic"; citation?: string; note?: string };
type Validity = { temperature_min?: Quantity; temperature_max?: Quantity; substrate_max?: Quantity };
type Reaction = DraftReaction & { rate_law?: RateLaw; provenance?: Provenance; validity?: Validity };
type Form = { id: string; name: string; stoich: Record<string, string>; orders: Record<string, string>; base: string;
  kind: "power_law_arrhenius" | "monod" | "haldane"; vMax: string; vMaxUnit: string; ks: string; ksUnit: string; ki: string; kiUnit: string;
  a: string; aUnit: string; e: string; eUnit: string; inhibitions: { kind: Inhibition["kind"]; inhibitor: string; ki: string; unit: string }[];
  useTemperature: boolean; activation: string; activationUnit: string; reference: string; referenceUnit: string;
  provenance: Provenance["kind"]; citation: string; note: string; tMin: string; tMax: string; tUnit: string; sMax: string; sUnit: string };
const RATE_UNITS = ["kmol/[m3.h]", "mol/[m3.s]", "mol/[L.h]"];
const ARRH_UNITS = ["kmol/[m3.h]"];
const CONC_UNITS = ["kmol/m3", "mol/m3"];
const ENERGY_UNITS = ["J/mol", "kJ/mol"];
const TEMP_UNITS = ["degC", "K"];
const numberText = (value: unknown) => typeof value === "number" ? String(value) : value && typeof value === "object" && "value" in value ? String((value as Quantity).value) : "";
const quantityUnit = (value: unknown, fallback: string) => value && typeof value === "object" && "unit" in value ? String((value as Quantity).unit) : fallback;
const emptyForm = (compounds: string[], reactions: Record<string, DraftReaction>): Form => {
  let n = 1; while (`R${n}` in reactions) n++;
  return { id: `R${n}`, name: "", stoich: {}, orders: {}, base: compounds[0] ?? "", kind: "monod", vMax: "", vMaxUnit: RATE_UNITS[0], ks: "", ksUnit: CONC_UNITS[0], ki: "", kiUnit: CONC_UNITS[0],
    a: "", aUnit: ARRH_UNITS[0], e: "", eUnit: ENERGY_UNITS[0], inhibitions: [], useTemperature: false, activation: "", activationUnit: ENERGY_UNITS[0], reference: "", referenceUnit: TEMP_UNITS[0],
    provenance: "synthetic", citation: "", note: "", tMin: "", tMax: "", tUnit: TEMP_UNITS[0], sMax: "", sUnit: CONC_UNITS[0] };
};
const fromReaction = (id: string, reaction: Reaction, compounds: string[], reactions: Record<string, DraftReaction>): Form => {
  const initial = emptyForm(compounds, reactions); const rate = reaction.rate_law;
  return { ...initial, id, name: reaction.name, stoich: Object.fromEntries(Object.entries(reaction.stoichiometry).map(([k, v]) => [k, String(v)])),
    orders: Object.fromEntries(Object.entries(reaction.orders ?? {}).map(([k, v]) => [k, String(v)])), base: reaction.base_reactant ?? "",
    kind: rate?.form ?? "power_law_arrhenius", vMax: numberText(rate?.v_max), vMaxUnit: quantityUnit(rate?.v_max, RATE_UNITS[0]),
    ks: numberText(rate?.k_s), ksUnit: quantityUnit(rate?.k_s, CONC_UNITS[0]), ki: numberText(rate?.k_i), kiUnit: quantityUnit(rate?.k_i, CONC_UNITS[0]),
    a: numberText(reaction.A_forward), aUnit: quantityUnit(reaction.A_forward, ARRH_UNITS[0]), e: numberText(reaction.E_forward), eUnit: quantityUnit(reaction.E_forward, ENERGY_UNITS[0]),
    inhibitions: (rate?.inhibitions ?? []).map((item) => ({ kind: item.kind, inhibitor: item.inhibitor, ki: numberText(item.k_i), unit: quantityUnit(item.k_i, CONC_UNITS[0]) })),
    useTemperature: Boolean(rate?.temperature), activation: numberText(rate?.temperature?.activation_energy), activationUnit: quantityUnit(rate?.temperature?.activation_energy, ENERGY_UNITS[0]),
    reference: numberText(rate?.temperature?.reference_temperature), referenceUnit: quantityUnit(rate?.temperature?.reference_temperature, TEMP_UNITS[0]),
    provenance: reaction.provenance?.kind ?? "synthetic", citation: reaction.provenance?.citation ?? "", note: reaction.provenance?.note ?? "",
    tMin: numberText(reaction.validity?.temperature_min), tMax: numberText(reaction.validity?.temperature_max), tUnit: quantityUnit(reaction.validity?.temperature_min ?? reaction.validity?.temperature_max, TEMP_UNITS[0]),
    sMax: numberText(reaction.validity?.substrate_max), sUnit: quantityUnit(reaction.validity?.substrate_max, CONC_UNITS[0]) };
};
const formLabel = (form: Form["kind"]) => ({ power_law_arrhenius: "Power law (Arrhenius)", monod: "Monod", haldane: "Haldane / Andrews" })[form];
const equation = (form: Form["kind"]): MathNode => ({ tag: "math", children: [{ tag: "mrow", children: [
  { tag: "mi", text: "r" }, { tag: "mo", text: "=" }, { tag: "mi", text: form === "power_law_arrhenius" ? "A exp(−E/RT) Π Cᵢⁿⁱ" : "Vₘₐₓ" },
  ...(form === "power_law_arrhenius" ? [] : [{ tag: "mo", text: "·" }, { tag: "mfrac", children: [{ tag: "mi", text: "S" }, { tag: "mrow", children: [
    { tag: "mi", text: "Kₛ" }, { tag: "mo", text: "+" }, { tag: "mi", text: "S" }, ...(form === "haldane" ? [{ tag: "mo", text: "+" }, { tag: "mi", text: "S²/Kᵢ" }] : []) ] }] }]) ] }] });
const quantity = (value: string, unit: string): Quantity => ({ value: Number(value), unit });
const numericError = (value: string, label: string, positive: boolean) => !value.trim() ? `${label} is required.` : !Number.isFinite(Number(value)) ? `${label} must be finite.` : Number(value) < 0 || (positive && Number(value) === 0) ? `${label} must be ${positive ? "positive" : "non-negative"}.` : "";
const temperatureError = (value: string, unit: string, label: string) => !value.trim() ? `${label} is required.` : !Number.isFinite(Number(value)) ? `${label} must be finite.` : Number(value) + (unit === "degC" ? 273.15 : 0) <= 0 ? `${label} must be above absolute zero.` : "";

export default function ReactorKinetics({ unit, objects, reactions, compounds, findings, results, run, script, apply, showError }: {
  unit: DraftObject; objects: DraftObject[]; reactions: Record<string, DraftReaction>; compounds: string[]; findings: Finding[];
  results: ResultsState; run: DraftRun | null; script?: { reaction_id: string; script_title: string; script_text: string }; apply(ops: DraftOp[]): Promise<unknown>; showError(message: string): void;
}) {
  const [form, setForm] = useState<Form | null>(null);
  const [pick, setPick] = useState("");
  const [removeId, setRemoveId] = useState<string | null>(null);
  useEffect(() => { setForm(null); setPick(""); setRemoveId(null); }, [unit.id]);
  const assigned = unit.reactions ?? [];
  const available = Object.entries(reactions).filter(([key]) => !assigned.includes(key));
  const update = (patch: Partial<Form>) => setForm((old) => old ? { ...old, ...patch } : old);
  const errors: Record<string, string> = {};
  if (form) {
    if (!/^[A-Za-z][A-Za-z0-9_-]{0,31}$/.test(form.id)) errors.id = "Use 1–32 letters, numbers, underscores or hyphens; start with a letter.";
    if (!form.name.trim()) errors.name = "Name is required.";
    if (form.name.length > 80) errors.name = "Name is too long.";
    if (form.note.length > 500) errors.note = "Note is too long.";
    const participants = Object.entries(form.stoich).filter(([, v]) => v.trim());
    if (participants.length < 2) errors.stoich = "Choose at least two participants.";
    if (participants.some(([, v]) => !Number.isFinite(Number(v)) || Number(v) === 0)) errors.stoich = "Coefficients must be finite and non-zero.";
    if (!participants.some(([k, v]) => k === form.base && Number(v) < 0)) errors.base = "Base reactant must have a negative coefficient.";
    if (form.kind === "power_law_arrhenius") {
      if (Object.values(form.orders).some((value) => value.trim() && (!Number.isFinite(Number(value)) || Number(value) < 0))) errors.orders = "Orders must be finite and non-negative.";
      errors.a = numericError(form.a, "A", false); errors.e = numericError(form.e, "E", false);
    } else {
      errors.vMax = numericError(form.vMax, "Vmax", false); errors.ks = numericError(form.ks, "Ks", true);
      if (form.kind === "haldane") errors.ki = numericError(form.ki, "Ki", true);
      if (!participants.some(([k]) => k === form.base)) errors.base = "Substrate must be the base reactant.";
      form.inhibitions.forEach((term, i) => {
        errors[`inhibitor${i}`] = !term.inhibitor || term.inhibitor === form.base || !participants.some(([k]) => k === term.inhibitor) ? "Inhibitor must be another reaction participant." : "";
        errors[`termKi${i}`] = numericError(term.ki, "Ki", true);
      });
      if (new Set(form.inhibitions.map((term) => term.inhibitor)).size !== form.inhibitions.length) errors.inhibitions = "Each inhibitor can appear once.";
      if (form.useTemperature) { errors.activation = numericError(form.activation, "Activation energy", false); errors.reference = temperatureError(form.reference, form.referenceUnit, "Reference temperature"); }
      if (form.provenance === "literature" && !form.citation.trim()) errors.citation = "A literature citation is required.";
    }
    if (form.tMin) errors.tMin = temperatureError(form.tMin, form.tUnit, "Minimum temperature");
    if (form.tMax) errors.tMax = temperatureError(form.tMax, form.tUnit, "Maximum temperature");
    if (form.sMax) errors.sMax = numericError(form.sMax, "Maximum substrate", true);
    if (form.tMin && form.tMax && Number(form.tMax) <= Number(form.tMin)) errors.tMax = "Maximum temperature must exceed the minimum.";
  }
  const valid = form && !Object.values(errors).some(Boolean);
  const field = (label: string, key: keyof Form, units: string[], errorKey = String(key)) => <label className="reactor-quantity"><span>{label}</span><span className="reactor-quantity__row"><input inputMode="decimal" aria-label={label} aria-invalid={Boolean(errors[errorKey])} value={String(form?.[key] ?? "")} onChange={(event) => update({ [key]: event.target.value })} /><select aria-label={`${label} unit`} value={String(form?.[(key === "tMin" || key === "tMax" ? "tUnit" : key === "sMax" ? "sUnit" : `${String(key)}Unit`) as keyof Form] ?? units[0])} onChange={(event) => update({ [key === "tMin" || key === "tMax" ? "tUnit" : key === "sMax" ? "sUnit" : `${String(key)}Unit`]: event.target.value })}>{units.map((item) => <option key={item} value={item}>{item}</option>)}</select></span>{errors[errorKey] && <small role="alert">{errors[errorKey]}</small>}</label>;
  const save = () => {
    if (!form || !valid) return;
    const stoichiometry = Object.fromEntries(Object.entries(form.stoich).filter(([, value]) => value.trim()).map(([key, value]) => [key, Number(value)]));
    const validity: Validity = {};
    if (form.tMin) validity.temperature_min = quantity(form.tMin, form.tUnit);
    if (form.tMax) validity.temperature_max = quantity(form.tMax, form.tUnit);
    if (form.sMax) validity.substrate_max = quantity(form.sMax, form.sUnit);
    const common = { name: form.name.trim(), stoichiometry, base_reactant: form.base, phase: form.kind === "power_law_arrhenius" ? "Mixture" : "Liquid", basis: "MolarConc", ...(Object.keys(validity).length ? { validity } : {}) };
    const reaction = form.kind === "power_law_arrhenius"
      ? { ...common, orders: Object.fromEntries(Object.entries(form.orders).filter(([, value]) => value.trim()).map(([key, value]) => [key, Number(value)])), A_forward: quantity(form.a, form.aUnit), E_forward: quantity(form.e, form.eUnit) }
      : { ...common, rate_law: { form: form.kind, substrate: form.base, v_max: quantity(form.vMax, form.vMaxUnit), k_s: quantity(form.ks, form.ksUnit),
          ...(form.kind === "haldane" ? { k_i: quantity(form.ki, form.kiUnit) } : {}),
          inhibitions: form.inhibitions.map((term) => ({ kind: term.kind, inhibitor: term.inhibitor, k_i: quantity(term.ki, term.unit) })),
          ...(form.useTemperature ? { temperature: { activation_energy: quantity(form.activation, form.activationUnit), reference_temperature: quantity(form.reference, form.referenceUnit) } } : {}) },
        provenance: { kind: form.provenance, ...(form.citation.trim() ? { citation: form.citation.trim() } : {}), ...(form.note.trim() ? { note: form.note.trim() } : {}) } };
    void apply([{ op: "set_reactor_reaction", unit: unit.id, reaction_id: form.id, reaction }]).then((applied) => { if (applied) setForm(null); }).catch((cause: unknown) => showError(cause instanceof Error ? cause.message : "Could not save reaction."));
  };
  const result = run?.units?.[unit.tag] as (NonNullable<DraftRun["units"]>[string] & { kinetics?: Record<string, unknown> }) | undefined;
  const kinetics = result?.kinetics;
  const verified = kinetics?.verified === true && results.state === "current";
  return <section className="reactor-kinetics" aria-label="Reactor kinetics">
    <p>Rates are positive consumption of the base reactant per reactor volume. DWSIM evaluates the generated rate; Jarvis verifies the material balance after Run.</p>
    {assigned.length === 0 && <p className="draft-hint">No reaction assigned. Add one or assign an existing reaction before Run.</p>}
    <div className="reactor-reaction-list">{assigned.map((reactionId) => {
      const reaction = reactions[reactionId] as Reaction | undefined; if (!reaction) return <p key={reactionId}>Assigned reaction unavailable.</p>;
      const formName = reaction.rate_law?.form ?? "power_law_arrhenius";
      const shared = objects.filter((other) => other.kind === "unit" && other.id !== unit.id && other.reactions?.includes(reactionId)).map((other) => other.tag);
      const related = findings.filter((finding) => finding.object === unit.tag && (finding.field?.includes(reactionId) || finding.code.startsWith("KINETICS_") || finding.code === "REACTION_SET_MISSING"));
      return <article key={reactionId} className="reactor-reaction-card"><h4>{reaction.name}</h4>
        <div className="reactor-equation" aria-label={`${formLabel(formName)} rate equation`}><MathTree node={equation(formName)} /></div>
        <p>{formLabel(formName)} · base reactant {reaction.base_reactant}</p>
        <p className="draft-hint">{Object.entries(reaction.stoichiometry).map(([name, coeff]) => `${coeff > 0 ? "+" : ""}${coeff} ${name}`).join(" · ")}</p>
        {shared.length > 0 && <p className="draft-hint">Shared with {shared.join(", ")}</p>}
        {related.map((finding, index) => <p className="reactor-finding" key={`${finding.code}-${index}`}>{finding.message}</p>)}
        <div className="reactor-actions"><button type="button" onClick={() => setForm(fromReaction(reactionId, reaction, compounds, reactions))}>Edit</button>
          <button type="button" onClick={() => setRemoveId(reactionId)}>Remove</button></div>
        {removeId === reactionId && <div className="reactor-confirm"><p>{shared.length ? "Remove from this reactor? The shared reaction remains on the other reactor." : "Remove this reaction? It will be deleted when no reactor uses it."}</p>
          <button type="button" onClick={() => { void apply([{ op: "set_reactor_reaction", unit: unit.id, reaction_id: reactionId, reaction: null }]); setRemoveId(null); }}>Confirm remove</button>
          <button type="button" onClick={() => setRemoveId(null)}>Cancel</button></div>}
      </article>;
    })}</div>
    <div className="reactor-actions"><button type="button" onClick={() => setForm(emptyForm(compounds, reactions))}>Add reaction</button>
      {available.length > 0 && <label>Assign existing <select aria-label="Assign existing reaction" value={pick} onChange={(event) => setPick(event.target.value)}><option value="">Choose…</option>{available.map(([key, reaction]) => <option key={key} value={key}>{reaction.name}</option>)}</select></label>}
      {pick && <button type="button" onClick={() => { void apply([{ op: "set_reactor_reaction", unit: unit.id, reaction_id: pick, reaction: reactions[pick] }]); setPick(""); }}>Assign</button>}</div>
    {form && <section className="reactor-editor" aria-label="Reaction editor"><h4>{form.id in reactions ? "Edit reaction" : "Add reaction"}</h4>
      <label>Reaction ID<input aria-label="Reaction ID" value={form.id} disabled={form.id in reactions} onChange={(event) => update({ id: event.target.value })} /></label>{errors.id && <small role="alert">{errors.id}</small>}
      <label>Name<input aria-label="Reaction name" value={form.name} onChange={(event) => update({ name: event.target.value })} /></label>{errors.name && <small role="alert">{errors.name}</small>}
      <fieldset><legend>Stoichiometry</legend><p className="draft-hint">Negative for reactants; positive for products.</p>
        {compounds.map((compound) => <label key={compound}>{compound}<input inputMode="decimal" aria-label={`${compound} coefficient`} placeholder="Not a participant" value={form.stoich[compound] ?? ""} onChange={(event) => update({ stoich: { ...form.stoich, [compound]: event.target.value } })} /></label>)}
        {errors.stoich && <small role="alert">{errors.stoich}</small>}
        <label>Base reactant<select aria-label="Base reactant" value={form.base} onChange={(event) => update({ base: event.target.value })}>{compounds.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>{errors.base && <small role="alert">{errors.base}</small>}
      </fieldset>
      <label>Rate-law type<select aria-label="Rate-law type" value={form.kind} onChange={(event) => update({ kind: event.target.value as Form["kind"] })}>{(["power_law_arrhenius", "monod", "haldane"] as const).map((item) => <option key={item} value={item}>{formLabel(item)}</option>)}</select></label>
      <div className="reactor-equation"><MathTree node={equation(form.kind)} /></div>
      {form.kind === "power_law_arrhenius" ? <><p className="draft-hint">A is the pre-exponential rate; E is activation energy. Orders apply to participant concentrations.</p>{field("A", "a", ARRH_UNITS)}{field("E", "e", ENERGY_UNITS)}
        <fieldset><legend>Orders</legend>{Object.entries(form.stoich).filter(([, value]) => value.trim()).map(([name]) => <label key={name}>{name}<input aria-label={`${name} order`} inputMode="decimal" value={form.orders[name] ?? ""} onChange={(event) => update({ orders: { ...form.orders, [name]: event.target.value } })} /></label>)}{errors.orders && <small role="alert">{errors.orders}</small>}</fieldset></>
        : <><p className="draft-hint">Vmax is the maximum base-reactant consumption rate; Ks is the concentration at half that rate. Negative concentrations are treated as zero.{form.kind === "haldane" ? " Ki describes inhibition by excess substrate." : ""}</p>
          {field("Vmax", "vMax", RATE_UNITS)}{field("Ks", "ks", CONC_UNITS)}{form.kind === "haldane" && field("Ki (substrate)", "ki", CONC_UNITS)}
          <fieldset><legend>Inhibition terms (up to 3)</legend>{form.inhibitions.map((term, index) => <div className="reactor-inhibition" key={index}><label>Kind<select aria-label={`Inhibition ${index + 1} kind`} value={term.kind} onChange={(event) => update({ inhibitions: form.inhibitions.map((row, i) => i === index ? { ...row, kind: event.target.value as Inhibition["kind"] } : row) })}><option value="noncompetitive">Non-competitive</option><option value="competitive">Competitive</option></select></label>
            <label>Inhibitor<select aria-label={`Inhibition ${index + 1} compound`} value={term.inhibitor} onChange={(event) => update({ inhibitions: form.inhibitions.map((row, i) => i === index ? { ...row, inhibitor: event.target.value } : row) })}><option value="">Choose…</option>{Object.entries(form.stoich).filter(([, value]) => value.trim()).map(([name]) => <option key={name} value={name}>{name}</option>)}</select></label>
            <label>Ki<input aria-label={`Inhibition ${index + 1} Ki`} inputMode="decimal" value={term.ki} onChange={(event) => update({ inhibitions: form.inhibitions.map((row, i) => i === index ? { ...row, ki: event.target.value } : row) })} /><select aria-label={`Inhibition ${index + 1} Ki unit`} value={term.unit} onChange={(event) => update({ inhibitions: form.inhibitions.map((row, i) => i === index ? { ...row, unit: event.target.value } : row) })}>{CONC_UNITS.map((u) => <option key={u}>{u}</option>)}</select></label>
            <button type="button" onClick={() => update({ inhibitions: form.inhibitions.filter((_, i) => i !== index) })}>Remove inhibition</button>
            {(errors[`inhibitor${index}`] || errors[`termKi${index}`]) && <small role="alert">{errors[`inhibitor${index}`] || errors[`termKi${index}`]}</small>}</div>)}
            {form.inhibitions.length < 3 && <button type="button" onClick={() => update({ inhibitions: [...form.inhibitions, { kind: "noncompetitive", inhibitor: "", ki: "", unit: CONC_UNITS[0] }] })}>Add inhibition</button>}{errors.inhibitions && <small role="alert">{errors.inhibitions}</small>}</fieldset>
          <label className="reactor-check"><input type="checkbox" checked={form.useTemperature} onChange={(event) => update({ useTemperature: event.target.checked })} />Temperature factor</label>
          {form.useTemperature && <>{field("Activation energy", "activation", ENERGY_UNITS)}{field("Reference temperature", "reference", TEMP_UNITS)}</>}
          <fieldset><legend>Provenance</legend><label>Source kind<select aria-label="Provenance kind" value={form.provenance} onChange={(event) => update({ provenance: event.target.value as Provenance["kind"] })}><option value="synthetic">Synthetic</option><option value="operator_estimate">Operator estimate</option><option value="measurement">Measurement</option><option value="literature">Literature</option></select></label>
            <label>Citation<input aria-label="Citation" value={form.citation} maxLength={300} onChange={(event) => update({ citation: event.target.value })} /></label>{errors.citation && <small role="alert">{errors.citation}</small>}
            <label>Note<textarea aria-label="Provenance note" maxLength={500} value={form.note} onChange={(event) => update({ note: event.target.value })} /></label>{errors.note && <small role="alert">{errors.note}</small>}</fieldset></>}
      <fieldset><legend>Validity (optional)</legend>{field("Minimum temperature", "tMin", TEMP_UNITS)}{field("Maximum temperature", "tMax", TEMP_UNITS)}{field("Maximum substrate", "sMax", CONC_UNITS)}</fieldset>
      <div className="reactor-actions"><button type="button" disabled={!valid} onClick={save}>Apply reaction</button><button type="button" onClick={() => setForm(null)}>Cancel</button></div>
    </section>}
    <section className="reactor-compilation"><h4>DWSIM compilation</h4><p>Evaluated by DWSIM · authored by Jarvis</p>
      {script && <p>Script title: <code>{script.script_title}</code></p>}
      <p>{verified ? "Compiled and verified on the current Run" : results.state === "stale" ? "Previous Run is stale; run again to verify edits" : "Compilation and verification available after Run"}</p>
      {assigned.some((reactionId) => Boolean((reactions[reactionId] as Reaction | undefined)?.rate_law)) && <details><summary>Generated script preview</summary>
        {typeof script?.script_text === "string" ? <pre>{script.script_text}</pre> : <p className="draft-hint">Preview available after the reaction is saved.</p>}
      </details>}
      <p className="draft-hint">Unsupported: vapour or two-phase rate laws, reverse reactions, free-text expressions, and refused energy modes.</p></section>
  </section>;
}
