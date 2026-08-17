import { API_BASE_URL } from "./client";

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
  context?: { selection: ContextSelection; expectedDigest: string }
): Promise<ThreadInteraction> {
  const result = await requestJson<{ interaction: ThreadInteraction }>(
    `/ai/threads/${encodeURIComponent(threadId)}/interactions?workspace_id=${encodeURIComponent(workspaceId)}`,
    {
      method: "POST",
      body: JSON.stringify({
        request_id: requestId,
        prompt,
        ...(context
          ? { context_selection: context.selection, expected_context_digest: context.expectedDigest }
          : {})
      })
    }
  );
  return result.interaction;
}
