import { useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";

import type { StageSelection } from "../../app/selection";
import {
  ThreadsRequestError,
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
import "./JarvisSidecar.css";

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
  contextEnabled: boolean;
  expectedDigest: string | null;
}>;

function selectionIdentity(selection: StageSelection | null): string {
  if (selection === null) return "none";
  if (selection.kind === "record") {
    return `record:${selection.ref.workspaceId}:${selection.ref.resource}:${selection.ref.recordId}`;
  }
  return `geometry:${selection.viewerSessionId}:${selection.ephemeralObjectId}`;
}

function localSelectionLabel(selection: StageSelection | null): string {
  if (selection === null) return "No local selection";
  if (selection.kind === "record") return `${selection.ref.resource}:${selection.ref.recordId}`;
  return `Geometry hit ${selection.ephemeralObjectId}`;
}

export function useJarvisSidecar(
  workspaceId: string | null,
  routeId: string,
  selection: StageSelection | null,
  contextualContent?: ReactNode
): ReactNode {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ThreadDetail | null>(null);
  const [preview, setPreview] = useState<ContextPackPreview | null>(null);
  const [contextEnabled, setContextEnabled] = useState(true);
  const [previewNonce, setPreviewNonce] = useState(0);
  const [prompt, setPrompt] = useState("");
  const [pending, setPending] = useState<PendingSubmit | null>(null);
  const [loadingThreads, setLoadingThreads] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const workspaceOwner = useRef(0);
  const listOwner = useRef(0);
  const detailOwner = useRef(0);
  const previewOwner = useRef(0);
  const submitOwner = useRef(0);
  const selectionKey = useMemo(() => selectionIdentity(selection), [selection]);

  useEffect(() => {
    workspaceOwner.current += 1;
    listOwner.current += 1;
    detailOwner.current += 1;
    previewOwner.current += 1;
    submitOwner.current += 1;
    const workspaceToken = workspaceOwner.current;
    const listToken = listOwner.current;
    setThreads([]);
    setSelectedThreadId(null);
    setDetail(null);
    setPreview(null);
    setPending(null);
    setPrompt("");
    setLoadingThreads(false);
    setLoadingDetail(false);
    setPreviewLoading(false);
    setSubmitting(false);
    setError(null);
    if (!workspaceId) return;

    setLoadingThreads(true);
    void listThreads(workspaceId)
      .then((nextThreads) => {
        if (workspaceOwner.current !== workspaceToken || listOwner.current !== listToken) return;
        setThreads(nextThreads);
        setSelectedThreadId(nextThreads[0]?.id ?? null);
      })
      .catch(() => {
        if (workspaceOwner.current === workspaceToken && listOwner.current === listToken) {
          setError("Jarvis threads could not be loaded.");
        }
      })
      .finally(() => {
        if (workspaceOwner.current === workspaceToken && listOwner.current === listToken) {
          setLoadingThreads(false);
        }
      });
  }, [workspaceId]);

  useEffect(() => {
    const token = ++detailOwner.current;
    const workspaceToken = workspaceOwner.current;
    setDetail(null);
    setLoadingDetail(false);
    if (!workspaceId || !selectedThreadId) return;
    setLoadingDetail(true);
    void getThread(workspaceId, selectedThreadId)
      .then((next) => {
        if (detailOwner.current !== token || workspaceOwner.current !== workspaceToken) return;
        setDetail(next);
      })
      .catch(() => {
        if (detailOwner.current === token && workspaceOwner.current === workspaceToken) {
          setError("Selected Jarvis thread could not be loaded.");
        }
      })
      .finally(() => {
        if (detailOwner.current === token && workspaceOwner.current === workspaceToken) {
          setLoadingDetail(false);
        }
      });
  }, [workspaceId, selectedThreadId]);

  useEffect(() => {
    const token = ++previewOwner.current;
    const workspaceToken = workspaceOwner.current;
    setPreview(null);
    setPreviewLoading(false);
    if (!workspaceId || !contextEnabled) return;
    setPreviewLoading(true);
    void previewThreadContext(workspaceId, DEFAULT_SELECTION)
      .then((nextPreview) => {
        if (previewOwner.current !== token || workspaceOwner.current !== workspaceToken) return;
        setPreview(nextPreview);
      })
      .catch(() => {
        if (previewOwner.current === token && workspaceOwner.current === workspaceToken) {
          setError("Project context preview could not be loaded.");
        }
      })
      .finally(() => {
        if (previewOwner.current === token && workspaceOwner.current === workspaceToken) {
          setPreviewLoading(false);
        }
      });
  }, [workspaceId, contextEnabled, routeId, selectionKey, previewNonce]);

  useEffect(() => {
    submitOwner.current += 1;
    setSubmitting(false);
  }, [routeId, selectionKey]);

  const selectThread = (threadId: string | null) => {
    if (threadId === selectedThreadId) return;
    detailOwner.current += 1;
    submitOwner.current += 1;
    setSelectedThreadId(threadId);
    setDetail(null);
    setPending(null);
    setSubmitting(false);
    setError(null);
  };

  const create = async () => {
    if (!workspaceId || loadingThreads) return;
    const workspaceToken = workspaceOwner.current;
    setError(null);
    setLoadingThreads(true);
    try {
      const next = await createThread(workspaceId, "Jarvis advisory");
      if (workspaceOwner.current !== workspaceToken || next.workspace_id !== workspaceId) return;
      setThreads((current) => [next, ...current.filter((item) => item.id !== next.id)]);
      detailOwner.current += 1;
      submitOwner.current += 1;
      setSelectedThreadId(next.id);
      setDetail(null);
      setPending(null);
      setSubmitting(false);
    } catch {
      if (workspaceOwner.current === workspaceToken) setError("Thread creation failed.");
    } finally {
      if (workspaceOwner.current === workspaceToken) setLoadingThreads(false);
    }
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const text = prompt.trim();
    if (!workspaceId || !selectedThreadId || !text || submitting) return;

    const reusable = pending
      && pending.workspaceId === workspaceId
      && pending.threadId === selectedThreadId
      && pending.prompt === text
      && pending.contextEnabled === contextEnabled;
    const currentDigest = contextEnabled
      ? reusable
        ? pending.expectedDigest
        : preview?.context_digest ?? null
      : null;
    if (contextEnabled && !currentDigest) {
      setError("Project context is empty or stale. Refresh it or turn project context off.");
      return;
    }

    const captured: PendingSubmit = reusable
      ? pending
      : {
          workspaceId,
          threadId: selectedThreadId,
          requestId: requestId(),
          prompt: text,
          contextEnabled,
          expectedDigest: currentDigest
        };
    const token = ++submitOwner.current;
    const workspaceToken = workspaceOwner.current;
    setPending(captured);
    setSubmitting(true);
    setError(null);
    try {
      await submitThreadInteraction(
        captured.workspaceId,
        captured.threadId,
        captured.requestId,
        captured.prompt,
        captured.contextEnabled && captured.expectedDigest
          ? { selection: DEFAULT_SELECTION, expectedDigest: captured.expectedDigest }
          : undefined
      );
      if (submitOwner.current !== token || workspaceOwner.current !== workspaceToken) return;
      const refreshed = await getThread(captured.workspaceId, captured.threadId);
      if (submitOwner.current !== token || workspaceOwner.current !== workspaceToken) return;
      setDetail(refreshed);
      setPending(null);
      setPrompt("");
      if (captured.contextEnabled) setPreviewNonce((current) => current + 1);
    } catch (caught) {
      if (submitOwner.current !== token || workspaceOwner.current !== workspaceToken) return;
      if (caught instanceof ThreadsRequestError && caught.status === 409 && captured.contextEnabled) {
        setPending(null);
        setError("Project context changed before dispatch. Refresh the preview, inspect the new digest, then submit again.");
        setPreviewNonce((current) => current + 1);
      } else {
        setError("Submit failed or its durable result is uncertain. Retrying unchanged text reuses the same request id.");
      }
    } finally {
      if (submitOwner.current === token && workspaceOwner.current === workspaceToken) setSubmitting(false);
    }
  };

  const pendingRetryReady = Boolean(
    pending
      && pending.workspaceId === workspaceId
      && pending.threadId === selectedThreadId
      && pending.prompt === prompt.trim()
      && pending.contextEnabled === contextEnabled
      && (!contextEnabled || pending.expectedDigest)
  );
  const contextReady = !contextEnabled || pendingRetryReady || Boolean(preview?.context_digest);

  return <div className="jarvis-sidecar" data-testid="jarvis-sidecar">
    <header className="jarvis-sidecar__header">
      <div><p className="eyebrow">Jarvis advisory</p><strong>Contextual engineering assistant</strong></div>
      <button type="button" onClick={() => void create()} disabled={!workspaceId || loadingThreads}>New thread</button>
    </header>

    <section className="jarvis-sidecar__local-context" aria-label="Local application context">
      <strong>Local context</strong>
      <span>Route: {routeId}</span>
      <span>{localSelectionLabel(selection)}</span>
      <small>This descriptor stays local. Provider context is only the inspected project pack below.</small>
    </section>
    {contextualContent ? <section className="jarvis-sidecar__stage-context" aria-label="Current stage context">{contextualContent}</section> : null}

    {!workspaceId ? <p>Select a workspace to use Jarvis.</p> : null}
    {workspaceId ? <label className="jarvis-sidecar__field">Thread<select value={selectedThreadId ?? ""} onChange={(event) => selectThread(event.target.value || null)} disabled={loadingThreads}><option value="">Select thread</option>{threads.map((thread) => <option key={thread.id} value={thread.id}>{thread.title || "Untitled thread"}</option>)}</select></label> : null}
    {loadingDetail ? <p className="jarvis-sidecar__status">Loading thread…</p> : null}

    <section className="jarvis-sidecar__context" aria-label="Project context controls">
      <label className="jarvis-sidecar__toggle"><input type="checkbox" checked={contextEnabled} disabled={submitting} onChange={(event) => { setContextEnabled(event.target.checked); setError(null); }} />Use inspected project context</label>
      {contextEnabled && previewLoading ? <p className="jarvis-sidecar__status">Building context preview…</p> : null}
      {contextEnabled && preview ? <details><summary>Context pack · {preview.included_count} records · ~{preview.estimated_token_count} tokens</summary><p>Digest <code>{preview.context_digest ?? "empty"}</code></p><p>{preview.char_count} characters · {preview.dropped_count} dropped</p><ul>{preview.context_sources_manifest.map((source) => <li key={`${source.type}:${source.id}:${source.source}`}>{source.type ?? "record"}: {source.id ?? source.source}</li>)}</ul></details> : null}
      {contextEnabled ? <button type="button" onClick={() => setPreviewNonce((current) => current + 1)} disabled={!workspaceId || previewLoading || submitting}>Refresh context preview</button> : <p className="jarvis-sidecar__status">Project context is off. Only the current message is submitted.</p>}
      {pendingRetryReady && contextEnabled ? <p className="jarvis-sidecar__status">An uncertain prior submit retains its inspected digest for a safe idempotent retry.</p> : null}
    </section>

    {detail ? <ol className="jarvis-sidecar__transcript" aria-label="Jarvis thread transcript">{detail.interactions.map((interaction) => <li key={interaction.id}><p><strong>You</strong> {interaction.user_text}</p><p><strong>Jarvis advisory</strong> {interaction.assistant_text ?? "No durable assistant snapshot."}</p><dl><div><dt>Flow</dt><dd>{interaction.flow_id}</dd></div><div><dt>Canonical state</dt><dd>{interaction.flow_state}</dd></div><div><dt>Persistence</dt><dd>{interaction.persistence_state}</dd></div><div><dt>Attempts</dt><dd>{interaction.attempt_count}</dd></div><div><dt>Proposals</dt><dd>{interaction.proposal_count}{interaction.proposals_truncated ? "+" : ""}</dd></div></dl>{interaction.terminal_reason ? <small>Terminal reason: {interaction.terminal_reason}</small> : null}{interaction.persistence_error ? <small>Persistence diagnostic: {interaction.persistence_error}</small> : null}{interaction.proposal_ids.length ? <small>Proposal refs: {interaction.proposal_ids.join(", ")}</small> : null}</li>)}</ol> : null}
    {error ? <p className="jarvis-sidecar__status" role="status">{error}</p> : null}

    <form onSubmit={(event) => void submit(event)} className="jarvis-sidecar__composer">
      <label htmlFor="jarvis-prompt">Message</label>
      <textarea id="jarvis-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} maxLength={12000} rows={5} disabled={!selectedThreadId || submitting} />
      <button type="submit" disabled={!selectedThreadId || !prompt.trim() || submitting || !contextReady}>{submitting ? "Submitting…" : contextEnabled ? pendingRetryReady ? "Retry with original context" : "Send with inspected context" : "Send without project context"}</button>
      <small>Enter submits. Shift+Enter adds a line. Closing the sidecar does not cancel canonical execution.</small>
    </form>
  </div>;
}
