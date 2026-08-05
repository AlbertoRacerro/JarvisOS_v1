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

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">JarvisOS</p>
          <h1>BlueRev Model Foundry</h1>
        </div>
        <nav className="nav" aria-label="Main navigation">
          <button
            className={activePage === "dashboard" ? "nav-button active" : "nav-button"}
            type="button"
            onClick={() => onNavigate("dashboard")}
          >
            Dashboard
          </button>
          <button
            className={activePage === "system" ? "nav-button active" : "nav-button"}
            type="button"
            onClick={() => onNavigate("system")}
          >
            System Status
          </button>
          <button
            className={activePage === "foundation" ? "nav-button active" : "nav-button"}
            type="button"
            onClick={() => onNavigate("foundation")}
          >
            Domain Foundation
          </button>
          <button
            className={activePage === "bluecad" ? "nav-button active" : "nav-button"}
            type="button"
            onClick={() => onNavigate("bluecad")}
          >
            BLUECAD
          </button>
          <button
            className={activePage === "ai" ? "nav-button active" : "nav-button"}
            type="button"
            onClick={() => onNavigate("ai")}
          >
            AI Draft
          </button>
          {import.meta.env.DEV && (
            <button
              className={activePage === "devlocalchat" ? "nav-button active nav-button--dev" : "nav-button nav-button--dev"}
              type="button"
              onClick={() => onNavigate("devlocalchat")}
            >
              Dev Local Chat
            </button>
          )}
        </nav>
        <label className="appearance-control">
          <span>Appearance</span>
          <select
            aria-label="Appearance preference"
            value={appearance}
            onChange={(event) => onAppearanceChange(event.target.value as AppearancePreference)}
          >
            {APPEARANCE_OPTIONS.map((option) => (
              <option key={option} value={option}>{APPEARANCE_LABELS[option]}</option>
            ))}
          </select>
        </label>
      </aside>
      <main className="main-panel">{children}</main>
    </div>
  );
}

export default Layout;
