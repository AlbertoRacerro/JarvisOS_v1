import type { ProcessSurface } from "../components/ai/workspaceActionPresentation";

const SURFACE_EVENT = "jarvis:workspace-surface";
let processSurface: ProcessSurface = { draft_id: null, process_selection: [] };

export function publishProcessSurface(next: ProcessSurface): void {
  processSurface = next;
  window.dispatchEvent(new CustomEvent(SURFACE_EVENT, { detail: next }));
}

export function currentProcessSurface(): ProcessSurface { return processSurface; }

export function listenForProcessSurface(listener: (next: ProcessSurface) => void): () => void {
  const receive = (event: Event) => listener((event as CustomEvent<ProcessSurface>).detail);
  window.addEventListener(SURFACE_EVENT, receive);
  return () => window.removeEventListener(SURFACE_EVENT, receive);
}

export type WorkspaceActionEvent = {
  workspaceId: string; surface: "process" | "bluecad"; state: "applied" | "undone";
  draftId?: string | null; resultRevision?: string | null; candidateId?: string | null; childCandidateId?: string | null;
};

export function publishWorkspaceAction(event: WorkspaceActionEvent): void {
  window.dispatchEvent(new CustomEvent("jarvis:workspace-action", { detail: event }));
}
