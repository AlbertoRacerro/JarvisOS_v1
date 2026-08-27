import { Suspense, lazy, useEffect, useState, type ReactNode } from "react";

import type { StageSelection } from "./app/selection";
import { useAppRouter } from "./app/useAppRouter";
import Layout from "./components/Layout";
import PageErrorBoundary from "./components/PageErrorBoundary";
import { useJarvisSidecar } from "./components/ai/useJarvisSidecar";
import AnalyticsDockContent from "./components/analytics/AnalyticsDockContent";
import {
  EngineeringPropertiesPanel,
  useEngineeringProperties
} from "./components/engineering/EngineeringProperties";
import JarvisEngineeringActions from "./components/engineering/JarvisEngineeringActions";
import LegacyDiagnosticSurface from "./components/shell/LegacyDiagnosticSurface";
import MigrationPendingSurface from "./components/shell/MigrationPendingSurface";
import AIDraft from "./pages/AIDraft";
import AIThreads from "./pages/AIThreads";
import DomainFoundation from "./pages/DomainFoundation";
import EngineeringData from "./pages/EngineeringData";
import RunsWorkbench from "./pages/RunsWorkbench";
import Settings from "./pages/Settings";
import SystemStatus from "./pages/SystemStatus";
import { PRIMARY_STAGES, type ShellRegion, type ShellRegionContributions } from "./stages/registry";

const DevLocalChat = import.meta.env.DEV ? lazy(() => import("./pages/DevLocalChat")) : null;
type ShellRegionRequest = Readonly<{ region: ShellRegion; nonce: number }>;

const unavailableSurface = (title: string, description: string, navigate: ReturnType<typeof useAppRouter>["navigate"], links: readonly Readonly<{ href: string; label: string }>[] = []) => <MigrationPendingSurface title={title} description={description} navigate={navigate} links={links} unavailable />;

function App() {
  const { resolved, navigate } = useAppRouter();
  const { route } = resolved;
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [selection, setSelection] = useState<StageSelection | null>(null);
  const [shellRegions, setShellRegions] = useState<ShellRegionContributions>({});
  const [shellRegionRequest, setShellRegionRequest] = useState<ShellRegionRequest | null>(null);
  const engineeringProperties = useEngineeringProperties(workspaceId, setWorkspaceId, selection);

  useEffect(() => {
    setSelection(null);
    setShellRegions({});
    setShellRegionRequest(null);
  }, [route.id]);

  useEffect(() => {
    if (selection?.kind === "record" && selection.ref.workspaceId !== workspaceId) setWorkspaceId(selection.ref.workspaceId);
  }, [selection, workspaceId]);

  const requestShellRegionOpen = (region: ShellRegion) => setShellRegionRequest((current) => ({ region, nonce: (current?.nonce ?? 0) + 1 }));

  let content: ReactNode;
  if (route.stageKind && (route.id === "design-process" || route.id === "design-bluecad" || route.id === "review")) {
    const Stage = PRIMARY_STAGES[route.stageKind].render;
    content = <Stage workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} selection={selection} onSelectionChange={setSelection} onShellRegionsChange={setShellRegions} requestShellRegionOpen={requestShellRegionOpen} navigate={navigate} />;
  } else {
    switch (route.id) {
      case "memory-project-basis":
        content = unavailableSurface("Project Basis", "The approved Project Basis composition is reserved here, but no dedicated server-owned Project Basis read/write contract exists yet. Canonical project facts are not synthesized in React.", navigate, [{ href: "/engineering-data", label: "Open existing Engineering Data compatibility view" }]);
        break;
      case "memory-models":
        content = unavailableSurface("Models", "The approved exact-version model dossier requires a truthful model inventory/read owner. Existing engineering records remain reachable without being reinterpreted as model dossiers.", navigate, [{ href: "/engineering-data", label: "Open existing Engineering Data compatibility view" }, { href: "/runs", label: "Open existing Runs compatibility view" }]);
        break;
      case "memory-literature":
        content = unavailableSurface("Literature", "The approved Literature surface requires a bounded literature corpus/read owner. No reference fixture citations are promoted into production truth.", navigate);
        break;
      case "development-roadmap-timeline":
        content = unavailableSurface("Roadmap · Timeline", "No server-owned roadmap item store currently supplies truthful workstream or execution-status items. The canonical Timeline structure will remain empty until that owner exists.", navigate);
        break;
      case "development-roadmap-calendar":
        content = unavailableSurface("Roadmap · Calendar", "No server-owned time-allocation calendar currently supplies actual scheduled work. Gantt/reference blocks are not converted into synthetic calendar events.", navigate);
        break;
      case "development-brainstorm":
        content = unavailableSurface("Brainstorm", "The RAW → reconciliation → RECONCILED → explicit promotion workflow has no accepted persistence owner in the current frontend boundary. Reference ideas are not production records.", navigate, [{ href: "/ai-threads", label: "Open existing AI Threads compatibility view" }]);
        break;
      case "coding-repository":
        content = unavailableSurface("Repository", "No accepted frontend-safe repository observer supplies remote repository truth. The browser does not call GitHub or store a GitHub token directly.", navigate);
        break;
      case "coding-runtime":
        content = unavailableSurface("Runtime", "No accepted runtime observer supplies local-executed versus remote-exact state to this surface. Runtime health, SHA, update and terminal state therefore remain Unknown or unavailable.", navigate, [{ href: "/legacy/system-status", label: "Open existing system diagnostic" }]);
        break;
      case "settings-appearance":
      case "settings-ai":
      case "settings-system":
        content = <Settings />;
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

  const stageSidecar = shellRegions.sidecar;
  const semanticSelectionContext = selection?.kind === "bluecad-part" ? <div className="shell-properties__selection"><strong>{selection.partId}</strong><p>{selection.partKind ? `${selection.partKind} · selected BLUECAD part` : "Selected BLUECAD part"}</p></div> : undefined;
  const jarvisLocalContext = <>{semanticSelectionContext}<JarvisEngineeringActions controller={engineeringProperties} /></>;
  const jarvisSidecar = useJarvisSidecar(workspaceId, route.id, selection, jarvisLocalContext);
  const propertiesContent = <EngineeringPropertiesPanel controller={engineeringProperties} stageContext={stageSidecar} navigate={navigate} />;
  const effectiveShellRegions: ShellRegionContributions = {
    ...shellRegions,
    sidecar: route.primaryNav === "settings" ? undefined : jarvisSidecar,
    ...(route.id === "runs" || route.id === "engineering-data" || route.id === "design-process" ? { dock: <AnalyticsDockContent workspaceId={workspaceId} /> } : {})
  };

  return <Layout route={route} navigate={navigate} selection={selection} propertiesContent={propertiesContent} shellRegions={effectiveShellRegions} shellRegionRequest={shellRegionRequest}><PageErrorBoundary key={resolved.canonicalPath}>{content}</PageErrorBoundary></Layout>;
}

export default App;
