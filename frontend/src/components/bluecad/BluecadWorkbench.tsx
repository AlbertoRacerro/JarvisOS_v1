import { type FormEvent, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { StageSelection } from "../../app/selection";
import {
  archiveBluecadCandidate,
  bluecadArtifactContentUrl,
  createBluecadCandidate,
  getBluecadArtifactJson,
  getBluecadCandidateAggregate,
  listBluecadCandidates,
  listWorkspaces,
  promoteBluecadCandidate,
  type BluecadCandidate,
  type BluecadCandidateAggregateRead,
  type BluecadValidationCheck,
  type Workspace
} from "../../api/client";
import type { ShellRegion, ShellRegionContributions } from "../../stages/registry";
import BluecadGlbViewer from "../BluecadGlbViewer";
import {
  acceptsRequest,
  duplicateBrief,
  revalidateSelection,
  type RequestContext
} from "./workbenchState";

type ValidationReport = {
  checks?: BluecadValidationCheck[];
  validation?: { checks?: BluecadValidationCheck[] };
};

type Props = Readonly<{
  onSelectionChange(next: StageSelection | null): void;
  onShellRegionsChange(next: ShellRegionContributions): void;
  requestShellRegionOpen(region: ShellRegion): void;
}>;

type LoadState = "idle" | "loading" | "ready" | "error";

function BluecadWorkbench({ onSelectionChange, onShellRegionsChange, requestShellRegionOpen }: Props) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [workspaceState, setWorkspaceState] = useState<LoadState>("loading");
  const [candidates, setCandidates] = useState<BluecadCandidate[]>([]);
  const [candidateState, setCandidateState] = useState<LoadState>("idle");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [aggregate, setAggregate] = useState<BluecadCandidateAggregateRead | null>(null);
  const [aggregateState, setAggregateState] = useState<LoadState>("idle");
  const [checks, setChecks] = useState<BluecadValidationCheck[]>([]);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const [filterText, setFilterText] = useState("");
  const [briefText, setBriefText] = useState("");
  const [pendingAction, setPendingAction] = useState<"create" | "archive" | "promote" | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const listGeneration = useRef(0);
  const detailGeneration = useRef(0);
  const validationGeneration = useRef(0);
  const currentList = useRef<RequestContext | null>(null);
  const currentDetail = useRef<RequestContext | null>(null);
  const currentValidation = useRef<RequestContext | null>(null);
  const briefRef = useRef<HTMLTextAreaElement | null>(null);
  const candidateRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const focusAfterSelectionChange = useRef(false);

  const visibleCandidates = useMemo(() => {
    const query = filterText.trim().toLowerCase();
    return candidates.filter((candidate) => {
      if (!showArchived && candidate.status === "archived") return false;
      return !query || candidate.id.toLowerCase().includes(query) || candidate.brief_text.toLowerCase().includes(query);
    });
  }, [candidates, filterText, showArchived]);

  const selected = useMemo(
    () => visibleCandidates.find((candidate) => candidate.id === selectedId) ?? null,
    [selectedId, visibleCandidates]
  );

  const publishSelection = useCallback((nextWorkspaceId: string, nextCandidateId: string | null) => {
    onSelectionChange(nextWorkspaceId && nextCandidateId ? {
      kind: "record",
      ref: { resource: "bluecad-candidate", workspaceId: nextWorkspaceId, recordId: nextCandidateId }
    } : null);
  }, [onSelectionChange]);

  const chooseCandidate = useCallback((candidateId: string | null) => {
    setSelectedId(candidateId);
    publishSelection(workspaceId, candidateId);
  }, [publishSelection, workspaceId]);

  const loadCandidates = useCallback(async (targetWorkspaceId: string, preferredId: string | null) => {
    const request: RequestContext = {
      generation: ++listGeneration.current,
      workspaceId: targetWorkspaceId,
      candidateId: preferredId
    };
    currentList.current = request;
    setCandidateState("loading");
    try {
      const items = await listBluecadCandidates(targetWorkspaceId);
      if (!currentList.current || !acceptsRequest(currentList.current, request)) return items;
      setCandidates(items);
      const nextId = revalidateSelection(items, preferredId, showArchived);
      setSelectedId(nextId);
      publishSelection(targetWorkspaceId, nextId);
      setCandidateState("ready");
      return items;
    } catch (error) {
      if (currentList.current && acceptsRequest(currentList.current, request)) {
        setCandidateState("error");
        setMessage(error instanceof Error ? error.message : "Candidate discovery failed.");
      }
      return [];
    }
  }, [publishSelection, showArchived]);

  const loadAggregate = useCallback(async (targetWorkspaceId: string, candidateId: string) => {
    const request: RequestContext = {
      generation: ++detailGeneration.current,
      workspaceId: targetWorkspaceId,
      candidateId
    };
    currentDetail.current = request;
    setAggregateState("loading");
    try {
      const next = await getBluecadCandidateAggregate(targetWorkspaceId, candidateId);
      if (!currentDetail.current || !acceptsRequest(currentDetail.current, request)) return null;
      setAggregate(next);
      setAggregateState("ready");
      return next;
    } catch (error) {
      if (currentDetail.current && acceptsRequest(currentDetail.current, request)) {
        setAggregate(null);
        setAggregateState("error");
        setMessage(error instanceof Error ? error.message : "Candidate detail unavailable.");
      }
      return null;
    }
  }, []);

  const loadValidation = useCallback(async (candidate: BluecadCandidate) => {
    const request: RequestContext = {
      generation: ++validationGeneration.current,
      workspaceId: candidate.workspace_id,
      candidateId: candidate.id,
      artifactId: candidate.report_artifact_id ?? null
    };
    currentValidation.current = request;
    setChecks([]);
    setValidationMessage(null);
    if (!candidate.report_artifact_id) return;
    try {
      const report = await getBluecadArtifactJson<ValidationReport>(candidate.workspace_id, candidate.report_artifact_id);
      if (!currentValidation.current || !acceptsRequest(currentValidation.current, request)) return;
      setChecks(report.checks ?? report.validation?.checks ?? []);
    } catch (error) {
      if (!currentValidation.current || !acceptsRequest(currentValidation.current, request)) return;
      setValidationMessage(error instanceof Error ? error.message : "Validation report unavailable.");
    }
  }, []);

  useEffect(() => {
    let active = true;
    listWorkspaces().then((items) => {
      if (!active) return;
      setWorkspaces(items);
      setWorkspaceState("ready");
      setWorkspaceId(items[0]?.id ?? "");
    }).catch((error: Error) => {
      if (!active) return;
      setWorkspaceState("error");
      setMessage(`Workspace discovery failed: ${error.message}`);
    });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!workspaceId) {
      setCandidates([]);
      chooseCandidate(null);
      return;
    }
    setCandidates([]);
    setAggregate(null);
    chooseCandidate(null);
    void loadCandidates(workspaceId, null);
  }, [chooseCandidate, loadCandidates, workspaceId]);

  useEffect(() => {
    if (!workspaceId || !selectedId) {
      setAggregate(null);
      setAggregateState("idle");
      return;
    }
    void loadAggregate(workspaceId, selectedId);
  }, [loadAggregate, selectedId, workspaceId]);

  useEffect(() => {
    if (aggregate?.candidate && aggregate.candidate.id === selectedId) void loadValidation(aggregate.candidate);
  }, [aggregate, loadValidation, selectedId]);

  useEffect(() => {
    const nextId = revalidateSelection(candidates, selectedId, showArchived);
    if (nextId === selectedId) return;
    focusAfterSelectionChange.current = true;
    chooseCandidate(nextId);
  }, [candidates, chooseCandidate, selectedId, showArchived]);

  useEffect(() => {
    if (!focusAfterSelectionChange.current) return;
    focusAfterSelectionChange.current = false;
    window.requestAnimationFrame(() => {
      if (selectedId) candidateRefs.current[selectedId]?.focus();
    });
  }, [selectedId]);

  const refresh = useCallback(async () => {
    if (!workspaceId) return;
    const items = await loadCandidates(workspaceId, selectedId);
    const nextId = revalidateSelection(items, selectedId, showArchived);
    if (nextId) await loadAggregate(workspaceId, nextId);
  }, [loadAggregate, loadCandidates, selectedId, showArchived, workspaceId]);

  const onCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const brief = briefText.trim();
    if (!brief || !workspaceId || pendingAction) return;
    const startedWorkspace = workspaceId;
    const generation = listGeneration.current;
    setPendingAction("create");
    setMessage(null);
    try {
      const created = await createBluecadCandidate(startedWorkspace, brief);
      if (workspaceId !== startedWorkspace || listGeneration.current !== generation) return;
      const items = await loadCandidates(startedWorkspace, created.id);
      if (workspaceId !== startedWorkspace || !items.some((item) => item.id === created.id)) return;
      setBriefText("");
      chooseCandidate(created.id);
      await loadAggregate(startedWorkspace, created.id);
      setMessage("Candidate created.");
    } catch (error) {
      if (workspaceId === startedWorkspace) setMessage(error instanceof Error ? error.message : "Candidate creation failed.");
    } finally {
      if (workspaceId === startedWorkspace) setPendingAction(null);
    }
  };

  const onArchive = async () => {
    if (!selected || pendingAction) return;
    const startedWorkspace = workspaceId;
    const startedCandidate = selected.id;
    setPendingAction("archive");
    setMessage(null);
    try {
      await archiveBluecadCandidate(startedWorkspace, startedCandidate);
      if (workspaceId !== startedWorkspace || selectedId !== startedCandidate) return;
      focusAfterSelectionChange.current = true;
      await loadCandidates(startedWorkspace, startedCandidate);
      setMessage("Candidate archived.");
    } catch (error) {
      if (workspaceId === startedWorkspace && selectedId === startedCandidate) setMessage(error instanceof Error ? error.message : "Archive failed.");
    } finally {
      if (workspaceId === startedWorkspace) setPendingAction(null);
    }
  };

  const onPromote = async () => {
    if (!selected || pendingAction) return;
    const startedWorkspace = workspaceId;
    const startedCandidate = selected.id;
    setPendingAction("promote");
    setMessage(null);
    try {
      const promoted = await promoteBluecadCandidate(startedWorkspace, startedCandidate);
      if (workspaceId !== startedWorkspace || selectedId !== startedCandidate) return;
      await refresh();
      setMessage(`Promoted to Decision ${promoted.promoted_decision_id ?? "(pending id)"}.`);
    } catch (error) {
      if (workspaceId === startedWorkspace && selectedId === startedCandidate) setMessage(error instanceof Error ? error.message : "Promotion failed.");
    } finally {
      if (workspaceId === startedWorkspace) setPendingAction(null);
    }
  };

  const duplicateSelectedBrief = () => {
    if (!selected) return;
    setBriefText(duplicateBrief(selected.brief_text).briefText);
    requestShellRegionOpen("navigator");
    window.requestAnimationFrame(() => {
      briefRef.current?.scrollIntoView({ block: "nearest" });
      briefRef.current?.focus();
    });
  };

  const navigator = useMemo<ReactNode>(() => (
    <div className="bluecad-workbench__navigator">
      <label>Workspace<select value={workspaceId} onChange={(event) => setWorkspaceId(event.target.value)} disabled={workspaceState !== "ready" || workspaces.length === 0}>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}</select></label>
      <label>Filter candidates<input value={filterText} onChange={(event) => setFilterText(event.target.value)} /></label>
      <label className="checkbox-line"><input type="checkbox" checked={showArchived} onChange={(event) => setShowArchived(event.target.checked)} />Show archived</label>
      <button type="button" className="secondary-button" onClick={() => void refresh()} disabled={!workspaceId || candidateState === "loading"}>Refresh</button>
      <form className="bluecad-new-form" onSubmit={onCreate}><label>New candidate brief<textarea ref={briefRef} value={briefText} onChange={(event) => setBriefText(event.target.value)} required /></label><button type="submit" disabled={!briefText.trim() || pendingAction !== null}>{pendingAction === "create" ? "Creating…" : "New candidate"}</button></form>
      {workspaceState === "loading" && <p>Loading workspaces…</p>}
      {workspaceState === "error" && <p className="error-banner">Workspace discovery failed.</p>}
      {workspaceState === "ready" && workspaces.length === 0 && <p>No workspaces are available.</p>}
      {candidateState === "loading" && <p>Loading candidates…</p>}
      {candidateState === "error" && <p className="error-banner">Candidate discovery failed.</p>}
      <div className="bluecad-candidate-list" aria-label="BLUECAD candidates">{visibleCandidates.map((candidate) => <button key={candidate.id} ref={(node) => { candidateRefs.current[candidate.id] = node; }} type="button" aria-pressed={candidate.id === selectedId} className={candidate.id === selectedId ? "bluecad-candidate active" : "bluecad-candidate"} onClick={() => chooseCandidate(candidate.id)}><span className={`status-pill status-${candidate.status}`}>{candidate.status}</span><strong>{candidate.brief_text.slice(0, 90)}{candidate.brief_text.length > 90 ? "…" : ""}</strong>{candidate.parked_reason && <small>Parked: {candidate.parked_reason}</small>}</button>)}</div>
      {candidateState === "ready" && candidates.length === 0 && <p>No BLUECAD candidates exist in this workspace.</p>}
      {candidateState === "ready" && candidates.length > 0 && visibleCandidates.length === 0 && <p>No candidates match the current filter. Archived candidates may be hidden.</p>}
    </div>
  ), [briefText, candidateState, candidates.length, filterText, pendingAction, refresh, selectedId, showArchived, visibleCandidates, workspaceId, workspaceState, workspaces]);

  const sidecar = useMemo<ReactNode>(() => {
    const candidate = aggregate?.candidate;
    if (!candidate) return <p>{aggregateState === "loading" ? "Loading candidate detail…" : "Select a candidate to inspect canonical detail."}</p>;
    return <div className="bluecad-workbench__sidecar"><h3>Candidate</h3><dl className="details"><div><dt>Lifecycle</dt><dd>{candidate.status}</dd></div><div><dt>Freshness</dt><dd>{aggregate.freshness}</dd></div><div><dt>Promotion</dt><dd>{candidate.promoted_decision_id ?? "Not promoted"}</dd></div></dl>{candidate.parked_reason && <p className="warning-banner">Parked reason: {candidate.parked_reason}</p>}<h3>Validation</h3>{validationMessage ? <p className="error-banner">Validation report unavailable: {validationMessage}</p> : <ReportTable checks={checks} />}<h3>Canonical references</h3><p>{aggregate.artifacts.length} artifacts · {aggregate.evidence.length} evidence refs · {aggregate.runs.length} run refs</p>{aggregate.diagnostics.map((diagnostic, index) => <p className="warning-banner" key={`${diagnostic.code}-${index}`}>{diagnostic.message}</p>)}</div>;
  }, [aggregate, aggregateState, checks, validationMessage]);

  const dock = useMemo<ReactNode>(() => {
    const attempts = aggregate?.candidate.attempts ?? [];
    return <div className="bluecad-workbench__dock"><h3>Attempt history</h3>{attempts.length === 0 ? <p>No attempts recorded yet.</p> : <div className="table-wrap"><table className="smoke-table bluecad-table"><thead><tr><th>#</th><th>Route</th><th>Proposal</th><th>Build</th><th>Validation</th><th>Error detail</th></tr></thead><tbody>{attempts.map((attempt) => <tr key={attempt.id}><td>{attempt.attempt_no}</td><td>{attempt.route_class}</td><td>{attempt.proposal_outcome}</td><td>{attempt.build_outcome ?? "—"}</td><td>{attempt.validation_verdict ?? "—"}</td><td>{formatAttemptDetail(attempt.error_detail_json)}</td></tr>)}</tbody></table></div>}</div>;
  }, [aggregate]);

  useEffect(() => { onShellRegionsChange({ navigator, sidecar, dock }); }, [dock, navigator, onShellRegionsChange, sidecar]);
  useEffect(() => () => onShellRegionsChange({}), [onShellRegionsChange]);

  const candidate = aggregate?.candidate;
  const canPromote = candidate?.status === "valid" && !candidate.promoted_decision_id;

  return <section className="bluecad-workbench" aria-labelledby="bluecad-workbench-title"><header className="bluecad-workbench__chrome"><div><p className="eyebrow">BLUECAD</p><h1 id="bluecad-workbench-title">Model workbench</h1></div>{candidate && <div className="button-row"><span className={`status-pill status-${candidate.status}`}>{candidate.status}</span><button type="button" className="secondary-button" onClick={duplicateSelectedBrief}>Duplicate brief</button>{candidate.status !== "archived" && <button type="button" className="secondary-button" onClick={() => void onArchive()} disabled={pendingAction !== null}>Archive</button>}{canPromote && <button type="button" onClick={() => void onPromote()} disabled={pendingAction !== null}>Promote to Decision</button>}</div>}</header>{message && <div className="error-banner" role="status">{message}</div>}<div className="bluecad-workbench__viewport">{candidate?.glb_artifact_id ? <BluecadGlbViewer artifactUrl={bluecadArtifactContentUrl(candidate.workspace_id, candidate.glb_artifact_id)} /> : candidate ? <div className="bluecad-workbench__empty-viewer"><h2>Geometry unavailable</h2><p>{candidate.parked_reason ? `Candidate is parked: ${candidate.parked_reason}` : "No GLB artifact is available for this candidate yet."}</p></div> : <div className="bluecad-workbench__empty-viewer"><p>{aggregateState === "loading" ? "Loading candidate geometry…" : "Select a candidate from the navigator."}</p></div>}</div></section>;
}

function isRecord(value: unknown): value is Record<string, unknown> { return typeof value === "object" && value !== null && !Array.isArray(value); }
function formatCell(value: unknown): string { if (value === null || value === undefined) return ""; if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value); try { return JSON.stringify(value); } catch { return String(value); } }
function formatPercent(value: unknown): string | null { return typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toPrecision(3)}%` : null; }
function formatValidationDetail(value: unknown): string { if (!isRecord(value)) return formatCell(value); if ("actual" in value && "declared" in value) { const relErr = formatPercent(value.rel_err); const relTol = formatPercent(value.rel_tol); return `actual ${formatCell(value.actual)} vs declared ${formatCell(value.declared)}${relErr ? ` (rel err ${relErr}${relTol ? ` / tol ${relTol}` : ""})` : ""}`; } return Object.entries(value).map(([key, item]) => `${key}: ${formatCell(item)}`).join(" · "); }
function ReportTable({ checks }: { checks: BluecadValidationCheck[] }) { return checks.length === 0 ? <p>No validation checks are available.</p> : <div className="table-wrap"><table className="smoke-table bluecad-table"><thead><tr><th>Check</th><th>Status</th><th>Detail</th></tr></thead><tbody>{checks.map((check, index) => <tr key={`${check.id ?? check.check_id ?? "check"}-${index}`}><td>{check.id ?? check.check_id ?? `check-${index + 1}`}</td><td>{check.status ?? check.verdict ?? "—"}</td><td>{formatValidationDetail(check.detail ?? check.message) || "—"}</td></tr>)}</tbody></table></div>; }
function formatAttemptDetail(value?: string | null): string { if (!value) return "—"; try { return formatCell(JSON.parse(value) as unknown); } catch { return value; } }

export default BluecadWorkbench;
