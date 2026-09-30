import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";

import type { KnowledgeContextPreview } from "../../api/knowledgeActions";
import type { StageSelection } from "../../app/selection";
import {
  ThreadsRequestError,
  confirmCloudEscalation,
  draftInteractionEscalation,
  escalateInteraction,
  getConversationOptions,
  getRelayStatus,
  listCloudEscalations,
  listRelayRuns,
  submitRelayRun,
  type CloudEscalation,
  type EscalationDraft,
  type ConversationRoute,
  type RelayRunRead,
  type RelayStatus,
  listThreads,
  getThread,
  createThread,
  previewThreadContext,
  submitThreadInteraction,
  type ContextPackPreview,
  type ContextSelection,
  type ThreadDetail,
  type ThreadInteraction,
  type ThreadSummary
} from "../../api/threads";
import JarvisMessageText from "./JarvisMessageText";
import "./JarvisSidecar.css";

const DEFAULT_SELECTION: ContextSelection = {};
const KNOWLEDGE_ROUTES = new Set(["memory-project-basis", "memory-models", "memory-literature"]);
const TERMINAL_FLOW_STATES = new Set(["complete", "partial_terminal", "failed_terminal", "cancelled_terminal"]);
const RESPONDER_STORAGE_KEY = "jarvisos.jarvis.responder";

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

type InFlight = Readonly<{ workspaceId: string; threadId: string | null; requestId: string | null; prompt: string; routeClass: string; startedAt: number }>;

function selectionIdentity(selection: StageSelection | null): string {
  if (selection === null) return "none";
  if (selection.kind === "record") {
    return `record:${selection.ref.workspaceId}:${selection.ref.resource}:${selection.ref.recordId}`;
  }
  return `geometry:${selection.viewerSessionId}:${selection.ephemeralObjectId}`;
}

function routeUsable(route: ConversationRoute | undefined): boolean {
  if (!route) return false;
  if (route.execution_class === "synthetic") return true;
  return Boolean(route.availability.runtime_reachable && (route.execution_class === "agent" || route.availability.model_installed));
}

function responderLabel(route: ConversationRoute): string {
  if (route.execution_class === "agent") return "Jarvis agent (Hermes)";
  if (route.execution_class === "synthetic") return "Test responder — not AI";
  return `Direct model · ${route.model_id}`;
}

function preferredRoute(routes: ConversationRoute[], current: string): string {
  if (routes.some(route => route.route_class === current && routeUsable(route))) return current;
  let stored: string | null = null;
  try { stored = window.localStorage.getItem(RESPONDER_STORAGE_KEY); } catch { stored = null; }
  const usable = routes.filter(routeUsable);
  return usable.find(route => route.route_class === stored)?.route_class
    ?? usable.find(route => route.execution_class === "agent")?.route_class
    ?? usable.find(route => route.execution_class === "local_compute")?.route_class
    ?? usable[0]?.route_class
    ?? routes.find(route => route.route_class === current)?.route_class
    ?? "";
}

type Readiness = Readonly<{ tone: "ready" | "busy" | "warning" | "down"; label: string; detail: string }>;

function readiness(route: ConversationRoute | undefined, routes: ConversationRoute[], optionsError: boolean, loaded: boolean): Readiness {
  if (optionsError) return { tone: "down", label: "Offline", detail: "The JarvisOS server is not reachable. It may be restarting; this panel retries automatically." };
  if (!loaded) return { tone: "busy", label: "Checking", detail: "Checking which responders are available…" };
  if (!route) return { tone: "down", label: "Unavailable", detail: "No conversation responder is configured on this machine." };
  const llama = routes.find(item => item.route_class === "local:llamacpp");
  if (route.execution_class === "agent") {
    if (!route.availability.runtime_reachable) return { tone: "down", label: "Unavailable", detail: route.availability.message };
    if (llama && !routeUsable(llama)) {
      return llama.availability.reason_code === "LLAMACPP_LOADING"
        ? { tone: "busy", label: "Loading model", detail: `The local model ${llama.model_id} is still loading. Messages will wait for it.` }
        : { tone: "warning", label: "Model unavailable", detail: llama.availability.message };
    }
    return { tone: "ready", label: "Ready", detail: route.availability.model_loaded ? "Jarvis agent is running on the local model." : "Jarvis agent starts with your first message (a few seconds)." };
  }
  if (route.execution_class === "synthetic") return { tone: "warning", label: "Test mode", detail: "Synthetic test responder: replies are canned, not AI answers." };
  if (!routeUsable(route)) return { tone: route.availability.reason_code === "LLAMACPP_LOADING" ? "busy" : "down", label: route.availability.reason_code === "LLAMACPP_LOADING" ? "Loading model" : "Unavailable", detail: route.availability.message };
  return { tone: "ready", label: "Ready", detail: `Answers come directly from the local model ${route.model_id}.` };
}

function relativeTime(iso: string): string {
  const seconds = Math.max(0, (Date.now() - Date.parse(iso)) / 1000);
  if (!Number.isFinite(seconds)) return "";
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h ago`;
  return new Date(iso).toLocaleDateString();
}

function outcomeNotice(interaction: ThreadInteraction): string | null {
  if (interaction.flow_state === "partial_terminal") {
    return interaction.terminal_reason === "output_length_limit"
      ? "This answer stopped at the output limit. You can ask Jarvis to continue."
      : "This answer ended before completion. You can try again or continue from the last visible text.";
  }
  if (interaction.flow_state === "failed_terminal") {
    if (interaction.terminal_reason?.endsWith("output_budget_exhausted")) return "The model spent its whole output budget before producing a visible answer. Try a shorter or more direct request.";
    return "Jarvis could not complete this request. Check that the selected responder is available, then try again.";
  }
  if (interaction.flow_state === "cancelled_terminal") return "This request was cancelled.";
  return null;
}

function relayRunTone(state: RelayRunRead["state"]): Readiness["tone"] {
  if (state === "queued" || state === "running") return "busy";
  if (state === "completed") return "ready";
  return "down";
}

function accessModeLabel(accessMode: "repository" | "derivative"): string {
  return accessMode === "repository" ? "real repository (read-write clone)" : "derivative workspace, no source";
}

function failureMessage(caught: unknown): string {
  if (caught instanceof ThreadsRequestError) {
    if (caught.status === 503) return "Jarvis is temporarily unavailable (the local runtime is busy or starting). Your message is kept — send it again in a moment.";
    return `Jarvis could not complete this request (server error ${caught.status}). Your message is kept; sending it again is safe and will not duplicate it.`;
  }
  return "The JarvisOS server did not answer. Your message is kept; sending it again is safe and will not duplicate it.";
}

export function useJarvisSidecar(
  workspaceId: string | null,
  routeId: string,
  selection: StageSelection | null,
  contextualContent?: ReactNode,
  knowledgeContext?: KnowledgeContextPreview | null,
  pinnedContent?: ReactNode
): ReactNode {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ThreadDetail | null>(null);
  const [preview, setPreview] = useState<ContextPackPreview | null>(null);
  const [projectPackEnabled, setContextEnabled] = useState(false);
  const [routes, setRoutes] = useState<ConversationRoute[]>([]);
  const [routesLoaded, setRoutesLoaded] = useState(false);
  const [routeClass, setRouteClass] = useState("");
  const [optionsError, setOptionsError] = useState(false);
  const activeKnowledge = knowledgeContext?.workspace_id === workspaceId && knowledgeContext.route_id === routeId ? knowledgeContext : null;
  const contextEnabled = projectPackEnabled && !activeKnowledge;
  const activeRoute = routes.find(route => route.route_class === routeClass);
  const activeRouteAvailable = routeUsable(activeRoute);

  useEffect(() => {
    let alive = true;
    const refresh = () => void getConversationOptions().then(result => {
      if (!alive) return;
      setRoutes(result.routes);
      setRoutesLoaded(true);
      setOptionsError(false);
      setRouteClass(current => preferredRoute(result.routes, current));
    }).catch(() => { if (alive) setOptionsError(true); });
    refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => { alive = false; window.clearInterval(timer); };
  }, []);

  // Relay availability and the allowed agent list are host configuration, not
  // per-workspace state; fetch once and let the agent select pick up a default.
  useEffect(() => {
    let alive = true;
    void getRelayStatus().then(result => {
      if (!alive) return;
      setRelayStatus(result);
      setRelayAgent(current => current || result.agents[0] || "");
    }).catch(() => { if (alive) setRelayStatus(null); });
    return () => { alive = false; };
  }, []);
  const [previewNonce, setPreviewNonce] = useState(0);
  const [prompt, setPrompt] = useState("");
  const [pending, setPending] = useState<PendingSubmit | null>(null);
  const [inFlight, setInFlight] = useState<InFlight | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [loadingThreads, setLoadingThreads] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cloudResults, setCloudResults] = useState<CloudEscalation[]>([]);
  const [cloudSource, setCloudSource] = useState<string | null>(null);
  const [cloudDraft, setCloudDraft] = useState<EscalationDraft | null>(null);
  const [cloudEditText, setCloudEditText] = useState("");
  const [cloudFamily, setCloudFamily] = useState("");
  const [cloudWorking, setCloudWorking] = useState(false);
  const [cloudPendingStarted, setCloudPendingStarted] = useState<number | null>(null);
  const [relayStatus, setRelayStatus] = useState<RelayStatus | null>(null);
  const [relayRuns, setRelayRuns] = useState<RelayRunRead[]>([]);
  const [relayAgent, setRelayAgent] = useState("");
  const [composerTarget, setComposerTarget] = useState<"jarvis" | "relay">("jarvis");
  const [relayAttested, setRelayAttested] = useState(false);
  const [relayWorking, setRelayWorking] = useState(false);
  const submitting = inFlight !== null;
  const workspaceOwner = useRef(0);
  const listOwner = useRef(0);
  const detailOwner = useRef(0);
  const previewOwner = useRef(0);
  const submitOwner = useRef(0);
  const selectedThreadRef = useRef<string | null>(null);
  const transcriptRef = useRef<HTMLOListElement | null>(null);
  const selectionKey = useMemo(() => selectionIdentity(selection), [selection]);
  selectedThreadRef.current = selectedThreadId;

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
    setInFlight(null);
    setPrompt("");
    setLoadingThreads(false);
    setPreviewLoading(false);
    setSubmitting(false);
    setError(null);
    setCloudResults([]);
    setCloudSource(null);
    setCloudDraft(null);
    setRelayRuns([]);
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
          setError("Your Jarvis conversations could not be loaded. They are safe on the server; reopen this panel to retry.");
        }
      })
      .finally(() => {
        if (workspaceOwner.current === workspaceToken && listOwner.current === listToken) {
          setLoadingThreads(false);
        }
      });
  }, [workspaceId]);

  const loadDetail = useCallback((threadId: string, quiet: boolean) => {
    if (!workspaceId) return;
    const token = ++detailOwner.current;
    const workspaceToken = workspaceOwner.current;
    void getThread(workspaceId, threadId)
      .then((next) => {
        if (detailOwner.current !== token || workspaceOwner.current !== workspaceToken || selectedThreadRef.current !== threadId) return;
        setDetail(next);
      })
      .catch(() => {
        if (!quiet && detailOwner.current === token && workspaceOwner.current === workspaceToken) {
          setError("This conversation could not be loaded. It is safe on the server; select it again to retry.");
        }
      });
  }, [workspaceId]);

  useEffect(() => {
    setDetail(null);
    setCloudResults([]);
    setCloudSource(null);
    setCloudDraft(null);
    setRelayRuns([]);
    if (!workspaceId || !selectedThreadId) return;
    let active = true;
    loadDetail(selectedThreadId, false);
    void listCloudEscalations(workspaceId, selectedThreadId).then(result => {
      if (active) setCloudResults(result);
    }).catch(() => {});
    if (relayStatus?.enabled) {
      void listRelayRuns(workspaceId, selectedThreadId).then(result => {
        if (active) setRelayRuns(result);
      }).catch(() => {});
    }
    return () => { active = false; };
  }, [workspaceId, selectedThreadId, loadDetail, relayStatus?.enabled]);

  // Later turns in a thread continue the same Relay session; keep the run list
  // current while anything is still queued or running, then stop polling.
  const relayRunsActive = relayRuns.some(run => run.state === "queued" || run.state === "running");
  useEffect(() => {
    if (!workspaceId || !selectedThreadId || !relayRunsActive) return;
    const targetThread = selectedThreadId;
    const timer = window.setInterval(() => {
      void listRelayRuns(workspaceId, targetThread).then(result => {
        if (selectedThreadRef.current === targetThread) setRelayRuns(result);
      }).catch(() => {});
    }, 3000);
    return () => window.clearInterval(timer);
  }, [workspaceId, selectedThreadId, relayRunsActive]);

  const sendCloud = async () => {
    if (!workspaceId || !selectedThreadId || !cloudSource || !cloudDraft || cloudWorking) return;
    if (cloudDraft.status !== "ready" || !cloudDraft.text_digest || cloudEditText !== cloudDraft.text) return;
    const targetThread = selectedThreadId;
    setCloudWorking(true);
    setCloudPendingStarted(Date.now());
    setError(null);
    try {
      const result = await escalateInteraction(workspaceId, targetThread, cloudSource,
        cloudDraft.text, cloudDraft.text_digest, cloudFamily || undefined);
      if (selectedThreadRef.current === targetThread) {
        setCloudResults(current => [result, ...current.filter(item => item.id !== result.id)]);
        setCloudSource(null);
        setCloudDraft(null);
      }
    } catch (caught) {
      setError(caught instanceof ThreadsRequestError
        ? caught.detail ?? `Cloud escalation was not dispatched (${caught.status}). Check the provider and budget settings.`
        : "Cloud escalation could not be completed. Check its status before retrying.");
    } finally { setCloudWorking(false); setCloudPendingStarted(null); }
  };

  const prepareEscalation = async (family?: string, sourceInteraction = cloudSource, editedText?: string) => {
    if (!workspaceId || !selectedThreadId || !sourceInteraction || cloudWorking) return;
    setCloudWorking(true);
    setError(null);
    try {
      const draft = await draftInteractionEscalation(workspaceId, selectedThreadId, sourceInteraction, family, editedText);
      setCloudDraft(draft);
      setCloudEditText(draft.text);
      setCloudFamily(family ?? "");
    } catch (caught) {
      setError(caught instanceof ThreadsRequestError ? caught.detail ?? "This turn cannot be escalated." : "Jarvis could not prepare the cloud request.");
    } finally { setCloudWorking(false); }
  };

  const confirmCloud = async (escalationId: string) => {
    if (!workspaceId || !selectedThreadId || cloudWorking) return;
    const targetThread = selectedThreadId;
    setCloudWorking(true);
    setError(null);
    try {
      const result = await confirmCloudEscalation(workspaceId, targetThread, escalationId);
      if (selectedThreadRef.current === targetThread) {
        setCloudResults(current => current.map(item => item.id === result.id ? result : item));
      }
    } catch {
      setError("The cloud confirmation could not be used. The approved derivative or provider policy may have changed.");
    } finally { setCloudWorking(false); }
  };

  const sendRelay = async () => {
    const relayText = prompt.trim();
    if (!workspaceId || !relayAgent || !relayText || !relayAttested || relayWorking) return;
    setRelayWorking(true);
    setError(null);
    try {
      let targetThread = selectedThreadId;
      if (!targetThread) {
        // A new conversation has no thread until its first submission, as with ordinary messages.
        const created = await createThread(workspaceId, relayText.slice(0, 70));
        targetThread = created.id;
        setThreads((current) => [created, ...current]);
        selectedThreadRef.current = created.id;
        setSelectedThreadId(created.id);
      }
      const result = await submitRelayRun(workspaceId, targetThread, {
        prompt: relayText, agent: relayAgent, cloud_safe_attested: relayAttested
      });
      if (selectedThreadRef.current === targetThread) {
        setRelayRuns(current => [...current.filter(item => item.id !== result.id), result]);
        setPrompt("");
        setRelayAttested(false);
      }
    } catch (caught) {
      setError(caught instanceof ThreadsRequestError && caught.status === 409
        ? "A Relay run is already in progress for this conversation. Wait for it to finish, then send again."
        : "The Relay run could not be started. Check that Relay is enabled and the agent is on the allowed list.");
    } finally { setRelayWorking(false); }
  };

  // A turn keeps running on the server while you navigate, refresh or switch
  // conversations; poll the selected conversation until it settles.
  const detailRunning = Boolean(detail?.interactions.some((interaction) => !TERMINAL_FLOW_STATES.has(interaction.flow_state)));
  const inFlightHere = Boolean(inFlight && inFlight.threadId === selectedThreadId);
  useEffect(() => {
    if (!selectedThreadId || !(detailRunning || inFlightHere)) return;
    const timer = window.setInterval(() => loadDetail(selectedThreadId, true), 2500);
    return () => window.clearInterval(timer);
  }, [selectedThreadId, detailRunning, inFlightHere, loadDetail]);

  useEffect(() => {
    if (!inFlight && !detailRunning && !relayRunsActive && cloudPendingStarted === null) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [inFlight, detailRunning, relayRunsActive, cloudPendingStarted]);

  useEffect(() => {
    const list = transcriptRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [detail, inFlightHere]);

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
          setError("The project context preview could not be built. Turn project context off, or try again.");
        }
      })
      .finally(() => {
        if (previewOwner.current === token && workspaceOwner.current === workspaceToken) {
          setPreviewLoading(false);
        }
      });
  }, [workspaceId, contextEnabled, routeId, selectionKey, previewNonce]);

  function setSubmitting(value: false) {
    if (!value) setInFlight(null);
  }

  const selectThread = (threadId: string | null) => {
    if (threadId === selectedThreadId) return;
    detailOwner.current += 1;
    submitOwner.current += 1;
    setSelectedThreadId(threadId);
    setDetail(null);
    setPending(null);
    setError(null);
  };

  const chooseResponder = (next: string) => {
    setRouteClass(next);
    setPending(null);
    setError(null);
    try { window.localStorage.setItem(RESPONDER_STORAGE_KEY, next); } catch { /* preference only */ }
  };

  const submit = async (event?: FormEvent) => {
    event?.preventDefault();
    if (composerTarget === "relay") { await sendRelay(); return; }
    const text = prompt.trim();
    // Wait for thread ownership to settle before auto-creating or dispatching.
    // Otherwise a delayed initial list (or explicit creation) can select a
    // different thread while this submit publishes its transcript.
    if (!workspaceId || !text || loadingThreads || submitting || !activeRoute || !activeRouteAvailable || activeKnowledge?.route_id === "memory-project-basis") return;
    const workspaceToken = workspaceOwner.current;
    const creationToken = ++submitOwner.current;
    setError(null);
    setInFlight({ workspaceId, threadId: selectedThreadId, requestId: null, prompt: text, routeClass, startedAt: Date.now() });
    let threadId = selectedThreadId;
    if (!threadId) {
      try {
        const created = await createThread(workspaceId, text.slice(0, 70));
        if (workspaceOwner.current !== workspaceToken || submitOwner.current !== creationToken) return;
        threadId = created.id;
        setThreads((current) => [created, ...current]);
        selectedThreadRef.current = created.id;
        setSelectedThreadId(created.id);
      } catch (caught) {
        if (workspaceOwner.current !== workspaceToken || submitOwner.current !== creationToken) return;
        setError(failureMessage(caught));
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
      setError("Project context is empty or out of date. Refresh it, or turn project context off.");
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
    setPending(captured);
    setInFlight({ workspaceId, threadId, requestId: captured.requestId, prompt: text, routeClass, startedAt: Date.now() });
    setPrompt("");
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
      if (workspaceOwner.current !== workspaceToken) return;
      setPending(null);
      setThreads((current) => {
        const hit = current.find((item) => item.id === captured.threadId);
        return hit ? [{ ...hit, last_activity_at: new Date().toISOString() }, ...current.filter((item) => item.id !== captured.threadId)] : current;
      });
      // Publish only into the conversation this turn belongs to.
      if (selectedThreadRef.current === captured.threadId) loadDetail(captured.threadId, false);
      if (captured.contextEnabled) setPreviewNonce((current) => current + 1);
    } catch (caught) {
      if (workspaceOwner.current !== workspaceToken) return;
      setPrompt((current) => current || captured.prompt);
      if (caught instanceof ThreadsRequestError && caught.status === 409 && (captured.contextEnabled || captured.knowledgeContext)) {
        setPending(null);
        setError("The selected context changed while you were writing. Remove it and add it again, then send.");
        setPreviewNonce((current) => current + 1);
      } else {
        setError(failureMessage(caught));
      }
      if (selectedThreadRef.current === captured.threadId) loadDetail(captured.threadId, true);
    } finally {
      if (workspaceOwner.current === workspaceToken) setSubmitting(false);
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
  const state = readiness(activeRoute, routes, optionsError, routesLoaded);
  const usableRoutes = routes.filter(routeUsable);
  const unavailableRoutes = routes.filter((route) => !routeUsable(route));
  const serverHasInFlight = Boolean(inFlight?.requestId && detail?.interactions.some((interaction) => interaction.request_id === inFlight.requestId));
  const showOptimistic = inFlight && inFlight.workspaceId === workspaceId && (inFlight.threadId === selectedThreadId || inFlight.threadId === null) && !serverHasInFlight;
  const hermesCold = activeRoute?.execution_class === "agent" && !activeRoute.availability.model_loaded;
  const sendDisabledReason = !workspaceId ? "Select a workspace to talk to Jarvis."
    : !activeRouteAvailable ? state.detail
    : basisDiscussionBlocked ? null
    : null;
  const contextSummary = activeKnowledge ? `${activeKnowledge.included_count} selected record${activeKnowledge.included_count === 1 ? "" : "s"} attached`
    : contextEnabled ? "Project context attached" : "No project context";
  const workingLabel = (startedAt: number, route: string) => {
    const seconds = Math.max(0, Math.round((now - startedAt) / 1000));
    const agent = routes.find((item) => item.route_class === route)?.execution_class === "agent";
    return `${agent ? "Jarvis agent is working" : "Jarvis is thinking"} · ${seconds}s`;
  };
  const composerLabel = contextEnabled ? pendingRetryReady ? "Retry with original context" : "Send with inspected context" : activeKnowledge ? "Send with selected context" : "Send without project context";

  const renderInteraction = (interaction: ThreadInteraction) => {
    const running = !TERMINAL_FLOW_STATES.has(interaction.flow_state);
    const notice = outcomeNotice(interaction);
    const viaAgent = interaction.execution_class === "agent";
    const synthetic = interaction.execution_class === "synthetic";
    const elapsed = interaction.elapsed_ms ?? interaction.latency_ms;
    const providerKind = interaction.execution_class === "external_provider" ? "cloud" : interaction.execution_class === "synthetic" ? "synthetic" : "local";
    const metadata = [interaction.model_id ?? "Model unknown", `${providerKind} · ${interaction.provider_id ?? "provider unknown"}`, elapsed != null ? `${(elapsed / 1000).toFixed(1)}s` : null, interaction.cost_estimate_usd != null ? `$${interaction.cost_estimate_usd.toFixed(6)}` : null].filter(Boolean).join(" · ");
    return <li key={interaction.id} className="jarvis-turn">
      <div className="jarvis-bubble jarvis-bubble--user"><p>{interaction.user_text}</p></div>
      <div className={`jarvis-bubble jarvis-bubble--jarvis${running ? " is-working" : ""}${notice && !interaction.assistant_text ? " is-failed" : ""}`}>
        <div className="jarvis-bubble__meta">
          <span className="jarvis-bubble__author">{synthetic ? "Test responder" : "Jarvis"}</span>
          <span>{running ? "working…" : viaAgent ? `agent · ${interaction.model_id ?? "local model"}` : interaction.model_id ?? ""}</span>
        </div>
        {running
          ? <p className="jarvis-working"><span className="jarvis-working__dots" aria-hidden="true"><i /><i /><i /></span>{interaction.activity ?? "Thinking…"} · {Math.max(0, Math.floor((now - Date.parse(interaction.created_at)) / 1000))}s</p>
          : interaction.assistant_text ? <JarvisMessageText text={interaction.assistant_text} /> : null}
        {notice ? <p className="jarvis-bubble__notice" role="status">{notice}</p> : null}
        {interaction.assistant_text_truncated ? <p className="jarvis-bubble__notice">This saved answer was shortened for storage.</p> : null}
        {interaction.assistant_text && !synthetic ? <p className="jarvis-bubble__advisory">Advisory answer · no project change was applied.</p> : null}
        {interaction.proposal_count ? <p className="jarvis-bubble__proposals">{interaction.proposal_count}{interaction.proposals_truncated ? "+" : ""} proposal{interaction.proposal_count === 1 ? "" : "s"} recorded for your review — nothing was applied.</p> : null}
        <div className="jarvis-bubble__actions">
          {interaction.flow_state === "partial_terminal" ? <button type="button" className="jarvis-link-button" disabled={submitting} onClick={() => setPrompt(`Continue the previous answer from where it stopped. Do not repeat the completed part. Original request: ${interaction.user_text.slice(0, 1500)}\n\nPrevious partial answer:\n${(interaction.assistant_text ?? "").slice(-8500)}`)}>Continue answer</button> : null}
          {interaction.flow_state === "failed_terminal" ? <button type="button" className="jarvis-link-button" disabled={submitting} onClick={() => setPrompt(interaction.user_text)}>Try again</button> : null}
          {interaction.assistant_text && !running ? <p className="jarvis-bubble__metadata">{metadata}</p> : null}
          {!running && interaction.execution_class === "local_compute" && interaction.assistant_text ? <button type="button" className="jarvis-link-button" disabled={submitting || cloudWorking} onClick={() => { setCloudSource(interaction.id); setCloudDraft(null); setCloudEditText(""); void prepareEscalation(undefined, interaction.id); }}>Escalate</button> : null}
          <details className="jarvis-bubble__details"><summary aria-label="Show answer information">ⓘ Info</summary><dl><div><dt>Responder</dt><dd>{viaAgent ? "Jarvis agent (Hermes)" : interaction.route_class ?? "Unknown"}</dd></div><div><dt>Model</dt><dd>{interaction.model_id ?? "Unknown"}</dd></div><div><dt>Provider</dt><dd>{interaction.provider_id ?? "Unknown"}</dd></div><div><dt>Run state</dt><dd>{interaction.flow_state}</dd></div><div><dt>Persistence</dt><dd>{interaction.persistence_state}</dd></div><div><dt>Attempts</dt><dd>{interaction.attempt_count}</dd></div><div><dt>Tokens</dt><dd>{interaction.input_tokens ?? "unknown"} in · {interaction.output_tokens ?? "unknown"} out</dd></div><div><dt>Cost</dt><dd>{interaction.cost_estimate_usd == null ? "unknown" : `$${interaction.cost_estimate_usd}`}</dd></div><div><dt>Latency</dt><dd>{interaction.latency_ms == null ? "unknown" : `${interaction.latency_ms} ms`}</dd></div><div><dt>Flow</dt><dd><code>{interaction.flow_id}</code></dd></div></dl>{interaction.persistence_error ? <p>Persistence diagnostic: {interaction.persistence_error}</p> : null}{interaction.proposal_ids.length ? <p>Proposal refs: {interaction.proposal_ids.join(", ")}</p> : null}</details>
        </div>
      </div>
      {cloudSource === interaction.id ? <section className="jarvis-linked-result" aria-label="Governed cloud escalation"><strong>Review cloud request</strong>{cloudPendingStarted !== null ? <p className="jarvis-working" role="status"><span className="jarvis-working__dots" aria-hidden="true"><i /><i /><i /></span>Checking cloud request… · {Math.max(0, Math.floor((now - cloudPendingStarted) / 1000))}s</p> : null}<p>Only the approved text below can leave this conversation.</p>{!cloudDraft ? <p role="status">{cloudWorking ? "Checking provider, cost and sensitivity…" : error ?? "Could not prepare this cloud request."}</p> : <><p>{cloudDraft.reason}</p><label className="jarvis-sidecar__field"><span>Exact text for the cloud model</span><textarea value={cloudEditText} onChange={event => { setCloudEditText(event.target.value); setCloudDraft({ ...cloudDraft, status: "edit_required", text_digest: null }); }} rows={4} /></label><p>{cloudDraft.candidate ? `${cloudDraft.candidate.provider_id}/${cloudDraft.candidate.model_id} · maximum $${cloudDraft.candidate.max_cost_usd} · ${cloudDraft.task_family}${cloudDraft.task_family_inferred ? " (inferred)" : ""}` : `Task type: ${cloudDraft.task_family}`}</p><details><summary>Advanced · task type</summary><label className="jarvis-sidecar__field"><span>Override task type</span><select value={cloudFamily || cloudDraft.task_family} onChange={event => void prepareEscalation(event.target.value, cloudSource, cloudEditText)}>{cloudDraft.family_options.map(family => <option key={family}>{family}</option>)}</select></label></details>{cloudDraft.status === "ready" && cloudDraft.text_digest && cloudEditText === cloudDraft.text ? <button type="button" disabled={cloudWorking} onClick={() => void sendCloud()}>{cloudWorking ? "Checking and sending…" : "Approve text and escalate"}</button> : cloudDraft.status !== "refused" && cloudEditText.trim() ? <button type="button" disabled={cloudWorking} onClick={() => void prepareEscalation(cloudFamily || undefined, cloudSource, cloudEditText)}>{cloudWorking ? "Checking…" : "Review edited text"}</button> : null}<button type="button" className="jarvis-link-button" onClick={() => { setCloudSource(null); setCloudDraft(null); }}>Cancel</button></>}</section> : null}
      {cloudResults.filter(item => item.source_interaction_id === interaction.id).map(item => <section className="jarvis-linked-result" key={item.id} aria-label="Cloud advice"><strong>Cloud advice · {item.provider_id}/{item.model_id} · {item.state}</strong>{item.response_text ? <JarvisMessageText text={item.response_text} /> : <p>{item.reason_code ?? "Waiting for cloud model…"}</p>}<p className="jarvis-bubble__advisory">Advisory only · no local action was applied.</p><details><summary>Cloud provenance</summary><p>{item.task_family} · tier {item.quality_tier} · maximum ${item.projected_cost_usd} · actual €{item.accounted_cost_eur}</p><p>Tokens: {item.actual_input_tokens ?? "unknown"} in · {item.actual_output_tokens ?? "unknown"} out · derivative {item.derivative_digest} · packet {item.egress_packet_digest ?? "none"}</p>{item.state === "confirmation_required" ? <button type="button" disabled={cloudWorking} onClick={() => void confirmCloud(item.id)}>Approve packet</button> : null}</details></section>)}
      {detail?.interactions[detail.interactions.length - 1]?.id === interaction.id ? relayRuns.map(run => <section className="jarvis-linked-result" key={run.id} aria-label="Relay run"><strong>Relay · {run.agent} · {run.state}</strong>{run.state === "queued" || run.state === "running" ? <p className="jarvis-working"><span className="jarvis-working__dots" aria-hidden="true"><i /><i /><i /></span>Waiting for Relay… · {Math.max(0, Math.floor((now - Date.parse(run.started_at ?? run.created_at)) / 1000))}s</p> : null}{run.result_text ? <p>{run.result_text}</p> : null}<details><summary>Relay run information</summary><p>{accessModeLabel(run.access_mode)} · turn {run.turn_index}</p>{run.reason_code || run.stop_reason ? <p>{run.reason_code ?? run.stop_reason}</p> : null}{run.workspace_path ? <p>Workspace <code>{run.workspace_path}</code> · head {run.head_commit ?? "unknown"}</p> : null}{run.change_summary ? <pre className="jarvis-relay-result">{run.change_summary}</pre> : null}</details></section>) : null}
    </li>;
  };

  return <div className="jarvis-sidecar" data-testid="jarvis-sidecar">
    <header className="jarvis-sidecar__header">
      <div className="jarvis-sidecar__title">
        <h3>Jarvis</h3>
        <span className={`jarvis-status jarvis-status--${state.tone}`} role="status" title={state.detail}><i aria-hidden="true" />{state.label}</span>
      </div>
      <button type="button" className="jarvis-sidecar__new" onClick={() => selectThread(null)} disabled={!workspaceId || submitting || selectedThreadId === null}>New conversation</button>
    </header>
    <p className="jarvis-sidecar__readiness">{state.detail}</p>

    {!workspaceId ? <p className="jarvis-sidecar__empty">Select a workspace to use Jarvis.</p> : <div className="jarvis-sidecar__controls">
      <label className="jarvis-sidecar__field"><span>Conversation</span><select value={selectedThreadId ?? ""} onChange={(event) => selectThread(event.target.value || null)} disabled={loadingThreads}>
        <option value="">{loadingThreads ? "Loading…" : "New conversation"}</option>
        {threads.map((thread) => <option key={thread.id} value={thread.id}>{(thread.title || "Untitled conversation").slice(0, 60)} · {relativeTime(thread.last_activity_at)}</option>)}
      </select></label>
      <label className="jarvis-sidecar__field"><span>Responder</span><select aria-label="Jarvis responder" value={routeClass} disabled={submitting || !routes.length} onChange={(event) => chooseResponder(event.target.value)}>
        {!routes.length && <option value="">Unavailable</option>}
        {usableRoutes.map((route) => <option value={route.route_class} key={route.route_class}>{responderLabel(route)}</option>)}
        {unavailableRoutes.length ? <optgroup label="Not available now">{unavailableRoutes.map((route) => <option value={route.route_class} key={route.route_class} disabled>{responderLabel(route)} — {route.availability.message}</option>)}</optgroup> : null}
      </select></label>
    </div>}

    <details className="jarvis-sidecar__context" aria-label="Project context controls"><summary><span>Context</span><span className="jarvis-sidecar__context-summary">{contextSummary}</span></summary>
      {contextualContent ? <section className={stageContextClassName} aria-label="Current stage context">{contextualContent}</section> : null}
      <label className="jarvis-sidecar__toggle"><input type="checkbox" checked={contextEnabled} disabled={submitting || Boolean(activeKnowledge)} onChange={(event) => { setContextEnabled(event.target.checked); setError(null); }} />Use inspected project context</label>
      {contextEnabled && previewLoading ? <p className="jarvis-sidecar__hint">Building context preview…</p> : null}
      {contextEnabled && preview ? <details><summary>Context pack · {preview.included_count} records · ~{preview.estimated_token_count} tokens</summary><p>Digest <code>{preview.context_digest ?? "empty"}</code></p><p>{preview.char_count} characters · {preview.dropped_count} dropped</p><ul>{preview.context_sources_manifest.map((source) => <li key={`${source.type}:${source.id}:${source.source}`}>{source.type ?? "record"}: {source.id ?? source.source}</li>)}</ul></details> : null}
      {contextEnabled ? <button type="button" className="jarvis-link-button" onClick={() => setPreviewNonce((current) => current + 1)} disabled={!workspaceId || previewLoading || submitting}>Refresh context preview</button> : <p className="jarvis-sidecar__hint">{activeKnowledge ? `${activeKnowledge.included_count} exact selected records will be sent with your message.` : "Project context is off. Only your message is sent."}</p>}
      {pendingRetryReady && contextEnabled ? <p className="jarvis-sidecar__hint">A retry keeps the originally inspected context digest.</p> : null}
    </details>

    <ol className="jarvis-sidecar__transcript" aria-label="Jarvis conversation" aria-live="polite" ref={transcriptRef}>
      {!detail && !showOptimistic && workspaceId ? <li className="jarvis-sidecar__welcome">
        <strong>Ask Jarvis about this workspace.</strong>
        <span>Jarvis explains, inspects and proposes. Its answers are advice: nothing in your project changes until you accept a proposal.</span>
      </li> : null}
      {detail?.interactions.map(renderInteraction)}
      {showOptimistic && inFlight ? <li className="jarvis-turn" key="in-flight">
        <div className="jarvis-bubble jarvis-bubble--user"><p>{inFlight.prompt}</p></div>
        <div className="jarvis-bubble jarvis-bubble--jarvis is-working">
          <div className="jarvis-bubble__meta"><span className="jarvis-bubble__author">Jarvis</span><span>working…</span></div>
          <p className="jarvis-working"><span className="jarvis-working__dots" aria-hidden="true"><i /><i /><i /></span>{workingLabel(inFlight.startedAt, inFlight.routeClass)}</p>
          {hermesCold ? <p className="jarvis-bubble__notice">The first message starts the agent; later replies are faster.</p> : null}
        </div>
      </li> : null}
    </ol>


    {pinnedContent}
    {error ? <p className="jarvis-sidecar__error" role="alert">{error}</p> : null}
    {basisDiscussionBlocked && <p className="jarvis-sidecar__error" role="status">Project Basis discussion is unavailable under the current sensitivity controls. Prepare a written proposal above, or clear selected context to ask a general question.</p>}
    <form onSubmit={(event) => void submit(event)} className="jarvis-sidecar__composer">
      <label className="jarvis-sidecar__field"><span>Send to</span><select value={composerTarget} onChange={event => setComposerTarget(event.target.value as "jarvis" | "relay")} disabled={submitting || relayWorking}><option value="jarvis">Jarvis</option>{relayStatus?.enabled ? <option value="relay">Relay agent</option> : null}</select></label>
      {composerTarget === "relay" && relayStatus?.enabled ? <>
        <label className="jarvis-sidecar__field"><span>Relay agent</span><select value={relayAgent} disabled={relayWorking || !relayStatus.agents.length} onChange={event => setRelayAgent(event.target.value)}>{relayStatus.agents.map(agent => <option key={agent}>{agent}</option>)}</select></label>
        <p className="jarvis-sidecar__hint">Relay uses {accessModeLabel(relayStatus.access_mode)} access at level {relayStatus.repository_level}. {relayStatus.blocked_reason ?? "Only submit a task that contains no strategic or domain IP."}</p>
        <label className="jarvis-sidecar__toggle"><input type="checkbox" checked={relayAttested} disabled={relayWorking} onChange={event => setRelayAttested(event.target.checked)} />This task contains no strategic/domain IP (cloud-safe)</label>
      </> : null}
      <label htmlFor="jarvis-prompt" className="visually-hidden">{composerTarget === "relay" ? "Message to Relay" : "Message to Jarvis"}</label>
      <textarea id="jarvis-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} maxLength={12000} rows={Math.min(8, Math.max(2, prompt.split("\n").length))} disabled={!workspaceId} placeholder={composerTarget === "relay" ? "Task for the Relay agent…" : activeRoute?.execution_class === "agent" ? "Ask the Jarvis agent…" : "Ask Jarvis…"} />
      <div className="jarvis-sidecar__composer-bar">
        <small>{sendDisabledReason && !activeRouteAvailable ? sendDisabledReason : "Enter to send · Shift+Enter for a new line"}</small>
        <button type="submit" disabled={!workspaceId || !prompt.trim() || loadingThreads || (composerTarget === "jarvis" ? (!activeRoute || !activeRouteAvailable || submitting || !contextReady) : (!relayAgent || !relayAttested || relayWorking || Boolean(relayStatus?.blocked_reason)))} aria-label={composerTarget === "relay" ? "Send to Relay agent" : composerLabel} title={composerTarget === "relay" ? "Send to Relay agent" : composerLabel}>{submitting || relayWorking ? "Working…" : loadingThreads ? "Loading…" : "Send"}</button>
      </div>
    </form>
  </div>;
}
