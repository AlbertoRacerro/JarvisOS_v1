import { useEffect, useMemo, useState } from "react";

import { listWorkspaces, type Workspace } from "../api/client";
import {
  listLiteratureSources,
  literatureContentUrl,
  type LiteratureEntry,
  type LiteratureSource
} from "../api/literature";

type Props = Readonly<{
  workspaceId: string | null;
  onWorkspaceChange: (workspaceId: string) => void;
}>;

function locationLabel(entry: LiteratureEntry): string {
  if (!entry.locator_kind) return "Location not recorded";
  if (entry.locator_start === null) return entry.locator_kind;
  if (entry.locator_end !== null && entry.locator_end !== entry.locator_start) {
    return `${entry.locator_kind} ${entry.locator_start}–${entry.locator_end}`;
  }
  return `${entry.locator_kind} ${entry.locator_start}`;
}

function entryValue(entry: LiteratureEntry): string {
  if (entry.entry_kind === "claim") return entry.statement ?? "Claim unavailable";
  if (entry.value_number !== null) return `${entry.value_number}${entry.unit ? ` ${entry.unit}` : ""}`;
  return entry.value_text ?? "Datum unavailable";
}

function SourceDisclosure({ source }: Readonly<{ source: LiteratureSource }>) {
  const contentUrl = literatureContentUrl(source);
  return <details className="final-fusion__disclosure" data-source-id={source.id}>
    <summary className="final-fusion__disclosure-row">
      <span><strong>{source.title}</strong><small>{source.source_kind}{source.published_year ? ` · ${source.published_year}` : ""}</small></span>
      <em>{source.state}</em>
    </summary>
    <div className="final-fusion__disclosure-body">
      <div className="final-fusion__detail-grid">
        <div>
          <h3>Source</h3>
          <p>{source.citation || "Citation metadata not recorded."}</p>
          <p>{source.publisher || "Publisher not recorded."}</p>
          <small>{source.source_ref}</small>
          {source.backing ? <p>{source.backing.filename} · {source.backing.mime_type || "unknown MIME"}</p> : <p>No backing artifact registered.</p>}
          {contentUrl ? <a className="final-fusion__link" href={contentUrl} target="_blank" rel="noreferrer">Open source</a> : <p>Safe preview unavailable.</p>}
        </div>
        <div>
          <h3>Claims & data</h3>
          {source.entries.length === 0 ? <p>No structured claims or data have been curated for this source.</p> : source.entries.map((entry) => <article key={entry.id} className="final-fusion__record-card">
            <div className="final-fusion__record-heading"><strong>{entry.entry_kind === "claim" ? "Claim" : "Datum"}</strong><em>{entry.status}</em></div>
            <p>{entryValue(entry)}</p>
            <small>{locationLabel(entry)} · {entry.provenance_ref}</small>
            {entry.context_text ? <p>{entry.context_text}</p> : null}
            <div><strong>Used by</strong>{entry.used_by.length === 0 ? <p>Not referenced by canonical records.</p> : <ul>{entry.used_by.map((use) => <li key={use.ref}>{use.kind}: {use.title}</li>)}</ul>}</div>
          </article>)}
        </div>
      </div>
      {contentUrl ? <div className="final-fusion__preview"><iframe title={`Preview ${source.title}`} src={contentUrl} /></div> : null}
    </div>
  </details>;
}

export default function LiteratureKnowledge({ workspaceId, onWorkspaceChange }: Props) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [sources, setSources] = useState<LiteratureSource[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const activeWorkspaceId = useMemo(() => workspaceId ?? workspaces[0]?.id ?? null, [workspaceId, workspaces]);

  useEffect(() => {
    let alive = true;
    void listWorkspaces().then((items) => {
      if (!alive) return;
      setWorkspaces(items);
      if (!workspaceId && items[0]) onWorkspaceChange(items[0].id);
    }).catch((cause: unknown) => {
      if (alive) setError(cause instanceof Error ? cause.message : "Workspace read failed");
    });
    return () => { alive = false; };
  }, [onWorkspaceChange, workspaceId]);

  useEffect(() => {
    if (!activeWorkspaceId) {
      setSources([]);
      setTotal(0);
      setLoading(false);
      return;
    }
    let alive = true;
    setLoading(true);
    setError(null);
    void listLiteratureSources(activeWorkspaceId).then((page) => {
      if (!alive) return;
      setSources(page.items);
      setTotal(page.total);
    }).catch((cause: unknown) => {
      if (alive) setError(cause instanceof Error ? cause.message : "Literature read failed");
    }).finally(() => {
      if (alive) setLoading(false);
    });
    return () => { alive = false; };
  }, [activeWorkspaceId]);

  return <div className="final-fusion__workbench final-fusion__workbench--literature">
    <section className="final-fusion__panel">
      <div className="final-fusion__panel-heading">
        <div><span className="final-fusion__eyebrow">Project knowledge</span><h2>Literature</h2><p>Structured sources, exact provenance, and canonical used-by links.</p></div>
        <select aria-label="Workspace" value={activeWorkspaceId ?? ""} onChange={(event) => onWorkspaceChange(event.target.value)}>
          {workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
        </select>
      </div>
      <div className="final-fusion__summary"><strong>{total}</strong> sources · <span>Browsing does not add Jarvis context.</span></div>
      {loading ? <p className="final-fusion__source-empty">Loading literature…</p> : null}
      {error ? <div className="final-fusion__source-empty" role="alert"><strong>Literature unavailable</strong><p>{error}</p></div> : null}
      {!loading && !error && sources.length === 0 ? <div className="final-fusion__source-empty"><strong>No literature sources yet</strong><p>Register a bounded source through the Literature API; fixture citations are never promoted into production facts.</p></div> : null}
      <div>{sources.map((source) => <SourceDisclosure key={source.id} source={source} />)}</div>
    </section>
  </div>;
}
