import InlineNotice from "../components/ui/InlineNotice";
import Surface from "../components/ui/Surface";
import type { PrimaryStageProps } from "./registry";

function ReviewStage(_props: PrimaryStageProps) {
  return (
    <section className="shell-placeholder" aria-labelledby="review-stage-title">
      <div className="page-header">
        <p className="eyebrow">Unavailable</p>
        <h1 id="review-stage-title">Review</h1>
      </div>
      <Surface as="div" className="shell-placeholder__surface">
        <InlineNotice tone="neutral">Proposal review is not implemented by APP-SHELL-1. It remains owned by re-derived spec 054.</InlineNotice>
      </Surface>
    </section>
  );
}

export default ReviewStage;
