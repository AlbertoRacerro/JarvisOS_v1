import React, { useState } from "react";
import ReactDOM from "react-dom/client";

import AnalyticsDockContent from "../components/analytics/AnalyticsDockContent";
import "../styles/tokens.css";
import "../styles/global.css";
import "../styles/foundation.css";
import "../styles/shell.css";
import "../styles/responsive.css";

function EvidenceApp() {
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

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode><EvidenceApp /></React.StrictMode>
);
