import { API_BASE_URL } from "./client";

export type LiteratureState = "raw" | "review" | "accepted";
export type LiteratureEntryKind = "claim" | "datum";

export type LiteratureUsedBy = {
  kind: "parameter" | "assumption" | "artifact";
  record_id: string;
  title: string;
  ref: string;
};

export type LiteratureEntry = {
  id: string;
  workspace_id: string;
  source_id: string;
  entry_kind: LiteratureEntryKind;
  statement: string | null;
  value_text: string | null;
  value_number: number | null;
  unit: string | null;
  status: LiteratureState;
  locator_kind: "page" | "line" | "section" | null;
  locator_start: number | null;
  locator_end: number | null;
  context_text: string | null;
  provenance_ref: string;
  used_by: LiteratureUsedBy[];
  created_at: string;
  updated_at: string;
};

export type LiteratureSource = {
  id: string;
  workspace_id: string;
  title: string;
  source_kind: "paper" | "book" | "report" | "standard" | "dataset" | "web" | "other";
  state: LiteratureState;
  citation: string | null;
  publisher: string | null;
  published_year: number | null;
  source_ref: string;
  backing: null | {
    artifact_id: string;
    filename: string;
    mime_type: string | null;
    sha256: string | null;
    content_available: boolean;
    content_url: string | null;
  };
  entries: LiteratureEntry[];
  created_at: string;
  updated_at: string;
};

export type LiteratureSourcePage = {
  items: LiteratureSource[];
  offset: number;
  limit: number;
  total: number;
  next_offset: number | null;
};

export async function listLiteratureSources(workspaceId: string): Promise<LiteratureSourcePage> {
  const response = await fetch(`${API_BASE_URL}/workspaces/${encodeURIComponent(workspaceId)}/literature/sources?limit=100`);
  if (!response.ok) throw new Error(`Literature request failed with ${response.status}`);
  return response.json() as Promise<LiteratureSourcePage>;
}

export function literatureContentUrl(source: LiteratureSource): string | null {
  if (!source.backing?.content_available || !source.backing.content_url) return null;
  return `${API_BASE_URL}${source.backing.content_url}`;
}
