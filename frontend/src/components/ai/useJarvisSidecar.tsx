import { useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";

import {
  createThread,
  getThread,
  listThreads,
  previewThreadContext,
  submitThreadInteraction,
  type ContextPackPreview,
  type ContextSelection,
  type ThreadDetail,
  type ThreadSummary
} from "../../api/threads";

const DEFAULT_SELECTION: ContextSelection = {};

function requestId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `jarvis-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

type PendingSubmit = Readonly<{
  workspaceId: string;
  threadId: string;
  requestId: string;
  prompt: string;
  selection: ContextSelection;
  expectedDigest: string;
}>;

export function useJarvisSidecar(workspaceId: string | null): ReactNode {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ThreadDetail | null>(null);
  const [preview, setPreview] = useState<ContextPackPreview | null>(null);
  const [prompt, setPrompt] = useState("");
  const [pending, setPending] = useState<PendingSubmit | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ownership = useRef(0);

  useEffect(() => {
    ownership.current += 1;
    const token = ownership.current;
    setThreads([]);
    setSelectedThreadId(null);
    setDetail(null);
    setPreview(null);
    setError(null);
    if (!workspaceId) return;
    void Promise.all([listThreads(workspaceId), previewThreadContext(workspaceId, DEFAULT_SELECTION)])
      .then(([nextThreads, nextPreview]) => {
        if (ownership.current !== token) return;
        setThreads(nextThreads);
        setSelectedThreadId(nextThreads[0]?.id ?? null);
        setPreview(nextPreview);
      })
      .catch(() => { if (ownership.current === token) setError("Jarvis context could not be loaded."); });
  }, [workspaceId]);

  useEffect(() => {
    const token = ownership.current;
    if (!workspaceId || !selectedThreadId) { setDetail(null); return; }
    void getThread(workspaceId, selectedThreadId)
      .then((next) => { if (ownership.current === token) setDetail(next); })
      .catch(() => { if (ownership.current === token) setError("Thread could not be loaded."); });
  }, [workspaceId, selectedThreadId]);

  const create = async () => {
    if (!workspaceId) return;
    setError(null);
    try {
      const next = await createThread(workspaceId, "Jarvis advisory");
      if (workspaceId !== next.workspace_id) return;
      setThreads((current) => [next, ...current.filter((item) => item.id !== next.id)]);
      setSelectedThreadId(next.id);
    } catch {
      setError("Thread creation failed.");
    }
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!workspaceId || !selectedThreadId || !prompt.trim() || !preview?.context_digest) return;
    const captured: PendingSubmit = pending && pending.workspaceId === workspaceId && pending.threadId === selectedThreadId && pending.prompt === prompt
      ? pending
      : {
          workspaceId,
          threadId: selectedThreadId,
          requestId: requestId(),
          prompt,
          selection: DEFAULT_SELECTION,
          expectedDigest: preview.context_digest
        };
    setPending(captured);
    setError(null);
    try {
      await submitThreadInteraction(
        captured.workspaceId,
        captured.threadId,
        captured.requestId,
        captured.prompt,
        { selection: captured.selection, expectedDigest: captured.expectedDigest }
      );
      if (workspaceId !== captured.workspaceId || selectedThreadId !== captured.threadId) return;
      setPending(null);
      setPrompt("");
      setDetail(await getThread(captured.workspaceId, captured.threadId));
      setPreview(await previewThreadContext(captured.workspaceId, DEFAULT_SELECTION));
    } catch {
      if (workspaceId === captured.workspaceId && selectedThreadId === captured.threadId) {
        setError("Submit failed. Retry preserves the same request id; no automatic redispatch occurs.");
      }
    }
  };

  return useMemo(() => (
    <div className="jarvis-sidecar" data-testid="jarvis-sidecar">
      <header className="jarvis-sidecar__header">
        <div><p className="eyebrow">Jarvis advisory</p><strong>Contextual engineering assistant</strong></div>
        <button type="button" onClick={() => void create()} disabled={!workspaceId}>New thread</button>
      </header>
      {!workspaceId ? <p>Select a workspace to use Jarvis.</p> : null}
      {workspaceId ? <label>Thread<select value={selectedThreadId ?? ""} onChange={(event) => { setSelectedThreadId(event.target.value || null); setError(null); }}><option value="">Select thread</option>{threads.map((thread) => <option key={thread.id} value={thread.id}>{thread.title || "Untitled thread"}</option>)}</select></label> : null}
      {preview ? <details className="jarvis-sidecar__context"><summary>Context pack · {preview.included_count} records · ~{preview.estimated_token_count} tokens</summary><p>Digest <code>{preview.context_digest ?? "empty"}</code></p><ul>{preview.context_sources_manifest.map((source) => <li key={`${source.type}:${source.id}`}>{source.type ?? "record"}: {source.id ?? source.source}</li>)}</ul></details> : null}
      {detail ? <ol className="jarvis-sidecar__transcript" aria-label="Jarvis thread transcript">{detail.interactions.map((interaction) => <li key={interaction.id}><p><strong>You</strong> {interaction.user_text}</p><p><strong>Jarvis</strong> {interaction.assistant_text ?? `Execution ${interaction.flow_state}`}</p><small>Flow {interaction.flow_id} · {interaction.persistence_state}</small></li>)}</ol> : null}
      {error ? <p role="alert">{error}</p> : null}
      <form onSubmit={(event) => void submit(event)} className="jarvis-sidecar__composer">
        <label htmlFor="jarvis-prompt">Message</label>
        <textarea id="jarvis-prompt" value={prompt} onChange={(event) => { setPrompt(event.target.value); if (pending && event.target.value !== pending.prompt) setPending(null); }} maxLength={12000} rows={5} disabled={!selectedThreadId} />
        <button type="submit" disabled={!selectedThreadId || !prompt.trim() || !preview?.context_digest}>Send with inspected context</button>
      </form>
    </div>
  ), [detail, error, pending, preview, prompt, selectedThreadId, threads, workspaceId]);
}
