import { useMemo, useState } from "react";

import type { ModelInputVariable, Parameter } from "../../api/client";
import type { EngineeringPropertiesController } from "./EngineeringProperties";

type WorkingBinding = Readonly<{ value: string; parameterId: string }>;
type ActionStatus = "ready" | "applied" | "stale" | "invalid" | "rejected";
type ActionBasis = "working-baseline" | "cad-source";

type EngineeringActionOperation = Readonly<{
  variableName: string;
  label: string;
  unit: string;
  expectedBinding: WorkingBinding;
  proposedBinding: WorkingBinding;
  basis: ActionBasis;
  basisLabel: string;
  reason: string;
}>;

export type EngineeringWorkingAction = Readonly<{
  id: string;
  workspaceId: string;
  modelVersionId: string;
  contractDigest: string;
  workingRevision: number;
  semanticFingerprint: string;
  operations: EngineeringActionOperation[];
}>;

function sameBinding(left: WorkingBinding | undefined, right: WorkingBinding | undefined): boolean {
  return (left?.value ?? "") === (right?.value ?? "") && (left?.parameterId ?? "") === (right?.parameterId ?? "");
}

function finiteBinding(binding: WorkingBinding | undefined): boolean {
  const value = binding?.value.trim() ?? "";
  return Boolean(value) && Number.isFinite(Number(value));
}

function semanticFingerprint(controller: EngineeringPropertiesController): string {
  const target = controller.semanticTarget;
  if (!target) return "";
  const source = controller.semanticSource;
  return [
    target.workspaceId,
    target.candidateId,
    target.artifactId,
    target.viewerSessionId,
    target.ephemeralObjectId,
    target.semanticKey,
    target.partId,
    target.partKind ?? "",
    source?.transformation_version ?? "",
    source?.source_simulation_run_id ?? "",
    source?.source_model_version_id ?? ""
  ].join("\u001f");
}

function compatibleParameters(controller: EngineeringPropertiesController, variable: ModelInputVariable): Parameter[] {
  return controller.parameters.filter((parameter) =>
    parameter.unit === variable.unit
    && parameter.value != null
    && Number.isFinite(Number(parameter.value))
    && parameter.status !== "superseded"
  );
}

function blockerVariables(controller: EngineeringPropertiesController): ModelInputVariable[] {
  const variables = controller.selected?.input_contract?.variables ?? [];
  return variables.filter((variable) => {
    const binding = controller.working[variable.name];
    const value = binding?.value.trim() ?? "";
    const localInvalid = Boolean(value) && !Number.isFinite(Number(value));
    const variablePreview = controller.preview?.variables.find((item) => item.name === variable.name);
    return localInvalid
      || variablePreview?.binding_state === "invalid"
      || Boolean(variable.required && variablePreview?.binding_state === "missing");
  });
}

function cadBaselineMatches(controller: EngineeringPropertiesController, variable: ModelInputVariable, baseline: WorkingBinding): boolean {
  const source = controller.semanticSource;
  if (!source || !["tube_length", "tube_inner_diameter", "tube_outer_diameter"].includes(variable.name)) return false;
  const binding = source.geometry_bindings[variable.name as keyof typeof source.geometry_bindings];
  return Boolean(binding)
    && String(binding.value) === baseline.value
    && binding.unit === variable.unit
    && binding.source_parameter_id === baseline.parameterId;
}

function safeOperation(controller: EngineeringPropertiesController, variable: ModelInputVariable): EngineeringActionOperation | null {
  const current = controller.working[variable.name] ?? { value: "", parameterId: "" };
  const baseline = controller.baseline[variable.name];
  if (finiteBinding(baseline) && !sameBinding(current, baseline)) {
    const cad = cadBaselineMatches(controller, variable, baseline!);
    if (baseline!.parameterId && !cad) {
      const parameter = compatibleParameters(controller, variable).find((item) => item.id === baseline!.parameterId);
      if (!parameter) return null;
    }
    return {
      variableName: variable.name,
      label: variable.label,
      unit: variable.unit,
      expectedBinding: { ...current },
      proposedBinding: { ...baseline! },
      basis: cad ? "cad-source" : "working-baseline",
      basisLabel: cad ? "CAD source baseline" : "Working baseline",
      reason: cad
        ? "Restore the exact adopted CAD-linked baseline already authoritative for this object."
        : "Restore the existing working baseline instead of inventing a replacement value."
    };
  }

  // A matching unit alone is not enough engineering evidence to bind an unrelated
  // canonical Parameter to a missing field (dimensionless values are the obvious
  // counterexample). Until a semantic parameter-to-variable identity exists, an
  // empty baseline stays unresolved rather than receiving a guessed safe fix.
  return null;
}

function actionFromOperations(controller: EngineeringPropertiesController, operations: EngineeringActionOperation[]): EngineeringWorkingAction | null {
  if (!controller.workspaceId || !controller.selected || !controller.selected.input_contract_sha256 || !operations.length) return null;
  const fingerprint = semanticFingerprint(controller);
  const id = [
    controller.workspaceId,
    controller.selected.id,
    controller.selected.input_contract_sha256,
    String(controller.revision),
    fingerprint,
    ...operations.map((operation) => `${operation.variableName}:${operation.expectedBinding.value}:${operation.expectedBinding.parameterId}:${operation.proposedBinding.value}:${operation.proposedBinding.parameterId}`)
  ].join("\u001e");
  return {
    id,
    workspaceId: controller.workspaceId,
    modelVersionId: controller.selected.id,
    contractDigest: controller.selected.input_contract_sha256,
    workingRevision: controller.revision,
    semanticFingerprint: fingerprint,
    operations
  };
}

function validateAction(controller: EngineeringPropertiesController, action: EngineeringWorkingAction): "ok" | "stale" | "invalid" {
  if (
    !controller.workspaceId
    || !controller.selected
    || controller.workspaceId !== action.workspaceId
    || controller.selected.id !== action.modelVersionId
    || controller.selected.input_contract_sha256 !== action.contractDigest
    || controller.revision !== action.workingRevision
    || semanticFingerprint(controller) !== action.semanticFingerprint
  ) return "stale";

  const variables = controller.selected.input_contract?.variables ?? [];
  for (const operation of action.operations) {
    const variable = variables.find((item) => item.name === operation.variableName);
    if (!variable || variable.unit !== operation.unit) return "invalid";
    if (!sameBinding(controller.working[operation.variableName], operation.expectedBinding)) return "stale";
    if (!finiteBinding(operation.proposedBinding)) return "invalid";

    if (operation.proposedBinding.parameterId) {
      if (operation.basis === "cad-source") {
        if (!cadBaselineMatches(controller, variable, operation.proposedBinding)) return "invalid";
      } else {
        const parameter = compatibleParameters(controller, variable).find((item) => item.id === operation.proposedBinding.parameterId);
        if (!parameter || String(parameter.value ?? "") !== operation.proposedBinding.value) return "invalid";
      }
    }
  }
  return "ok";
}

function applyAction(controller: EngineeringPropertiesController, action: EngineeringWorkingAction): "applied" | "stale" | "invalid" {
  const validation = validateAction(controller, action);
  if (validation !== "ok") return validation;

  if (action.operations.length === 1) {
    const operation = action.operations[0];
    const variable = controller.selected?.input_contract?.variables.find((item) => item.name === operation.variableName);
    if (!variable) return "invalid";
    if (sameBinding(operation.proposedBinding, controller.baseline[operation.variableName])) {
      controller.revertField(operation.variableName);
      return "applied";
    }
    if (operation.proposedBinding.parameterId) {
      controller.selectParameter(variable, operation.proposedBinding.parameterId);
      return "applied";
    }
    controller.updateValue(variable, operation.proposedBinding.value);
    return "applied";
  }

  const operationNames = new Set(action.operations.map((operation) => operation.variableName));
  const dirtyNames = [...controller.dirtyNames];
  const exactRevertAll = dirtyNames.length === action.operations.length
    && dirtyNames.every((name) => operationNames.has(name))
    && action.operations.every((operation) => sameBinding(operation.proposedBinding, controller.baseline[operation.variableName]));
  if (!exactRevertAll) return "invalid";
  controller.revertAll();
  return "applied";
}

function renderBinding(binding: WorkingBinding, unit: string): string {
  if (!binding.value.trim()) return "Empty";
  return `${binding.value} ${unit}`;
}

export default function JarvisEngineeringActions({ controller }: { controller: EngineeringPropertiesController }) {
  const [selectedAction, setSelectedAction] = useState<EngineeringWorkingAction | null>(null);
  const [status, setStatus] = useState<ActionStatus>("ready");
  const [showOther, setShowOther] = useState(false);
  const [otherText, setOtherText] = useState("");

  const blockers = useMemo(() => blockerVariables(controller), [controller]);
  const previewErrors = controller.preview?.errors ?? [];
  const blockerSignalCount = blockers.length + previewErrors.length;
  const safeOperations = useMemo(
    () => blockers.map((variable) => safeOperation(controller, variable)).filter((item): item is EngineeringActionOperation => Boolean(item)),
    [blockers, controller]
  );
  const singleActions = useMemo(
    () => safeOperations.map((operation) => actionFromOperations(controller, [operation])).filter((item): item is EngineeringWorkingAction => Boolean(item)),
    [controller, safeOperations]
  );
  const bulkAction = useMemo(() => {
    if (safeOperations.length < 2) return null;
    const dirtyNames = [...controller.dirtyNames];
    const operationNames = new Set(safeOperations.map((operation) => operation.variableName));
    const exactBulkRevert = dirtyNames.length === safeOperations.length
      && dirtyNames.every((name) => operationNames.has(name))
      && safeOperations.every((operation) => sameBinding(operation.proposedBinding, controller.baseline[operation.variableName]));
    return exactBulkRevert ? actionFromOperations(controller, safeOperations) : null;
  }, [controller, safeOperations]);

  const previewAction = (action: EngineeringWorkingAction) => {
    setSelectedAction(action);
    setStatus("ready");
  };

  const confirm = () => {
    if (!selectedAction || status !== "ready") return;
    const result = applyAction(controller, selectedAction);
    setStatus(result);
  };

  const goToIssue = () => {
    const first = blockers[0];
    if (first) document.getElementById(`engineering-property-${first.name}`)?.focus();
  };

  if (!controller.workspaceId || !controller.selected) return null;

  return (
    <section aria-label="Jarvis engineering actions">
      <div className="shell-properties__selection">
        <strong>Engineering actions</strong>
        <p>{blockerSignalCount ? `${blockerSignalCount} deterministic blocker signal${blockerSignalCount === 1 ? "" : "s"} in the current working configuration.` : "Current working configuration has no deterministic blocker."}</p>
      </div>

      {blockerSignalCount ? (
        <div>
          {blockers[0] ? <p><strong>{blockers[0].label}</strong> · {blockers[0].unit}</p> : null}
          {!blockers.length && previewErrors[0] ? <p><strong>Preflight</strong> · {previewErrors[0]}</p> : null}
          {safeOperations.length ? <small>Only fixes with an existing deterministic basis are offered. No value is invented.</small> : <small>No deterministic safe value is available. Edit Properties manually or ask Jarvis for advisory help.</small>}
          <div>
            {bulkAction ? <button type="button" className="secondary-button" onClick={() => previewAction(bulkAction)}>Apply safe fixes</button> : null}
            {singleActions.map((action) => (
              <button key={action.id} type="button" className="secondary-button" onClick={() => previewAction(action)}>
                Review safe fix · {action.operations[0].label}
              </button>
            ))}
            {blockers.length ? <button type="button" className="secondary-button" onClick={goToIssue}>I'll edit</button> : null}
            <button type="button" className="secondary-button" onClick={() => setShowOther((current) => !current)}>Other</button>
          </div>
        </div>
      ) : null}

      {showOther ? (
        <label>
          Other
          <input value={otherText} onChange={(event) => setOtherText(event.target.value)} placeholder="Describe an alternative" />
          <small>This text is inert. It is not parsed as a command, JSON, field=value instruction, or working-state mutation.</small>
        </label>
      ) : null}

      {selectedAction ? (
        <div aria-live="polite">
          <p><strong>Proposed working-state change</strong></p>
          {selectedAction.operations.map((operation) => (
            <div key={operation.variableName} className="scenario-variable">
              <strong>{operation.label}</strong>
              <span>{renderBinding(operation.expectedBinding, operation.unit)} → {renderBinding(operation.proposedBinding, operation.unit)}</span>
              <small>{operation.basisLabel}</small>
              <small>{operation.reason}</small>
            </div>
          ))}
          {status === "ready" ? (
            <div>
              <button type="button" onClick={confirm}>Confirm</button>
              <button type="button" className="secondary-button" onClick={() => setStatus("rejected")}>Reject</button>
            </div>
          ) : null}
          {status === "applied" ? <p role="status">Applied to the working configuration. Properties, dirty state and preflight now use the updated revision. Run remains a separate explicit action.</p> : null}
          {status === "stale" ? <p role="status">This action is stale because the workspace, model, contract, object context, revision or expected value changed. No mutation was applied.</p> : null}
          {status === "invalid" ? <p role="status">This action no longer satisfies the current deterministic contract/source rules. No mutation was applied.</p> : null}
          {status === "rejected" ? <p role="status">Rejected. No mutation was applied.</p> : null}
        </div>
      ) : null}

      <small>Jarvis conversation remains advisory. Numeric or model suggestions in assistant prose are AI suggested — not validated and never execute from transcript text.</small>
    </section>
  );
}