import BluecadWorkbench from "../components/bluecad/BluecadWorkbench";
import type { PrimaryStageProps } from "./registry";

function ModelStage({ onSelectionChange, onShellRegionsChange, requestShellRegionOpen, navigate }: PrimaryStageProps) {
  return (
    <section className="bluecad-final-stage design-stage" aria-labelledby="bluecad-final-title">
      <header className="design-stage__header bluecad-final-stage__header">
        <div className="design-stage__title-row">
          <div>
            <p className="eyebrow">Design</p>
            <h1 id="bluecad-final-title">BLUECAD workspace</h1>
            <p className="panel-subtitle">Inspect server-built geometry, create deterministic template parts and hand off STL or STEP files for printing.</p>
          </div>
          <span className="design-stage__truth-state">Geometry · Server-owned</span>
        </div>
        <nav className="design-stage__tabs" aria-label="Design workspaces">
          <button type="button" onClick={() => navigate("/design/process")}>Process</button>
          <button type="button" className="is-active" aria-current="page">BLUECAD</button>
        </nav>
      </header>

      <div className="bluecad-final-stage__body">
        <BluecadWorkbench
          onSelectionChange={onSelectionChange}
          onShellRegionsChange={onShellRegionsChange}
          requestShellRegionOpen={requestShellRegionOpen}
        />
      </div>
    </section>
  );
}

export default ModelStage;
