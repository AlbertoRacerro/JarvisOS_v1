import type { PrimaryStageProps } from "./registry";

function ProcessStage(_props: PrimaryStageProps) {
  return (
    <section className="process-stage" aria-labelledby="process-stage-title">
      <header className="page-header process-stage__header">
        <div>
          <p className="eyebrow">Process</p>
          <h1 id="process-stage-title">Process workspace</h1>
          <p className="panel-subtitle">
            Process topology editing is unavailable until server-owned process and evaluator contracts are integrated.
          </p>
        </div>
      </header>

      <div className="process-stage__workbench">
        <div className="process-stage__toolbar" aria-label="Process tools">
          <button type="button" className="secondary-button" disabled>Add equipment</button>
          <button type="button" className="secondary-button" disabled>Connect</button>
          <button type="button" className="secondary-button" disabled>Disconnect</button>
          <button type="button" className="secondary-button" disabled>Validate</button>
          <button type="button" className="secondary-button" disabled>Solve</button>
        </div>

        <aside className="process-stage__palette" aria-label="Process equipment">
          <strong>Process equipment</strong>
          <p className="panel-subtitle">Not available yet.</p>
        </aside>

        <div className="process-stage__canvas" role="region" aria-label="Process canvas">
          <div>
            <strong>No process topology is loaded.</strong>
            <p className="panel-subtitle">
              This canvas becomes editable only after server-owned process and evaluator contracts are integrated.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default ProcessStage;
