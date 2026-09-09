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

const plainDisclosureRowStyle = { gridTemplateColumns: "minmax(0, 1fr) auto" } as const;

function Empty({ children }: Readonly<{ children: React.ReactNode }>) {
  return <div className="final-fusion__source-empty">{children}</div>;
}

function Value({ label, value }: Readonly<{ label: string; value?: string | null }>) {
  return <div className="final-fusion__disclosure-row" style={plainDisclosureRowStyle}><strong>{label}</strong><em>{value || "Unknown"}</em></div>;
}

function TechnicalDetails({ children }: Readonly<{ children: React.ReactNode }>) {
  return <details><summary>Technical details</summary>{children}</details>;
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
      <header className="final-fusion__panel-head"><h2>Model versions</h2><span>Canonical READ</span></header>
      <div className="final-fusion__toolbar-line"><span>Project workspace</span><select aria-label="Project workspace" value={activeWorkspaceId ?? ""} onChange={(event) => onWorkspaceChange(event.target.value)} disabled={!workspaces.length}><option value="">Select workspace…</option>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}</select></div>
      <div className="final-fusion__searchbox">Choose a model by its human title, version and current status. Exact identifiers remain available in Technical details.</div>
      {loading && !versions.length ? <Empty><strong>Loading model dossiers…</strong></Empty> : error && !versions.length ? <Empty><strong>Backend read failed</strong><span>{error}</span></Empty> : versions.length ? <div className="final-fusion__source-list">{versions.map(({ item, version }) => <button type="button" className="final-fusion__disclosure-row" style={plainDisclosureRowStyle} key={version.model_version_id} onClick={() => setSelectedVersionId(version.model_version_id)} aria-pressed={selectedVersionId === version.model_version_id}><strong>{item.title}</strong><em>{version.version_label || "Unlabelled version"} · {version.status || "Unknown status"}</em></button>)}</div> : <Empty><strong>No model versions</strong><span>The selected workspace exposes no model dossier versions.</span></Empty>}
      <div className="final-fusion__lineage-slot">{detail ? `Selected · ${detail.title} · ${detail.identity.version_label || "Unlabelled version"}` : "No model version selected"}</div>
    </section>

    <section className="final-fusion__panel final-fusion__model-dossier" aria-label="Version dossier">
      <header className="final-fusion__panel-head"><h2>Version dossier</h2><span>{detail ? "Canonical READ" : loading ? "Loading" : "Unavailable"}</span></header>
      <div className="final-fusion__dossier-top"><strong>{detail?.title ?? "Model / version"}</strong><span>{detail?.identity.version_label ?? "No version selected"}</span></div>
      <div className="final-fusion__summary-strip"><span>Status · {detail?.identity.status ?? "Unknown"}</span><span>Maturity · {detail?.maturity_status ?? "Unknown"}</span><span>Runs · {detail?.runs.length ?? 0}</span><span>Evidence · {detail?.evidence.length ?? 0}</span></div>
      {detail ? <TechnicalDetails><Value label="Model version ID" value={detail.identity.model_version_id} /><Value label="Model spec ID" value={detail.identity.model_spec_id} /></TechnicalDetails> : null}
      {error && <Empty><strong>Version read failed</strong><span>{error}</span></Empty>}
      <div className="final-fusion__dossier-grid">
        <section><header><strong>Definition</strong><span>READ</span></header><p>{detail?.engineering_question ?? "Unknown"}</p><p>{detail?.scope ?? "Scope unavailable"}</p></section>
        <section><header><strong>Assumptions</strong><span>Summary</span></header><p>{detail?.assumptions_summary ?? "Unknown"}</p></section>
        <section><header><strong>Parameters & Inputs</strong><span>Summary</span></header><p>{detail?.inputs_summary ?? "Unknown"}</p></section>
        <section><header><strong>Outputs</strong><span>Summary</span></header><p>{detail?.outputs_summary ?? "Unknown"}</p></section>
        <section><header><strong>Runs</strong><span>{detail?.runs.length ?? 0}</span></header>{detail?.runs.length ? detail.runs.map((run) => <div key={run.run_id}><Value label={run.run_label || "Model run"} value={run.status || "Unknown status"} /><TechnicalDetails><Value label="Run ID" value={run.run_id} /><Value label="Project Knowledge revision" value={run.project_knowledge_revision_id} /></TechnicalDetails></div>) : <p>No version-bound runs.</p>}</section>
        <section><header><strong>Artifacts</strong><span>{detail?.artifacts.length ?? 0}</span></header>{detail?.artifacts.length ? detail.artifacts.map((artifact) => <div key={artifact.artifact_id}><Value label={artifact.role || "Artifact"} value={artifact.availability || "Unknown availability"} /><TechnicalDetails><Value label="Artifact ID" value={artifact.artifact_id} /><Value label="Digest" value={artifact.digest} /></TechnicalDetails></div>) : <p>No version-bound artifacts.</p>}</section>
        <section><header><strong>Freshness & Evidence</strong><span>{detail?.evidence.length ?? 0}</span></header>{detail?.evidence.length ? detail.evidence.map((evidence) => <div key={evidence.evidence_id}><Value label={evidence.kind || "Evidence"} value={`${evidence.freshness || "Unknown freshness"} · ${evidence.availability}`} /><TechnicalDetails><Value label="Evidence ID" value={evidence.evidence_id} /></TechnicalDetails></div>) : <p>No explicit evidence records.</p>}</section>
        <section><header><strong>Version lineage</strong><span>Identity</span></header><Value label="Version label" value={detail?.identity.version_label} /><Value label="Implementation" value={detail?.identity.implementation_kind} />{detail ? <TechnicalDetails><Value label="Input contract digest" value={detail.identity.input_contract_digest} /><Value label="Created" value={detail.identity.created_at} /></TechnicalDetails> : null}</section>
      </div>
      <div className="final-fusion__context-strip">Browsing is context-neutral. This surface does not add dossier records to Project Context or invoke mutation authority.</div>
    </section>

    <section className="final-fusion__panel final-fusion__jarvis" aria-label="Jarvis"><header className="final-fusion__panel-head"><h2>Jarvis</h2><span>Read context only</span></header><div className="final-fusion__jarvis-body"><div className="final-fusion__context-note">Model browsing does not add records to Jarvis context. Explicit context insertion remains governed separately.</div><div className="final-fusion__bubble">{detail ? `Viewing ${detail.title}, ${detail.identity.version_label || "unlabelled version"}.` : "Select a model version to inspect canonical dossier evidence."}</div><div className="final-fusion__composer" aria-disabled="true"><span>Ask Jarvis about an explicitly inserted model context…</span><button type="button" disabled>Send</button></div></div></section>
  </div>;
}
