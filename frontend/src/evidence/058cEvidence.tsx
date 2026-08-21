import React, { useMemo, useState } from "react";
import ReactDOM from "react-dom/client";

import type { StageSelection } from "../app/selection";
import EngineeringData from "../pages/EngineeringData";
import { EngineeringPropertiesPanel, useEngineeringProperties } from "../components/engineering/EngineeringProperties";
import { applyAppearancePreference } from "../theme";
import "../styles/tokens.css";
import "../styles/global.css";
import "../styles/foundation.css";
import "../styles/shell.css";
import "../styles/engineering-data.css";
import "../styles/responsive.css";

const WS = "ws1";

function part(candidateId: string, viewerSessionId: string, partId = "illuminated_tube_proxy", partKind = "tube_run"): StageSelection {
  return {
    kind: "bluecad-part",
    workspaceId: WS,
    candidateId,
    artifactId: `artifact-${candidateId}`,
    viewerSessionId,
    ephemeralObjectId: `object-${candidateId}`,
    meshKey: `mesh-${candidateId}`,
    semanticKey: `semantic-${candidateId}`,
    partId,
    partKind
  };
}

function EvidenceApp() {
  const [selection, setSelection] = useState<StageSelection>(() => part("cand-a", "session-a1"));
  const [route, setRoute] = useState(() => `${window.location.pathname}${window.location.search}`);
  const [appearance, setAppearance] = useState<"system" | "light" | "dark">("system");
  const controller = useEngineeringProperties(WS, () => undefined, selection);

  const navigate = (href: string) => {
    const destination = new URL(href, window.location.href);
    window.history.pushState({}, "", `${destination.pathname}${destination.search}`);
    setRoute(`${destination.pathname}${destination.search}`);
  };

  const current = useMemo(() => selection.kind === "bluecad-part" ? selection : null, [selection]);
  const setTheme = (value: "system" | "light" | "dark") => {
    setAppearance(value);
    applyAppearancePreference(value);
  };

  return (
    <main style={{ minHeight: "100vh", padding: 12 }}>
      <div data-testid="evidence-controls" style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <button type="button" onClick={() => { window.history.pushState({}, "", "/058c-evidence.html"); setRoute("/058c-evidence.html"); setSelection(part("cand-a", "session-a1")); }}>Select A</button>
        <button type="button" onClick={() => setSelection(part("cand-a", "session-a2"))}>A new viewer session</button>
        <button type="button" onClick={() => setSelection(part("cand-b", "session-b1"))}>Select B</button>
        <button type="button" onClick={() => setSelection(part("cand-a", "session-nonmatching", "other_part", "other_kind"))}>Non-matching part</button>
        <button type="button" onClick={() => setTheme("light")}>Light</button>
        <button type="button" onClick={() => setTheme("dark")}>Dark</button>
        <button type="button" onClick={() => setTheme("system")}>System</button>
        <span data-testid="selection-state">{current ? `${current.candidateId}:${current.viewerSessionId}:${current.partId}:${current.partKind}` : "none"}</span>
        <span data-testid="route-state">{route}</span>
        <span data-testid="appearance-state">{appearance}</span>
      </div>
      {route.startsWith("/engineering-data") ? (
        <EngineeringData workspaceId={WS} onWorkspaceChange={() => undefined} navigate={navigate} />
      ) : (
        <div style={{ maxWidth: 720 }}>
          <EngineeringPropertiesPanel controller={controller} navigate={navigate} />
        </div>
      )}
    </main>
  );
}

applyAppearancePreference("system");
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(<EvidenceApp />);
