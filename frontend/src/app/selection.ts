export type RecordResource =
  | "workspace"
  | "model-spec"
  | "assumption"
  | "parameter"
  | "simulation-run"
  | "decision"
  | "bluecad-candidate";

export type RecordRef = Readonly<{
  resource: RecordResource;
  workspaceId: string;
  recordId: string;
}>;

export type StageSelection =
  | Readonly<{ kind: "record"; ref: RecordRef }>
  | Readonly<{
      kind: "geometry-hit";
      viewerSessionId: string;
      ephemeralObjectId: string;
      point?: readonly [number, number, number];
    }>;
