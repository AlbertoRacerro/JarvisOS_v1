import { API_BASE_URL } from "./client";

export type StudioVariable = { name: string; label: string; unit: string; description: string; min?: number | null; max?: number | null };
export type StudioCase = { inputs: Record<string, number>; expected_outputs?: Record<string, number>; tolerance?: number };
export type StudioReport = { source_sha256: string; contract_sha256: string; passed: boolean; cases: { passed: boolean; classification: string; outputs?: Record<string, unknown>; errors: string[] }[] };
export type StudioMathNode = { tag: string; text?: string; children?: StudioMathNode[] };
export type StudioStep =
  | { kind: "equation"; target: StudioMathNode; expr: StudioMathNode; line: number }
  | { kind: "code"; text: string; reason: string; line: number }
  | { kind: "conditional"; form: "piecewise"; target: StudioMathNode; cases: { condition: StudioMathNode | null; expr: StudioMathNode }[]; line: number }
  | { kind: "conditional"; form: "branches"; branches: { label: string; condition: StudioMathNode | null; steps: StudioStep[] }[]; line: number };
export type StudioDerived = {
  source_sha256: string; status: "ok" | "syntax_error" | "entry_missing"; unrendered_count: number;
  functions: { name: string; args: string[]; docstring: string | null; steps: StudioStep[] }[];
  module_constants: StudioStep[]; error?: { message: string; line: number | null };
};
export type StudioVersion = { id: string; version_label: string; source_sha256: string; contract_sha256: string; created_at: string };
export type StudioModel = {
  id: string; workspace_id: string; name: string; engineering_question: string; category: "calculation"; status: string;
  inputs: StudioVariable[]; outputs: StudioVariable[]; source: string; source_sha256: string; contract_sha256: string;
  annotations: string; assumptions: string; annotations_stale: boolean; test_cases: StudioCase[];
  documentation: { derived: StudioDerived; inputs: StudioVariable[]; outputs: StudioVariable[] };
  last_test_report?: StudioReport | null; versions: StudioVersion[]; created_at: string; updated_at: string;
};
export type StudioCategory = { id: string; label: string; available: boolean; reason?: string | null };
export type StudioLibraryEntry = { id: string; model_spec_id: string; name: string; version_label: string; source_sha256: string; contract_sha256: string; created_at: string; scientific_status: "unqualified" };
export type StudioRuntimeStatus = { enabled: boolean; available: boolean; mechanism: string; reason?: string | null };

async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { method, headers: body === undefined ? undefined : { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
  if (!response.ok) {
    const data = await response.json().catch(() => null) as { detail?: { message?: string } | string } | null;
    const detail = typeof data?.detail === "string" ? data.detail : data?.detail?.message;
    throw new Error(detail ?? `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}
const root = (workspaceId: string) => `/workspaces/${encodeURIComponent(workspaceId)}/studio`;
const model = (workspaceId: string, id: string) => `${root(workspaceId)}/models/${encodeURIComponent(id)}`;
export const listStudioCategories = () => request<StudioCategory[]>("/studio/categories");
export const getStudioRuntimeStatus = () => request<StudioRuntimeStatus>("/studio/runtime/status");
export const listStudioModels = (workspaceId: string) => request<StudioModel[]>(`${root(workspaceId)}/models`);
export const getStudioModel = (workspaceId: string, id: string) => request<StudioModel>(model(workspaceId, id));
export const createStudioModel = (workspaceId: string, payload: Pick<StudioModel, "name" | "engineering_question" | "inputs" | "outputs">) => request<StudioModel>(`${root(workspaceId)}/models`, "POST", payload);
export const saveStudioModel = (workspaceId: string, id: string, payload: Partial<Pick<StudioModel, "name" | "engineering_question" | "inputs" | "outputs" | "source" | "annotations" | "assumptions">>) => request<StudioModel>(model(workspaceId, id), "PATCH", payload);
export const testStudioModel = (workspaceId: string, id: string, cases: StudioCase[]) => request<StudioReport>(`${model(workspaceId, id)}/test`, "POST", { cases });
export const publishStudioModel = (workspaceId: string, id: string) => request<StudioVersion>(`${model(workspaceId, id)}/publish`, "POST", {});
export const reviseStudioModel = (workspaceId: string, id: string) => request<StudioModel>(`${model(workspaceId, id)}/revise`, "POST", {});
export const listStudioLibrary = (workspaceId: string) => request<StudioLibraryEntry[]>(`${root(workspaceId)}/library`);
