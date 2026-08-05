import { useEffect, useState, type ReactNode } from "react";

import { useAppRouter } from "./app/useAppRouter";
import type { StageSelection } from "./app/selection";
import Layout from "./components/Layout";
import PageErrorBoundary from "./components/PageErrorBoundary";
import LegacyDiagnosticSurface from "./components/shell/LegacyDiagnosticSurface";
import MigrationPendingSurface from "./components/shell/MigrationPendingSurface";
import AIDraft from "./pages/AIDraft";
import Dashboard from "./pages/Dashboard";
import DevLocalChat from "./pages/DevLocalChat";
import DomainFoundation from "./pages/DomainFoundation";
import SystemStatus from "./pages/SystemStatus";
import { PRIMARY_STAGES } from "./stages/registry";

function App() {
  const { resolved, navigate } = useAppRouter();
  const { route } = resolved;
  const [selection, setSelection] = useState<StageSelection | null>(null);

  useEffect(() => {
    setSelection(null);
  }, [route.id]);

  let content: ReactNode;

  if (route.stageKind) {
    const Stage = PRIMARY_STAGES[route.stageKind].render;
    content = <Stage workspaceId={null} selection={selection} onSelectionChange={setSelection} />;
  } else {
    switch (route.id) {
      case "home":
        content = <Dashboard />;
        break;
      case "runs":
        content = (
          <MigrationPendingSurface
            title="Runs"
            description="The dedicated run list and detail workbench belongs to spec 088. Existing scenario and run controls remain available on the legacy diagnostic route."
            navigate={navigate}
            links={[{ href: "/legacy/domain-foundation", label: "Open legacy Domain Foundation" }]}
          />
        );
        break;
      case "engineering-data":
        content = (
          <MigrationPendingSurface
            title="Engineering Data"
            description="Searchable engineering-record navigation belongs to re-derived spec 035. Current records remain available on the legacy diagnostic route."
            navigate={navigate}
            links={[{ href: "/legacy/domain-foundation", label: "Open legacy Domain Foundation" }]}
          />
        );
        break;
      case "settings":
        content = (
          <MigrationPendingSurface
            title="Settings"
            description="The product Settings surface belongs to re-derived spec 029. Current provider, storage, budget, and AI diagnostics remain on explicit legacy routes."
            navigate={navigate}
            links={[
              { href: "/legacy/system-status", label: "Open legacy System Status" },
              { href: "/legacy/ai-draft", label: "Open legacy AI Draft" }
            ]}
          />
        );
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
        content = import.meta.env.DEV ? (
          <LegacyDiagnosticSurface title="Development Local Chat"><DevLocalChat /></LegacyDiagnosticSurface>
        ) : null;
        break;
      case "not-found":
      default:
        content = (
          <MigrationPendingSurface
            title="Page not found"
            description={`No application route matches ${resolved.canonicalPath}.`}
            navigate={navigate}
            links={[
              { href: "/home", label: "Return to Home" },
              { href: "/design/model", label: "Open Design" }
            ]}
            unavailable
          />
        );
        break;
    }
  }

  return (
    <Layout route={route} navigate={navigate} selection={selection}>
      <PageErrorBoundary key={route.id}>{content}</PageErrorBoundary>
    </Layout>
  );
}

export default App;
