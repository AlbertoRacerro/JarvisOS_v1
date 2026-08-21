import { useEffect, useMemo, useRef, useState } from "react";

import AppLink, { type Navigate } from "../app/AppLink";
import { listAssumptions, listDecisions, listModelSpecs, listParameters, listWorkspaces, type Assumption, type Decision, type ModelSpec, type Parameter, type Workspace } from "../api/client";
import { acceptsWorkspaceResponse, chooseEngineeringSelection, ENGINEERING_KINDS, projectEngineeringData, recordKey, visibleEngineeringRecords, type EngineeringKind, type EngineeringRecordProjection } from "../components/engineering-data/engineeringDataState";

type Props = {
  workspaceId: string | null;
  onWorkspaceChange(next: string | null): void;
  navigate: Navigate;
};
type LoadState = "idle" | "loading" | "ready" | "error";

const KIND_LABEL: Readonly<Record<EngineeringKind, string>> = {
  "model-spec": "Model specs",
  assumption: "Assumptions",
  parameter: "Parameters",
  decision: "Decisions",
};

function shown(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "Unavailable";
  return String(value);
}

function linkedParameterTarget(search: string): string | null {
  const params = new URLSearchParams(search);
  if (params.get("kind") !== "parameter") return null;
  const id = params.get("id")?.trim() ?? "";
  return id || null;
}

function EngineeringData({ workspaceId, onWorkspaceChange, navigate }: Props) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceState, setWorkspaceState] = useState<LoadState>("loading");
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [modelSpecs, setModelSpecs] = useState<ModelSpec[]>([]);
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [modelSpecsState, setModelSpecsState] = useState<LoadState>("idle");
  const [assumptionsState, setAssumptionsState] = useState<LoadState>("idle");
  const [parametersState, setParametersState] = useState<LoadState>("idle");
  const [decisionsState, setDecisionsState] = useState<LoadState>("idle");
  const [modelSpecsError, setModelSpecsError] = useState<string | null>(null);
  const [assumptionsError, setAssumptionsError] = useState<string | null>(null);
  const [parametersError, setParametersError] = useState<string | null>(null);
  const [decisionsError, setDecisionsError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [enabledKinds, setEnabledKinds] = useState<EngineeringKind[]>([...ENGINEERING_KINDS]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [sourceTargetMessage, setSourceTargetMessage] = useState<string | null>(null);
  const workspaceDiscoveryGeneration = useRef(0);
  const recordsGeneration = useRef(0);
  const currentWorkspace = useRef(workspaceId);
  currentWorkspace.current = workspaceId;

  const sourceParameterId = linkedParameterTarget(window.location.search);

  const clearRecords = () => {
    recordsGeneration.current += 1;
    setModelSpecs([]);
    setAssumptions([]);
    setParameters([]);
    setDecisions([]);
    setModelSpecsState("idle");
    setAssumptionsState("idle");
    setParametersState("idle");
    setDecisionsState("idle");
    setModelSpecsError(null);
    setAssumptionsError(null);
    setParametersError(null);
    setDecisionsError(null);
    setSelectedKey(null);
    setSourceTargetMessage(null);
  };

  const requestWorkspaceChange = (next: string | null) => {
    clearRecords();
    onWorkspaceChange(next);
  };

  const loadWorkspaces = () => {
    const generation = ++workspaceDiscoveryGeneration.current;
    setWorkspaceState("loading");
    setWorkspaceError(null);
    void listWorkspaces().then((rows) => {
      if (generation !== workspaceDiscoveryGeneration.current) return;
      setWorkspaces(rows);
      setWorkspaceState("ready");
      const active = currentWorkspace.current;
      if (active === null || !rows.some((row) => row.id === active)) requestWorkspaceChange(rows[0]?.id ?? null);
    }).catch((error: Error) => {
      if (generation !== workspaceDiscoveryGeneration.current) return;
      setWorkspaceState("error");
      setWorkspaceError(error.message);
    });
  };

  useEffect(loadWorkspaces, []);

  const loadRecords = (targetWorkspace: string) => {
    const generation = ++recordsGeneration.current;
    const accepted = () => acceptsWorkspaceResponse(generation, targetWorkspace, recordsGeneration.current, currentWorkspace.current);

    setModelSpecsState("loading");
    setAssumptionsState("loading");
    setParametersState("loading");
    setDecisionsState("loading");
    setModelSpecsError(null);
    setAssumptionsError(null);
    setParametersError(null);
    setDecisionsError(null);

    void listModelSpecs(targetWorkspace).then((rows) => {
      if (!accepted()) return;
      setModelSpecs(rows);
      setModelSpecsState("ready");
    }).catch((error: Error) => {
      if (!accepted()) return;
      setModelSpecs([]);
      setModelSpecsState("error");
      setModelSpecsError(error.message);
    });
    void listAssumptions(targetWorkspace).then((rows) => {
      if (!accepted()) return;
      setAssumptions(rows);
      setAssumptionsState("ready");
    }).catch((error: Error) => {
      if (!accepted()) return;
      setAssumptions([]);
      setAssumptionsState("error");
      setAssumptionsError(error.message);
    });
    void listParameters(targetWorkspace).then((rows) => {
      if (!accepted()) return;
      setParameters(rows);
      setParametersState("ready");
    }).catch((error: Error) => {
      if (!accepted()) return;
      setParameters([]);
      setParametersState("error");
      setParametersError(error.message);
    });
    void listDecisions(targetWorkspace).then((rows) => {
      if (!accepted()) return;
      setDecisions(rows);
      setDecisionsState("ready");
    }).catch((error: Error) => {
      if (!accepted()) return;
      setDecisions([]);
      setDecisionsState("error");
      setDecisionsError(error.message);
    });
  };

  useEffect(() => {
    clearRecords();
    if (workspaceId) loadRecords(workspaceId);
  }, [workspaceId]);

  useEffect(() => {
    setSourceTargetMessage(null);
    if (!sourceParameterId) return;
    setEnabledKinds((current) => current.includes("parameter")
      ? current
      : ENGINEERING_KINDS.filter((kind) => current.includes(kind) || kind === "parameter"));
    if (parametersState !== "ready" || !workspaceId) return;
    const exact = parameters.find((parameter) => parameter.id === sourceParameterId && parameter.workspace_id === workspaceId);
    if (!exact) {
      setSourceTargetMessage("The linked Parameter is unavailable in the current workspace.");
      return;
    }
    setQuery("");
    setSelectedKey(recordKey({ kind: "parameter", id: exact.id, workspaceId: exact.workspace_id, primary: exact.name, secondary: exact.symbol ?? exact.unit ?? "", status: exact.status, record: exact }));
  }, [sourceParameterId, parametersState, parameters, workspaceId]);

  const projected = useMemo(() => projectEngineeringData({ modelSpecs, assumptions, parameters, decisions }), [modelSpecs, assumptions, parameters, decisions]);
  const visible = useMemo(() => visibleEngineeringRecords(projected, query, enabledKinds), [projected, query, enabledKinds]);
  useEffect(() => setSelectedKey((current) => chooseEngineeringSelection(current, visible)), [visible]);
  const selected = useMemo(() => visible.find((row) => recordKey(row) === selectedKey) ?? null, [visible, selectedKey]);

  const toggleKind = (kind: EngineeringKind) => setEnabledKinds((current) => current.includes(kind) ? current.filter((value) => value !== kind) : ENGINEERING_KINDS.filter((value) => current.includes(value) || value === kind));
  const anyLoading = [modelSpecsState, assumptionsState, parametersState, decisionsState].some((state) => state === "loading");

  if (workspaceState === "loading") return <section className="engineering-data-empty"><h1>Engineering Data</h1><p>Loading workspaces…</p></section>;
  if (workspaceState === "error") return <section className="engineering-data-empty"><h1>Engineering Data</h1><p>Workspace discovery failed: {workspaceError}</p><button type="button" onClick={loadWorkspaces}>Retry</button></section>;
  if (workspaces.length === 0) return <section className="engineering-data-empty"><h1>Engineering Data</h1><p>No workspaces are available.</p></section>;

  return (
    <section className="engineering-data" aria-labelledby="engineering-data-title">
      <header className="engineering-data__toolbar">
        <div><p className="eyebrow">Canonical records</p><h1 id="engineering-data-title">Engineering Data</h1></div>
        <label>Workspace<select value={workspaceId ?? ""} onChange={(event) => requestWorkspaceChange(event.target.value || null)}>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}</select></label>
        <button type="button" disabled={!workspaceId || anyLoading} onClick={() => workspaceId && loadRecords(workspaceId)}>Refresh</button>
      </header>

      <div className="engineering-data__controls">
        <label className="engineering-data__search">Search<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Canonical record fields" /></label>
        <fieldset><legend>Record kinds</legend>{ENGINEERING_KINDS.map((kind) => <label key={kind}><input type="checkbox" checked={enabledKinds.includes(kind)} onChange={() => toggleKind(kind)} />{KIND_LABEL[kind]}</label>)}</fieldset>
      </div>

      <KindFailures rows={[
        ["Model specs", modelSpecsState, modelSpecsError],
        ["Assumptions", assumptionsState, assumptionsError],
        ["Parameters", parametersState, parametersError],
        ["Decisions", decisionsState, decisionsError],
      ]} />
      {sourceTargetMessage ? <div className="engineering-data__failures" role="status"><p><strong>Linked source unavailable.</strong> {sourceTargetMessage}</p></div> : null}

      <div className="engineering-data__grid">
        <div className="engineering-data__list" aria-label="Engineering records">
          {anyLoading && projected.length === 0 && <p>Loading engineering records…</p>}
          {!anyLoading && projected.length === 0 && ![modelSpecsState, assumptionsState, parametersState, decisionsState].includes("error") && <p>No supported engineering records</p>}
          {projected.length > 0 && visible.length === 0 && <p>No records match the current search and kind filters.</p>}
          {visible.map((row) => <button type="button" key={recordKey(row)} className={recordKey(row) === selectedKey ? "engineering-record is-selected" : "engineering-record"} aria-pressed={recordKey(row) === selectedKey} onClick={() => setSelectedKey(recordKey(row))}><span className="engineering-record__kind">{KIND_LABEL[row.kind]}</span><span className="engineering-record__body"><strong>{shown(row.primary)}</strong><small>{shown(row.secondary)}</small></span><span className="engineering-record__status">{row.status}</span></button>)}
        </div>
        <aside className="engineering-data__inspector" aria-label="Selected engineering record">
          {selected ? <Inspector record={selected} /> : <p>Select a visible engineering record.</p>}
        </aside>
      </div>

      <nav className="engineering-data__links" aria-label="Related engineering surfaces">
        <AppLink href="/design/flowsheet" navigate={navigate}>Open lineage</AppLink>
        <AppLink href="/runs" navigate={navigate}>Open runs</AppLink>
        <AppLink href="/legacy/domain-foundation" navigate={navigate}>Open legacy Domain Foundation</AppLink>
      </nav>
    </section>
  );
}

function KindFailures({ rows }: { rows: Array<[string, LoadState, string | null]> }) {
  const failures = rows.filter(([, state]) => state === "error");
  if (failures.length === 0) return null;
  return <div className="engineering-data__failures" aria-label="Partial data failures">{failures.map(([label, , error]) => <p key={label}><strong>{label} unavailable.</strong> {error}</p>)}</div>;
}

function Inspector({ record }: { record: EngineeringRecordProjection }) {
  return <div className="engineering-inspector"><header><p className="eyebrow">{KIND_LABEL[record.kind]}</p><h2>{shown(record.primary)}</h2><p className="technical-token">{record.id}</p></header><dl><Fact label="Status" value={record.status} /><Fact label="Workspace id" value={record.workspaceId} /><Fact label="Freshness" value="Unavailable" />{record.kind === "model-spec" && <><Fact label="Engineering question" value={record.record.engineering_question} /><Fact label="Scope" value={record.record.scope} /><Fact label="Maturity status" value={record.record.maturity_status} /><Fact label="Schema version" value={record.record.schema_version} /><Fact label="Created" value={record.record.created_at} /><Fact label="Updated" value={record.record.updated_at} /></>}{record.kind === "assumption" && <><Fact label="Statement" value={record.record.statement} /><Fact label="Confidence (persisted)" value={record.record.confidence} /></>}{record.kind === "parameter" && <><Fact label="Name" value={record.record.name} /><Fact label="Symbol" value={record.record.symbol} /><Fact label="Value (persisted text)" value={record.record.value} /><Fact label="Unit (persisted)" value={record.record.unit} /></>}{record.kind === "decision" && <><Fact label="Title" value={record.record.title} /><Fact label="Decision" value={record.record.decision_text} /></>}</dl></div>;
}

function Fact({ label, value }: { label: string; value: string | number | null | undefined }) {
  return <div><dt>{label}</dt><dd>{shown(value)}</dd></div>;
}

export default EngineeringData;