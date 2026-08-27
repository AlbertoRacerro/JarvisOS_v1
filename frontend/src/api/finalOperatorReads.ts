import { API_BASE_URL, type SystemInfoResponse, getSystemInfo } from "./client";

export type FinalWorkspace = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  status: string;
};

export type FinalModelSpec = {
  id: string;
  workspace_id: string;
  title: string;
  engineering_question: string;
  scope?: string | null;
  status: string;
  maturity_status: string;
  schema_version: number;
  created_at: string;
  updated_at: string;
};

export type FinalRequirement = {
  id: string;
  workspace_id: string;
  statement: string;
  rationale?: string | null;
  status: string;
  notes?: string | null;
  schema_version: number;
  created_at: string;
  updated_at: string;
};

export type FinalParameter = {
  id: string;
  workspace_id: string;
  name: string;
  symbol?: string | null;
  value?: string | null;
  unit?: string | null;
  value_status?: string | null;
  status: string;
  lifecycle_state?: string | null;
};

export type FinalDecision = {
  id: string;
  workspace_id: string;
  title: string;
  decision_text: string;
  rationale?: string | null;
  status: string;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) throw new Error(`Request failed with ${response.status}`);
  return response.json() as Promise<T>;
}

export function listFinalWorkspaces(): Promise<FinalWorkspace[]> {
  return getJson<FinalWorkspace[]>("/workspaces");
}

export function listFinalModelSpecs(workspaceId: string): Promise<FinalModelSpec[]> {
  return getJson<FinalModelSpec[]>(`/workspaces/${workspaceId}/model-specs`);
}

export function listFinalRequirements(workspaceId: string): Promise<FinalRequirement[]> {
  return getJson<FinalRequirement[]>(`/workspaces/${workspaceId}/requirements`);
}

export function listFinalParameters(workspaceId: string): Promise<FinalParameter[]> {
  return getJson<FinalParameter[]>(`/workspaces/${workspaceId}/parameters`);
}

export function listFinalDecisions(workspaceId: string): Promise<FinalDecision[]> {
  return getJson<FinalDecision[]>(`/workspaces/${workspaceId}/decisions`);
}

export function readFinalSystemInfo(): Promise<SystemInfoResponse> {
  return getSystemInfo();
}
