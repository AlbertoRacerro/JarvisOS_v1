import { useEffect, useRef, useState } from "react";

import {
  previewKnowledgeContext,
  proposeKnowledgeAction,
  type KnowledgeContextPreview,
  type KnowledgeOwner,
  type KnowledgeProposal,
  type KnowledgeRouteId
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

export default function JarvisKnowledgeActions({ workspaceId, routeId, stableRef }: Props) {
  const [preview, setPreview] = useState<KnowledgeContextPreview | null>(null);
  const [intent, setIntent] = useState("");
  const [proposal, setProposal] = useState<KnowledgeProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const selectionGeneration = useRef(0);

  useEffect(() => {
    selectionGeneration.current += 1;
    setPreview(null);
    setProposal(null);
    setIntent("");
    setError(null);
    setBusy(false);
  }, [workspaceId, routeId, stableRef]);

  if (!isKnowledgeRoute(routeId)) return null;
  const owner = OWNERS[routeId];
  if (!owner) return null;

  const addContext = async () => {
    if (!workspaceId || !stableRef || busy) return;
    const generation = selectionGeneration.current;
    setBusy(true);
    setError(null);
    setProposal(null);
    try {
      const nextPreview = await previewKnowledgeContext(workspaceId, routeId, owner, stableRef);
      if (generation === selectionGeneration.current) setPreview(nextPreview);
    } catch (caught) {
      if (generation !== selectionGeneration.current) return;
      setPreview(null);
      setError(caught instanceof Error ? caught.message : "Exact context preview failed");
    } finally {
      if (generation === selectionGeneration.current) setBusy(false);
    }
  };

  const propose = async () => {
    const text = intent.trim();
    if (!preview || !text || busy) return;
    const generation = selectionGeneration.current;
    setBusy(true);
    setError(null);
    setProposal(null);
    try {
      const nextProposal = await proposeKnowledgeAction(preview, text);
      if (generation === selectionGeneration.current) setProposal(nextProposal);
    } catch (caught) {
      if (generation !== selectionGeneration.current) return;
      setError(caught instanceof Error ? caught.message : "Knowledge proposal failed");
    } finally {
      if (generation === selectionGeneration.current) setBusy(false);
    }
  };

  return <section className="jarvis-sidecar__stage-context" aria-label="Knowledge actions" data-testid="knowledge-actions">
    <strong>Knowledge actions</strong>
    <p>{stableRef ? `Selected exact candidate: ${stableRef}` : "Select a Project search result or exact model/literature record first."}</p>
    <button type="button" onClick={() => void addContext()} disabled={!workspaceId || !stableRef || busy}>
      {busy && !preview ? "Inspecting…" : "Add selected to Jarvis context"}
    </button>
    {preview ? <div data-testid="knowledge-context-preview">
      <p><strong>Inspected context</strong> · {preview.included_count} exact ref</p>
      <code>{preview.context_digest}</code>
      <small>{preview.estimated_token_count} estimated tokens · source manifest bound to this digest</small>
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
