import BluecadWorkbench from "../components/bluecad/BluecadWorkbench";
import type { PrimaryStageProps } from "./registry";

function ModelStage({ onSelectionChange, onShellRegionsChange, requestShellRegionOpen }: PrimaryStageProps) {
  return (
    <BluecadWorkbench
      onSelectionChange={onSelectionChange}
      onShellRegionsChange={onShellRegionsChange}
      requestShellRegionOpen={requestShellRegionOpen}
    />
  );
}

export default ModelStage;
