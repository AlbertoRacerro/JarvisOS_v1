import type { ActionOutcome, SurfaceRef } from "../../api/workspaceActions";
import type { StageSelection } from "../../app/selection";

export type ProcessSurface = { draft_id: string | null; process_selection: SurfaceRef["process_selection"] };
export function buildSurfaceRef(routeId: string, selection: StageSelection | null, process: ProcessSurface): SurfaceRef {
  if (routeId === "design-process") {
    return { route_id: routeId, draft_id: process.draft_id, process_selection: process.process_selection ?? [] };
  }
  if (routeId === "design-bluecad") {
    const validPart = selection?.kind === "bluecad-part" ? selection : null;
    const candidate = selection?.kind === "bluecad-part" || selection?.kind === "bluecad-binding-status"
      ? selection.candidateId
      : selection?.kind === "record" && selection.ref.resource === "bluecad-candidate" ? selection.ref.recordId : null;
    return { route_id: routeId, candidate_id: candidate, bluecad_part_ids: validPart ? [validPart.partId] : [] };
  }
  return { route_id: routeId };
}

export function isToolCallShaped(text: string | null | undefined): boolean {
  if (!text) return false;
  const normalized = text.trim();
  const candidates = [normalized, ...[...normalized.matchAll(/(?:```|~~~)(?:json|jsonc|javascript)?\s*\n?([\s\S]*?)\n?\s*(?:```|~~~)/gi)].map(match => match[1])];
  return candidates.some(candidate => {
    const value = candidate.trim();
    if (/<\|(?:tool_call|python_tag|function_call)\|>|<\|im_start\|>\s*(?:tool_call|function_call)\b|<start_function_call>|<\s*function(?:=|\s)|assistant\s+to=/i.test(value)) return true;
    if (/(?:mcp__jarvis__)?jarvis_(?:process|bluecad)_(?:act|read)\s*[({]/i.test(value)) return true;
    if (/\{\s*[\s\S]{0,1000}"name"\s*:\s*"[^"]+"[\s\S]{0,1000}"arguments"\s*:/i.test(value)) return true;
    if (/\{\s*[\s\S]{0,1000}"arguments"\s*:[\s\S]{0,1000}"name"\s*:\s*"[^"]+"/i.test(value)) return true;
    try {
      const parsed: unknown = JSON.parse(value);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        const record = parsed as Record<string, unknown>;
        if (typeof record.name === "string" && /(?:mcp__jarvis__)?jarvis_(?:process|bluecad)_(?:act|read)$/i.test(record.name)) return true;
        if (Array.isArray(record.tool_calls) && record.tool_calls.some(call => call && typeof call === "object" && "name" in call)) return true;
      }
    } catch { /* Prose and non-JSON answers remain visible. */ }
    return false;
  });
}

export function actionStatePresentation(state: ActionOutcome["state"]): { label: string; tone: "success" | "pending" | "plain" | "muted" } {
  switch (state) {
    case "applied": return { label: "Applied", tone: "success" };
    case "proposed": return { label: "Proposed", tone: "pending" };
    case "refused": return { label: "Refused", tone: "plain" };
    case "stale": return { label: "Stale", tone: "plain" };
    case "dismissed": return { label: "Dismissed", tone: "muted" };
    case "undone": return { label: "Undone", tone: "muted" };
  }
}

export function actionOriginLabel(origin: ActionOutcome["origin"]): string {
  return origin.kind === "local" ? "Jarvis local" : `Relay${origin.model ? ` · ${origin.model}` : ""}`;
}
