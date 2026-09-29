import { API_BASE_URL } from "./client";

// Spec 155: Jarvis-owned process draft. Quantities travel as value + unit; the server converts.
export type DraftQuantity = { value: number; unit: string };
export type StoredQuantity = DraftQuantity & { si: number };
export type Endpoint = { unit: string; port: number };
export type DraftObject = {
  id: string;
  kind: "unit" | "stream";
  type: string;
  tag: string;
  x: number;
  y: number;
  mode?: string | null;
  params?: Record<string, StoredQuantity>;
  source?: Endpoint | null;
  target?: Endpoint | null;
  spec?: {
    temperature?: StoredQuantity;
    pressure?: StoredQuantity;
    mass_flow?: StoredQuantity;
    composition?: Record<string, number>;
  };
};
export type Finding = {
  severity: "blocker" | "warning" | string;
  code: string;
  object: string;
  field?: string;
  message: string;
  fix?: string;
  source: "jarvis" | "dwsim";
};
export type ProposalChange = {
  target: string;
  target_id: string;
  kind: "unit" | "stream";
  property: string;
  current: DraftQuantity | string | Record<string, number> | null;
  proposed: DraftQuantity | string | Record<string, number>;
};
export type Proposal = {
  proposal_id: string;
  draft_id: string;
  base_revision: string;
  status: "pending" | "approved" | "rejected";
  state: "pending" | "stale" | "approved" | "rejected";
  changes: ProposalChange[];
  rationale: string;
  source: string;
  created_at: string;
  applied_revision: string | null;
};
export type ResultsState = {
  state: "none" | "current" | "stale";
  run_id?: string;
  draft_revision?: string;
  edits_since?: number;
  materialization_fingerprint?: string;
  last_attempt: { run_id: string; action: string; status: string; draft_revision: string; started_at: string } | null;
};
export type DraftProjection = {
  workspace_id: string;
  draft_id: string;
  name: string;
  revision: string;
  seq: number;
  compounds: string[];
  property_package: string | null;
  objects: DraftObject[];
  findings: Finding[];
  results: ResultsState;
  proposals: Proposal[];
};
export type RegistryParam = { key: string; label: string; kind: string; modes: string[]; default: number | null };
export type RegistryUnit = {
  type: string;
  label: string;
  inlets: string[];
  outlets: string[];
  required_inlets: number;
  modes: string[];
  params: RegistryParam[];
};
export type DraftRegistry = {
  compiler_version: string;
  compounds: string[];
  property_packages: string[];
  quantity_units: Record<string, { si: string; display: string[] }>;
  stream_specs: { key: string; label: string; kind: string }[];
  units: RegistryUnit[];
  unsupported: Record<string, string>;
};
export type StreamResult = {
  temperature_K: number | null;
  pressure_Pa: number | null;
  mass_flow_kg_s: number | null;
  vapor_fraction: number | null;
  mass_fractions: Record<string, number>;
  display?: Record<string, DraftQuantity>;
};
export type MaterializationDiff = { path: string; expected: unknown; actual: unknown };
export type DraftRun = {
  run_id: string;
  action: "validate" | "run";
  status: string;
  draft_revision: string;
  compiler_version: string;
  dwsim_version: string;
  mcp_sha256: string;
  started_at: string;
  finished_at?: string;
  expected_fingerprint?: string;
  materialization_fingerprint?: string;
  materialization_diffs?: MaterializationDiff[];
  dwsim_check?: { ready: boolean; findings: Finding[] };
  solve?: { ok: boolean; errors: unknown[]; failed_objects: { tag: string; error: string }[] };
  streams?: Record<string, StreamResult>;
  units?: Record<string, { calculated: boolean; error: string; reported: Record<string, { value: string; units: string }> }>;
  mass_balance?: { status: string; residual_kg_s?: number; boundary_kg_s?: Record<string, number>; error?: string };
  compile_seconds?: number;
  error?: string;
  error_detail?: Record<string, unknown>;
};
export type DraftSummary = { draft_id: string; name: string; revision: string; updated_at: string };
export type RevisionSummary = {
  seq: number;
  revision: string;
  parent_revision: string | null;
  actor: string;
  created_at: string;
  ops: string[];
};
export type DraftOp = Record<string, unknown> & { op: string };

export class DraftApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly detail: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "DraftApiError";
  }
}

const base = (workspaceId: string) => `/workspaces/${encodeURIComponent(workspaceId)}/process/drafts`;
const draftPath = (workspaceId: string, draftId: string) => `${base(workspaceId)}/${encodeURIComponent(draftId)}`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
  });
  if (!response.ok) {
    let detail: Record<string, unknown> = { code: `http_${response.status}`, message: `Request failed (${response.status})` };
    try {
      const body = (await response.json()) as { detail?: Record<string, unknown> };
      if (body.detail && typeof body.detail === "object") detail = body.detail;
    } catch {
      /* Keep the status-based message when the server has no JSON body. */
    }
    throw new DraftApiError(response.status, String(detail.code), String(detail.message), detail);
  }
  return response.json() as Promise<T>;
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const getDraftRegistry = (workspaceId: string) => request<DraftRegistry>(`${base(workspaceId)}/registry`);
export const listDrafts = (workspaceId: string) => request<DraftSummary[]>(base(workspaceId));
export const createDraft = (workspaceId: string, name: string) => post<DraftProjection>(base(workspaceId), { name });
export const getDraft = (workspaceId: string, draftId: string) => request<DraftProjection>(draftPath(workspaceId, draftId));
export const patchDraft = (workspaceId: string, draftId: string, expectedRevision: string, ops: DraftOp[]) =>
  post<DraftProjection>(`${draftPath(workspaceId, draftId)}/patch`, { expected_revision: expectedRevision, ops });
export const listDraftRevisions = (workspaceId: string, draftId: string) =>
  request<RevisionSummary[]>(`${draftPath(workspaceId, draftId)}/revisions`);
export const restoreDraftRevision = (workspaceId: string, draftId: string, expectedRevision: string, sourceRevision: string) =>
  post<DraftProjection>(`${draftPath(workspaceId, draftId)}/restore`, {
    expected_revision: expectedRevision,
    source_revision: sourceRevision,
  });
export const executeDraft = (workspaceId: string, draftId: string, revision: string, action: "validate" | "run") =>
  post<{ run: DraftRun; draft: DraftProjection }>(
    `${draftPath(workspaceId, draftId)}/revisions/${encodeURIComponent(revision)}/${action}`,
  );
export const getDraftRun = (workspaceId: string, draftId: string, runId: string) =>
  request<DraftRun>(`${draftPath(workspaceId, draftId)}/runs/${encodeURIComponent(runId)}`);
export const listProposals = (workspaceId: string, draftId: string) =>
  request<Proposal[]>(`${draftPath(workspaceId, draftId)}/proposals`);
export const approveProposal = (workspaceId: string, draftId: string, proposalId: string, acceptedChanges?: number[]) =>
  post<{ proposal: Proposal; draft: DraftProjection | null }>(
    `${draftPath(workspaceId, draftId)}/proposals/${encodeURIComponent(proposalId)}/approve`,
    { accepted_changes: acceptedChanges ?? null },
  );
export const rejectProposal = (workspaceId: string, draftId: string, proposalId: string) =>
  post<{ proposal: Proposal; draft: DraftProjection | null }>(
    `${draftPath(workspaceId, draftId)}/proposals/${encodeURIComponent(proposalId)}/reject`,
  );

// Draft changes made outside the Process page (Sidecar approvals) announce themselves here.
export const DRAFT_CHANGED_EVENT = "jarvis:process-draft-changed";
export const announceDraftChanged = (draftId: string) =>
  window.dispatchEvent(new CustomEvent(DRAFT_CHANGED_EVENT, { detail: { draftId } }));

export const formatQuantity = (value: unknown): string => {
  if (value == null) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "object" && "value" in (value as object) && "unit" in (value as object)) {
    const quantity = value as DraftQuantity;
    return `${quantity.value} ${unitLabel(quantity.unit)}`;
  }
  return Object.entries(value as Record<string, number>)
    .map(([name, fraction]) => `${name} ${fraction}`)
    .join(", ");
};

export const unitLabel = (unit: string) =>
  ({ degC: "°C", percent: "%", "kg/h": "kg/h", "kg/s": "kg/s", "t/h": "t/h" })[unit] ?? unit;
