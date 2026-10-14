import { API_BASE_URL } from "./client";

export type StudioVariable = { name: string; label: string; unit: string; description: string; min?: number | null; max?: number | null };
export type StudioCase = { inputs: Record<string, number>; expected_outputs?: Record<string, number>; tolerance?: number };
export type StudioReport = { source_sha256: string; contract_sha256: string; passed: boolean; cases: { passed: boolean; classification: string; outputs?: Record<string, unknown> | null; errors: string[]; codes?: string[]; culture_generation?: Record<string, number> | null }[] };
// Spec 190: process-unit contract and test-case shapes (backend studio/unit_models.py).
export type StudioPort = { name: string; label: string };
export const CULTURE_FIELDS = ["biomass", "nitrogen", "phosphorus", "oxygen", "dic", "salinity"] as const;
export type StudioUnitStream = { mass_flow_kg_s: number; temperature_K: number; pressure_Pa: number; mass_fractions: Record<string, number>; culture: Record<string, number | null> };
export type StudioExpectedStream = { mass_flow_kg_s?: number | null; temperature_K?: number | null; pressure_Pa?: number | null; mass_fractions?: Record<string, number> | null };
export type StudioUnitCase = { inlets: Record<string, StudioUnitStream>; params: Record<string, number>; expected_outlets?: Record<string, StudioExpectedStream> | null; tolerance?: number };
export type StudioUnitContract = { inlets: StudioPort[]; outlets: StudioPort[]; parameters: StudioVariable[]; symbol: string | null; culture_generation: string[] };
export type StudioUnitCreate = StudioUnitContract & { category: "process_unit"; name: string; engineering_question: string };
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
  id: string; workspace_id: string; name: string; engineering_question: string; category: "calculation" | "process_unit"; status: string;
  // A calculation declares inputs/outputs; a process unit (spec 190) declares ports and parameters instead.
  inputs: StudioVariable[]; outputs: StudioVariable[]; source: string;
  inlets?: StudioPort[]; outlets?: StudioPort[]; parameters?: StudioVariable[]; symbol?: string | null; culture_generation?: string[]; source_sha256: string; contract_sha256: string;
  annotations: string; assumptions: string; annotations_stale: boolean; test_cases: StudioCase[] | StudioUnitCase[];
  documentation: { derived: StudioDerived; inputs: StudioVariable[]; outputs: StudioVariable[] } & Partial<StudioUnitContract>;
  last_test_report?: StudioReport | null; versions: StudioVersion[]; created_at: string; updated_at: string;
};
export type StudioCategory = { id: string; label: string; available: boolean; reason?: string | null };
export type StudioLibraryEntry = { category?: "calculation" | "process_unit"; id: string; model_spec_id: string; name: string; version_label: string; source_sha256: string; contract_sha256: string; created_at: string; scientific_status: "unqualified" };
export type StudioRuntimeStatus = { enabled: boolean; available: boolean; mechanism: string; reason?: string | null };

/** Carries the backend's typed code, for example studio_symbol_invalid. */
export class StudioApiError extends Error {
  constructor(message: string, readonly code: string | null) { super(message); this.name = "StudioApiError"; }
}
async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { method, headers: body === undefined ? undefined : { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
  if (!response.ok) {
    const data = await response.json().catch(() => null) as { detail?: { message?: string; code?: string } | { loc?: unknown[]; msg?: string }[] | string } | null;
    const list = Array.isArray(data?.detail) ? data.detail.map((item) => `${(item.loc ?? []).slice(1).join(".")}: ${item.msg ?? "invalid"}`).join("; ") : undefined;
    const detail = typeof data?.detail === "string" ? data.detail : list ?? (data?.detail as { message?: string } | undefined)?.message;
    throw new StudioApiError(detail ?? `Request failed with ${response.status}`, data?.detail && !Array.isArray(data.detail) && typeof data.detail === "object" ? (data.detail as { code?: string }).code ?? null : null);
  }
  return response.json() as Promise<T>;
}
const root = (workspaceId: string) => `/workspaces/${encodeURIComponent(workspaceId)}/studio`;
const model = (workspaceId: string, id: string) => `${root(workspaceId)}/models/${encodeURIComponent(id)}`;
export const listStudioCategories = () => request<StudioCategory[]>("/studio/categories");
export const getStudioRuntimeStatus = () => request<StudioRuntimeStatus>("/studio/runtime/status");
export const listStudioModels = (workspaceId: string) => request<StudioModel[]>(`${root(workspaceId)}/models`);
export const getStudioModel = (workspaceId: string, id: string) => request<StudioModel>(model(workspaceId, id));
export const createStudioModel = (workspaceId: string, payload: Pick<StudioModel, "name" | "engineering_question" | "inputs" | "outputs"> | StudioUnitCreate) => request<StudioModel>(`${root(workspaceId)}/models`, "POST", payload);
export const saveStudioModel = (workspaceId: string, id: string, payload: Partial<Pick<StudioModel, "name" | "engineering_question" | "inputs" | "outputs" | "source" | "annotations" | "assumptions">> | Partial<StudioUnitContract & Pick<StudioModel, "name" | "engineering_question" | "source" | "annotations" | "assumptions">>) => request<StudioModel>(model(workspaceId, id), "PUT", payload);
export const testStudioModel = (workspaceId: string, id: string, cases: StudioCase[] | StudioUnitCase[]) => request<StudioReport>(`${model(workspaceId, id)}/test`, "POST", { cases });
export const publishStudioModel = (workspaceId: string, id: string) => request<StudioVersion>(`${model(workspaceId, id)}/publish`, "POST", {});
export const reviseStudioModel = (workspaceId: string, id: string) => request<StudioModel>(`${model(workspaceId, id)}/revise`, "POST", {});
export const listStudioLibrary = (workspaceId: string) => request<StudioLibraryEntry[]>(`${root(workspaceId)}/library`);
