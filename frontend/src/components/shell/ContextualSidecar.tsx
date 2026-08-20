import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import type { StageSelection } from "../../app/selection";
import Button from "../ui/Button";
import InlineNotice from "../ui/InlineNotice";

type Pane = "jarvis" | "properties";
type ContextualSidecarProps = Readonly<{
  open: boolean;
  selection: StageSelection | null;
  onClose(): void;
  content?: ReactNode;
  propertiesContent?: ReactNode;
}>;

type BindingStatusSelection = Extract<StageSelection, { kind: "bluecad-binding-status" }>;

function BindingStatusContext({ selection }: { selection: BindingStatusSelection }) {
  const title = selection.state === "resolving"
    ? "Resolving engineering binding"
    : selection.state === "unresolved"
      ? "Unresolved engineering binding"
      : "Ambiguous engineering binding";
  const detail = selection.state === "resolving"
    ? "Checking the current artifact binding. No engineering object is editable until resolution finishes."
    : selection.state === "unresolved"
      ? "Geometry remains viewable, but this hit cannot be mapped to a current engineering object. Candidate authority is unchanged."
      : "More than one authoritative binding is possible for this hit. No engineering object was selected.";
  return <div className="shell-properties__selection" role="status"><strong>{title}</strong><p>{detail}</p><details><summary>Technical details</summary><dl className="details"><div><dt>Workspace</dt><dd>{selection.workspaceId}</dd></div><div><dt>Candidate</dt><dd>{selection.candidateId}</dd></div><div><dt>Artifact</dt><dd>{selection.artifactId}</dd></div><div><dt>Viewer session</dt><dd>{selection.viewerSessionId}</dd></div><div><dt>Mesh inspection key</dt><dd>{selection.meshKey}</dd></div><div><dt>Semantic key</dt><dd>{selection.semanticKey}</dd></div></dl></details></div>;
}

function PropertiesFallback({ selection }: { selection: StageSelection | null }) {
  if (selection === null) {
    return <InlineNotice tone="neutral">No object selected. Select a current engineering or viewer object to inspect available properties.</InlineNotice>;
  }
  if (selection.kind === "geometry-hit") {
    return <div className="shell-properties__selection"><strong>Viewer geometry selection</strong><p>This hit is ephemeral viewer-session data and is not yet an engineering record.</p><details><summary>Technical details</summary><dl className="details"><div><dt>Viewer session</dt><dd>{selection.viewerSessionId}</dd></div><div><dt>Ephemeral object</dt><dd>{selection.ephemeralObjectId}</dd></div></dl></details></div>;
  }
  if (selection.kind === "bluecad-binding-status") {
    return <BindingStatusContext selection={selection} />;
  }
  if (selection.kind === "bluecad-part") {
    return <div className="shell-properties__selection"><strong>{selection.partId}</strong><p>{selection.partKind ? `${selection.partKind} · selected BLUECAD part` : "Selected BLUECAD part"}</p><details><summary>Technical details</summary><dl className="details"><div><dt>Workspace</dt><dd>{selection.workspaceId}</dd></div><div><dt>Candidate</dt><dd>{selection.candidateId}</dd></div><div><dt>Artifact</dt><dd>{selection.artifactId}</dd></div><div><dt>Viewer session</dt><dd>{selection.viewerSessionId}</dd></div><div><dt>Mesh inspection key</dt><dd>{selection.meshKey}</dd></div><div><dt>Semantic key</dt><dd>{selection.semanticKey}</dd></div></dl></details></div>;
  }
  return <div className="shell-properties__selection"><strong>Engineering record selection</strong><p>No editable model-contract Properties are available for this context yet. Current machine identity remains inspectable below.</p><details><summary>Technical details</summary><dl className="details"><div><dt>Resource</dt><dd>{selection.ref.resource}</dd></div><div><dt>Workspace</dt><dd>{selection.ref.workspaceId}</dd></div><div><dt>Record</dt><dd>{selection.ref.recordId}</dd></div></dl></details></div>;
}

function ContextualSidecar({ open, selection, onClose, content, propertiesContent }: ContextualSidecarProps) {
  const headingRef = useRef<HTMLHeadingElement | null>(null);
  const jarvisTabRef = useRef<HTMLButtonElement | null>(null);
  const propertiesTabRef = useRef<HTMLButtonElement | null>(null);
  const [activePane, setActivePane] = useState<Pane>("jarvis");
  useEffect(() => { if (open) headingRef.current?.focus(); }, [open]);
  const onPanelKeyDown = (event: KeyboardEvent<HTMLElement>) => { if (event.key === "Escape") { event.stopPropagation(); onClose(); } };
  const activatePane = (pane: Pane, moveFocus = false) => {
    setActivePane(pane);
    if (moveFocus) window.requestAnimationFrame(() => (pane === "jarvis" ? jarvisTabRef.current : propertiesTabRef.current)?.focus());
  };
  const onTabsKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    activatePane(activePane === "jarvis" ? "properties" : "jarvis", true);
  };
  const semanticTarget = selection?.kind === "bluecad-part"
    ? <div className="shell-properties__selection"><strong>{selection.partId}</strong><p>{selection.partKind ? `${selection.partKind} · selected BLUECAD part` : "Selected BLUECAD part"}</p><details><summary>Technical details</summary><dl className="details"><div><dt>Workspace</dt><dd>{selection.workspaceId}</dd></div><div><dt>Candidate</dt><dd>{selection.candidateId}</dd></div><div><dt>Artifact</dt><dd>{selection.artifactId}</dd></div><div><dt>Viewer session</dt><dd>{selection.viewerSessionId}</dd></div><div><dt>Mesh inspection key</dt><dd>{selection.meshKey}</dd></div><div><dt>Semantic key</dt><dd>{selection.semanticKey}</dd></div></dl></details></div>
    : selection?.kind === "bluecad-binding-status"
      ? <BindingStatusContext selection={selection} />
      : null;
  if (!open) return null;
  return <aside id="shell-sidecar" className="shell-panel shell-sidecar" aria-labelledby="shell-sidecar-title" onKeyDown={onPanelKeyDown}>
    <div className="shell-panel__header"><h2 id="shell-sidecar-title" ref={headingRef} tabIndex={-1}>Jarvis &amp; Properties</h2><Button variant="ghost" onClick={onClose}>Close sidecar</Button></div>
    <div className="shell-sidecar__tabs" role="tablist" aria-label="Sidecar views" onKeyDown={onTabsKeyDown}>
      <button ref={jarvisTabRef} id="shell-sidecar-tab-jarvis" type="button" role="tab" aria-selected={activePane === "jarvis"} aria-controls="shell-sidecar-pane-jarvis" tabIndex={activePane === "jarvis" ? 0 : -1} onClick={() => activatePane("jarvis")}>Jarvis</button>
      <button ref={propertiesTabRef} id="shell-sidecar-tab-properties" type="button" role="tab" aria-selected={activePane === "properties"} aria-controls="shell-sidecar-pane-properties" tabIndex={activePane === "properties" ? 0 : -1} onClick={() => activatePane("properties")}>Properties</button>
    </div>
    <div className="shell-sidecar__workbench">
      <section id="shell-sidecar-pane-jarvis" className="shell-sidecar__pane shell-sidecar__pane--jarvis" role="tabpanel" aria-labelledby="shell-sidecar-tab-jarvis" data-compact-hidden={activePane !== "jarvis"}>{content ?? <InlineNotice tone="neutral">Jarvis is unavailable for this route.</InlineNotice>}</section>
      <section id="shell-sidecar-pane-properties" className="shell-sidecar__pane shell-sidecar__pane--properties" role="tabpanel" aria-labelledby="shell-sidecar-tab-properties" data-compact-hidden={activePane !== "properties"}>
        <header className="shell-properties__header"><p className="eyebrow">Engineering model</p><h3>Properties</h3></header>
        {semanticTarget}
        {propertiesContent ?? <PropertiesFallback selection={selection} />}
      </section>
    </div>
  </aside>;
}
export default ContextualSidecar;
