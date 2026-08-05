import { useEffect, useState, type ReactNode } from "react";

import type { AppPage } from "../App";
import {
  APPEARANCE_OPTIONS,
  applyAppearancePreference,
  applyResolvedAppearance,
  readAppearancePreference,
  subscribeToSystemAppearance,
  writeAppearancePreference,
  type AppearancePreference
} from "../theme";
import Button from "./ui/Button";
import Field from "./ui/Field";

type LayoutProps = {
  activePage: AppPage;
  children: ReactNode;
  onNavigate: (page: AppPage) => void;
};

const APPEARANCE_LABELS: Record<AppearancePreference, string> = {
  system: "System",
  light: "Light",
  dark: "Dark"
};

function Layout({ activePage, children, onNavigate }: LayoutProps) {
  const [appearance, setAppearance] = useState<AppearancePreference>(() => readAppearancePreference());

  useEffect(() => {
    applyAppearancePreference(appearance);
    return subscribeToSystemAppearance(appearance, applyResolvedAppearance);
  }, [appearance]);

  const onAppearanceChange = (preference: AppearancePreference) => {
    writeAppearancePreference(preference);
    applyAppearancePreference(preference);
    setAppearance(preference);
  };

  const appearanceSelect = (
    <select
      aria-label="Appearance preference"
      value={appearance}
      onChange={(event) => onAppearanceChange(event.target.value as AppearancePreference)}
    >
      {APPEARANCE_OPTIONS.map((option) => (
        <option key={option} value={option}>{APPEARANCE_LABELS[option]}</option>
      ))}
    </select>
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">JarvisOS</p>
          <h1>BlueRev Model Foundry</h1>
        </div>
        <nav className="nav" aria-label="Main navigation">
          <Button
            variant="ghost"
            className={activePage === "dashboard" ? "nav-button active" : "nav-button"}
            onClick={() => onNavigate("dashboard")}
          >
            Dashboard
          </Button>
          <Button
            variant="ghost"
            className={activePage === "system" ? "nav-button active" : "nav-button"}
            onClick={() => onNavigate("system")}
          >
            System Status
          </Button>
          <Button
            variant="ghost"
            className={activePage === "foundation" ? "nav-button active" : "nav-button"}
            onClick={() => onNavigate("foundation")}
          >
            Domain Foundation
          </Button>
          <Button
            variant="ghost"
            className={activePage === "bluecad" ? "nav-button active" : "nav-button"}
            onClick={() => onNavigate("bluecad")}
          >
            BLUECAD
          </Button>
          <Button
            variant="ghost"
            className={activePage === "ai" ? "nav-button active" : "nav-button"}
            onClick={() => onNavigate("ai")}
          >
            AI Draft
          </Button>
          {import.meta.env.DEV && (
            <Button
              variant="ghost"
              className={activePage === "devlocalchat" ? "nav-button active nav-button--dev" : "nav-button nav-button--dev"}
              onClick={() => onNavigate("devlocalchat")}
            >
              Dev Local Chat
            </Button>
          )}
        </nav>
        <Field className="appearance-control" label="Appearance" control={appearanceSelect} />
      </aside>
      <main className="main-panel">{children}</main>
    </div>
  );
}

export default Layout;
