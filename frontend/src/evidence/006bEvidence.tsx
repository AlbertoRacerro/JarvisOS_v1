import React, { useState } from "react";
import ReactDOM from "react-dom/client";

import { EngineeringPropertiesPanel, useEngineeringProperties } from "../components/engineering/EngineeringProperties";
import RunsWorkbench from "../pages/RunsWorkbench";
import "../styles/tokens.css";
import "../styles/global.css";
import "../styles/foundation.css";
import "../styles/shell.css";
import "../styles/runs.css";
import "../styles/responsive.css";

function EvidenceApp() {
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const engineeringProperties = useEngineeringProperties(workspaceId, setWorkspaceId, null);

  return (
    <main style={{ display: "grid", gridTemplateColumns: "minmax(0, 2fr) minmax(320px, 1fr)", gap: 16, padding: 16 }}>
      <RunsWorkbench
        workspaceId={workspaceId}
        onWorkspaceChange={setWorkspaceId}
        engineeringProperties={engineeringProperties}
      />
      <aside aria-label="Properties evidence">
        <EngineeringPropertiesPanel controller={engineeringProperties} />
      </aside>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <EvidenceApp />
  </React.StrictMode>
);
