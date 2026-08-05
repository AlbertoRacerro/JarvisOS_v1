import type { ReactNode, RefObject } from "react";

import Button from "../ui/Button";

type PanelToggle = Readonly<{
  id: string;
  label: string;
  expanded: boolean;
  controls: string;
  ref: RefObject<HTMLButtonElement>;
  onToggle(): void;
}>;

type TopBarProps = Readonly<{
  title: string;
  appearanceControl: ReactNode;
  toggles: readonly PanelToggle[];
}>;

function TopBar({ title, appearanceControl, toggles }: TopBarProps) {
  return (
    <header className="shell-topbar">
      <div className="shell-topbar__title">
        <span>Current route</span>
        <strong>{title}</strong>
      </div>
      <div className="shell-topbar__controls">
        {toggles.map((toggle) => (
          <Button
            key={toggle.id}
            ref={toggle.ref}
            variant="ghost"
            aria-expanded={toggle.expanded}
            aria-controls={toggle.controls}
            onClick={toggle.onToggle}
          >
            {toggle.label}
          </Button>
        ))}
        {appearanceControl}
      </div>
    </header>
  );
}

export default TopBar;
