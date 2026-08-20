import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import {
  createRunnerJob,
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
type RunSnapshot = Readonly<{
  requestKey: string;
  revision: number;
  bindings: BindingMap;
  payload: Record<string, unknown>;
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
  updateValue(variable: ModelInputVariable, value: string): void;
  selectParameter(variable: ModelInputVariable, parameterId: string): void;
  undo(): void;
  revertField(name: string): void;
  revertAll(): void;
  startRun(): void;
  retryRunStart(): void;
}>;

const EMPTY_BINDING: WorkingBinding = { value: "", parameterId: "" };
const MAX_UNDO = 20;
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

export function useEngineeringProperties(
  workspaceId: string | null,
  onWorkspaceChange: (workspaceId: string | null) => void
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

  const loadGeneration = useRef(0);
  const previewGeneration = useRef(0);
  const revisionRef = useRef(revision);
  const selectedIdRef = useRef(selectedId);
  revisionRef.current = revision;
  selectedIdRef.current = selectedId;

  const eligible = useMemo(
    () => implementations.filter((item) => Boolean(item.input_contract?.variables.length && item.input_contract_sha256)),
    [implementations]
  );
  const selected = useMemo(() => eligible.find((item) => item.id === selectedId) ?? null, [eligible, selectedId]);
  const variables = selected?.input_contract?.variables ?? [];

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
  }, [selected?.id]);

  useEffect(() => {
    if (!workspaceId || !selected) {
      setPreview(null);
      setPreviewPhase("idle");
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
  }, [workspaceId, selected?.id, selected?.input_contract_sha256, revision]);

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
    if (!pendingRun || runBusy) return;
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
    updateValue,
    selectParameter,
    undo,
    revertField,
    revertAll,
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
  stageContext
}: {
  controller: EngineeringPropertiesController;
  stageContext?: ReactNode;
}) {
  const selected = controller.selected;
  const variables = selected?.input_contract?.variables ?? [];
  const blockers = blockerCount(controller);
  const groups = useMemo(() => {
    const grouped = new Map<ModelInputVariable["category"], ModelInputVariable[]>();
    variables.forEach((variable) => grouped.set(variable.category, [...(grouped.get(variable.category) ?? []), variable]));
    return [...grouped.entries()];
  }, [variables]);

  const goToFirstIssue = () => {
    const name = firstBlockingName(controller);
    if (!name) return;
    document.getElementById(`engineering-property-${name}`)?.focus();
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
          <label className="scenario-model-select">
            Model contract
            <select value={controller.selectedId} onChange={(event) => controller.setSelectedId(event.target.value)}>
              {controller.implementations.map((item) => <option key={item.id} value={item.id}>{item.version_label}</option>)}
            </select>
          </label>

          <div className="dof-strip" aria-live="polite">
            {controller.previewPhase === "checking" ? <strong>Checking…</strong> : null}
            {controller.previewPhase === "ready" && controller.preview?.state === "ready" ? <strong>Ready</strong> : null}
            {blockers > 0 ? <strong>{blockers} blocker{blockers === 1 ? "" : "s"}</strong> : null}
            {controller.previewPhase === "unavailable" ? <strong>Preflight unavailable</strong> : null}
            {controller.dirtyNames.size > 0 ? <span>{controller.dirtyNames.size} unsaved change{controller.dirtyNames.size === 1 ? "" : "s"} · Baseline: current bindings</span> : <span>Baseline: current bindings</span>}
          </div>
          {controller.previewMessage ? <div className="error-banner">{controller.previewMessage}</div> : null}
          {blockers > 0 ? <button type="button" className="secondary-button" onClick={goToFirstIssue}>Go to first issue</button> : null}

          <div className="scenario-variable-list">
            {groups.map(([category, rows]) => (
              <section key={category} aria-labelledby={`engineering-properties-${category}`}>
                <h4 id={`engineering-properties-${category}`}>{CATEGORY_LABELS[category]}</h4>
                {rows.map((variable) => {
                  const binding = controller.working[variable.name] ?? EMPTY_BINDING;
                  const variablePreview = controller.preview?.variables.find((item) => item.name === variable.name);
                  const compatible = controller.parameters.filter(
                    (parameter) => parameter.unit === variable.unit && parameter.value != null && Number.isFinite(Number(parameter.value))
                  );
                  const isDirty = controller.dirtyNames.has(variable.name);
                  const isRequiredMissing = Boolean(variable.required && variablePreview?.binding_state === "missing");
                  const isInvalid = variablePreview?.binding_state === "invalid" || (binding.value.trim() !== "" && !Number.isFinite(Number(binding.value)));
                  const source = binding.parameterId
                    ? `Parameter · ${controller.parameters.find((item) => item.id === binding.parameterId)?.name ?? "linked source"}`
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
                          {compatible.map((parameter) => <option key={parameter.id} value={parameter.id}>{parameter.name}: {parameter.value} {parameter.unit}</option>)}
                        </select>
                      </label>
                      <div className={`binding-state ${isInvalid ? "invalid" : isRequiredMissing ? "missing" : variablePreview?.binding_state ?? "missing"}`}>
                        {isRequiredMissing ? <span>Required value is empty.</span> : null}
                        {!variable.required && !binding.value.trim() ? <span>Optional · Empty</span> : null}
                        {isInvalid && !variablePreview?.errors.length ? <span>Enter a finite number.</span> : null}
                        {variablePreview?.errors.map((error) => <span key={error}>{error}</span>)}
                      </div>
                      {isDirty ? <button type="button" className="secondary-button" onClick={() => controller.revertField(variable.name)}>Revert field</button> : null}
                    </div>
                  );
                })}
              </section>
            ))}
          </div>

          <div className="scenario-actions">
            <button type="button" className="secondary-button" disabled={!controller.undoAvailable} onClick={controller.undo}>Undo</button>
            <button type="button" className="secondary-button" disabled={controller.dirtyNames.size === 0} onClick={controller.revertAll}>Revert all</button>
            <label>
              Run label
              <input value={controller.runLabel} onChange={(event) => controller.setRunLabel(event.target.value)} />
            </label>
            <button
              type="button"
              disabled={controller.runBusy || controller.previewPhase !== "ready" || controller.preview?.state !== "ready" || !controller.runLabel.trim()}
              onClick={controller.startRun}
            >
              Run
            </button>
          </div>
          {controller.pendingRun && controller.runMessage ? <button type="button" className="secondary-button" disabled={controller.runBusy} onClick={controller.retryRunStart}>Retry same run request</button> : null}
          {controller.runMessage ? <p>{controller.runMessage}</p> : null}
          {controller.runResult ? <p>Execution status: <strong>{controller.runResult.runner_job.status}</strong></p> : null}
        </>
      )}

      {stageContext ? <details className="shell-properties__inspect"><summary>Current stage context</summary>{stageContext}</details> : null}
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
