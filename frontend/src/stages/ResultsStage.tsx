import InlineNotice from "../components/ui/InlineNotice";
import Surface from "../components/ui/Surface";
import type { PrimaryStageProps } from "./registry";

function ResultsStage(_props: PrimaryStageProps) {
  return (
    <section className="shell-placeholder" aria-labelledby="results-stage-title">
      <div className="page-header">
        <p className="eyebrow">Unavailable</p>
        <h1 id="results-stage-title">Results</h1>
      </div>
      <Surface as="div" className="shell-placeholder__surface">
        <InlineNotice tone="neutral">
          A dedicated results workbench is not available yet. APP-SHELL-1 provides only the stage boundary.
        </InlineNotice>
        <nav className="shell-placeholder__links" aria-label="Results alternatives">
          <a href="/runs" className="shell-text-link">Open Runs</a>
        </nav>
      </Surface>
    </section>
  );
}

export default ResultsStage;
