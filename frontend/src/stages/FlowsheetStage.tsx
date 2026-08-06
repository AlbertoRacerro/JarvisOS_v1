import AppLink from "../app/AppLink";
import InlineNotice from "../components/ui/InlineNotice";
import Surface from "../components/ui/Surface";
import type { PrimaryStageProps } from "./registry";

function FlowsheetStage({ navigate }: PrimaryStageProps) {
  return (
    <section className="shell-placeholder" aria-labelledby="flowsheet-stage-title">
      <div className="page-header">
        <p className="eyebrow">Unavailable</p>
        <h1 id="flowsheet-stage-title">Flowsheet</h1>
      </div>
      <Surface as="div" className="shell-placeholder__surface">
        <InlineNotice tone="neutral">
          Editable flowsheets are unavailable. APP-SHELL-1 does not render a fake canvas, simulated streams, or solver state.
        </InlineNotice>
        <nav className="shell-placeholder__links" aria-label="Flowsheet alternatives">
          <AppLink href="/runs" navigate={navigate} className="shell-text-link">Open Runs</AppLink>
          <span>Lineage is future work under spec 087.</span>
        </nav>
      </Surface>
    </section>
  );
}

export default FlowsheetStage;
