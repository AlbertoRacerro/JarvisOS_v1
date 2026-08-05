import { useEffect, useRef } from "react";

import AppLink, { type Navigate } from "../../app/AppLink";
import { DESIGN_STAGE_ITEMS, type StageKind } from "../../app/routes";
import Button from "../ui/Button";

type ContextualNavigatorProps = Readonly<{
  open: boolean;
  currentStage: StageKind | undefined;
  navigate: Navigate;
  onClose(): void;
}>;

function ContextualNavigator({ open, currentStage, navigate, onClose }: ContextualNavigatorProps) {
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
    <aside id="shell-navigator" className="shell-panel shell-navigator" aria-labelledby="shell-navigator-title">
      <div className="shell-panel__header">
        <h2 id="shell-navigator-title" ref={headingRef} tabIndex={-1}>Navigator</h2>
        <Button variant="ghost" onClick={onClose}>Close navigator</Button>
      </div>
      {currentStage ? (
        <nav className="shell-stage-links" aria-label="Design stages">
          {DESIGN_STAGE_ITEMS.map((item) => (
            <AppLink
              key={item.kind}
              href={item.href}
              navigate={navigate}
              className="shell-nav-link"
              aria-current={currentStage === item.kind ? "page" : undefined}
            >
              {item.label}
            </AppLink>
          ))}
        </nav>
      ) : (
        <p className="panel-subtitle">No contextual navigation is available for this route.</p>
      )}
    </aside>
  );
}

export default ContextualNavigator;
