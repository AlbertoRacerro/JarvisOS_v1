import { useEffect, useRef, useState } from "react";

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
  const [projectionWorkspaceId, setProjectionWorkspaceId] = useState<string | null>(null);
  const activeWorkspaceRef = useRef<string | null>(workspaceId);
  const retryKeysRef = useRef(new Map<string, string>());

  function retryIdentity(operation: string, payload: object): { fingerprint: string; key: string } {
    const fingerprint = `${operation}:${JSON.stringify(payload)}`;
    const existing = retryKeysRef.current.get(fingerprint);
    if (existing) return { fingerprint, key: existing };
    const key = `${operation}-${crypto.randomUUID()}`;
    retryKeysRef.current.set(fingerprint, key);
    return { fingerprint, key };
  }

  function clearRetryIdentity(fingerprint: string) {
    retryKeysRef.current.delete(fingerprint);
  }

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

  useEffect(() => {
    activeWorkspaceRef.current = workspaceId;
    retryKeysRef.current.clear();
    setProjectionWorkspaceId(null);
    setRawRecords([]);
    setIdeas([]);
    setPromotions([]);
    setExpanded(null);
    setSourceRawId("");
    setEditingIdeaId("");
    setSuccessorId("");
    setBusy(false);
    setError(null);
  }, [workspaceId]);

  async function refresh(selectedWorkspaceId: string) {
    const expandedId = expanded?.id ?? null;
    const [nextRaw, nextIdeas, nextPromotions] = await Promise.all([
      listBrainstormRaw(selectedWorkspaceId),
      listBrainstormIdeas(selectedWorkspaceId),
      listBrainstormPromotions(selectedWorkspaceId)
    ]);
    if (activeWorkspaceRef.current !== selectedWorkspaceId) return;
    setRawRecords(nextRaw);
    setIdeas(nextIdeas);
    setPromotions(nextPromotions);
    setProjectionWorkspaceId(selectedWorkspaceId);
    if (expandedId) {
      const fresh = nextIdeas.find((idea) => idea.id === expandedId);
      if (!fresh) setExpanded(null);
      else {
        const detail = await getBrainstormIdea(selectedWorkspaceId, fresh.id);
        if (activeWorkspaceRef.current === selectedWorkspaceId) setExpanded(detail);
      }
    }
  }

  useEffect(() => {
    if (!workspaceId) return;
    let alive = true;
    const selectedWorkspaceId = workspaceId;
    Promise.all([
      listBrainstormRaw(selectedWorkspaceId),
      listBrainstormIdeas(selectedWorkspaceId),
      listBrainstormPromotions(selectedWorkspaceId)
    ]).then(([nextRaw, nextIdeas, nextPromotions]) => {
      if (!alive || activeWorkspaceRef.current !== selectedWorkspaceId) return;
      setRawRecords(nextRaw);
      setIdeas(nextIdeas);
      setPromotions(nextPromotions);
      setProjectionWorkspaceId(selectedWorkspaceId);
      if (nextRaw[0]) setSourceRawId(nextRaw[0].id);
    }).catch((exc: unknown) => {
      if (alive && activeWorkspaceRef.current === selectedWorkspaceId) {
        setProjectionWorkspaceId(null);
        setError(exc instanceof Error ? exc.message : "Brainstorm data failed to load.");
      }
    });
    return () => { alive = false; };
  }, [workspaceId]);

  async function run(action: () => Promise<void>) {
    if (!workspaceId || busy) return;
    const selectedWorkspaceId = workspaceId;
    setBusy(true);
    setError(null);
    try {
      await action();
      if (activeWorkspaceRef.current === selectedWorkspaceId) await refresh(selectedWorkspaceId);
    } catch (exc) {
      if (activeWorkspaceRef.current === selectedWorkspaceId) {
        setError(exc instanceof Error ? exc.message : "Brainstorm mutation failed.");
        try {
          await refresh(selectedWorkspaceId);
        } catch {
          setProjectionWorkspaceId(null);
          // Preserve the server rejection without presenting a stale projection as canonical.
        }
      }
    } finally {
      if (activeWorkspaceRef.current === selectedWorkspaceId) setBusy(false);
    }
  }

  const projectionCurrent = projectionWorkspaceId !== null && projectionWorkspaceId === workspaceId;
  const visibleRawRecords = projectionCurrent ? rawRecords : [];
  const visibleIdeas = projectionCurrent ? ideas : [];
  const visiblePromotions = projectionCurrent ? promotions : [];
  const selectedIdea = visibleIdeas.find((idea) => idea.id === editingIdeaId);
  const selectedSuccessor = visibleIdeas.find((idea) => idea.id === successorId);

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
            const identity = retryIdentity("raw", { workspaceId, content: rawText, refs });
            const created = await createBrainstormRaw(workspaceId!, rawText, identity.key, refs);
            clearRetryIdentity(identity.fingerprint);
            setSourceRawId(created.id);
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
              {visibleRawRecords.map((raw) => <option key={raw.id} value={raw.id}>{raw.content.slice(0, 80)}</option>)}
            </select>
          </label>
          <label>
            Existing idea revision
            <select value={editingIdeaId} onChange={(event) => setEditingIdeaId(event.target.value)}>
              <option value="">Create new reconciled idea</option>
              {visibleIdeas.filter((idea) => idea.lineage_state !== "SUPERSEDED").map((idea) => <option key={idea.id} value={idea.id}>{idea.current.title} · r{idea.current_revision}</option>)}
            </select>
          </label>
          <label>Title<input value={title} onChange={(event) => setTitle(event.target.value)} /></label>
          <label>Takeaway<textarea value={takeaway} onChange={(event) => setTakeaway(event.target.value)} /></label>
          <label>Synthesis<textarea value={synthesis} onChange={(event) => setSynthesis(event.target.value)} /></label>
          <button disabled={!projectionCurrent || !workspaceId || !sourceRawId || busy} onClick={() => run(async () => {
            const identity = retryIdentity("discussion", { workspaceId, sourceRawId });
            await recordBrainstormDiscussion(workspaceId!, sourceRawId, identity.key);
            clearRetryIdentity(identity.fingerprint);
          })}>Record discussion</button>
          <button disabled={!projectionCurrent || !workspaceId || !sourceRawId || !title.trim() || !takeaway.trim() || !synthesis.trim() || busy} onClick={() => run(async () => {
            const identity = retryIdentity("reconcile", {
              workspaceId,
              sourceRawId,
              title,
              takeaway,
              synthesis,
              ideaId: selectedIdea?.id ?? null,
              revision: selectedIdea?.current_revision ?? null
            });
            await reconcileBrainstorm(workspaceId!, sourceRawId, title, takeaway, synthesis, identity.key, selectedIdea);
            clearRetryIdentity(identity.fingerprint);
            setTitle("");
            setTakeaway("");
            setSynthesis("");
            setEditingIdeaId("");
          })}>{selectedIdea ? "Append reconciled revision" : "Create reconciled idea"}</button>
        </article>
      </section>

      <section aria-labelledby="brainstorm-raw-heading">
        <h2 id="brainstorm-raw-heading">Immutable RAW</h2>
        {visibleRawRecords.length === 0 ? <p>No RAW captures yet.</p> : visibleRawRecords.map((raw) => (
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
        {visibleIdeas.length === 0 ? <p>No reconciled ideas yet.</p> : visibleIdeas.map((idea) => (
          <article className="operator-card" data-testid="brainstorm-idea" key={idea.id}>
            <h3>{idea.current.title}</h3>
            <p><strong>{idea.lineage_state}</strong> · revision {idea.current_revision}</p>
            <p>{idea.current.takeaway}</p>
            <button disabled={busy} onClick={async () => {
              const selectedWorkspaceId = idea.workspace_id;
              setBusy(true);
              setError(null);
              try {
                const detail = await getBrainstormIdea(selectedWorkspaceId, idea.id);
                if (activeWorkspaceRef.current === selectedWorkspaceId) setExpanded(detail);
              } catch (exc) {
                if (activeWorkspaceRef.current === selectedWorkspaceId) setError(exc instanceof Error ? exc.message : "Brainstorm detail failed to load.");
              } finally {
                if (activeWorkspaceRef.current === selectedWorkspaceId) setBusy(false);
              }
            }}>Inspect synthesis and provenance</button>
            {idea.lineage_state !== "SUPERSEDED" ? <>
              <button disabled={busy} onClick={() => setEditingIdeaId(idea.id)}>Revise this idea</button>
              <button disabled={busy} onClick={() => setEditingIdeaId(idea.id)}>Use as lineage source</button>
              <button disabled={busy} onClick={() => setSuccessorId(idea.id)}>Use as successor</button>
            </> : null}
            <div role="group" aria-label={`Promotion proposals for ${idea.current.title}`}>
              {(["roadmap", "design", "coding"] as const).map((target) => (
                <button key={target} disabled={busy} onClick={() => run(async () => {
                  const identity = retryIdentity(`promotion-${target}`, {
                    workspaceId: idea.workspace_id,
                    ideaId: idea.id,
                    revision: idea.current_revision,
                    target
                  });
                  await createBrainstormPromotion(idea, target, identity.key);
                  clearRetryIdentity(identity.fingerprint);
                })}>{target === "roadmap" ? "Add to Roadmap proposal" : `Promote ${target[0].toUpperCase()}${target.slice(1)} proposal`}</button>
              ))}
            </div>
          </article>
        ))}
      </section>

      {projectionCurrent && expanded ? (
        <section className="operator-card" data-testid="brainstorm-detail">
          <h2>{expanded.current.title} · detail</h2>
          <p>{expanded.current.synthesis}</p>
          <h3>Exact provenance</h3>
          <ul>
            {expanded.current.source_refs.map((ref, index) => <li key={`${ref.ref_type}-${ref.ref_id}-${index}`}>{ref.ref_type}:{ref.ref_id}{ref.revision ? `@${ref.revision}` : ""}</li>)}
          </ul>
          <h3>Discussion provenance</h3>
          {(expanded.discussions ?? []).length === 0 ? <p>No recorded discussions.</p> : (
            <ul>{(expanded.discussions ?? []).map((discussion) => (
              <li key={`${discussion.id}-${discussion.bound_revision}`}>
                {discussion.id} · bound to r{discussion.bound_revision} · {discussion.created_by} · {discussion.created_at} · {discussion.source_refs.map((ref) => `${ref.ref_type}:${ref.ref_id}${ref.revision ? `@${ref.revision}` : ""}`).join(", ")}
              </li>
            ))}</ul>
          )}
          <h3>Immutable revisions</h3>
          <ul>{(expanded.revisions ?? []).map((revision) => <li key={revision.revision}>r{revision.revision}: {revision.title}</li>)}</ul>
        </section>
      ) : null}

      <section className="operator-card">
        <h2>Supersede lineage</h2>
        <p>Choose source and successor from the reconciled idea cards.</p>
        <button disabled={!projectionCurrent || !selectedIdea || !selectedSuccessor || selectedIdea.id === selectedSuccessor.id || busy} onClick={() => run(async () => {
          const identity = retryIdentity("supersede", {
            workspaceId: selectedIdea!.workspace_id,
            sourceId: selectedIdea!.id,
            sourceRevision: selectedIdea!.current_revision,
            successorId: selectedSuccessor!.id,
            successorRevision: selectedSuccessor!.current_revision
          });
          await supersedeBrainstormIdea(selectedIdea!, selectedSuccessor!, identity.key);
          clearRetryIdentity(identity.fingerprint);
          setEditingIdeaId("");
          setSuccessorId("");
        })}>Supersede with successor</button>
      </section>

      <section aria-labelledby="brainstorm-promotions-heading">
        <h2 id="brainstorm-promotions-heading">Promotion proposals</h2>
        {visiblePromotions.length === 0 ? <p>No promotion proposals yet.</p> : visiblePromotions.map((promotion) => (
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
