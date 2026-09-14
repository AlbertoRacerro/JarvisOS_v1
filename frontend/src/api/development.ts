import { API_BASE_URL } from "./client";

export type RoadmapItem = {
  id: string;
  workspace_id: string;
  title: string;
  description?: string | null;
  item_type: string;
  status: string;
  priority: string;
  window_start_date?: string | null;
  window_end_date?: string | null;
  done_when?: string | null;
  done_when_satisfied?: boolean | null;
  revision: number;
};

export type CalendarAllocation = {
  id: string;
  workspace_id: string;
  roadmap_item_id?: string | null;
  title: string;
  event_type: string;
  start_instant: string;
  end_instant: string;
  timezone: string;
  priority?: string | null;
  revision: number;
};

export type BrainstormExactRef = {
  ref_type: "raw" | "brainstorm_revision" | "ai_thread_message" | "run_artifact" | "literature_entry";
  ref_id: string;
  revision?: number | null;
};

export type BrainstormRaw = {
  id: string;
  workspace_id: string;
  content: string;
  attachment_refs: BrainstormExactRef[];
  lineage_state: "NEW" | "DISCUSSED" | "RECONCILED" | "SUPERSEDED";
  created_by: string;
  created_at: string;
};

export type BrainstormRevision = {
  idea_id: string;
  workspace_id: string;
  revision: number;
  title: string;
  takeaway: string;
  synthesis: string;
  source_refs: BrainstormExactRef[];
  created_by: string;
  created_at: string;
};

export type BrainstormIdea = {
  id: string;
  workspace_id: string;
  current_revision: number;
  lineage_state: "NEW" | "DISCUSSED" | "RECONCILED" | "SUPERSEDED";
  successor_idea_id?: string | null;
  successor_revision?: number | null;
  current: BrainstormRevision;
  revisions?: BrainstormRevision[];
};

export type BrainstormPromotion = {
  id: string;
  workspace_id: string;
  idea_id: string;
  source_revision: number;
  target: "roadmap" | "design" | "coding";
  state: "pending" | "accepted" | "rejected";
  downstream_handoff_id?: string | null;
  created_by: string;
  created_at: string;
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    try {
      const payload = await response.json() as { detail?: { message?: string } | string };
      if (typeof payload.detail === "string") message = payload.detail;
      else if (payload.detail?.message) message = payload.detail.message;
    } catch {
      // Preserve the status-based fallback when a non-JSON error reaches the UI.
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function mutationId(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function listRoadmapItems(workspaceId: string): Promise<RoadmapItem[]> {
  return requestJson(`/development/roadmap/items?workspace_id=${encodeURIComponent(workspaceId)}`);
}

export function createRoadmapItem(workspaceId: string, title: string): Promise<RoadmapItem> {
  return requestJson("/development/roadmap/items", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: workspaceId,
      title,
      item_type: "Task",
      status: "Planned",
      priority: "Normal",
      created_by: "operator"
    })
  });
}

export function updateRoadmapItem(item: RoadmapItem, patch: Record<string, unknown>): Promise<RoadmapItem> {
  return requestJson(`/development/roadmap/items/${encodeURIComponent(item.id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_id: item.workspace_id, expected_revision: item.revision, actor: "operator", ...patch })
  });
}

export function deleteRoadmapItem(item: RoadmapItem): Promise<void> {
  return requestJson(`/development/roadmap/items/${encodeURIComponent(item.id)}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_id: item.workspace_id, expected_revision: item.revision, actor: "operator" })
  });
}

export function listCalendarAllocations(workspaceId: string): Promise<CalendarAllocation[]> {
  return requestJson(`/development/calendar/allocations?workspace_id=${encodeURIComponent(workspaceId)}`);
}

export function createCalendarAllocation(
  workspaceId: string,
  roadmapItemId: string | null,
  title: string,
  startLocal: string,
  endLocal: string,
  timezone: string
): Promise<CalendarAllocation> {
  return requestJson("/development/calendar/allocations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: workspaceId,
      roadmap_item_id: roadmapItemId,
      title,
      event_type: "work session",
      start_local: startLocal,
      end_local: endLocal,
      timezone,
      created_by: "operator"
    })
  });
}

export function updateCalendarAllocation(allocation: CalendarAllocation, patch: Record<string, unknown>): Promise<CalendarAllocation> {
  return requestJson(`/development/calendar/allocations/${encodeURIComponent(allocation.id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_id: allocation.workspace_id, expected_revision: allocation.revision, actor: "operator", ...patch })
  });
}

export function deleteCalendarAllocation(allocation: CalendarAllocation): Promise<void> {
  return requestJson(`/development/calendar/allocations/${encodeURIComponent(allocation.id)}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_id: allocation.workspace_id, expected_revision: allocation.revision, actor: "operator" })
  });
}

export function listBrainstormRaw(workspaceId: string): Promise<BrainstormRaw[]> {
  return requestJson(`/development/brainstorm/raw?workspace_id=${encodeURIComponent(workspaceId)}`);
}

export function createBrainstormRaw(workspaceId: string, content: string, attachmentRefs: BrainstormExactRef[] = []): Promise<BrainstormRaw> {
  return requestJson("/development/brainstorm/raw", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: workspaceId,
      content,
      attachment_refs: attachmentRefs,
      created_by: "operator",
      idempotency_key: mutationId("raw")
    })
  });
}

export function listBrainstormIdeas(workspaceId: string): Promise<BrainstormIdea[]> {
  return requestJson(`/development/brainstorm/ideas?workspace_id=${encodeURIComponent(workspaceId)}`);
}

export function getBrainstormIdea(workspaceId: string, ideaId: string): Promise<BrainstormIdea> {
  return requestJson(`/development/brainstorm/ideas/${encodeURIComponent(ideaId)}?workspace_id=${encodeURIComponent(workspaceId)}`);
}

export function recordBrainstormDiscussion(workspaceId: string, rawId: string): Promise<Record<string, unknown>> {
  return requestJson("/development/brainstorm/discussions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: workspaceId,
      target_type: "raw",
      target_id: rawId,
      expected_revision: null,
      source_refs: [{ ref_type: "raw", ref_id: rawId, revision: null }],
      actor: "operator",
      idempotency_key: mutationId("discussion")
    })
  });
}

export function reconcileBrainstorm(
  workspaceId: string,
  sourceRawId: string,
  title: string,
  takeaway: string,
  synthesis: string,
  idea?: BrainstormIdea
): Promise<BrainstormIdea> {
  return requestJson("/development/brainstorm/ideas/reconcile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: workspaceId,
      idea_id: idea?.id ?? null,
      expected_revision: idea?.current_revision ?? null,
      title,
      takeaway,
      synthesis,
      source_refs: [{ ref_type: "raw", ref_id: sourceRawId, revision: null }],
      actor: "operator",
      idempotency_key: mutationId("reconcile")
    })
  });
}

export function supersedeBrainstormIdea(source: BrainstormIdea, successor: BrainstormIdea): Promise<BrainstormIdea> {
  return requestJson(`/development/brainstorm/ideas/${encodeURIComponent(source.id)}/supersede`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: source.workspace_id,
      idea_id: source.id,
      expected_revision: source.current_revision,
      successor_idea_id: successor.id,
      successor_revision: successor.current_revision,
      actor: "operator",
      idempotency_key: mutationId("supersede")
    })
  });
}

export function listBrainstormPromotions(workspaceId: string): Promise<BrainstormPromotion[]> {
  return requestJson(`/development/brainstorm/promotions?workspace_id=${encodeURIComponent(workspaceId)}`);
}

export function createBrainstormPromotion(idea: BrainstormIdea, target: "roadmap" | "design" | "coding"): Promise<BrainstormPromotion> {
  return requestJson("/development/brainstorm/promotions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: idea.workspace_id,
      idea_id: idea.id,
      source_revision: idea.current_revision,
      target,
      payload: {
        proposal_only: true,
        title: idea.current.title,
        takeaway: idea.current.takeaway,
        source: { idea_id: idea.id, revision: idea.current_revision }
      },
      actor: "operator",
      idempotency_key: mutationId(`promotion-${target}`)
    })
  });
}
