import { createElement, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { API_BASE_URL } from "../../api/client";
import {
  BioModelsError, createBioCard, createBioSet, duplicateBioSet, editBioValue,
  evaluateBioCard, listBioCards, listBioForms, listBioSets, reviewBioValue, verifyBioValue,
} from "../../api/bioModels";
import type { BioCard, BioForm, BioQuantity, BioSet, MathNode } from "../../api/bioModels";
import "./BiologyModelLibrary.css";

const allowedMathTags = new Set(["math", "mrow", "mi", "mn", "mo", "mtext", "msup", "msub", "mfrac", "msqrt"]);

type DisplaySymbol = { unit: string; validRange: string };
function rangeBounds(range: string, value: number): [number, number] | null {
  const interval = range.match(/^\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*(?:\)|\])$/);
  if (interval) return [Number(interval[1]), Number(interval[2])];
  if (/^(≥|>=|>|greater than)/.test(range)) return [0, Math.max(1, value * 2)];
  return null;
}

function MathTree({ node }: { node: MathNode }) {
  if (!allowedMathTags.has(node.tag)) return <span>{node.text ?? ""}</span>;
  const children: ReactNode = node.children?.map((child, index) => <MathTree key={`${child.tag}-${index}`} node={child} />) ?? node.text ?? "";
  return createElement(node.tag, node.tag === "math" ? { xmlns: "http://www.w3.org/1998/Math/MathML", display: "block" } : {}, children);
}

async function createLiteratureBasis(workspaceId: string, title: string, citation: string, value: number, unit: string) {
  const sourceResponse = await fetch(`${API_BASE_URL}/workspaces/${encodeURIComponent(workspaceId)}/literature/sources`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, source_kind: "paper", citation, state: "raw" }),
  });
  const source = await sourceResponse.json() as { id?: string; detail?: { message?: string } };
  if (!sourceResponse.ok || !source.id) throw new Error(source.detail?.message ?? "Could not create literature source");
  const entryResponse = await fetch(`${API_BASE_URL}/workspaces/${encodeURIComponent(workspaceId)}/literature/sources/${source.id}/entries`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entry_kind: "datum", value_number: value, unit, status: "raw", context_text: citation }),
  });
  const entry = await entryResponse.json() as { id?: string; detail?: { message?: string } };
  if (!entryResponse.ok || !entry.id) throw new Error(entry.detail?.message ?? "Could not create literature entry");
  return { object_type: "literature_entry", object_id: entry.id };
}

export default function BiologyModelLibrary({ workspaceId, onClose }: { workspaceId: string; onClose(): void }) {
  const [forms, setForms] = useState<BioForm[]>([]);
  const [sets, setSets] = useState<BioSet[]>([]);
  const [cards, setCards] = useState<BioCard[]>([]);
  const [setId, setSetId] = useState("");
  const [selectedForm, setSelectedForm] = useState("light.haldane");
  const [notice, setNotice] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceCitation, setSourceCitation] = useState("");
  const [muValue, setMuValue] = useState("");
  const [muUnit, setMuUnit] = useState("1/hour");
  const [cardLight, setCardLight] = useState("light.haldane");
  const [cardTemperature, setCardTemperature] = useState("temperature.ctmi");
  const [cardNutrient, setCardNutrient] = useState("nutrient.monod");
  const [cardCombination, setCardCombination] = useState("combine.liebig");
  const [cardLoss, setCardLoss] = useState("loss.first_order");
  const [nSource, setNSource] = useState<"NH3" | "HNO3">("NH3");
  const [preview, setPreview] = useState<{ mu_net: { value: number; unit: string }; breakdown: Record<string, { value: number; unit: string }> } | null>(null);
  const currentSet = sets.find((item) => item.id === setId) ?? null;
  const activeForm = forms.find((item) => item.id === selectedForm) ?? null;
  const symbols = useMemo(() => {
    const map = new Map<string, DisplaySymbol>();
    const selectedIds = new Set([
      cardLight, "optics.slab_response_average", cardTemperature, cardNutrient,
      cardCombination, cardLoss, "stoich.photoautotrophic",
    ]);
    const selectedSymbols = new Set<string>(["mu_max", "k_X", "a", "b", "c", "d", "w_ash"]);
    for (const form of forms) if (selectedIds.has(form.id)) for (const symbol of form.symbols) {
      if (symbol.symbol === "N-source") continue;
      if (symbol.symbol === "a,b,c,d") {
        for (const name of ["a", "b", "c", "d"]) {
          selectedSymbols.add(name);
          map.set(name, { unit: "1", validRange: "≥ 0" });
        }
      } else {
        selectedSymbols.add(symbol.symbol);
        map.set(symbol.symbol, { unit: symbol.unit, validRange: symbol.valid_range });
      }
    }
    map.set("mu_max", { unit: "h⁻¹", validRange: "> 0" });
    return [...selectedSymbols].flatMap((name) => {
      const definition = map.get(name);
      return definition ? [[name, definition] as const] : [];
    });
  }, [forms, cardLight, cardTemperature, cardNutrient, cardCombination, cardLoss]);

  const reload = async () => {
    const [nextForms, nextSets, nextCards] = await Promise.all([listBioForms(workspaceId), listBioSets(workspaceId), listBioCards(workspaceId)]);
    setForms(nextForms); setSets(nextSets); setCards(nextCards);
    setSetId((current) => current || nextSets[0]?.id || "");
  };
  useEffect(() => { void reload().catch((error: unknown) => setNotice(error instanceof Error ? error.message : "Could not load biology models")); }, [workspaceId]);

  const updateSet = (next: BioSet) => { setSets((items) => [next, ...items.filter((item) => item.id !== next.id)]); setSetId(next.id); };
  const act = async (operation: () => Promise<unknown>) => {
    setNotice("");
    try { await operation(); }
    catch (error) {
      if (error instanceof BioModelsError && error.status === 409) { await reload(); setNotice("This set changed elsewhere. Reloaded the latest revision; retry your action."); }
      else setNotice(error instanceof Error ? error.message : "Biology model action failed");
    }
  };

  const createCard = async () => {
    if (!currentSet || !(Number(muValue) > 0)) return;
    const card = await createBioCard(workspaceId, "Growth model", currentSet,
      { light: cardLight, optics: "optics.slab_response_average", temperature: cardTemperature,
        nutrients: [cardNutrient], combination: cardCombination, loss: cardLoss,
        stoichiometry: "stoich.photoautotrophic" }, { value: Number(muValue), unit: muUnit }, nSource);
    setCards((items) => [card, ...items]); setNotice("Model card created with pinned form versions.");
  };

  const saveMu = async () => {
    if (!currentSet) return;
    let basisRef: Record<string, unknown> | undefined;
    if (sourceTitle.trim()) basisRef = await createLiteratureBasis(workspaceId, sourceTitle.trim(), sourceCitation.trim(), Number(muValue), muUnit);
    const next = await editBioValue(workspaceId, currentSet, "mu_max", Number(muValue), muUnit, "1/hour", basisRef);
    updateSet(next);
    if (basisRef) setNotice("μ_max saved with a literature entry. Verify records the literature snapshot.");
  };

  const verify = async (symbol: string) => {
    if (!currentSet) return;
    const record = currentSet.values[symbol];
    let locatorConfirmed = false;
    if (record?.basis_ref?.object_type === "literature_source") {
      const kind = String(record.basis_ref.locator_kind ?? "locator");
      const locator = String(record.basis_ref.locator ?? "");
      locatorConfirmed = window.confirm(`Confirm the shown ${kind} locator: ${locator}`);
      if (!locatorConfirmed) return;
    }
    const next = await verifyBioValue(workspaceId, currentSet, symbol, locatorConfirmed); updateSet(next);
  };
  const editSymbol = async (symbol: string, unit: string) => {
    if (!currentSet) return;
    const previous = currentSet.values[symbol];
    const entered = window.prompt(`Value for ${symbol}`, previous ? String(previous.value) : "");
    if (entered === null || !entered.trim()) return;
    const parsed = Number(entered);
    if (!Number.isFinite(parsed)) { setNotice(`${symbol} must be a finite number.`); return; }
    const next = await editBioValue(workspaceId, currentSet, symbol, parsed, previous?.unit ?? unit, unit);
    updateSet(next);
  };
  const review = async (symbol: string) => {
    if (!currentSet) return;
    const reviewer = window.prompt("Reviewer name"); if (!reviewer) return;
    const note = window.prompt("Review note"); if (!note) return;
    const next = await reviewBioValue(workspaceId, currentSet, symbol, reviewer, note); updateSet(next);
  };

  return <section className="bio-library" aria-label="Biology model library" data-testid="biology-model-library">
    <header className="bio-library__header"><div><p className="eyebrow">Process · Biology</p><h2>Biology model library</h2></div><button type="button" onClick={onClose} aria-label="Close biology model library">Close</button></header>
    {notice && <p role="status" className="bio-library__notice">{notice}</p>}
    <div className="bio-library__layout">
      <section className="bio-library__forms" aria-label="Biological forms"><h3>Forms</h3>
        <label>Form<select aria-label="Biological form" value={selectedForm} onChange={(event) => setSelectedForm(event.target.value)}>{forms.map((form) => <option key={form.id} value={form.id}>{form.id}</option>)}</select></label>
        {activeForm && <article className="bio-form-card"><h4>{activeForm.id} <small>v{activeForm.version}</small></h4><div className="bio-equation" aria-label={`Equation: ${activeForm.equation_text}`}><MathTree node={activeForm.equation} /></div>
          <table><caption>Symbols and valid ranges</caption><thead><tr><th>Symbol</th><th>Meaning</th><th>Unit · range</th></tr></thead><tbody>{activeForm.symbols.map((symbol) => <tr key={symbol.symbol}><th>{symbol.symbol}</th><td>{symbol.meaning}</td><td>{symbol.unit} · {symbol.valid_range}</td></tr>)}</tbody></table>
          <p>{activeForm.applies_to}</p><p className="bio-library__metadata">Version {activeForm.version}{activeForm.citations.length ? ` · References: ${activeForm.citations.join(", ")}` : ""}</p>
        </article>}
      </section>
      <section className="bio-library__sets" aria-label="Parameter sets"><h3>Parameter sets</h3>
        <div className="bio-library__actions"><select aria-label="Parameter set" value={setId} onChange={(event) => setSetId(event.target.value)}><option value="">Select set</option>{sets.map((set) => <option key={set.id} value={set.id}>{set.name}</option>)}</select>
          <button type="button" onClick={() => void act(async () => updateSet(await createBioSet(workspaceId, "N. gaditana T1 — empty")))}>New empty template</button>
          <button type="button" disabled={!currentSet} onClick={() => currentSet && void act(async () => updateSet(await duplicateBioSet(workspaceId, currentSet)))}>Duplicate set</button>
        </div>
        {currentSet && <><p className="bio-library__metadata">Revision {currentSet.revision} · {currentSet.species || "species unspecified"} {currentSet.strain}</p>
          <table className="bio-parameter-table"><caption>Values and provenance</caption><thead><tr><th>Symbol</th><th>Value</th><th>Range</th><th>Unit</th><th>Source / state</th><th>Actions</th></tr></thead><tbody>
            {symbols.map(([symbol, definition]) => { const unit = definition.unit; const record = currentSet.values[symbol]; const basisId = typeof record?.basis_ref?.object_id === "string" ? record.basis_ref.object_id : null; const stateLabel = record?.display_state === "source_changed_since_verification" ? "source changed since verification" : record?.display_state ?? record?.state; const noBacking = record?.verification?.no_backing_document === true; const bounds = record ? rangeBounds(definition.validRange, record.value) : null; const offRange = record && bounds ? record.value < bounds[0] || record.value > bounds[1] || (definition.validRange.trim().startsWith(">") && record.value <= 0) || (definition.validRange.includes(")") && record.value === bounds[1]) : false; return <tr key={symbol}><th>{symbol}</th><td>{record ? record.value : "—"}</td><td>{record && bounds ? <><progress aria-label={`${symbol} valid range`} max={bounds[1]} value={Math.max(bounds[0], Math.min(bounds[1], record.value))} />{offRange && <strong role="alert">Off range</strong>}</> : definition.validRange}</td><td>{record?.unit ?? unit}</td><td>{basisId ? <><a href={`/memory/literature?entry_id=${encodeURIComponent(basisId)}`}>{String(stateLabel)}</a>{noBacking && <small> · no backing document</small>}</> : "operator assumption"}</td><td><button type="button" onClick={() => void act(() => editSymbol(symbol, unit))}>Edit</button>{record && <><button type="button" onClick={() => void act(() => verify(symbol))}>Verify</button><button type="button" disabled={record.state !== "source_verified"} onClick={() => void act(() => review(symbol))}>Review</button></>}</td></tr>; })}
          </tbody></table>
          <details><summary>Revision history ({currentSet.history.length})</summary><ol>{currentSet.history.map((revision, index) => <li key={String(revision.revision ?? index)}>{String(revision.action)} · {String(revision.revision)} · {String(revision.actor)}</li>)}</ol></details>
          <fieldset className="bio-parameter-editor"><legend>Edit μ_max</legend><label>Value<input aria-label="μ_max value" type="number" step="any" value={muValue} onChange={(event) => setMuValue(event.target.value)} /></label><label>Unit<select aria-label="μ_max unit" value={muUnit} onChange={(event) => setMuUnit(event.target.value)}><option>1/hour</option><option>1/day</option></select></label>
            <label>Literature source title<input aria-label="Literature source title" value={sourceTitle} onChange={(event) => setSourceTitle(event.target.value)} placeholder="Optional source for μ_max" /></label><label>Citation or locator context<input aria-label="Literature citation" value={sourceCitation} onChange={(event) => setSourceCitation(event.target.value)} /></label>
            <button type="button" disabled={!(Number(muValue) > 0)} onClick={() => void act(saveMu)}>Save μ_max revision</button></fieldset>
        </>}
      </section>
      <section className="bio-library__builder" aria-label="Model card builder"><h3>Growth model card</h3><p>Factor picker · selected forms are version pinned on save.</p>
        <label>Light<select aria-label="Light factor" value={cardLight} onChange={(event) => setCardLight(event.target.value)}><option value="light.monod">Monod</option><option value="light.haldane">Haldane</option><option value="light.steele">Steele</option><option value="light.eilers_peeters_steady">Eilers–Peeters steady</option></select></label><label>Temperature<select aria-label="Temperature factor" value={cardTemperature} onChange={(event) => setCardTemperature(event.target.value)}><option value="temperature.ctmi">CTMI</option><option value="temperature.isothermal">Isothermal</option><option value="temperature.arrhenius_ref">Arrhenius reference</option></select></label><label>Nutrient<select aria-label="Nutrient factor" value={cardNutrient} onChange={(event) => setCardNutrient(event.target.value)}><option value="nutrient.monod">Monod</option><option value="nutrient.droop">Droop</option></select></label><label>Nutrient combination<select aria-label="Nutrient combination" value={cardCombination} onChange={(event) => setCardCombination(event.target.value)}><option value="combine.liebig">Liebig minimum</option><option value="combine.multiplicative">Multiplicative</option></select></label><label>Loss<select aria-label="Loss factor" value={cardLoss} onChange={(event) => setCardLoss(event.target.value)}><option value="loss.first_order">First order</option><option value="loss.light_dark">Light / dark</option></select></label><label>Nitrogen source<select aria-label="Nitrogen source" value={nSource} onChange={(event) => setNSource(event.target.value as "NH3" | "HNO3")}><option value="NH3">NH₃</option><option value="HNO3">HNO₃</option></select></label>
        <button type="button" disabled={!currentSet || !(Number(muValue) > 0)} onClick={() => void act(createCard)}>Save model card</button>
        <ul>{cards.map((card) => <li key={card.id}><strong>{card.name}</strong> · {card.id.slice(0, 8)} · {Object.values(card.factors).map(String).join(" · ")} <button type="button" onClick={() => void act(async () => { const point: Record<string, BioQuantity> = { I0: { value: 800, unit: "umol/(m**2*s)" }, k_X: { value: 120, unit: "m**2/kg" }, X: { value: 0.7, unit: "kg/m3" }, L: { value: 0.05, unit: "m" }, T: { value: 298.15, unit: "K" }, S: { value: 0.1, unit: "kg/m3" } }; setPreview(await evaluateBioCard(workspaceId, card, point)); })}>Preview</button></li>)}</ul>
        {preview && <table><caption>Evaluation preview · μ = {preview.mu_net.value.toPrecision(5)} {preview.mu_net.unit}</caption><tbody>{Object.entries(preview.breakdown).map(([name, value]) => <tr key={name}><th>{name}</th><td>{value.value.toPrecision(5)} {value.unit}</td></tr>)}</tbody></table>}
      </section>
    </div>
  </section>;
}
