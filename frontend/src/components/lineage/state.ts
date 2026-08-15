import type { StageSelection } from "../../app/selection";
import type { LineageGraph, LineageNode, LineageNodeKind } from "./api";

export type LineageRequestContext = Readonly<{
  generation: number;
  workspaceId: string;
  nodeRef: string | null;
}>;

export function acceptsLineageResponse(
  current: LineageRequestContext | null,
  request: LineageRequestContext
): boolean {
  return Boolean(
    current
      && current.generation === request.generation
      && current.workspaceId === request.workspaceId
      && current.nodeRef === request.nodeRef
  );
}

export function orderedLineageNodes(graph: LineageGraph): LineageNode[] {
  if (!graph.is_acyclic || !graph.topological_order) return graph.nodes;
  const byRef = new Map(graph.nodes.map((node) => [node.ref, node]));
  const ordered: LineageNode[] = [];
  const seen = new Set<string>();
  for (const ref of graph.topological_order) {
    const node = byRef.get(ref);
    if (!node || seen.has(ref)) continue;
    ordered.push(node);
    seen.add(ref);
  }
  for (const node of graph.nodes) {
    if (!seen.has(node.ref)) ordered.push(node);
  }
  return ordered;
}

const RESOURCE_BY_KIND = {
  model_spec: "model-spec",
  assumption: "assumption",
  parameter: "parameter",
  simulation_run: "simulation-run",
  decision: "decision",
  bluecad_candidate: "bluecad-candidate"
} as const satisfies Partial<Record<LineageNodeKind, string>>;

export function stageSelectionForLineageNode(workspaceId: string, node: LineageNode): StageSelection | null {
  const resource = RESOURCE_BY_KIND[node.kind];
  if (!resource) return null;
  return {
    kind: "record",
    ref: {
      resource,
      workspaceId,
      recordId: node.id
    }
  };
}

export function nodeMatchesFilter(node: LineageNode, query: string, kind: LineageNodeKind | "all"): boolean {
  const normalized = query.trim().toLowerCase();
  if (kind !== "all" && node.kind !== kind) return false;
  return !normalized || node.label.toLowerCase().includes(normalized) || node.ref.toLowerCase().includes(normalized);
}
