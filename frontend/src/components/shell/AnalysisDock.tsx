import { useEffect, useRef } from "react";

import Button from "../ui/Button";
import InlineNotice from "../ui/InlineNotice";

type AnalysisDockProps = Readonly<{
  open: boolean;
  onClose(): void;
}>;

function AnalysisDock({ open, onClose }: AnalysisDockProps) {
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
    <section id="shell-analysis-dock" className="shell-panel shell-analysis-dock" aria-labelledby="shell-analysis-title">
      <div className="shell-panel__header">
        <h2 id="shell-analysis-title" ref={headingRef} tabIndex={-1}>Analysis dock</h2>
        <Button variant="ghost" onClick={onClose}>Close analysis dock</Button>
      </div>
      <InlineNotice tone="neutral">Analytics are not available in APP-SHELL-1. Real-data analysis belongs to spec 089.</InlineNotice>
    </section>
  );
}

export default AnalysisDock;
