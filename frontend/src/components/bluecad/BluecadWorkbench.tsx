import { type FormEvent, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { StageSelection } from "../../app/selection";
import {
  API_BASE_URL,
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
  acceptsMutation,
  acceptsRequest,
  duplicateBrief,
  mutationConflicts,
  revalidateSelection,
  type MutationContext,
  type RequestContext
} from "./workbenchState";

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
  const [validationState, setValidationState] = useState<LoadState>("idle");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const [filterText, setFilterText] = useState("");
  const [briefText, setBriefText] = useState("");
  const [pendingAction, setPendingAction] = useState<"create" | "archive" | "promote" | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const listGeneration = useRef(0);
  const detailGeneration = useRef(0);
  const validationGeneration = useRef(0);
  const mutationGeneration = useRef(0);
  const workspaceRef = useRef("");
  const selectedRef = useRef<string | null>(null);
  const showArchivedRef = useRef(showArchived);
  showArchivedRef.current = showArchived;
  const currentList = useRef<RequestContext | null>(null);
  const currentDetail = useRef<RequestContext | null>(null);
  const currentValidation = useRef<RequestContext | null>(null);
  const suppressNextDetailEffect = useRef<string | null>(null);
  const briefRef = useRef<HTMLTextAreaElement | null>(null);
  const focusBriefOnMount = useRef(false);
  const filterRef = useRef<HTMLInputElement | null>(null);
  const candidateRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const emptyCandidatesRef = useRef<HTMLParagraphElement | null>(null);
  const workbenchTitleRef = useRef<HTMLHeadingElement | null>(null);
  const focusAfterSelectionChange = useRef(false);

  const handleBriefRef = useCallback((node: HTMLTextAreaElement | null) => {
    briefRef.current = node;
    if (!node || !focusBriefOnMount.current) return;
    focusBriefOnMount.current = false;
    node.scrollIntoView({ block: "nearest" });
    node.focus();
  }, []);

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

  const clearVisibleDetail = useCallback((nextState: LoadState) => {
    setAggregate(null);
    setAggregateState(nextState);
    setChecks([]);
    setValidationState("idle");
    setValidationMessage(null);
  }, []);

  const chooseCandidate = useCallback((candidateId: string | null) => {
    mutationGeneration.current += 1;
    selectedRef.current = candidateId;
    if (currentList.current) setCandidateState("ready");
    currentList.current = null;
    currentDetail.current = null;
    currentValidation.current = null;
    suppressNextDetailEffect.current = null;
    clearVisibleDetail(candidateId ? "loading" : "idle");
    setMessage(null);
    setSelectedId(candidateId);
    publishSelection(workspaceRef.current, candidateId);
  }, [clearVisibleDetail, publishSelection]);

  const loadCandidates = useCallback(async (
    targetWorkspaceId: string,
    preferredId: string | null,
    suppressDetailEffect = false
  ) => {
    const request: RequestContext = {
      generation: ++listGeneration.current,
      workspaceId: targetWorkspaceId,
      candidateId: preferredId
    };
    currentList.current = request;
    setCandidateState("loading");
    try {
      const items = await listBluecadCandidates(targetWorkspaceId);
      if (!currentList.current || !acceptsRequest(currentList.current, request)) return null;
      setCandidates(items);
      const nextId = revalidateSelection(items, preferredId, showArchivedRef.current);
      selectedRef.current = nextId;
      currentDetail.current = null;
      currentValidation.current = null;
      clearVisibleDetail(nextId ? "loading" : "idle");
      setMessage(null);
      if (suppressDetailEffect && nextId) suppressNextDetailEffect.current = nextId;
      setSelectedId(nextId);
      publishSelection(targetWorkspaceId, nextId);
      setCandidateState("ready");
      return items;
    } catch (error) {
      if (currentList.current && acceptsRequest(currentList.current, request)) {
        currentList.current = null;
        currentDetail.current = null;
        currentValidation.current = null;
        setCandidates([]);
        selectedRef.current = null;
        clearVisibleDetail("idle");
        setSelectedId(null);
        publishSelection(targetWorkspaceId, null);
        setCandidateState("error");
        setMessage(error instanceof Error ? error.message : "Candidate discovery failed.");
      }
      return null;
    }
  }, [clearVisibleDetail, publishSelection]);

  const loadAggregate = useCallback(async (targetWorkspaceId: string, candidateId: string) => {
    const request: RequestContext = {
      generation: ++detailGeneration.current,
      workspaceId: targetWorkspaceId,
      candidateId
    };
    currentDetail.current = request;
    setAggregate(null);
    setAggregateState("loading");
    try {
      const next = await getBluecadCandidateAggregate(targetWorkspaceId, candidateId);
      if (!currentDetail.current || !acceptsRequest(currentDetail.current, request)) return null;
      setAggregate(next);
      setAggregateState("ready");
      return next;
    } catch (error) {
      if (currentDetail.current && acceptsRequest(currentDetail.current, request)) {
        if (error instanceof Error && error.message === "Request failed with 404") {
          currentDetail.current = null;
          const items = await loadCandidates(targetWorkspaceId, candidateId);
          if (items && workspaceRef.current === targetWorkspaceId && selectedRef.current === candidateId) {
            setAggregate(null);
            setAggregateState("error");
            setMessage("Candidate detail unavailable. Use Refresh to retry.");
          }
          return null;
        }
        setAggregate(null);
        setAggregateState("error");
        setMessage(error instanceof Error ? error.message : "Candidate detail unavailable.");
      }
      return null;
    }
  }, [loadCandidates]);

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
    if (!candidate.report_artifact_id) {
      setValidationState("ready");
      return;
    }
    setValidationState("loading");
    try {
      const report = await getBluecadArtifactJson<unknown>(candidate.workspace_id, candidate.report_artifact_id);
      if (!currentValidation.current || !acceptsRequest(currentValidation.current, request)) return;
      if (!isRecord(report)) throw new Error("Validation report has an invalid shape.");
      const nestedValidation = isRecord(report.validation) ? report.validation : null;
      const reportChecks = report.checks ?? nestedValidation?.checks;
      if (reportChecks !== undefined && (!Array.isArray(reportChecks) || !reportChecks.every(isValidationCheck))) {
        throw new Error("Validation report checks have an invalid shape.");
      }
      setChecks(reportChecks ?? []);
      setValidationState("ready");
    } catch (error) {
      if (!currentValidation.current || !acceptsRequest(currentValidation.current, request)) return;
      setValidationState("error");
      setValidationMessage(error instanceof Error ? error.message : "Validation report unavailable.");
    }
  }, []);

  useEffect(() => {
    let active = true;
    listWorkspaces().then((items) => {
      if (!active) return;
      const firstWorkspaceId = items[0]?.id ?? "";
      workspaceRef.current = firstWorkspaceId;
      selectedRef.current = null;
      setWorkspaces(items);
      setWorkspaceState("ready");
      setWorkspaceId(firstWorkspaceId);
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
    chooseCandidate(null);
    void loadCandidates(workspaceId, null);
  }, [chooseCandidate, loadCandidates, workspaceId]);

  useEffect(() => {
    if (!workspaceId || !selectedId) {
      clearVisibleDetail("idle");
      return;
    }
    if (suppressNextDetailEffect.current === selectedId) {
      suppressNextDetailEffect.current = null;
      return;
    }
    void loadAggregate(workspaceId, selectedId);
  }, [clearVisibleDetail, loadAggregate, selectedId, workspaceId]);

  useEffect(() => {
    if (aggregate?.candidate && aggregate.candidate.id === selectedId) void loadValidation(aggregate.candidate);
  }, [aggregate, loadValidation, selectedId]);

  useEffect(() => {
    const nextId = revalidateSelection(visibleCandidates, selectedId, true);
    if (nextId === selectedId) return;
    focusAfterSelectionChange.current = Boolean(selectedId && document.activeElement === candidateRefs.current[selectedId]);
    chooseCandidate(nextId);
  }, [chooseCandidate, selectedId, visibleCandidates]);

  useEffect(() => {
    if (!focusAfterSelectionChange.current) return;
    focusAfterSelectionChange.current = false;
    window.requestAnimationFrame(() => {
      if (selectedId) candidateRefs.current[selectedId]?.focus();
      else emptyCandidatesRef.current?.focus();
    });
  }, [selectedId]);

  const refresh = useCallback(async () => {
    if (!workspaceId) return false;
    currentDetail.current = null;
    currentValidation.current = null;
    clearVisibleDetail("loading");
    const items = await loadCandidates(workspaceId, selectedId, true);
    if (!items) return false;
    const nextId = revalidateSelection(items, selectedId, showArchivedRef.current);
    if (!nextId) return false;
    const detail = await loadAggregate(workspaceId, nextId);
    return detail !== null;
  }, [clearVisibleDetail, loadAggregate, loadCandidates, selectedId, workspaceId]);

  const onCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const brief = briefText.trim();
    if (!brief || !workspaceId || mutationConflicts(pendingAction, "create")) return;
    const mutation: MutationContext = {
      generation: ++mutationGeneration.current,
      workspaceId: workspaceRef.current,
      candidateId: selectedRef.current,
      kind: "create"
    };
    setPendingAction("create");
    setMessage(null);
    try {
      const created = await createBluecadCandidate(mutation.workspaceId, brief);
      if (!acceptsMutation({ generation: mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selectedRef.current }, mutation)) return;
      setFilterText("");
      suppressNextDetailEffect.current = created.id;
      const items = await loadCandidates(mutation.workspaceId, created.id);
      if (!items || !items.some((item) => item.id === created.id)) {
        suppressNextDetailEffect.current = null;
        return;
      }
      setBriefText("");
      const detail = await loadAggregate(mutation.workspaceId, created.id);
      if (!detail || workspaceRef.current !== mutation.workspaceId || selectedRef.current !== created.id) return;
      setMessage("Candidate created.");
    } catch (error) {
      suppressNextDetailEffect.current = null;
      if (acceptsMutation({ generation: mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selectedRef.current }, mutation)) setMessage(error instanceof Error ? error.message : "Candidate creation failed.");
    } finally {
      setPendingAction(null);
    }
  };

  const onArchive = async () => {
    if (!selected || mutationConflicts(pendingAction, "archive")) return;
    const mutation: MutationContext = { generation: ++mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selected.id, kind: "archive" };
    setPendingAction("archive");
    setMessage(null);
    try {
      await archiveBluecadCandidate(mutation.workspaceId, mutation.candidateId!);
      if (!acceptsMutation({ generation: mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selectedRef.current }, mutation)) return;
      const items = await loadCandidates(mutation.workspaceId, mutation.candidateId ?? null);
      if (!items || workspaceRef.current !== mutation.workspaceId) return;
      window.requestAnimationFrame(() => {
        const nextId = selectedRef.current;
        const candidateNode = nextId ? candidateRefs.current[nextId] : null;
        (candidateNode ?? emptyCandidatesRef.current ?? workbenchTitleRef.current)?.focus();
      });
      if (selectedRef.current === mutation.candidateId) void loadAggregate(mutation.workspaceId, mutation.candidateId!);
      setMessage("Candidate archived.");
    } catch (error) {
      if (acceptsMutation({ generation: mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selectedRef.current }, mutation)) setMessage(error instanceof Error ? error.message : "Archive failed.");
    } finally {
      setPendingAction(null);
    }
  };

  const onPromote = async () => {
    if (!selected || mutationConflicts(pendingAction, "promote")) return;
    const mutation: MutationContext = { generation: ++mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selected.id, kind: "promote" };
    setPendingAction("promote");
    setMessage(null);
    try {
      const promoted = await promoteBluecadCandidate(mutation.workspaceId, mutation.candidateId!);
      if (!acceptsMutation({ generation: mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selectedRef.current }, mutation)) return;
      const refreshed = await refresh();
      if (!refreshed || workspaceRef.current !== mutation.workspaceId || selectedRef.current !== mutation.candidateId) return;
      window.requestAnimationFrame(() => {
        const candidateNode = candidateRefs.current[mutation.candidateId!];
        (candidateNode ?? workbenchTitleRef.current)?.focus();
      });
      setMessage(`Promoted to Decision ${promoted.promoted_decision_id ?? "(pending id)"}.`);
    } catch (error) {
      if (acceptsMutation({ generation: mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selectedRef.current }, mutation)) setMessage(error instanceof Error ? error.message : "Promotion failed.");
    } finally {
      setPendingAction(null);
    }
  };

  const duplicateSelectedBrief = () => {
    if (!selected) return;
    setBriefText(duplicateBrief(selected.brief_text).briefText);
    const briefNode = briefRef.current;
    if (briefNode) {
      briefNode.scrollIntoView({ block: "nearest" });
      briefNode.focus();
      return;
    }
    focusBriefOnMount.current = true;
    requestShellRegionOpen("navigator");
  };

  const navigator = useMemo<ReactNode>(() => (
    <div className="bluecad-workbench__navigator">
      <label>Workspace<select value={workspaceId} onChange={(event) => {
        const nextWorkspaceId = event.target.value;
        mutationGeneration.current += 1;
        workspaceRef.current = nextWorkspaceId;
        selectedRef.current = null;
        currentList.current = null;
        currentDetail.current = null;
        currentValidation.current = null;
        suppressNextDetailEffect.current = null;
        clearVisibleDetail("idle");
        setMessage(null);
        setWorkspaceId(nextWorkspaceId);
      }} disabled={workspaceState !== "ready" || workspaces.length === 0} style={{ width: "100%", minWidth: 0, maxWidth: "100%" }}>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}</select></label>
      <label>Filter candidates<input ref={filterRef} value={filterText} onChange={(event) => setFilterText(event.target.value)} disabled={candidateState === "loading"} /></label>
      <label className="checkbox-line"><input type="checkbox" checked={showArchived} onChange={(event) => setShowArchived(event.target.checked)} disabled={candidateState === "loading"} />Show archived</label>
      <button type="button" className="secondary-button" onClick={() => void refresh()} disabled={!workspaceId || candidateState === "loading" || pendingAction !== null}>Refresh</button>
      <form className="bluecad-new-form" onSubmit={onCreate}><label>New candidate brief<textarea ref={handleBriefRef} value={briefText} onChange={(event) => setBriefText(event.target.value)} required /></label><button type="submit" disabled={!workspaceId || !briefText.trim() || pendingAction !== null}>{pendingAction === "create" ? "Creating…" : "New candidate"}</button></form>
      {workspaceState === "loading" && <p>Loading workspaces…</p>}
      {workspaceState === "error" && <p className="error-banner">Workspace discovery failed.</p>}
      {workspaceState === "ready" && workspaces.length === 0 && <p>No workspaces are available.</p>}
      {candidateState === "loading" && <p>Loading candidates…</p>}
      {candidateState === "error" && <p className="error-banner">Candidate discovery failed.</p>}
      <div className="bluecad-candidate-list" aria-label="BLUECAD candidates">{visibleCandidates.map((candidate) => <button key={candidate.id} ref={(node) => { candidateRefs.current[candidate.id] = node; }} type="button" aria-pressed={candidate.id === selectedId} className={candidate.id === selectedId ? "bluecad-candidate active" : "bluecad-candidate"} onClick={() => chooseCandidate(candidate.id)} disabled={candidateState === "loading"}><span className={`status-pill status-${candidate.status}`}>{candidate.status}</span><strong>{candidate.brief_text.slice(0, 90)}{candidate.brief_text.length > 90 ? "…" : ""}</strong>{candidate.parked_reason && <small>Parked: {candidate.parked_reason}</small>}</button>)}</div>
      {candidateState === "ready" && candidates.length === 0 && <p ref={emptyCandidatesRef} tabIndex={-1}>No BLUECAD candidates exist in this workspace.</p>}
      {candidateState === "ready" && candidates.length > 0 && visibleCandidates.length === 0 && <p ref={emptyCandidatesRef} tabIndex={-1}>No candidates match the current filter. Archived candidates may be hidden.</p>}
    </div>
  ), [briefText, candidateState, candidates.length, clearVisibleDetail, filterText, handleBriefRef, pendingAction, refresh, selectedId, showArchived, visibleCandidates, workspaceId, workspaceState, workspaces]);

  const sidecar = useMemo<ReactNode>(() => {
    const candidate = aggregate?.candidate;
    if (!candidate || candidate.id !== selectedId) {
      if (selectedId && aggregateState === "error") return <p className="error-banner">Candidate detail unavailable. Use Refresh to retry.</p>;
      return <p>{aggregateState === "loading" ? "Loading candidate detail…" : "Select a candidate to inspect canonical detail."}</p>;
    }
    const validation = !candidate.report_artifact_id
      ? <p>No validation report is available.</p>
      : validationState === "loading"
        ? <p>Loading validation report…</p>
        : validationState === "error" || validationMessage
          ? <p className="error-banner">Validation report unavailable: {validationMessage ?? "Request failed."}</p>
          : <ReportTable checks={checks} />;
    return <div className="bluecad-workbench__sidecar"><h3>Candidate</h3><dl className="details"><div><dt>Lifecycle</dt><dd>{candidate.status}</dd></div><div><dt>Freshness</dt><dd>{aggregate.freshness}</dd></div><div><dt>Promotion</dt><dd>{candidate.promoted_decision_id ?? "Not promoted"}</dd></div></dl>{candidate.parked_reason && <p className="warning-banner">Parked reason: {candidate.parked_reason}</p>}<h3>Validation</h3>{validation}<h3>Artifacts</h3>{aggregate.artifacts.length === 0 ? <p>No aggregate-linked artifacts.</p> : <ul>{aggregate.artifacts.map((artifact) => <li key={artifact.id}><a href={`${API_BASE_URL}${artifact.content_url}`}>{artifact.filename}</a> · {artifact.roles.join(", ")} · {artifact.status}</li>)}</ul>}<h3>Canonical references</h3><p>{aggregate.evidence.length} evidence refs · {aggregate.runs.length} run refs</p>{aggregate.diagnostics.map((diagnostic, index) => <p className="warning-banner" key={`${diagnostic.code}-${index}`}>{diagnostic.message}</p>)}</div>;
  }, [aggregate, aggregateState, checks, selectedId, validationMessage, validationState]);

  const dock = useMemo<ReactNode>(() => {
    const activeAggregate = aggregate?.candidate.id === selectedId ? aggregate : null;
    const attempts = activeAggregate?.candidate.attempts ?? [];
    const evidence = activeAggregate?.evidence ?? [];
    const runs = activeAggregate?.runs ?? [];
    return <div className="bluecad-workbench__dock"><h3>Attempt history</h3>{attempts.length === 0 ? <p>No attempts recorded yet.</p> : <div className="table-wrap"><table className="smoke-table bluecad-table"><thead><tr><th>#</th><th>Route</th><th>Proposal</th><th>Build</th><th>Validation</th><th>Error detail</th></tr></thead><tbody>{attempts.map((attempt) => <tr key={attempt.id}><td>{attempt.attempt_no}</td><td>{attempt.route_class}</td><td>{attempt.proposal_outcome}</td><td>{attempt.build_outcome ?? "—"}</td><td>{attempt.validation_verdict ?? "—"}</td><td>{formatAttemptDetail(attempt.error_detail_json)}</td></tr>)}</tbody></table></div>}<h3>Evidence references</h3>{evidence.length === 0 ? <p>No aggregate-linked evidence.</p> : <ul>{evidence.map((item) => <li key={`${item.subject_ref}-${item.ref}`}><strong>{item.kind}</strong> · {item.ref} · subject {item.subject_ref} · {item.status}{item.summary ? ` · ${item.summary}` : ""}</li>)}</ul>}<h3>Run references</h3>{runs.length === 0 ? <p>No aggregate-linked runs.</p> : <ul>{runs.map((run) => <li key={`${run.source_ref ?? "direct"}-${run.ref}`}><strong>{run.kind}</strong> · {run.ref}{run.source_ref ? ` · source ${run.source_ref}` : ""}{run.status ? ` · ${run.status}` : ""}{run.stale === true ? " · stale" : ""}</li>)}</ul>}</div>;
  }, [aggregate, selectedId]);

  useEffect(() => { onShellRegionsChange({ navigator, sidecar, dock }); }, [dock, navigator, onShellRegionsChange, sidecar]);
  useEffect(() => () => {
    currentList.current = null;
    currentDetail.current = null;
    currentValidation.current = null;
    suppressNextDetailEffect.current = null;
    mutationGeneration.current += 1;
    onShellRegionsChange({});
  }, [onShellRegionsChange]);

  const candidate = aggregate?.candidate.id === selectedId ? aggregate.candidate : null;
  const canPromote = candidate?.status === "valid" && !candidate.promoted_decision_id;
  const viewportFallback = selectedId && aggregateState === "error" ? "Candidate detail unavailable. Use Refresh to retry." : aggregateState === "loading" ? "Loading candidate geometry…" : "Select a candidate from the navigator.";

  return <section className="bluecad-workbench" aria-labelledby="bluecad-workbench-title"><header className="bluecad-workbench__chrome"><div><p className="eyebrow">BLUECAD</p><h1 id="bluecad-workbench-title" ref={workbenchTitleRef} tabIndex={-1}>Model workbench</h1>{candidate && <p className="panel-subtitle" style={{ overflowWrap: "anywhere", minWidth: 0 }}><strong>{candidate.id}</strong> · {candidate.brief_text}</p>}</div>{candidate && <div className="button-row"><span className={`status-pill status-${candidate.status}`}>{candidate.status}</span><button type="button" className="secondary-button" onClick={duplicateSelectedBrief}>Duplicate brief</button>{candidate.status !== "archived" && <button type="button" className="secondary-button" onClick={() => void onArchive()} disabled={pendingAction !== null}>Archive</button>}{canPromote && <button type="button" onClick={() => void onPromote()} disabled={pendingAction !== null}>Promote to Decision</button>}</div>}</header>{message && <div className="panel-subtitle" role="status">{message}</div>}<div className="bluecad-workbench__viewport">{candidate?.glb_artifact_id ? <BluecadGlbViewer artifactUrl={bluecadArtifactContentUrl(candidate.workspace_id, candidate.glb_artifact_id)} /> : candidate ? <div className="bluecad-workbench__empty-viewer"><h2>Geometry unavailable</h2><p>{candidate.parked_reason ? `Candidate is parked: ${candidate.parked_reason}` : "No GLB artifact is available for this candidate yet."}</p></div> : <div className="bluecad-workbench__empty-viewer"><p>{viewportFallback}</p></div>}</div></section>;
}

function isRecord(value: unknown): value is Record<string, unknown> { return typeof value === "object" && value !== null && !Array.isArray(value); }
function isValidationCheck(value: unknown): value is BluecadValidationCheck {
  if (!isRecord(value)) return false;
  const optionalString = (field: unknown) => field === undefined || typeof field === "string";
  const tier = value.tier;
  const hint = value.hint;
  return optionalString(value.id)
    && optionalString(value.check_id)
    && (tier === undefined || typeof tier === "string" || typeof tier === "number")
    && optionalString(value.status)
    && optionalString(value.verdict)
    && (hint === undefined || hint === null || typeof hint === "string");
}
function formatCell(value: unknown): string { if (value === null || value === undefined) return ""; if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value); try { return JSON.stringify(value); } catch { return String(value); } }
function formatPercent(value: unknown): string | null { return typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toPrecision(3)}%` : null; }
function formatValidationDetail(value: unknown): string { if (!isRecord(value)) return formatCell(value); if ("actual" in value && "declared" in value) { const relErr = formatPercent(value.rel_err); const relTol = formatPercent(value.rel_tol); return `actual ${formatCell(value.actual)} vs declared ${formatCell(value.declared)}${relErr ? ` (rel err ${relErr}${relTol ? ` / tol ${relTol}` : ""})` : ""}`; } return Object.entries(value).map(([key, item]) => `${key}: ${formatCell(item)}`).join(" · "); }
function ReportTable({ checks }: { checks: BluecadValidationCheck[] }) { return checks.length === 0 ? <p>No validation checks are available.</p> : <div className="table-wrap"><table className="smoke-table bluecad-table"><thead><tr><th>Check</th><th>Tier</th><th>Status</th><th>Detail</th><th>Hint</th></tr></thead><tbody>{checks.map((check, index) => <tr key={`${check.id ?? check.check_id ?? "check"}-${index}`}><td>{check.id ?? check.check_id ?? `check-${index + 1}`}</td><td>{check.tier ?? "—"}</td><td>{check.status ?? check.verdict ?? "—"}</td><td>{formatValidationDetail(check.detail ?? check.message) || "—"}</td><td>{check.hint ?? "—"}</td></tr>)}</tbody></table></div>; }
function formatAttemptDetail(value?: string | null): string { if (!value) return "—"; try { return formatCell(JSON.parse(value) as unknown); } catch { return value; } }

export default BluecadWorkbench;