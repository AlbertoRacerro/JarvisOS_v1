import { useEffect, useMemo, useRef, useState } from "react";

import { listWorkspaces, type Workspace } from "../api/client";
import { RunsRequestError, getRun, listRunArtifacts, listRunLogs, listRuns, type RunArtifact, type RunLog, type SimulationRunDetail, type SimulationRunSummary } from "../api/runs";
import { acceptsResponse, chooseSelection, projectPayload, visibleRuns } from "../components/runs/state";

type Props = {
  workspaceId: string | null;
  onWorkspaceChange(next: string | null): void;
};

type LoadState = "idle" | "loading" | "ready" | "error";

function fmt(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function RunsWorkbench({ workspaceId, onWorkspaceChange }: Props) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceState, setWorkspaceState] = useState<LoadState>("loading");
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [runs, setRuns] = useState<SimulationRunSummary[]>([]);
  const [runsState, setRunsState] = useState<LoadState>("idle");
  const [runsError, setRunsError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<SimulationRunDetail | null>(null);
  const [detailState, setDetailState] = useState<LoadState>("idle");
  const [detailError, setDetailError] = useState<string | null>(null);
  const [logs, setLogs] = useState<RunLog[]>([]);
  const [logsState, setLogsState] = useState<LoadState>("idle");
  const [logsError, setLogsError] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<RunArtifact[]>([]);
  const [artifactsState, setArtifactsState] = useState<LoadState>("idle");
  const [artifactsError, setArtifactsError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const workspaceGeneration = useRef(0);
  const listGeneration = useRef(0);
  const detailGeneration = useRef(0);
  const logsGeneration = useRef(0);
  const artifactsGeneration = useRef(0);
  const currentWorkspace = useRef(workspaceId);
  const currentRun = useRef(selectedId);
  currentWorkspace.current = workspaceId;
  currentRun.current = selectedId;

  const clearRunState = () => {
    listGeneration.current += 1;
    detailGeneration.current += 1;
    logsGeneration.current += 1;
    artifactsGeneration.current += 1;
    setRuns([]);
    setSelectedId(null);
    setDetail(null);
    setLogs([]);
    setArtifacts([]);
    setRunsState("idle");
    setDetailState("idle");
    setLogsState("idle");
    setArtifactsState("idle");
    setRunsError(null);
    setDetailError(null);
    setLogsError(null);
    setArtifactsError(null);
  };

  const changeWorkspace = (next: string | null) => {
    clearRunState();
    onWorkspaceChange(next);
  };

  const loadWorkspaces = () => {
    const generation = ++workspaceGeneration.current;
    setWorkspaceState("loading");
    setWorkspaceError(null);
    void listWorkspaces().then((rows) => {
      if (!acceptsResponse({ generation, identity: "workspaces" }, workspaceGeneration.current, "workspaces")) return;
      setWorkspaces(rows);
      setWorkspaceState("ready");
      const activeWorkspace = currentWorkspace.current;
      const valid = activeWorkspace !== null && rows.some((row) => row.id === activeWorkspace);
      if (!valid) changeWorkspace(rows[0]?.id ?? null);
    }).catch((error: Error) => {
      if (!acceptsResponse({ generation, identity: "workspaces" }, workspaceGeneration.current, "workspaces")) return;
      setWorkspaceState("error");
      setWorkspaceError(error.message);
    });
  };

  useEffect(loadWorkspaces, []);

  const loadRuns = (targetWorkspace: string) => {
    const generation = ++listGeneration.current;
    setRunsState("loading");
    setRunsError(null);
    void listRuns(targetWorkspace).then((rows) => {
      if (!acceptsResponse({ generation, identity: targetWorkspace }, listGeneration.current, currentWorkspace.current ?? "")) return;
      setRuns(rows);
      setRunsState("ready");
      setSelectedId((current) => chooseSelection(current, rows));
    }).catch((error: Error) => {
      if (!acceptsResponse({ generation, identity: targetWorkspace }, listGeneration.current, currentWorkspace.current ?? "")) return;
      setRuns([]);
      setSelectedId(null);
      setRunsState("error");
      setRunsError(error.message);
    });
  };

  useEffect(() => {
    clearRunState();
    if (workspaceId) loadRuns(workspaceId);
  }, [workspaceId]);

  const loadDetail = (targetWorkspace: string, runId: string) => {
    const identity = `${targetWorkspace}:${runId}`;
    const generation = ++detailGeneration.current;
    setDetailState("loading");
    setDetailError(null);
    void getRun(targetWorkspace, runId).then((value) => {
      const currentIdentity = `${currentWorkspace.current ?? ""}:${currentRun.current ?? ""}`;
      if (!acceptsResponse({ generation, identity }, detailGeneration.current, currentIdentity)) return;
      setDetail(value);
      setDetailState("ready");
    }).catch((error: Error) => {
      const currentIdentity = `${currentWorkspace.current ?? ""}:${currentRun.current ?? ""}`;
      if (!acceptsResponse({ generation, identity }, detailGeneration.current, currentIdentity)) return;
      setDetail(null);
      setDetailState("error");
      setDetailError(error instanceof RunsRequestError && error.status === 404 ? "Selected run is no longer available. Refresh the run list." : error.message);
    });
  };

  const loadLogs = (targetWorkspace: string, runId: string) => {
    const identity = `${targetWorkspace}:${runId}`;
    const generation = ++logsGeneration.current;
    setLogsState("loading");
    setLogsError(null);
    void listRunLogs(targetWorkspace, runId).then((rows) => {
      const currentIdentity = `${currentWorkspace.current ?? ""}:${currentRun.current ?? ""}`;
      if (!acceptsResponse({ generation, identity }, logsGeneration.current, currentIdentity)) return;
      setLogs(rows);
      setLogsState("ready");
    }).catch((error: Error) => {
      const currentIdentity = `${currentWorkspace.current ?? ""}:${currentRun.current ?? ""}`;
      if (!acceptsResponse({ generation, identity }, logsGeneration.current, currentIdentity)) return;
      setLogs([]);
      setLogsState("error");
      setLogsError(error.message);
    });
  };

  const loadArtifacts = (targetWorkspace: string, runId: string) => {
    const identity = `${targetWorkspace}:${runId}`;
    const generation = ++artifactsGeneration.current;
    setArtifactsState("loading");
    setArtifactsError(null);
    void listRunArtifacts(targetWorkspace, runId).then((rows) => {
      const currentIdentity = `${currentWorkspace.current ?? ""}:${currentRun.current ?? ""}`;
      if (!acceptsResponse({ generation, identity }, artifactsGeneration.current, currentIdentity)) return;
      setArtifacts(rows);
      setArtifactsState("ready");
    }).catch((error: Error) => {
      const currentIdentity = `${currentWorkspace.current ?? ""}:${currentRun.current ?? ""}`;
      if (!acceptsResponse({ generation, identity }, artifactsGeneration.current, currentIdentity)) return;
      setArtifacts([]);
      setArtifactsState("error");
      setArtifactsError(error.message);
    });
  };

  useEffect(() => {
    detailGeneration.current += 1;
    logsGeneration.current += 1;
    artifactsGeneration.current += 1;
    setDetail(null);
    setLogs([]);
    setArtifacts([]);
    if (workspaceId && selectedId) {
      loadDetail(workspaceId, selectedId);
      loadLogs(workspaceId, selectedId);
      loadArtifacts(workspaceId, selectedId);
    }
  }, [workspaceId, selectedId]);

  const statuses = useMemo(() => Array.from(new Set(runs.map((run) => run.status))).sort(), [runs]);
  const filtered = useMemo(() => visibleRuns(runs, query, statusFilter), [runs, query, statusFilter]);
  const hiddenSelection = Boolean(selectedId && !filtered.some((run) => run.id === selectedId));

  if (workspaceState === "error") return <section className="runs-empty"><h1>Runs</h1><p>Workspace discovery failed: {workspaceError}</p><button onClick={loadWorkspaces}>Retry</button></section>;
  if (workspaceState === "loading") return <section className="runs-empty"><h1>Runs</h1><p>Loading workspaces…</p></section>;
  if (workspaces.length === 0) return <section className="runs-empty"><h1>Runs</h1><p>No workspaces</p></section>;

  return (
    <section className="runs-workbench" aria-labelledby="runs-title">
      <header className="runs-toolbar">
        <div><p className="eyebrow">Execution evidence</p><h1 id="runs-title">Runs</h1></div>
        <label>Workspace<select value={workspaceId ?? ""} onChange={(event) => changeWorkspace(event.target.value || null)}>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}</select></label>
        <button type="button" disabled={!workspaceId || runsState === "loading"} onClick={() => workspaceId && loadRuns(workspaceId)}>Refresh</button>
      </header>

      <div className="runs-grid">
        <aside className="runs-list" aria-labelledby="run-list-title">
          <h2 id="run-list-title">Run history</h2>
          <label>Search<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Label or id" /></label>
          <label>Status<select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="">All statuses</option>{statuses.map((status) => <option key={status} value={status}>{status}</option>)}</select></label>
          {runsState === "loading" && <p>Loading runs…</p>}
          {runsState === "error" && <div className="runs-inline-error"><p>Run list failed: {runsError}</p><button onClick={() => workspaceId && loadRuns(workspaceId)}>Retry</button></div>}
          {runsState === "ready" && runs.length === 0 && <p>No persisted runs</p>}
          {hiddenSelection && <p className="runs-note">Selected run hidden by current filter</p>}
          <div className="runs-list__rows">{filtered.map((run) => <button type="button" key={run.id} className={run.id === selectedId ? "run-row is-selected" : "run-row"} aria-pressed={run.id === selectedId} onClick={() => setSelectedId(run.id)}><span><strong>{run.run_label || run.id}</strong><small>{run.id}</small></span><span className="run-row__meta"><span>{run.status}</span><time>{fmt(run.created_at)}</time></span></button>)}</div>
        </aside>

        <main className="run-detail">
          {!selectedId && runsState === "ready" && runs.length > 0 && <p>Select a run</p>}
          {detailState === "loading" && <p>Loading run detail…</p>}
          {detailState === "error" && <div className="runs-inline-error"><p>Run detail failed: {detailError}</p><button onClick={() => workspaceId && selectedId && loadDetail(workspaceId, selectedId)}>Retry</button></div>}
          {detail && <>
            <header className="run-detail__header"><div><p className="eyebrow">Persisted run</p><h2>{detail.run_label || detail.id}</h2><p className="run-id">{detail.id}</p></div><strong className="run-status">{detail.status}</strong></header>
            <dl className="run-facts"><div><dt>Model version</dt><dd>{detail.model_version_id ?? "—"}</dd></div><div><dt>Created</dt><dd>{fmt(detail.created_at)}</dd></div><div><dt>Started</dt><dd>{fmt(detail.started_at)}</dd></div><div><dt>Completed</dt><dd>{fmt(detail.completed_at)}</dd></div></dl>
            {detail.notes && <p className="run-notes">{detail.notes}</p>}
            <Payload title="Inputs" projection={projectPayload(detail.input_payload, "input")} />
            <Payload title="Bindings" projection={projectPayload(detail.parameter_payload, "binding")} />
            <Payload title="Results" projection={projectPayload(detail.output_payload, "result")} />

            <section className="run-evidence"><header><h3>Logs</h3>{logsState === "error" && <button onClick={() => workspaceId && selectedId && loadLogs(workspaceId, selectedId)}>Retry</button>}</header>{logsState === "loading" && <p>Loading logs…</p>}{logsState === "error" && <p>Logs unavailable: {logsError}</p>}{logsState === "ready" && logs.length === 0 && <p>No persisted logs</p>}{logs.map((log) => <article className="run-log" key={log.id}><header><strong>{log.stream}</strong><time>{fmt(log.created_at)}</time>{log.truncated && <span>truncated</span>}</header><pre>{log.content}</pre></article>)}</section>

            <section className="run-evidence"><header><h3>Artifacts</h3>{artifactsState === "error" && <button onClick={() => workspaceId && selectedId && loadArtifacts(workspaceId, selectedId)}>Retry</button>}</header>{artifactsState === "loading" && <p>Loading artifacts…</p>}{artifactsState === "error" && <p>Artifacts unavailable: {artifactsError}</p>}{artifactsState === "ready" && artifacts.length === 0 && <p>No persisted artifacts</p>}<div className="run-artifacts">{artifacts.map((artifact) => <article key={artifact.artifact_id}><strong>{artifact.filename}</strong><dl><div><dt>Role / type</dt><dd>{artifact.role} / {artifact.artifact_type}</dd></div><div><dt>Status</dt><dd>{artifact.status}</dd></div><div><dt>Size</dt><dd>{artifact.size_bytes ?? "—"}</dd></div><div><dt>MIME</dt><dd>{artifact.mime_type ?? "—"}</dd></div><div><dt>SHA-256</dt><dd className="technical-token">{artifact.sha256 ?? "—"}</dd></div><div><dt>Source</dt><dd>{[artifact.source_module, artifact.source_ref].filter(Boolean).join(" · ") || "—"}</dd></div><div><dt>Created</dt><dd>{fmt(artifact.created_at)}</dd></div>{!artifact.under_data_root && <div><dt>Storage boundary</dt><dd>Outside configured data root</dd></div>}</dl></article>)}</div></section>
          </>}
        </main>
      </div>
    </section>
  );
}

function Payload({ title, projection }: { title: string; projection: ReturnType<typeof projectPayload> }) {
  return <section className="run-payload"><header><h3>{title}</h3>{projection.state === "ok" && projection.truncated && <span>Presentation truncated</span>}</header>{projection.state === "ok" ? <pre>{projection.text}</pre> : <p>{projection.text}</p>}</section>;
}

export default RunsWorkbench;
