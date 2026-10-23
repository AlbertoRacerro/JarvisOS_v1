import { useCallback, useEffect, useState, type ReactNode } from "react";
import AppLink, { type Navigate } from "../app/AppLink";
import { listWorkspaces } from "../api/client";
import {
  activateDesignVersion, createDesignComponent, createDesignVersion,
  listDesignComponents, listDesignVersions,
  type DesignComponent, type DesignVersionSet
} from "../api/designProject";
import { listStudioLibrary, type StudioLibraryEntry } from "../api/studio";
import ProcessDraftEditor from "../stages/ProcessDraftEditor";
import "./designProject.css";

const NODES = ["Parameters", "Geometry", "Materials", "Physics", "Mesh", "Studies", "Results", "Reduced model"] as const;
const STAGES = ["Plant", "CAD", "Motion/Mechanics", "CFD", "Optics", "Reduced model"] as const;

export default function DesignProject({ projectId, navigate }: { projectId: string | null; navigate: Navigate }) {
  const [projectName, setProjectName] = useState("");
  const [versions, setVersions] = useState<DesignVersionSet | null>(null);
  const [components, setComponents] = useState<DesignComponent[]>([]);
  const [library, setLibrary] = useState<StudioLibraryEntry[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [stage, setStage] = useState<(typeof STAGES)[number]>("Plant");
  const [newVersion, setNewVersion] = useState("");
  const [newComponent, setNewComponent] = useState("");
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
  const selected = components.find((item) => item.id === selectedId);

  function tree(parentId: string | null, depth = 0): ReactNode {
    return components.filter((item) => item.parent_id === parentId).map((item) => (
      <div key={item.id} className="design-project__tree-row" style={{ paddingInlineStart: `${depth * 1.1}rem` }}>
        <button type="button" aria-current={selectedId === item.id ? "true" : undefined} onClick={() => setSelectedId(item.id)}>{item.name}</button>
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
      {STAGES.map((item) => <button key={item} type="button" aria-current={stage === item ? "step" : undefined} onClick={() => { setStage(item); if (item === "Plant") setSelectedId(null); }}>{item}</button>)}
    </nav>
    <div className="design-project__body">
      <aside className="design-project__panel">
        <h2>Components</h2>
        {components.length ? tree(null) : <p>No components in this version.</p>}
        <form onSubmit={(event) => { event.preventDefault(); if (!active || !newComponent.trim()) return; void perform(async () => { await createDesignComponent(projectId, active.id, newComponent.trim(), selectedId); setNewComponent(""); }); }}>
          <label htmlFor="design-component-name">{selected ? `Add within ${selected.name}` : "Add a component"}</label>
          <input id="design-component-name" value={newComponent} maxLength={120} onChange={(event) => setNewComponent(event.target.value)} />
          <button type="submit" disabled={!active || busy || !newComponent.trim()}>Add</button>
        </form>
      </aside>
      <main className="design-project__panel design-project__main">
        <h2>{selected?.name ?? stage}</h2>
        {selected ? <div className="design-project__nodes" aria-label="Component model tree">{NODES.map((node) => <button key={node} type="button" onClick={() => setStage(node === "Geometry" ? "CAD" : node === "Reduced model" ? "Reduced model" : node === "Physics" || node === "Mesh" ? "CFD" : "Plant")}>{node}</button>)}</div> : null}
        {stage === "Plant" && !selected && active ? <>
          <p>Flowsheet edits and runs use this version's Process data context. The Process editor owns its revisions and solver results.</p>
          <ProcessDraftEditor key={active.data_workspace_id} workspaceId={active.data_workspace_id} navigate={navigate} />
        </> : <p>{stage === "Plant" ? "Select Plant to edit this version's flowsheet." : `${stage} is a navigation placeholder in this Phase 1 checkpoint.`}</p>}
        {active?.id === projectId ? <AppLink href="/design/process" navigate={navigate}>Open old Process view</AppLink> : null}
      </main>
      <aside className="design-project__panel">
        <h2>Library</h2>
        {library.length ? <ul>{library.map((item) => <li key={item.id}>{item.name} · {item.version_label}</li>)}</ul> : <p>No published Studio models in this version.</p>}
        {active?.id === projectId ? <AppLink href="/design/studio" navigate={navigate}>Open current Studio workspace</AppLink> : null}
        <h2>Versions</h2>
        <form onSubmit={(event) => { event.preventDefault(); if (!versions || !newVersion.trim()) return; void perform(async () => { await createDesignVersion(projectId, newVersion.trim(), versions.active_version_id); setNewVersion(""); }); }}>
          <label htmlFor="design-new-version">New empty version from current</label>
          <input id="design-new-version" value={newVersion} maxLength={80} onChange={(event) => setNewVersion(event.target.value)} />
          <button type="submit" disabled={!versions || busy || !newVersion.trim()}>Create</button>
        </form>
        <p><AppLink href="/design/bluecad" navigate={navigate}>Open old Design</AppLink></p>
      </aside>
    </div>
  </div>;
}
