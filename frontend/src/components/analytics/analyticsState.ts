export type AnalyticsRun = Readonly<{
  id: string;
  model_version_id: string | null;
  run_label: string | null;
  status: string;
  output_payload: string | null;
}>;

export type RequestContext = Readonly<{ generation: number; identity: string }>;

export type Observation = Readonly<{ key: string; value: number; unit: string }>;
export type RunProjection = Readonly<{
  runId: string;
  label: string;
  modelVersionId: string | null;
  state: "ok" | "rejected";
  reason: string | null;
  observations: Readonly<Record<string, Observation>>;
  rejectedKeys: Readonly<Record<string, string>>;
}>;
export type ComparisonGroup =
  | Readonly<{ state: "valid"; key: string; unit: string; values: ReadonlyArray<Readonly<{ runId: string; label: string; value: number }>>; min: number; max: number; range: number }>
  | Readonly<{ state: "rejected"; key: string; reason: string }>;
export type ComparisonResult = Readonly<{
  state: "instruction" | "rejected" | "ready";
  message: string | null;
  projections: readonly RunProjection[];
  groups: readonly ComparisonGroup[];
}>;

export const MAX_SELECTED_RUNS = 6;
export const MAX_OUTPUT_KEYS = 128;
export const MAX_OUTPUT_KEY_LENGTH = 160;
export const MAX_UNIT_LENGTH = 64;
export const MAX_OUTPUT_PAYLOAD_BYTES = 1_048_576;

export function acceptsWorkspaceResponse(request: RequestContext, currentGeneration: number, currentWorkspace: string): boolean {
  return request.generation === currentGeneration && request.identity === currentWorkspace;
}

function codePointLength(value: string): number {
  return Array.from(value).length;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function labelFor(run: AnalyticsRun): string {
  const label = run.run_label?.trim();
  return Array.from(label || run.id).slice(0, 160).join("");
}

function rejected(run: AnalyticsRun, reason: string): RunProjection {
  return { runId: run.id, label: labelFor(run), modelVersionId: run.model_version_id, state: "rejected", reason, observations: {}, rejectedKeys: {} };
}

export function projectAnalyticsRun(run: AnalyticsRun): RunProjection {
  if (run.status !== "succeeded") return rejected(run, `Run status is ${run.status}; only succeeded runs provide numeric observations.`);
  if (!run.model_version_id || run.model_version_id.trim().length === 0) return rejected(run, "Model version identity is missing.");
  if (run.output_payload === null) return rejected(run, "Persisted output payload is missing.");
  if (new TextEncoder().encode(run.output_payload).length > MAX_OUTPUT_PAYLOAD_BYTES) return rejected(run, "Persisted output payload exceeds the 1 MiB analytics limit.");

  let parsed: unknown;
  try {
    parsed = JSON.parse(run.output_payload) as unknown;
  } catch {
    return rejected(run, "Persisted output payload is malformed JSON.");
  }
  if (!isRecord(parsed) || parsed.schema_version !== 1 || parsed.status !== "succeeded" || !isRecord(parsed.outputs)) {
    return rejected(run, "Persisted output payload is not a supported succeeded schema-v1 result envelope.");
  }

  const entries = Object.entries(parsed.outputs);
  if (entries.length > MAX_OUTPUT_KEYS) return rejected(run, `Persisted output payload exceeds ${MAX_OUTPUT_KEYS} output keys.`);

  const observations: Record<string, Observation> = {};
  const rejectedKeys: Record<string, string> = {};
  for (const [key, raw] of entries) {
    if (key.trim().length === 0 || codePointLength(key) > MAX_OUTPUT_KEY_LENGTH) return rejected(run, "Persisted output key is empty or exceeds the bounded key length.");
    if (!isRecord(raw)) {
      rejectedKeys[key] = "Output is not a scalar result record.";
      continue;
    }
    const value = raw.value;
    const unit = raw.unit;
    if (typeof value !== "number" || !Number.isFinite(value)) {
      rejectedKeys[key] = "Output value is not a finite numeric value.";
      continue;
    }
    if (typeof unit !== "string" || unit.trim().length === 0 || codePointLength(unit) > MAX_UNIT_LENGTH) {
      rejectedKeys[key] = "Output unit is missing or exceeds the bounded unit length.";
      continue;
    }
    observations[key] = { key, value, unit };
  }

  if (Object.keys(observations).length === 0 && Object.keys(rejectedKeys).length === 0) {
    return rejected(run, "Succeeded run has no trustworthy unit-bearing scalar outputs.");
  }
  return { runId: run.id, label: labelFor(run), modelVersionId: run.model_version_id, state: "ok", reason: null, observations, rejectedKeys };
}

export function retainExistingSelection(selectedIds: readonly string[], runs: readonly AnalyticsRun[]): string[] {
  const present = new Set(runs.map((run) => run.id));
  return selectedIds.filter((id) => present.has(id)).slice(0, MAX_SELECTED_RUNS);
}

export function toggleRunSelection(selectedIds: readonly string[], runId: string): string[] {
  if (selectedIds.includes(runId)) return selectedIds.filter((id) => id !== runId);
  if (selectedIds.length >= MAX_SELECTED_RUNS) return [...selectedIds];
  return [...selectedIds, runId];
}

export function compareAnalyticsRuns(runs: readonly AnalyticsRun[]): ComparisonResult {
  const projections = runs.map(projectAnalyticsRun);
  if (runs.length === 0) return { state: "instruction", message: "Select at least two persisted runs to compare.", projections, groups: [] };
  if (runs.length === 1) return { state: "instruction", message: "Select one more persisted run to compare.", projections, groups: [] };
  if (runs.length > MAX_SELECTED_RUNS) return { state: "rejected", message: `A comparison may include at most ${MAX_SELECTED_RUNS} runs.`, projections, groups: [] };

  const rejectedRuns = projections.filter((projection) => projection.state === "rejected");
  if (rejectedRuns.length > 0) {
    return { state: "rejected", message: rejectedRuns.map((run) => `${run.label}: ${run.reason}`).join(" · "), projections, groups: [] };
  }

  const versions = new Set(projections.map((projection) => projection.modelVersionId));
  if (versions.size !== 1) return { state: "rejected", message: "Direct comparison requires one exact model version across all selected runs.", projections, groups: [] };

  const keys = Array.from(new Set(projections.flatMap((projection) => [...Object.keys(projection.observations), ...Object.keys(projection.rejectedKeys)]))).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  const groups: ComparisonGroup[] = keys.map((key) => {
    const invalid = projections.find((projection) => projection.rejectedKeys[key]);
    if (invalid) return { state: "rejected", key, reason: `${invalid.label}: ${invalid.rejectedKeys[key]}` };
    const missing = projections.find((projection) => !projection.observations[key]);
    if (missing) return { state: "rejected", key, reason: `${missing.label}: metric is missing from the selected run.` };
    const observations = projections.map((projection) => projection.observations[key]);
    const units = new Set(observations.map((observation) => observation.unit));
    if (units.size !== 1) return { state: "rejected", key, reason: `Exact units are incompatible: ${Array.from(units).join(" vs ")}. No conversion was applied.` };
    const values = observations.map((observation, index) => ({ runId: projections[index].runId, label: projections[index].label, value: observation.value }));
    const numeric = values.map((item) => item.value);
    const min = Math.min(...numeric);
    const max = Math.max(...numeric);
    return { state: "valid", key, unit: observations[0].unit, values, min, max, range: max - min };
  });

  if (groups.length === 0) return { state: "rejected", message: "Selected runs contain no trustworthy comparable observations.", projections, groups: [] };
  return { state: "ready", message: null, projections, groups };
}
