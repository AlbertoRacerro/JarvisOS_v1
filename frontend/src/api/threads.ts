import { API_BASE_URL } from "./client";
import type { KnowledgeContextPreview } from "./knowledgeActions";

export type ConversationRoute = {
  route_class: string;
  label: string;
  model_id: string;
  execution_class: "local_compute" | "synthetic";
  availability: {
    configured: boolean;
    runtime_reachable: boolean | null;
    model_installed: boolean | null;
    model_loaded: boolean | null;
    qualified: true | false | "unknown";
    reason_code: string | null;
    message: string;
  };
};

export type ThreadSummary = {
  id: string;
  workspace_id: string;
  title: string | null;
  created_at: string;
  last_activity_at: string;
};

export type ThreadInteraction = {
  id: string;
  request_id: string;
  interaction_index: number;
  user_text: string;
  assistant_text: string | null;
  assistant_text_truncated: boolean;
  flow_id: string;
  persistence_state: string;
  persistence_error: string | null;
  flow_state: string;
  terminal_reason: string | null;
  attempt_count: number;
  terminal_attempt_id: string | null;
  execution_class?: string | null;
  model_id?: string | null;
  proposal_ids: string[];
  proposal_count: number;
  proposals_truncated: boolean;
  created_at: string;
  updated_at: string;
};

export type ThreadDetail = ThreadSummary & {
  interactions: ThreadInteraction[];
  has_older: boolean;
};

export type ContextSelection = {
  kinds?: string[];
  statuses?: Record<string, string[]> | string[] | null;
  ids?: string[] | null;
  query?: string | null;
  max_items_per_kind?: number;
};

export type ContextPackPreview = {
  context_digest: string | null;
  context_sources_manifest: Array<{ source: string; type?: string | null; id?: string | null }>;
  char_count: number;
  estimated_token_count: number;
  included_count: number;
  dropped_count: number;
  budget_chars: number;
};

export class ThreadsRequestError extends Error {
  readonly status: number;
  constructor(status: number) {
    super(`AI thread request failed with ${status}`);
    this.name = "ThreadsRequestError";
    this.status = status;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) }
  });
  if (!response.ok) throw new ThreadsRequestError(response.status);
  return response.json() as Promise<T>;
}

export async function listThreads(workspaceId: string): Promise<ThreadSummary[]> {
  const result = await requestJson<{ threads: ThreadSummary[] }>(
    `/ai/threads?workspace_id=${encodeURIComponent(workspaceId)}`
  );
  return result.threads;
}

export function getConversationOptions(): Promise<{routes: ConversationRoute[]; availability: "configured" | "unavailable"}> {
  return requestJson("/ai/threads/conversation-options");
}

export function getThread(workspaceId: string, threadId: string): Promise<ThreadDetail> {
  return requestJson(
    `/ai/threads/${encodeURIComponent(threadId)}?workspace_id=${encodeURIComponent(workspaceId)}`
  );
}

export function createThread(workspaceId: string, title?: string): Promise<ThreadSummary> {
  return requestJson("/ai/threads", {
    method: "POST",
    body: JSON.stringify({ workspace_id: workspaceId, title: title || null })
  });
}

export function previewThreadContext(
  workspaceId: string,
  selection: ContextSelection
): Promise<ContextPackPreview> {
  return requestJson("/ai/context/packs/preview", {
    method: "POST",
    body: JSON.stringify({ workspace_id: workspaceId, selection })
  });
}

export async function submitThreadInteraction(
  workspaceId: string,
  threadId: string,
  requestId: string,
  prompt: string,
  context?: { selection: ContextSelection; expectedDigest: string },
  options?: { routeClass: string; knowledgeContext?: KnowledgeContextPreview | null }
): Promise<ThreadInteraction> {
  const result = await requestJson<{ interaction: ThreadInteraction }>(
    `/ai/threads/${encodeURIComponent(threadId)}/interactions?workspace_id=${encodeURIComponent(workspaceId)}`,
    {
      method: "POST",
      body: JSON.stringify({
        request_id: requestId,
        prompt,
        ...(options ? { route_class: options.routeClass } : {}),
        ...(options?.knowledgeContext ? {
          jarvis_context: {
            workspace_id: options.knowledgeContext.workspace_id,
            route: {
              route_id: options.knowledgeContext.route_id,
              canonical_path: {
                "memory-project-basis": "/memory/project-basis",
                "memory-models": "/memory/models",
                "memory-literature": "/memory/literature"
              }[options.knowledgeContext.route_id]
            },
            added_context_refs: options.knowledgeContext.exact_refs
          },
          expected_jarvis_context_digest: options.knowledgeContext.context_digest
        } : {}),
        ...(context
          ? { context_selection: context.selection, expected_context_digest: context.expectedDigest }
          : {})
      })
    }
  );
  return result.interaction;
}
