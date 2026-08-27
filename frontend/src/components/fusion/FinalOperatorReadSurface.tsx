import { useEffect, useMemo, useState } from "react";

import {
  listFinalDecisions,
  listFinalModelSpecs,
  listFinalParameters,
  listFinalRequirements,
  listFinalWorkspaces,
  readFinalSystemInfo,
  type FinalDecision,
  type FinalModelSpec,
  type FinalParameter,
  type FinalRequirement,
  type FinalWorkspace
} from "../../api/finalOperatorReads";
import type { SystemInfoResponse } from "../../api/client";

type ReadKind = "project-basis" | "models" | "runtime";

type Props = Readonly<{
  kind: ReadKind;
  workspaceId: string | null;
  onWorkspaceChange: (workspaceId: string) => void;
}>;

type WorkspaceRecords = Readonly<{
  requirements: FinalRequirement[];
  parameters: FinalParameter[];
  decisions: FinalDecision[];
  modelSpecs: FinalModelSpec[];
}>;

const emptyRecords: WorkspaceRecords = { requirements: [], parameters: [], decisions: [], modelSpecs: [] };

function Panel({ title, children, className = "", status }: Readonly<{ title: string; children: React.ReactNode; className?: string; status?: string }>) {
  return <section className={`final-fusion__panel ${className}`.trim()} aria-label={title}><header className="final-fusion__panel-head"><h2>{title}</h2>{status && <span>{status}</span>}</header>{children}</section>;
}

function JarvisReadBoundary({ detail }: Readonly<{ detail: string }>) {
  return <Panel title="Jarvis" className="final-fusion__jarvis" status="Read context only"><div className="final-fusion__jarvis-body"><div className="final-fusion__context-note">Browsing does not add records to Jarvis context. Explicit context insertion remains separately governed.</div><div className="final-fusion__bubble">{detail}</div><div className="final-fusion__composer" aria-disabled="true"><span>Ask Jarvis about an exact selected record…</span><button type="button" disabled>Send</button></div></div></Panel>;
}

function WorkspacePicker({ workspaces, selectedId, onSelect }: Readonly<{ workspaces: FinalWorkspace[]; selectedId: string | null; onSelect: (id: string) => void }>) {
  return <div className="final-fusion__toolbar-line"><span>Project workspace</span><select aria-label="Project workspace" value={selectedId ?? ""} onChange={(event) => onSelect(event.target.value)} disabled={!workspaces.length}><option value="">Select workspace…</option>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}</select></div>;
}

function ProjectBasis({ records, workspaces, workspaceId, onWorkspaceChange, loading, error }: Readonly<{ records: WorkspaceRecords; workspaces: FinalWorkspace[]; workspaceId: string | null; onWorkspaceChange: (id: string) => void; loading: boolean; error: string | null }>) {
  const rows = [
    ...records.requirements.map((item) => ({ id: `requirement:${item.id}`, label: item.statement, meta: `Requirement · ${item.status}` })),
    ...records.parameters.map((item) => ({ id: `parameter:${item.id}`, label: `${item.name}${item.symbol ? ` (${item.symbol})` : ""}`, meta: `Parameter · ${item.value ?? "Unknown"}${item.unit ? ` ${item.unit}` : ""} · ${item.lifecycle_state ?? item.status}` })),
    ...records.decisions.map((item) => ({ id: `decision:${item.id}`, label: item.title, meta: `Decision · ${item.status}` }))
  ];
  return <div className="final-fusion__workbench final-fusion__workbench--memory"><Panel title="Project search" className="final-fusion__search-panel" status="READ"><div className="final-fusion__searchbox">Canonical record search is unavailable in this slice.</div><WorkspacePicker workspaces={workspaces} selectedId={workspaceId} onSelect={onWorkspaceChange} /><div className="final-fusion__source-list">{loading ? <div className="final-fusion__source-empty"><strong>Loading backend records…</strong></div> : error ? <div className="final-fusion__source-empty"><strong>Backend read failed</strong><span>{error}</span></div> : rows.length ? rows.map((row) => <div className="final-fusion__disclosure-row" key={row.id}><span>›</span><strong>{row.label}</strong><em>{row.meta}</em></div>) : <div className="final-fusion__source-empty"><strong>No current basis records</strong><span>The selected workspace returned no requirements, current parameters or decisions.</span></div>}</div></Panel><Panel title="Project Basis" className="final-fusion__basis" status="Existing READ projection"><div className="final-fusion__dossier-top"><strong>Current server-owned engineering records</strong><span>Working revisions are unavailable</span></div><div className="final-fusion__summary-strip"><span>Requirements · {records.requirements.length}</span><span>Parameters · {records.parameters.length}</span><span>Decisions · {records.decisions.length}</span></div><div className="final-fusion__toolbar-line"><span>Approve-all, working revision and deterministic revalidation require their future accepted owner.</span><button type="button" disabled>Approve all</button></div><div className="final-fusion__disclosures"><div className="final-fusion__disclosure-row"><span>›</span><strong>Objectives & engineering question</strong><em>Unavailable</em></div><div className="final-fusion__disclosure-row"><span>›</span><strong>Requirements & acceptance criteria</strong><em>{records.requirements.length ? "Read-only projection" : "Empty"}</em></div><div className="final-fusion__disclosure-row"><span>›</span><strong>Stable constraints & boundary conditions</strong><em>{records.parameters.length ? "Current parameters available" : "Empty"}</em></div><div className="final-fusion__disclosure-row"><span>›</span><strong>Standards, decisions & resources</strong><em>{records.decisions.length ? "Decisions available" : "Partial / unavailable"}</em></div></div></Panel><JarvisReadBoundary detail="Current requirements, parameters and decisions are backend-owned READ evidence. Working-revision proposals remain unavailable rather than being simulated in React." /></div>;
}

function Models({ records, workspaces, workspaceId, onWorkspaceChange, loading, error }: Readonly<{ records: WorkspaceRecords; workspaces: FinalWorkspace[]; workspaceId: string | null; onWorkspaceChange: (id: string) => void; loading: boolean; error: string | null }>) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = records.modelSpecs.find((item) => item.id === selectedId) ?? records.modelSpecs[0] ?? null;
  useEffect(() => { if (selected && selected.id !== selectedId) setSelectedId(selected.id); }, [selected, selectedId]);
  return <div className="final-fusion__workbench final-fusion__workbench--models"><Panel title="Model versions" className="final-fusion__versions" status="Model specs only"><WorkspacePicker workspaces={workspaces} selectedId={workspaceId} onSelect={onWorkspaceChange} /><div className="final-fusion__searchbox">Exact model-version inventory is not exposed by the current read owner.</div>{loading ? <div className="final-fusion__source-empty"><strong>Loading model specifications…</strong></div> : error ? <div className="final-fusion__source-empty"><strong>Backend read failed</strong><span>{error}</span></div> : records.modelSpecs.length ? <div className="final-fusion__source-list">{records.modelSpecs.map((item) => <button type="button" className="final-fusion__disclosure-row" key={item.id} onClick={() => setSelectedId(item.id)} aria-pressed={selected?.id === item.id}><span>›</span><strong>{item.title}</strong><em>{item.status} · schema {item.schema_version}</em></button>)}</div> : <div className="final-fusion__source-empty"><strong>No model specifications</strong></div>}<div className="final-fusion__lineage-slot">Exact version lineage · Unknown</div></Panel><Panel title="Version dossier" className="final-fusion__model-dossier" status={selected ? "Model spec READ" : "Unavailable"}><div className="final-fusion__dossier-top"><strong>{selected?.title ?? "Exact model / version"}</strong><span>{selected ? "Specification record; not an exact model version" : "Unknown"}</span></div><div className="final-fusion__summary-strip"><span>Identity · {selected?.id ?? "Unknown"}</span><span>Status · {selected?.status ?? "Unknown"}</span><span>Maturity · {selected?.maturity_status ?? "Unknown"}</span></div><div className="final-fusion__dossier-grid"><section><header><strong>Definition</strong><span>{selected ? "READ" : "Unavailable"}</span></header><p>{selected?.engineering_question ?? "No exact-version definition is available."}</p>{selected?.scope && <p>{selected.scope}</p>}</section>{["Assumptions", "Methods & Equations", "Parameters & Inputs", "Process", "BLUECAD", "Results & Validation", "Criticalities", "Sources", "Artifacts", "Runs", "Changelog / Lineage"].map((label) => <section key={label}><header><strong>{label}</strong><span>Exact-version owner unavailable</span></header><p>Not projected from workspace-level records because exact model/version binding cannot be proven.</p></section>)}</div><div className="final-fusion__context-strip">Workspace records are not promoted into exact-version evidence without an explicit binding.</div></Panel><JarvisReadBoundary detail="The selected model specification can be read. Exact version, runs, artifacts and evidence remain Unknown until an accepted version-bound read owner exists." /></div>;
}

function Runtime({ system, loading, error }: Readonly<{ system: SystemInfoResponse | null; loading: boolean; error: string | null }>) {
  return <div className="final-fusion__workbench final-fusion__workbench--coding"><Panel title="Runtime" className="final-fusion__runtime-main" status="Observed system facts"><div className="final-fusion__repo-status"><div><strong>JarvisOS runtime identity</strong><span>Exact executed SHA vs remote SHA observer unavailable</span></div><span className="final-fusion__unknown">Unknown</span></div><div className="final-fusion__runtime-body"><section className="final-fusion__compare"><div className="final-fusion__version-card"><small>Local current · actually executed</small><strong>LOCAL · Unknown SHA</strong><code>{system?.environment ?? "Environment unknown"}</code><p>{system ? `${system.app_name} ${system.version} is reporting through /system/info, but that does not prove an executed Git SHA.` : "No exact local code identity is proven."}</p></div><div className="final-fusion__delta">→<span>Unknown</span></div><div className="final-fusion__version-card is-remote"><small>GitHub latest · remote exact</small><strong>REMOTE · Unknown</strong><code>Repository observer unavailable</code><p>The frontend does not call GitHub directly or infer alignment.</p></div></section><section className="final-fusion__runtime-services"><Panel title="Observed backend" status={loading ? "Loading" : error ? "Read error" : system?.database.ready ? "Database ready" : "Unknown"}>{error ? <div className="final-fusion__empty">{error}</div> : <div className="final-fusion__facts"><div>Application · {system?.app_name ?? "Unknown"}</div><div>Version · {system?.version ?? "Unknown"}</div><div>Environment · {system?.environment ?? "Unknown"}</div><div>Database initialized · {system ? String(system.database.initialized) : "Unknown"}</div></div>}</Panel><Panel title="Update / terminal" status="Unavailable"><div className="final-fusion__empty">Safe update and terminal EXECUTE authority are not present in 100f.</div></Panel></section></div></Panel><div className="final-fusion__rightstack"><JarvisReadBoundary detail="Observed /system/info facts may be discussed, but local executed SHA, remote exact SHA and alignment remain Unknown." /><Panel title="Runtime facts" className="final-fusion__facts" status="READ"><div className="final-fusion__empty">System observations are backend-provided. No GitHub or process authority exists in the browser.</div></Panel></div></div>;
}

export default function FinalOperatorReadSurface({ kind, workspaceId, onWorkspaceChange }: Props) {
  const [workspaces, setWorkspaces] = useState<FinalWorkspace[]>([]);
  const [records, setRecords] = useState<WorkspaceRecords>(emptyRecords);
  const [system, setSystem] = useState<SystemInfoResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const activeWorkspaceId = useMemo(() => workspaceId ?? workspaces[0]?.id ?? null, [workspaceId, workspaces]);

  useEffect(() => {
    if (kind === "runtime") {
      setLoading(true); setError(null);
      void readFinalSystemInfo().then(setSystem).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Runtime read failed")).finally(() => setLoading(false));
      return;
    }
    setLoading(true); setError(null);
    void listFinalWorkspaces().then((items) => {
      setWorkspaces(items);
      if (!workspaceId && items[0]) onWorkspaceChange(items[0].id);
    }).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Workspace read failed")).finally(() => setLoading(false));
  }, [kind, onWorkspaceChange, workspaceId]);

  useEffect(() => {
    if (kind === "runtime" || !activeWorkspaceId) return;
    setLoading(true); setError(null);
    const calls = kind === "models"
      ? Promise.all([Promise.resolve([] as FinalRequirement[]), Promise.resolve([] as FinalParameter[]), Promise.resolve([] as FinalDecision[]), listFinalModelSpecs(activeWorkspaceId)])
      : Promise.all([listFinalRequirements(activeWorkspaceId), listFinalParameters(activeWorkspaceId), listFinalDecisions(activeWorkspaceId), Promise.resolve([] as FinalModelSpec[])]);
    void calls.then(([requirements, parameters, decisions, modelSpecs]) => setRecords({ requirements, parameters, decisions, modelSpecs })).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Workspace record read failed")).finally(() => setLoading(false));
  }, [activeWorkspaceId, kind]);

  if (kind === "runtime") return <Runtime system={system} loading={loading} error={error} />;
  if (kind === "models") return <Models records={records} workspaces={workspaces} workspaceId={activeWorkspaceId} onWorkspaceChange={onWorkspaceChange} loading={loading} error={error} />;
  return <ProjectBasis records={records} workspaces={workspaces} workspaceId={activeWorkspaceId} onWorkspaceChange={onWorkspaceChange} loading={loading} error={error} />;
}
