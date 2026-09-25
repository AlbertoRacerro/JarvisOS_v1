// GENERATED FILE — DO NOT EDIT.
// Source: backend/app/modules/process_stack/editor_models.py
// Regenerate with: python scripts/generate_frontend_contracts.py

export type EditorQuantity = {
  value: number;
  unit: string;
};

export type EditorCaseRead = {
  workspace_id: string;
  case_id: string;
  revision: string;
  case_sha256: string;
  dwsim_version: string;
  created_at: string;
};

export type RevisionRead = {
  seq: number;
  case_sha256: string;
  revision: string;
  parent_revision: string | null;
  command_kind: string;
  created_at: string;
  readback: Record<string, unknown>;
};

export type EditorObjectRead = {
  native_id: string | null;
  tag: string | null;
  type: string | null;
  category: "unit" | "material_stream" | "energy_stream" | "other";
  x: number | null;
  y: number | null;
  width: number | null;
  height: number | null;
  calculated: boolean | null;
  errors: string;
  results: Record<string, unknown> | null;
};

export type EditorConnectionRead = {
  source_native_id: string;
  source_port: number;
  target_native_id: string;
  target_port: number;
  kind: "material" | "energy";
};

export type EditorProjectionRead = {
  workspace_id: string;
  case_id: string;
  revision: string;
  case_sha256: string;
  dwsim_version: string;
  mcp_sha256: string;
  availability: "available";
  objects: EditorObjectRead[];
  connections: EditorConnectionRead[];
  compounds: string[];
  property_package: string | null;
  last_solve: Record<string, unknown> | null;
  editable_commands: string[];
  unsupported_commands: Record<string, string>;
};

export type CommandResult = {
  case: EditorCaseRead;
  projection: EditorProjectionRead;
  readback: Record<string, unknown>;
};

export type CreateUnit = {
  kind: "create_unit";
  expected_revision: string;
  unit_type: string;
  tag: string;
  x: number;
  y: number;
};

export type CreateMaterialStream = {
  kind: "create_material_stream";
  expected_revision: string;
  tag: string;
  x: number;
  y: number;
  temperature: EditorQuantity | null;
  pressure: EditorQuantity | null;
  mass_flow: EditorQuantity | null;
  composition: Record<string, number> | null;
};

export type CreateEnergyStream = {
  kind: "create_energy_stream";
  expected_revision: string;
  tag: string;
  x: number;
  y: number;
};

export type Connect = {
  kind: "connect";
  expected_revision: string;
  unit: string;
  stream: string;
  role: "feed" | "product" | "energy_feed" | "energy_product";
  port: number;
};

export type Move = {
  kind: "move";
  expected_revision: string;
  object: string;
  x: number;
  y: number;
};

export type Rename = {
  kind: "rename";
  expected_revision: string;
  object: string;
  new_tag: string;
};

export type SetStreamConditions = {
  kind: "set_stream_conditions";
  expected_revision: string;
  stream: string;
  temperature: EditorQuantity | null;
  pressure: EditorQuantity | null;
  mass_flow: EditorQuantity | null;
  molar_flow: EditorQuantity | null;
  composition: Record<string, number> | null;
};

export type SetUnitProperties = {
  kind: "set_unit_properties";
  expected_revision: string;
  unit: string;
  properties: Record<string, unknown>;
};

export type AddCompounds = {
  kind: "add_compounds";
  expected_revision: string;
  compounds: string[];
};

export type SetPropertyPackage = {
  kind: "set_property_package";
  expected_revision: string;
  name: string;
};

export type Solve = {
  kind: "solve";
  expected_revision: string;
};

export type DeleteObject = {
  kind: "delete_object";
  expected_revision: string;
  object: string;
};

export type Disconnect = {
  kind: "disconnect";
  expected_revision: string;
  unit: string;
  stream: string;
  role: "feed" | "product" | "energy_feed" | "energy_product";
  port: number;
};

export type UnsupportedCommand = {
  kind: "controller_set" | "event_add" | "event_remove" | "dynamics_run" | "state_save" | "state_restore";
  expected_revision: string;
  parameters: Record<string, unknown>;
};

export type EditorCommand =
  | CreateUnit
  | CreateMaterialStream
  | CreateEnergyStream
  | Connect
  | Move
  | Rename
  | SetStreamConditions
  | SetUnitProperties
  | AddCompounds
  | SetPropertyPackage
  | Solve
  | DeleteObject
  | Disconnect
  | UnsupportedCommand;
