import { API_BASE_URL } from "../../api/client";

export type LineageNodeKind =
  | "model_spec"
  | "model_version"
  | "simulation_run"
  | "runner_job"
  | "artifact"
  | "assumption"
  | "parameter"
  | "decision"
  | "requirement"
  | "ai_job"
  | "bluecad_candidate"
  | "bluecad_attempt"
  | "evidence";

export type LineageMetadataValue = string | number | boolean | null;

export type LineageNode = {
  ref: string;
  kind: LineageNodeKind;
  id: string;
  label: string;
  status: string | null;
  origin: string | null;
  created_at: string | null;
  metadata: Record<string, LineageMetadataValue>;
};

export type LineageEdge = {
  id: string;
  upstream_ref: string;
  downstream_ref: string;
  relation: string;
  edge_class: "dependency" | "provenance";
  authorities: string[];
  source_fields: string[];
};

export type LineageUnresolvedReference = {
  owner_ref: string;
  source_field: string;
  code:
    | "malformed_reference"
    | "unsupported_reference"
    | "dangling_reference"
    | "payload_invalid"
    | "payload_reference_invalid"
    | "context_manifest_invalid";
  raw_ref: string | null;
};

export type LineageDiagnostics = {
  unsupported_reference_count: number;
  malformed_reference_count: number;
  dangling_reference_count: number;
  cycle_count: number;
  manual_binding_count: number;
  unresolved_references: LineageUnresolvedReference[];
  cycles: string[][];
};

export type LineageGraph = {
  workspace_id: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
  topological_order: string[] | null;
  is_acyclic: boolean;
  diagnostics: LineageDiagnostics;
};

export type LineageFreshnessInvalidation = {
  id: string;
  source_ref: string;
  replacement_ref: string;
  affected_count: number | null;
  graph_digest: string | null;
  reason_code: string | null;
  path: string[] | null;
  path_digest: string | null;
  created_at: string;
};

export type LineageFreshness = {
  record_ref: string;
  state: "fresh" | "stale";
  invalidation_count: number;
  latest_invalidation: LineageFreshnessInvalidation | null;
};

export class LineageRequestError extends Error {
  readonly status: number;

  constructor(status: number) {
    super(`Request failed with ${status}`);
    this.name = "LineageRequestError";
    this.status = status;
  }
}

async function getLineageJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) throw new LineageRequestError(response.status);
  return response.json() as Promise<T>;
}

export function getLineageGraph(workspaceId: string): Promise<LineageGraph> {
  return getLineageJson<LineageGraph>(`/workspaces/${encodeURIComponent(workspaceId)}/flowsheet/graph`);
}

export function getLineageNode(workspaceId: string, nodeRef: string): Promise<LineageNode> {
  return getLineageJson<LineageNode>(
    `/workspaces/${encodeURIComponent(workspaceId)}/flowsheet/nodes/${encodeURIComponent(nodeRef)}`
  );
}

export function getLineageFreshness(workspaceId: string, nodeRef: string): Promise<LineageFreshness> {
  return getLineageJson<LineageFreshness>(
    `/workspaces/${encodeURIComponent(workspaceId)}/flowsheet/nodes/${encodeURIComponent(nodeRef)}/freshness`
  );
}
