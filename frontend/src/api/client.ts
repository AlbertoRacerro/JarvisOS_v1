const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type HealthResponse = {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  data_root: string;
};

export type SystemInfoResponse = {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  data_root: string;
  data_root_exists: boolean;
  paths: Record<string, string>;
  database: {
    engine: string;
    database_file: string;
    configured: boolean;
    ready: boolean;
    initialized: boolean;
  };
  ai: {
    provider: string;
    gateway_configured: boolean;
    provider_configured: boolean;
    provider_calls_enabled: boolean;
    provider_mode: string;
    monthly_budget_usd: number;
    spend_month_to_date_usd: number;
    scaleway_enabled: boolean;
    scaleway_api_key_configured: boolean;
    scaleway_provider_implementation: string;
    scaleway_smoke_test_enabled: boolean;
    scaleway_live_smoke_test_enabled: boolean;
    scaleway_monthly_token_cap: number;
    scaleway_hard_stop_token_cap: number;
    scaleway_free_tier_reference_tokens: number;
    scaleway_input_tokens_month_to_date: number;
    scaleway_output_tokens_month_to_date: number;
    blocking_reason?: string | null;
  };
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function postJson<T>(path: string, payload: Record<string, unknown> = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function putJson<T>(path: string, payload: Record<string, unknown>): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function deleteJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/health");
}

export function getSystemInfo(): Promise<SystemInfoResponse> {
  return getJson<SystemInfoResponse>("/system/info");
}

export type Workspace = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ModelSpec = {
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

export type Assumption = {
  id: string;
  workspace_id: string;
  statement: string;
  confidence?: number | null;
  status: string;
};

export type Parameter = {
  id: string;
  workspace_id: string;
  name: string;
  symbol?: string | null;
  value?: string | null;
  unit?: string | null;
  status: string;
};

export type SimulationRun = {
  id: string;
  workspace_id: string;
  run_label?: string | null;
  status: string;
  created_at: string;
};

export type Decision = {
  id: string;
  workspace_id: string;
  title: string;
  decision_text: string;
  status: string;
};

export function initializeSystem(): Promise<unknown> {
  return postJson<unknown>("/system/initialize");
}

export function listWorkspaces(): Promise<Workspace[]> {
  return getJson<Workspace[]>("/workspaces");
}

export function createWorkspace(payload: Record<string, unknown>): Promise<Workspace> {
  return postJson<Workspace>("/workspaces", payload);
}

export function listModelSpecs(workspaceId: string): Promise<ModelSpec[]> {
  return getJson<ModelSpec[]>(`/workspaces/${workspaceId}/model-specs`);
}

export function createModelSpec(workspaceId: string, payload: Record<string, unknown>): Promise<ModelSpec> {
  return postJson<ModelSpec>(`/workspaces/${workspaceId}/model-specs`, payload);
}

export function listAssumptions(workspaceId: string): Promise<Assumption[]> {
  return getJson<Assumption[]>(`/workspaces/${workspaceId}/assumptions`);
}

export function createAssumption(workspaceId: string, payload: Record<string, unknown>): Promise<Assumption> {
  return postJson<Assumption>(`/workspaces/${workspaceId}/assumptions`, payload);
}

export function listParameters(workspaceId: string): Promise<Parameter[]> {
  return getJson<Parameter[]>(`/workspaces/${workspaceId}/parameters`);
}

export function createParameter(workspaceId: string, payload: Record<string, unknown>): Promise<Parameter> {
  return postJson<Parameter>(`/workspaces/${workspaceId}/parameters`, payload);
}

export function listSimulationRuns(workspaceId: string): Promise<SimulationRun[]> {
  return getJson<SimulationRun[]>(`/workspaces/${workspaceId}/simulation-runs`);
}

export function createSimulationRun(workspaceId: string, payload: Record<string, unknown>): Promise<SimulationRun> {
  return postJson<SimulationRun>(`/workspaces/${workspaceId}/simulation-runs`, payload);
}

export function listDecisions(workspaceId: string): Promise<Decision[]> {
  return getJson<Decision[]>(`/workspaces/${workspaceId}/decisions`);
}

export function createDecision(workspaceId: string, payload: Record<string, unknown>): Promise<Decision> {
  return postJson<Decision>(`/workspaces/${workspaceId}/decisions`, payload);
}

export type AISettings = {
  policy_mode: string;
  monthly_api_budget_usd: number;
  api_spend_month_to_date_usd: number;
  paid_ai_enabled: boolean;
  default_ai_provider: string;
  default_ai_model: string;
  provider_mode: string;
  use_fake_provider_when_budget_zero: boolean;
  scaleway_enabled: boolean;
  scaleway_smoke_test_enabled: boolean;
  scaleway_live_smoke_test_enabled: boolean;
  scaleway_monthly_token_cap: number;
  scaleway_hard_stop_token_cap: number;
  scaleway_free_tier_reference_tokens: number;
  scaleway_input_tokens_month_to_date: number;
  scaleway_output_tokens_month_to_date: number;
  usage_total_tokens: number;
  smoke_test_mode_enabled: boolean;
  updated_at: string;
};

export type AIStatus = {
  policy_mode: string;
  ai_enabled: boolean;
  active_provider_mode: string;
  provider_mode: string;
  provider_id: string;
  adapter_enabled: boolean;
  fake_provider_enabled: boolean;
  scaleway_enabled: boolean;
  scaleway_api_key_configured: boolean;
  scaleway_provider_implementation: string;
  paid_ai_enabled: boolean;
  monthly_api_budget_usd: number;
  spend_month_to_date_usd: number;
  scaleway_smoke_test_enabled: boolean;
  scaleway_live_smoke_test_enabled: boolean;
  scaleway_monthly_token_cap: number;
  scaleway_hard_stop_token_cap: number;
  scaleway_free_tier_reference_tokens: number;
  scaleway_input_tokens_month_to_date: number;
  scaleway_output_tokens_month_to_date: number;
  usage_total_tokens: number;
  budget_status: string;
  credential_status: string;
  external_calls_allowed: boolean;
  blocking_reason?: string | null;
  default_ai_provider: string;
  default_ai_model: string;
};

export type ModelingDraftResponse = {
  draft: {
    engineering_question: string;
    model_title_suggestion: string;
    model_scope: string;
    proposed_assumptions: string[];
    proposed_parameters: string[];
    expected_inputs: string[];
    expected_outputs: string[];
    missing_information: string[];
    model_weaknesses: string[];
    suggested_next_step: string;
  } | null;
  ai_metadata: {
    provider: string;
    model: string;
    provider_mode: string;
    task_type: string;
    quality_level: string;
    paid_api_call_attempted: boolean;
    blocked_by_budget: boolean;
    blocked_reason?: string | null;
    estimated_cost_usd?: number | null;
    monthly_budget_usd: number;
    spend_month_to_date_usd: number;
    success: boolean;
  };
};

export function getAISettings(): Promise<AISettings> {
  return getJson<AISettings>("/ai/settings");
}

export function updateAISettings(payload: Record<string, unknown>): Promise<AISettings> {
  return putJson<AISettings>("/ai/settings", payload);
}

export function getAIStatus(): Promise<AIStatus> {
  return getJson<AIStatus>("/ai/status");
}

export type ScalewaySecretStatus = {
  key_present: boolean;
  source: string;
  masked_preview?: string | null;
  last_updated_at?: string | null;
  storage_mode: string;
};

export function getScalewaySecretStatus(): Promise<ScalewaySecretStatus> {
  return getJson<ScalewaySecretStatus>("/secrets/scaleway/status");
}

export function setScalewayApiKey(apiKey: string): Promise<ScalewaySecretStatus> {
  return postJson<ScalewaySecretStatus>("/secrets/scaleway/api-key", { api_key: apiKey });
}

export function deleteScalewayApiKey(): Promise<ScalewaySecretStatus> {
  return deleteJson<ScalewaySecretStatus>("/secrets/scaleway/api-key");
}

export function createModelingDraft(payload: Record<string, unknown>): Promise<ModelingDraftResponse> {
  return postJson<ModelingDraftResponse>("/ai/modeling/draft", payload);
}

export type AITaskRunRequest = {
  prompt: string;
  route_class?: string;
  task_kind?: string;
  max_tokens?: number;
  context_blocks?: unknown[];
};

export type AIUsage = {
  provider_id: string;
  model_id: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens?: number | null;
  usage_source: string;
  provider_cost_estimate?: number | null;
  currency?: string | null;
};

export type AITaskRunResponse = {
  status: string;
  ledger_id: string;
  selected_route_class?: string | null;
  decision_reason: string;
  blocked_reason?: string | null;
  response_text?: string | null;
  provider_id?: string | null;
  model_id?: string | null;
  usage?: AIUsage | null;
  error_type?: string | null;
};

export function runAITask(payload: AITaskRunRequest): Promise<AITaskRunResponse> {
  return postJson<AITaskRunResponse>("/ai/tasks/run", payload as Record<string, unknown>);
}

export type SmokeTestTokenMetadata = {
  blocked_by_token_cap: boolean;
  estimated_input_tokens: number;
  estimated_output_tokens: number;
  reported_input_tokens?: number | null;
  reported_output_tokens?: number | null;
  monthly_token_cap: number;
  hard_stop_token_cap: number;
  token_usage_month_to_date: number;
  usage_source: string;
};

export type SmokeTestResult = {
  case_id: string;
  input_excerpt: string;
  expected_class: string;
  local_privacy_class: string;
  provider_reported_class?: string | null;
  fake_classification?: string | null;
  passed: boolean;
  provider_mode: string;
  provider: string;
  smoke_mode: string;
  external_call_attempted: boolean;
  external_call_succeeded: boolean;
  blocking_reason?: string | null;
  response_text?: string | null;
  usage_source: string;
  provider_metadata?: Record<string, unknown> | null;
  token_metadata: SmokeTestTokenMetadata;
};

export type SmokeTestResponse = {
  provider_mode: string;
  smoke_mode: string;
  external_call_attempted: boolean;
  external_call_succeeded: boolean;
  results: SmokeTestResult[];
};

export function runAISmokeTests(payload: Record<string, unknown>): Promise<SmokeTestResponse> {
  return postJson<SmokeTestResponse>("/ai/smoke-tests/run", payload);
}

export type SmokeConsoleResponse = {
  response_text?: string | null;
  provider: string;
  model: string;
  mode: string;
  privacy_class: string;
  blocked_reason?: string | null;
  external_call_attempted: boolean;
  external_call_succeeded: boolean;
  estimated_input_tokens: number;
  estimated_output_tokens: number;
  actual_input_tokens?: number | null;
  actual_output_tokens?: number | null;
  usage_source: string;
  current_month_input_tokens: number;
  current_month_output_tokens: number;
  current_month_total_tokens: number;
  configured_monthly_token_cap: number;
  token_threshold: number;
  token_threshold_percent: number;
  remaining_tokens_to_threshold: number;
};

export function runAISmokeConsole(payload: Record<string, unknown>): Promise<SmokeConsoleResponse> {
  return postJson<SmokeConsoleResponse>("/ai/smoke-console/run", payload);
}
