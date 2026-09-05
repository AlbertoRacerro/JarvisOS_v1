import { useEffect, useMemo, useState } from "react";

import { listWorkspaces, type Workspace } from "../api/client";
import {
  getModelDossier,
  listModelDossiers,
  type ModelDossierDetail,
  type ModelDossierIndexItem
} from "../api/modelDossier";

type Props = Readonly<{
  workspaceId: string | null;
  onWorkspaceChange: (workspaceId: string) => void;
}>;

function Empty({ children }: Readonly<{ children: React.ReactNode }>) {
  return <div className="final-fusion__source-empty">{children}</div>;
}

function Value({ label, value }: Readonly<{ label: string; value?: string | null }>) {
  return <div className="final-fusion__disclosure-row"><span>›</span><strong>{label}</strong><em>{value || "Unknown"}</em></div>;
}

export default function ModelDossier({ workspaceId, onWorkspaceChange }: Props) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [index, setIndex] = useState<ModelDossierIndexItem[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ModelDossierDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const activeWorkspaceId = useMemo(() => workspaceId ?? workspaces[0]?.id ?? null, [workspaceId, workspaces]);
  const versions = useMemo(() => index.flatMap((item) => item.versions.map((version) => ({ item, version }))), [index]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    void listWorkspaces().then((items) => {
      if (!alive) return;
      setWorkspaces(items);
      if (!workspaceId && items[0]) onWorkspaceChange(items[0].id);
    }).catch((cause: unknown) => {
      if (alive) setError(cause instanceof Error ? cause.message : "Workspace read failed");
    }).finally(() => {
      if (alive) setLoading(false);
    });
    return () => { alive = false; };
  }, [onWorkspaceChange, workspaceId]);

  useEffect(() => {
    if (!activeWorkspaceId) {
      setIndex([]);
      setSelectedVersionId(null);
      setDetail(null);
      return;
    }
    let alive = true;
    setLoading(true);
    setError(null);
    setDetail(null);
    void listModelDossiers(activeWorkspaceId).then((items) => {
      if (!alive) return;
      setIndex(items);
      const firstVersion = items.flatMap((item) => item.versions)[0]?.model_version_id ?? null;
      setSelectedVersionId((current) => items.some((item) => item.versions.some((version) => version.model_version_id === current)) ? current : firstVersion);
    }).catch((cause: unknown) => {
      if (alive) setError(cause instanceof Error ? cause.message : "Model dossier index read failed");
    }).finally(() => {
      if (alive) setLoading(false);
    });
    return () => { alive = false; };
  }, [activeWorkspaceId]);

  useEffect(() => {
    if (!activeWorkspaceId || !selectedVersionId) {
      setDetail(null);
      return;
    }
    let alive = true;
    setLoading(true);
    setError(null);
    void getModelDossier(activeWorkspaceId, selectedVersionId).then((value) => {
      if (alive) setDetail(value);
    }).catch((cause: unknown) => {
      if (alive) setError(cause instanceof Error ? cause.message : "Exact model-version dossier read failed");
    }).finally(() => {
      if (alive) setLoading(false);
    });
    return () => { alive = false; };
  }, [activeWorkspaceId, selectedVersionId]);

  return <div className="final-fusion__workbench final-fusion__workbench--models">
    <section className="final-fusion__panel final-fusion__versions" aria-label="Model versions">
      <header className="final-fusion__panel-head"><h2>Model versions</h2><span>Exact-version READ</span></header>
      <div className="final-fusion__toolbar-line"><span>Project workspace</span><select aria-label="Project workspace" value={activeWorkspaceId ?? ""} onChange={(event) => onWorkspaceChange(event.target.value)} disabled={!workspaces.length}><option value="">Select workspace…</option>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}</select></div>
      <div className="final-fusion__searchbox">Canonical dossier index; each selection is bound to exact model_version_id.</div>
      {loading && !versions.length ? <Empty><strong>Loading model dossiers…</strong></Empty> : error && !versions.length ? <Empty><strong>Backend read failed</strong><span>{error}</span></Empty> : versions.length ? <div className="final-fusion__source-list">{versions.map(({ item, version }) => <button type="button" className="final-fusion__disclosure-row" key={version.model_version_id} onClick={() => setSelectedVersionId(version.model_version_id)} aria-pressed={selectedVersionId === version.model_version_id}><span>›</span><strong>{item.title}</strong><em>{version.version_label || version.model_version_id} · {version.status || "Unknown"}</em></button>)}</div> : <Empty><strong>No exact model versions</strong><span>The selected workspace exposes no model dossier versions.</span></Empty>}
      <div className="final-fusion__lineage-slot">Selected exact version · {selectedVersionId ?? "None"}</div>
    </section>

    <section className="final-fusion__panel final-fusion__model-dossier" aria-label="Version dossier">
      <header className="final-fusion__panel-head"><h2>Version dossier</h2><span>{detail ? "Canonical READ" : loading ? "Loading" : "Unavailable"}</span></header>
      <div className="final-fusion__dossier-top"><strong>{detail?.title ?? "Exact model / version"}</strong><span>{detail?.identity.model_version_id ?? "No exact version selected"}</span></div>
      <div className="final-fusion__summary-strip"><span>Model spec · {detail?.identity.model_spec_id ?? "Unknown"}</span><span>Status · {detail?.identity.status ?? "Unknown"}</span><span>Maturity · {detail?.maturity_status ?? "Unknown"}</span></div>
      {error && <Empty><strong>Exact-version read failed</strong><span>{error}</span></Empty>}
      <div className="final-fusion__dossier-grid">
        <section><header><strong>Definition</strong><span>READ</span></header><p>{detail?.engineering_question ?? "Unknown"}</p><p>{detail?.scope ?? "Scope unavailable"}</p></section>
        <section><header><strong>Assumptions</strong><span>Summary</span></header><p>{detail?.assumptions_summary ?? "Unknown"}</p></section>
        <section><header><strong>Parameters & Inputs</strong><span>Summary</span></header><p>{detail?.inputs_summary ?? "Unknown"}</p></section>
        <section><header><strong>Outputs</strong><span>Summary</span></header><p>{detail?.outputs_summary ?? "Unknown"}</p></section>
        <section><header><strong>Runs</strong><span>{detail?.runs.length ?? 0}</span></header>{detail?.runs.length ? detail.runs.map((run) => <Value key={run.run_id} label={run.run_label || run.run_id} value={`${run.status} · ${run.project_knowledge_revision_id || "no PK revision"}`} />) : <p>No version-bound runs.</p>}</section>
        <section><header><strong>Artifacts</strong><span>{detail?.artifacts.length ?? 0}</span></header>{detail?.artifacts.length ? detail.artifacts.map((artifact) => <Value key={artifact.artifact_id} label={artifact.role || artifact.artifact_id} value={`${artifact.availability}${artifact.digest ? ` · ${artifact.digest}` : ""}`} />) : <p>No version-bound artifacts.</p>}</section>
        <section><header><strong>Freshness & Evidence</strong><span>{detail?.evidence.length ?? 0}</span></header>{detail?.evidence.length ? detail.evidence.map((evidence) => <Value key={evidence.evidence_id} label={evidence.kind || evidence.evidence_id} value={`${evidence.freshness || "Unknown freshness"} · ${evidence.availability}`} />) : <p>No explicit evidence records.</p>}</section>
        <section><header><strong>Changelog / Lineage</strong><span>Identity</span></header><Value label="Version label" value={detail?.identity.version_label} /><Value label="Implementation" value={detail?.identity.implementation_kind} /><Value label="Input contract digest" value={detail?.identity.input_contract_digest} /><Value label="Created" value={detail?.identity.created_at} /></section>
      </div>
      <div className="final-fusion__context-strip">Browsing is context-neutral. This surface does not add dossier records to Project Context or invoke mutation authority.</div>
    </section>

    <section className="final-fusion__panel final-fusion__jarvis" aria-label="Jarvis"><header className="final-fusion__panel-head"><h2>Jarvis</h2><span>Read context only</span></header><div className="final-fusion__jarvis-body"><div className="final-fusion__context-note">Exact-version browsing does not add records to Jarvis context. Explicit context insertion remains governed separately.</div><div className="final-fusion__bubble">{detail ? `Viewing exact model_version_id ${detail.identity.model_version_id}.` : "Select an exact model version to inspect canonical dossier evidence."}</div><div className="final-fusion__composer" aria-disabled="true"><span>Ask Jarvis about an explicitly inserted model context…</span><button type="button" disabled>Send</button></div></div></section>
  </div>;
}
