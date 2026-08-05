import type { PrimaryStageProps } from "./registry";
import BlueCAD from "../pages/BlueCAD";

function ModelStage(_props: PrimaryStageProps) {
  return (
    <section className="shell-stage shell-stage--model" aria-labelledby="model-stage-title">
      <header className="shell-stage__header">
        <p className="eyebrow">Primary stage</p>
        <h1 id="model-stage-title">Model</h1>
        <p>Current BLUECAD is compatibility-mounted here without changing its lifecycle, API calls, evidence, or viewer internals.</p>
      </header>
      <div className="shell-stage__compatibility">
        <BlueCAD />
      </div>
    </section>
  );
}

export default ModelStage;
