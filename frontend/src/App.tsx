import type { KnowledgeContextPreview } from "./api/knowledgeActions";
import { Suspense, lazy, useEffect, useCallback, useRef, useState, type ReactNode } from "react";

import type { StageSelection } from "./app/selection";
import { useAppRouter } from "./app/useAppRouter";
import Layout from "./components/Layout";
import PageErrorBoundary from "./components/PageErrorBoundary";
import JarvisKnowledgeActions from "./components/ai/JarvisKnowledgeActions";
import { useJarvisSidecar } from "./components/ai/useJarvisSidecar";
import AnalyticsDockContent from "./components/analytics/AnalyticsDockContent";
import {
  EngineeringPropertiesPanel,
  useEngineeringProperties
} from "./components/engineering/EngineeringProperties";
import JarvisEngineeringActions from "./components/engineering/JarvisEngineeringActions";
import FinalOperatorReadSurface from "./components/fusion/FinalOperatorReadSurface";
import FinalSettingsSurface from "./components/fusion/FinalSettingsSurface";
import FinalWorkspaceHeader from "./components/fusion/FinalWorkspaceHeader";
import ProjectKnowledgePanel from "./components/fusion/ProjectKnowledgePanel";
import ProjectSearchPanel from "./components/fusion/ProjectSearchPanel";
import WorkspaceBootstrap, { readStoredWorkspaceId, writeStoredWorkspaceId } from "./components/WorkspaceBootstrap";
import { listWorkspaces, type Workspace } from "./api/client";
import LegacyDiagnosticSurface from "./components/shell/LegacyDiagnosticSurface";
import MigrationPendingSurface from "./components/shell/MigrationPendingSurface";
import AIDraft from "./pages/AIDraft";
import AIThreads from "./pages/AIThreads";
import CodingWorkbench from "./pages/CodingWorkbench";
import DevelopmentBrainstorm from "./pages/DevelopmentBrainstorm";
import DevelopmentRoadmap from "./pages/DevelopmentRoadmap";
import DomainFoundation from "./pages/DomainFoundation";
import EngineeringData from "./pages/EngineeringData";
import LiteratureKnowledge from "./pages/LiteratureKnowledge";
import ModelDossier from "./pages/ModelDossier";
import RunsWorkbench from "./pages/RunsWorkbench";
import SystemStatus from "./pages/SystemStatus";
import { PRIMARY_STAGES, type ShellRegion, type ShellRegionContributions } from "./stages/registry";

const DevLocalChat = import.meta.env.DEV ? lazy(() => import("./pages/DevLocalChat")) : null;
type ShellRegionRequest = Readonly<{ region: ShellRegion; nonce: number }>;
const PROJECT_BASIS_RECORD_KINDS = new Set(["requirement", "parameter", "assumption", "decision"]);
const KNOWLEDGE_ROUTES = new Set(["memory-project-basis", "memory-models", "memory-literature"]);
const WORKSPACE_OPTIONAL_ROUTES = new Set(["settings-appearance", "settings-ai", "settings-system", "coding-runtime", "legacy-domain-foundation", "legacy-ai-draft", "legacy-system-status", "legacy-dev-local-chat"]);
type WorkspaceLoadState = "loading" | "ready" | "empty" | "error";

function boundedSearchParam(params: URLSearchParams, name: string): string | null {
  const value = params.get(name)?.trim() ?? "";
  return value && value.length <= 200 ? value : null;
}

function App() {
  const { resolved, navigate } = useAppRouter();
  const { route } = resolved;
  const [workspaceId, setWorkspaceIdState] = useState<string | null>(null);
  const [workspaceLoadState, setWorkspaceLoadState] = useState<WorkspaceLoadState>("loading");
  const [workspaceLoadError, setWorkspaceLoadError] = useState<string | null>(null);
  const workspaceIds = useRef(new Set<string>());
  const workspaceLoadGeneration = useRef(0);
  const [selection, setSelection] = useState<StageSelection | null>(null);
  const [shellRegions, setShellRegions] = useState<ShellRegionContributions>({});
  const [shellRegionRequest, setShellRegionRequest] = useState<ShellRegionRequest | null>(null);
  const [knowledgeContext, setKnowledgeContext] = useState<KnowledgeContextPreview | null>(null);
  const [selectedKnowledgeLabel, setSelectedKnowledgeLabel] = useState<string | null>(null);
  const [selectedKnowledgeRef, setSelectedKnowledgeRef] = useState<string | null>(null);
  const [selectedModelVersionId, setSelectedModelVersionId] = useState<string | null>(null);
  const selectKnowledge = useCallback((ref: string | null, label?: string) => {
    setSelectedKnowledgeRef(ref); setSelectedKnowledgeLabel(label ?? null);
  }, []);
  const selectModelVersion = useCallback((id: string | null, label?: string) => {
    setSelectedModelVersionId(id); setSelectedKnowledgeLabel(label ?? null);
  }, []);
  const loadWorkspaces = useCallback((preferredId?: string | null) => {
    const generation = ++workspaceLoadGeneration.current;
    setWorkspaceLoadState("loading"); setWorkspaceLoadError(null); setWorkspaceIdState(null);
    return listWorkspaces().then((items: Workspace[]) => {
      if (generation !== workspaceLoadGeneration.current) return;
      workspaceIds.current = new Set(items.map((item) => item.id));
      const stored = preferredId ?? readStoredWorkspaceId();
      const selected = stored && workspaceIds.current.has(stored) ? stored : items[0]?.id ?? null;
      setWorkspaceIdState(selected);
      writeStoredWorkspaceId(selected);
      setWorkspaceLoadState(items.length ? "ready" : "empty");
    }).catch((cause: unknown) => {
      if (generation !== workspaceLoadGeneration.current) return;
      setWorkspaceLoadState("error"); setWorkspaceLoadError(cause instanceof Error ? cause.message : "Workspace discovery failed.");
    });
  }, []);
  useEffect(() => { void loadWorkspaces(); return () => { workspaceLoadGeneration.current++; }; }, [loadWorkspaces]);
  const setWorkspaceId = useCallback((next: string | null) => {
    if (!next || !workspaceIds.current.has(next)) { void loadWorkspaces(next); return; }
    setWorkspaceIdState(next);
    writeStoredWorkspaceId(next);
  }, [loadWorkspaces]);
  const handleWorkspaceCreated = useCallback((workspace: Workspace) => {
    workspaceLoadGeneration.current++;
    workspaceIds.current.add(workspace.id); setWorkspaceIdState(workspace.id); setWorkspaceLoadState("ready"); setWorkspaceLoadError(null);
    writeStoredWorkspaceId(workspace.id);
  }, []);
  const engineeringProperties = useEngineeringProperties(workspaceId, setWorkspaceId, selection);
  const routeParams = new URLSearchParams(window.location.search);
  const requestedRecordKind = boundedSearchParam(routeParams, "recordKind");
  const requestedRecordId = boundedSearchParam(routeParams, "recordId");
  const requestedRecordRef = requestedRecordKind && requestedRecordId && PROJECT_BASIS_RECORD_KINDS.has(requestedRecordKind)
    ? `${requestedRecordKind}:${requestedRecordId}`
    : null;
  const requestedModelVersionId = boundedSearchParam(routeParams, "modelVersionId");
  const requestedLiteratureSourceId = boundedSearchParam(routeParams, "sourceId");
  const requestedLiteratureEntryId = boundedSearchParam(routeParams, "entryId");
  const knowledgeStableRef = route.id === "memory-project-basis"
    ? selectedKnowledgeRef ?? requestedRecordRef
    : route.id === "memory-models" && selectedModelVersionId
      ? `model_version:${selectedModelVersionId}`
      : route.id === "memory-literature" && selectedKnowledgeRef
        ? selectedKnowledgeRef
        : route.id === "memory-literature" && requestedLiteratureEntryId
        ? `literature_entry:${requestedLiteratureEntryId}`
        : route.id === "memory-literature" && requestedLiteratureSourceId
          ? `literature_source:${requestedLiteratureSourceId}`
          : null;

  useEffect(() => {
    setSelection(null);
    setSelectedKnowledgeRef(null);
    setSelectedKnowledgeLabel(null);
    setShellRegions({});
    setShellRegionRequest(null);
    setSelectedModelVersionId(null);
  }, [route.id]);

  useEffect(() => {
    setSelectedKnowledgeRef(null);
    setSelectedKnowledgeLabel(null);
    setSelectedModelVersionId(null);
  }, [workspaceId]);

  useEffect(() => {
    if (selection?.kind === "record" && selection.ref.workspaceId !== workspaceId) setWorkspaceId(selection.ref.workspaceId);
  }, [selection, setWorkspaceId, workspaceId]);

  const requestShellRegionOpen = (region: ShellRegion) => setShellRegionRequest((current) => ({ region, nonce: (current?.nonce ?? 0) + 1 }));

  const stageSidecar = shellRegions.sidecar;
  const semanticSelectionContext = selection?.kind === "bluecad-part" ? <div className="shell-properties__selection"><strong>{selection.partId}</strong><p>{selection.partKind ? `${selection.partKind} · selected BLUECAD part` : "Selected BLUECAD part"}</p></div> : undefined;
  const knowledgeActions = <JarvisKnowledgeActions workspaceId={workspaceId} routeId={route.id} stableRef={knowledgeStableRef} selectedLabel={selectedKnowledgeLabel} onContextChange={setKnowledgeContext} />;
  const jarvisLocalContext = KNOWLEDGE_ROUTES.has(route.id)
    ? knowledgeActions
    : <>{semanticSelectionContext}<JarvisEngineeringActions controller={engineeringProperties} />{knowledgeActions}</>;
  const jarvisSidecar = useJarvisSidecar(workspaceId, route.id, selection, jarvisLocalContext, knowledgeContext);

  let content: ReactNode;
  const workspaceRequired = !WORKSPACE_OPTIONAL_ROUTES.has(route.id);
  if (workspaceRequired && workspaceLoadState !== "ready") {
    content = workspaceLoadState === "loading" ? <div className="workspace-bootstrap" aria-live="polite"><p>Loading workspaces…</p></div>
      : workspaceLoadState === "error" ? <WorkspaceBootstrap error={workspaceLoadError} onRetry={() => void loadWorkspaces()} onCreated={handleWorkspaceCreated} />
      : <WorkspaceBootstrap onCreated={handleWorkspaceCreated} />;
  } else if (route.stageKind && (route.id === "design-process" || route.id === "design-bluecad" || route.id === "review")) {
    const Stage = PRIMARY_STAGES[route.stageKind].render;
    content = <Stage workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} selection={selection} onSelectionChange={setSelection} onShellRegionsChange={setShellRegions} requestShellRegionOpen={requestShellRegionOpen} navigate={navigate} />;
  } else if (route.id === "design-studies") {
    const Stage = PRIMARY_STAGES.studies.render;
    content = <Stage workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} selection={selection} onSelectionChange={setSelection} onShellRegionsChange={setShellRegions} requestShellRegionOpen={requestShellRegionOpen} navigate={navigate} />;
  } else {
    switch (route.id) {
      case "memory-project-basis":
        content = <><FinalWorkspaceHeader group="memory" active="project-basis" navigate={navigate} /><FinalOperatorReadSurface kind="project-basis" workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} requestedRecordRef={requestedRecordRef} onRecordSelect={selectKnowledge} jarvis={jarvisSidecar} projectSearch={<ProjectSearchPanel workspaceId={workspaceId} navigate={navigate} />} /></>;
        break;
      case "memory-models":
        content = <><FinalWorkspaceHeader group="memory" active="models" navigate={navigate} /><ModelDossier workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} requestedModelVersionId={requestedModelVersionId} onModelVersionSelectionChange={selectModelVersion} jarvis={jarvisSidecar} revisionPanel={<ProjectKnowledgePanel workspaceId={workspaceId} readOnly />} /></>;
        break;
      case "memory-literature":
        content = <><FinalWorkspaceHeader group="memory" active="literature" navigate={navigate} /><LiteratureKnowledge kind="literature" workspaceId={workspaceId} jarvis={jarvisSidecar} onWorkspaceChange={setWorkspaceId} requestedSourceId={requestedLiteratureSourceId} requestedEntryId={requestedLiteratureEntryId} onKnowledgeSelectionChange={selectKnowledge} searchPanel={<ProjectSearchPanel workspaceId={workspaceId} navigate={navigate} />} /></>;
        break;
      case "development-roadmap-timeline":
        content = <><FinalWorkspaceHeader group="development" active="roadmap" navigate={navigate} /><DevelopmentRoadmap mode="timeline" workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} jarvis={jarvisSidecar} /></>;
        break;
      case "development-roadmap-calendar":
        content = <><FinalWorkspaceHeader group="development" active="roadmap" navigate={navigate} /><DevelopmentRoadmap mode="calendar" workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} jarvis={jarvisSidecar} /></>;
        break;
      case "development-brainstorm":
        content = <><FinalWorkspaceHeader group="development" active="brainstorm" navigate={navigate} /><DevelopmentBrainstorm jarvis={jarvisSidecar} workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} /></>;
        break;
      case "coding-repository":
        content = <><FinalWorkspaceHeader group="coding" active="repository" navigate={navigate} /><CodingWorkbench mode="repository" workspaceId={workspaceId} jarvis={jarvisSidecar} /></>;
        break;
      case "coding-runtime":
        content = <><FinalWorkspaceHeader group="coding" active="runtime" navigate={navigate} /><CodingWorkbench mode="runtime" workspaceId={workspaceId} jarvis={jarvisSidecar} /></>;
        break;
      case "settings-appearance":
        content = <FinalSettingsSurface section="appearance" navigate={navigate} />;
        break;
      case "settings-ai":
        content = <FinalSettingsSurface section="ai" navigate={navigate} />;
        break;
      case "settings-system":
        content = <FinalSettingsSurface section="system" navigate={navigate} />;
        break;
      case "runs":
        content = <RunsWorkbench workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} engineeringProperties={engineeringProperties} />;
        break;
      case "engineering-data":
        content = <EngineeringData workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} navigate={navigate} />;
        break;
      case "ai-threads":
        content = <AIThreads workspaceId={workspaceId} />;
        break;
      case "legacy-domain-foundation":
        content = <LegacyDiagnosticSurface title="Domain Foundation"><DomainFoundation /></LegacyDiagnosticSurface>;
        break;
      case "legacy-ai-draft":
        content = <LegacyDiagnosticSurface title="AI Draft"><AIDraft /></LegacyDiagnosticSurface>;
        break;
      case "legacy-system-status":
        content = <LegacyDiagnosticSurface title="System Status"><SystemStatus /></LegacyDiagnosticSurface>;
        break;
      case "legacy-dev-local-chat":
        content = import.meta.env.DEV && DevLocalChat ? <LegacyDiagnosticSurface title="Development Local Chat"><Suspense fallback={<p>Loading development diagnostic…</p>}><DevLocalChat /></Suspense></LegacyDiagnosticSurface> : null;
        break;
      case "not-found":
      default:
        content = <MigrationPendingSurface title="Page not found" description={`No application route matches ${resolved.canonicalPath}.`} navigate={navigate} links={[{ href: "/design/process", label: "Open Process" }, { href: "/memory/models", label: "Open Models" }]} unavailable />;
        break;
    }
  }

  const propertiesContent = <EngineeringPropertiesPanel controller={engineeringProperties} stageContext={stageSidecar} navigate={navigate} />;
  const effectiveShellRegions: ShellRegionContributions = {
    ...shellRegions,
    sidecar: route.primaryNav === "settings" || route.primaryNav === "coding" || workspaceLoadState !== "ready" || !workspaceId ? undefined : jarvisSidecar,
    ...(route.id === "runs" || route.id === "engineering-data" || route.id === "design-process" ? { dock: <AnalyticsDockContent workspaceId={workspaceId} /> } : {})
  };

  return <Layout route={route} navigate={navigate} selection={selection} propertiesContent={propertiesContent} shellRegions={effectiveShellRegions} shellRegionRequest={shellRegionRequest}><PageErrorBoundary key={resolved.canonicalPath}>{content}</PageErrorBoundary></Layout>;
}

export default App;
