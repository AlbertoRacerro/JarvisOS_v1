import { request } from "./studio";

export type DesignVersion = {
  id: string; project_id: string; data_workspace_id: string;
  parent_version_id: string | null; label: string; active: boolean;
  starts_empty: boolean; created_at: string;
};
export type DesignVersionSet = { project_id: string; active_version_id: string; versions: DesignVersion[] };
export type DesignComponent = {
  id: string; project_id: string; version_id: string; parent_id: string | null;
  name: string; revision: number; created_at: string; updated_at: string;
  source_draft_id: string | null; source_unit_id: string | null;
  geometry_candidate_id: string | null; geometry_source_draft_revision: string | null;
  models: DesignComponentModel[];
};
export type DesignComponentModel = {
  model_version_id: string; node: string; category: string; source_sha256: string; contract_sha256: string; attached_at: string;
};
/** Studio categories that attach to a component node; process units and procedures attach to Plant. */
export const COMPONENT_NODE_OF_CATEGORY: Record<string, string> = { calculation: "Physics", geometry: "Geometry" };

const base = (projectId: string) => `/workspaces/${encodeURIComponent(projectId)}/design-versions`;
const components = (projectId: string, versionId: string) => `${base(projectId)}/${encodeURIComponent(versionId)}/components`;

export const listDesignVersions = (projectId: string) => request<DesignVersionSet>(base(projectId));
export const createDesignVersion = (projectId: string, label: string, expected: string) =>
  request<DesignVersionSet>(base(projectId), "POST", { label, expected_active_version_id: expected });
export const activateDesignVersion = (projectId: string, versionId: string, expected: string) =>
  request<DesignVersionSet>(`${base(projectId)}/activate`, "POST", { version_id: versionId, expected_active_version_id: expected });
export const listDesignComponents = (projectId: string, versionId: string) =>
  request<DesignComponent[]>(components(projectId, versionId));
export const createDesignComponent = (projectId: string, versionId: string, name: string, parentId: string | null) =>
  request<DesignComponent>(components(projectId, versionId), "POST", {
    name, parent_id: parentId, expected_active_version_id: versionId
  });
export const openDesignUnit = (projectId: string, versionId: string, draftId: string, revision: string, unitId: string) =>
  request<DesignComponent>(`${components(projectId, versionId)}/from-unit`, "POST", {
    draft_id: draftId, unit_id: unitId, expected_draft_revision: revision,
    expected_active_version_id: versionId
  });
export const editDesignComponent = (projectId: string, versionId: string, component: DesignComponent,
  name: string, parentId: string | null) =>
  request<DesignComponent>(`${components(projectId, versionId)}/${encodeURIComponent(component.id)}`, "PUT", {
    name, parent_id: parentId, expected_revision: component.revision, expected_active_version_id: versionId
  });
export const attachDesignGeometry = (projectId: string, versionId: string, component: DesignComponent,
  candidateId: string, draftRevision: string | null) =>
  request<DesignComponent>(`${components(projectId, versionId)}/${encodeURIComponent(component.id)}/geometry`, "PUT", {
    candidate_id: candidateId, expected_revision: component.revision, expected_active_version_id: versionId,
    expected_draft_revision: draftRevision
  });
export type ProcessGeometryMapping = {
  supported: boolean; unit_type: string; template: string | null; inner_d_mm: number | null; length_mm: number | null;
  basis: string; draft_revision: string;
};
export const getProcessGeometryMapping = (projectId: string, versionId: string, componentId: string) =>
  request<ProcessGeometryMapping>(`${components(projectId, versionId)}/${encodeURIComponent(componentId)}/geometry/process-mapping`);
export const deepenDesignGeometry = (projectId: string, versionId: string, component: DesignComponent,
  wallMm: number, draftRevision: string) =>
  request<DesignComponent>(`${components(projectId, versionId)}/${encodeURIComponent(component.id)}/geometry/from-process`, "POST", {
    wall_t_mm: wallMm, expected_revision: component.revision, expected_active_version_id: versionId,
    expected_draft_revision: draftRevision
  });
export const attachDesignModel = (projectId: string, versionId: string, component: DesignComponent, modelVersionId: string) =>
  request<DesignComponent>(`${components(projectId, versionId)}/${encodeURIComponent(component.id)}/models`, "PUT", {
    model_version_id: modelVersionId, expected_revision: component.revision, expected_active_version_id: versionId
  });
