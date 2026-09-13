import { useEffect, useRef, useState } from "react";

import {
  previewKnowledgeContext,
  proposeKnowledgeAction,
  type KnowledgeContextPreview,
  type KnowledgeOwner,
  type KnowledgeProposal,
  type KnowledgeRouteId,
  type StableKnowledgeRef
} from "../../api/knowledgeActions";

type Props = Readonly<{
  workspaceId: string | null;
  routeId: string;
  stableRef: string | null;
}>;

const OWNERS: Partial<Record<KnowledgeRouteId, KnowledgeOwner>> = {
  "memory-project-basis": "modeling",
  "memory-models": "model-dossier",
  "memory-literature": "literature"
};

function isKnowledgeRoute(routeId: string): routeId is KnowledgeRouteId {
  return routeId in OWNERS;
}

function emptyBasket(): Record<KnowledgeRouteId, string[]> {
  return {
    "memory-project-basis": [],
    "memory-models": [],
    "memory-literature": []
  };
}

function emptyPreviews(): Partial<Record<KnowledgeRouteId, KnowledgeContextPreview>> {
  return {};
}

function boundedManifestEntry(entry: Record<string, unknown>): string {
  const serialized = JSON.stringify(entry);
  return serialized.length > 800 ? `${serialized.slice(0, 797)}…` : serialized;
}

export default function JarvisKnowledgeActions({ workspaceId, routeId, stableRef }: Props) {
  const [basket, setBasket] = useState<Record<KnowledgeRouteId, string[]>>(emptyBasket);
  const [previews, setPreviews] = useState<Partial<Record<KnowledgeRouteId, KnowledgeContextPreview>>>(emptyPreviews);
  const [intent, setIntent] = useState("");
  const [proposal, setProposal] = useState<KnowledgeProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestGeneration = useRef(0);

  useEffect(() => {
    requestGeneration.current += 1;
    setBasket(emptyBasket());
    setPreviews(emptyPreviews());
    setProposal(null);
    setIntent("");
    setError(null);
    setBusy(false);
  }, [workspaceId]);

  useEffect(() => {
    requestGeneration.current += 1;
    setProposal(null);
    setIntent("");
    setError(null);
    setBusy(false);
  }, [routeId, stableRef]);

  if (!isKnowledgeRoute(routeId)) return null;
  const owner = OWNERS[routeId];
  if (!owner) return null;
  const routeBasket = basket[routeId];
  const preview = previews[routeId] ?? null;

  const refsFor = (stableRefs: string[]): StableKnowledgeRef[] => stableRefs.map((ref) => ({ owner, stable_ref: ref }));

  const inspectBasket = async (stableRefs: string[]) => {
    if (!workspaceId || stableRefs.length === 0) return null;
    return previewKnowledgeContext(workspaceId, routeId, refsFor(stableRefs));
  };

  const addContext = async () => {
    if (!workspaceId || !stableRef || busy) return;
    const nextRefs = routeBasket.includes(stableRef) ? routeBasket : [...routeBasket, stableRef];
    const generation = requestGeneration.current;
    setBusy(true);
    setError(null);
    setProposal(null);
    try {
      const nextPreview = await inspectBasket(nextRefs);
      if (generation !== requestGeneration.current || !nextPreview) return;
      setBasket((current) => ({ ...current, [routeId]: nextRefs }));
      setPreviews((current) => ({ ...current, [routeId]: nextPreview }));
    } catch (caught) {
      if (generation !== requestGeneration.current) return;
      setError(caught instanceof Error ? caught.message : "Exact context preview failed");
    } finally {
      if (generation === requestGeneration.current) setBusy(false);
    }
  };

  const removeContext = async (refToRemove: string) => {
    if (!workspaceId || busy) return;
    const nextRefs = routeBasket.filter((ref) => ref !== refToRemove);
    const generation = requestGeneration.current;
    setBusy(true);
    setError(null);
    setProposal(null);
    try {
      if (nextRefs.length === 0) {
        if (generation !== requestGeneration.current) return;
        setBasket((current) => ({ ...current, [routeId]: [] }));
        setPreviews((current) => {
          const next = { ...current };
          delete next[routeId];
          return next;
        });
        return;
      }
      const nextPreview = await inspectBasket(nextRefs);
      if (generation !== requestGeneration.current || !nextPreview) return;
      setBasket((current) => ({ ...current, [routeId]: nextRefs }));
      setPreviews((current) => ({ ...current, [routeId]: nextPreview }));
    } catch (caught) {
      if (generation !== requestGeneration.current) return;
      setError(caught instanceof Error ? caught.message : "Exact context preview failed");
    } finally {
      if (generation === requestGeneration.current) setBusy(false);
    }
  };

  const propose = async () => {
    const text = intent.trim();
    if (!preview || !text || busy) return;
    const generation = requestGeneration.current;
    setBusy(true);
    setError(null);
    setProposal(null);
    try {
      const nextProposal = await proposeKnowledgeAction(preview, text);
      if (generation === requestGeneration.current) setProposal(nextProposal);
    } catch (caught) {
      if (generation !== requestGeneration.current) return;
      setError(caught instanceof Error ? caught.message : "Knowledge proposal failed");
    } finally {
      if (generation === requestGeneration.current) setBusy(false);
    }
  };

  return <section className="jarvis-sidecar__stage-context" aria-label="Knowledge actions" data-testid="knowledge-actions">
    <strong>Knowledge actions</strong>
    <p>{stableRef ? `Selected exact candidate: ${stableRef}` : "Select a Project search result or exact model/literature record first."}</p>
    <button type="button" onClick={() => void addContext()} disabled={!workspaceId || !stableRef || busy || Boolean(stableRef && routeBasket.includes(stableRef))}>
      {busy && !preview ? "Inspecting…" : stableRef && routeBasket.includes(stableRef) ? "Selected context added" : "Add selected to Jarvis context"}
    </button>
    {routeBasket.length ? <div data-testid="knowledge-context-basket">
      <p><strong>Context basket</strong> · {routeBasket.length} exact selection{routeBasket.length === 1 ? "" : "s"}</p>
      <ul>{routeBasket.map((ref) => <li key={ref}><code>{ref}</code> <button type="button" onClick={() => void removeContext(ref)} disabled={busy}>Remove</button></li>)}</ul>
    </div> : null}
    {preview ? <div data-testid="knowledge-context-preview">
      <p><strong>Inspected context</strong> · {preview.included_count} exact ref{preview.included_count === 1 ? "" : "s"}</p>
      <code>{preview.context_digest}</code>
      <small>{preview.estimated_token_count} estimated tokens</small>
      <details open>
        <summary>Inspected source manifest · {preview.context_sources_manifest.length}</summary>
        <ul>{preview.context_sources_manifest.map((source, index) => <li key={`${index}:${boundedManifestEntry(source)}`}><code>{boundedManifestEntry(source)}</code></li>)}</ul>
      </details>
      <label htmlFor="knowledge-proposal-intent">Advisory proposal</label>
      <textarea id="knowledge-proposal-intent" rows={3} maxLength={4000} value={intent} onChange={(event) => setIntent(event.target.value)} disabled={busy} placeholder="Ask Jarvis to propose a bounded change, question, or research step…" />
      <button type="button" onClick={() => void propose()} disabled={!intent.trim() || busy}>{busy ? "Generating…" : "Generate proposal"}</button>
    </div> : null}
    {proposal ? <div data-testid="knowledge-proposal">
      <p><strong>Advisory proposal · {proposal.target_domain}</strong></p>
      <p>{proposal.summary}</p>
      {proposal.proposed_items.length ? <ul>{proposal.proposed_items.map((item) => <li key={item}>{item}</li>)}</ul> : null}
      {proposal.authoritative_next_action ? <small>Authoritative next action: {proposal.authoritative_next_action}</small> : null}
      <small>No domain mutation was performed.</small>
    </div> : null}
    {error ? <p role="status">{error}</p> : null}
  </section>;
}
