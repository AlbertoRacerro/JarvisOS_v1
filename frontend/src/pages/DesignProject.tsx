import { useCallback, useEffect, useState, type ReactNode } from "react";
import AppLink, { type Navigate } from "../app/AppLink";
import { bluecadArtifactContentUrl, getBluecadCandidateAggregate, listBluecadCandidates, listWorkspaces,
  type BluecadCandidate, type BluecadCandidateAggregateRead } from "../api/client";
import {
  activateDesignVersion, attachDesignGeometry, createDesignComponent, createDesignVersion, editDesignComponent,
  listDesignComponents, listDesignVersions, openDesignUnit,
  type DesignComponent, type DesignVersionSet
} from "../api/designProject";
import { listStudioLibrary, type StudioLibraryEntry } from "../api/studio";
import ProcessDraftEditor from "../stages/ProcessDraftEditor";
import Studio from "./Studio";
import type { EngineeringPropertiesController } from "../components/engineering/EngineeringProperties";
import { getDraft, type DraftObject } from "../api/processDraft";
import BluecadGlbViewer from "../components/BluecadGlbViewer";
import "./designProject.css";

const NODES = ["Parameters", "Geometry", "Materials", "Physics", "Mesh", "Studies", "Results", "Reduced model"] as const;
const STAGES = ["Plant", "CAD", "Motion/Mechanics", "CFD", "Optics", "Reduced model"] as const;

export default function DesignProject({ projectId, navigate, engineeringProperties }: { projectId: string | null; navigate: Navigate; engineeringProperties: EngineeringPropertiesController }) {
  const [projectName, setProjectName] = useState("");
  const [versions, setVersions] = useState<DesignVersionSet | null>(null);
  const [components, setComponents] = useState<DesignComponent[]>([]);
  const [library, setLibrary] = useState<StudioLibraryEntry[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<(typeof NODES)[number]>("Parameters");
  const [sourceUnit, setSourceUnit] = useState<DraftObject | null>(null);
  const [sourceRevision, setSourceRevision] = useState<string | null>(null);
  const [sourceError, setSourceError] = useState<string | null>(null);
  const [geometryCandidates, setGeometryCandidates] = useState<BluecadCandidate[]>([]);
  const [geometrySelection, setGeometrySelection] = useState("");
  const [geometryAggregate, setGeometryAggregate] = useState<BluecadCandidateAggregateRead | null>(null);
  const [stage, setStage] = useState<(typeof STAGES)[number]>("Plant");
  const [workshop, setWorkshop] = useState<{ modelId: string | null; key: number } | null>(null);
  const [newVersion, setNewVersion] = useState("");
  const [newComponent, setNewComponent] = useState("");
  const [editName, setEditName] = useState("");
  const [editParent, setEditParent] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!projectId) return;
    const next = await listDesignVersions(projectId);
    const active = next.versions.find((item) => item.id === next.active_version_id);
    if (!active) throw new Error("The active Design version is unavailable.");
    const [tree, published] = await Promise.all([
      listDesignComponents(projectId, active.id), listStudioLibrary(active.data_workspace_id)
    ]);
    setVersions(next); setComponents(tree); setLibrary(published);
    setSelectedId((current) => tree.some((item) => item.id === current) ? current : null);
  }, [projectId]);

  useEffect(() => {
    let live = true;
    setVersions(null); setComponents([]); setLibrary([]); setSelectedId(null); setError(null);
    if (projectId) {
      void Promise.all([listWorkspaces(), listDesignVersions(projectId)]).then(async ([workspaces, next]) => {
        const active = next.versions.find((item) => item.id === next.active_version_id);
        if (!active) throw new Error("The active Design version is unavailable.");
        const [tree, published] = await Promise.all([
          listDesignComponents(projectId, active.id), listStudioLibrary(active.data_workspace_id)
        ]);
        if (!live) return;
        setProjectName(workspaces.find((item) => item.id === projectId)?.name ?? "Project");
        setVersions(next); setComponents(tree); setLibrary(published);
      }).catch((cause: Error) => { if (live) setError(cause.message); });
    }
    return () => { live = false; };
  }, [projectId]);

  const perform = async (action: () => Promise<unknown>) => {
    setBusy(true); setError(null);
    try { await action(); await reload(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Design operation failed."); }
    finally { setBusy(false); }
  };
  const active = versions?.versions.find((item) => item.id === versions.active_version_id);
  useEffect(() => { setWorkshop(null); }, [active?.id]);
  const selected = components.find((item) => item.id === selectedId);
  useEffect(() => {
    let live = true;
    setGeometryCandidates([]); setGeometrySelection("");
    if (active) void listBluecadCandidates(active.data_workspace_id).then((items) => {
      if (live) setGeometryCandidates(items.filter((item) => item.status === "valid"));
    }).catch((cause: unknown) => { if (live) setError(cause instanceof Error ? cause.message : "BlueCad candidates are unavailable."); });
    return () => { live = false; };
  }, [active?.data_workspace_id, active?.id]);
  useEffect(() => {
    let live = true;
    setGeometryAggregate(null);
    if (active && selected?.geometry_candidate_id) {
      void getBluecadCandidateAggregate(active.data_workspace_id, selected.geometry_candidate_id).then((item) => {
        if (live) setGeometryAggregate(item);
      }).catch((cause: unknown) => { if (live) setError(cause instanceof Error ? cause.message : "Attached geometry is unavailable."); });
    }
    return () => { live = false; };
  }, [active?.data_workspace_id, selected?.geometry_candidate_id]);
  useEffect(() => {
    let live = true;
    setSourceUnit(null); setSourceRevision(null); setSourceError(null);
    if (active && selected?.source_draft_id && selected.source_unit_id) {
      void getDraft(active.data_workspace_id, selected.source_draft_id).then((process) => {
        if (!live) return;
        setSourceRevision(process.revision);
        const unit = process.objects.find((item) => item.id === selected.source_unit_id && item.kind === "unit");
        if (unit) setSourceUnit(unit);
        else setSourceError("The source Process unit is no longer in this draft.");
      }).catch((cause: unknown) => {
        if (live) setSourceError(cause instanceof Error ? cause.message : "Process source is unavailable.");
      });
    }
    return () => { live = false; };
  }, [active?.data_workspace_id, selected?.source_draft_id, selected?.source_unit_id]);
  const descendants = new Set<string>();
  if (selected) {
    const visit = (id: string) => {
      if (descendants.has(id)) return;
      descendants.add(id);
      components.filter((item) => item.parent_id === id).forEach((item) => visit(item.id));
    };
    visit(selected.id);
  }
  const selectComponent = (item: DesignComponent) => {
    setSelectedId(item.id); setSelectedNode("Parameters");
    setGeometrySelection("");
    setEditName(item.name); setEditParent(item.parent_id ?? "");
  };
  const openUnit = async (draftId: string, revision: string, unit: DraftObject) => {
    if (!projectId || !active) return;
    setBusy(true); setError(null);
    try {
      const component = await openDesignUnit(projectId, active.id, draftId, revision, unit.id);
      await reload();
      selectComponent(component); setStage("CAD");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not open the Process unit."); }
    finally { setBusy(false); }
  };

  function tree(parentId: string | null, depth = 0): ReactNode {
    return components.filter((item) => item.parent_id === parentId).map((item) => (
      <div key={item.id} className="design-project__tree-row" style={{ paddingInlineStart: `${depth * 1.1}rem` }}>
        <button type="button" aria-current={selectedId === item.id ? "true" : undefined} onClick={() => selectComponent(item)}>{item.name}</button>
        {tree(item.id, depth + 1)}
      </div>
    ));
  }

  if (!projectId) return <p>Select a project to open Design.</p>;
  return <div className="design-project">
    <header className="design-project__header">
      <div><p className="eyebrow">Design · Phase 1</p><h1>{projectName || "Project"}</h1></div>
      <div className="design-project__version">
        <label htmlFor="design-version">Project version</label>
        <select id="design-version" value={versions?.active_version_id ?? ""} disabled={!versions || busy}
          onChange={(event) => { if (versions) void perform(() => activateDesignVersion(projectId, event.target.value, versions.active_version_id)); }}>
          {versions?.versions.map((item) => <option key={item.id} value={item.id}>{item.label}{item.starts_empty ? " · empty start" : ""}</option>)}
        </select>
      </div>
    </header>
    {error ? <p role="alert" className="design-project__error">{error}</p> : null}
    <nav className="design-project__stages" aria-label="Design stages">
      {STAGES.map((item) => <button key={item} type="button" aria-current={stage === item ? "step" : undefined} onClick={() => {
        setWorkshop(null); setStage(item);
        if (item === "Plant") setSelectedId(null);
        else if (item === "CAD") setSelectedNode("Geometry");
        else if (item === "Reduced model") setSelectedNode("Reduced model");
        else setSelectedNode("Physics");
      }}>{item}</button>)}
    </nav>
    {workshop && active ? <section className="design-project__workshop" aria-label="Workshop">
      <div className="design-project__workshop-head"><h2>Workshop · {active.label}</h2><button type="button" onClick={() => { setWorkshop(null); void reload(); }}>Back to Design</button></div>
      <Studio key={`${active.data_workspace_id}:${workshop.key}`} workspaceId={active.data_workspace_id} navigate={navigate}
        engineeringProperties={engineeringProperties} requestedModelId={workshop.modelId} startWizard={!workshop.modelId} embedded />
    </section> : <div className="design-project__body">
      <aside className="design-project__panel">
        <h2>Components</h2>
        {components.length ? tree(null) : <p>No components in this version.</p>}
        <form onSubmit={(event) => { event.preventDefault(); if (!active || !newComponent.trim()) return; void perform(async () => { await createDesignComponent(projectId, active.id, newComponent.trim(), selectedId); setNewComponent(""); }); }}>
          <label htmlFor="design-component-name">{selected ? `Add within ${selected.name}` : "Add a component"}</label>
          <input id="design-component-name" value={newComponent} maxLength={120} onChange={(event) => setNewComponent(event.target.value)} />
          <button type="submit" disabled={!active || busy || !newComponent.trim()}>Add</button>
        </form>
        {selected && active ? <form onSubmit={(event) => { event.preventDefault(); if (!editName.trim()) return;
          void perform(() => editDesignComponent(projectId, active.id, selected, editName.trim(), editParent || null));
        }}>
          <h3>Edit {selected.name}</h3>
          <label htmlFor="design-edit-name">Name</label>
          <input id="design-edit-name" value={editName} maxLength={120} onChange={(event) => setEditName(event.target.value)} />
          <label htmlFor="design-edit-parent">Parent component</label>
          <select id="design-edit-parent" value={editParent} onChange={(event) => setEditParent(event.target.value)}>
            <option value="">Plant</option>
            {components.filter((item) => !descendants.has(item.id)).map((item) =>
              <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
          <button type="submit" disabled={busy || !editName.trim() ||
            (editName.trim() === selected.name && editParent === (selected.parent_id ?? ""))}>Save component</button>
        </form> : null}
      </aside>
      <main className="design-project__panel design-project__main">
        <h2>{selected?.name ?? stage}</h2>
        {selected?.source_unit_id ? <p>Process unit model · source draft {selected.source_draft_id?.slice(0, 8)} · unit {selected.source_unit_id.slice(0, 8)}. Process owns the 0D/1D calculation; {selected.geometry_candidate_id ? "validated BlueCad geometry is attached" : "no validated geometry is attached yet"}. No CFD is implied.</p> : null}
        {selected ? <>
          <div className="design-project__nodes" aria-label="Component model tree">{NODES.map((node) => <button key={node} type="button" aria-pressed={selectedNode === node} onClick={() => { setSelectedNode(node); setStage(node === "Geometry" ? "CAD" : node === "Reduced model" ? "Reduced model" : node === "Physics" || node === "Mesh" ? "CFD" : "Plant"); }}>{node}</button>)}</div>
          <section aria-label={`${selectedNode} details`}><h3>{selectedNode}</h3>
            {selectedNode === "Geometry" && selected.geometry_candidate_id ? <>
              <p>A validated BlueCad candidate is attached to this component in the active project version.</p>
              {selected.geometry_source_draft_revision ? <p>Process source revision: {selected.geometry_source_draft_revision.slice(0, 12)}</p> : null}
              <details><summary>Geometry reference</summary><code>{selected.geometry_candidate_id}</code></details>
              {active && geometryAggregate?.candidate.id === selected.geometry_candidate_id && geometryAggregate.candidate.glb_artifact_id
                ? <BluecadGlbViewer artifactUrl={bluecadArtifactContentUrl(active.data_workspace_id, geometryAggregate.candidate.glb_artifact_id)} />
                : <p>Loading geometry preview or no GLB artifact is available.</p>}
              <p>Geometry remains a separate BlueCad candidate; no CFD or reduced model is implied.</p>
            </> : selectedNode === "Parameters" && selected.source_unit_id ? <>
              {sourceError ? <p role="status">{sourceError}</p> : sourceUnit ? <>
                <p>{sourceUnit.tag} · {sourceUnit.type} · Process 0D/1D model. Values below are read from the active version's Process draft.</p>
                {Object.entries(sourceUnit.params ?? {}).length ? <dl>{Object.entries(sourceUnit.params ?? {}).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value.value} {value.unit}</dd></div>)}</dl> : <p>No typed Process design parameters are set for this unit.</p>}
              </> : <p>Loading Process parameters…</p>}
            </> : <p>{selectedNode === "Parameters" ? "No Process source is attached to this component." : `No ${selectedNode.toLowerCase()} capability is attached to this component yet.`}</p>}
          </section>
          {selectedNode === "Geometry" && active ? <form onSubmit={(event) => {
            event.preventDefault();
            if (!geometrySelection || (selected.source_draft_id && !sourceRevision)) return;
            void perform(() => attachDesignGeometry(projectId, active.id, selected, geometrySelection,
              selected.source_draft_id ? sourceRevision : null));
          }}>
            <label htmlFor="design-geometry-candidate">Attach validated BlueCad candidate</label>
            <select id="design-geometry-candidate" value={geometrySelection} onChange={(event) => setGeometrySelection(event.target.value)}>
              <option value="">Choose a candidate</option>
              {geometryCandidates.map((item) => <option key={item.id} value={item.id}>{item.brief_text.slice(0, 80)} · {item.id.slice(0, 8)}</option>)}
            </select>
            <button type="submit" disabled={busy || !geometrySelection || Boolean(selected.source_draft_id && !sourceRevision)}>Attach geometry</button>
            {!geometryCandidates.length ? <p>No validated BlueCad candidates in this project version.</p> : null}
          </form> : null}
        </> : null}
        {stage === "Plant" && !selected && active ? <>
          <p>Flowsheet edits and runs use this version's Process data context. The Process editor owns its revisions and solver results.</p>
          <ProcessDraftEditor key={active.data_workspace_id} workspaceId={active.data_workspace_id} navigate={navigate} onOpenUnit={(draftId, revision, unit) => void openUnit(draftId, revision, unit)} />
        </> : <p>{stage === "Plant" ? "Select Plant to edit this version's flowsheet." : `${stage} is a navigation placeholder in this Phase 1 checkpoint.`}</p>}
        {active?.id === projectId ? <AppLink href="/design/process" navigate={navigate}>Open old Process view</AppLink> : null}
      </main>
      <aside className="design-project__panel">
        <h2>Library</h2>
        {library.length ? <ul>{library.map((item) => <li key={item.id}><button type="button" onClick={() => setWorkshop({ modelId: item.model_spec_id, key: Date.now() })}>{item.name} · {item.version_label}</button></li>)}</ul> : <p>No published Studio models in this version.</p>}
        <button type="button" disabled={!active} onClick={() => setWorkshop({ modelId: null, key: Date.now() })}>Generate new in Workshop</button>
        {active?.id === projectId ? <AppLink href="/design/studio" navigate={navigate}>Open current Studio workspace</AppLink> : null}
        <h2>Versions</h2>
        <form onSubmit={(event) => { event.preventDefault(); if (!versions || !newVersion.trim()) return; void perform(async () => { await createDesignVersion(projectId, newVersion.trim(), versions.active_version_id); setNewVersion(""); }); }}>
          <label htmlFor="design-new-version">New empty version from current</label>
          <input id="design-new-version" value={newVersion} maxLength={80} onChange={(event) => setNewVersion(event.target.value)} />
          <button type="submit" disabled={!versions || busy || !newVersion.trim()}>Create</button>
        </form>
        <p><AppLink href="/design/bluecad" navigate={navigate}>Open old Design</AppLink></p>
      </aside>
    </div>}
  </div>;
}
