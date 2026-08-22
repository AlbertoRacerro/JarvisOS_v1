import React, { useEffect, useRef, useState } from "react";
import ReactDOM from "react-dom/client";

// Evidence-only harness for the current PR #333 product head. This file is never merged.
import type { StageSelection } from "../app/selection";
import { EngineeringPropertiesPanel, useEngineeringProperties } from "../components/engineering/EngineeringProperties";
import JarvisEngineeringActions from "../components/engineering/JarvisEngineeringActions";
import "../styles/tokens.css";
import "../styles/global.css";
import "../styles/foundation.css";
import "../styles/shell.css";
import "../styles/responsive.css";

function part(workspaceId: string, candidateId: string, session: string): StageSelection {
  return {
    kind: "bluecad-part",
    workspaceId,
    candidateId,
    artifactId: `artifact-${candidateId}`,
    viewerSessionId: session,
    ephemeralObjectId: `object-${candidateId}`,
    meshKey: `mesh-${candidateId}`,
    semanticKey: `semantic-${candidateId}`,
    partId: "illuminated_tube_proxy",
    partKind: "tube_run"
  };
}

function EvidenceApp() {
  const [workspaceId, setWorkspaceId] = useState("ws1");
  const [selection, setSelection] = useState<StageSelection>(() => part("ws1", "cand-a", "session-a1"));
  const controller = useEngineeringProperties(workspaceId, () => undefined, selection);
  const primedSafeFix = useRef(false);

  useEffect(() => {
    if (primedSafeFix.current || workspaceId !== "ws1" || selection.kind !== "bluecad-part" || selection.candidateId !== "cand-a") return;
    const variable = controller.selected?.input_contract?.variables.find((item) => item.name === "tube_length");
    const baseline = controller.baseline.tube_length;
    const working = controller.working.tube_length;
    if (!variable || !baseline?.value || !working || working.value !== baseline.value || working.parameterId !== baseline.parameterId) return;
    primedSafeFix.current = true;
    // Prime a real deterministic blocker while retaining an exact valid baseline.
    // A merely dirty-but-valid field is not a blocker and therefore must not create a Jarvis safe-fix action.
    controller.updateValue(variable, "not-a-number");
  }, [controller, selection, workspaceId]);

  const switchWorkspace = () => {
    const next = workspaceId === "ws1" ? "ws2" : "ws1";
    setWorkspaceId(next);
    setSelection(part(next, next === "ws1" ? "cand-a" : "cand-c", `session-${next}`));
  };

  return (
    <main style={{ minHeight: "100vh", padding: 12 }}>
      <div data-testid="evidence-controls" style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <button type="button" onClick={() => setSelection(part(workspaceId, "cand-a", `session-a-${Date.now()}`))}>Select A</button>
        <button type="button" onClick={() => setSelection(part(workspaceId, "cand-b", `session-b-${Date.now()}`))}>Select B</button>
        <button type="button" onClick={switchWorkspace}>Switch workspace</button>
        <span data-testid="workspace-state">{workspaceId}</span>
        <span data-testid="selection-state">{selection.kind === "bluecad-part" ? `${selection.candidateId}:${selection.partId}` : "none"}</span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)", gap: 12 }}>
        <section aria-label="Evidence Jarvis pane"><JarvisEngineeringActions controller={controller} /></section>
        <section aria-label="Evidence Properties pane"><EngineeringPropertiesPanel controller={controller} navigate={() => undefined} /></section>
      </div>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(<EvidenceApp />);
