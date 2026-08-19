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
import LegacyDiagnosticSurface from "./components/shell/LegacyDiagnosticSurface";
import MigrationPendingSurface from "./components/shell/MigrationPendingSurface";
import AIDraft from "./pages/AIDraft";
import AIThreads from "./pages/AIThreads";
import Dashboard from "./pages/Dashboard";
import DomainFoundation from "./pages/DomainFoundation";
import EngineeringData from "./pages/EngineeringData";
import RunsWorkbench from "./pages/RunsWorkbench";
import Settings from "./pages/Settings";
import SystemStatus from "./pages/SystemStatus";
import { PRIMARY_STAGES, type ShellRegion, type ShellRegionContributions } from "./stages/registry";

const DevLocalChat = import.meta.env.DEV ? lazy(() => import("./pages/DevLocalChat")) : null;
type ShellRegionRequest = Readonly<{ region: ShellRegion; nonce: number }>;

function App() {
  const { resolved, navigate } = useAppRouter();
  const { route } = resolved;
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [selection, setSelection] = useState<StageSelection | null>(null);
  const [shellRegions, setShellRegions] = useState<ShellRegionContributions>({});
  const [shellRegionRequest, setShellRegionRequest] = useState<ShellRegionRequest | null>(null);
  const engineeringProperties = useEngineeringProperties(workspaceId, setWorkspaceId);

  useEffect(() => {
    setSelection(null);
    setShellRegions({});
    setShellRegionRequest(null);
  }, [route.id]);

  useEffect(() => {
    if (selection?.kind === "record" && selection.ref.workspaceId !== workspaceId) {
      setWorkspaceId(selection.ref.workspaceId);
    }
  }, [selection, workspaceId]);

  const requestShellRegionOpen = (region: ShellRegion) => {
    setShellRegionRequest((current) => ({ region, nonce: (current?.nonce ?? 0) + 1 }));
  };

  let content: ReactNode;
  if (route.stageKind) {
    const Stage = PRIMARY_STAGES[route.stageKind].render;
    content = <Stage workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} selection={selection} onSelectionChange={setSelection} onShellRegionsChange={setShellRegions} requestShellRegionOpen={requestShellRegionOpen} navigate={navigate} />;
  } else {
    switch (route.id) {
      case "home":
        content = <section className="shell-home" aria-labelledby="shell-home-title"><header className="shell-home__header"><p className="eyebrow">Application shell</p><h1 id="shell-home-title">Home</h1></header><div className="shell-home__content"><Dashboard /></div></section>;
        break;
      case "runs":
        content = <RunsWorkbench workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} />;
        break;
      case "engineering-data":
        content = <EngineeringData workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} navigate={navigate} />;
        break;
      case "ai-threads":
        content = <AIThreads workspaceId={workspaceId} />;
        break;
      case "settings":
        content = <Settings />;
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
        content = <MigrationPendingSurface title="Page not found" description={`No application route matches ${resolved.canonicalPath}.`} navigate={navigate} links={[{ href: "/home", label: "Return to Home" }, { href: "/design/model", label: "Open Design" }]} unavailable />;
        break;
    }
  }

  const stageSidecar = shellRegions.sidecar;
  const semanticSelectionContext = selection?.kind === "bluecad-part"
    ? <div className="shell-properties__selection"><strong>{selection.partId}</strong><p>{selection.partKind ? `${selection.partKind} · selected BLUECAD part` : "Selected BLUECAD part"}</p></div>
    : undefined;
  const jarvisSidecar = useJarvisSidecar(workspaceId, route.id, selection, semanticSelectionContext);
  const propertiesContent = <EngineeringPropertiesPanel controller={engineeringProperties} stageContext={stageSidecar} />;
  const effectiveShellRegions: ShellRegionContributions = {
    ...shellRegions,
    sidecar: jarvisSidecar,
    ...(route.id === "runs" || route.id === "engineering-data"
      ? { dock: <AnalyticsDockContent workspaceId={workspaceId} /> }
      : {})
  };

  return <Layout route={route} navigate={navigate} selection={selection} propertiesContent={propertiesContent} shellRegions={effectiveShellRegions} shellRegionRequest={shellRegionRequest}><PageErrorBoundary key={resolved.canonicalPath}>{content}</PageErrorBoundary></Layout>;
}

export default App;
