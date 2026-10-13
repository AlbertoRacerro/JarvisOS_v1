import { useEffect, useMemo, useState } from "react";
import type { Navigate } from "../app/AppLink";
import DerivedDocumentation from "../components/studio/DerivedDocumentation";
import PythonEditor from "../components/studio/PythonEditor";
import { canPublishStudioDraft } from "./studioState";
import {
  createStudioModel, getStudioModel, getStudioRuntimeStatus, listStudioCategories, listStudioLibrary, listStudioModels,
  publishStudioModel, reviseStudioModel, saveStudioModel, testStudioModel,
  type StudioCase, type StudioCategory, type StudioLibraryEntry, type StudioModel, type StudioRuntimeStatus, type StudioVariable
} from "../api/studio";
import "./studio.css";

type Tab = "contract" | "code" | "documentation" | "tests" | "versions";
const blankVariable = (): StudioVariable => ({ name: "", label: "", unit: "dimensionless", description: "" });
const defaultCategories: StudioCategory[] = [
  { id: "calculation", label: "Calculation / correlation", available: true },
  { id: "steady_unit", label: "Steady unit operation", available: false, reason: "Process Studio binding is planned for a later slice." },
  { id: "dynamic", label: "Dynamic model", available: false, reason: "Time integration is not available in this Studio slice." },
  { id: "procedure", label: "Procedure", available: false, reason: "Procedure authoring is planned for a later slice." },
  { id: "geometry", label: "Geometry", available: false, reason: "CAD as code is planned for a later slice." },
  { id: "optimization", label: "Optimization", available: false, reason: "Optimization execution is not yet available." },
  { id: "cfd_fem", label: "CFD / FEM", available: false, reason: "CFD and FEM execution is not yet available." }
];
function VariableForm({ title, rows, onChange }: { title: string; rows: StudioVariable[]; onChange(rows: StudioVariable[]): void }) {
  const update = (index: number, patch: Partial<StudioVariable>) => onChange(rows.map((row, i) => i === index ? { ...row, ...patch } : row));
  return <fieldset className="studio-variables"><legend>{title}</legend>
    {rows.map((row, index) => <div className="studio-variable" key={index}>
      <label>Python name<input required pattern="[A-Za-z_][A-Za-z0-9_]*" value={row.name} onChange={(event) => update(index, { name: event.target.value })} placeholder="e.g. pipe_length" /></label>
      <label>Label<input required value={row.label} onChange={(event) => update(index, { label: event.target.value })} placeholder="e.g. Pipe length" /></label>
      <label>Unit<input required value={row.unit} onChange={(event) => update(index, { unit: event.target.value })} placeholder="e.g. meter" /></label>
      <label>Description<input value={row.description} onChange={(event) => update(index, { description: event.target.value })} placeholder="Meaning and basis" /></label>
      <label>Minimum<input type="number" step="any" value={row.min ?? ""} onChange={(event) => update(index, { min: event.target.value === "" ? null : Number(event.target.value) })} /></label>
      <label>Maximum<input type="number" step="any" value={row.max ?? ""} onChange={(event) => update(index, { max: event.target.value === "" ? null : Number(event.target.value) })} /></label>
      <button type="button" onClick={() => onChange(rows.filter((_, i) => i !== index))} disabled={rows.length === 1}>Remove</button>
    </div>)}
    <button type="button" onClick={() => onChange([...rows, blankVariable()])}>+ Add {title.toLowerCase().slice(0, -1)}</button>
  </fieldset>;
}
function NumberMapEditor({ title, variables, values, onChange }: { title: string; variables: StudioVariable[]; values: Record<string, number>; onChange(values: Record<string, number>): void }) {
  return <div className="studio-number-map"><strong>{title}</strong>{variables.map((variable) => <label key={variable.name}>{variable.label || variable.name} [{variable.unit}]<input type="number" step="any" value={values[variable.name] ?? ""} onChange={(event) => {
    const next = { ...values }; if (event.target.value === "") delete next[variable.name]; else next[variable.name] = Number(event.target.value); onChange(next);
  }} /></label>)}</div>;
}
const emptyCase = (): StudioCase => ({ inputs: {}, expected_outputs: {}, tolerance: 1e-6 });
export default function Studio({ workspaceId, navigate }: { workspaceId: string | null; navigate: Navigate }) {
  const [models, setModels] = useState<StudioModel[]>([]);
  const [library, setLibrary] = useState<StudioLibraryEntry[]>([]);
  const [categories, setCategories] = useState<StudioCategory[]>(defaultCategories);
  const [runtime, setRuntime] = useState<StudioRuntimeStatus | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [model, setModel] = useState<StudioModel | null>(null);
  const [tab, setTab] = useState<Tab>("contract");
  const [wizard, setWizard] = useState(false);
  const [custom, setCustom] = useState(false);
  const [name, setName] = useState(""); const [question, setQuestion] = useState("");
  const [inputs, setInputs] = useState<StudioVariable[]>([blankVariable()]); const [outputs, setOutputs] = useState<StudioVariable[]>([blankVariable()]);
  const [source, setSource] = useState(""); const [annotations, setAnnotations] = useState(""); const [assumptions, setAssumptions] = useState("");
  const [cases, setCases] = useState<StudioCase[]>([]);
  const [busy, setBusy] = useState(false); const [error, setError] = useState<string | null>(null); const [notice, setNotice] = useState<string | null>(null);
  const sourceDirty = Boolean(model && source !== model.source);
  const contractDirty = Boolean(model && (name !== model.name || question !== model.engineering_question || JSON.stringify(inputs) !== JSON.stringify(model.inputs) || JSON.stringify(outputs) !== JSON.stringify(model.outputs)));
  const textDirty = Boolean(model && (annotations !== model.annotations || assumptions !== model.assumptions));
  const draftDirty = sourceDirty || contractDirty || textDirty;
  const runtimeReady = Boolean(runtime?.enabled && runtime?.available);
  const locked = model?.status === "published";
  const newest = useMemo(() => model?.versions[model.versions.length - 1] ?? null, [model]);

  const adopt = (next: StudioModel) => { setModel(next); setSelectedId(next.id); setName(next.name); setQuestion(next.engineering_question); setInputs(next.inputs); setOutputs(next.outputs); setSource(next.source); setAnnotations(next.annotations ?? ""); setAssumptions(next.assumptions ?? ""); setCases(next.test_cases ?? []); };
  const refreshLists = (ws: string) => Promise.all([listStudioModels(ws), listStudioLibrary(ws)]).then(([nextModels, nextLibrary]) => { setModels(nextModels); setLibrary(nextLibrary); });
  useEffect(() => {
    let alive = true; setModel(null); setSelectedId(null); setError(null);
    void Promise.all([listStudioCategories(), getStudioRuntimeStatus()]).then(([nextCategories, nextRuntime]) => { if (alive) { setCategories(nextCategories); setRuntime(nextRuntime); } }).catch((cause: Error) => { if (alive) setError(cause.message); });
    if (workspaceId) void Promise.all([listStudioModels(workspaceId), listStudioLibrary(workspaceId)]).then(([nextModels, nextLibrary]) => { if (alive) { setModels(nextModels); setLibrary(nextLibrary); } }).catch((cause: Error) => { if (alive) setError(cause.message); });
    return () => { alive = false; };
  }, [workspaceId]);
  const perform = async (action: () => Promise<void>) => { setBusy(true); setError(null); setNotice(null); try { await action(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Studio action failed"); } finally { setBusy(false); } };
  const open = (id: string) => { if (!workspaceId) return; void perform(async () => { adopt(await getStudioModel(workspaceId, id)); setWizard(false); setTab("contract"); }); };
  const create = (event: React.FormEvent) => { event.preventDefault(); if (!workspaceId) return; void perform(async () => {
    const next = await createStudioModel(workspaceId, { name: name.trim(), engineering_question: question.trim(), inputs, outputs });
    adopt(next); await refreshLists(workspaceId); setWizard(false); setTab("code"); setNotice("Draft created. Edit the Python scaffold, then save and test it.");
  }); };
  const save = () => { if (!workspaceId || !model) return; void perform(async () => { const next = await saveStudioModel(workspaceId, model.id, { name, engineering_question: question, inputs, outputs, source, annotations, assumptions }); adopt(next); await refreshLists(workspaceId); setNotice("Draft saved. Documentation reflects the saved source."); }); };
  const test = () => { if (!workspaceId || !model) return; void perform(async () => { await testStudioModel(workspaceId, model.id, cases); adopt(await getStudioModel(workspaceId, model.id)); setNotice("Test report recorded against the current source and contract."); }); };
  const publish = () => { if (!workspaceId || !model) return; void perform(async () => { const version = await publishStudioModel(workspaceId, model.id); adopt(await getStudioModel(workspaceId, model.id)); await refreshLists(workspaceId); setTab("versions"); setNotice(`Published ${version.version_label}. Scientific status: unqualified.`); }); };
  const revise = () => { if (!workspaceId || !model) return; void perform(async () => { adopt(await reviseStudioModel(workspaceId, model.id)); await refreshLists(workspaceId); setTab("code"); setNotice("New draft opened from the latest published version."); }); };
  const updateCase = (index: number, patch: Partial<StudioCase>) => setCases(cases.map((item, i) => i === index ? { ...item, ...patch } : item));

  return <main className="studio" aria-labelledby="studio-title">
    <header className="studio-header"><div><p className="eyebrow">Design · Engineering Studio</p><h1 id="studio-title">Model authoring</h1><p>Create, test and publish reusable engineering calculations.</p></div><button type="button" onClick={() => { setWizard(true); setModel(null); setSelectedId(null); setName(""); setQuestion(""); setInputs([blankVariable()]); setOutputs([blankVariable()]); setCustom(false); }}>+ New model</button></header>
    {!runtimeReady && runtime ? <p className="studio-warning" role="status">Studio execution unavailable: {runtime.reason || (runtime.enabled ? "Runtime unavailable" : "Runtime disabled")}. To enable it, start the backend with JARVISOS_STUDIO_USER_CODE_ENABLED=1 on a Linux or WSL2 host with bubblewrap installed. Test and Run stay refused until then.</p> : null}
    {error ? <p className="studio-error" role="alert">{error}</p> : null}{notice ? <p className="studio-notice" role="status">{notice}</p> : null}
    <div className="studio-layout"><aside className="studio-library"><h2>Library</h2><p>Published versions are recorded and scientifically unqualified.</p>
      {library.length ? library.map((item) => <article key={item.id}><button type="button" onClick={() => open(item.model_spec_id)}><strong>{item.name}</strong><span>{item.version_label} · unqualified</span></button><button type="button" onClick={() => navigate(`/design/process?modelVersionId=${encodeURIComponent(item.id)}`)}>Select for calculation</button></article>) : <p>No published versions yet.</p>}
      <h2>Drafts & models</h2>{models.map((item) => <button className={selectedId === item.id ? "is-selected" : ""} type="button" key={item.id} onClick={() => open(item.id)}><strong>{item.name}</strong><span>{item.versions.length} published version{item.versions.length === 1 ? "" : "s"}</span></button>)}
    </aside><section className="studio-workspace">
      {wizard ? <form onSubmit={create}><h2>New calculation</h2><p>Choose a path. The calculation contract and Python source remain editable in the workspace.</p>
        <div className="studio-paths"><button type="button" aria-pressed={!custom} onClick={() => setCustom(false)}>Guided calculation</button><button type="button" aria-pressed={custom} onClick={() => setCustom(true)}>Custom · no preset</button></div>
        <label>Model name<input required value={name} onChange={(event) => setName(event.target.value)} placeholder="Pipe pressure-loss correlation" /></label>
        <label>Engineering question<textarea required value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What should this model calculate?" /></label>
        <VariableForm title="Inputs" rows={inputs} onChange={setInputs} /><VariableForm title="Outputs" rows={outputs} onChange={setOutputs} />
        <button type="submit" disabled={busy}>Create draft and Python scaffold</button>
        <h3>Other model categories</h3><div className="studio-categories">{categories.filter((category) => category.id !== "calculation").map((category) => <div key={category.id}><button type="button" disabled={!category.available} title={category.reason ?? undefined}>{category.label}</button><small>{category.reason || "Available"}</small></div>)}</div>
      </form> : model ? <><div className="studio-model-head"><div><h2>{model.name}</h2><p>{model.engineering_question}</p><small>Model ID {model.id} · {model.versions.length} published · scientifically unqualified</small></div><div className="studio-actions"><button type="button" disabled={busy || locked || !draftDirty} onClick={save}>Save Draft</button><button type="button" disabled={busy || locked || draftDirty || !runtimeReady || cases.length === 0} onClick={test}>Test</button><button type="button" disabled={busy || locked || !canPublishStudioDraft(model, cases, draftDirty, runtimeReady)} onClick={publish}>Publish</button>{newest ? <button type="button" disabled={busy || draftDirty} onClick={revise}>Revise</button> : null}</div></div>
        {locked ? <p className="studio-notice" role="status">{newest?.version_label} is published and immutable. Revise opens a new draft from it; existing runs keep their version.</p> : null}
        {draftDirty && !locked ? <p className="studio-warning">Unsaved edits. Save Draft to refresh documentation and test the exact source.</p> : null}
        <nav className="studio-tabs" aria-label="Model workspace">{(["contract", "code", "documentation", "tests", "versions"] as Tab[]).map((item) => <button key={item} type="button" aria-current={tab === item ? "page" : undefined} onClick={() => setTab(item)}>{item[0].toUpperCase() + item.slice(1)}</button>)}</nav>
        {tab === "contract" ? <fieldset className="studio-panel" disabled={locked}><label>Model name<input value={name} onChange={(event) => setName(event.target.value)} /></label><label>Engineering question<textarea value={question} onChange={(event) => setQuestion(event.target.value)} /></label><VariableForm title="Inputs" rows={inputs} onChange={setInputs} /><VariableForm title="Outputs" rows={outputs} onChange={setOutputs} /></fieldset> : null}
        {tab === "code" ? <div className="studio-panel"><p>Python is the executable source. The editor is always available for this draft.</p><PythonEditor value={source} onChange={setSource} disabled={locked} /><small>Source SHA-256: {model.source_sha256}</small></div> : null}
        {tab === "documentation" ? <div className="studio-panel"><h3>Derived equations</h3><p>Read-only equations are parsed from saved Python; source is never executed to render them.</p><DerivedDocumentation derived={model.documentation.derived} />
          <h3>Contract tables</h3><div className="studio-contract-tables"><section><h4>Inputs</h4>{model.documentation?.inputs.map((row) => <p key={row.name}>{row.label} ({row.name}) [{row.unit}] · {row.description}</p>)}</section><section><h4>Outputs</h4>{model.documentation?.outputs.map((row) => <p key={row.name}>{row.label} ({row.name}) [{row.unit}] · {row.description}</p>)}</section></div>
          {model.annotations_stale || sourceDirty ? <p className="studio-warning">Annotations were written against an older source hash.</p> : null}<label>Annotations<textarea disabled={locked} value={annotations} onChange={(event) => setAnnotations(event.target.value)} /></label><label>Assumptions<textarea disabled={locked} value={assumptions} onChange={(event) => setAssumptions(event.target.value)} /></label></div> : null}
        {tab === "tests" ? <fieldset className="studio-panel" disabled={locked}><h3>Test cases</h3><p>Enter values in declared units. Expected outputs are optional; each test checks that every output exists and is finite.</p>{cases.map((item, index) => <fieldset className="studio-case" key={index}><legend>Case {index + 1}</legend><NumberMapEditor title="Inputs" variables={model.inputs} values={item.inputs} onChange={(values) => updateCase(index, { inputs: values })} /><NumberMapEditor title="Expected outputs (optional)" variables={model.outputs} values={item.expected_outputs ?? {}} onChange={(values) => updateCase(index, { expected_outputs: values })} /><label>Tolerance<input type="number" min="0" step="any" value={item.tolerance ?? 1e-6} onChange={(event) => updateCase(index, { tolerance: Number(event.target.value) })} /></label><button type="button" onClick={() => setCases(cases.filter((_, i) => i !== index))}>Remove case</button></fieldset>)}<button type="button" onClick={() => setCases([...cases, emptyCase()])}>+ Add test case</button><button type="button" disabled={busy || locked || draftDirty || !runtimeReady || !cases.length} onClick={test}>Run Test</button>
          {model.last_test_report ? <section className="studio-report"><h4>{model.last_test_report.passed ? "Passing report" : "Failed report"}</h4><p>Source {model.last_test_report.source_sha256.slice(0, 12)} · Contract {model.last_test_report.contract_sha256.slice(0, 12)}</p>{model.last_test_report.cases.map((result, i) => <div key={i}><strong>Case {i + 1}: {result.passed ? "Pass" : "Fail"}</strong> · {result.classification}{result.errors.length ? <ul>{result.errors.map((message, n) => <li key={n}>{message}</li>)}</ul> : null}{result.outputs ? <pre>{JSON.stringify(result.outputs, null, 2)}</pre> : null}</div>)}</section> : null}</fieldset> : null}
        {tab === "versions" ? <div className="studio-panel"><h3>Published versions</h3><p>Published versions are immutable and scientifically unqualified. Revise creates a new draft.</p>{model.versions.length ? model.versions.map((version) => <article key={version.id}><strong>{version.version_label}</strong><span> · {new Date(version.created_at).toLocaleString()}</span><p>Source {version.source_sha256.slice(0, 12)} · Contract {version.contract_sha256.slice(0, 12)}</p><button type="button" onClick={() => navigate(`/design/process?modelVersionId=${encodeURIComponent(version.id)}`)}>Select for calculation</button></article>) : <p>No published versions.</p>}</div> : null}
      </> : <div className="studio-empty"><h2>Start with a calculation</h2><p>Create an input/output contract, edit its Python scaffold, test and publish a reusable version.</p><button type="button" onClick={() => setWizard(true)}>Start wizard</button></div>}
    </section></div>
  </main>;
}
