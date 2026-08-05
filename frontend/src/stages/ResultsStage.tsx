import type { Navigate } from "../app/AppLink";
import MigrationPendingSurface from "../components/shell/MigrationPendingSurface";
import type { PrimaryStageProps } from "./registry";

type ResultsStageProps = PrimaryStageProps & Readonly<{ navigate: Navigate }>;

function ResultsStage({ navigate }: ResultsStageProps) {
  return (
    <MigrationPendingSurface
      title="Results"
      description="A dedicated results workbench is not available yet. APP-SHELL-1 provides only the stage boundary."
      navigate={navigate}
      links={[{ href: "/runs", label: "Open the Runs destination" }]}
      unavailable
    />
  );
}

export default ResultsStage;
