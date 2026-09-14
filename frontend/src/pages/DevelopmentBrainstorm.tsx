import { useEffect, useState } from "react";

import { listWorkspaces, type Workspace } from "../api/client";
import {
  createBrainstormPromotion,
  createBrainstormRaw,
  getBrainstormIdea,
  listBrainstormIdeas,
  listBrainstormPromotions,
  listBrainstormRaw,
  reconcileBrainstorm,
  recordBrainstormDiscussion,
  supersedeBrainstormIdea,
  type BrainstormIdea,
  type BrainstormPromotion,
  type BrainstormRaw
} from "../api/development";

type Props = {
  workspaceId: string | null;
  onWorkspaceChange(next: string | null): void;
};

export default function DevelopmentBrainstorm({ workspaceId, onWorkspaceChange }: Props) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [rawRecords, setRawRecords] = useState<BrainstormRaw[]>([]);
  const [ideas, setIdeas] = useState<BrainstormIdea[]>([]);
  const [promotions, setPromotions] = useState<BrainstormPromotion[]>([]);
  const [expanded, setExpanded] = useState<BrainstormIdea | null>(null);
  const [rawText, setRawText] = useState("");
  const [attachmentType, setAttachmentType] = useState<"run_artifact" | "literature_entry">("run_artifact");
  const [attachmentId, setAttachmentId] = useState("");
  const [sourceRawId, setSourceRawId] = useState("");
  const [title, setTitle] = useState("");
  const [takeaway, setTakeaway] = useState("");
  const [synthesis, setSynthesis] = useState("");
  const [editingIdeaId, setEditingIdeaId] = useState("");
  const [successorId, setSuccessorId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    listWorkspaces().then((rows) => {
      if (!alive) return;
      setWorkspaces(rows);
      if (!workspaceId && rows[0]) onWorkspaceChange(rows[0].id);
      else if (workspaceId && !rows.some((row) => row.id === workspaceId)) onWorkspaceChange(rows[0]?.id ?? null);
    }).catch((exc: unknown) => alive && setError(exc instanceof Error ? exc.message : "Workspace discovery failed."));
    return () => { alive = false; };
  }, [workspaceId, onWorkspaceChange]);

  async function refresh(selectedWorkspaceId: string) {
    const [nextRaw, nextIdeas, nextPromotions] = await Promise.all([
      listBrainstormRaw(selectedWorkspaceId),
      listBrainstormIdeas(selectedWorkspaceId),
      listBrainstormPromotions(selectedWorkspaceId)
    ]);
    setRawRecords(nextRaw);
    setIdeas(nextIdeas);
    setPromotions(nextPromotions);
    if (expanded) {
      const fresh = nextIdeas.find((idea) => idea.id === expanded.id);
      setExpanded(fresh ? await getBrainstormIdea(selectedWorkspaceId, fresh.id) : null);
    }
  }

  useEffect(() => {
    if (!workspaceId) {
      setRawRecords([]);
      setIdeas([]);
      setPromotions([]);
      return;
    }
    let alive = true;
    setError(null);
    Promise.all([
      listBrainstormRaw(workspaceId),
      listBrainstormIdeas(workspaceId),
      listBrainstormPromotions(workspaceId)
    ]).then(([nextRaw, nextIdeas, nextPromotions]) => {
      if (!alive) return;
      setRawRecords(nextRaw);
      setIdeas(nextIdeas);
      setPromotions(nextPromotions);
      if (!sourceRawId && nextRaw[0]) setSourceRawId(nextRaw[0].id);
    }).catch((exc: unknown) => alive && setError(exc instanceof Error ? exc.message : "Brainstorm data failed to load."));
    return () => { alive = false; };
  }, [workspaceId, sourceRawId]);

  async function run(action: () => Promise<void>) {
    if (!workspaceId || busy) return;
    setBusy(true);
    setError(null);
    try {
      await action();
      await refresh(workspaceId);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Brainstorm mutation failed.");
      try {
        await refresh(workspaceId);
      } catch {
        // Preserve the server rejection while avoiding a browser-owned canonical projection.
      }
    } finally {
      setBusy(false);
    }
  }

  const selectedIdea = ideas.find((idea) => idea.id === editingIdeaId);
  const selectedSuccessor = ideas.find((idea) => idea.id === successorId);

  return (
    <main className="operator-page" aria-label="Brainstorm workspace">
      <header className="operator-page__header">
        <div>
          <p className="operator-page__eyebrow">Development</p>
          <h1>Brainstorm</h1>
          <p>Capture immutable RAW thoughts, reconcile them with explicit provenance, and create proposal-only handoffs.</p>
        </div>
        <label>
          Workspace
          <select value={workspaceId ?? ""} onChange={(event) => onWorkspaceChange(event.target.value || null)}>
            <option value="">Select workspace</option>
            {workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
          </select>
        </label>
      </header>

      {error ? <p role="alert" className="operator-error">{error}</p> : null}

      <section className="operator-grid">
        <article className="operator-card">
          <h2>RAW capture</h2>
          <label>
            RAW idea
            <textarea value={rawText} onChange={(event) => setRawText(event.target.value)} placeholder="Capture the original thought exactly as written." />
          </label>
          <label>
            Attachment ref type
            <select value={attachmentType} onChange={(event) => setAttachmentType(event.target.value as "run_artifact" | "literature_entry")}>
              <option value="run_artifact">Run artifact</option>
              <option value="literature_entry">Literature entry</option>
            </select>
          </label>
          <label>
            Attachment ref ID (optional)
            <input value={attachmentId} onChange={(event) => setAttachmentId(event.target.value)} placeholder="Exact existing owner ID" />
          </label>
          <button disabled={!workspaceId || !rawText.trim() || busy} onClick={() => run(async () => {
            const refs = attachmentId.trim() ? [{ ref_type: attachmentType, ref_id: attachmentId.trim(), revision: null }] : [];
            await createBrainstormRaw(workspaceId!, rawText, refs);
            setRawText("");
            setAttachmentId("");
          })}>Capture RAW</button>
          <p>Attachment references are accepted only when the server resolves the exact existing owner ID in this workspace.</p>
          <p><strong>Speech capture:</strong> unavailable — deferred until a bounded media/privacy path exists.</p>
        </article>

        <article className="operator-card">
          <h2>Reconcile</h2>
          <label>
            Source RAW
            <select value={sourceRawId} onChange={(event) => setSourceRawId(event.target.value)}>
              <option value="">Select RAW</option>
              {rawRecords.map((raw) => <option key={raw.id} value={raw.id}>{raw.content.slice(0, 80)}</option>)}
            </select>
          </label>
          <label>
            Existing idea revision
            <select value={editingIdeaId} onChange={(event) => setEditingIdeaId(event.target.value)}>
              <option value="">Create new reconciled idea</option>
              {ideas.filter((idea) => idea.lineage_state !== "SUPERSEDED").map((idea) => <option key={idea.id} value={idea.id}>{idea.current.title} · r{idea.current_revision}</option>)}
            </select>
          </label>
          <label>Title<input value={title} onChange={(event) => setTitle(event.target.value)} /></label>
          <label>Takeaway<textarea value={takeaway} onChange={(event) => setTakeaway(event.target.value)} /></label>
          <label>Synthesis<textarea value={synthesis} onChange={(event) => setSynthesis(event.target.value)} /></label>
          <button disabled={!workspaceId || !sourceRawId || !title.trim() || !takeaway.trim() || !synthesis.trim() || busy} onClick={() => run(async () => {
            await recordBrainstormDiscussion(workspaceId!, sourceRawId);
            await reconcileBrainstorm(workspaceId!, sourceRawId, title, takeaway, synthesis, selectedIdea);
            setTitle("");
            setTakeaway("");
            setSynthesis("");
            setEditingIdeaId("");
          })}>{selectedIdea ? "Append reconciled revision" : "Create reconciled idea"}</button>
        </article>
      </section>

      <section aria-labelledby="brainstorm-raw-heading">
        <h2 id="brainstorm-raw-heading">Immutable RAW</h2>
        {rawRecords.length === 0 ? <p>No RAW captures yet.</p> : rawRecords.map((raw) => (
          <article className="operator-card" data-testid="brainstorm-raw" key={raw.id}>
            <p>{raw.content}</p>
            <p><strong>State:</strong> {raw.lineage_state}</p>
            <p><strong>Identity:</strong> {raw.id}</p>
            <p><strong>Attachments:</strong> {raw.attachment_refs.length === 0 ? "none" : raw.attachment_refs.map((ref) => `${ref.ref_type}:${ref.ref_id}`).join(", ")}</p>
            <button disabled={busy} onClick={() => setSourceRawId(raw.id)}>Use as reconciliation source</button>
          </article>
        ))}
      </section>

      <section aria-labelledby="brainstorm-reconciled-heading">
        <h2 id="brainstorm-reconciled-heading">Reconciled ideas</h2>
        {ideas.length === 0 ? <p>No reconciled ideas yet.</p> : ideas.map((idea) => (
          <article className="operator-card" data-testid="brainstorm-idea" key={idea.id}>
            <h3>{idea.current.title}</h3>
            <p><strong>{idea.lineage_state}</strong> · revision {idea.current_revision}</p>
            <p>{idea.current.takeaway}</p>
            <button disabled={busy} onClick={() => run(async () => setExpanded(await getBrainstormIdea(idea.workspace_id, idea.id)))}>Inspect synthesis and provenance</button>
            {idea.lineage_state !== "SUPERSEDED" ? <>
              <button disabled={busy} onClick={() => setEditingIdeaId(idea.id)}>Revise this idea</button>
              <button disabled={busy} onClick={() => setEditingIdeaId(idea.id)}>Use as lineage source</button>
              <button disabled={busy} onClick={() => setSuccessorId(idea.id)}>Use as successor</button>
            </> : null}
            <div role="group" aria-label={`Promotion proposals for ${idea.current.title}`}>
              <button disabled={busy} onClick={() => run(async () => { await createBrainstormPromotion(idea, "roadmap"); })}>Add to Roadmap proposal</button>
              <button disabled={busy} onClick={() => run(async () => { await createBrainstormPromotion(idea, "design"); })}>Promote Design proposal</button>
              <button disabled={busy} onClick={() => run(async () => { await createBrainstormPromotion(idea, "coding"); })}>Promote Coding proposal</button>
            </div>
          </article>
        ))}
      </section>

      {expanded ? (
        <section className="operator-card" data-testid="brainstorm-detail">
          <h2>{expanded.current.title} · detail</h2>
          <p>{expanded.current.synthesis}</p>
          <h3>Exact provenance</h3>
          <ul>
            {expanded.current.source_refs.map((ref, index) => <li key={`${ref.ref_type}-${ref.ref_id}-${index}`}>{ref.ref_type}:{ref.ref_id}{ref.revision ? `@${ref.revision}` : ""}</li>)}
          </ul>
          <h3>Immutable revisions</h3>
          <ul>{(expanded.revisions ?? []).map((revision) => <li key={revision.revision}>r{revision.revision}: {revision.title}</li>)}</ul>
        </section>
      ) : null}

      <section className="operator-card">
        <h2>Supersede lineage</h2>
        <p>Choose source and successor from the reconciled idea cards.</p>
        <button disabled={!selectedIdea || !selectedSuccessor || selectedIdea.id === selectedSuccessor.id || busy} onClick={() => run(async () => { await supersedeBrainstormIdea(selectedIdea!, selectedSuccessor!); setEditingIdeaId(""); setSuccessorId(""); })}>Supersede with successor</button>
      </section>

      <section aria-labelledby="brainstorm-promotions-heading">
        <h2 id="brainstorm-promotions-heading">Promotion proposals</h2>
        {promotions.length === 0 ? <p>No promotion proposals yet.</p> : promotions.map((promotion) => (
          <article className="operator-card" data-testid="brainstorm-promotion" key={promotion.id}>
            <p><strong>{promotion.target}</strong> proposal · {promotion.state}</p>
            <p>Proposal identity: {promotion.id}</p>
            <p>Source revision: {promotion.idea_id}@{promotion.source_revision}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
