import { useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";

import type { KnowledgeContextPreview } from "../../api/knowledgeActions";
import type { StageSelection } from "../../app/selection";
import {
  ThreadsRequestError,
  getConversationOptions,
  type ConversationRoute,
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
const KNOWLEDGE_ROUTES = new Set(["memory-project-basis", "memory-models", "memory-literature"]);

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
  routeClass: string;
  knowledgeContext: KnowledgeContextPreview | null;
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
  contextualContent?: ReactNode,
  knowledgeContext?: KnowledgeContextPreview | null
): ReactNode {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ThreadDetail | null>(null);
  const [preview, setPreview] = useState<ContextPackPreview | null>(null);
  const [projectPackEnabled, setContextEnabled] = useState(false);
  const [routes, setRoutes] = useState<ConversationRoute[]>([]);
  const [routeClass, setRouteClass] = useState("");
  const [routeError, setRouteError] = useState<string | null>(null);
  const activeKnowledge = knowledgeContext?.workspace_id === workspaceId && knowledgeContext.route_id === routeId ? knowledgeContext : null;
  const contextEnabled = projectPackEnabled && !activeKnowledge;
  const activeRoute = routes.find(route => route.route_class === routeClass);
  const activeRouteAvailable = activeRoute?.execution_class === "synthetic"
    || Boolean(activeRoute?.availability.runtime_reachable && activeRoute.availability.model_installed);

  useEffect(() => {
    let alive = true;
    const refresh = () => void getConversationOptions().then(result => {
      if (!alive) return;
      setRoutes(result.routes);
      setRouteClass(current => result.routes.some(route => route.route_class === current)
        ? current : result.routes.find(route => route.availability.runtime_reachable && route.availability.model_installed)?.route_class ?? result.routes[0]?.route_class ?? "");
      setRouteError(result.routes.length ? null : "No local conversation route is configured.");
    }).catch(() => { if (alive) setRouteError("Conversation availability could not be loaded."); });
    refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => { alive = false; window.clearInterval(timer); };
  }, []);
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
    // Wait for thread ownership to settle before auto-creating or dispatching.
    // Otherwise a delayed initial list (or explicit creation) can select a
    // different thread while this submit publishes its transcript.
    if (!workspaceId || !text || loadingThreads || submitting || !activeRoute || !activeRouteAvailable || activeKnowledge?.route_id === "memory-project-basis") return;
    const workspaceTokenForCreate = workspaceOwner.current;
    const creationToken = ++submitOwner.current;
    let threadId = selectedThreadId;
    if (!threadId) {
      setSubmitting(true);
      try {
        const created = await createThread(workspaceId, text.slice(0, 70));
        if (workspaceOwner.current !== workspaceTokenForCreate || submitOwner.current !== creationToken) return;
        threadId = created.id;
        setThreads((current) => [created, ...current]);
        setSelectedThreadId(created.id);
      } catch {
        if (workspaceOwner.current !== workspaceTokenForCreate || submitOwner.current !== creationToken) return;
        setError("Could not start a conversation. Your message is preserved; try again.");
        setSubmitting(false);
        return;
      }
    }

    const reusable = pending
      && pending.workspaceId === workspaceId
      && pending.threadId === threadId
      && pending.prompt === text
      && pending.contextEnabled === contextEnabled
      && pending.routeClass === routeClass
      && pending.knowledgeContext?.context_digest === activeKnowledge?.context_digest;
    const currentDigest = contextEnabled
      ? reusable
        ? pending.expectedDigest
        : preview?.context_digest ?? null
      : null;
    if (contextEnabled && !currentDigest) {
      setSubmitting(false);
      setError("Project context is empty or stale. Refresh it or turn project context off.");
      return;
    }

    const captured: PendingSubmit = reusable
      ? pending
      : {
          workspaceId,
          threadId,
          requestId: requestId(),
          prompt: text,
          contextEnabled,
          expectedDigest: currentDigest,
          routeClass,
          knowledgeContext: activeKnowledge
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
          : undefined,
        { routeClass: captured.routeClass, knowledgeContext: captured.knowledgeContext }
      );
      if (submitOwner.current !== token || workspaceOwner.current !== workspaceToken) return;
      detailOwner.current += 1;
      const refreshed = await getThread(captured.workspaceId, captured.threadId);
      if (submitOwner.current !== token || workspaceOwner.current !== workspaceToken) return;
      setDetail(refreshed);
      setPending(null);
      setPrompt("");
      if (captured.contextEnabled) setPreviewNonce((current) => current + 1);
    } catch (caught) {
      if (submitOwner.current !== token || workspaceOwner.current !== workspaceToken) return;
      if (caught instanceof ThreadsRequestError && caught.status === 409 && (captured.contextEnabled || captured.knowledgeContext)) {
        setPending(null);
        setError("The selected context changed. Remove it and add it again before retrying your message.");
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
      && pending.routeClass === routeClass
      && pending.knowledgeContext?.context_digest === activeKnowledge?.context_digest
      && (!contextEnabled || pending.expectedDigest)
  );
  const basisDiscussionBlocked = activeKnowledge?.route_id === "memory-project-basis";
  const contextReady = !basisDiscussionBlocked && (!contextEnabled || pendingRetryReady || Boolean(preview?.context_digest));
  const stageContextClassName = KNOWLEDGE_ROUTES.has(routeId)
    ? "jarvis-sidecar__stage-context jarvis-sidecar__stage-context--visible"
    : "jarvis-sidecar__stage-context";

  return <div className="jarvis-sidecar" data-testid="jarvis-sidecar">
    <header className="jarvis-sidecar__header">
      <div><p className="eyebrow">Jarvis advisory</p><strong>Jarvis</strong></div>
      <button type="button" onClick={() => void create()} disabled={!workspaceId || loadingThreads}>New thread</button>
    </header>

    <details className="jarvis-sidecar__local-context"><summary>Technical details</summary>
      <strong>Local context</strong>
      <span>Route: {routeId}</span>
      <span>{localSelectionLabel(selection)}</span>
      <small>This descriptor stays local. Only explicitly included project context is sent.</small>
    </details>
    {contextualContent ? <section className={`jarvis-selection-actions ${stageContextClassName}`} aria-label="Current stage context">{contextualContent}</section> : null}

    {!workspaceId ? <p>Select a workspace to use Jarvis.</p> : null}
    <details className="jarvis-conversation-settings"><summary>{activeRoute?.label ?? "Conversation setup"} · conversations & model</summary>
    {workspaceId ? <label className="jarvis-sidecar__field">Conversation<select value={selectedThreadId ?? ""} onChange={(event) => selectThread(event.target.value || null)} disabled={loadingThreads}><option value="">Select thread</option>{threads.map((thread) => <option key={thread.id} value={thread.id}>{thread.title || "Untitled thread"}</option>)}</select></label> : null}
    <label className="jarvis-sidecar__field">Responder<select aria-label="Jarvis responder" value={routeClass} disabled={submitting || !routes.length} onChange={event => { setRouteClass(event.target.value); setPending(null); setError(null); }}>
      {!routes.length && <option value="">Unavailable</option>}
      {routes.map(route => {
        const unavailable = route.execution_class !== "synthetic" && (!route.availability.runtime_reachable || !route.availability.model_installed);
        return <option value={route.route_class} key={route.route_class} disabled={unavailable}>{route.label}{unavailable ? ` — ${route.availability.message}` : ""}</option>;
      })}
    </select></label>
    {activeRoute && <p className="jarvis-sidecar__status" role="status">{activeRoute.availability.message}{activeRoute.availability.qualified === "unknown" && activeRoute.execution_class !== "synthetic" ? " Qualification has not been recorded." : ""}</p>}
    </details>
    {routeError && <p role="status">{routeError}</p>}
    {activeRoute && <small>{activeRoute.execution_class === "synthetic" ? "Test responder only — synthetic output, not an AI answer." : `Uses local model ${activeRoute.model_id}.`}</small>}
    {loadingDetail ? <p className="jarvis-sidecar__status">Loading thread…</p> : null}

    <details className="jarvis-sidecar__context" aria-label="Project context controls"><summary>{activeKnowledge ? `${activeKnowledge.included_count} selected records` : contextEnabled ? "Project context included" : "Optional project context"}</summary>
      <label className="jarvis-sidecar__toggle"><input type="checkbox" checked={contextEnabled} disabled={submitting || Boolean(activeKnowledge)} onChange={(event) => { setContextEnabled(event.target.checked); setError(null); }} />Use inspected project context</label>
      {contextEnabled && previewLoading ? <p className="jarvis-sidecar__status">Building context preview…</p> : null}
      {contextEnabled && preview ? <details><summary>Context pack · {preview.included_count} records · ~{preview.estimated_token_count} tokens</summary><p>Digest <code>{preview.context_digest ?? "empty"}</code></p><p>{preview.char_count} characters · {preview.dropped_count} dropped</p><ul>{preview.context_sources_manifest.map((source) => <li key={`${source.type}:${source.id}:${source.source}`}>{source.type ?? "record"}: {source.id ?? source.source}</li>)}</ul></details> : null}
      {contextEnabled ? <button type="button" onClick={() => setPreviewNonce((current) => current + 1)} disabled={!workspaceId || previewLoading || submitting}>Refresh context preview</button> : <p className="jarvis-sidecar__status">{activeKnowledge ? `${activeKnowledge.included_count} exact selected records will be sent with your message.` : "Project context is off. Only the current message is submitted."}</p>}
      {pendingRetryReady && contextEnabled ? <p className="jarvis-sidecar__status">An uncertain prior submit retains its inspected digest for a safe idempotent retry.</p> : null}
    </details>

    {detail ? <ol className="jarvis-sidecar__transcript" aria-label="Jarvis thread transcript">{detail.interactions.map((interaction) => <li key={interaction.id}><p><strong>You</strong> {interaction.user_text}</p><p><strong>{interaction.execution_class === "synthetic" ? "Test responder" : "Jarvis"}</strong> {interaction.assistant_text ?? "No answer was produced. See the saved outcome below."}</p><details><summary>Interaction details</summary><dl><div><dt>Model</dt><dd>{interaction.model_id ?? "Unknown"}</dd></div><div><dt>Flow</dt><dd>{interaction.flow_id}</dd></div><div><dt>Canonical state</dt><dd>{interaction.flow_state}</dd></div><div><dt>Persistence</dt><dd>{interaction.persistence_state}</dd></div><div><dt>Attempts</dt><dd>{interaction.attempt_count}</dd></div><div><dt>Proposals</dt><dd>{interaction.proposal_count}{interaction.proposals_truncated ? "+" : ""}</dd></div></dl></details>{interaction.flow_state === "partial_terminal" ? <p role="status">This answer is incomplete: {interaction.terminal_reason === "output_length_limit" ? "it stopped at the output limit" : (interaction.terminal_reason?.replace(/_/g, " ") ?? "the answer ended early")}. You can request a continuation as a new message.</p> : null}{interaction.flow_state === "failed_terminal" ? <p role="status">The responder could not answer. {interaction.terminal_reason?.replace(/_/g, " ")}. Check that the configured local model is running.</p> : null}{interaction.assistant_text_truncated ? <small>This saved response was truncated.</small> : null}{interaction.flow_state === "partial_terminal" ? <button type="button" disabled={submitting} onClick={() => setPrompt(`Continue the previous answer from where it stopped. Do not repeat the completed part. Original request: ${interaction.user_text.slice(0, 1500)}\n\nPrevious partial answer:\n${(interaction.assistant_text ?? "").slice(-8500)}`)}>Continue as a new message</button> : null}{interaction.flow_state === "failed_terminal" ? <button type="button" disabled={submitting} onClick={() => setPrompt(interaction.user_text)}>Try this message again</button> : null}{interaction.persistence_error ? <small>Persistence diagnostic: {interaction.persistence_error}</small> : null}{interaction.proposal_ids.length ? <small>Proposal refs: {interaction.proposal_ids.join(", ")}</small> : null}</li>)}</ol> : null}
    {error ? <p className="jarvis-sidecar__status" role="status">{error}</p> : null}

    {basisDiscussionBlocked && <p role="status">Project Basis discussion is unavailable under the current sensitivity controls. Prepare a written proposal above, or clear selected context to ask a general question.</p>}
    <form onSubmit={(event) => void submit(event)} className="jarvis-sidecar__composer">
      <label htmlFor="jarvis-prompt">Message</label>
      <textarea id="jarvis-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} maxLength={12000} rows={5} disabled={!workspaceId || submitting} placeholder="Ask Jarvis…" />
      <button type="submit" disabled={!workspaceId || !activeRoute || !activeRouteAvailable || !prompt.trim() || loadingThreads || submitting || !contextReady}>{submitting ? "Submitting…" : loadingThreads ? "Loading conversations…" : contextEnabled ? pendingRetryReady ? "Retry with original context" : "Send with inspected context" : activeKnowledge ? "Send with selected context" : "Send without project context"}</button>
      <small>Enter submits. Shift+Enter adds a line. Closing the sidecar does not cancel canonical execution.</small>
    </form>
  </div>;
}
