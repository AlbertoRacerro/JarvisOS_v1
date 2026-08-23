import React, { useState } from "react";
import ReactDOM from "react-dom/client";

// Evidence-only harness for product PR #339. This file is never merged.
import EngineeringData from "../pages/EngineeringData";
import "../styles/tokens.css";
import "../styles/global.css";
import "../styles/foundation.css";
import "../styles/shell.css";
import "../styles/responsive.css";

function EvidenceApp() {
  const [workspaceId, setWorkspaceId] = useState<string | null>("ws1");
  const [lastNavigation, setLastNavigation] = useState("none");

  return (
    <main style={{ minHeight: "100vh" }}>
      <output data-testid="evidence-workspace">{workspaceId ?? "none"}</output>
      <output data-testid="evidence-navigation">{lastNavigation}</output>
      <EngineeringData
        workspaceId={workspaceId}
        onWorkspaceChange={setWorkspaceId}
        navigate={(path) => setLastNavigation(path)}
      />
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(<EvidenceApp />);
