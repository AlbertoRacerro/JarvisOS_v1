import { type FormEvent, type ReactNode, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import type { StageSelection } from "../../app/selection";
import {
  API_BASE_URL,
  archiveBluecadCandidate,
  bluecadArtifactContentUrl,
  createBluecadCandidate,
  createBluecadTemplateCandidate,
  getBluecadArtifactJson,
  getBluecadCandidateAggregate,
  getBluecadGenerationAvailability,
  listBluecadCandidates,
  listWorkspaces,
  promoteBluecadCandidate,
  type BluecadCandidate,
  type BluecadArtifactRefRead,
  type BluecadCandidateAggregateRead,
  type BluecadGenerationAvailability,
  type BluecadTemplateCreate,
  type BluecadValidationCheck,
  type Workspace
} from "../../api/client";
import type { ShellRegion, ShellRegionContributions } from "../../stages/registry";
import BluecadGlbViewer, {
  type GeometryInspectionCommand,
  type GeometryInspectionSnapshot
} from "../BluecadGlbViewer";
import {
  acceptsSceneSelectionResolution,
  currentGlbArtifact,
  resolveCandidateSceneHitFromArtifacts,
  type SceneSelectionPreconditions
} from "./sceneSelection";
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
type SceneBindingPresentation = "idle" | "resolving" | "unresolved" | "ambiguous";

const EMPTY_INSPECTION: GeometryInspectionSnapshot = {
  sessionKey: null,
  status: "idle",
  meshes: [],
  selected: null
};

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
  const [inspection, setInspection] = useState<GeometryInspectionSnapshot>(EMPTY_INSPECTION);
  const [inspectionCommand, setInspectionCommand] = useState<GeometryInspectionCommand | null>(null);
  const [sceneBindingPresentation, setSceneBindingPresentation] = useState<SceneBindingPresentation>("idle");
  const [showCreate, setShowCreate] = useState(false);
  const [availability, setAvailability] = useState<BluecadGenerationAvailability | null>(null);
  const [availabilityState, setAvailabilityState] = useState<LoadState>("idle");

  const listGeneration = useRef(0);
  const detailGeneration = useRef(0);
  const validationGeneration = useRef(0);
  const mutationGeneration = useRef(0);
  const inspectionNonce = useRef(0);
  const workspaceRef = useRef("");
  const selectedRef = useRef<string | null>(null);
  const aggregateRef = useRef<BluecadCandidateAggregateRead | null>(aggregate);
  aggregateRef.current = aggregate;
  const currentSceneSelection = useRef<SceneSelectionPreconditions | null>(null);
  const showArchivedRef = useRef(showArchived);
  showArchivedRef.current = showArchived;
  const filterTextRef = useRef(filterText);
  filterTextRef.current = filterText;
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
  const focusAfterArchive = useRef(false);

  const handleBriefRef = useCallback((node: HTMLTextAreaElement | null) => {
    briefRef.current = node;
    if (!node || !focusBriefOnMount.current) return;
    focusBriefOnMount.current = false;
    node.scrollIntoView({ block: "nearest" });
    node.focus();
  }, []);

  const visibleCandidates = useMemo(
    () => filterCandidates(candidates, filterText, showArchived),
    [candidates, filterText, showArchived]
  );

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

  const handleInspectionChange = useCallback((snapshot: GeometryInspectionSnapshot) => {
    setInspection(snapshot);
    if (!snapshot.sessionKey) setInspectionCommand(null);
    setSceneBindingPresentation("idle");

    currentSceneSelection.current = null;
    const targetWorkspaceId = workspaceRef.current;
    const targetCandidateId = selectedRef.current;
    publishSelection(targetWorkspaceId, targetCandidateId);

    const currentAggregate = aggregateRef.current;
    const candidate = currentAggregate?.candidate;
    const hit = snapshot.selected;
    if (
      !targetWorkspaceId
      || !targetCandidateId
      || !candidate
      || candidate.workspace_id !== targetWorkspaceId
      || candidate.id !== targetCandidateId
      || !candidate.glb_artifact_id
      || !snapshot.sessionKey
      || !hit
      || !hit.semanticKey
    ) return;

    const glbArtifact = currentGlbArtifact(currentAggregate.artifacts, candidate.glb_artifact_id);
    if (!glbArtifact) return;

    const captured: SceneSelectionPreconditions = {
      workspaceId: targetWorkspaceId,
      candidateId: targetCandidateId,
      artifactId: glbArtifact.id,
      viewerSessionId: snapshot.sessionKey,
      meshKey: hit.meshKey,
      semanticKey: hit.semanticKey
    };
    const publishBindingStatus = (state: "resolving" | "unresolved" | "ambiguous") => {
      onSelectionChange({
        kind: "bluecad-binding-status",
        state,
        workspaceId: captured.workspaceId,
        candidateId: captured.candidateId,
        artifactId: captured.artifactId,
        viewerSessionId: captured.viewerSessionId,
        ephemeralObjectId: captured.meshKey,
        meshKey: captured.meshKey,
        semanticKey: captured.semanticKey
      });
    };
    currentSceneSelection.current = captured;
    setSceneBindingPresentation("resolving");
    publishBindingStatus("resolving");

    void resolveCandidateSceneHitFromArtifacts(
      currentAggregate.artifacts,
      hit.semanticKey,
      glbArtifact.sha256,
      (artifactId) => getBluecadArtifactJson<unknown>(targetWorkspaceId, artifactId)
    ).then((resolution) => {
      if (!acceptsSceneSelectionResolution(currentSceneSelection.current, captured)) return;
      if (resolution.state !== "resolved") {
        setSceneBindingPresentation(resolution.state);
        publishBindingStatus(resolution.state);
        return;
      }
      setSceneBindingPresentation("idle");
      onSelectionChange({
        kind: "bluecad-part",
        workspaceId: captured.workspaceId,
        candidateId: captured.candidateId,
        artifactId: captured.artifactId,
        viewerSessionId: captured.viewerSessionId,
        ephemeralObjectId: captured.meshKey,
        meshKey: captured.meshKey,
        semanticKey: captured.semanticKey,
        partId: resolution.part.partId,
        partKind: resolution.part.partKind
      });
    });
  }, [onSelectionChange, publishSelection]);

  const requestInspection = useCallback((meshKey: string | null) => {
    if (!inspection.sessionKey) return;
    inspectionNonce.current += 1;
    setInspectionCommand({
      sessionKey: inspection.sessionKey,
      meshKey,
      nonce: inspectionNonce.current
    });
  }, [inspection.sessionKey]);

  const clearVisibleDetail = useCallback((nextState: LoadState) => {
    setAggregate(null);
    setAggregateState(nextState);
    setChecks([]);
    setValidationState("idle");
    setValidationMessage(null);
  }, []);

  const chooseCandidate = useCallback((candidateId: string | null) => {
    if (candidateId === selectedRef.current) return;
    mutationGeneration.current += 1;
    currentSceneSelection.current = null;
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
      const selectableItems = filterCandidates(items, filterTextRef.current, showArchivedRef.current);
      const nextId = revalidateSelection(selectableItems, preferredId, true);
      currentSceneSelection.current = null;
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
        currentSceneSelection.current = null;
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
      currentSceneSelection.current = null;
      publishSelection(targetWorkspaceId, candidateId);
      setAggregate(next);
      setAggregateState("ready");
      return next;
    } catch (error) {
      if (currentDetail.current && acceptsRequest(currentDetail.current, request)) {
        currentSceneSelection.current = null;
        publishSelection(targetWorkspaceId, candidateId);
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
  }, [loadCandidates, publishSelection]);

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
    setShowCreate(false);
    setAvailability(null);
    if (!workspaceId) {
      setAvailabilityState("idle");
      return undefined;
    }
    let active = true;
    setAvailabilityState("loading");
    getBluecadGenerationAvailability(workspaceId).then((next) => {
      if (!active) return;
      setAvailability(next);
      setAvailabilityState("ready");
    }).catch(() => {
      if (active) setAvailabilityState("error");
    });
    return () => { active = false; };
  }, [workspaceId]);

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
    currentSceneSelection.current = null;
    setSceneBindingPresentation("idle");
    publishSelection(workspaceRef.current, selectedRef.current);
    setInspection(EMPTY_INSPECTION);
    setInspectionCommand(null);
  }, [aggregate?.candidate.glb_artifact_id, publishSelection, selectedId]);

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

  useEffect(() => {
    if (!focusAfterArchive.current || candidateState === "loading") return;
    const finalId = revalidateSelection(visibleCandidates, selectedId, true);
    if (finalId !== selectedId) return;
    focusAfterArchive.current = false;
    window.requestAnimationFrame(() => {
      const candidateNode = finalId ? candidateRefs.current[finalId] : null;
      (candidateNode ?? emptyCandidatesRef.current ?? workbenchTitleRef.current)?.focus();
    });
  }, [candidateState, selectedId, visibleCandidates]);

  const refresh = useCallback(async () => {
    if (!workspaceId) return false;
    currentSceneSelection.current = null;
    publishSelection(workspaceId, selectedId);
    currentDetail.current = null;
    currentValidation.current = null;
    clearVisibleDetail("loading");
    const items = await loadCandidates(workspaceId, selectedId, true);
    if (!items || workspaceRef.current !== workspaceId) return false;
    const nextId = selectedRef.current;
    if (!nextId) return false;
    const detail = await loadAggregate(workspaceId, nextId);
    return detail !== null;
  }, [clearVisibleDetail, loadAggregate, loadCandidates, publishSelection, selectedId, workspaceId]);

  const reconcileAfterMutationError = useCallback(async (mutation: MutationContext, failureMessage: string) => {
    if (!acceptsMutation({ generation: mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selectedRef.current }, mutation)) return;
    currentSceneSelection.current = null;
    publishSelection(mutation.workspaceId, selectedRef.current);
    if (mutation.kind === "archive") focusAfterArchive.current = true;
    const preferredId = selectedRef.current;
    currentDetail.current = null;
    currentValidation.current = null;
    const items = await loadCandidates(mutation.workspaceId, preferredId, true);
    if (items && workspaceRef.current === mutation.workspaceId) {
      const nextId = selectedRef.current;
      if (nextId) await loadAggregate(mutation.workspaceId, nextId);
    }
    if (workspaceRef.current === mutation.workspaceId) setMessage(failureMessage);
  }, [loadAggregate, loadCandidates, publishSelection]);

  const onCreateTemplate = async (payload: BluecadTemplateCreate): Promise<boolean> => {
    if (!workspaceId || candidateState === "loading" || mutationConflicts(pendingAction, "create")) return false;
    const mutation: MutationContext = {
      generation: ++mutationGeneration.current,
      workspaceId: workspaceRef.current,
      candidateId: selectedRef.current,
      kind: "create"
    };
    setPendingAction("create");
    setMessage(null);
    try {
      const created = await createBluecadTemplateCandidate(mutation.workspaceId, payload);
      if (!acceptsMutation({ generation: mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selectedRef.current }, mutation)) return false;
      filterTextRef.current = "";
      setFilterText("");
      suppressNextDetailEffect.current = created.id;
      const items = await loadCandidates(mutation.workspaceId, created.id);
      if (!items || !items.some((item) => item.id === created.id)) {
        suppressNextDetailEffect.current = null;
        return false;
      }
      setShowCreate(false);
      const detail = await loadAggregate(mutation.workspaceId, created.id);
      if (!detail || workspaceRef.current !== mutation.workspaceId || selectedRef.current !== created.id) return true;
      setMessage(`Template candidate saved · ${detail.candidate.status}${detail.candidate.parked_reason ? ` — ${detail.candidate.parked_reason}` : ""}.`);
      return true;
    } catch (error) {
      suppressNextDetailEffect.current = null;
      const refused = error instanceof Error && error.message === "Request failed with 422";
      await reconcileAfterMutationError(mutation, refused ? "The server refused these template parameters." : error instanceof Error ? error.message : "Template creation failed.");
      return false;
    } finally {
      setPendingAction(null);
    }
  };

  const onCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const brief = briefText.trim();
    if (!brief || !workspaceId || candidateState === "loading" || mutationConflicts(pendingAction, "create")) return;
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
      filterTextRef.current = "";
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
      setMessage(`Candidate saved · ${detail.candidate.status}${detail.candidate.parked_reason ? ` — ${detail.candidate.parked_reason}` : ""}.`);
    } catch (error) {
      suppressNextDetailEffect.current = null;
      await reconcileAfterMutationError(mutation, error instanceof Error ? error.message : "Candidate creation failed.");
    } finally {
      setPendingAction(null);
    }
  };

  const onArchive = async () => {
    if (!selected || candidateState === "loading" || mutationConflicts(pendingAction, "archive")) return;
    const mutation: MutationContext = { generation: ++mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selected.id, kind: "archive" };
    setPendingAction("archive");
    setMessage(null);
    try {
      await archiveBluecadCandidate(mutation.workspaceId, mutation.candidateId!);
      if (!acceptsMutation({ generation: mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selectedRef.current }, mutation)) return;
      focusAfterArchive.current = true;
      const items = await loadCandidates(mutation.workspaceId, mutation.candidateId ?? null);
      if (!items || workspaceRef.current !== mutation.workspaceId) return;
      if (selectedRef.current === mutation.candidateId) void loadAggregate(mutation.workspaceId, mutation.candidateId!);
      setMessage("Candidate archived.");
    } catch (error) {
      await reconcileAfterMutationError(mutation, error instanceof Error ? error.message : "Archive failed.");
    } finally {
      setPendingAction(null);
    }
  };

  const onPromote = async () => {
    if (!selected || candidateState === "loading" || mutationConflicts(pendingAction, "promote")) return;
    const mutation: MutationContext = { generation: ++mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selected.id, kind: "promote" };
    setPendingAction("promote");
    setMessage(null);
    try {
      const promoted = await promoteBluecadCandidate(mutation.workspaceId, mutation.candidateId!);
      if (!acceptsMutation({ generation: mutationGeneration.current, workspaceId: workspaceRef.current, candidateId: selectedRef.current }, mutation)) return;
      const refreshed = await refresh();
      if (!refreshed || workspaceRef.current !== mutation.workspaceId || selectedRef.current !== mutation.candidateId) {
        if (workspaceRef.current === mutation.workspaceId) window.requestAnimationFrame(() => workbenchTitleRef.current?.focus());
        return;
      }
      window.requestAnimationFrame(() => workbenchTitleRef.current?.focus());
      setMessage(`Promoted to Decision ${promoted.promoted_decision_id ?? "(pending id)"}.`);
    } catch (error) {
      await reconcileAfterMutationError(mutation, error instanceof Error ? error.message : "Promotion failed.");
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

  const openBriefComposer = () => {
    requestShellRegionOpen("navigator");
    const briefNode = briefRef.current;
    if (briefNode) {
      briefNode.scrollIntoView({ block: "nearest" });
      briefNode.focus();
      return;
    }
    focusBriefOnMount.current = true;
  };

  const aiBriefState = availabilityState === "loading" || availabilityState === "idle"
    ? "Checking provider and budget state…"
    : availabilityState === "error" || !availability
      ? "Provider state is unavailable. The server still enforces provider permission and budget; a blocked brief is saved as a parked candidate."
      : availability.external_calls_allowed
        ? "Paid AI is enabled for the external tier. A brief starts server-side generation and may spend budget."
        : `Paid AI is off (${availability.blocking_reason ?? "external calls blocked"}). A brief is saved but parks as budget_blocked until paid AI and budget are enabled in Settings.`;

  const navigator = useMemo<ReactNode>(() => (
    <div className="bluecad-workbench__navigator">
      <label>Workspace<select value={workspaceId} onChange={(event) => {
        const nextWorkspaceId = event.target.value;
        mutationGeneration.current += 1;
        currentSceneSelection.current = null;
        workspaceRef.current = nextWorkspaceId;
        selectedRef.current = null;
        currentList.current = null;
        currentDetail.current = null;
        currentValidation.current = null;
        suppressNextDetailEffect.current = null;
        clearVisibleDetail("idle");
        setMessage(null);
        publishSelection(nextWorkspaceId, null);
        setWorkspaceId(nextWorkspaceId);
      }} disabled={workspaceState !== "ready" || workspaces.length === 0 || pendingAction !== null} style={{ width: "100%", minWidth: 0, maxWidth: "100%" }}>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}</select></label>
      <label>Filter candidates<input ref={filterRef} value={filterText} onChange={(event) => { filterTextRef.current = event.target.value; setFilterText(event.target.value); }} disabled={candidateState === "loading" || pendingAction !== null} /></label>
      <label className="checkbox-line"><input type="checkbox" checked={showArchived} onChange={(event) => setShowArchived(event.target.checked)} disabled={candidateState === "loading" || pendingAction !== null} />Show archived</label>
      <button type="button" className="secondary-button" onClick={() => void refresh()} disabled={!workspaceId || candidateState === "loading" || pendingAction !== null}>Refresh</button>
      <p className="panel-subtitle">New candidate saves your brief and requests AI generation. {aiBriefState}</p>
      <form className="bluecad-new-form" onSubmit={onCreate}><label>New candidate brief<textarea ref={handleBriefRef} value={briefText} onChange={(event) => setBriefText(event.target.value)} required /></label><button type="submit" disabled={!workspaceId || !briefText.trim() || candidateState === "loading" || pendingAction !== null}>{pendingAction === "create" ? "Creating…" : "New candidate"}</button></form>
      {workspaceState === "loading" && <p>Loading workspaces…</p>}
      {workspaceState === "error" && <p className="error-banner">Workspace discovery failed.</p>}
      {workspaceState === "ready" && workspaces.length === 0 && <p>No workspaces are available.</p>}
      {candidateState === "loading" && <p>Loading candidates…</p>}
      {candidateState === "error" && <p className="error-banner">Candidate discovery failed.</p>}
      <div className="bluecad-candidate-list" aria-label="BLUECAD candidates">{visibleCandidates.map((candidate) => <button key={candidate.id} ref={(node) => { candidateRefs.current[candidate.id] = node; }} type="button" aria-pressed={candidate.id === selectedId} className={candidate.id === selectedId ? "bluecad-candidate active" : "bluecad-candidate"} onClick={() => chooseCandidate(candidate.id)} disabled={candidateState === "loading" || pendingAction !== null}><span className={`status-pill status-${candidate.status}`}>{candidate.status}</span><strong>{candidate.brief_text.slice(0, 90)}{candidate.brief_text.length > 90 ? "…" : ""}</strong>{candidate.parked_reason && <small>Parked: {candidate.parked_reason}</small>}</button>)}</div>
      {candidateState === "ready" && candidates.length === 0 && <p ref={emptyCandidatesRef} tabIndex={-1}>No BLUECAD candidates exist in this workspace.</p>}
      {candidateState === "ready" && candidates.length > 0 && visibleCandidates.length === 0 && <p ref={emptyCandidatesRef} tabIndex={-1}>No candidates match the current filter. Archived candidates may be hidden.</p>}
    </div>
  ), [aiBriefState, briefText, candidateState, candidates.length, clearVisibleDetail, filterText, handleBriefRef, pendingAction, publishSelection, refresh, selectedId, showArchived, visibleCandidates, workspaceId, workspaceState, workspaces]);

  const sceneBindingNotice = sceneBindingPresentation === "resolving"
    ? "Resolving engineering binding…"
    : sceneBindingPresentation === "unresolved"
      ? "Unresolved engineering binding. Geometry remains viewable; candidate authority is unchanged."
      : sceneBindingPresentation === "ambiguous"
        ? "Ambiguous engineering binding. Geometry remains viewable; no engineering object was selected."
        : null;

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
    return <div className="bluecad-workbench__sidecar">{sceneBindingNotice && <p className={sceneBindingPresentation === "resolving" ? "panel-subtitle" : "warning-banner"} role="status">{sceneBindingNotice}</p>}<h3>Candidate inspector</h3><dl className="details"><div><dt>Lifecycle</dt><dd>{candidate.status}</dd></div><div><dt>Freshness</dt><dd>{aggregate.freshness}</dd></div><div><dt>Promotion</dt><dd>{candidate.promoted_decision_id ?? "Not promoted"}</dd></div></dl>{candidate.parked_reason && <p className="warning-banner">Parked reason: {candidate.parked_reason}</p>}<GeometryInspectionPanel snapshot={inspection} onSelect={requestInspection} /><h3>Validation</h3>{validation}<h3>Artifacts</h3>{aggregate.artifacts.length === 0 ? <p>No aggregate-linked artifacts.</p> : <ul>{aggregate.artifacts.map((artifact) => <li key={artifact.id}><a href={`${API_BASE_URL}${artifact.content_url}`}>{artifact.filename}</a> · {artifact.roles.join(", ")} · {artifact.status}</li>)}</ul>}<h3>Canonical references</h3><p>{aggregate.evidence.length} evidence refs · {aggregate.runs.length} run refs</p>{aggregate.diagnostics.map((diagnostic, index) => <p className="warning-banner" key={`${diagnostic.code}-${index}`}>{diagnostic.message}</p>)}</div>;
  }, [aggregate, aggregateState, checks, inspection, requestInspection, sceneBindingNotice, sceneBindingPresentation, selectedId, validationMessage, validationState]);

  const dock = useMemo<ReactNode>(() => {
    const activeAggregate = aggregate?.candidate.id === selectedId ? aggregate : null;
    const attempts = activeAggregate?.candidate.attempts ?? [];
    const evidence = activeAggregate?.evidence ?? [];
    const runs = activeAggregate?.runs ?? [];
    return <div className="bluecad-workbench__dock"><h3>Attempt history</h3>{attempts.length === 0 ? <p>No attempts recorded yet.</p> : <div className="table-wrap"><table className="smoke-table bluecad-table"><thead><tr><th>#</th><th>Route</th><th>Proposal</th><th>Build</th><th>Validation</th><th>Started</th><th>Finished</th><th>Error detail</th></tr></thead><tbody>{attempts.map((attempt) => <tr key={attempt.id}><td>{attempt.attempt_no}</td><td>{attempt.route_class}</td><td>{attempt.proposal_outcome}</td><td>{attempt.build_outcome ?? "—"}</td><td>{attempt.validation_verdict ?? "—"}</td><td>{attempt.started_at}</td><td>{attempt.finished_at ?? "—"}</td><td>{formatAttemptDetail(attempt.error_detail_json)}</td></tr>)}</tbody></table></div>}<h3>Evidence references</h3>{evidence.length === 0 ? <p>No aggregate-linked evidence.</p> : <ul>{evidence.map((item) => <li key={`${item.subject_ref}-${item.ref}`}><strong>{item.kind}</strong> · {item.ref} · subject {item.subject_ref} · {item.status}{item.summary ? ` · ${item.summary}` : ""}</li>)}</ul>}<h3>Run references</h3>{runs.length === 0 ? <p>No aggregate-linked runs.</p> : <ul>{runs.map((run) => <li key={`${run.source_ref ?? "direct"}-${run.ref}`}><strong>{run.kind}</strong> · {run.ref}{run.source_ref ? ` · source ${run.source_ref}` : ""}{run.status ? ` · ${run.status}` : ""}{run.stale === true ? " · stale" : ""}</li>)}</ul>}</div>;
  }, [aggregate, selectedId]);

  useEffect(() => { onShellRegionsChange({ navigator, sidecar, dock }); }, [dock, navigator, onShellRegionsChange, sidecar]);
  useEffect(() => () => {
    currentSceneSelection.current = null;
    currentList.current = null;
    currentDetail.current = null;
    currentValidation.current = null;
    suppressNextDetailEffect.current = null;
    mutationGeneration.current += 1;
    onSelectionChange(null);
    onShellRegionsChange({});
  }, [onSelectionChange, onShellRegionsChange]);

  const candidate = aggregate?.candidate.id === selectedId ? aggregate.candidate : null;
  const canPromote = candidate?.status === "valid" && !candidate.promoted_decision_id;
  const exports = aggregate?.candidate.id === selectedId ? aggregate.exports ?? [] : [];
  const busy = candidateState === "loading" || pendingAction !== null;
  const noCandidates = candidateState === "ready" && candidates.length === 0;
  const createPanel = <CreateGeometryPanel
    heading={noCandidates ? "No geometry yet" : "Create geometry"}
    intro={noCandidates ? "This workspace has no BLUECAD candidates, so there is nothing to show in 3D. Create geometry in one of two ways:" : "Add a candidate to this workspace in one of two ways:"}
    aiBriefState={aiBriefState}
    disabled={!workspaceId || busy}
    pending={pendingAction === "create"}
    onCreateTemplate={onCreateTemplate}
    onOpenBrief={openBriefComposer}
    onCancel={noCandidates ? null : () => setShowCreate(false)}
  />;
  const viewportContent = workspaceState === "loading"
    ? <div className="bluecad-workbench__empty-viewer"><p>Loading workspaces…</p></div>
    : workspaceState === "ready" && workspaces.length === 0
      ? <div className="bluecad-workbench__empty-viewer"><p>No workspaces are available.</p></div>
      : showCreate || noCandidates
        ? <div className="bluecad-workbench__empty-viewer">{createPanel}</div>
        : candidate?.glb_artifact_id
          ? <BluecadGlbViewer artifactUrl={bluecadArtifactContentUrl(candidate.workspace_id, candidate.glb_artifact_id)} inspectionCommand={inspectionCommand} onInspectionChange={handleInspectionChange} />
          : candidate
            ? <div className="bluecad-workbench__empty-viewer"><h2>Geometry unavailable</h2><p>{candidate.parked_reason ? `Generation was parked: ${candidate.parked_reason}` : "No GLB artifact is available for this candidate yet."}</p><p><button type="button" className="secondary-button" onClick={() => setShowCreate(true)}>Create geometry</button></p></div>
            : <div className="bluecad-workbench__empty-viewer"><p>{selectedId && aggregateState === "error" ? "Candidate detail unavailable. Use Refresh to retry." : aggregateState === "loading" || candidateState === "loading" ? "Loading candidate geometry…" : "Select a candidate from the navigator."}</p>{candidateState === "ready" && aggregateState !== "loading" && <p className="button-row"><button type="button" className="secondary-button" onClick={() => requestShellRegionOpen("navigator")}>Open candidate list</button><button type="button" className="secondary-button" onClick={() => setShowCreate(true)}>Create geometry</button></p>}</div>;

  return <section className="bluecad-workbench" aria-labelledby="bluecad-workbench-title"><header className="bluecad-workbench__chrome"><div style={{ minWidth: 0, flex: "1 1 18rem" }}><p className="eyebrow">BLUECAD</p><h1 id="bluecad-workbench-title" ref={workbenchTitleRef} tabIndex={-1}>Model workbench</h1>{candidate && !showCreate && <div style={{ minWidth: 0, overflowWrap: "anywhere" }}><p className="panel-subtitle">{candidate.brief_text.slice(0, 180)}{candidate.brief_text.length > 180 ? "…" : ""}</p><details><summary>Candidate details</summary><dl><dt>Candidate ID</dt><dd>{candidate.id}</dd></dl><p style={{ maxHeight: "10rem", overflow: "auto", whiteSpace: "pre-wrap" }}>{candidate.brief_text}</p></details></div>}</div><div className="button-row">{candidate && !showCreate && <><span className={`status-pill status-${candidate.status}`}>{candidate.status}</span>{exports.length > 0 && <ExportMenu exports={exports} />}<button type="button" className="secondary-button" onClick={() => requestShellRegionOpen("sidecar")}>Inspect candidate</button><button type="button" className="secondary-button" onClick={duplicateSelectedBrief}>Duplicate brief</button>{candidate.status !== "archived" && <button type="button" className="secondary-button" onClick={() => void onArchive()} disabled={busy}>Archive</button>}{canPromote && <button type="button" onClick={() => void onPromote()} disabled={busy}>Promote to Decision</button>}</>}{workspaceId && !noCandidates && !showCreate && <button type="button" className="secondary-button" onClick={() => setShowCreate(true)} disabled={busy}>New geometry</button>}</div></header>{message && <div className="panel-subtitle" role="status">{message}</div>}{sceneBindingNotice && <div className={sceneBindingPresentation === "resolving" ? "panel-subtitle" : "warning-banner"} role="status">{sceneBindingNotice}</div>}<div className="bluecad-workbench__viewport">{viewportContent}</div></section>;
}

const EXPORT_LABELS: Record<string, [string, string]> = {
  "export.stl": ["STL mesh", "Millimetres · for slicers such as Bambu Studio"],
  "export.step": ["STEP solid", "Exact B-rep · for CAD exchange"]
};

function ExportMenu({ exports }: { exports: BluecadArtifactRefRead[] }) {
  const [open, setOpen] = useState(false);
  const [flipped, setFlipped] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!open) return undefined;
    const onPointerDown = (event: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);
  const items = exports.filter((item) => EXPORT_LABELS[item.roles[0] ?? ""]);
  useLayoutEffect(() => {
    if (!open) {
      setFlipped(false);
      return undefined;
    }
    const fitMenu = () => {
      const menu = menuRef.current;
      if (!menu) return;
      setFlipped(menu.getBoundingClientRect().right > window.innerWidth - 8);
    };
    fitMenu();
    window.addEventListener("resize", fitMenu);
    return () => window.removeEventListener("resize", fitMenu);
  }, [open, items.length]);
  return <div className="bluecad-export" ref={rootRef} onKeyDown={(event) => {
    if (event.key === "Escape" && open) {
      event.stopPropagation();
      setOpen(false);
      buttonRef.current?.focus();
    }
  }}><button ref={buttonRef} type="button" className="secondary-button" aria-expanded={open} aria-controls="bluecad-export-menu" onClick={() => setOpen((value) => !value)}>Export ▾</button>{open && <div ref={menuRef} id="bluecad-export-menu" className={`bluecad-export__menu${flipped ? " bluecad-export__menu--flipped" : ""}`} aria-label="Download exports">{items.map((item) => {
    const [label, detail] = EXPORT_LABELS[item.roles[0]];
    return <a key={item.id} href={`${API_BASE_URL}${item.content_url}`} download onClick={() => setOpen(false)}><strong>{label}</strong><small>{detail}</small></a>;
  })}</div>}</div>;
}

type TemplateKind = BluecadTemplateCreate["template"];
type FieldSpec = Readonly<{ key: string; label: string; min: number; max: number; step: number; integer?: boolean; initial: string }>;

// Bounds mirror the server template contract; the server remains the authority.
const TEMPLATE_FIELDS: Record<TemplateKind, readonly FieldSpec[]> = {
  tube: [
    { key: "outer_d_mm", label: "Outer Ø (mm)", min: 2, max: 1000, step: 0.1, initial: "40" },
    { key: "wall_t_mm", label: "Wall (mm)", min: 0.5, max: 100, step: 0.1, initial: "3" },
    { key: "length_mm", label: "Length (mm)", min: 1, max: 5000, step: 1, initial: "120" }
  ],
  manifold: [
    { key: "outer_d_mm", label: "Header Ø (mm)", min: 2, max: 1000, step: 0.1, initial: "50" },
    { key: "wall_t_mm", label: "Wall (mm)", min: 0.5, max: 100, step: 0.1, initial: "3" },
    { key: "length_mm", label: "Length (mm)", min: 1, max: 5000, step: 1, initial: "240" },
    { key: "branch_count", label: "Branches", min: 1, max: 12, step: 1, integer: true, initial: "3" },
    { key: "branch_outer_d_mm", label: "Branch Ø (mm)", min: 2, max: 1000, step: 0.1, initial: "20" }
  ]
};

function templateProblem(kind: TemplateKind, values: Record<string, number>): string | null {
  for (const field of TEMPLATE_FIELDS[kind]) {
    const value = values[field.key];
    if (!Number.isFinite(value) || value < field.min || value > field.max || (field.integer && !Number.isInteger(value))) {
      return `${field.label} must be ${field.integer ? "a whole number " : ""}between ${field.min} and ${field.max}.`;
    }
  }
  if (values.wall_t_mm * 2 >= values.outer_d_mm) return "Wall must be less than half of the outer diameter.";
  if (kind === "manifold") {
    if (values.wall_t_mm * 2 >= values.branch_outer_d_mm) return "Wall must be less than half of the branch diameter.";
    if (values.branch_outer_d_mm >= values.outer_d_mm) return "Branch Ø must be smaller than the header Ø.";
    if (values.branch_outer_d_mm >= values.length_mm / (values.branch_count + 1)) return "Branches do not fit: make the header longer or the branches fewer or thinner.";
  }
  return null;
}

function CreateGeometryPanel({ heading, intro, aiBriefState, disabled, pending, onCreateTemplate, onOpenBrief, onCancel }: {
  heading: string;
  intro: string;
  aiBriefState: string;
  disabled: boolean;
  pending: boolean;
  onCreateTemplate(payload: BluecadTemplateCreate): Promise<boolean>;
  onOpenBrief(): void;
  onCancel: (() => void) | null;
}) {
  const [kind, setKind] = useState<TemplateKind>("tube");
  const [raw, setRaw] = useState<Record<TemplateKind, Record<string, string>>>(() => ({
    tube: Object.fromEntries(TEMPLATE_FIELDS.tube.map((field) => [field.key, field.initial])),
    manifold: Object.fromEntries(TEMPLATE_FIELDS.manifold.map((field) => [field.key, field.initial]))
  }));
  const [problem, setProblem] = useState<string | null>(null);
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const values = Object.fromEntries(TEMPLATE_FIELDS[kind].map((field) => [field.key, Number(raw[kind][field.key])]));
    const nextProblem = templateProblem(kind, values);
    setProblem(nextProblem);
    if (nextProblem) return;
    const payload = kind === "tube"
      ? { template: "tube" as const, params: { outer_d_mm: values.outer_d_mm, wall_t_mm: values.wall_t_mm, length_mm: values.length_mm } }
      : { template: "manifold" as const, params: { outer_d_mm: values.outer_d_mm, wall_t_mm: values.wall_t_mm, length_mm: values.length_mm, branch_count: values.branch_count, branch_outer_d_mm: values.branch_outer_d_mm } };
    void onCreateTemplate(payload);
  };
  return <div className="bluecad-create">
    <div className="bluecad-create__intro"><h2>{heading}</h2><p>{intro}</p></div>
    <form className="bluecad-create__route" onSubmit={submit} aria-labelledby="bluecad-template-title" noValidate>
      <h3 id="bluecad-template-title">Template part · no AI</h3>
      <p>Built deterministically on the server from your dimensions, validated, and exported as GLB, STL and STEP.</p>
      <div className="bluecad-create__fields">
        <label>Template<select value={kind} onChange={(event) => { setKind(event.target.value as TemplateKind); setProblem(null); }} disabled={disabled}><option value="tube">Tube</option><option value="manifold">Manifold</option></select></label>
        {TEMPLATE_FIELDS[kind].map((field) => <label key={`${kind}-${field.key}`}>{field.label}<input type="number" inputMode="decimal" min={field.min} max={field.max} step={field.step} value={raw[kind][field.key]} onChange={(event) => setRaw((current) => ({ ...current, [kind]: { ...current[kind], [field.key]: event.target.value } }))} disabled={disabled} required /></label>)}
      </div>
      {problem && <p className="error-banner" role="alert">{problem}</p>}
      <div className="button-row"><button type="submit" disabled={disabled}>{pending ? "Building…" : `Create ${kind}`}</button>{onCancel && <button type="button" className="secondary-button" onClick={onCancel}>Cancel</button>}</div>
    </form>
    <section className="bluecad-create__route" aria-labelledby="bluecad-ai-title">
      <h3 id="bluecad-ai-title">AI brief</h3>
      <p>Describe the part in words; the generation loop proposes a GeometrySpec through an external AI tier.</p>
      <p role="status">{aiBriefState}</p>
      <div className="button-row"><button type="button" className="secondary-button" onClick={onOpenBrief}>Write a brief</button></div>
    </section>
  </div>;
}

function GeometryInspectionPanel({ snapshot, onSelect }: { snapshot: GeometryInspectionSnapshot; onSelect(meshKey: string | null): void }) {
  const selected = snapshot.selected;
  return <section aria-labelledby="geometry-inspection-title"><h3 id="geometry-inspection-title">Geometry inspection</h3><p className="panel-subtitle">Geometry-only · current viewer session · semantic identity resolves only through current manifest evidence</p>{snapshot.status === "loading" && <p>Loading inspectable geometry…</p>}{snapshot.status === "error" && <p className="error-banner">Geometry inspection is unavailable for this artifact.</p>}{snapshot.status === "ready" && snapshot.meshes.length === 0 && <p>No inspectable artifact meshes.</p>}{snapshot.status === "ready" && snapshot.meshes.length > 0 && <><label>Inspectable mesh<select value={selected?.meshKey ?? ""} onChange={(event) => onSelect(event.target.value || null)} style={{ width: "100%", minWidth: 0, maxWidth: "100%" }}><option value="">No mesh selected</option>{snapshot.meshes.map((mesh) => <option key={mesh.meshKey} value={mesh.meshKey}>{mesh.displayName}</option>)}</select></label><button type="button" className="secondary-button" onClick={() => onSelect(null)} disabled={!selected}>Clear inspection</button>{selected && <dl className="details"><div><dt>Mesh</dt><dd>{selected.displayName}</dd></div><div><dt>Session key</dt><dd>{selected.meshKey}</dd></div><div><dt>Artifact material names</dt><dd>{selected.materialNames.length ? selected.materialNames.join(", ") : "Not named"}</dd></div><div><dt>Rendered triangles</dt><dd>{selected.triangleCount ?? "Unavailable"}</dd></div><div><dt>World bounds</dt><dd>{formatBounds(selected.worldBounds)}</dd></div></dl>}</>}</section>;
}

function formatBounds(bounds: GeometryInspectionSnapshot["selected"] extends infer T ? T extends { worldBounds: infer B } ? B : never : never): string {
  if (!bounds) return "Unavailable";
  const format = (value: number) => Number.isFinite(value) ? Number(value.toPrecision(6)).toString() : "?";
  return `min (${bounds.min.map(format).join(", ")}) · max (${bounds.max.map(format).join(", ")}) · unitless`;
}

function filterCandidates(items: BluecadCandidate[], filterText: string, showArchived: boolean): BluecadCandidate[] {
  const query = filterText.trim().toLowerCase();
  return items.filter((candidate) => {
    if (!showArchived && candidate.status === "archived") return false;
    return !query || candidate.id.toLowerCase().includes(query) || candidate.brief_text.toLowerCase().includes(query);
  });
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
function formatValidationValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value.length <= 160 ? value : `${value.slice(0, 159)}…`;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return `[${value.length} items]`;
  if (isRecord(value)) {
    const keys = Object.keys(value);
    const preview = keys.slice(0, 4).map((key) => key.length <= 40 ? key : `${key.slice(0, 39)}…`).join(", ");
    return `{${preview}${keys.length > 4 ? ", …" : ""}}`;
  }
  return String(value).slice(0, 160);
}
function formatValidationDetail(value: unknown): string {
  if (!isRecord(value)) return formatValidationValue(value);
  if ("actual" in value && "declared" in value) {
    const relErr = formatPercent(value.rel_err);
    const relTol = formatPercent(value.rel_tol);
    return `actual ${formatValidationValue(value.actual)} vs declared ${formatValidationValue(value.declared)}${relErr ? ` (rel err ${relErr}${relTol ? ` / tol ${relTol}` : ""})` : ""}`;
  }
  const entries = Object.entries(value);
  const detail = entries.slice(0, 6).map(([key, item]) => `${formatValidationValue(key)}: ${formatValidationValue(item)}`).join(" · ");
  return `${detail}${entries.length > 6 ? " · …" : ""}`;
}
function ReportTable({ checks }: { checks: BluecadValidationCheck[] }) { return checks.length === 0 ? <p>No validation checks are available.</p> : <div className="table-wrap"><table className="smoke-table bluecad-table"><thead><tr><th>Check</th><th>Tier</th><th>Status</th><th>Detail</th><th>Hint</th></tr></thead><tbody>{checks.map((check, index) => <tr key={`${check.id ?? check.check_id ?? "check"}-${index}`}><td>{check.id ?? check.check_id ?? `check-${index + 1}`}</td><td>{check.tier ?? "—"}</td><td>{check.status ?? check.verdict ?? "—"}</td><td>{formatValidationDetail(check.detail ?? check.message) || "—"}</td><td>{check.hint ?? "—"}</td></tr>)}</tbody></table></div>; }
function formatAttemptDetail(value?: string | null): string { if (!value) return "—"; try { return formatCell(JSON.parse(value) as unknown); } catch { return value; } }

export default BluecadWorkbench;
