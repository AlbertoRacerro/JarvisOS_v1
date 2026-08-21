import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import type { Navigate } from "../../app/AppLink";
import type { StageSelection } from "../../app/selection";
import {
  createRunnerJob,
  getBluecadCandidateAggregate,
  listModelImplementations,
  listParameters,
  listWorkspaces,
  previewModelBindings,
  runRunnerJob,
  type BindingPreviewResponse,
  type ModelImplementation,
  type ModelInputVariable,
  type Parameter,
  type RunnerJobRunResponse
} from "../../api/client";
import InlineNotice from "../ui/InlineNotice";

type WorkingBinding = Readonly<{ value: string; parameterId: string }>;
type BindingMap = Record<string, WorkingBinding>;
type PreviewPhase = "idle" | "checking" | "ready" | "unavailable" | "local-invalid";
type SemanticPhase = "none" | "loading" | "limited" | "ready" | "conflict";
type RunSnapshot = Readonly<{
  requestKey: string;
  revision: number;
  bindings: BindingMap;
  payload: Record<string, unknown>;
}>;

type BluecadPartSelection = Extract<StageSelection, { kind: "bluecad-part" }>;
type SemanticVariable = ModelInputVariable & Readonly<{
  physical_dimension?: string;
  semantic_basis?: string;
  property_group?: string;
  applicable_part_kinds?: string[];
}>;
type SemanticContract = Readonly<{
  schema_version: 3;
  semantic_context: Readonly<{
    applicable_part_kinds: string[];
    model_family_key: string;
    model_family_label: string;
    model_option_label: string;
  }>;
  variables: SemanticVariable[];
}>;
type SemanticGeometryBinding = Readonly<{ value: number; unit: "m" | "mm"; source_parameter_id: string }>;
type SemanticSource = Readonly<{
  schema_version: 1;
  kind: "cad_link_047_m0";
  transformation_version: "bluerev_047_m0_tube_proxy_v0_1";
  source_simulation_run_id: string;
  source_model_version_id: string;
  geometry_bindings: Readonly<Record<"tube_length" | "tube_inner_diameter" | "tube_outer_diameter", SemanticGeometryBinding>>;
}>;

export type EngineeringPropertiesController = Readonly<{
  workspaceId: string | null;
  implementations: ModelImplementation[];
  selected: ModelImplementation | null;
  selectedId: string;
  setSelectedId(value: string): void;
  parameters: Parameter[];
  baseline: BindingMap;
  working: BindingMap;
  preview: BindingPreviewResponse | null;
  previewPhase: PreviewPhase;
  previewMessage: string | null;
  revision: number;
  dirtyNames: ReadonlySet<string>;
  undoAvailable: boolean;
  runLabel: string;
  setRunLabel(value: string): void;
  runBusy: boolean;
  runMessage: string | null;
  runResult: RunnerJobRunResponse | null;
  pendingRun: RunSnapshot | null;
  semanticTarget: BluecadPartSelection | null;
  semanticPhase: SemanticPhase;
  semanticMessage: string | null;
  semanticSource: SemanticSource | null;
  semanticContract: SemanticContract | null;
  updateValue(variable: ModelInputVariable, value: string): void;
  selectParameter(variable: ModelInputVariable, parameterId: string): void;
  undo(): void;
  revertField(name: string): void;
  revertAll(): void;
  discardPreviousObjectChanges(): void;
  startRun(): void;
  retryRunStart(): void;
}>;

const EMPTY_BINDING: WorkingBinding = { value: "", parameterId: "" };
const MAX_UNDO = 20;
const REVIEWED_PART_ID = "illuminated_tube_proxy";
const REVIEWED_PART_KIND = "tube_run";
const REVIEWED_FAMILY_KEY = "geometry_hydraulics";
const REVIEWED_OPTION_LABEL = "Reviewed 047 tubular-loop V0";
const GEOMETRY_NAMES = ["tube_length", "tube_inner_diameter", "tube_outer_diameter"] as const;
const CATEGORY_LABELS: Record<ModelInputVariable["category"], string> = {
  design: "Design",
  operating: "Operating",
  property: "Properties",
  model_parameter: "Model parameters",
  equipment: "Equipment"
};

function cloneBindings(bindings: BindingMap): BindingMap {
  return Object.fromEntries(Object.entries(bindings).map(([name, item]) => [name, { ...item }]));
}

function emptyBindings(variables: ModelInputVariable[]): BindingMap {
  return Object.fromEntries(variables.map((variable) => [variable.name, { ...EMPTY_BINDING }]));
}

function sameBinding(left: WorkingBinding | undefined, right: WorkingBinding | undefined): boolean {
  return (left?.value ?? "") === (right?.value ?? "") && (left?.parameterId ?? "") === (right?.parameterId ?? "");
}

function buildPayload(variables: ModelInputVariable[], bindings: BindingMap): {
  payload: Record<string, Record<string, unknown>>;
  invalidNames: string[];
} {
  const invalidNames: string[] = [];
  const entries = variables.flatMap((variable) => {
    const binding = bindings[variable.name] ?? EMPTY_BINDING;
    const value = binding.value.trim();
    if (!value) return [];
    const number = Number(value);
    if (!Number.isFinite(number)) {
      invalidNames.push(variable.name);
      return [];
    }
    const item: Record<string, unknown> = { value: number, unit: variable.unit };
    if (binding.parameterId) item.source_parameter_id = binding.parameterId;
    return [[variable.name, item] as const];
  });
  return { payload: Object.fromEntries(entries), invalidNames };
}

function newRequestKey(): string {
  if (!globalThis.crypto?.randomUUID) throw new Error("Secure run request identity is unavailable in this browser.");
  return globalThis.crypto.randomUUID();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, expected: readonly string[]): boolean {
  const keys = Object.keys(value).sort();
  return keys.length === expected.length && expected.slice().sort().every((item, index) => item === keys[index]);
}

function semanticContractOf(implementation: ModelImplementation | null): SemanticContract | null {
  if (!implementation?.input_contract) return null;
  const raw = implementation.input_contract as unknown;
  if (!isRecord(raw) || raw.schema_version !== 3 || !isRecord(raw.semantic_context) || !Array.isArray(raw.variables)) return null;
  const context = raw.semantic_context;
  if (
    !Array.isArray(context.applicable_part_kinds) ||
    !context.applicable_part_kinds.every((item) => typeof item === "string") ||
    typeof context.model_family_key !== "string" ||
    typeof context.model_family_label !== "string" ||
    typeof context.model_option_label !== "string"
  ) return null;

  const variables: SemanticVariable[] = [];
  for (const item of raw.variables) {
    if (!isRecord(item) || typeof item.name !== "string") return null;
    if (typeof item.property_group !== "string" || !Array.isArray(item.applicable_part_kinds)) return null;
    if (!item.applicable_part_kinds.every((kind) => typeof kind === "string")) return null;
    variables.push(item as unknown as SemanticVariable);
  }
  return {
    schema_version: 3,
    semantic_context: {
      applicable_part_kinds: context.applicable_part_kinds as string[],
      model_family_key: context.model_family_key,
      model_family_label: context.model_family_label,
      model_option_label: context.model_option_label
    },
    variables
  };
}

function reviewedContractForTarget(implementation: ModelImplementation | null, target: BluecadPartSelection | null): SemanticContract | null {
  const contract = semanticContractOf(implementation);
  if (!contract || !target || target.partId !== REVIEWED_PART_ID || target.partKind !== REVIEWED_PART_KIND) return null;
  if (
    contract.semantic_context.model_family_key !== REVIEWED_FAMILY_KEY ||
    contract.semantic_context.model_option_label !== REVIEWED_OPTION_LABEL ||
    !contract.semantic_context.applicable_part_kinds.includes(REVIEWED_PART_KIND)
  ) return null;
  const objectNames = contract.variables
    .filter((variable) => variable.applicable_part_kinds?.includes(REVIEWED_PART_KIND))
    .map((variable) => variable.name)
    .sort();
  const expected = [...GEOMETRY_NAMES].sort();
  if (objectNames.length !== expected.length || !expected.every((name, index) => name === objectNames[index])) return null;
  return contract;
}

function parseSemanticBinding(value: unknown, expectedUnit: "m" | "mm"): SemanticGeometryBinding | null {
  if (!isRecord(value) || !exactKeys(value, ["value", "unit", "source_parameter_id"])) return null;
  if (
    typeof value.value !== "number" ||
    !Number.isFinite(value.value) ||
    value.unit !== expectedUnit ||
    typeof value.source_parameter_id !== "string" ||
    !value.source_parameter_id
  ) return null;
  return { value: value.value, unit: expectedUnit, source_parameter_id: value.source_parameter_id };
}

function parseSemanticSource(value: unknown): SemanticSource | null {
  if (!isRecord(value) || !exactKeys(value, [
    "schema_version",
    "kind",
    "transformation_version",
    "source_simulation_run_id",
    "source_model_version_id",
    "geometry_bindings"
  ])) return null;
  if (
    value.schema_version !== 1 ||
    value.kind !== "cad_link_047_m0" ||
    value.transformation_version !== "bluerev_047_m0_tube_proxy_v0_1" ||
    typeof value.source_simulation_run_id !== "string" ||
    !value.source_simulation_run_id ||
    typeof value.source_model_version_id !== "string" ||
    !value.source_model_version_id ||
    !isRecord(value.geometry_bindings) ||
    !exactKeys(value.geometry_bindings, GEOMETRY_NAMES)
  ) return null;
  const tubeLength = parseSemanticBinding(value.geometry_bindings.tube_length, "m");
  const inner = parseSemanticBinding(value.geometry_bindings.tube_inner_diameter, "mm");
  const outer = parseSemanticBinding(value.geometry_bindings.tube_outer_diameter, "mm");
  if (!tubeLength || !inner || !outer) return null;
  return {
    schema_version: 1,
    kind: "cad_link_047_m0",
    transformation_version: "bluerev_047_m0_tube_proxy_v0_1",
    source_simulation_run_id: value.source_simulation_run_id,
    source_model_version_id: value.source_model_version_id,
    geometry_bindings: {
      tube_length: tubeLength,
      tube_inner_diameter: inner,
      tube_outer_diameter: outer
    }
  };
}

function semanticTargetKey(target: BluecadPartSelection | null): string {
  if (!target) return "";
  return [
    target.workspaceId,
    target.candidateId,
    target.artifactId,
    target.viewerSessionId,
    target.ephemeralObjectId,
    target.semanticKey,
    target.partId,
    target.partKind ?? ""
  ].join("\u001f");
}

function semanticStableTargetKey(target: BluecadPartSelection, source: SemanticSource): string {
  return [
    target.workspaceId,
    target.candidateId,
    target.artifactId,
    target.partId,
    target.partKind ?? "",
    source.transformation_version,
    source.source_simulation_run_id,
    source.source_model_version_id
  ].join("\u001f");
}

function withSemanticGeometry(bindings: BindingMap, source: SemanticSource): BindingMap {
  const next = cloneBindings(bindings);
  for (const name of GEOMETRY_NAMES) {
    const item = source.geometry_bindings[name];
    next[name] = { value: String(item.value), parameterId: item.source_parameter_id };
  }
  return next;
}

export function useEngineeringProperties(
  workspaceId: string | null,
  onWorkspaceChange: (workspaceId: string | null) => void,
  selection: StageSelection | null = null
): EngineeringPropertiesController {
  const [implementations, setImplementations] = useState<ModelImplementation[]>([]);
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [selectedId, setSelectedIdState] = useState("");
  const [baseline, setBaseline] = useState<BindingMap>({});
  const [working, setWorking] = useState<BindingMap>({});
  const [undoStack, setUndoStack] = useState<BindingMap[]>([]);
  const [revision, setRevision] = useState(0);
  const [preview, setPreview] = useState<BindingPreviewResponse | null>(null);
  const [previewPhase, setPreviewPhase] = useState<PreviewPhase>("idle");
  const [previewMessage, setPreviewMessage] = useState<string | null>(null);
  const [runLabel, setRunLabel] = useState("");
  const [runBusy, setRunBusy] = useState(false);
  const [runMessage, setRunMessage] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<RunnerJobRunResponse | null>(null);
  const [pendingRun, setPendingRun] = useState<RunSnapshot | null>(null);
  const [semanticSource, setSemanticSource] = useState<SemanticSource | null>(null);
  const [semanticPhase, setSemanticPhase] = useState<SemanticPhase>("none");
  const [semanticMessage, setSemanticMessage] = useState<string | null>(null);
  const [semanticAdoptedContextKey, setSemanticAdoptedContextKey] = useState("");

  const loadGeneration = useRef(0);
  const previewGeneration = useRef(0);
  const semanticGeneration = useRef(0);
  const semanticAdoptionKeyRef = useRef<string | null>(null);
  const activeSemanticStableKeyRef = useRef<string | null>(null);
  const pendingPreviousTargetKeyRef = useRef<string | null>(null);
  const revisionRef = useRef(revision);
  const selectedIdRef = useRef(selectedId);
  const selectionKeyRef = useRef("");
  revisionRef.current = revision;
  selectedIdRef.current = selectedId;

  const semanticTarget = useMemo<BluecadPartSelection | null>(() => {
    if (!workspaceId || selection?.kind !== "bluecad-part" || selection.workspaceId !== workspaceId) return null;
    return selection;
  }, [selection, workspaceId]);
  const currentSemanticTargetKey = useMemo(() => semanticTargetKey(semanticTarget), [semanticTarget]);
  selectionKeyRef.current = currentSemanticTargetKey;

  const eligible = useMemo(
    () => implementations.filter((item) => Boolean(item.input_contract?.variables.length && item.input_contract_sha256)),
    [implementations]
  );
  const selected = useMemo(() => eligible.find((item) => item.id === selectedId) ?? null, [eligible, selectedId]);
  const variables = selected?.input_contract?.variables ?? [];
  const semanticContract = useMemo(() => reviewedContractForTarget(selected, semanticTarget), [selected, semanticTarget]);

  useEffect(() => {
    if (workspaceId) return;
    const generation = ++loadGeneration.current;
    listWorkspaces()
      .then((items) => {
        if (generation !== loadGeneration.current) return;
        onWorkspaceChange(items[0]?.id ?? null);
      })
      .catch(() => undefined);
  }, [workspaceId, onWorkspaceChange]);

  useEffect(() => {
    if (!workspaceId) {
      setImplementations([]);
      setParameters([]);
      return;
    }
    const generation = ++loadGeneration.current;
    Promise.all([listModelImplementations(workspaceId), listParameters(workspaceId)])
      .then(([nextImplementations, nextParameters]) => {
        if (generation !== loadGeneration.current) return;
        setImplementations(nextImplementations);
        setParameters(nextParameters);
      })
      .catch((error: Error) => {
        if (generation !== loadGeneration.current) return;
        setPreviewPhase("unavailable");
        setPreviewMessage(error.message);
      });
  }, [workspaceId]);

  useEffect(() => {
    if (!eligible.some((item) => item.id === selectedId)) setSelectedIdState(eligible[0]?.id ?? "");
  }, [eligible, selectedId]);

  useEffect(() => {
    const next = emptyBindings(variables);
    setBaseline(next);
    setWorking(next);
    setUndoStack([]);
    setPreview(null);
    setPreviewPhase(selected ? "checking" : "idle");
    setPreviewMessage(null);
    setRunResult(null);
    setRunMessage(null);
    setPendingRun(null);
    setRunLabel("");
    setRevision((current) => current + 1);
    previewGeneration.current += 1;
    semanticAdoptionKeyRef.current = null;
    activeSemanticStableKeyRef.current = null;
    pendingPreviousTargetKeyRef.current = null;
    setSemanticAdoptedContextKey("");
  }, [selected?.id]);

  useEffect(() => {
    const generation = ++semanticGeneration.current;
    setSemanticSource(null);
    setSemanticMessage(null);

    if (!workspaceId || !semanticTarget) {
      setSemanticPhase("none");
      return;
    }
    if (semanticTarget.partId !== REVIEWED_PART_ID || semanticTarget.partKind !== REVIEWED_PART_KIND) {
      setSemanticPhase("limited");
      setSemanticMessage("No reviewed object-specific model semantics are available for this selected part.");
      return;
    }

    const requestedKey = currentSemanticTargetKey;
    const requestedWorkspace = workspaceId;
    const requestedCandidate = semanticTarget.candidateId;
    setSemanticPhase("loading");
    getBluecadCandidateAggregate(requestedWorkspace, requestedCandidate)
      .then((aggregate) => {
        if (generation !== semanticGeneration.current || selectionKeyRef.current !== requestedKey) return;
        if (aggregate.candidate.id !== requestedCandidate || aggregate.candidate.workspace_id !== requestedWorkspace) {
          setSemanticPhase("limited");
          setSemanticMessage("The engineering source response no longer matches the selected candidate.");
          return;
        }
        const rawAggregate = aggregate as typeof aggregate & { semantic_source?: unknown };
        const source = parseSemanticSource(rawAggregate.semantic_source ?? null);
        if (!source) {
          const semanticDiagnostic = aggregate.diagnostics.find((item) => item.source === "bluecad.semantic_source");
          setSemanticPhase("limited");
          setSemanticMessage(semanticDiagnostic?.message ?? "This candidate has no reviewed-047 semantic source for the selected object.");
          return;
        }
        setSemanticSource(source);
        setSemanticPhase("ready");
      })
      .catch((error: Error) => {
        if (generation !== semanticGeneration.current || selectionKeyRef.current !== requestedKey) return;
        setSemanticPhase("limited");
        setSemanticMessage(`Object semantic source unavailable: ${error.message}`);
      });
  }, [workspaceId, currentSemanticTargetKey, semanticTarget]);

  useEffect(() => {
    if (!semanticSource || !semanticContract || !semanticTarget || semanticPhase !== "ready") return;
    const objectVariables = semanticContract.variables.filter((variable) => variable.applicable_part_kinds?.includes(REVIEWED_PART_KIND));
    const stableKey = semanticStableTargetKey(semanticTarget, semanticSource);
    const adoptionKey = [
      currentSemanticTargetKey,
      selected?.id ?? "",
      stableKey,
      ...GEOMETRY_NAMES.map((name) => {
        const item = semanticSource.geometry_bindings[name];
        return `${name}:${item.value}:${item.unit}:${item.source_parameter_id}`;
      })
    ].join("\u001e");
    if (semanticAdoptionKeyRef.current === adoptionKey) return;

    if (activeSemanticStableKeyRef.current === stableKey) {
      semanticAdoptionKeyRef.current = adoptionKey;
      setSemanticAdoptedContextKey(currentSemanticTargetKey);
      if (pendingPreviousTargetKeyRef.current === stableKey) {
        pendingPreviousTargetKeyRef.current = null;
        setSemanticMessage(null);
      }
      return;
    }

    const dirtyObjectNames = objectVariables.filter((variable) => !sameBinding(working[variable.name], baseline[variable.name]));
    if (activeSemanticStableKeyRef.current && dirtyObjectNames.length > 0) {
      pendingPreviousTargetKeyRef.current = activeSemanticStableKeyRef.current;
      setSemanticPhase("conflict");
      setSemanticMessage("Unsaved object changes belong to the previous engineering target. Discard them explicitly before loading the selected object, or reselect the previous object to continue editing.");
      previewGeneration.current += 1;
      setPreview(null);
      setPreviewPhase("unavailable");
      setPreviewMessage("Resolve the previous object's unsaved changes before preflight or Run for the selected object.");
      return;
    }

    const nextBaseline = withSemanticGeometry(baseline, semanticSource);
    const nextWorking = withSemanticGeometry(working, semanticSource);
    semanticAdoptionKeyRef.current = adoptionKey;
    activeSemanticStableKeyRef.current = stableKey;
    pendingPreviousTargetKeyRef.current = null;
    setSemanticAdoptedContextKey(currentSemanticTargetKey);
    setBaseline(nextBaseline);
    setWorking(nextWorking);
    setUndoStack((stack) => stack.map((snapshot) => withSemanticGeometry(snapshot, semanticSource)));
    setRevision((current) => current + 1);
    setPreview(null);
    setPreviewPhase("checking");
    setPreviewMessage(null);
    previewGeneration.current += 1;
    setSemanticPhase("ready");
    setSemanticMessage(null);
  }, [semanticSource, semanticContract, semanticTarget, semanticPhase, currentSemanticTargetKey, selected?.id, working, baseline]);

  useEffect(() => {
    if (!workspaceId || !selected) {
      setPreview(null);
      setPreviewPhase("idle");
      return;
    }
    if (semanticPhase === "conflict") {
      previewGeneration.current += 1;
      setPreview(null);
      setPreviewPhase("unavailable");
      setPreviewMessage("Resolve the previous object's unsaved changes before preflight or Run for the selected object.");
      return;
    }
    if (semanticContract && semanticTarget && semanticAdoptedContextKey !== currentSemanticTargetKey) {
      previewGeneration.current += 1;
      setPreview(null);
      setPreviewPhase("unavailable");
      setPreviewMessage("The selected engineering object is still resolving its authoritative semantic source.");
      return;
    }
    const built = buildPayload(variables, working);
    if (built.invalidNames.length) {
      previewGeneration.current += 1;
      setPreview(null);
      setPreviewPhase("local-invalid");
      setPreviewMessage("One or more values are not finite numbers.");
      return;
    }

    const generation = ++previewGeneration.current;
    const requestedRevision = revision;
    const requestedModel = selected.id;
    const requestedDigest = selected.input_contract_sha256 ?? "";
    setPreviewPhase("checking");
    setPreviewMessage(null);
    const timer = window.setTimeout(() => {
      previewModelBindings(workspaceId, requestedModel, built.payload)
        .then((response) => {
          if (
            generation !== previewGeneration.current ||
            requestedRevision !== revisionRef.current ||
            requestedModel !== selectedIdRef.current
          ) return;
          if (response.model_version_id !== requestedModel || response.contract_sha256 !== requestedDigest) {
            setPreview(null);
            setPreviewPhase("unavailable");
            setPreviewMessage("The model contract changed during preflight. Refresh the engineering context.");
            return;
          }
          setPreview(response);
          setPreviewPhase("ready");
        })
        .catch((error: Error) => {
          if (generation !== previewGeneration.current || requestedRevision !== revisionRef.current) return;
          setPreview(null);
          setPreviewPhase("unavailable");
          setPreviewMessage(`Preflight unavailable: ${error.message}`);
        });
    }, 120);
    return () => window.clearTimeout(timer);
  }, [workspaceId, selected?.id, selected?.input_contract_sha256, revision, semanticPhase, semanticTarget, semanticAdoptedContextKey, currentSemanticTargetKey]);

  const dirtyNames = useMemo(
    () => new Set(variables.filter((variable) => !sameBinding(working[variable.name], baseline[variable.name])).map((variable) => variable.name)),
    [variables, working, baseline]
  );

  const commitWorking = (next: BindingMap) => {
    setUndoStack((stack) => [...stack.slice(-(MAX_UNDO - 1)), cloneBindings(working)]);
    setWorking(cloneBindings(next));
    setRevision((current) => current + 1);
    setRunResult(null);
  };

  const updateValue = (variable: ModelInputVariable, value: string) => {
    const next = { ...working, [variable.name]: { value, parameterId: "" } };
    commitWorking(next);
  };

  const selectParameter = (variable: ModelInputVariable, parameterId: string) => {
    const parameter = parameters.find((item) => item.id === parameterId && item.unit === variable.unit);
    const nextBinding = parameter
      ? { parameterId: parameter.id, value: parameter.value ?? "" }
      : { parameterId: "", value: working[variable.name]?.value ?? "" };
    commitWorking({ ...working, [variable.name]: nextBinding });
  };

  const undo = () => {
    const previous = undoStack[undoStack.length - 1];
    if (!previous) return;
    setUndoStack((stack) => stack.slice(0, -1));
    setWorking(cloneBindings(previous));
    setRevision((current) => current + 1);
  };

  const revertField = (name: string) => commitWorking({ ...working, [name]: { ...(baseline[name] ?? EMPTY_BINDING) } });
  const revertAll = () => commitWorking(baseline);

  const discardPreviousObjectChanges = () => {
    if (!semanticSource || !semanticContract || !semanticTarget || semanticPhase !== "conflict") return;
    const stableKey = semanticStableTargetKey(semanticTarget, semanticSource);
    const nextBaseline = withSemanticGeometry(baseline, semanticSource);
    const nextWorking = withSemanticGeometry(working, semanticSource);
    setBaseline(nextBaseline);
    setWorking(nextWorking);
    setUndoStack((stack) => stack.map((snapshot) => withSemanticGeometry(snapshot, semanticSource)));
    pendingPreviousTargetKeyRef.current = null;
    activeSemanticStableKeyRef.current = stableKey;
    semanticAdoptionKeyRef.current = null;
    setSemanticAdoptedContextKey(currentSemanticTargetKey);
    setRevision((current) => current + 1);
    setRunResult(null);
    setPendingRun(null);
    setPreview(null);
    setPreviewPhase("checking");
    setPreviewMessage(null);
    previewGeneration.current += 1;
    setSemanticPhase("ready");
    setSemanticMessage(null);
  };

  const executeSnapshot = async (snapshot: RunSnapshot) => {
    setRunBusy(true);
    setRunMessage(null);
    try {
      const created = await createRunnerJob(workspaceId!, snapshot.payload);
      if (created.runner_job.status !== "queued") {
        const reconciled: RunnerJobRunResponse = {
          runner_job: created.runner_job,
          simulation_run: created.simulation_run,
          output: null,
          error: null
        };
        setRunResult(reconciled);

        if (created.runner_job.status === "succeeded") {
          setPendingRun(null);
          if (revisionRef.current === snapshot.revision && selectedIdRef.current === selected?.id) {
            setBaseline(cloneBindings(snapshot.bindings));
            setUndoStack([]);
          }
          setRunMessage("Run already completed successfully. Canonical project records were not changed.");
          return;
        }

        if (["failed", "cancelled", "timed_out"].includes(created.runner_job.status)) {
          setPendingRun(null);
          setRunMessage(`Execution already finished with status ${created.runner_job.status}. Working edits were preserved.`);
          return;
        }

        setPendingRun(snapshot);
        setRunMessage(`Run is already ${created.runner_job.status}. Retry reconciliation uses the same request identity and will not redispatch execution.`);
        return;
      }

      const result = await runRunnerJob(created.runner_job.id);
      setRunResult(result);
      setPendingRun(null);
      if (result.runner_job.status === "succeeded") {
        if (revisionRef.current === snapshot.revision && selectedIdRef.current === selected?.id) {
          setBaseline(cloneBindings(snapshot.bindings));
          setUndoStack([]);
        }
        setRunMessage("Run completed. Canonical project records were not changed.");
      } else {
        setRunMessage("Execution finished without success. Working edits were preserved.");
      }
    } catch (error) {
      setPendingRun(snapshot);
      setRunMessage(`Run start/execution outcome is uncertain: ${error instanceof Error ? error.message : String(error)}. Retry uses the same request identity.`);
    } finally {
      setRunBusy(false);
    }
  };

  const startRun = () => {
    if (
      !workspaceId ||
      !selected ||
      runBusy ||
      semanticPhase === "conflict" ||
      (semanticContract && semanticTarget && semanticAdoptedContextKey !== currentSemanticTargetKey) ||
      previewPhase !== "ready" ||
      preview?.state !== "ready" ||
      !preview.normalized_input_set ||
      !runLabel.trim()
    ) return;
    const requestKey = newRequestKey();
    const snapshot: RunSnapshot = {
      requestKey,
      revision,
      bindings: cloneBindings(working),
      payload: {
        request_key: requestKey,
        model_version_id: selected.id,
        run_label: runLabel.trim(),
        input_set: preview.normalized_input_set
      }
    };
    setPendingRun(snapshot);
    void executeSnapshot(snapshot);
  };

  const retryRunStart = () => {
    if (!pendingRun || runBusy || semanticPhase === "conflict") return;
    void executeSnapshot(pendingRun);
  };

  return {
    workspaceId,
    implementations: eligible,
    selected,
    selectedId,
    setSelectedId: setSelectedIdState,
    parameters,
    baseline,
    working,
    preview,
    previewPhase,
    previewMessage,
    revision,
    dirtyNames,
    undoAvailable: undoStack.length > 0,
    runLabel,
    setRunLabel,
    runBusy,
    runMessage,
    runResult,
    pendingRun,
    semanticTarget,
    semanticPhase,
    semanticMessage,
    semanticSource,
    semanticContract,
    updateValue,
    selectParameter,
    undo,
    revertField,
    revertAll,
    discardPreviousObjectChanges,
    startRun,
    retryRunStart
  };
}

function firstBlockingName(controller: EngineeringPropertiesController): string | null {
  const variables = controller.selected?.input_contract?.variables ?? [];
  const localInvalid = variables.find((variable) => {
    const value = controller.working[variable.name]?.value.trim() ?? "";
    return Boolean(value) && !Number.isFinite(Number(value));
  });
  if (localInvalid) return localInvalid.name;
  const previewBlocker = controller.preview?.variables.find(
    (variable) => variable.binding_state === "invalid" || (variable.required && variable.binding_state === "missing")
  );
  return previewBlocker?.name ?? null;
}

function blockerCount(controller: EngineeringPropertiesController): number {
  const variables = controller.selected?.input_contract?.variables ?? [];
  const localInvalid = variables.filter((variable) => {
    const value = controller.working[variable.name]?.value.trim() ?? "";
    return Boolean(value) && !Number.isFinite(Number(value));
  }).length;
  if (localInvalid) return localInvalid;
  if (!controller.preview) return 0;
  return controller.preview.variables.filter(
    (variable) => variable.binding_state === "invalid" || (variable.required && variable.binding_state === "missing")
  ).length + controller.preview.errors.length;
}

export function EngineeringPropertiesPanel({
  controller,
  stageContext,
  navigate
}: {
  controller: EngineeringPropertiesController;
  stageContext?: ReactNode;
  navigate?: Navigate;
}) {
  const selected = controller.selected;
  const variables = selected?.input_contract?.variables ?? [];
  const blockers = blockerCount(controller);
  const semanticContract = controller.semanticContract;
  const semanticEditable = Boolean(
    semanticContract &&
    controller.semanticSource &&
    controller.semanticTarget &&
    controller.semanticPhase === "ready"
  );
  const objectVariables = semanticEditable
    ? semanticContract!.variables.filter((variable) => variable.applicable_part_kinds?.includes(REVIEWED_PART_KIND))
    : [];
  const genericVariables = semanticContract
    ? semanticContract.variables.filter((variable) => (variable.applicable_part_kinds?.length ?? 0) === 0)
    : variables;
  const objectGroups = useMemo(() => {
    const grouped = new Map<string, SemanticVariable[]>();
    objectVariables.forEach((variable) => {
      const group = variable.property_group ?? "Properties";
      grouped.set(group, [...(grouped.get(group) ?? []), variable]);
    });
    return [...grouped.entries()];
  }, [objectVariables]);
  const genericGroups = useMemo(() => {
    const grouped = new Map<string, ModelInputVariable[]>();
    genericVariables.forEach((variable) => {
      const semantic = variable as SemanticVariable;
      const group = semanticContract ? semantic.property_group ?? "Model configuration" : CATEGORY_LABELS[variable.category];
      grouped.set(group, [...(grouped.get(group) ?? []), variable]);
    });
    return [...grouped.entries()];
  }, [genericVariables, semanticContract]);
  const applicableSemantic = useMemo(
    () => controller.semanticTarget
      ? controller.implementations
        .map((item) => ({ item, contract: reviewedContractForTarget(item, controller.semanticTarget) }))
        .filter((entry): entry is { item: ModelImplementation; contract: SemanticContract } => Boolean(entry.contract))
      : [],
    [controller.implementations, controller.semanticTarget]
  );

  const goToFirstIssue = () => {
    const name = firstBlockingName(controller);
    if (!name) return;
    document.getElementById(`engineering-property-${name}`)?.focus();
  };

  const renderVariable = (variable: ModelInputVariable) => {
    const binding = controller.working[variable.name] ?? EMPTY_BINDING;
    const variablePreview = controller.preview?.variables.find((item) => item.name === variable.name);
    const linkedParameter = binding.parameterId ? controller.parameters.find((item) => item.id === binding.parameterId) : undefined;
    const compatible = controller.parameters.filter(
      (parameter) =>
        parameter.unit === variable.unit &&
        parameter.value != null &&
        Number.isFinite(Number(parameter.value)) &&
        (parameter.status !== "superseded" || parameter.id === binding.parameterId)
    );
    const isDirty = controller.dirtyNames.has(variable.name);
    const isRequiredMissing = Boolean(variable.required && variablePreview?.binding_state === "missing");
    const isInvalid = variablePreview?.binding_state === "invalid" || (binding.value.trim() !== "" && !Number.isFinite(Number(binding.value)));
    const source = binding.parameterId
      ? `Linked parameter · ${linkedParameter?.name ?? "linked source"}`
      : binding.value.trim() ? "Working override" : "Empty";
    return (
      <div className="scenario-variable" key={variable.name}>
        <div>
          <strong>{variable.label}{isDirty ? " · Modified" : ""}</strong>
          <span>{source}</span>
          <small>{variable.description}</small>
        </div>
        <label>
          Value [{variable.unit}]
          <input
            id={`engineering-property-${variable.name}`}
            type="number"
            step="any"
            value={binding.value}
            placeholder="Empty"
            aria-invalid={isInvalid || isRequiredMissing || undefined}
            onChange={(event) => controller.updateValue(variable, event.target.value)}
          />
        </label>
        <label>
          Source
          <select value={binding.parameterId} onChange={(event) => controller.selectParameter(variable, event.target.value)}>
            <option value="">Working override</option>
            {compatible.map((parameter) => (
              <option key={parameter.id} value={parameter.id}>
                {parameter.name}{parameter.status === "superseded" ? " (superseded)" : ""}: {parameter.value} {parameter.unit}
              </option>
            ))}
          </select>
        </label>
        <div className={`binding-state ${isInvalid ? "invalid" : isRequiredMissing ? "missing" : variablePreview?.binding_state ?? "missing"}`}>
          {isRequiredMissing ? <span>Required value is empty.</span> : null}
          {!variable.required && !binding.value.trim() ? <span>Optional · Empty</span> : null}
          {isInvalid && !variablePreview?.errors.length ? <span>Enter a finite number.</span> : null}
          {variablePreview?.errors.map((error) => <span key={error}>{error}</span>)}
        </div>
        {binding.parameterId ? (
          <details className="shell-properties__inspect">
            <summary>Inspect linked source</summary>
            <dl className="details">
              <div><dt>Parameter</dt><dd>{linkedParameter?.name ?? "Unavailable source record"}</dd></div>
              <div><dt>Status</dt><dd>{linkedParameter?.status ?? "unavailable"}</dd></div>
            </dl>
            {navigate ? (
              <button
                type="button"
                className="secondary-button"
                onClick={() => navigate(`/engineering-data?kind=parameter&id=${encodeURIComponent(binding.parameterId)}`)}
              >
                Open source
              </button>
            ) : null}
          </details>
        ) : null}
        {isDirty ? <button type="button" className="secondary-button" onClick={() => controller.revertField(variable.name)}>Revert field</button> : null}
      </div>
    );
  };

  if (!controller.workspaceId) {
    return <InlineNotice tone="neutral">No workspace is available for engineering Properties.</InlineNotice>;
  }

  return (
    <div className="engineering-properties">
      {controller.implementations.length === 0 ? (
        <InlineNotice tone="neutral">No eligible model input contract is registered in this workspace.</InlineNotice>
      ) : (
        <>
          {controller.semanticTarget ? (
            <div className="shell-properties__selection">
              <strong>{controller.semanticTarget.partId}</strong>
              <p>{controller.semanticTarget.partKind ? `${controller.semanticTarget.partKind} · selected engineering object` : "Selected engineering object · semantics limited"}</p>
            </div>
          ) : null}

          <label className="scenario-model-select">
            Model contract
            <select value={controller.selectedId} onChange={(event) => controller.setSelectedId(event.target.value)}>
              {controller.implementations.map((item) => <option key={item.id} value={item.id}>{item.version_label}</option>)}
            </select>
          </label>

          {semanticContract ? (
            <div className="dof-strip" aria-label="Active engineering model">
              <span>{semanticContract.semantic_context.model_family_label}</span>
              <strong>{semanticContract.semantic_context.model_option_label}</strong>
            </div>
          ) : controller.semanticTarget && applicableSemantic.length > 0 ? (
            <InlineNotice tone="neutral">Object semantics are available through {applicableSemantic[0].contract.semantic_context.model_option_label}; select that model contract to edit the selected object.</InlineNotice>
          ) : null}

          {controller.semanticPhase === "loading" ? <InlineNotice tone="neutral">Resolving authoritative object source…</InlineNotice> : null}
          {controller.semanticPhase === "limited" && controller.semanticMessage ? <InlineNotice tone="neutral">{controller.semanticMessage}</InlineNotice> : null}
          {controller.semanticPhase === "conflict" && controller.semanticMessage ? (
            <InlineNotice tone="warning">
              {controller.semanticMessage}
              <div><button type="button" className="secondary-button" onClick={controller.discardPreviousObjectChanges}>Discard previous object changes and load selected object</button></div>
            </InlineNotice>
          ) : null}

          <div className="dof-strip" aria-live="polite">
            {controller.previewPhase === "checking" ? <strong>Checking…</strong> : null}
            {controller.previewPhase === "ready" && controller.preview?.state === "ready" ? <strong>Ready</strong> : null}
            {blockers > 0 ? <strong>{blockers} blocker{blockers === 1 ? "" : "s"}</strong> : null}
            {controller.previewPhase === "unavailable" ? <strong>Preflight unavailable</strong> : null}
            {controller.dirtyNames.size > 0 ? <span>{controller.dirtyNames.size} unsaved change{controller.dirtyNames.size === 1 ? "" : "s"} · Baseline: current bindings</span> : <span>Baseline: current bindings</span>}
          </div>
          {controller.previewMessage ? <div className="error-banner">{controller.previewMessage}</div> : null}
          {blockers > 0 ? <button type="button" className="secondary-button" onClick={goToFirstIssue}>Go to first issue</button> : null}

          {objectGroups.length > 0 ? (
            <div className="scenario-variable-list" aria-label="Selected object properties">
              {objectGroups.map(([group, rows]) => (
                <section key={`object-${group}`} aria-labelledby={`engineering-object-properties-${group.replace(/\s+/g, "-").toLowerCase()}`}>
                  <h4 id={`engineering-object-properties-${group.replace(/\s+/g, "-").toLowerCase()}`}>{group}</h4>
                  {rows.map(renderVariable)}
                </section>
              ))}
            </div>
          ) : null}

          {genericGroups.length > 0 ? (
            <div className="scenario-variable-list" aria-label={semanticContract ? "Generic model configuration" : "Model properties"}>
              {semanticContract ? <h4>Model configuration</h4> : null}
              {genericGroups.map(([group, rows]) => (
                <section key={`generic-${group}`} aria-labelledby={`engineering-generic-properties-${group.replace(/\s+/g, "-").toLowerCase()}`}>
                  <h4 id={`engineering-generic-properties-${group.replace(/\s+/g, "-").toLowerCase()}`}>{group}</h4>
                  {rows.map(renderVariable)}
                </section>
              ))}
            </div>
          ) : null}

          <div className="scenario-actions">
            <button type="button" className="secondary-button" disabled={!controller.undoAvailable} onClick={controller.undo}>Undo</button>
            <button type="button" className="secondary-button" disabled={controller.dirtyNames.size === 0} onClick={controller.revertAll}>Revert all</button>
            <label>
              Run label
              <input value={controller.runLabel} onChange={(event) => controller.setRunLabel(event.target.value)} />
            </label>
            <button
              type="button"
              disabled={controller.runBusy || controller.semanticPhase === "conflict" || controller.previewPhase !== "ready" || controller.preview?.state !== "ready" || !controller.runLabel.trim()}
              onClick={controller.startRun}
            >
              Run
            </button>
          </div>
          {controller.pendingRun && controller.runMessage ? <button type="button" className="secondary-button" disabled={controller.runBusy || controller.semanticPhase === "conflict"} onClick={controller.retryRunStart}>Retry same run request</button> : null}
          {controller.runMessage ? <p>{controller.runMessage}</p> : null}
          {controller.runResult ? <p>Execution status: <strong>{controller.runResult.runner_job.status}</strong></p> : null}
        </>
      )}

      {stageContext ? <details className="shell-properties__inspect"><summary>Current stage context</summary>{stageContext}</details> : null}
      {controller.semanticSource ? (
        <details className="shell-properties__inspect">
          <summary>Semantic source</summary>
          <dl className="details">
            <div><dt>Basis</dt><dd>Reviewed 047 CAD link</dd></div>
            <div><dt>Source run</dt><dd>{controller.semanticSource.source_simulation_run_id}</dd></div>
            <div><dt>Source model</dt><dd>{controller.semanticSource.source_model_version_id}</dd></div>
          </dl>
        </details>
      ) : null}
      {selected ? (
        <details className="shell-properties__inspect">
          <summary>Technical details</summary>
          <dl className="details">
            <div><dt>Model version</dt><dd>{selected.id}</dd></div>
            <div><dt>Contract digest</dt><dd>{selected.input_contract_sha256}</dd></div>
            <div><dt>Working revision</dt><dd>{controller.revision}</dd></div>
          </dl>
        </details>
      ) : null}
    </div>
  );
}
