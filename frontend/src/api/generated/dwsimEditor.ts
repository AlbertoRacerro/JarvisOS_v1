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
