import type { ChangeEvent, RefObject } from "react";

import { APPEARANCE_OPTIONS, type AppearancePreference } from "../../theme";
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
  appearance: AppearancePreference;
  onAppearanceChange(next: AppearancePreference): void;
  toggles: readonly PanelToggle[];
}>;

function TopBar({ title, appearance, onAppearanceChange, toggles }: TopBarProps) {
  const handleAppearance = (event: ChangeEvent<HTMLSelectElement>) => {
    onAppearanceChange(event.target.value as AppearancePreference);
  };

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
        <label className="appearance-control shell-appearance-control">
          <span>Appearance</span>
          <select value={appearance} onChange={handleAppearance} aria-label="Appearance preference">
            {APPEARANCE_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option[0].toUpperCase() + option.slice(1)}
              </option>
            ))}
          </select>
        </label>
      </div>
    </header>
  );
}

export default TopBar;
