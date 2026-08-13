import type { ComponentType, ReactNode } from "react";

import type { Navigate } from "../app/AppLink";
import type { StageSelection } from "../app/selection";
import type { StageKind } from "../app/routes";
import FlowsheetStage from "./FlowsheetStage";
import ModelStage from "./ModelStage";
import ResultsStage from "./ResultsStage";
import ReviewStage from "./ReviewStage";

export type ShellRegion = "navigator" | "sidecar" | "dock";

export type ShellRegionContributions = Readonly<{
  navigator?: ReactNode;
  sidecar?: ReactNode;
  dock?: ReactNode;
}>;

export type PrimaryStageProps = Readonly<{
  workspaceId: string | null;
  selection: StageSelection | null;
  onSelectionChange(next: StageSelection | null): void;
  onShellRegionsChange(next: ShellRegionContributions): void;
  requestShellRegionOpen(region: ShellRegion): void;
  navigate: Navigate;
}>;

export type StageDefinition = Readonly<{
  kind: StageKind;
  label: string;
  render: ComponentType<PrimaryStageProps>;
}>;

export const PRIMARY_STAGES: Readonly<Record<StageKind, StageDefinition>> = {
  model: { kind: "model", label: "Model", render: ModelStage },
  results: { kind: "results", label: "Results", render: ResultsStage },
  review: { kind: "review", label: "Review", render: ReviewStage },
  flowsheet: { kind: "flowsheet", label: "Flowsheet", render: FlowsheetStage }
};
