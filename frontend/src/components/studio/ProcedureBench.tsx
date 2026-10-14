import { useCallback, useEffect, useMemo, useState } from "react";
import { StudioApiError, type StudioModel } from "../../api/studio";
import {
  applyProcedure, createBenchScenario, getProcedureResults, getRunManifest, getRunSeries, listBenchDrafts, listEnvironmentProfiles, listProcedureLinks, listProcedureRuns, runProcedureLink, updateProcedureLink,
  type BenchDraft, type EnvironmentProfileHead, type ProcedureLink, type RunResults, type RunRow, type SeriesResponse
} from "../../api/studioProcedure";
import { Refusal, SimulationNotice } from "./ProcedureAuthoring";
import { balanceStatus, boundHint, canRun, chartPaths, fmt, KPI_COLUMNS, linkBadges, parameterValuesIssues, updateLabel } from "./procedureLogic";

// Spec 191 minimal test bench: pick a draft and scenario, Apply a published version, Run, read the event log, balances and series.
type Failure = { code: string | null; message: string } | null;
const OVERWRITE_CODES = new Set(["studio_procedure_link_modified", "studio_procedure_schedule_exists", "studio_procedure_scenario_schedule_conflict"]);
const COLORS = ["#246b45", "#24729b", "#c56825", "#7256a3", "#9a4a55"];
const failure = (cause: unknown): Failure => cause instanceof StudioApiError ? { code: cause.code, message: cause.message } : { code: null, message: cause instanceof Error ? cause.message : "Request failed" };

function SeriesChart({ series, channels }: { series: SeriesResponse; channels: string[] }) {
  const t = series.channels.t_s ?? [];
  const paths = chartPaths(t, channels.filter((name) => series.channels[name]).map((name) => ({ name, values: series.channels[name] })), 640, 160);
  if (!paths.length) return <p>No series points to plot.</p>;
  return <figure className="studio-chart"><svg viewBox="0 0 640 160" role="img" aria-label={`Series ${channels.join(", ")}`} preserveAspectRatio="none">
    {paths.map((path, index) => <path key={path.name} d={path.d} fill="none" stroke={COLORS[index % COLORS.length]} strokeWidth="1.5" vectorEffect="non-scaling-stroke" />)}</svg>
    <figcaption>{paths.map((path, index) => <span key={path.name} style={{ color: COLORS[index % COLORS.length] }}>{path.name} </span>)}· {series.returned_points} of {series.total_points} points, {fmt((t[t.length - 1] ?? 0) / 86400)} days. Each channel is scaled to its own range.</figcaption>
    <details><summary>Values table</summary><table className="studio-table"><thead><tr><th>t [s]</th>{paths.map((path) => <th key={path.name}>{path.name}</th>)}</tr></thead>
      <tbody>{t.map((time, row) => row % Math.max(1, Math.ceil(t.length / 40)) === 0 ? <tr key={row}><td>{fmt(time)}</td>{paths.map((path) => <td key={path.name}>{fmt(series.channels[path.name][row])}</td>)}</tr> : null)}</tbody></table></details></figure>;
}

function Results({ results, workspaceId, draftId }: { results: RunResults; workspaceId: string; draftId: string }) {
  const [channels, setChannels] = useState<string[]>([]); const [picked, setPicked] = useState<string[]>([]); const [series, setSeries] = useState<SeriesResponse | null>(null); const [problem, setProblem] = useState<Failure>(null);
  const balance = balanceStatus(results); const link = results.procedure_link;
  useEffect(() => {
    let alive = true; setSeries(null); setProblem(null);
    void getRunManifest(workspaceId, draftId, results.job_id).then((manifest) => {
      if (!alive) return; const names = Object.keys(manifest.channels ?? {}).filter((name) => name !== "t_s"); setChannels(names);
      const defaults = [...names.filter((name) => name.endsWith("_X")).slice(0, 2), ...names.filter((name) => name.endsWith("_V_m3")).slice(0, 1)]; setPicked(defaults.length ? defaults : names.slice(0, 2));
    }).catch((cause) => { if (alive) setProblem(failure(cause)); });
    return () => { alive = false; };
  }, [workspaceId, draftId, results.job_id]);
  useEffect(() => {
    if (!picked.length) { setSeries(null); return; }
    let alive = true;
    void getRunSeries(workspaceId, draftId, results.job_id, picked).then((next) => { if (alive) setSeries(next); }).catch((cause) => { if (alive) setProblem(failure(cause)); });
    return () => { alive = false; };
  }, [workspaceId, draftId, results.job_id, picked]);
  const actionEvents = results.event_log.filter((entry) => entry.type === "actions");
  return <section className="studio-report studio-results" data-job={results.job_id}><h4>Run {results.job_id.slice(0, 8)} · {results.status}</h4><SimulationNotice />
    <p className="studio-link-provenance">Procedure {link.version_label} · source {link.source_sha256.slice(0, 12)} · contract {link.contract_sha256.slice(0, 12)} · compiled {link.compiled_sha256.slice(0, 12)} · values {Object.entries(link.parameter_values).map(([key, value]) => `${key} = ${value}`).join(", ") || "none"} · schedule {link.schedule_id}</p>
    {results.error ? <Refusal code={results.error.code} message={results.error.message} /> : null}
    <p className={balance.closed ? "studio-notice" : "studio-warning"} data-balance={balance.closed ? "closed" : "open"}>Balances: {balance.text}</p>
    {problem ? <Refusal code={problem.code} message={problem.message} /> : null}
    {channels.length ? <label>Series channels<select multiple size={Math.min(6, channels.length)} aria-label="Series channels" value={picked} onChange={(event) => setPicked(Array.from(event.target.selectedOptions, (option) => option.value).slice(0, 5))}>{channels.map((name) => <option key={name} value={name}>{name}</option>)}</select></label> : null}
    {series ? <SeriesChart series={series} channels={picked} /> : null}
    <h5>Event log ({actionEvents.length} action events)</h5>
    <table className="studio-table"><thead><tr><th>#</th><th>Time [s]</th><th>Trigger</th><th>Actions</th><th>Balance</th></tr></thead>
      <tbody>{actionEvents.map((entry, index) => <tr key={index}><td>{index + 1}</td><td>{fmt(entry.time_s)}</td><td>{entry.trigger ?? "time"}</td><td>{(entry.actions ?? []).map((record) => String(record.type)).join(", ")}</td><td>{entry.balance?.closed === false ? "OPEN" : "closed"}</td></tr>)}</tbody></table>
    {results.campaign ? Object.entries(results.campaign.loops).map(([loop, data]) => <div key={loop}><h5>Per-cycle KPIs · loop {loop} · {String(data.summary.periodicity ?? "")}</h5>
      <table className="studio-table"><thead><tr>{KPI_COLUMNS.map(([, title]) => <th key={title}>{title}</th>)}</tr></thead><tbody>{data.cycles.map((cycle, i) => <tr key={i}>{KPI_COLUMNS.map(([key]) => <td key={key}>{fmt(cycle[key])}</td>)}</tr>)}</tbody></table>
      <p>Draws {fmt(data.summary.draws)} · harvested {fmt(data.summary.harvested_biomass_kg)} kg · mean last-{fmt(data.summary.last_k)} productivity {fmt(data.summary.mean_last_k_net_volumetric_productivity_kg_m3_day)} kg/m3/d</p></div>) : null}
  </section>;
}

export default function ProcedureBench({ workspaceId, model }: { workspaceId: string; model: StudioModel }) {
  const parameters = model.parameters ?? [];
  const published = model.versions;
  const [drafts, setDrafts] = useState<BenchDraft[]>([]); const [profiles, setProfiles] = useState<EnvironmentProfileHead[]>([]);
  const [draftId, setDraftId] = useState(""); const [scenarioId, setScenarioId] = useState(""); const [scheduleId, setScheduleId] = useState("procedure");
  const [versionId, setVersionId] = useState(published[published.length - 1]?.id ?? ""); const [values, setValues] = useState<Record<string, number | undefined>>({});
  const [links, setLinks] = useState<ProcedureLink[]>([]); const [runs, setRuns] = useState<RunRow[]>([]); const [results, setResults] = useState<RunResults | null>(null);
  const [problem, setProblem] = useState<Failure>(null); const [info, setInfo] = useState<string | null>(null); const [busy, setBusy] = useState(false);
  const [newScenario, setNewScenario] = useState({ id: "bench", profile: "", days: 7 });
  const [circulation, setCirculation] = useState<Record<string, number | undefined>>({}); const [initial, setInitial] = useState<Record<string, Partial<Record<"X" | "N" | "O2", number>>>>({});
  const draft = drafts.find((item) => item.draft_id === draftId) ?? null;
  const ownLinks = useMemo(() => links.filter((link) => link.model_spec_id === model.id), [links, model.id]);
  const activeLink = ownLinks.find((link) => link.schedule_id === scheduleId && link.scenario_id === scenarioId) ?? ownLinks.find((link) => link.schedule_id === scheduleId) ?? null;
  const settled = (status: string) => ["succeeded", "failed", "cancelled", "interrupted"].includes(status);

  const reloadDrafts = useCallback(() => listBenchDrafts(workspaceId).then((next) => { setDrafts(next); setDraftId((current) => current || next[0]?.draft_id || ""); }), [workspaceId]);
  const reloadDraft = useCallback((id: string) => id ? Promise.all([listProcedureLinks(workspaceId, id), listProcedureRuns(workspaceId, id), reloadDrafts()]).then(([nextLinks, nextRuns]) => { setLinks(nextLinks); setRuns(nextRuns); }) : Promise.resolve(), [workspaceId, reloadDrafts]);
  useEffect(() => { void reloadDrafts().catch((cause) => setProblem(failure(cause))); void listEnvironmentProfiles(workspaceId).then(setProfiles).catch(() => undefined); }, [workspaceId, reloadDrafts]);
  useEffect(() => { setScenarioId((current) => draft?.scenarios.some((item) => item.id === current) ? current : draft?.scenarios[0]?.id ?? ""); void reloadDraft(draftId).catch((cause) => setProblem(failure(cause))); }, [draftId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (activeLink) setValues(Object.fromEntries(parameters.map((item) => [item.name, activeLink.parameter_values[item.name]]))); }, [activeLink?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { setValues((current) => Object.fromEntries(parameters.map((item) => [item.name, current[item.name] ?? (activeLink?.parameter_values[item.name]) ?? (item.min != null && item.max != null ? (item.min + item.max) / 2 : item.min ?? item.max ?? 0)]))); }, [model.id, activeLink?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (!published.some((item) => item.id === versionId)) setVersionId(published[published.length - 1]?.id ?? ""); }, [published, versionId]);
  // Poll while a run is unsettled.
  useEffect(() => {
    if (!draftId || !runs.some((row) => !settled(row.job.status))) return;
    const timer = window.setInterval(() => { void reloadDraft(draftId).catch(() => undefined); }, 1500);
    return () => window.clearInterval(timer);
  }, [runs, draftId, reloadDraft]);

  const act = async (action: () => Promise<void>) => { setBusy(true); setProblem(null); setInfo(null); try { await action(); } catch (cause) { setProblem(failure(cause)); } finally { setBusy(false); } };
  const numbers = () => Object.fromEntries(Object.entries(values).filter(([, value]) => value !== undefined)) as Record<string, number>;
  const apply = (overwrite: boolean) => void act(async () => { const link = await applyProcedure(workspaceId, { version_id: versionId, draft_id: draftId, scenario_id: scenarioId, schedule_id: scheduleId, parameter_values: numbers(), overwrite }); await reloadDraft(draftId); setInfo(`Applied ${link.version_label} as schedule "${link.schedule_id}". Nothing has run yet.`); });
  const update = (link: ProcedureLink, overwrite: boolean) => void act(async () => { const next = await updateProcedureLink(workspaceId, link.id, { parameter_values: numbers(), overwrite }); await reloadDraft(draftId); setInfo(`Updated to ${next.version_label}.`); });
  const run = (link: ProcedureLink) => void act(async () => { const started = await runProcedureLink(workspaceId, link.id); await reloadDraft(draftId); setResults(null); setInfo(`Run ${started.job_id.slice(0, 8)} ${started.status}.`); });
  const open = (row: RunRow) => void act(async () => { setResults(await getProcedureResults(workspaceId, row.procedure_link.draft_id, row.job.job_id)); });
  const create = () => void act(async () => { const row = await createBenchScenario(workspaceId, draftId, { scenario_id: newScenario.id, profile_id: newScenario.profile, days: newScenario.days, output_cadence_s: 3600, circulation: Object.fromEntries(Object.entries(circulation).filter(([, value]) => value !== undefined)) as Record<string, number>, initial: initial as Record<string, { X: number; N: number; O2: number }> }); await reloadDraft(draftId); setScenarioId(newScenario.id); setInfo(row.scenario_check && !row.scenario_check.ok ? `Scenario created, but the host check says ${row.scenario_check.code}: ${row.scenario_check.message}` : `Scenario "${newScenario.id}" created.`); });
  const pumps = (draft?.units ?? []).filter((item) => item.type === "Pump").map((item) => item.tag);
  const cultureUnits = (draft?.units ?? []).filter((item) => item.type === "PhotobioreactorT1" || item.type === "HoldupTank").map((item) => item.tag);
  const initialComplete = cultureUnits.every((tag) => (["X", "N", "O2"] as const).every((key) => Number.isFinite(initial[tag]?.[key])));
  const valueIssues = parameterValuesIssues(parameters, values);
  const retryable = problem?.code && OVERWRITE_CODES.has(problem.code);

  return <div className="studio-panel studio-bench"><h3>Test bench</h3><SimulationNotice />
    <p>Pick a Process draft and one of its scenarios, apply a published version of this procedure, run it, and read the result. This is a minimal bench, not the Dynamic Studio.</p>
    {!published.length ? <p className="studio-warning">Publish a version first. Only published versions can be applied.</p> : null}
    <div className="studio-number-map">
      <label>Process draft<select aria-label="Bench draft" value={draftId} onChange={(event) => setDraftId(event.target.value)}><option value="">Choose a draft…</option>{drafts.map((item) => <option key={item.draft_id} value={item.draft_id}>{item.name}</option>)}</select></label>
      <label>Scenario<select aria-label="Bench scenario" value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}><option value="">{draft?.scenarios.length ? "Choose a scenario…" : "No scenario yet"}</option>{(draft?.scenarios ?? []).map((item) => <option key={item.id} value={item.id}>{item.id}{item.schedule_id ? ` (schedule ${item.schedule_id})` : ""}</option>)}</select></label>
      <label>Schedule id<input aria-label="Schedule id" value={scheduleId} pattern="[a-z][a-z0-9_-]{0,39}" onChange={(event) => setScheduleId(event.target.value)} /></label>
      <label>Published version<select aria-label="Version to apply" value={versionId} onChange={(event) => setVersionId(event.target.value)}>{published.map((item) => <option key={item.id} value={item.id}>{item.version_label}</option>)}</select></label></div>
    {draft ? <p>Tanks: {draft.tanks.join(", ") || "none"} · Units: {draft.units.map((item) => `${item.tag} (${item.type})`).join(", ") || "none"} · revision {draft.revision.slice(0, 12)}</p> : null}
    {draft ? <details className="studio-case" open={!draft.scenarios.length}><summary>Create a minimal scenario</summary>
      <p>This writes one new scenario to the draft; it never overwrites an existing one. If the host check refuses the scenario, its code is shown and you can create another with a different id.</p>
      <div className="studio-number-map"><label>Scenario id<input aria-label="New scenario id" value={newScenario.id} onChange={(event) => setNewScenario({ ...newScenario, id: event.target.value })} /></label>
        <label>Environment profile<select aria-label="Environment profile" value={newScenario.profile} onChange={(event) => setNewScenario({ ...newScenario, profile: event.target.value })}><option value="">Choose a profile…</option>{profiles.map((item) => <option key={item.profile_id} value={item.profile_id}>{item.name}</option>)}</select></label>
        <label>Days<input type="number" min="0.01" max="120" step="any" aria-label="Scenario days" value={newScenario.days} onChange={(event) => setNewScenario({ ...newScenario, days: Number(event.target.value) })} /></label></div>
      <div className="studio-number-map"><strong>Initial culture state (required for every PBR and tank, kg/m3)</strong>{cultureUnits.flatMap((tag) => (["X", "N", "O2"] as const).map((key) => <label key={`${tag}${key}`}>{tag} {key}<input type="number" step="any" min="0" aria-label={`Initial ${key} of ${tag}`} value={initial[tag]?.[key] ?? ""} onChange={(event) => setInitial({ ...initial, [tag]: { ...initial[tag], [key]: event.target.value === "" ? undefined : Number(event.target.value) } })} /></label>))}</div>
      {pumps.length ? <div className="studio-number-map"><strong>Pump circulation (m3/s, optional)</strong>{pumps.map((tag) => <label key={tag}>{tag}<input type="number" step="any" min="0" aria-label={`Circulation of ${tag}`} value={circulation[tag] ?? ""} onChange={(event) => setCirculation({ ...circulation, [tag]: event.target.value === "" ? undefined : Number(event.target.value) })} /></label>)}</div> : null}
      <button type="button" disabled={busy || !newScenario.profile || !initialComplete} onClick={create}>Create scenario</button>{!profiles.length ? <p className="studio-warning">No environment profile exists. Import one in the Environment panel first.</p> : null}</details> : null}
    <fieldset className="studio-case"><legend>Apply</legend><SimulationNotice />
      <div className="studio-number-map"><strong>Parameter values (declared units)</strong>{parameters.map((item) => <label key={item.name}>{item.label || item.name} [{item.unit}]{boundHint(item)}<input type="number" step="any" aria-label={`Apply value of ${item.name}`} value={values[item.name] ?? ""} onChange={(event) => setValues({ ...values, [item.name]: event.target.value === "" ? undefined : Number(event.target.value) })} /></label>)}</div>
      {valueIssues.map((issue) => <p className="studio-warning" key={issue}>{issue}</p>)}
      <p>Apply writes the compiled schedule into the draft under this schedule id. It is an explicit action. A refusal changes nothing.</p>
      <button type="button" disabled={busy || !draftId || !scenarioId || !versionId || valueIssues.length > 0} onClick={() => apply(false)}>Apply</button>
      {retryable ? <button type="button" disabled={busy} onClick={() => apply(true)}>Apply anyway (overwrite)</button> : null}</fieldset>
    {problem ? <Refusal code={problem.code} message={problem.message} /> : null}{info ? <p className="studio-notice" role="status">{info}</p> : null}
    <h4>Applied procedures on this draft</h4>
    {ownLinks.length ? ownLinks.map((link) => <article key={link.id} className="studio-link" data-link-state={link.state}>
      <strong>{link.version_label} · schedule {link.schedule_id} · scenario {link.scenario_id}</strong>
      <p className="studio-link-provenance">Source {link.source_sha256.slice(0, 12)} · contract {link.contract_sha256.slice(0, 12)} · compiled {link.compiled_sha256.slice(0, 12)} · values {Object.entries(link.parameter_values).map(([key, value]) => `${key} = ${value}`).join(", ") || "none"}</p>
      {linkBadges(link).map((badge) => <p key={badge.text} className={badge.tone === "ok" ? "studio-notice" : badge.tone === "warn" ? "studio-warning" : "studio-error"} role="status">{badge.text}</p>)}
      <SimulationNotice />
      <div className="studio-actions"><button type="button" disabled={busy || !canRun(link)} onClick={() => run(link)}>Run</button>
        {updateLabel(link) ? <button type="button" disabled={busy} onClick={() => update(link, false)}>{updateLabel(link)}</button> : null}
        {link.state === "modified" ? <button type="button" disabled={busy} onClick={() => update(link, true)}>Re-apply and overwrite my edit</button> : null}</div></article>) : <p>No procedure is applied to this draft yet.</p>}
    <header className="studio-runs-head"><h4>Runs</h4><button type="button" disabled={!draftId} onClick={() => void reloadDraft(draftId)}>Refresh</button></header>
    {runs.filter((row) => row.procedure_link.model_spec_id === model.id).map((row) => <article key={row.job.job_id} data-job-status={row.job.status}><strong>Run {row.job.job_id.slice(0, 8)} · {row.job.status}</strong>
      <span> · {row.procedure_link.version_label} · values {Object.entries(row.procedure_link.parameter_values).map(([key, value]) => `${key} = ${value}`).join(", ") || "none"}</span>
      {row.job.error ? <Refusal code={row.job.error.code} message={row.job.error.message} /> : null}
      <button type="button" disabled={busy || !settled(row.job.status)} onClick={() => open(row)}>View results</button></article>)}
    {results ? <Results results={results} workspaceId={workspaceId} draftId={results.procedure_link.draft_id} /> : null}
  </div>;
}
