import React, { useState } from "react";
import ReactDOM from "react-dom/client";

import AnalyticsDockContent from "../components/analytics/AnalyticsDockContent";
import type { EngineeringPropertiesController } from "../components/engineering/EngineeringProperties";
import RunsWorkbench from "../pages/RunsWorkbench";
import "../styles/tokens.css";
import "../styles/global.css";
import "../styles/foundation.css";
import "../styles/shell.css";
import "../styles/responsive.css";

const evidenceEngineeringProperties = {
  revision: 0,
  previousRunLoadability: () => ({ loadable: false, reason: "Current engineering target is incompatible" }),
  loadPreviousSuccessfulRun: () => ({ status: "incompatible", reason: "Evidence-only run navigation does not mutate working configuration." })
} as unknown as EngineeringPropertiesController;

function ComparisonEvidence() {
  const [workspaceId, setWorkspaceId] = useState("ws1");
  return (
    <main style={{ minWidth: 0, padding: 16 }}>
      <nav aria-label="Evidence workspace controls">
        <button type="button" onClick={() => setWorkspaceId("ws1")}>Workspace A</button>
        <button type="button" onClick={() => setWorkspaceId("ws2")}>Workspace B</button>
      </nav>
      <section aria-label="Analysis evidence" style={{ minWidth: 0, maxWidth: 960 }}>
        <AnalyticsDockContent workspaceId={workspaceId} />
      </section>
    </main>
  );
}

function RunsEvidence() {
  const [workspaceId, setWorkspaceId] = useState<string | null>("ws2");
  return (
    <RunsWorkbench
      workspaceId={workspaceId}
      onWorkspaceChange={setWorkspaceId}
      engineeringProperties={evidenceEngineeringProperties}
    />
  );
}

function EvidenceApp() {
  const params = new URLSearchParams(window.location.search);
  return params.get("evidenceRunLanding") === "1" ? <RunsEvidence /> : <ComparisonEvidence />;
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode><EvidenceApp /></React.StrictMode>
);
