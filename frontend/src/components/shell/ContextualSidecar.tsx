import { useEffect, useRef } from "react";

import type { StageSelection } from "../../app/selection";
import Button from "../ui/Button";
import InlineNotice from "../ui/InlineNotice";

type ContextualSidecarProps = Readonly<{
  open: boolean;
  selection: StageSelection | null;
  onClose(): void;
}>;

function ContextualSidecar({ open, selection, onClose }: ContextualSidecarProps) {
  const headingRef = useRef<HTMLHeadingElement | null>(null);

  useEffect(() => {
    if (!open) return undefined;
    headingRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <aside id="shell-sidecar" className="shell-panel shell-sidecar" aria-labelledby="shell-sidecar-title">
      <div className="shell-panel__header">
        <h2 id="shell-sidecar-title" ref={headingRef} tabIndex={-1}>Context</h2>
        <Button variant="ghost" onClick={onClose}>Close sidecar</Button>
      </div>
      {selection === null ? (
        <InlineNotice tone="neutral">No record selected. APP-SHELL-1 does not infer identity from page or viewer state.</InlineNotice>
      ) : selection.kind === "record" ? (
        <dl className="details">
          <div><dt>Resource</dt><dd>{selection.ref.resource}</dd></div>
          <div><dt>Workspace</dt><dd>{selection.ref.workspaceId}</dd></div>
          <div><dt>Record</dt><dd>{selection.ref.recordId}</dd></div>
        </dl>
      ) : (
        <InlineNotice tone="neutral">Geometry hits are ephemeral viewer-session data and are not engineering records.</InlineNotice>
      )}
    </aside>
  );
}

export default ContextualSidecar;
